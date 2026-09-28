"""Train the length-of-stay models and the admissions model (CPU, about a minute).

Temporal split: admissions before day 274 (Jan-Sep) train, Oct-Dec are held out.
Outputs: models/los_regressor.json, models/los_classifier.json, models/arrivals.json, models/los_meta.json,
         experiments/metrics.json
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (accuracy_score, f1_score, mean_absolute_error, mean_squared_error, precision_score,
                             r2_score, recall_score, roc_auc_score)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.config import EXPERIMENTS_DIR, FACILITIES, LONG_STAY_DAYS, MODELS_DIR, OPERATING_DAY, PROCESSED_DIR, WARDS  # noqa: E402
from app.services.engine import (ARRIVAL_FEATURES, FEATURES, HORIZON_MAX, TRAIN_END_DAY, arrival_features,  # noqa: E402
                                 arrival_matrix, los_frame)

SEED = 42


def train_los(p):
    tr, te = p[p.admit_day < TRAIN_END_DAY], p[p.admit_day >= TRAIN_END_DAY]
    Xtr, Xte = los_frame(tr), los_frame(te)
    ytr, yte = tr.lengthofstay.values, te.lengthofstay.values
    params = dict(n_estimators=400, max_depth=6, learning_rate=0.08, subsample=0.9, colsample_bytree=0.9,
                  tree_method="hist", random_state=SEED, n_jobs=-1)
    reg = xgb.XGBRegressor(**params).fit(Xtr, ytr)
    pred = reg.predict(Xte).clip(1, None)
    clf = xgb.XGBClassifier(**params, eval_metric="logloss").fit(Xtr, (ytr > LONG_STAY_DAYS).astype(int))
    prob = clf.predict_proba(Xte)[:, 1]
    ylong = (yte > LONG_STAY_DAYS).astype(int)
    cls = (prob >= 0.5).astype(int)
    metrics = {
        "train_rows": int(len(tr)), "test_rows": int(len(te)),
        "regression": {"mae_days": float(mean_absolute_error(yte, pred)),
                       "rmse_days": float(np.sqrt(mean_squared_error(yte, pred))),
                       "r2": float(r2_score(yte, pred)),
                       "baseline_mean_mae_days": float(mean_absolute_error(yte, np.full(len(yte), ytr.mean())))},
        "classification": {"long_stay_threshold_days": LONG_STAY_DAYS, "accuracy": float(accuracy_score(ylong, cls)),
                           "precision": float(precision_score(ylong, cls)), "recall": float(recall_score(ylong, cls)),
                           "f1": float(f1_score(ylong, cls)), "roc_auc": float(roc_auc_score(ylong, prob)),
                           "long_stay_rate": float(ylong.mean())},
    }
    reg.save_model(MODELS_DIR / "los_regressor.json")
    clf.save_model(MODELS_DIR / "los_classifier.json")
    resid = yte - pred
    imp = sorted(zip(FEATURES, reg.feature_importances_.tolist()), key=lambda t: -t[1])
    meta = {"features": FEATURES, "residual_quantiles": np.quantile(resid, np.linspace(0.005, 0.995, 100)).round(3).tolist(),
            "train_mean_los": float(ytr.mean()), "feature_importance": imp}
    (MODELS_DIR / "los_meta.json").write_text(json.dumps(meta, indent=1))
    return metrics


def arrival_dataset(arr, origins):
    X, y = [], []
    for (f, w), s in arr.items():
        for o in origins:
            X.append(arrival_features(s, o, f, w))
            y.append(s[o + 1: o + 1 + HORIZON_MAX])
    return np.vstack(X), np.concatenate(y)


def train_arrivals(p):
    arr = arrival_matrix(p, OPERATING_DAY)
    train_origins = range(35, TRAIN_END_DAY - HORIZON_MAX)
    test_origins = range(TRAIN_END_DAY, OPERATING_DAY - HORIZON_MAX + 1)
    Xtr, ytr = arrival_dataset(arr, train_origins)
    Xte, yte = arrival_dataset(arr, test_origins)
    model = xgb.XGBRegressor(n_estimators=200, max_depth=4, learning_rate=0.05, objective="count:poisson",
                             tree_method="hist", random_state=SEED, n_jobs=-1).fit(Xtr, ytr)
    pred = model.predict(Xte)
    model.save_model(MODELS_DIR / "arrivals.json")
    naive = Xte[:, ARRIVAL_FEATURES.index("mean_7d")]
    last = Xte[:, ARRIVAL_FEATURES.index("last_day")]
    return {"series": len(FACILITIES) * len(WARDS), "train_samples": int(len(ytr)), "test_samples": int(len(yte)),
            "mae": float(mean_absolute_error(yte, pred)), "naive_7d_mean_mae": float(mean_absolute_error(yte, naive)),
            "naive_last_day_mae": float(mean_absolute_error(yte, last))}


def main():
    t0 = time.time()
    p = pd.read_csv(PROCESSED_DIR / "patients.csv.gz")
    metrics = {"length_of_stay": train_los(p), "admissions": train_arrivals(p)}
    metrics["train_seconds"] = round(time.time() - t0, 1)
    EXPERIMENTS_DIR.mkdir(exist_ok=True)
    (EXPERIMENTS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
