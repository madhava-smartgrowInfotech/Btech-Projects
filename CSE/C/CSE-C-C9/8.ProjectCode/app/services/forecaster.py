"""Forecast loading service for FinSight AI."""
from .predictor import load_json_artifact

EMPTY = {"history": [], "forecast": [], "interpretation": "Forecast data is unavailable.",
         "trend_direction": "unknown", "method": "n/a"}


def get_forecast() -> dict:
    data = load_json_artifact("forecast.json", None)
    if not data or not data.get("history") or not data.get("forecast"):
        return {"available": False, **EMPTY}
    return {"available": True, **data}
