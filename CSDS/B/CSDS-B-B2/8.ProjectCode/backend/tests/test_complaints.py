"""Automatic complaints end to end: detect -> register -> engineer workflow -> auto-verify or reopen; dismissals."""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone

import pytest


def _pt(lat0, lon0, east_m=0.0, north_m=0.0):
    return lat0 + math.degrees(north_m / 6_371_008.8), lon0 + math.degrees(east_m / (6_371_008.8 * math.cos(math.radians(lat0))))


@pytest.fixture(scope="module")
def phone(client, user_headers, admin_headers):
    r = client.post("/api/admin/settings/preset/demo", headers=admin_headers)
    assert r.status_code == 200
    key = client.post("/api/devices/phone", headers=user_headers, json={"name": "Complaint phone"}).json()["api_key"]
    return {"X-Device-Key": key}


def _send(client, h, lat, lon, labels: list[str], start: datetime, step_s: int = 30):
    rows = []
    for i, lab in enumerate(labels):
        dead, weak = lab == "Dead", lab == "Weak"
        rows.append({"client_uuid": str(uuid.uuid4()), "ts": (start + timedelta(seconds=i * step_s)).isoformat(), "lat": lat, "lon": lon,
                     "operator": "Airtel", "connection_type": "cellular", "connected": not dead, "probes_sent": 3,
                     "probes_ok": 0 if dead else 3, "latency_ms": None if dead else (700.0 if weak else 60.0),
                     "dl_mbps": None if dead else (0.5 if weak else 20.0)})
    body = client.post("/api/ingest/readings", headers=h, json={"readings": rows}).json()
    assert body["accepted"] == len(labels), body
    return body


def _find(client, headers, lat, lon):
    items = client.get("/api/complaints?limit=200", headers=headers).json()["items"]
    near = [c for c in items if abs(c["lat"] - lat) < 0.004 and abs(c["lon"] - lon) < 0.004 and c["operator"] == "Airtel"]
    return max(near, key=lambda c: c["id"]) if near else None


def test_dead_zone_registers_then_verifies(client, phone, user_headers, engineer_headers):
    lat, lon = _pt(28.6139, 77.2090, 0, 0)
    now = datetime.now(timezone.utc)
    _send(client, phone, lat, lon, ["Dead"] * 6, now - timedelta(minutes=4))          # 6 readings over 2.5 minutes
    c = _find(client, engineer_headers, lat, lon)
    assert c and c["status"] == "registered" and c["severity"] == "dead" and c["ref_code"].startswith("SS-")
    detail = client.get(f"/api/complaints/{c['id']}", headers=engineer_headers).json()
    assert detail["evidence"]["readings"] >= 6 and detail["evidence"]["classes"]["Dead"] >= 6
    assert detail["summary"] and "Dead" in detail["summary"]
    assert [e["to_status"] for e in detail["events"] if e["kind"] == "status"][:2] == ["detected", "registered"]
    assert len(detail["boundary"]) == 6

    mine = client.get("/api/complaints?mine=true", headers=user_headers).json()["items"]
    assert any(x["id"] == c["id"] for x in mine)                                        # the reporter sees it
    assert client.post(f"/api/complaints/{c['id']}/transition", headers=user_headers, json={"to": "acknowledged"}).status_code == 403

    for to in ("acknowledged", "in_progress", "resolved"):
        r = client.post(f"/api/complaints/{c['id']}/transition", headers=engineer_headers, json={"to": to, "note": f"step {to}"})
        assert r.status_code == 200 and r.json()["status"] == to
    assert client.post(f"/api/complaints/{c['id']}/transition", headers=engineer_headers, json={"to": "acknowledged"}).status_code == 409

    _send(client, phone, lat, lon, ["Strong"] * 3, datetime.now(timezone.utc) + timedelta(seconds=5), step_s=10)
    after = client.get(f"/api/complaints/{c['id']}", headers=engineer_headers).json()
    assert after["status"] == "verified" and after["verification"]["state"] == "verified"


def test_failed_fix_reopens(client, phone, engineer_headers):
    lat, lon = _pt(28.6139, 77.2090, 2000, 0)
    _send(client, phone, lat, lon, ["Weak", "Dead", "Weak", "Dead", "Dead"], datetime.now(timezone.utc) - timedelta(minutes=5))
    c = _find(client, engineer_headers, lat, lon)
    assert c["status"] == "registered"
    client.post(f"/api/complaints/{c['id']}/transition", headers=engineer_headers, json={"to": "in_progress"})
    client.post(f"/api/complaints/{c['id']}/transition", headers=engineer_headers, json={"to": "resolved"})
    _send(client, phone, lat, lon, ["Dead", "Weak", "Dead"], datetime.now(timezone.utc) + timedelta(seconds=5), step_s=10)
    after = client.get(f"/api/complaints/{c['id']}", headers=engineer_headers).json()
    assert after["status"] == "registered" and after["reopen_count"] == 1
    assert any("reopened" in (e["note"] or "") for e in after["events"])


def test_recovered_zone_is_dismissed(client, phone, engineer_headers):
    lat, lon = _pt(28.6139, 77.2090, 4000, 0)
    start = datetime.now(timezone.utc) - timedelta(minutes=6)
    _send(client, phone, lat, lon, ["Dead"] * 4, start, step_s=10)                         # bad for only 30 s
    c = _find(client, engineer_headers, lat, lon)
    assert c["status"] == "detected"
    _send(client, phone, lat, lon, ["Strong"] * 12, start + timedelta(seconds=60), step_s=10)
    assert client.get(f"/api/complaints/{c['id']}", headers=engineer_headers).json()["status"] == "dismissed"


def test_notes_assignment_exports_and_counts(client, engineer_headers):
    items = client.get("/api/complaints?status=registered,verified", headers=engineer_headers).json()
    assert items["counts"]["verified"] >= 1 and items["total"] >= 1
    cid = items["items"][0]["id"]
    eng = client.get("/api/complaints/meta/engineers", headers=engineer_headers).json()
    assert eng
    r = client.post(f"/api/complaints/{cid}/assign", headers=engineer_headers, json={"user_id": eng[0]["id"]})
    assert r.json()["assigned_to_id"] == eng[0]["id"]
    r = client.post(f"/api/complaints/{cid}/notes", headers=engineer_headers, json={"note": "Tower sector checked"})
    assert any(e["note"] == "Tower sector checked" for e in r.json()["events"])
    js = client.get(f"/api/complaints/{cid}/evidence.json", headers=engineer_headers)
    assert js.status_code == 200 and js.json()["ref_code"] == items["items"][0]["ref_code"]
    csv = client.get(f"/api/complaints/{cid}/evidence.csv", headers=engineer_headers)
    assert csv.status_code == 200 and csv.text.startswith("ts,source")


def test_user_report_is_registered_with_evidence(client, user_headers):
    lat, lon = _pt(28.6139, 77.2090, 0, 0)
    r = client.post("/api/complaints", headers=user_headers, json={"lat": lat, "lon": lon, "operator": "Jio", "note": "Calls drop near the market"})
    assert r.status_code == 201 and r.json()["status"] == "registered" and r.json()["origin"] == "user"
    assert "Calls drop near the market" in r.json()["summary"]


def test_admin_settings_and_channels(client, admin_headers, engineer_headers):
    s = client.get("/api/admin/settings", headers=admin_headers).json()
    assert {x["key"] for x in s["settings"]} >= {"detect_min_readings", "detect_persist_min", "verify_min_readings"}
    bad = client.put("/api/admin/settings", headers=admin_headers, json={"detect_bad_share": 5})
    assert bad.status_code == 422
    ok = client.put("/api/admin/settings", headers=admin_headers, json={"detect_window_min": 15}).json()
    assert next(x for x in ok["settings"] if x["key"] == "detect_window_min")["value"] == 15
    tests = client.post("/api/admin/notifications/test", headers=admin_headers).json()
    assert {t["channel"] for t in tests} == {"telegram", "email"} and not any(t["ok"] for t in tests)   # nothing configured in tests
    assert client.get("/api/admin/settings", headers=engineer_headers).status_code == 403
