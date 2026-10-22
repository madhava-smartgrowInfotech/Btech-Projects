"""
Decision-threshold sweep of the shipped success model (logistic regression) on the held-out synthetic test split.

    python scripts/threshold_sweep.py            # project .venv; writes experiments/threshold_sweep.json

The data are re-generated with the shipped seed (42) and split exactly as train_pipeline.py does, the model is
re-fitted with the same settings, and the sweep is checked against the shipped confusion matrix at threshold 0.5.
The shipped artefacts are not modified.
"""
import json
import os
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import train_pipeline as tp  # noqa: E402


def main():
    df, source = tp.acquire_data()
    tr, va, te = tp.split_learners(df)
    sc = StandardScaler().fit(tr[tp.FEATURES].values)
    m = LogisticRegression(max_iter=1000).fit(sc.transform(tr[tp.FEATURES].values), tr["success"].values)
    p = m.predict_proba(sc.transform(te[tp.FEATURES].values))[:, 1]
    y = te["success"].values
    rows = []
    for t in (0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70):
        pred = (p >= t).astype(int)
        tn, fp, fn, tpos = confusion_matrix(y, pred, labels=[0, 1]).ravel()
        rows.append({"threshold": t, "predicted_positive": int(pred.sum()), "accuracy": round(float(accuracy_score(y, pred)), 4),
                     "precision": round(float(precision_score(y, pred, zero_division=0)), 4), "recall": round(float(recall_score(y, pred)), 4),
                     "f1": round(float(f1_score(y, pred)), 4), "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tpos)})
    at50 = [r for r in rows if r["threshold"] == 0.5][0]
    shipped = json.load(open(os.path.join(ROOT, "artifacts", "metrics", "model_metrics.json")))["models"]["logistic_regression"]["confusion_matrix"]
    ok = [[at50["tn"], at50["fp"]], [at50["fn"], at50["tp"]]] == shipped
    out = {"dataset_source": source, "test_rows": int(len(y)), "positive_rate": round(float(y.mean()), 4), "model": "logistic_regression",
           "matches_shipped_confusion_at_0.5": bool(ok), "sweep": rows, "mean_predicted_probability": round(float(p.mean()), 4),
           "min_probability": round(float(p.min()), 4), "max_probability": round(float(p.max()), 4)}
    with open(os.path.join(ROOT, "experiments", "threshold_sweep.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("matches shipped confusion:", ok)
    for r in rows:
        print(r["threshold"], r["accuracy"], r["precision"], r["recall"], r["f1"], r["predicted_positive"])


if __name__ == "__main__":
    main()
