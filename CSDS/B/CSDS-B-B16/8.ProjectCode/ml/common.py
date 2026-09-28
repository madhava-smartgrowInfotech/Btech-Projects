"""Shared helpers for training and evaluation scripts."""
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import confusion_matrix, f1_score, roc_auc_score, roc_curve

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

RAW = ROOT / "data" / "raw"
SEED = 42


def hr_label_csv() -> Path:
    hits = list(RAW.glob("hr/**/2-Groundtruths/*.csv"))
    if not hits:
        raise SystemExit("Retinopathy dataset not found. Run: python scripts/download_data.py")
    return hits[0]


def hr_image_dir() -> Path:
    return next(RAW.glob("hr/**/1-Images/1-Training Set"))


def binary_metrics(y_true, prob, threshold: float = 0.5) -> dict:
    y_true = np.asarray(y_true).astype(int)
    prob = np.asarray(prob, dtype=float)
    pred = (prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    fpr, tpr, _ = roc_curve(y_true, prob)
    idx = np.unique(np.linspace(0, len(fpr) - 1, min(len(fpr), 60)).astype(int))
    return {
        "n": int(len(y_true)),
        "threshold": round(float(threshold), 4),
        "accuracy": round(float((tp + tn) / len(y_true)), 4),
        "sensitivity": round(float(tp / (tp + fn)) if tp + fn else 0.0, 4),
        "specificity": round(float(tn / (tn + fp)) if tn + fp else 0.0, 4),
        "precision": round(float(tp / (tp + fp)) if tp + fp else 0.0, 4),
        "f1": round(float(f1_score(y_true, pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, prob)), 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "roc_curve": {"fpr": [round(float(v), 4) for v in fpr[idx]], "tpr": [round(float(v), 4) for v in tpr[idx]]},
    }


def youden_threshold(y_true, prob) -> float:
    fpr, tpr, thr = roc_curve(y_true, prob)
    i = int(np.argmax(tpr - fpr))
    return float(min(max(thr[i], 0.05), 0.95))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
