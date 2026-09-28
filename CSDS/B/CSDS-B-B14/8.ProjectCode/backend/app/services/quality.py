"""Water-quality (potability) prediction: stacking ensemble + exact SHAP + guideline checks."""
import threading

import joblib
import numpy as np
import pandas as pd
import shap

from ..config import MODELS

FEATURES = ["ph", "Hardness", "Solids", "Chloramines", "Sulfate", "Conductivity",
            "Organic_carbon", "Trihalomethanes", "Turbidity"]
LABELS = {"ph": "pH", "Hardness": "Hardness", "Solids": "Total dissolved solids", "Chloramines": "Chloramines",
          "Sulfate": "Sulfate", "Conductivity": "Conductivity", "Organic_carbon": "Organic carbon",
          "Trihalomethanes": "Trihalomethanes", "Turbidity": "Turbidity"}
# drinking-water guideline limits (min, max, unit, source)
LIMITS = {
    "ph": (6.5, 8.5, "", "WHO"),
    "Hardness": (None, 300.0, "mg/L", "WHO (scaling above ~200-300)"),
    "Solids": (None, 1000.0, "mg/L", "WHO (palatability)"),
    "Chloramines": (None, 4.0, "mg/L", "WHO / US EPA"),
    "Sulfate": (None, 250.0, "mg/L", "WHO (taste)"),
    "Conductivity": (None, 400.0, "uS/cm", "WHO"),
    "Organic_carbon": (None, 2.0, "mg/L", "US EPA (treated water)"),
    "Trihalomethanes": (None, 80.0, "ug/L", "WHO / US EPA"),
    "Turbidity": (None, 5.0, "NTU", "WHO"),
}
MODEL_PATH = MODELS / "quality_stack.joblib"

_bundle = None
_explainer = None
_lock = threading.Lock()


def bundle():
    global _bundle
    if _bundle is None:
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def _prob_potable(X):
    b = bundle()
    df = pd.DataFrame(np.asarray(X, dtype=float), columns=FEATURES)
    return b["model"].predict_proba(df)[:, 1]


def explainer():
    global _explainer
    if _explainer is None:
        bg = bundle()["background"]
        _explainer = shap.Explainer(_prob_potable, shap.maskers.Independent(bg, max_samples=40), algorithm="exact")
    return _explainer


def check_limits(sample):
    out = []
    for f in FEATURES:
        lo, hi, unit, src = LIMITS[f]
        v = sample.get(f)
        if v is None:
            status = "missing"
        elif (lo is not None and v < lo) or (hi is not None and v > hi):
            status = "exceeds"
        else:
            status = "ok"
        rng = f"{lo}-{hi}" if lo is not None else f"<= {hi}"
        out.append({"parameter": f, "label": LABELS[f], "value": v, "limit": rng, "unit": unit,
                    "source": src, "status": status})
    return out


def predict(sample):
    """sample: dict of the 9 parameters (None allowed -> imputed by the model's median imputer)."""
    b = bundle()
    x = np.array([[np.nan if sample.get(f) is None else float(sample[f]) for f in FEATURES]])
    p = float(_prob_potable(x)[0])
    # SHAP over the whole ensemble; missing values replaced by the training median first
    xi = b["imputer_median"].copy()
    for i, f in enumerate(FEATURES):
        if sample.get(f) is not None:
            xi[i] = float(sample[f])
    with _lock:
        sv = explainer()(xi.reshape(1, -1))
    values = sv.values[0]
    reasons = []
    for i in np.argsort(-np.abs(values)):
        f = FEATURES[i]
        reasons.append({"parameter": f, "label": LABELS[f], "value": float(xi[i]),
                        "shap": round(float(values[i]), 4),
                        "effect": "towards potable" if values[i] > 0 else "towards not potable"})
    potable = p >= 0.5
    members = {}
    df = pd.DataFrame(x, columns=FEATURES)
    model = b["model"]
    imp = model.named_steps["impute"].transform(df)
    for name, est in zip(b["member_names"], model.named_steps["stack"].estimators_):
        members[name] = round(float(est.predict_proba(imp)[0, 1]), 4)
    return {
        "potable": bool(potable),
        "label": "Potable" if potable else "Not potable",
        "probability_potable": round(p, 4),
        "confidence": round(p if potable else 1 - p, 4),
        "base_value": round(float(sv.base_values[0]), 4),
        "reasons": reasons,
        "limits": check_limits({f: (None if sample.get(f) is None else float(sample[f])) for f in FEATURES}),
        "members": members,
    }


def samples():
    return bundle()["presets"]
