"""Calibrated no-show probability for a booking (model trained in ml/train_noshow.py)."""
from datetime import date
from functools import lru_cache

import joblib
import pandas as pd

from ..config import MODELS


@lru_cache
def _bundle():
    return joblib.load(MODELS / "noshow_model.joblib")


def predict(age: int | None, gender: str | None, visit_date: date, booked_on: date) -> float:
    b = _bundle()
    row = {
        "age": min(max(age if age is not None else 35, 0), 100),
        "is_female": 1 if (gender or "").upper() == "F" else 0,
        "lead_days": max((visit_date - booked_on).days, 0),
        "weekday": visit_date.weekday(),
        "sms_received": 1,  # every booking gets in-app live updates
        "scholarship": 0, "hypertension": 0, "diabetes": 0, "alcoholism": 0, "handicap": 0,
    }
    p = b["model"].predict_proba(pd.DataFrame([row])[b["features"]])[0, 1]
    return round(float(p), 4)
