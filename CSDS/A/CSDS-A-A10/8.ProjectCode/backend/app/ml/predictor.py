from __future__ import annotations

import os
from datetime import datetime
from functools import lru_cache

import joblib
import pandas as pd

from app.ml.train import train_all

ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
WAIT_MODEL_PATH = os.path.join(ARTIFACT_DIR, "wait_time_model.joblib")
TRIAGE_MODEL_PATH = os.path.join(ARTIFACT_DIR, "triage_model.joblib")


def ensure_models_trained() -> None:
    if not (os.path.exists(WAIT_MODEL_PATH) and os.path.exists(TRIAGE_MODEL_PATH)):
        train_all()


@lru_cache(maxsize=1)
def _load_wait_model():
    ensure_models_trained()
    return joblib.load(WAIT_MODEL_PATH)


@lru_cache(maxsize=1)
def _load_triage_model():
    ensure_models_trained()
    return joblib.load(TRIAGE_MODEL_PATH)


def predict_wait_minutes(
    department_type: str,
    queue_ahead: int,
    priority: str,
    avg_service_minutes: float,
    servers: int = 2,
    at: datetime | None = None,
) -> float:
    bundle = _load_wait_model()
    model, dept_encoder, priority_encoder = (
        bundle["model"],
        bundle["dept_encoder"],
        bundle["priority_encoder"],
    )
    hour = (at or datetime.utcnow()).hour

    dept_code = dept_encoder.transform([department_type])[0] if department_type in dept_encoder.classes_ else 0
    priority_code = priority_encoder.transform([priority])[0] if priority in priority_encoder.classes_ else 0

    X = pd.DataFrame(
        [
            {
                "department_type": dept_code,
                "queue_ahead": queue_ahead,
                "hour": hour,
                "priority": priority_code,
                "avg_service_minutes": avg_service_minutes,
                "servers": servers,
            }
        ]
    )
    prediction = model.predict(X)[0]
    return round(max(0.0, float(prediction)), 1)


def predict_triage(
    age: float,
    heart_rate: float,
    systolic_bp: float,
    spo2: float,
    temperature_c: float,
    respiratory_rate: float,
) -> tuple[str, float]:
    """Returns (priority_label, confidence_score 0-1)."""
    bundle = _load_triage_model()
    model, priority_encoder, feature_cols = (
        bundle["model"],
        bundle["priority_encoder"],
        bundle["feature_cols"],
    )
    row = {
        "age": age,
        "heart_rate": heart_rate,
        "systolic_bp": systolic_bp,
        "spo2": spo2,
        "temperature_c": temperature_c,
        "respiratory_rate": respiratory_rate,
    }
    X = pd.DataFrame([row])[feature_cols]
    proba = model.predict_proba(X)[0]
    pred_idx = proba.argmax()
    label = priority_encoder.inverse_transform([pred_idx])[0]
    confidence = float(proba[pred_idx])
    return label, round(confidence, 3)


DEFAULT_VITALS = {
    "heart_rate": 78,
    "systolic_bp": 118,
    "diastolic_bp": 76,
    "spo2": 97,
    "temperature_c": 36.9,
    "respiratory_rate": 16,
}
