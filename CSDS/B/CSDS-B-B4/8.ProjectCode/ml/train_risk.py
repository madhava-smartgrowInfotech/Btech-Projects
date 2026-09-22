"""M3 - payment risk model (the 0-100 score users see before confirming a payment).

Trained on the seeded UPI scenario simulator (ml/simulator.py), which uses the real M1 and M2
models for its behaviour and SMS signals. Time-based split: months 1-9 train, month 10
validation (threshold tuning), months 11-12 test. Compares Logistic Regression, Random Forest
and XGBoost (monotonic constraints); XGBoost + SHAP is deployed.
Run: venv\\Scripts\\python ml\\train_risk.py [--regenerate]
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
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from common import (
    DATA_PROCESSED,
    DATA_SAMPLE,
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
    threshold_for_precision,
    threshold_for_recall,
    write_json,
)
from app.ml.features import RISK_FEATURES, RISK_MONOTONE  # noqa: E402

SCENARIOS = DATA_PROCESSED / "upi_scenarios.csv.gz"
MEDIUM_SCORE, HIGH_SCORE = 35, 70
MEDIUM_FRICTION, HIGH_FRICTION = 0.08, 0.005


def load_or_simulate(regenerate: bool, n_users: int, log) -> pd.DataFrame:
    if SCENARIOS.exists() and not regenerate:
        log.info("loading cached scenarios %s", SCENARIOS.name)
        return pd.read_csv(SCENARIOS, parse_dates=["timestamp"])
    from simulator import simulate

    log.info("simulating %d users for 12 months (seed %d)", n_users, SEED)
    df = simulate(joblib.load(MODELS / "behaviour_model.joblib"), joblib.load(MODELS / "sms_model.joblib"), seed=SEED, n_users=n_users)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(SCENARIOS, index=False, compression="gzip")
    DATA_SAMPLE.mkdir(parents=True, exist_ok=True)
    sample = pd.concat([df[df.label == 1].sample(1000, random_state=SEED), df[df.label == 0].sample(4000, random_state=SEED)]).sort_values("timestamp")
    sample.to_csv(DATA_SAMPLE / "upi_scenarios_sample.csv", index=False)
    return df


def score_map(p: np.ndarray, t_med: float, t_high: float) -> np.ndarray:
    """Piecewise-linear 0-100 scale anchored so the tuned thresholds land on 35 and 70."""
    p = np.asarray(p, dtype=float)
    return np.where(
        p < t_med,
        MEDIUM_SCORE * p / t_med,
        np.where(p < t_high, MEDIUM_SCORE + (HIGH_SCORE - MEDIUM_SCORE) * (p - t_med) / (t_high - t_med), HIGH_SCORE + (100 - HIGH_SCORE) * (p - t_high) / (1 - t_high)),
    )


def main(regenerate: bool, n_users: int) -> None:
    exp = Experiment(run_name("m3_risk"), family="risk")
    log = exp.log
    df = load_or_simulate(regenerate, n_users, log)
    df["month"] = df.timestamp.dt.month
    log.info("%d payments, %d scam payments (%.2f%%), %d label-noise flips", len(df), df.label.sum(), 100 * df.label.mean(), df.label_noise.sum())
    log.info("scam mix: %s", df[df.label == 1].scam_type.value_counts().to_dict())

    train, val, test = df[df.month <= 9], df[df.month == 10], df[df.month >= 11]
    X = lambda d: d[RISK_FEATURES]  # noqa: E731
    y_tr, y_va, y_te = train.label.to_numpy(), val.label.to_numpy(), test.label.to_numpy()
    log.info("train %d (%d scam)  val %d (%d)  test %d (%d)", len(train), y_tr.sum(), len(val), y_va.sum(), len(test), y_te.sum())

    lr = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=1.0))
    rf = RandomForestClassifier(n_estimators=400, min_samples_leaf=10, max_features=0.5, n_jobs=-1, random_state=SEED)
    booster = xgb.XGBClassifier(
        n_estimators=2000,
        learning_rate=0.04,
        max_depth=5,
        min_child_weight=3,
        subsample=0.85,
        colsample_bytree=0.8,
        reg_lambda=1.5,
        tree_method="hist",
        monotone_constraints=tuple(RISK_MONOTONE[f] for f in RISK_FEATURES),
        eval_metric="aucpr",
        early_stopping_rounds=120,
        random_state=SEED,
        n_jobs=-1,
    )
    lr.fit(X(train), y_tr)
    rf.fit(X(train), y_tr)
    booster.fit(X(train), y_tr, eval_set=[(X(val), y_va)], verbose=False)
    log.info("xgboost best iteration %d", booster.best_iteration)

    results, test_scores = {}, {}
    for name, model in {"Logistic Regression": lr, "Random Forest": rf, "XGBoost": booster}.items():
        s_va = model.predict_proba(X(val))[:, 1]
        s_te = model.predict_proba(X(test))[:, 1]
        thr = best_f1_threshold(y_va, s_va)
        results[name] = {"validation": classification_metrics(y_va, s_va, thr), "test": classification_metrics(y_te, s_te, thr)}
        test_scores[name] = s_te
        log.info("%-20s val PR-AUC %.4f | test PR-AUC %.4f ROC %.4f P %.3f R %.3f F1 %.4f", name, results[name]["validation"]["pr_auc"], results[name]["test"]["pr_auc"], results[name]["test"]["roc_auc"], results[name]["test"]["precision"], results[name]["test"]["recall"], results[name]["test"]["f1"])

    # Ablation: how much each signal group adds (XGBoost refit without the group).
    groups = {
        "without SMS signals": ["sms_scam_prob", "sms_recent_scam"],
        "without payee trust signals": ["payee_account_age_days", "payee_reports", "payee_distinct_payers_24h", "payee_new_payer_share_7d", "payee_collects_7d", "payee_is_merchant"],
        "without history signals": ["is_new_payee", "payee_times_paid", "is_saved_contact"],
        "without M1 behaviour score": ["behaviour_score"],
        "without collect/QR guard signals": ["channel_collect", "channel_qr", "collect_note_score", "qr_flag"],
    }
    ablation = {}
    for label, drop in groups.items():
        cols = [c for c in RISK_FEATURES if c not in drop]
        m = xgb.XGBClassifier(
            n_estimators=booster.best_iteration + 1, learning_rate=0.04, max_depth=5, min_child_weight=3, subsample=0.85, colsample_bytree=0.8,
            reg_lambda=1.5, tree_method="hist", monotone_constraints=tuple(RISK_MONOTONE[f] for f in cols), random_state=SEED, n_jobs=-1,
        )
        m.fit(train[cols], y_tr)
        s = m.predict_proba(test[cols])[:, 1]
        ablation[label] = classification_metrics(y_te, s, best_f1_threshold(y_va, m.predict_proba(val[cols])[:, 1]))["pr_auc"]
        log.info("ablation %-34s test PR-AUC %.4f", label, ablation[label])
    ablation["all signals (deployed)"] = results["XGBoost"]["test"]["pr_auc"]

    # Policy with friction budgets (validation month only):
    #   Medium (intent check) - aim for 92% scam recall, but never ask on more than 8% of genuine payments.
    #   High (hold)           - at least 60% precision, and hold no more than 0.5% of genuine payments.
    s_va = booster.predict_proba(X(val))[:, 1]
    genuine_va = s_va[y_va == 0]
    t_med = max(threshold_for_recall(y_va, s_va, 0.92), float(np.quantile(genuine_va, 1 - MEDIUM_FRICTION)))
    t_high = max(t_med * 1.5, threshold_for_precision(y_va, s_va, 0.60), float(np.quantile(genuine_va, 1 - HIGH_FRICTION)))
    t_high = min(t_high, 0.97)
    log.info("policy probabilities: medium >= %.4f, high >= %.4f", t_med, t_high)
    s_te = test_scores["XGBoost"]
    score_te = score_map(s_te, t_med, t_high)
    level = np.where(score_te >= HIGH_SCORE, "high", np.where(score_te >= MEDIUM_SCORE, "medium", "low"))
    t2 = test.assign(level=level, score=score_te)
    policy_eval = {
        "scams_reaching_medium_or_high": round(float((t2[t2.label == 1].level != "low").mean()), 4),
        "scams_reaching_high_hold": round(float((t2[t2.label == 1].level == "high").mean()), 4),
        "genuine_payments_low": round(float((t2[t2.label == 0].level == "low").mean()), 4),
        "genuine_payments_asked_intent_medium": round(float((t2[t2.label == 0].level == "medium").mean()), 4),
        "genuine_payments_held_high": round(float((t2[t2.label == 0].level == "high").mean()), 4),
        "precision_of_high": round(float(t2[t2.level == "high"].label.mean()), 4) if (t2.level == "high").any() else None,
        "level_share": t2.level.value_counts(normalize=True).round(4).to_dict(),
    }
    per_type = (
        t2[t2.label == 1]
        .groupby("scam_type")
        .apply(lambda g: pd.Series({"n": len(g), "caught_medium_or_high": round(float((g.level != "low").mean()), 3), "held_high": round(float((g.level == "high").mean()), 3)}), include_groups=False)
        .to_dict(orient="index")
    )
    log.info("policy on test: %s", policy_eval)
    log.info("per scam type: %s", per_type)

    # SHAP.
    explainer = shap.TreeExplainer(booster)
    sample = X(test).sample(5000, random_state=SEED)
    sv = explainer.shap_values(sample)
    importance = {f: float(np.abs(sv[:, i]).mean()) for i, f in enumerate(RISK_FEATURES)}
    plot_bars(importance, "M3 risk model - mean |SHAP|", "Mean absolute SHAP value (log-odds)", exp.path("shap_importance.png"))
    import matplotlib.pyplot as plt

    shap.summary_plot(sv, sample, feature_names=RISK_FEATURES, show=False, max_display=18)
    plt.gcf().set_size_inches(7.5, 7)
    plt.tight_layout()
    plt.savefig(exp.path("shap_summary.png"))
    plt.close("all")

    plot_pr_roc({k: (y_te, v) for k, v in test_scores.items()}, "M3 risk (test months 11-12)", exp.path("pr_curve.png"), exp.path("roc_curve.png"))
    plot_confusion(classification_metrics(y_te, s_te, t_high)["confusion"], "M3 at the High (hold) threshold", exp.path("confusion_matrix.png"), labels=("Genuine", "Scam"))
    plot_calibration(y_te, s_te, "M3 XGBoost", exp.path("calibration.png"))
    plot_bars({k: v["caught_medium_or_high"] for k, v in per_type.items()}, "M3 - share of scams stopped for a check, by type", "Share at Medium or High", exp.path("recall_by_scam_type.png"))
    plot_bars(ablation, "M3 - test PR-AUC with signal groups removed", "PR-AUC", exp.path("ablation.png"))

    version = f"m3-xgb-{exp.name.split('_')[-1]}"
    bundle = {
        "version": version,
        "model": booster,
        "features": RISK_FEATURES,
        "monotone": RISK_MONOTONE,
        "score_anchors": {"t_medium": float(t_med), "t_high": float(t_high), "medium_score": MEDIUM_SCORE, "high_score": HIGH_SCORE},
        "base_value": float(explainer.expected_value),
        "metrics": {"test": results["XGBoost"]["test"], "policy": policy_eval},
        "run": exp.name,
    }
    joblib.dump(bundle, exp.path("risk_model.joblib"), compress=3)
    shutil.copy(exp.path("risk_model.joblib"), MODELS / "risk_model.joblib")
    policy = {
        "medium": MEDIUM_SCORE,
        "high": HIGH_SCORE,
        "block_report_score": 2.5,
        "probability_anchors": {"medium": round(float(t_med), 5), "high": round(float(t_high), 5)},
        "tuned_on": "validation month 10 of the scenario simulator: Medium = 92% scam recall capped at 8% of genuine payments; High = 60% precision capped at 0.5% of genuine payments",
        "run": exp.name,
    }
    write_json(MODELS / "risk_policy.json", policy)

    exp.save_metrics(
        {
            "model": "M3 payment risk model",
            "deployed": "XGBoost (monotonic constraints) + SHAP",
            "version": version,
            "dataset": {
                "name": "UPI Guardian scenario simulator (ml/simulator.py), calibrated from UPI Transactions 2024, signals from M1 and M2",
                "file": "data/processed/upi_scenarios.csv.gz (re-created by ml/train_risk.py --regenerate); 5,000-row sample in data/sample/",
                "users": n_users,
                "split": "time-based: months 1-9 train, month 10 validation, months 11-12 test",
                "rows": {"train": len(train), "validation": len(val), "test": len(test)},
                "scam_rate": {"train": round(float(y_tr.mean()), 5), "validation": round(float(y_va.mean()), 5), "test": round(float(y_te.mean()), 5)},
                "scam_mix": df[df.label == 1].scam_type.value_counts().to_dict(),
                "label_noise_share": round(float(df.label_noise.mean()), 5),
            },
            "features": RISK_FEATURES,
            "monotone_constraints": RISK_MONOTONE,
            "models": results,
            "ablation_test_pr_auc": ablation,
            "policy": {"medium_score": MEDIUM_SCORE, "high_score": HIGH_SCORE, "probability_anchors": policy["probability_anchors"], "test": policy_eval},
            "per_scam_type_test": per_type,
            "shap_mean_abs": importance,
            "plots": ["pr_curve.png", "roc_curve.png", "confusion_matrix.png", "calibration.png", "shap_importance.png", "shap_summary.png", "recall_by_scam_type.png", "ablation.png"],
        }
    )
    log.info("done in %s", exp.directory)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--regenerate", action="store_true", help="re-run the scenario simulator")
    ap.add_argument("--users", type=int, default=3000)
    args = ap.parse_args()
    main(args.regenerate, args.users)
