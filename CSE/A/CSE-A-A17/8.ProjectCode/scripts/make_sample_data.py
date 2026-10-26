"""
make_sample_data.py
--------------------
Generates SYNTHETIC files in the exact H&M schema (articles.csv, customers.csv,
transactions_train.csv) so the app can be exercised end to end without the Kaggle
download. This is a development / demo aid only: the numbers are simulated, not
real H&M sales. Real data is uploaded through the app the same way.

    python scripts/make_sample_data.py            -> data/sample_hm/
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

# (product_type, product_group, department, section, garment_group, base price, summer weight, winter weight)
CATALOGUE = [
    ("Trousers", "Garment Lower body", "Trousers", "Womens Trend", "Trousers", 0.040, 1.0, 1.0),
    ("Jeans", "Garment Lower body", "Denim", "Ladies Denim", "Trousers Denim", 0.050, 1.0, 1.0),
    ("Shorts", "Garment Lower body", "Shorts", "Womens Casual", "Shorts", 0.030, 1.8, 0.2),
    ("Skirt", "Garment Lower body", "Skirts", "Womens Everyday Collection", "Skirts", 0.035, 1.5, 0.5),
    ("T-shirt", "Garment Upper body", "Jersey Basic", "Womens Everyday Basics", "Jersey Basic", 0.020, 1.6, 0.6),
    ("Sweater", "Garment Upper body", "Knitwear", "Womens Everyday Collection", "Knitwear", 0.045, 0.3, 1.9),
    ("Blouse", "Garment Upper body", "Blouse", "Womens Smart Casual", "Blouse", 0.038, 1.2, 0.9),
    ("Hoodie", "Garment Upper body", "Jersey", "Divided Basics", "Jersey Fancy", 0.042, 0.4, 1.8),
    ("Dress", "Garment Full body", "Dresses Ladies", "Womens Trend", "Dresses Ladies", 0.060, 1.7, 0.6),
    ("Jacket", "Garment Upper body", "Outdoor", "Mens Outerwear", "Outdoor", 0.090, 0.3, 2.0),
    ("Coat", "Garment Upper body", "Outdoor", "Ladies Outerwear", "Outdoor", 0.110, 0.2, 2.2),
    ("Socks", "Socks & Tights", "Socks", "Womens Lingerie", "Socks and Tights", 0.010, 0.8, 1.3),
    ("Sneakers", "Shoes", "Shoes", "Womens Shoes", "Shoes", 0.070, 1.3, 0.9),
    ("Bag", "Accessories", "Bags", "Womens Accessories", "Accessories", 0.055, 1.1, 1.0),
    ("Cap", "Accessories", "Hats", "Divided Accessories", "Accessories", 0.018, 1.7, 0.4),
]
COLOURS = ["Black", "White", "Dark Blue", "Light Blue", "Beige", "Grey", "Red", "Dark Green", "Pink", "Light Beige"]


def build(args: argparse.Namespace) -> None:
    rng = np.random.default_rng(args.seed)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # ---- articles ---------------------------------------------------------
    rows = []
    for i in range(args.articles):
        t = CATALOGUE[i % len(CATALOGUE)]
        colour = COLOURS[int(rng.integers(len(COLOURS)))]
        rows.append({
            "article_id": 108775015 + i * 7919,
            "product_code": 108775 + i,
            "prod_name": f"{t[0]} {colour} {i:03d}",
            "product_type_name": t[0],
            "product_group_name": t[1],
            "colour_group_name": colour,
            "department_name": t[2],
            "index_name": "Ladieswear" if t[3].startswith(("Womens", "Ladies")) else "Divided",
            "index_group_name": "Ladieswear" if t[3].startswith(("Womens", "Ladies")) else "Divided",
            "section_name": t[3],
            "garment_group_name": t[4],
            "detail_desc": f"{t[0]} in {colour.lower()}.",
            "_price": t[5] * float(rng.uniform(0.7, 1.4)),
            "_summer": t[6],
            "_winter": t[7],
            "_pop": float(rng.lognormal(0, 0.7)),
            "_online_bias": float(rng.uniform(0.15, 0.85)),
        })
    art = pd.DataFrame(rows)

    # ---- customers --------------------------------------------------------
    n_cust = args.customers
    cust_ids = [f"{int(x):016x}" for x in rng.integers(1, 2**60, size=n_cust)]
    customers = pd.DataFrame({
        "customer_id": cust_ids,
        "FN": rng.choice([1.0, np.nan], size=n_cust),
        "Active": rng.choice([1.0, np.nan], size=n_cust),
        "club_member_status": rng.choice(["ACTIVE", "PRE-CREATE", "LEFT CLUB"], p=[0.92, 0.07, 0.01], size=n_cust),
        "fashion_news_frequency": rng.choice(["NONE", "Regularly", "Monthly"], p=[0.6, 0.38, 0.02], size=n_cust),
        "age": rng.integers(16, 75, size=n_cust),
        "postal_code": [f"{int(x):064x}" for x in rng.integers(1, 2**60, size=n_cust)],
    })

    # ---- transactions: per (day, article) Poisson demand with season + weekday + channel mix ------
    days = pd.date_range(args.start, periods=args.days, freq="D")
    day_of_year = days.dayofyear.values
    summer = 0.5 * (1 + np.cos(2 * np.pi * (day_of_year - 200) / 365.25))  # peaks in July
    weekday = np.array([1.0, 0.9, 0.9, 1.0, 1.2, 1.6, 1.4])[days.dayofweek.values]
    trend = np.linspace(0.9, 1.15, len(days))

    txn_chunks = []
    for _, a in art.iterrows():
        season = a["_summer"] * summer + a["_winter"] * (1 - summer)
        base = args.scale * a["_pop"] * season * weekday * trend
        for channel, share in ((1, 1 - a["_online_bias"]), (2, a["_online_bias"])):
            lam = base * share * (1.15 if channel == 2 else 0.9)
            counts = rng.poisson(lam)
            total = int(counts.sum())
            if total == 0:
                continue
            day_idx = np.repeat(np.arange(len(days)), counts)
            price_mult = 1.0 if channel == 1 else 0.92  # online skews cheaper: a real domain shift to adapt to
            price = a["_price"] * price_mult * rng.normal(1.0, 0.06, size=total)
            txn_chunks.append(pd.DataFrame({
                "t_dat": days[day_idx].strftime("%Y-%m-%d"),
                "customer_id": rng.choice(cust_ids, size=total),
                "article_id": a["article_id"],
                "price": np.round(np.clip(price, 0.002, None), 8),
                "sales_channel_id": channel,
            }))
    txn = pd.concat(txn_chunks, ignore_index=True).sample(frac=1.0, random_state=args.seed)
    txn = txn.sort_values("t_dat", kind="stable").reset_index(drop=True)

    art_out = art[[c for c in art.columns if not c.startswith("_")]]
    art_out.to_csv(out / "articles.csv", index=False)
    customers.to_csv(out / "customers.csv", index=False)
    txn.to_csv(out / "transactions_train.csv", index=False)
    print(f"articles {len(art_out):,} | customers {len(customers):,} | transactions {len(txn):,} -> {out}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Generate synthetic H&M-schema CSVs (not real sales).")
    p.add_argument("--out", default=str(ROOT / "data" / "sample_hm"))
    p.add_argument("--articles", type=int, default=90)
    p.add_argument("--customers", type=int, default=4000)
    p.add_argument("--days", type=int, default=240)
    p.add_argument("--start", default="2020-03-01")
    p.add_argument("--scale", type=float, default=2.2, help="average units per article per day")
    p.add_argument("--seed", type=int, default=17)
    build(p.parse_args())
