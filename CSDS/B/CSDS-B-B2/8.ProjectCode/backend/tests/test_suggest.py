"""Better-signal API on phone-probe readings: a weak west side and a strong east side."""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone

LAT0, LON0 = 26.8467, 80.9462


def _pt(east_m: float, north_m: float) -> tuple[float, float]:
    return LAT0 + math.degrees(north_m / 6_371_008.8), LON0 + math.degrees(east_m / (6_371_008.8 * math.cos(math.radians(LAT0))))


def test_suggestion_from_phone_speed_tests(client, user_headers):
    key = client.post("/api/devices/phone", headers=user_headers, json={"name": "Walk phone"}).json()["api_key"]
    now = datetime.now(timezone.utc)
    rows = []
    for i in range(60):
        east = -500 + (i % 20) * 50           # a walk grid from 500 m west to 450 m east
        north = -150 + (i // 20) * 150
        lat, lon = _pt(east, north)
        mbps = 0.3 if east < 0 else 25.0       # slow in the west, fast in the east
        rows.append({"client_uuid": str(uuid.uuid4()), "ts": (now - timedelta(minutes=60 - i)).isoformat(), "lat": lat, "lon": lon,
                     "operator": "Vi", "connection_type": "cellular", "connected": True, "probes_sent": 3, "probes_ok": 3,
                     "latency_ms": 90.0, "dl_mbps": mbps, "ul_mbps": mbps / 4})
    assert client.post("/api/ingest/readings", headers={"X-Device-Key": key}, json={"readings": rows}).json()["accepted"] == 60

    user_lat, user_lon = _pt(-350, 0)
    s = client.get(f"/api/suggest?lat={user_lat}&lon={user_lon}&operator=Vi", headers=user_headers).json()
    assert s["found"] and s["status"] == "found" and s["target"] == "log_dl" and s["operator"] == "Vi"
    assert 45 <= s["bearing_deg"] <= 135, s        # east
    assert s["predicted_mbps"] >= 2 and s["probability"] >= 0.8

    strong_here = client.get(f"/api/suggest?lat={_pt(300, 0)[0]}&lon={_pt(300, 0)[1]}&operator=Vi", headers=user_headers).json()
    assert strong_here["status"] == "already_strong"

    pack = client.get(f"/api/suggest/area?lat={user_lat}&lon={user_lon}&operator=Vi&radius_m=1000", headers=user_headers).json()
    assert pack["spots"] and all(s["p_strong"] >= 0.8 for s in pack["spots"])
    surface = client.get(f"/api/coverage/predicted?lat={LAT0}&lon={LON0}&operator=Vi&radius_m=600", headers=user_headers).json()
    assert surface["target"] == "log_dl" and surface["cells"]


def test_suggestion_without_nearby_data(client, user_headers):
    s = client.get("/api/suggest?lat=-33.9&lon=18.4", headers=user_headers).json()
    assert s["found"] is False and s["status"] == "not_enough_data"
