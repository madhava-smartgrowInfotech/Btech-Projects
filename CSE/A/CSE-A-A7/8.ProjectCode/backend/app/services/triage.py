"""Triage model inference: calibrated priority + per-patient SHAP attribution."""
import time
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .features import FEATURES, PRIORITY_NAMES, fuse, label_for, risk_level

MODEL_PATH = Path(__file__).resolve().parents[3] / "models" / "triage_model.joblib"


@lru_cache(maxsize=1)
def _bundle():
    if not MODEL_PATH.exists():
        raise RuntimeError("Model not trained yet. Run: python ml/train.py")
    bundle = joblib.load(MODEL_PATH)
    import shap
    bundle["explainer"] = shap.TreeExplainer(bundle["base"])
    return bundle


def _display(name, value):
    if name == "arrival_code":
        return {0: "walk-in", 1: "transfer", 2: "ambulance"}.get(int(value), "walk-in")
    if name in ("temp_c",):
        return f"{value:.1f}"
    if float(value) in (0.0, 1.0) and name not in ("age",) and name not in ("spo2",):
        return "present" if value else "absent"
    return f"{value:g}"


def predict(vitals: dict, flags: dict, top: int = 8) -> dict:
    t0 = time.time()
    b = _bundle()
    row = fuse(vitals, flags)
    X = pd.DataFrame([row])[FEATURES]
    proba = b["calibrated"].predict_proba(X)[0]
    cls = int(np.argmax(proba))
    sv = b["explainer"].shap_values(X)
    # shap returns list per class or (n, features, classes) depending on version
    if isinstance(sv, list):
        contrib = np.asarray(sv[cls])[0]
    else:
        arr = np.asarray(sv)
        contrib = arr[0, :, cls] if arr.ndim == 3 else arr[0]
    order = np.argsort(-np.abs(contrib))
    shap_items = []
    for i in order:
        name = FEATURES[i]
        is_flag = name not in ("age", "heart_rate", "sbp", "dbp", "spo2", "temp_c", "resp_rate", "arrival_code")
        if is_flag and row[name] == 0 and abs(contrib[i]) < 0.15:
            continue
        shap_items.append({
            "feature": name, "label": label_for(name), "value": _display(name, row[name]),
            "impact": round(float(contrib[i]), 4),
            "direction": "raises urgency" if contrib[i] > 0 else "lowers urgency",
        })
        if len(shap_items) >= top:
            break
    priority = cls + 1
    return {
        "priority": priority,
        "priority_name": PRIORITY_NAMES[priority],
        "risk_level": risk_level(priority),
        "confidence": round(float(proba[cls]), 4),
        "probabilities": {str(i + 1): round(float(p), 4) for i, p in enumerate(proba)},
        "shap": shap_items,
        "fused": row,
        "seconds": round(time.time() - t0, 4),
    }
