"""Coverage map endpoints: hexagons, heat, points, filters (hour window with time zone), nodes."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone



def _seed(client, headers):
    key = client.post("/api/devices/phone", headers=headers, json={"name": "Coverage phone"}).json()["api_key"]
    base = datetime.now(timezone.utc).replace(hour=6, minute=0, second=0, microsecond=0) - timedelta(days=1)   # 06:00 UTC = 11:30 IST
    rows = []
    for i in range(12):
        dead = i >= 8
        rows.append({"client_uuid": str(uuid.uuid4()), "ts": (base + timedelta(minutes=i)).isoformat(), "lat": 12.9716 + i * 0.0001,
                     "lon": 77.5946, "operator": "MTNL", "connection_type": "cellular", "connected": not dead, "probes_sent": 3,
                     "probes_ok": 0 if dead else 3, "latency_ms": None if dead else 70.0, "dl_mbps": None if dead else 15.0})
    r = client.post("/api/ingest/readings", headers={"X-Device-Key": key}, json={"readings": rows})
    assert r.json()["accepted"] == 12


def test_hexagons_and_heat(client, user_headers):
    _seed(client, user_headers)
    fc = client.get("/api/coverage/hex?operator=MTNL", headers=user_headers).json()
    assert fc["type"] == "FeatureCollection" and fc["features"]
    props = [f["properties"] for f in fc["features"]]
    total = sum(p["n"] for p in props)
    assert total == 12 and sum(p["dead"] for p in props) == 4
    assert all(p["label"] in ("Strong", "Weak", "Dead") for p in props)
    ring = fc["features"][0]["geometry"]["coordinates"][0]
    assert ring[0] == ring[-1] and len(ring) == 7
    heat = client.get("/api/coverage/heat?operator=MTNL&mode=problems", headers=user_headers).json()
    assert heat["points"] and all(p[2] > 0 for p in heat["points"])


def test_hour_filter_uses_viewer_time_zone(client, user_headers):
    # readings were taken 06:00-06:11 UTC = 11:30-11:41 in India (UTC+5:30)
    ist = client.get("/api/coverage/hex?operator=MTNL&hour_from=11&hour_to=12&tz_offset_min=330", headers=user_headers).json()
    assert ist["readings"] == 12
    utc = client.get("/api/coverage/hex?operator=MTNL&hour_from=11&hour_to=12&tz_offset_min=0", headers=user_headers).json()
    assert utc["readings"] == 0
    wrap = client.get("/api/coverage/hex?operator=MTNL&hour_from=22&hour_to=12&tz_offset_min=330", headers=user_headers).json()
    assert wrap["readings"] == 12


def test_summary_points_and_nodes(client, user_headers):
    s = client.get("/api/coverage/summary", headers=user_headers).json()
    assert any(o["name"] == "MTNL" for o in s["operators"]) and s["total"] > 0 and s["bounds"]
    pts = client.get("/api/coverage/points?operator=MTNL&limit=5", headers=user_headers).json()
    assert len(pts) == 5 and pts[0]["ts"] >= pts[-1]["ts"] and pts[0]["mine"] is True
    assert isinstance(client.get("/api/coverage/nodes", headers=user_headers).json(), list)


def test_stream_requires_auth(client):
    assert client.get("/api/coverage/stream").status_code == 401
