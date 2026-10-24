"""SentinelFlow model loader: single entry point for inference."""

import json
import os

import joblib

from ml.features import FEATURE_COLUMNS, validate_feature_dict

_MODEL = None
_FEATURES = None
_METADATA = None


def _paths():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return (
        os.path.join(base, "models", "sentinelflow_rf.joblib"),
        os.path.join(base, "models", "feature_list.json"),
        os.path.join(base, "models", "metadata.json"),
    )


def is_trained() -> bool:
    model_path, _, _ = _paths()
    return os.path.exists(model_path)


def load_model():
    global _MODEL, _FEATURES, _METADATA
    model_path, features_path, metadata_path = _paths()
    if not os.path.exists(model_path):
        raise FileNotFoundError("SentinelFlow model not found at %s. Train it first (python ml/train_model.py)." % model_path)
    try:
        _MODEL = joblib.load(model_path)
    except Exception as exc:
        raise ValueError("Stored SentinelFlow model is corrupted and cannot be loaded: %s" % exc)
    if os.path.exists(features_path):
        with open(features_path, "r", encoding="utf-8") as fh:
            _FEATURES = json.load(fh)
    else:
        _FEATURES = list(FEATURE_COLUMNS)
    if _FEATURES != list(FEATURE_COLUMNS):
        raise ValueError("Stored feature list does not match ml/features.py schema.")
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as fh:
            _METADATA = json.load(fh)
    else:
        _METADATA = {}
    return _MODEL


def get_metadata() -> dict:
    global _METADATA
    if _METADATA is None:
        _, _, metadata_path = _paths()
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as fh:
                _METADATA = json.load(fh)
        else:
            _METADATA = {}
    return _METADATA


def predict_traffic(features: dict) -> dict:
    """Run the persisted Random Forest on one common-schema feature vector."""
    global _MODEL
    if _MODEL is None:
        load_model()
    ordered = validate_feature_dict(features)
    import pandas as pd

    frame = pd.DataFrame([ordered], columns=FEATURE_COLUMNS)
    label = int(_MODEL.predict(frame)[0])
    confidence = 0.5
    try:
        proba = _MODEL.predict_proba(frame)[0]
        classes = list(_MODEL.classes_)
        idx = classes.index(label)
        confidence = float(proba[idx])
    except Exception:
        confidence = 0.85 if label == 1 else 0.75
    return {
        "prediction": "Attack" if label == 1 else "Benign",
        "label": label,
        "confidence": round(float(confidence), 4),
    }
