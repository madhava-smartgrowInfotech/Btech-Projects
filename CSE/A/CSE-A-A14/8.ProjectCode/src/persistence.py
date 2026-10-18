"""
persistence.py
----------------
Save/load the trained model, preprocessor and metadata to/from the
models/ directory using joblib, so a trained model survives across
Streamlit reruns and app restarts.
"""

from __future__ import annotations
import os
import joblib
import datetime as dt

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")


def save_artifacts(model, preprocessor, metadata: dict):
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(model, os.path.join(MODELS_DIR, "model.pkl"))
    joblib.dump(preprocessor, os.path.join(MODELS_DIR, "preprocessor.pkl"))
    metadata = dict(metadata)
    metadata["saved_at"] = dt.datetime.now().isoformat(timespec="seconds")
    joblib.dump(metadata, os.path.join(MODELS_DIR, "model_metadata.pkl"))
    return metadata


def load_artifacts():
    model_path = os.path.join(MODELS_DIR, "model.pkl")
    pre_path = os.path.join(MODELS_DIR, "preprocessor.pkl")
    meta_path = os.path.join(MODELS_DIR, "model_metadata.pkl")
    if not (os.path.exists(model_path) and os.path.exists(pre_path) and os.path.exists(meta_path)):
        return None, None, None
    model = joblib.load(model_path)
    preprocessor = joblib.load(pre_path)
    metadata = joblib.load(meta_path)
    return model, preprocessor, metadata


def artifacts_exist() -> bool:
    return all(os.path.exists(os.path.join(MODELS_DIR, f)) for f in
               ["model.pkl", "preprocessor.pkl", "model_metadata.pkl"])
