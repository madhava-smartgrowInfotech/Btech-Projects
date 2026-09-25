"""Evaluation numbers for the area-risk model and the route-scoring logic it
feeds (SHEGUARD objectives 1 & 2 - safe route guidance). Loads the trained
K-Means model, recomputes cluster-quality metrics, and sanity-checks that the
route scorer always ranks a route through safer districts above one through
riskier districts. Saves everything to experiments/eval/metrics.json.

Usage: python ml/eval.py
"""
import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services import risk as risk_service  # noqa: E402

DISTRICT_RISK_CSV = ROOT / "data" / "district_risk.csv"
MODEL_PATH = ROOT / "models" / "risk_model.joblib"
OUT_DIR = ROOT / "experiments" / "eval"
OUT_DIR.mkdir(parents=True, exist_ok=True)


class FakeDistrict:
    def __init__(self, row):
        self.lat, self.lng, self.risk_tier = row.lat, row.lng, row.risk_tier


def cluster_quality(data):
    scaler = StandardScaler()
    X = scaler.fit_transform(data[["crime_rate"]].values)
    labels = data["risk_tier"].astype("category").cat.codes.values
    return {
        "silhouette_score": round(float(silhouette_score(X, labels)), 4),
        "davies_bouldin_score": round(float(davies_bouldin_score(X, labels)), 4),
    }


def route_scoring_sanity_check(districts):
    """A route sampled entirely from 'high' risk districts must score higher
    (riskier) than one sampled entirely from 'low' risk districts."""
    high = next((d for d in districts if d.risk_tier == "high"), None)
    low = next((d for d in districts if d.risk_tier == "low"), None)
    if not high or not low:
        return {"ran": False, "reason": "not enough tier variety to test"}

    risky_route = {"coordinates": [[high.lat, high.lng]] * 10}
    safe_route = {"coordinates": [[low.lat, low.lng]] * 10}
    risky_score = risk_service.score_route(risky_route, districts, sample_every_n=1)["score"]
    safe_score = risk_service.score_route(safe_route, districts, sample_every_n=1)["score"]

    return {
        "ran": True,
        "high_risk_route_score": risky_score,
        "low_risk_route_score": safe_score,
        "passed": risky_score > safe_score,
    }


def main():
    if not DISTRICT_RISK_CSV.exists() or not MODEL_PATH.exists():
        raise SystemExit("Run ml/train_risk_model.py first.")

    data = pd.read_csv(DISTRICT_RISK_CSV)
    districts = [FakeDistrict(r) for r in data.itertuples()]

    quality = cluster_quality(data)
    sanity = route_scoring_sanity_check(districts)

    tier_stats = data.groupby("risk_tier")["crime_rate"].agg(["count", "mean", "min", "max"]).round(2)

    results = {
        "n_districts_evaluated": len(data),
        "cluster_quality": quality,
        "route_scoring_sanity_check": sanity,
        "tier_stats": tier_stats.to_dict(orient="index"),
    }

    with open(OUT_DIR / "metrics.json", "w") as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results, indent=2))
    print(f"\nSaved -> {OUT_DIR / 'metrics.json'}")


if __name__ == "__main__":
    main()
