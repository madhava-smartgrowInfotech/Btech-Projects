"""Objective 1 - collect and preprocess historical e-commerce logistics data.

No public region-level order dataset is referenced in the project, so
`generate_dataset()` synthesises a realistic one: 30 Indian cities with
real coordinates, 36 months of monthly order volumes driven by population,
city tier, an upward e-commerce trend, festive-season peaks (Oct-Nov),
promotions and noise. Replace `data/*.csv` with real data of the same
schema to use your own history.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import config

CITIES = [
    # city, state, lat, lon, population (millions), tier
    ("Hyderabad", "Telangana", 17.385, 78.487, 10.5, 1),
    ("Mumbai", "Maharashtra", 19.076, 72.878, 21.0, 1),
    ("Delhi", "Delhi", 28.614, 77.209, 32.0, 1),
    ("Bengaluru", "Karnataka", 12.972, 77.594, 13.2, 1),
    ("Chennai", "Tamil Nadu", 13.083, 80.270, 11.5, 1),
    ("Kolkata", "West Bengal", 22.573, 88.364, 15.0, 1),
    ("Pune", "Maharashtra", 18.520, 73.857, 7.4, 1),
    ("Ahmedabad", "Gujarat", 23.023, 72.571, 8.6, 1),
    ("Jaipur", "Rajasthan", 26.912, 75.787, 4.1, 2),
    ("Lucknow", "Uttar Pradesh", 26.847, 80.947, 3.9, 2),
    ("Nagpur", "Maharashtra", 21.146, 79.088, 3.0, 2),
    ("Visakhapatnam", "Andhra Pradesh", 17.687, 83.219, 2.4, 2),
    ("Vijayawada", "Andhra Pradesh", 16.507, 80.648, 1.8, 2),
    ("Warangal", "Telangana", 17.978, 79.594, 0.9, 3),
    ("Indore", "Madhya Pradesh", 22.720, 75.858, 3.3, 2),
    ("Bhopal", "Madhya Pradesh", 23.259, 77.413, 2.6, 2),
    ("Surat", "Gujarat", 21.170, 72.831, 7.0, 2),
    ("Kochi", "Kerala", 9.931, 76.267, 2.3, 2),
    ("Coimbatore", "Tamil Nadu", 11.017, 76.956, 2.7, 2),
    ("Bhubaneswar", "Odisha", 20.296, 85.825, 1.2, 2),
    ("Patna", "Bihar", 25.594, 85.138, 2.5, 2),
    ("Guwahati", "Assam", 26.144, 91.736, 1.2, 3),
    ("Chandigarh", "Chandigarh", 30.733, 76.779, 1.2, 2),
    ("Ludhiana", "Punjab", 30.901, 75.857, 1.9, 3),
    ("Kanpur", "Uttar Pradesh", 26.450, 80.332, 3.4, 2),
    ("Raipur", "Chhattisgarh", 21.251, 81.630, 1.3, 3),
    ("Ranchi", "Jharkhand", 23.344, 85.310, 1.4, 3),
    ("Mysuru", "Karnataka", 12.296, 76.639, 1.2, 3),
    ("Tiruchirappalli", "Tamil Nadu", 10.790, 78.705, 1.1, 3),
    ("Dehradun", "Uttarakhand", 30.316, 78.032, 0.9, 3),
]

FESTIVAL_MONTHS = {10: 1.35, 11: 1.25, 1: 1.08, 8: 1.10}   # Diwali/Dussehra, New Year, Independence-day sales


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


SATELLITES_PER_TIER = {1: 3, 2: 2, 3: 1}       # district-level demand points around each city
_DIRS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def _build_regions(rng: np.random.Generator, satellites: bool = True) -> pd.DataFrame:
    rows = [dict(city=c, state=st, lat=la, lon=lo, population=pop, tier=t, parent=c)
            for c, st, la, lo, pop, t in CITIES]
    if satellites:
        for c, st, la, lo, pop, t in CITIES:
            for _ in range(SATELLITES_PER_TIER[t]):
                bearing = rng.uniform(0, 2 * math.pi)
                km = rng.uniform(45, 160)
                dlat = km / 111.0 * math.cos(bearing)
                dlon = km / (111.0 * math.cos(math.radians(la))) * math.sin(bearing)
                name = f"{c}-{_DIRS[int((math.degrees(bearing) + 22.5) // 45) % 8]}"
                k = 2
                while any(r["city"] == name for r in rows):
                    name = f"{c}-{_DIRS[int((math.degrees(bearing) + 22.5) // 45) % 8]}{k}"
                    k += 1
                rows.append(dict(city=name, state=st, lat=round(la + dlat, 4), lon=round(lo + dlon, 4),
                                 population=round(pop * rng.uniform(0.08, 0.28), 2), tier=3, parent=c))
    regions = pd.DataFrame(rows)
    regions.insert(0, "region_id", [f"R{i:03d}" for i in range(1, len(regions) + 1)])
    return regions


def generate_dataset(n_months: int = config.N_HISTORY_MONTHS, seed: int = config.RANDOM_STATE,
                     start: str = "2023-01", satellites: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    regions = _build_regions(rng, satellites)
    # per-city e-commerce penetration (tier-1 cities order more per capita)
    regions["penetration"] = np.round(
        regions["tier"].map({1: 0.055, 2: 0.038, 3: 0.028}) * rng.uniform(0.85, 1.15, len(regions)), 4)

    periods = pd.period_range(start, periods=n_months, freq="M")
    rows = []
    for _, r in regions.iterrows():
        base = r["population"] * 1e6 * r["penetration"] / 12          # monthly orders
        growth = rng.uniform(0.010, 0.022)                              # monthly growth rate
        level = base
        for t, p in enumerate(periods):
            month = p.month
            season = FESTIVAL_MONTHS.get(month, 1.0) * (0.93 if month in (2, 6) else 1.0)
            promo = int(rng.random() < 0.18 or month in (10, 11))
            promo_lift = 1.0 + (0.14 if promo else 0.0)
            shock = rng.normal(1.0, 0.06)
            orders = level * season * promo_lift * shock
            avg_weight = round(rng.uniform(0.8, 2.4), 2)
            rows.append({
                "region_id": r["region_id"], "period": str(p), "year": p.year, "month": month,
                "orders": int(max(orders, 50)), "promo": promo,
                "avg_order_value": round(rng.normal(1150, 120), 0),
                "avg_parcel_weight_kg": avg_weight,
                "return_rate": round(rng.uniform(0.05, 0.16), 3),
            })
            level *= 1 + growth + rng.normal(0, 0.004)
    demand = pd.DataFrame(rows)
    return regions, demand


def save_dataset(regions: pd.DataFrame, demand: pd.DataFrame) -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    regions.to_csv(config.REGIONS_CSV, index=False)
    demand.to_csv(config.DEMAND_CSV, index=False)


def load_dataset() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not (config.REGIONS_CSV.exists() and config.DEMAND_CSV.exists()):
        regions, demand = generate_dataset()
        save_dataset(regions, demand)
    regions = pd.read_csv(config.REGIONS_CSV)
    demand = pd.read_csv(config.DEMAND_CSV)
    if "tier" not in regions:
        regions["tier"] = 2
    if "penetration" not in regions:
        regions["penetration"] = 0.04
    # ---- preprocessing --------------------------------------------------
    demand["period"] = demand["period"].astype(str)
    demand = demand.drop_duplicates(["region_id", "period"])
    demand["orders"] = pd.to_numeric(demand["orders"], errors="coerce")
    demand = demand.sort_values(["region_id", "period"])
    # fill occasional gaps by interpolation inside each region
    demand["orders"] = demand.groupby("region_id")["orders"].transform(
        lambda s: s.interpolate(limit_direction="both"))
    demand = demand.dropna(subset=["orders"])
    demand["orders"] = demand["orders"].astype(int)
    if "year" not in demand:
        demand["year"] = demand["period"].str[:4].astype(int)
    if "month" not in demand:
        demand["month"] = demand["period"].str[5:7].astype(int)
    return regions.reset_index(drop=True), demand.reset_index(drop=True)


def distance_matrix(regions: pd.DataFrame) -> np.ndarray:
    n = len(regions)
    d = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d[i, j] = d[j, i] = haversine_km(regions.lat[i], regions.lon[i], regions.lat[j], regions.lon[j])
    return d * 1.25   # road-distance factor over great-circle distance


def dataset_summary(regions: pd.DataFrame, demand: pd.DataFrame) -> dict:
    monthly = demand.groupby("period")["orders"].sum()
    return {
        "regions": int(len(regions)),
        "periods": int(demand["period"].nunique()),
        "first_period": demand["period"].min(),
        "last_period": demand["period"].max(),
        "total_orders": int(demand["orders"].sum()),
        "monthly_total": {k: int(v) for k, v in monthly.items()},
        "top_regions": demand.groupby("region_id")["orders"].mean().sort_values(ascending=False)
        .head(5).round(0).astype(int).to_dict(),
    }
