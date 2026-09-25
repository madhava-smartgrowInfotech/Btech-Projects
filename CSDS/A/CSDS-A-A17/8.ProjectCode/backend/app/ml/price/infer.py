from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache

import joblib
import numpy as np
import shap

from app.core.config import DATA_DIR
from app.ml.price.features import build_row, build_row_from_context, market_context, row_to_vector, FEATURE_COLUMNS

SPOILAGE_WINDOW_DAYS = 14
FORECAST_DAYS = 30

READABLE_FEATURE = {
    "month_sin": "Seasonal timing",
    "month_cos": "Seasonal timing",
    "rainfall_mm": "Rainfall",
    "temp_avg_c": "Average temperature",
    "demand_index": "Market demand",
    "supply_index": "Market supply",
    "fuel_price_index": "Transport / fuel cost",
    "days_to_harvest": "Time since harvest",
    "year_trend": "Multi-year market trend",
    "grade_premium": "Quality grade",
    "region_factor": "Regional market factor",
}


@lru_cache(maxsize=1)
def load_artifact():
    path = DATA_DIR / "price_model.joblib"
    if not path.exists():
        from app.ml.price.train_model import train

        return train()
    return joblib.load(path)


@lru_cache(maxsize=1)
def _explainer():
    artifact = load_artifact()
    return shap.TreeExplainer(artifact["point_model"])


def readable_label(col: str) -> str:
    if col.startswith("crop_"):
        return "Crop type"
    return READABLE_FEATURE.get(col, col)


def predict_price(crop: str, region: str, grade: str, days_to_harvest: int = 0) -> dict:
    artifact = load_artifact()
    point_model = artifact["point_model"]
    low_model = artifact["low_model"]
    high_model = artifact["high_model"]

    today = date.today()
    row0 = build_row(crop, region, grade, today, days_to_harvest)
    vec0 = row_to_vector(row0)

    current_price = float(point_model.predict(vec0)[0])
    confidence_low = float(low_model.predict(vec0)[0])
    confidence_high = float(high_model.predict(vec0)[0])

    # Walk the market context forward day-by-day (smoothed toward each day's
    # target) instead of resampling it independently, so the forecast reads
    # as one continuous trajectory rather than an iid jump every day.
    forecast: dict[int, float] = {}
    running_ctx = market_context(crop, region, today)
    for offset in range(0, FORECAST_DAYS + 1):
        d = today + timedelta(days=offset)
        target_ctx = market_context(crop, region, d)
        running_ctx = {k: 0.8 * running_ctx[k] + 0.2 * target_ctx[k] for k in running_ctx}
        dth = max(0, days_to_harvest - offset)
        row = build_row_from_context(crop, region, grade, d, running_ctx, dth, year_trend=row0["year_trend"])
        vec = row_to_vector(row)
        forecast[offset] = float(point_model.predict(vec)[0])

    window = {k: v for k, v in forecast.items() if k <= SPOILAGE_WINDOW_DAYS}
    best_sell_day = max(window, key=window.get)

    explainer = _explainer()
    shap_values = explainer.shap_values(vec0)[0]
    grouped: dict[str, float] = {}
    for col, val in zip(FEATURE_COLUMNS, shap_values):
        label = readable_label(col)
        grouped[label] = grouped.get(label, 0.0) + float(val)

    top_features = sorted(
        [{"feature": k, "contribution": v} for k, v in grouped.items()],
        key=lambda x: abs(x["contribution"]),
        reverse=True,
    )[:6]

    return {
        "crop_type": crop,
        "region": region,
        "grade": grade,
        "current_price": round(current_price, 2),
        "confidence_low": round(min(confidence_low, current_price), 2),
        "confidence_high": round(max(confidence_high, current_price), 2),
        "forecast": {str(k): round(v, 2) for k, v in forecast.items()},
        "shap_explanation": {"top_features": top_features},
        "best_sell_day": best_sell_day,
    }
