"""SentinelFlow standalone evaluation (reloads persisted model and test features)."""

import json
import os
import sys

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.features import FEATURE_COLUMNS  # noqa: E402

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    model_path = os.path.join(BASE_DIR, "models", "sentinelflow_rf.joblib")
    test_path = os.path.join(BASE_DIR, "data", "processed", "test_features.csv")
    if not os.path.exists(model_path):
        raise SystemExit("Model not found. Run: python ml/train_model.py")
    if not os.path.exists(test_path):
        raise SystemExit("Test features not found. Run: python ml/train_model.py")
    clf = joblib.load(model_path)
    df = pd.read_csv(test_path)
    X = df[FEATURE_COLUMNS]
    y = df["label"].values
    pred = clf.predict(X)
    try:
        score = clf.predict_proba(X)[:, 1]
        auc = float(roc_auc_score(y, score))
    except Exception:
        auc = None
    print("Accuracy : %.4f" % accuracy_score(y, pred))
    print("Precision: %.4f" % precision_score(y, pred, zero_division=0))
    print("Recall   : %.4f" % recall_score(y, pred, zero_division=0))
    print("F1       : %.4f" % f1_score(y, pred, zero_division=0))
    print("ROC-AUC  : %s" % (("%.4f" % auc) if auc is not None else "n/a"))
    print(classification_report(y, pred, target_names=["Benign", "Attack"]))
    print("Confusion matrix:")
    print(confusion_matrix(y, pred))


if __name__ == "__main__":
    main()
