"""
evaluation.py
--------------
Computes classification metrics and curve data (confusion matrix, ROC,
precision-recall) for a trained model on a held-out test set.
"""

from __future__ import annotations
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix, roc_curve, precision_recall_curve,
)


def evaluate_model(model, X_test, y_test) -> dict:
    y_pred = model.predict(X_test)
    if hasattr(model, "predict_proba"):
        y_proba = model.predict_proba(X_test)[:, 1]
    else:
        # fall back for models without predict_proba (shouldn't happen here)
        y_proba = y_pred.astype(float)

    cm = confusion_matrix(y_test, y_pred)
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    prec_curve, rec_curve, _ = precision_recall_curve(y_test, y_proba)

    return {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1_score": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_proba) if len(np.unique(y_test)) > 1 else float("nan"),
        "confusion_matrix": cm,
        "roc_curve": (fpr, tpr),
        "pr_curve": (prec_curve, rec_curve),
        "y_pred": y_pred,
        "y_proba": y_proba,
    }


def results_to_table(results: dict):
    """Convert the {model_name: metrics_dict} results into a tidy
    pandas DataFrame suitable for st.dataframe."""
    import pandas as pd
    rows = []
    for name, m in results.items():
        rows.append({
            "Model": name,
            "Accuracy": round(m["accuracy"], 4),
            "Precision": round(m["precision"], 4),
            "Recall": round(m["recall"], 4),
            "F1-Score": round(m["f1_score"], 4),
            "ROC-AUC": round(m["roc_auc"], 4) if not np.isnan(m["roc_auc"]) else None,
        })
    return pd.DataFrame(rows).sort_values("F1-Score", ascending=False).reset_index(drop=True)
