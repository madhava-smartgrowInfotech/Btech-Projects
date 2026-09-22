"""UPI Transactions 2024: (1) checks whether its fraud_flag is learnable, (2) extracts behaviour profiles.

The profiles (hour-of-day curve, amount distributions by category / transaction type, weekend
effect) calibrate the payment simulator and give the risk engine sensible defaults for payers
who have no history yet. Output: models/behaviour_profile.json + experiments/m0_upi2024_<date>/.
Run: venv\\Scripts\\python ml\\profile_upi2024.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder

from common import BRAND, DATA_RAW, MODELS, SEED, Experiment, classification_metrics, plot_bars, plot_pr_roc, run_name, write_json

CATS = ["transaction type", "merchant_category", "sender_age_group", "receiver_age_group", "sender_state", "sender_bank", "receiver_bank", "device_type", "network_type", "day_of_week"]


def main() -> None:
    exp = Experiment(run_name("m0_upi2024"), family="profile")
    log = exp.log
    df = pd.read_csv(DATA_RAW / "upi_transactions_2024" / "upi_transactions_2024.csv", parse_dates=["timestamp"]).sort_values("timestamp")
    log.info("%s rows, fraud_flag rate %.4f (%d positives)", len(df), df.fraud_flag.mean(), df.fraud_flag.sum())

    # ---- 1. Is the label learnable? (time-based split) ------------------------
    train, test = df[df.timestamp < "2024-10-01"], df[df.timestamp >= "2024-10-01"]
    enc = OneHotEncoder(handle_unknown="ignore", min_frequency=20).fit(train[CATS])

    def frame(d: pd.DataFrame) -> np.ndarray:
        num = np.column_stack([np.log1p(d["amount (INR)"]), d.hour_of_day, d.is_weekend, (d.transaction_status == "FAILED").astype(int)])
        return np.hstack([num, enc.transform(d[CATS]).toarray()])

    xtr, xte = frame(train), frame(test)
    lr = LogisticRegression(max_iter=3000, class_weight="balanced").fit(xtr, train.fraud_flag)
    booster = xgb.XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=SEED, n_jobs=-1).fit(xtr, train.fraud_flag)
    s_lr, s_xgb = lr.predict_proba(xte)[:, 1], booster.predict_proba(xte)[:, 1]
    label_check = {
        "split": "train 2024-01..2024-09, test 2024-10..2024-12",
        "rows": {"train": len(train), "test": len(test)},
        "logistic_regression": classification_metrics(test.fraud_flag, s_lr, float(np.quantile(s_lr, 0.99))),
        "xgboost": classification_metrics(test.fraud_flag, s_xgb, float(np.quantile(s_xgb, 0.99))),
        "fraud_rate_by_feature_max_over_min": {
            c: round(float(df.groupby(c).fraud_flag.mean().max() / max(df.groupby(c).fraud_flag.mean().min(), 1e-6)), 2) for c in ["transaction type", "merchant_category", "device_type", "hour_of_day"]
        },
    }
    prevalence = float(test.fraud_flag.mean())
    best_ap = max(label_check["logistic_regression"]["pr_auc"], label_check["xgboost"]["pr_auc"])
    learnable = best_ap > 3 * prevalence
    label_check["conclusion"] = (
        "fraud_flag carries a usable signal" if learnable else
        f"fraud_flag is not learnable (best PR-AUC {best_ap:.4f} vs base rate {prevalence:.4f}); the flag looks randomly assigned, "
        "so this dataset is used only for behaviour profiles, as planned"
    )
    log.info("label check: LR PR-AUC %.4f, XGB PR-AUC %.4f, base rate %.4f -> %s", label_check["logistic_regression"]["pr_auc"], label_check["xgboost"]["pr_auc"], prevalence, label_check["conclusion"])
    plot_pr_roc({"Logistic Regression": (test.fraud_flag.to_numpy(), s_lr), "XGBoost": (test.fraud_flag.to_numpy(), s_xgb)}, "UPI 2024 fraud_flag (test)", exp.path("label_check_pr.png"), exp.path("label_check_roc.png"))

    # ---- 2. Behaviour profiles ---------------------------------------------------
    ok = df[df.transaction_status == "SUCCESS"]
    hour_share = ok.hour_of_day.value_counts(normalize=True).reindex(range(24), fill_value=0).round(5)
    window = {h: round(float(hour_share[[(h - 1) % 24, h, (h + 1) % 24]].sum()), 5) for h in range(24)}

    def lognormal(values: pd.Series) -> dict:
        logs = np.log(values.clip(lower=1))
        return {
            "mu": round(float(logs.mean()), 4),
            "sigma": round(float(logs.std()), 4),
            "p10": round(float(values.quantile(0.1)), 1),
            "p50": round(float(values.median()), 1),
            "p90": round(float(values.quantile(0.9)), 1),
            "p99": round(float(values.quantile(0.99)), 1),
        }

    by_category = {c: lognormal(g["amount (INR)"]) for c, g in ok.groupby("merchant_category")}
    by_type = {c: lognormal(g["amount (INR)"]) for c, g in ok.groupby("transaction type")}
    weekend = {c: round(float(g[g.is_weekend == 1]["amount (INR)"].median() / max(g[g.is_weekend == 0]["amount (INR)"].median(), 1)), 3) for c, g in ok.groupby("merchant_category")}
    profile = {
        "source": "UPI Transactions 2024 (Kaggle, CC0-1.0), successful transactions only",
        "rows": int(len(ok)),
        "hour_share": {str(h): float(v) for h, v in hour_share.items()},
        "hour_window_share": {str(h): v for h, v in window.items()},
        "amount_by_category": by_category,
        "amount_by_type": by_type,
        "weekend_amount_ratio": weekend,
        "type_share": ok["transaction type"].value_counts(normalize=True).round(4).to_dict(),
        "category_share": ok.merchant_category.value_counts(normalize=True).round(4).to_dict(),
        "overall_amount": lognormal(ok["amount (INR)"]),
    }
    write_json(MODELS / "behaviour_profile.json", profile)
    write_json(exp.path("behaviour_profile.json"), profile)
    plot_bars({f"{h:02d}:00": float(v) for h, v in hour_share.items()}, "UPI 2024 - share of payments by hour", "Share of payments", exp.path("hour_profile.png"), color=BRAND["primary"])
    plot_bars({k: v["p50"] for k, v in by_category.items()}, "UPI 2024 - median amount by category (INR)", "Median amount (INR)", exp.path("amount_by_category.png"), color=BRAND["accent"])

    exp.save_metrics(
        {
            "model": "UPI Transactions 2024 label check + behaviour profiles",
            "dataset": {"name": "UPI Transactions 2024 (Kaggle, CC0-1.0)", "rows": len(df), "fraud_rate": round(float(df.fraud_flag.mean()), 5)},
            "label_check": label_check,
            "profile_file": "models/behaviour_profile.json",
            "plots": ["label_check_pr.png", "label_check_roc.png", "hour_profile.png", "amount_by_category.png"],
        }
    )


if __name__ == "__main__":
    main()
