"""Train the triage model: XGBoost + isotonic calibration, evaluate on a held-out split.

Writes models/triage_model.joblib and experiments/metrics.json.
"""
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, recall_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.features import FEATURES  # noqa: E402
sys.path.insert(0, str(ROOT / "ml"))
from make_data import generate  # noqa: E402

SEED = 7307


def main():
    csv = ROOT / "data" / "sample" / "triage_synthetic.csv"
    df = pd.read_csv(csv) if csv.exists() else generate()
    X, y = df[FEATURES], df["priority"] - 1
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)
    X_fit, X_cal, y_fit, y_cal = train_test_split(X_tr, y_tr, test_size=0.2, stratify=y_tr, random_state=SEED)

    base = XGBClassifier(n_estimators=220, max_depth=4, learning_rate=0.1, subsample=0.9, colsample_bytree=0.9,
                         objective="multi:softprob", eval_metric="mlogloss", random_state=SEED, n_jobs=4)
    t0 = time.time()
    base.fit(X_fit, y_fit)
    train_s = time.time() - t0
    cal = CalibratedClassifierCV(FrozenEstimator(base), method="isotonic")
    cal.fit(X_cal, y_cal)

    t0 = time.time()
    proba = cal.predict_proba(X_te)
    per_patient = (time.time() - t0) / len(X_te)
    pred = proba.argmax(1)
    labels = [0, 1, 2, 3, 4]
    recall = recall_score(y_te, pred, labels=labels, average=None, zero_division=0)
    within_one = float((np.abs(pred - y_te.to_numpy()) <= 1).mean())
    metrics = {
        "data": "synthetic (data/sample/triage_synthetic.csv, seeded by ml/make_data.py)",
        "n_train": int(len(X_fit)), "n_calibration": int(len(X_cal)), "n_test": int(len(X_te)),
        "accuracy": round(float(accuracy_score(y_te, pred)), 4),
        "within_one_priority": round(within_one, 4),
        "macro_f1": round(float(f1_score(y_te, pred, average="macro")), 4),
        "per_class_recall": {str(i + 1): round(float(r), 4) for i, r in enumerate(recall)},
        "support": {str(i + 1): int((y_te == i).sum()) for i in labels},
        "confusion_matrix": confusion_matrix(y_te, pred, labels=labels).tolist(),
        "mean_confidence": round(float(proba.max(1).mean()), 4),
        "model_seconds_per_patient": round(per_patient, 6),
        "train_seconds": round(train_s, 2),
    }
    (ROOT / "models").mkdir(exist_ok=True)
    (ROOT / "experiments").mkdir(exist_ok=True)
    joblib.dump({"base": base, "calibrated": cal, "features": FEATURES}, ROOT / "models" / "triage_model.joblib")
    (ROOT / "experiments" / "metrics.json").write_text(json.dumps(metrics, indent=2))
    # hold-out rows used to seed the demo queue
    te = df.loc[X_te.index].copy()
    te.head(40).to_csv(ROOT / "data" / "sample" / "holdout_sample.csv", index=False)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
