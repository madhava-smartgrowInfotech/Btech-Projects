"""Analytics and model-performance endpoints (seeds its own readings, so it does not depend on test order)."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture(scope="module", autouse=True)
def seeded(client, user_headers, admin_headers):
    client.post("/api/admin/settings/preset/demo", headers=admin_headers)
    key = client.post("/api/devices/phone", headers=user_headers, json={"name": "Analytics phone"}).json()["api_key"]
    start = datetime.now(timezone.utc) - timedelta(minutes=20)
    rows = []
    for i in range(6):                                   # a dead zone for 2.5 minutes -> a registered complaint
        rows.append({"client_uuid": str(uuid.uuid4()), "ts": (start + timedelta(seconds=30 * i)).isoformat(), "lat": 22.5726, "lon": 88.3639,
                     "operator": "BSNL", "connection_type": "cellular", "connected": False, "probes_sent": 3, "probes_ok": 0})
    for i in range(24):                                  # strong readings nearby, with speed tests
        rows.append({"client_uuid": str(uuid.uuid4()), "ts": (start + timedelta(minutes=5, seconds=20 * i)).isoformat(),
                     "lat": 22.58 + i * 0.0004, "lon": 88.37, "operator": "BSNL", "connection_type": "cellular", "connected": True,
                     "probes_sent": 3, "probes_ok": 3, "latency_ms": 55.0, "dl_mbps": 18.0 + i % 5, "ul_mbps": 5.0})
    assert client.post("/api/ingest/readings", headers={"X-Device-Key": key}, json={"readings": rows}).json()["accepted"] == 30


def test_summary_and_trends(client, engineer_headers, user_headers):
    s = client.get("/api/analytics/summary", headers=engineer_headers).json()
    assert s["readings_total"] > 0 and s["zones_monitored"] > 0 and "median_hours_to_resolve" in s and s["mine"] is None
    mine = client.get("/api/analytics/summary", headers=user_headers).json()["mine"]
    assert mine["readings"] > 0
    t = client.get("/api/analytics/trends?days=30&tz_offset_min=330", headers=engineer_headers).json()["days"]
    assert t and all({"day", "readings", "registered", "resolved"} <= set(d) for d in t)
    assert sum(d["registered"] for d in t) >= 1


def test_worst_areas_time_of_day_operators_funnel(client, engineer_headers):
    worst = client.get("/api/analytics/worst-areas?min_readings=3", headers=engineer_headers).json()
    assert worst and worst[0]["bad_share"] >= worst[-1]["bad_share"]
    tod = client.get("/api/analytics/time-of-day?tz_offset_min=330", headers=engineer_headers).json()["cells"]
    assert tod and all(0 <= c["weekday"] <= 6 and 0 <= c["hour"] <= 23 for c in tod)
    ops = client.get("/api/analytics/operators", headers=engineer_headers).json()
    assert {o["operator"] for o in ops} >= {"BSNL"} and all(abs(o["strong_share"] + o["weak_share"] + o["dead_share"] - 1) < 0.01 for o in ops)
    f = client.get("/api/analytics/complaint-funnel", headers=engineer_headers).json()
    assert f["stages"][0]["stage"] == "detected" and f["stages"][0]["reached"] >= f["stages"][1]["reached"]


def test_model_performance_and_field_validation(client, user_headers):
    m = client.get("/api/ml/models", headers=user_headers).json()
    assert set(m["models"]) == {"zone_classifier", "radio_estimate", "gp_signal"}
    zc = m["models"]["zone_classifier"]
    assert zc["test_overall"]["macro_f1"] > 0.7 and zc["plots"]
    png = client.get(f"/api/ml/models/{zc['run']}/artifacts/{zc['plots'][0]}", headers=user_headers)
    assert png.status_code == 200 and png.headers["content-type"] == "image/png"
    assert client.get(f"/api/ml/models/{zc['run']}/artifacts/..%5C..%5C.env", headers=user_headers).status_code in (400, 404)
    fv = client.get("/api/ml/field-validation", headers=user_headers).json()
    assert {"radio", "probe", "gp"} <= set(fv) and fv["probe"]["readings"] > 0


def test_public_stats_need_no_sign_in(client):
    r = client.get("/api/public/stats")
    assert r.status_code == 200
    body = r.json()
    assert {"readings", "zones", "complaints_registered", "classifier_accuracy", "classifier_model", "predictor_gain_vs_idw"} <= set(body)
    assert body["readings"] >= 0 and body["zones"] >= 0
