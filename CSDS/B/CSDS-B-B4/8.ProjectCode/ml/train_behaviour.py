"""M1 - behaviour fraud model on the Digital Payment Fraud Detection Benchmark.

Strict time-based validation: fit on Jan-Aug 2023, tune on Sep 2023, test on Oct-Dec 2023
(the dataset's own held-out file). Compares Logistic Regression, Random Forest, XGBoost and a
contrastive + attention network; XGBoost is deployed. Run:  venv\\Scripts\\python ml\\train_behaviour.py
"""
from __future__ import annotations

import argparse
import shutil

import joblib
import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from common import (
    DATA_RAW,
    MODELS,
    SEED,
    Experiment,
    best_f1_threshold,
    classification_metrics,
    plot_bars,
    plot_calibration,
    plot_confusion,
    plot_pr_roc,
    run_name,
)
from app.ml.features import M1_FEATURES, M1_LABELS, m1_frame_from_benchmark  # noqa: E402

FULL_EXTRA = ["ip_risk_score", "credit_score_band", "kyc_level"]
GPS_MASK_SHARE = 0.5  # half the training rows lose GPS distance, like sandbox users who do not share location


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    folder = DATA_RAW / "payment_fraud_benchmark"
    train = pd.read_csv(folder / "transactions_train.csv", parse_dates=["transaction_time"])
    test = pd.read_csv(folder / "transactions_test.csv", parse_dates=["transaction_time"])
    return train.sort_values("transaction_time"), test.sort_values("transaction_time")


def main(epochs: int, skip_nn: bool) -> None:
    exp = Experiment(run_name("m1_behaviour"), family="behaviour")
    log = exp.log
    train_all, test = load()
    fit = train_all[train_all.transaction_time < "2023-09-01"]
    val = train_all[train_all.transaction_time >= "2023-09-01"]
    log.info("fit %s rows (%s fraud)  val %s (%s)  test %s (%s)", len(fit), fit.is_fraud.sum(), len(val), val.is_fraud.sum(), len(test), test.is_fraud.sum())

    rng = np.random.default_rng(SEED)
    x_fit = m1_frame_from_benchmark(fit)
    x_fit.loc[rng.random(len(x_fit)) < GPS_MASK_SHARE, "geo_distance_from_last_txn"] = np.nan
    x_val, x_test = m1_frame_from_benchmark(val), m1_frame_from_benchmark(test)
    x_test_nogps = x_test.assign(geo_distance_from_last_txn=np.nan)
    y_fit, y_val, y_test = fit.is_fraud.to_numpy(), val.is_fraud.to_numpy(), test.is_fraud.to_numpy()

    results: dict[str, dict] = {}
    test_scores: dict[str, np.ndarray] = {}

    # --- Logistic Regression ------------------------------------------------
    lr = make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(), LogisticRegression(max_iter=2000, C=0.5))
    lr.fit(x_fit, y_fit)
    # --- Random Forest ------------------------------------------------------
    rf = make_pipeline(
        SimpleImputer(strategy="constant", fill_value=-1),
        RandomForestClassifier(n_estimators=400, min_samples_leaf=25, max_features=0.5, n_jobs=-1, random_state=SEED),
    )
    rf.fit(x_fit, y_fit)
    # --- XGBoost (deployed) -------------------------------------------------
    booster = xgb.XGBClassifier(
        n_estimators=1500,
        learning_rate=0.03,
        max_depth=4,
        min_child_weight=5,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=2.0,
        tree_method="hist",
        eval_metric="aucpr",
        early_stopping_rounds=100,
        random_state=SEED,
        n_jobs=-1,
    )
    booster.fit(x_fit, y_fit, eval_set=[(x_val, y_val)], verbose=False)
    log.info("xgboost best iteration %s", booster.best_iteration)

    models = {"Logistic Regression": lr, "Random Forest": rf, "XGBoost": booster}
    for name, model in models.items():
        s_val = model.predict_proba(x_val)[:, 1]
        thr = best_f1_threshold(y_val, s_val)
        s_test = model.predict_proba(x_test)[:, 1]
        test_scores[name] = s_test
        results[name] = {
            "validation": classification_metrics(y_val, s_val, thr),
            "test": classification_metrics(y_test, s_test, thr),
            "test_without_gps": classification_metrics(y_test, model.predict_proba(x_test_nogps)[:, 1], thr),
        }
        log.info("%-20s val PR-AUC %.4f | test PR-AUC %.4f ROC %.4f F1 %.4f", name, results[name]["validation"]["pr_auc"], results[name]["test"]["pr_auc"], results[name]["test"]["roc_auc"], results[name]["test"]["f1"])

    # --- Contrastive + attention network (reference approach) --------------
    if not skip_nn:
        from contrastive import predict_contrastive, train_contrastive

        imputer = SimpleImputer(strategy="median", add_indicator=True).fit(x_fit)
        scaler = StandardScaler().fit(imputer.transform(x_fit))
        prep = lambda d: scaler.transform(imputer.transform(d)).astype(np.float32)  # noqa: E731
        net = train_contrastive(prep(x_fit), y_fit, prep(x_val), y_val, epochs=epochs, seed=SEED, log=log.info)
        s_val = predict_contrastive(net, prep(x_val))
        thr = best_f1_threshold(y_val, s_val)
        s_test = predict_contrastive(net, prep(x_test))
        test_scores["Contrastive + attention"] = s_test
        results["Contrastive + attention"] = {
            "validation": classification_metrics(y_val, s_val, thr),
            "test": classification_metrics(y_test, s_test, thr),
            "test_without_gps": classification_metrics(y_test, predict_contrastive(net, prep(x_test_nogps)), thr),
        }
        log.info("%-20s val PR-AUC %.4f | test PR-AUC %.4f", "Contrastive+attn", results["Contrastive + attention"]["validation"]["pr_auc"], results["Contrastive + attention"]["test"]["pr_auc"])

    # --- Full-feature reference (not deployable: uses signals the sandbox cannot see) ---
    full_cols = [c for c in train_all.columns if c not in ("transaction_id", "transaction_time", "customer_id", "merchant_id", "is_fraud", "post_auth_risk_score")]

    def full_frame(d: pd.DataFrame) -> pd.DataFrame:
        f = m1_frame_from_benchmark(d)
        for c in FULL_EXTRA:
            f[c] = d[c].astype(float).to_numpy()
        return f

    full = xgb.XGBClassifier(
        n_estimators=1500, learning_rate=0.03, max_depth=4, min_child_weight=5, subsample=0.8, colsample_bytree=0.8,
        tree_method="hist", eval_metric="aucpr", early_stopping_rounds=100, random_state=SEED, n_jobs=-1,
    )
    full.fit(full_frame(fit), y_fit, eval_set=[(full_frame(val), y_val)], verbose=False)
    s_full = full.predict_proba(full_frame(test))[:, 1]
    full_metrics = classification_metrics(y_test, s_full, best_f1_threshold(y_val, full.predict_proba(full_frame(val))[:, 1]))
    log.info("full-feature XGBoost (reference only) test PR-AUC %.4f", full_metrics["pr_auc"])

    # --- Drift: per-month PR-AUC of the deployed model --------------------
    months = pd.concat([val, test])
    x_months = m1_frame_from_benchmark(months)
    s_months = booster.predict_proba(x_months)[:, 1]
    per_month = {}
    for m, idx in months.groupby(months.transaction_time.dt.strftime("%Y-%m")).indices.items():
        per_month[m] = round(float(average_precision_score(months.is_fraud.to_numpy()[idx], s_months[idx])), 4)
    # Drift check: a model trained only on months 1-5 scored before vs after the month-6 change.
    early = train_all[train_all.transaction_time < "2023-06-01"]
    pre = train_all[(train_all.transaction_time >= "2023-06-01") & (train_all.transaction_time < "2023-07-01")]
    post = train_all[(train_all.transaction_time >= "2023-07-01")]
    drift_model = xgb.XGBClassifier(n_estimators=booster.best_iteration + 1, learning_rate=0.03, max_depth=4, min_child_weight=5, subsample=0.8, colsample_bytree=0.8, tree_method="hist", random_state=SEED, n_jobs=-1)
    drift_model.fit(m1_frame_from_benchmark(early), early.is_fraud)
    drift = {
        "trained_on": "2023-01 to 2023-05",
        "pr_auc_june_before_drift": round(float(average_precision_score(pre.is_fraud, drift_model.predict_proba(m1_frame_from_benchmark(pre))[:, 1])), 4),
        "pr_auc_jul_sep_after_drift": round(float(average_precision_score(post.is_fraud, drift_model.predict_proba(m1_frame_from_benchmark(post))[:, 1])), 4),
    }
    log.info("drift check %s", drift)

    # --- SHAP on the deployed model ---------------------------------------
    sample = x_test.sample(4000, random_state=SEED)
    explainer = shap.TreeExplainer(booster)
    sv = explainer.shap_values(sample)
    # Features that belong together (time of day = sin + cos, device = three flags) are summed per row first.
    importance: dict[str, float] = {}
    grouped: dict[str, np.ndarray] = {}
    for i, f in enumerate(M1_FEATURES):
        grouped[M1_LABELS[f]] = grouped.get(M1_LABELS[f], 0) + sv[:, i]
    importance = {label: float(np.abs(v).mean()) for label, v in grouped.items()}
    plot_bars(importance, "M1 behaviour model - mean |SHAP|", "Mean absolute SHAP value (log-odds)", exp.path("shap_importance.png"))
    import matplotlib.pyplot as plt

    shap.summary_plot(sv, sample, feature_names=M1_FEATURES, show=False, max_display=15)
    plt.gcf().set_size_inches(7.5, 6)
    plt.tight_layout()
    plt.savefig(exp.path("shap_summary.png"))
    plt.close("all")

    # --- Plots ------------------------------------------------------------
    plot_pr_roc({k: (y_test, v) for k, v in test_scores.items()}, "M1 behaviour (test Oct-Dec 2023)", exp.path("pr_curve.png"), exp.path("roc_curve.png"))
    plot_confusion(results["XGBoost"]["test"]["confusion"], "M1 XGBoost - test confusion matrix", exp.path("confusion_matrix.png"))
    plot_calibration(y_test, test_scores["XGBoost"], "M1 XGBoost", exp.path("calibration.png"))
    plot_bars(per_month, "M1 XGBoost - PR-AUC by month", "PR-AUC", exp.path("pr_auc_by_month.png"))

    # --- Save -------------------------------------------------------------
    deployed = results["XGBoost"]
    version = f"m1-xgb-{exp.name.split('_')[-1]}"
    bundle = {
        "version": version,
        "model": booster,
        "features": M1_FEATURES,
        "labels": M1_LABELS,
        "threshold": deployed["validation"]["threshold"],
        "base_value": float(explainer.expected_value),
        "metrics": {"test": deployed["test"], "validation": deployed["validation"]},
        "run": exp.name,
    }
    joblib.dump(bundle, exp.path("behaviour_model.joblib"), compress=3)
    MODELS.mkdir(exist_ok=True)
    shutil.copy(exp.path("behaviour_model.joblib"), MODELS / "behaviour_model.joblib")

    exp.save_metrics(
        {
            "model": "M1 behaviour fraud model",
            "deployed": "XGBoost",
            "version": version,
            "dataset": {
                "name": "Digital Payment Fraud Detection Benchmark (Kaggle, CC0-1.0)",
                "split": "time-based: fit 2023-01-01..2023-08-31, validation 2023-09, test 2023-10-01..2023-12-30 (provided test file)",
                "rows": {"fit": len(fit), "validation": len(val), "test": len(test)},
                "fraud_rate": {"fit": round(float(y_fit.mean()), 5), "validation": round(float(y_val.mean()), 5), "test": round(float(y_test.mean()), 5)},
                "gps_masked_share_in_training": GPS_MASK_SHARE,
            },
            "features": M1_FEATURES,
            "excluded_features": {"post_auth_risk_score": "target leakage", **{c: "not observable in the sandbox" for c in FULL_EXTRA + ["payment_channel"]}},
            "threshold_rule": "maximum F1 on the validation month",
            "models": results,
            "full_feature_reference": {"features": full_cols, "test": full_metrics},
            "pr_auc_by_month": per_month,
            "drift_check": drift,
            "shap_mean_abs": importance,
            "xgboost_best_iteration": int(booster.best_iteration),
            "plots": ["pr_curve.png", "roc_curve.png", "confusion_matrix.png", "calibration.png", "shap_importance.png", "shap_summary.png", "pr_auc_by_month.png"],
        }
    )
    log.info("done in %s", exp.directory)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--skip-nn", action="store_true", help="skip the contrastive network comparison")
    args = ap.parse_args()
    main(args.epochs, args.skip_nn)
