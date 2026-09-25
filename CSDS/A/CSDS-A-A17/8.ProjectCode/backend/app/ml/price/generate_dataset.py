"""Generates a multi-year synthetic market dataset for price forecasting.

Real historical mandi/market price feeds were not available, so this
builds a physically-plausible synthetic series: seasonality, a mild
multi-year trend, weather/demand/supply effects, transport-cost and
quality-grade premiums, all combined through the formula in
features.py::true_price with added noise -- then a real gradient-boosted
model is trained on it. Disclosed in the admin "model card".
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from app.ml.price.features import CROPS, REGIONS, GRADES, build_row, true_price, FEATURE_COLUMNS


def generate(start: date = date(2022, 1, 1), days: int = 3 * 365, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for crop in CROPS:
        for region in REGIONS:
            for offset in range(0, days, 3):  # every 3 days, keeps dataset a manageable size
                d = start + timedelta(days=offset)
                grade = rng.choice(GRADES, p=[0.28, 0.38, 0.24, 0.10])
                days_to_harvest = int(rng.integers(0, 20))
                row = build_row(crop, region, grade, d, days_to_harvest)
                noise = rng.normal(0, 0.035)
                price = true_price(crop, row, noise=noise)
                row["price"] = price
                row["crop_type"] = crop
                row["region"] = region
                row["grade"] = grade
                row["date"] = d.isoformat()
                rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    from app.core.config import DATA_DIR

    df = generate()
    out_path = DATA_DIR / "price_dataset.csv"
    df.to_csv(out_path, index=False)
    print(f"wrote {len(df)} rows to {out_path}")
