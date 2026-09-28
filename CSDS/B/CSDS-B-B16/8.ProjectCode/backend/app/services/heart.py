"""Heart-disease risk: Random Forest on clinical parameters with SHAP reasons."""
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
import shap

from ..config import MODELS_DIR

MODEL_PATH = MODELS_DIR / "heart_rf.joblib"

FEATURES = ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal"]
LABELS = {
    "age": "Age",
    "sex": "Sex",
    "cp": "Chest pain type",
    "trestbps": "Resting blood pressure",
    "chol": "Serum cholesterol",
    "fbs": "Fasting blood sugar > 120 mg/dl",
    "restecg": "Resting ECG",
    "thalach": "Max heart rate achieved",
    "exang": "Exercise-induced angina",
    "oldpeak": "ST depression (oldpeak)",
    "slope": "ST segment slope",
    "ca": "Major vessels coloured (fluoroscopy)",
    "thal": "Thalassemia test",
}
# Codes as used by the training CSV (mapping to the UCI source is in docs/02_HOW_IT_WORKS.md)
CODES = {
    "sex": {0: "Female", 1: "Male"},
    "cp": {0: "Asymptomatic", 1: "Atypical angina", 2: "Non-anginal pain", 3: "Typical angina"},
    "fbs": {0: "No", 1: "Yes"},
    "restecg": {0: "LV hypertrophy", 1: "Normal", 2: "ST-T abnormality"},
    "exang": {0: "No", 1: "Yes"},
    "slope": {0: "Downsloping", 1: "Flat", 2: "Upsloping"},
    "thal": {0: "Unknown", 1: "Fixed defect", 2: "Normal", 3: "Reversible defect"},
}
UNITS = {"age": " y", "trestbps": " mmHg", "chol": " mg/dl", "thalach": " bpm", "oldpeak": " mm"}
RANGES = {
    "age": (18, 100), "sex": (0, 1), "cp": (0, 3), "trestbps": (80, 220), "chol": (100, 600), "fbs": (0, 1),
    "restecg": (0, 2), "thalach": (60, 220), "exang": (0, 1), "oldpeak": (0, 7), "slope": (0, 2), "ca": (0, 4),
    "thal": (0, 3),
}


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        raise RuntimeError("Heart model not trained yet. Run: python ml/train_heart.py")
    model = joblib.load(MODEL_PATH)
    return model, shap.TreeExplainer(model)


def validate(clinical: dict) -> dict:
    out = {}
    for f in FEATURES:
        if f not in clinical or clinical[f] in ("", None):
            raise ValueError(f"Missing value: {LABELS[f]}")
        try:
            v = float(clinical[f])
        except (TypeError, ValueError):
            raise ValueError(f"{LABELS[f]} must be a number")
        lo, hi = RANGES[f]
        if not lo <= v <= hi:
            raise ValueError(f"{LABELS[f]} must be between {lo} and {hi}")
        out[f] = v
    return out


def display(feature: str, value: float) -> str:
    if feature in CODES:
        return CODES[feature].get(int(value), f"{value:g}")
    return f"{value:g}{UNITS.get(feature, '')}"


def _positive_class_shap(values) -> np.ndarray:
    v = values[1] if isinstance(values, list) else values
    v = np.asarray(v)
    if v.ndim == 3:
        v = v[..., 1]
    return v[0]


def predict(clinical: dict) -> dict:
    model, explainer = load_model()
    vals = validate(clinical)
    X = pd.DataFrame([vals], columns=FEATURES)
    prob = float(model.predict_proba(X)[0, 1])
    sv = _positive_class_shap(explainer.shap_values(X))
    factors = [
        {"feature": f, "label": LABELS[f], "value": vals[f], "display": display(f, vals[f]), "impact": round(float(s), 4),
         "direction": "raises risk" if s > 0 else "lowers risk"}
        for f, s in zip(FEATURES, sv)
    ]
    factors.sort(key=lambda d: abs(d["impact"]), reverse=True)
    return {"probability": prob, "factors": factors[:6], "inputs": vals}
