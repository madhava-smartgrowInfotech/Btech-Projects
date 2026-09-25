"""Train the SHEGUARD area-risk model: aggregate district-level crimes against
women (2001-2012), engineer a per-district crime-rate feature, and cluster
districts into 3 risk tiers (low/medium/high) with K-Means. Trains on CPU in
seconds. Saves the fitted model + scaler under models/ and metrics under
experiments/.

Usage: python ml/train_risk_model.py
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

ROOT = Path(__file__).resolve().parents[1]
CRIME_CSV = ROOT / "data" / "raw" / "district_wise_crimes_against_women_2001_2012.csv"
GEOCODED_CSV = ROOT / "data" / "districts_geocoded.csv"
MODELS_DIR = ROOT / "models"
EXPERIMENTS_DIR = ROOT / "experiments"
MODELS_DIR.mkdir(exist_ok=True)
EXPERIMENTS_DIR.mkdir(exist_ok=True)

CRIME_COLS = [
    "Rape", "Kidnapping and Abduction", "Dowry Deaths",
    "Assault on women with intent to outrage her modesty",
    "Insult to modesty of Women", "Cruelty by Husband or his Relatives",
    "Importation of Girls",
]

RANDOM_STATE = 42
N_CLUSTERS = 3
TIER_NAMES = ["low", "medium", "high"]  # assigned by sorted cluster mean crime_rate


def load_district_features():
    df = pd.read_csv(CRIME_CSV)
    df = df[~df["DISTRICT"].str.contains("TOTAL", case=False, na=False)]

    df["total_crimes"] = df[CRIME_COLS].sum(axis=1)
    agg = df.groupby(["STATE/UT", "DISTRICT"]).agg(
        total_crimes=("total_crimes", "sum"),
        years_reported=("Year", "nunique"),
    ).reset_index()
    agg["crime_rate"] = agg["total_crimes"] / agg["years_reported"]  # avg crimes/year
    agg = agg.rename(columns={"STATE/UT": "state", "DISTRICT": "district"})

    geo = pd.read_csv(GEOCODED_CSV)
    merged = agg.merge(geo, on=["state", "district"], how="inner")
    return merged


def main():
    data = load_district_features()
    if len(data) < N_CLUSTERS * 2:
        raise RuntimeError(
            f"Only {len(data)} geocoded districts available - run "
            "scripts/geocode_districts.py to completion first."
        )

    X = data[["crime_rate"]].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_STATE, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    data["cluster"] = labels

    # Map cluster id -> risk tier by sorted mean crime_rate (ascending = low risk).
    cluster_means = data.groupby("cluster")["crime_rate"].mean().sort_values()
    tier_map = {cluster_id: TIER_NAMES[i] for i, cluster_id in enumerate(cluster_means.index)}
    data["risk_tier"] = data["cluster"].map(tier_map)

    # 0-100 risk score, min-max scaled within the fitted data.
    rmin, rmax = data["crime_rate"].min(), data["crime_rate"].max()
    data["risk_score"] = ((data["crime_rate"] - rmin) / (rmax - rmin) * 100).round(2)

    sil = silhouette_score(X_scaled, labels) if len(set(labels)) > 1 else 0.0

    out_cols = ["state", "district", "lat", "lng", "crime_rate", "risk_score", "risk_tier"]
    data[out_cols].to_csv(ROOT / "data" / "district_risk.csv", index=False)

    joblib.dump({"scaler": scaler, "kmeans": kmeans, "tier_map": tier_map}, MODELS_DIR / "risk_model.joblib")

    metrics = {
        "n_districts": len(data),
        "n_clusters": N_CLUSTERS,
        "silhouette_score": round(float(sil), 4),
        "tier_counts": data["risk_tier"].value_counts().to_dict(),
        "cluster_mean_crime_rate": {tier_map[k]: round(float(v), 2) for k, v in cluster_means.items()},
    }
    with open(EXPERIMENTS_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(json.dumps(metrics, indent=2))
    print(f"Saved model -> {MODELS_DIR / 'risk_model.joblib'}")
    print(f"Saved district risk table -> {ROOT / 'data' / 'district_risk.csv'}")


if __name__ == "__main__":
    main()
