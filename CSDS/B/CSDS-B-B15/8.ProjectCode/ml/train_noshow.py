"""Train the calibrated no-show model used for overbooking-aware slot allocation.

Gradient-boosted trees + isotonic calibration on the Medical Appointment No Shows dataset.
Saves models/noshow_model.joblib and experiments/noshow_metrics.json.
"""
import json

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split

from common import EXPERIMENTS, MODELS, NOSHOW_FEATURES, load_noshow

SEED = 42


def ece(y, p, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & (p < hi)
        if m.any():
            total += m.mean() * abs(y[m].mean() - p[m].mean())
    return float(total)


def main():
    df = load_noshow()
    X, y = df[NOSHOW_FEATURES], df["no_show"].values
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=SEED, stratify=y)

    base = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08, max_depth=6, random_state=SEED)
    base.fit(Xtr, ytr)
    p_raw = base.predict_proba(Xte)[:, 1]

    model = CalibratedClassifierCV(
        HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08, max_depth=6, random_state=SEED),
        method="isotonic", cv=3)
    model.fit(Xtr, ytr)
    p = model.predict_proba(Xte)[:, 1]

    metrics = {
        "model": "HistGradientBoosting + isotonic calibration",
        "n_train": int(len(ytr)), "n_test": int(len(yte)),
        "base_no_show_rate": round(float(y.mean()), 4),
        "roc_auc": round(roc_auc_score(yte, p), 4),
        "brier_uncalibrated": round(brier_score_loss(yte, p_raw), 4),
        "brier_calibrated": round(brier_score_loss(yte, p), 4),
        "ece_uncalibrated": round(ece(yte, p_raw), 4),
        "ece_calibrated": round(ece(yte, p), 4),
        "features": NOSHOW_FEATURES,
    }
    joblib.dump({"model": model, "features": NOSHOW_FEATURES, "base_rate": float(y.mean())},
                MODELS / "noshow_model.joblib")
    (EXPERIMENTS / "noshow_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
