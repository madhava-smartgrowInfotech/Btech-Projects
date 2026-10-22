"""Re-derive the extra evaluation numbers used by the project documents.

Reproduces the 80/20 stratified split from scripts/train.py, loads the persisted
pipelines, and writes artifacts/report_metrics.json (confusion matrix, per-class
precision/recall, threshold sweep, calibration bins, forecast back-test).
Run inside the project .venv:  python scripts/report_metrics.py
"""
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score, average_precision_score, brier_score_loss)
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
from feature_engineering import (COLUMN_NAMES, TARGET_COL, POSITIVE_LABEL, RANDOM_STATE,  # noqa: E402
                                 clean_frame, add_derived_features)
from forecast import build_index_series  # noqa: E402


def load_data():
    raw = ROOT / "data" / "raw"
    tr = pd.read_csv(raw / "adult.data", header=None, names=COLUMN_NAMES, skipinitialspace=True)
    te = pd.read_csv(raw / "adult.test", header=None, names=COLUMN_NAMES, skipinitialspace=True, skiprows=1)
    return pd.concat([tr, te], ignore_index=True)


def main():
    df_raw = load_data()
    df = clean_frame(df_raw).dropna(subset=[TARGET_COL])
    df = add_derived_features(df)
    y = (df[TARGET_COL] == POSITIVE_LABEL).astype(int)
    X = df.drop(columns=[TARGET_COL])
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)

    out = {"rows": int(len(df)), "train": int(len(y_tr)), "test": int(len(y_te)),
           "positive_rate_all": round(float(y.mean()), 4),
           "raw_rows_adult_data": int(len(pd.read_csv(ROOT / "data/raw/adult.data", header=None))),
           "missing_cells_raw": {c: int((df_raw[c].astype(str).str.strip() == "?").sum())
                                 for c in ["workclass", "occupation", "native-country"]},
           "models": {}}
    for name in ["logistic_regression", "random_forest", "gradient_boosting", "xgboost"]:
        pipe = joblib.load(ROOT / "models" / f"{name}.pkl")
        p = pipe.predict_proba(X_te)[:, 1]
        pred = (p >= 0.5).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_te, pred).ravel()
        out["models"][name] = {
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
            "accuracy": round(accuracy_score(y_te, pred), 4),
            "precision": round(precision_score(y_te, pred), 4),
            "recall": round(recall_score(y_te, pred), 4),
            "f1": round(f1_score(y_te, pred), 4),
            "roc_auc": round(roc_auc_score(y_te, p), 4),
            "pr_auc": round(average_precision_score(y_te, p), 4),
            "brier": round(brier_score_loss(y_te, p), 4),
            "specificity": round(tn / (tn + fp), 4),
        }
    best = joblib.load(ROOT / "models" / "best_model.pkl")
    p = best.predict_proba(X_te)[:, 1]
    sweep = []
    for t in [0.2, 0.3, 0.35, 0.4, 0.5, 0.6, 0.7, 0.8]:
        pr = (p >= t).astype(int)
        sweep.append({"threshold": t, "accuracy": round(accuracy_score(y_te, pr), 4),
                      "precision": round(precision_score(y_te, pr), 4),
                      "recall": round(recall_score(y_te, pr), 4), "f1": round(f1_score(y_te, pr), 4)})
    out["threshold_sweep_xgboost"] = sweep
    # profile bands used by the application (>=0.60 Established, >=0.35 Developing, else Emerging)
    band = np.where(p >= 0.60, "Established", np.where(p >= 0.35, "Developing", "Emerging"))
    out["profile_band_counts_test"] = {b: int((band == b).sum()) for b in ["Emerging", "Developing", "Established"]}
    out["profile_band_actual_positive_rate"] = {
        b: round(float(y_te.values[band == b].mean()), 4) for b in ["Emerging", "Developing", "Established"]}
    # calibration: 10 equal-width bins
    bins = np.linspace(0, 1, 11)
    idx = np.digitize(p, bins[1:-1])
    out["calibration"] = [{"bin": f"{bins[i]:.1f}-{bins[i+1]:.1f}", "n": int((idx == i).sum()),
                           "mean_pred": round(float(p[idx == i].mean()), 4) if (idx == i).any() else None,
                           "observed": round(float(y_te.values[idx == i].mean()), 4) if (idx == i).any() else None}
                          for i in range(10)]
    # single-row latency (in-process)
    from app.services.predictor import predict_profile, get_model  # noqa: E402
    get_model()
    sample = {"age": 39, "workclass": "State-gov", "education": "Bachelors", "marital-status": "Never-married",
              "occupation": "Adm-clerical", "relationship": "Not-in-family", "race": "White", "sex": "Male",
              "native-country": "United-States", "capital-gain": 2174, "capital-loss": 0,
              "hours-per-week": 40, "education-num": 13}
    predict_profile(sample)
    ts = []
    for _ in range(30):
        t0 = time.perf_counter(); predict_profile(sample); ts.append((time.perf_counter() - t0) * 1000)
    out["predict_profile_ms"] = {"median": round(float(np.median(ts)), 1), "p95": round(float(np.percentile(ts, 95)), 1),
                                 "n": len(ts)}
    # forecast back-test: fit on 2015-01..2024-12, predict the held-out 12 months of 2025
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    s = build_index_series().set_index("date")["index_value"].asfreq("MS")
    train, test = s.iloc[:-12], s.iloc[-12:]
    fit = ExponentialSmoothing(train, trend="add", seasonal="add", seasonal_periods=12,
                               initialization_method="estimated").fit(optimized=True)
    fc = fit.forecast(12)
    mae = float(np.mean(np.abs(fc.values - test.values)))
    mape = float(np.mean(np.abs(fc.values - test.values) / test.values) * 100)
    rmse = float(np.sqrt(np.mean((fc.values - test.values) ** 2)))
    naive = float(np.mean(np.abs(train.values[-1] - test.values)))
    resid = float(np.std(fit.resid.dropna()))
    cover = float(np.mean((test.values >= fc.values - 1.96 * resid) & (test.values <= fc.values + 1.96 * resid)))
    out["forecast_backtest"] = {"train_months": int(len(train)), "test_months": 12,
                                "mae": round(mae, 3), "rmse": round(rmse, 3), "mape_pct": round(mape, 3),
                                "naive_last_value_mae": round(naive, 3), "interval_coverage_95": round(cover, 3),
                                "note": "Synthetic series (scripts/forecast.py); back-test measures the method, not real-world accuracy."}
    (ROOT / "artifacts" / "report_metrics.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
