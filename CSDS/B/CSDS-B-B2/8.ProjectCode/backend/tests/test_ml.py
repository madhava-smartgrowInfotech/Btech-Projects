"""ML pipeline tests: label rules, features, service-quality bands, loaded models and GP suggestions."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.core.config import settings
from app.ml.features import FEATURES, apply_profile, build_features
from app.ml.service import ModelService
from app.ml.service_quality import classify_probe
from app.ml.signal_ranges import DEAD, STRONG, WEAK, classify_by_ranges, classify_wifi, family_of, label_arrays
from app.ml.suggest import predicted_surface, suggest

MODELS_READY = all((settings.models_dir / f"{m}.joblib").exists() for m in ("zone_classifier", "radio_estimate", "gp_signal"))


# ------------------------------------------------------------------ documented ranges
@pytest.mark.parametrize("family,level,quality,sinr,expected", [
    ("lte_nr", -85, -9, 18, STRONG),
    ("lte_nr", -108, -9, 18, WEAK),        # RSRP in the weak band
    ("lte_nr", -95, -17, 18, WEAK),        # RSRQ below -15
    ("lte_nr", -95, -9, -6, DEAD),         # SINR below -3
    ("lte_nr", -121, None, None, DEAD),    # RSRP below -115
    ("3g", -90, -8, None, STRONG),
    ("3g", -101, -8, None, WEAK),
    ("2g", -104, None, None, DEAD),
])
def test_ranges_worst_metric_wins(family, level, quality, sinr, expected):
    assert classify_by_ranges(family, level, quality, sinr).label == expected


def test_ranges_explain_and_handle_no_service():
    v = classify_by_ranges("lte_nr", -118, -10, 12)
    assert v.label == DEAD and "RSRP -118 dBm is below -115 dBm" in v.reasons[0]
    assert classify_by_ranges("lte_nr", in_service=False).label == DEAD
    assert classify_by_ranges("lte_nr").label is None


def test_invalid_values_are_ignored():
    # -200 dBm is a logger sentinel, not a measurement
    assert classify_by_ranges("lte_nr", -200, -10, 12).label == STRONG


def test_vectorised_labels_match_scalar():
    fam = np.array(["lte_nr", "lte_nr", "3g", "2g"], dtype=object)
    lab = label_arrays(fam, np.array([-85, -118, -101, np.nan]), np.array([-9, -9, -8, np.nan]), np.array([18, 18, np.nan, np.nan]))
    assert lab.tolist() == [STRONG, DEAD, WEAK, -1]


def test_network_type_family():
    assert family_of("LTE") == "lte_nr" and family_of("nr_sa") == "lte_nr" and family_of("HSPA+") == "3g" and family_of("EDGE") == "2g"
    assert family_of("wifi") is None


# ------------------------------------------------------------------ features
def _trace(n=12, level=-95.0):
    return pd.DataFrame({
        "device_key": "d1", "ts": pd.date_range("2026-01-01", periods=n, freq="5s"), "family": "lte_nr",
        "level": np.linspace(level, level - 11, n), "quality": -11.0, "sinr": 9.0, "rssi": -70.0, "cqi": 9.0,
    })


def test_features_columns_and_rolling_window():
    f = build_features(_trace())
    assert list(f.columns) == FEATURES
    assert f["fam_lte_nr"].eq(1).all()
    # 30 s window at 5 s spacing -> the minimum is the level 6 readings back at most
    assert f["level_min30"].iloc[-1] == pytest.approx(f["level"].iloc[-1])
    assert f["level_median30"].iloc[0] == pytest.approx(f["level"].iloc[0])
    assert f["band_worst"].iloc[0] == 0 and f["band_worst"].iloc[-1] == 1


def test_profiles_blank_the_right_metrics():
    t = _trace()
    lvl = apply_profile(t, "level_only")
    assert lvl[["quality", "sinr", "rssi", "cqi"]].isna().all().all() and lvl.level.notna().all()
    rssi = apply_profile(t, "rssi_only")
    assert rssi.level.isna().all() and rssi.rssi.notna().all()


# ------------------------------------------------------------------ phone-probe bands and Wi-Fi ranges
def test_probe_bands():
    assert classify_probe(False, 3, 0, None, None).label == DEAD
    assert classify_probe(True, 3, 1, 90, None).label == DEAD            # 2 of 3 probes lost
    assert classify_probe(True, 3, 2, 90, None).label == WEAK            # 1 of 3 lost
    assert classify_probe(True, 3, 3, 650, 8).label == WEAK              # slow round trip
    assert classify_probe(True, 3, 3, 80, 0.6).label == WEAK             # slow download
    strong = classify_probe(True, 3, 3, 60, 25)
    assert strong.label == STRONG and 0.55 <= strong.confidence <= 1.0
    edge = classify_probe(True, 3, 3, 390, 2.1)
    assert edge.label == STRONG and edge.confidence < strong.confidence


def test_wifi_ranges():
    assert classify_wifi(-55).label == STRONG
    assert classify_wifi(-72).label == WEAK
    assert classify_wifi(-86).label == DEAD
    assert classify_wifi(-55, latency_ms=480).label == WEAK
    assert classify_wifi(None, connected=False).label == DEAD


# ------------------------------------------------------------------ Gaussian Process suggestions
GP_BUNDLE = {
    "targets": {"rsrp": {"params": {"amp_short": 20.0, "ls_short": 40.0, "amp_long": 60.0, "ls_long": 500.0, "noise": 6.0},
                         "strong_threshold": -100.0, "unit": "dBm"}},
    "search": {"cell_m": 10.0, "radius_m": 1500.0, "max_points": 1500, "grid_step_m": 25.0, "prob_threshold": 0.8},
}


def _field(rng, n=400, east_gradient=True):
    """Readings in a 1.2 km square; signal improves towards the east (about 3.5 dB per 100 m)."""
    lat0, lon0 = 17.40, 78.48
    x = rng.uniform(-600, 600, n)
    y = rng.uniform(-600, 600, n)
    val = (-108 + 0.035 * x if east_gradient else np.full(n, -80.0)) + rng.normal(0, 2, n)
    lat = lat0 + np.degrees(y / 6_371_008.8)
    lon = lon0 + np.degrees(x / (6_371_008.8 * np.cos(np.radians(lat0))))
    return lat0, lon0, lat, lon, val


def test_suggestion_points_towards_better_signal():
    lat0, lon0, lat, lon, val = _field(np.random.default_rng(1))
    user_lat, user_lon = lat0, lon0 - np.degrees(400 / (6_371_008.8 * np.cos(np.radians(lat0))))   # 400 m west, weak area
    s = suggest(GP_BUNDLE, "rsrp", user_lat, user_lon, lat, lon, val)
    assert s.found and s.status == "found" and s.method == "gaussian-process"
    assert 45 <= s.bearing_deg <= 135, s          # roughly east
    assert s.probability >= 0.8 and s.predicted >= -100
    assert 100 < s.distance_m < 900


def test_suggestion_when_already_strong_and_when_no_data():
    lat0, lon0, lat, lon, val = _field(np.random.default_rng(2), east_gradient=False)
    s = suggest(GP_BUNDLE, "rsrp", lat0, lon0, lat, lon, val)
    assert s.status == "already_strong" and s.distance_m == 0
    empty = suggest(GP_BUNDLE, "rsrp", lat0, lon0, [], [], [])
    assert not empty.found and empty.status == "not_enough_data"


def test_predicted_surface_has_probabilities():
    lat0, lon0, lat, lon, val = _field(np.random.default_rng(3))
    cells = predicted_surface(GP_BUNDLE, "rsrp", lat0, lon0, lat, lon, val, radius_m=500, step_m=50)
    assert len(cells) > 50
    assert all(0.0 <= c["p_strong"] <= 1.0 for c in cells)
    east = [c for c in cells if c["lon"] > lon0 + 0.003]
    west = [c for c in cells if c["lon"] < lon0 - 0.003]
    assert np.mean([c["value"] for c in east]) > np.mean([c["value"] for c in west])


# ------------------------------------------------------------------ trained models
@pytest.mark.skipif(not MODELS_READY, reason="models not trained yet (python ml/train_all.py)")
def test_trained_models_load_and_classify():
    svc = ModelService(settings.models_dir)
    assert all(v["loaded"] for v in svc.status().values())
    ts = pd.date_range("2026-01-01", periods=3, freq="5s")
    frame = pd.DataFrame({
        "device_key": ["a", "b", "c"], "ts": ts, "network_type": ["LTE", "LTE", "LTE"],
        "rsrp": [-78.0, -123.0, np.nan], "rsrq": [-8.0, -16.0, np.nan], "sinr": [22.0, -8.0, np.nan],
        "rssi": [-55.0, -95.0, np.nan], "cqi": [13.0, 2.0, np.nan], "in_service": [True, True, False],
    })
    v = svc.classify_radio(frame)
    assert [x.label for x in v] == ["Strong", "Dead", "Dead"]
    assert v[0].method == "model" and 0.5 < v[0].confidence <= 1.0
    assert v[2].method == "no-service" and v[2].confidence == 1.0


@pytest.mark.skipif(not MODELS_READY, reason="models not trained yet (python ml/train_all.py)")
def test_probe_readings_get_measured_class_and_radio_estimate():
    svc = ModelService(settings.models_dir)
    frame = pd.DataFrame({
        "device_key": "p", "ts": pd.date_range("2026-01-01", periods=4, freq="60s"),
        "connected": [True, True, True, False], "probes_sent": 3, "probes_ok": [3, 3, 3, 0],
        "latency_ms": [70.0, 95.0, 620.0, np.nan], "dl_mbps": [24.0, 18.0, 0.4, np.nan], "ul_mbps": [6.0, 5.0, 0.2, np.nan],
    })
    v = svc.classify_probes(frame)
    assert [x.label for x in v] == ["Strong", "Strong", "Weak", "Dead"]
    assert v[0].radio_estimate in ("Strong", "Weak", "Dead") and 0 < v[0].radio_estimate_conf <= 1
    assert v[3].radio_estimate is None     # no speed test while offline
