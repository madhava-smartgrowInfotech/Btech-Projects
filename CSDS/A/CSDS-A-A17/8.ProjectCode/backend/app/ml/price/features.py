from __future__ import annotations

import hashlib
from datetime import date, timedelta

import numpy as np
import pandas as pd

CROPS = ["Tomato", "Onion", "Potato", "Wheat", "Rice", "Mango", "Cotton", "Maize"]

REGIONS = [
    "Sunridge Valley",
    "Palmgrove Delta",
    "Amberfield Plains",
    "Cedarbrook Hills",
    "Millstone Basin",
    "Harborview Coast",
    "Stonegate Highlands",
    "Clearwater Flats",
]

GRADES = ["A", "B", "C", "Reject"]

BASE_PRICE_PER_QUINTAL = {
    "Tomato": 1800,
    "Onion": 1600,
    "Potato": 1200,
    "Wheat": 2400,
    "Rice": 2800,
    "Mango": 4200,
    "Cotton": 6800,
    "Maize": 2000,
}

GRADE_PREMIUM = {"A": 1.22, "B": 1.05, "C": 0.85, "Reject": 0.45}

REGION_FACTOR = {r: f for r, f in zip(REGIONS, [1.05, 0.98, 1.02, 0.95, 1.0, 1.08, 0.93, 1.0])}

FEATURE_COLUMNS = [
    "month_sin",
    "month_cos",
    "rainfall_mm",
    "temp_avg_c",
    "demand_index",
    "supply_index",
    "fuel_price_index",
    "days_to_harvest",
    "year_trend",
    "grade_premium",
    "region_factor",
] + [f"crop_{c}" for c in CROPS]


def _hash_seed(*parts: str) -> int:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return int(digest[:8], 16)


def market_context(crop: str, region: str, on_date: date) -> dict:
    """Deterministic-but-realistic market context for a crop/region/day.

    Same (crop, region, date) always returns the same numbers within a
    session, so repeated calls are stable, while different crops/regions/
    days vary independently -- mimicking how live weather/demand feeds
    would behave without requiring a real external data source.
    """
    seed = _hash_seed(crop, region, on_date.isoformat())
    rng = np.random.default_rng(seed)

    month = on_date.month
    seasonal_rain = 40 + 60 * max(0, np.sin((month - 6) / 12 * 2 * np.pi))
    rainfall_mm = float(np.clip(rng.normal(seasonal_rain, 15), 0, 260))

    seasonal_temp = 24 + 8 * np.sin((month - 3) / 12 * 2 * np.pi)
    temp_avg_c = float(np.clip(rng.normal(seasonal_temp, 2.5), 8, 44))

    demand_index = float(np.clip(rng.normal(0.55, 0.15), 0.1, 1.0))
    supply_index = float(np.clip(rng.normal(0.55, 0.18), 0.1, 1.0))
    fuel_price_index = float(np.clip(rng.normal(1.0, 0.08), 0.8, 1.3))

    return {
        "rainfall_mm": rainfall_mm,
        "temp_avg_c": temp_avg_c,
        "demand_index": demand_index,
        "supply_index": supply_index,
        "fuel_price_index": fuel_price_index,
    }


def build_row(crop: str, region: str, grade: str, on_date: date, days_to_harvest: int = 0, year_trend: float | None = None) -> dict:
    ctx = market_context(crop, region, on_date)
    return build_row_from_context(crop, region, grade, on_date, ctx, days_to_harvest, year_trend)


def build_row_from_context(
    crop: str,
    region: str,
    grade: str,
    on_date: date,
    ctx: dict,
    days_to_harvest: int = 0,
    year_trend: float | None = None,
) -> dict:
    month = on_date.month
    row = {
        "month_sin": np.sin(2 * np.pi * month / 12),
        "month_cos": np.cos(2 * np.pi * month / 12),
        "rainfall_mm": ctx["rainfall_mm"],
        "temp_avg_c": ctx["temp_avg_c"],
        "demand_index": ctx["demand_index"],
        "supply_index": ctx["supply_index"],
        "fuel_price_index": ctx["fuel_price_index"],
        "days_to_harvest": days_to_harvest,
        "year_trend": year_trend if year_trend is not None else (on_date.year - 2023) * 0.03,
        "grade_premium": GRADE_PREMIUM.get(grade, 1.0),
        "region_factor": REGION_FACTOR.get(region, 1.0),
    }
    for c in CROPS:
        row[f"crop_{c}"] = 1.0 if c == crop else 0.0
    return row


def row_to_vector(row: dict) -> np.ndarray:
    return np.array([[row[c] for c in FEATURE_COLUMNS]], dtype=np.float64)


def true_price(crop: str, row: dict, noise: float = 0.0) -> float:
    base = BASE_PRICE_PER_QUINTAL[crop]
    demand_supply = 0.65 + 0.7 * (row["demand_index"] / max(row["supply_index"], 0.15))
    demand_supply = float(np.clip(demand_supply, 0.55, 1.9))
    seasonal = 1.0 + 0.12 * row["month_sin"]
    weather_penalty = 1.0 - 0.001 * max(0, row["rainfall_mm"] - 150)
    freshness = 1.0 - 0.004 * row["days_to_harvest"]
    price = (
        base
        * row["grade_premium"]
        * row["region_factor"]
        * demand_supply
        * seasonal
        * weather_penalty
        * freshness
        * row["fuel_price_index"] ** 0.15
        * (1 + row["year_trend"])
    )
    return float(price * (1 + noise))
