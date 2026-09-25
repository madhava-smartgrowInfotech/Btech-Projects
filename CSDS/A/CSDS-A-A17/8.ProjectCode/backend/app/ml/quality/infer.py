from __future__ import annotations

from functools import lru_cache

import joblib
import numpy as np
import shap

from app.core.config import DATA_DIR
from app.ml.quality.feature_extraction import extract_features, features_to_vector


@lru_cache(maxsize=1)
def load_artifact():
    path = DATA_DIR / "quality_model.joblib"
    if not path.exists():
        from app.ml.quality.train_model import train

        return train()
    return joblib.load(path)


@lru_cache(maxsize=1)
def _explainer():
    artifact = load_artifact()
    return shap.TreeExplainer(artifact["model"])


def grade_image(image_bytes: bytes) -> dict:
    artifact = load_artifact()
    model = artifact["model"]
    features = extract_features(image_bytes)
    vector = features_to_vector(features)

    proba = model.predict_proba(vector)[0]
    classes = list(model.classes_)
    grade = classes[int(np.argmax(proba))]
    confidence = float(np.max(proba))
    probabilities = {cls: float(p) for cls, p in zip(classes, proba)}

    explainer = _explainer()
    shap_values = explainer.shap_values(vector)
    class_idx = classes.index(grade)
    if isinstance(shap_values, list):
        contribs = shap_values[class_idx][0]
    else:
        contribs = shap_values[0, :, class_idx]

    shap_explanation = sorted(
        [
            {"feature": name, "contribution": float(val), "value": float(features[name])}
            for name, val in zip(artifact["feature_names"], contribs)
        ],
        key=lambda x: abs(x["contribution"]),
        reverse=True,
    )[:6]

    return {
        "grade": grade,
        "confidence": confidence,
        "probabilities": probabilities,
        "features": features,
        "shap_explanation": {"top_features": shap_explanation},
    }
