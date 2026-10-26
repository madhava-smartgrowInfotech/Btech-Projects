"""Unit tests for the route-risk scorer and the area-risk model artefacts (no web server needed)."""
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import joblib
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.services import risk  # noqa: E402

DAY = datetime(2026, 10, 26, 7, 0, tzinfo=timezone.utc)      # 12:30 IST
NIGHT = datetime(2026, 10, 26, 18, 0, tzinfo=timezone.utc)   # 23:30 IST
D = [SimpleNamespace(lat=10.0, lng=10.0, risk_tier="low"), SimpleNamespace(lat=20.0, lng=20.0, risk_tier="medium"),
     SimpleNamespace(lat=30.0, lng=30.0, risk_tier="high")]


def route(lat, lng, n=16):
    return {"coordinates": [[lat, lng]] * n}


def test_haversine_known_distance():
    # Delhi to Jaipur is about 235 km as the crow flies
    assert risk._haversine_km(28.6139, 77.2090, 26.9124, 75.7873) == pytest.approx(235, abs=8)
    assert risk._haversine_km(1, 1, 1, 1) == 0


def test_nearest_district_picks_closest():
    assert risk.nearest_district(19.0, 19.0, D).risk_tier == "medium"
    assert risk.nearest_district(31.0, 29.0, D).risk_tier == "high"


def test_tier_weights_order_scores():
    lo = risk.score_route(route(10, 10), D, sample_every_n=1, now=DAY)["score"]
    me = risk.score_route(route(20, 20), D, sample_every_n=1, now=DAY)["score"]
    hi = risk.score_route(route(30, 30), D, sample_every_n=1, now=DAY)["score"]
    assert (lo, me, hi) == (1.0, 2.5, 5.0)


def test_night_multiplies_every_score_by_the_same_factor():
    for lat in (10, 20, 30):
        d = risk.score_route(route(lat, lat), D, now=DAY)
        n = risk.score_route(route(lat, lat), D, now=NIGHT)
        assert d["night"] is False and n["night"] is True
        assert n["score"] == pytest.approx(d["score"] * risk.NIGHT_MULTIPLIER)


def test_night_never_reorders_two_routes():
    mixed = {"coordinates": [[10, 10]] * 8 + [[30, 30]] * 8}
    medium = route(20, 20, 16)
    day = [risk.score_route(x, D, sample_every_n=1, now=DAY)["score"] for x in (mixed, medium)]
    night = [risk.score_route(x, D, sample_every_n=1, now=NIGHT)["score"] for x in (mixed, medium)]
    assert (day[0] < day[1]) == (night[0] < night[1])


def test_empty_route_scores_zero():
    assert risk.score_route({"coordinates": []}, D, now=DAY)["score"] == 0.0


def test_no_districts_defaults_to_medium():
    assert risk.score_route(route(1, 1), [], sample_every_n=1, now=DAY)["score"] == 2.5


def test_nearest_district_has_no_distance_limit():
    far = risk.nearest_district(0.0, 100.0, D)
    assert far is not None and risk._haversine_km(0.0, 100.0, far.lat, far.lng) > 1000


def test_night_window_boundaries_in_utc():
    assert risk._is_night_utc(datetime(2026, 1, 1, 15, 0, tzinfo=timezone.utc))
    assert not risk._is_night_utc(datetime(2026, 1, 1, 14, 59, tzinfo=timezone.utc))
    assert not risk._is_night_utc(datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc))


# ------------------------------------------------------------------ the shipped model + table
def test_shipped_model_artifact_loads_and_has_three_tiers():
    m = joblib.load(ROOT / "models" / "risk_model.joblib")
    assert m["kmeans"].n_clusters == 3 and sorted(m["tier_map"].values()) == ["high", "low", "medium"]


def test_district_table_is_consistent():
    t = pd.read_csv(ROOT / "data" / "district_risk.csv")
    assert len(t) == 467 and t["risk_score"].between(0, 100).all()
    means = t.groupby("risk_tier")["crime_rate"].mean()
    assert means["low"] < means["medium"] < means["high"]
    assert t["lat"].between(6, 38).all() and t["lng"].between(68, 98).all()


def test_tiers_are_threshold_bands_on_crime_rate():
    t = pd.read_csv(ROOT / "data" / "district_risk.csv")
    assert t[t.risk_tier == "low"]["crime_rate"].max() < t[t.risk_tier == "medium"]["crime_rate"].min()
    assert t[t.risk_tier == "medium"]["crime_rate"].max() < t[t.risk_tier == "high"]["crime_rate"].min()
