"""Ingestion: phone-probe batches, idempotent sync, validation, ESP32 nodes, radio readings, visibility."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.core.db import SessionLocal
from app.core.security import new_device_key
from app.models import Device, User


def _now(offset_s: float = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).isoformat()


def _pair(client, headers, name="Test phone") -> str:
    r = client.post("/api/devices/phone", headers=headers, json={"name": name, "hardware": "Chrome 140 on Android 15"})
    assert r.status_code == 201, r.text
    assert r.json()["api_key"].startswith("ssk_")
    return r.json()["api_key"]


def _probe(ts_offset=0, **kw):
    base = {"client_uuid": str(uuid.uuid4()), "ts": _now(ts_offset), "lat": 17.4485, "lon": 78.3908, "accuracy_m": 8,
            "connection_type": "cellular", "operator": "Jio", "connected": True, "probes_sent": 3, "probes_ok": 3,
            "latency_ms": 65.0, "jitter_ms": 8.0, "dl_mbps": 21.5, "ul_mbps": 6.1}
    base.update(kw)
    return base


def test_phone_probe_batch_is_classified_and_idempotent(client, user_headers):
    key = _pair(client, user_headers)
    h = {"X-Device-Key": key}
    batch = [_probe(-30), _probe(-20, latency_ms=720.0, dl_mbps=0.9), _probe(-10, connected=False, probes_ok=0, latency_ms=None, dl_mbps=None, ul_mbps=None)]
    r = client.post("/api/ingest/readings", headers=h, json={"readings": batch})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["accepted"] == 3 and body["duplicates"] == 0 and body["operator"] == "Jio" and body["link"] == "cellular"
    labels = [x["zone_label"] for x in body["results"]]
    assert labels == ["Strong", "Weak", "Dead"]
    assert all(x["label_method"] == "service-bands" for x in body["results"])
    assert body["results"][0]["radio_estimate"] in ("Strong", "Weak", "Dead")

    again = client.post("/api/ingest/readings", headers=h, json={"readings": batch}).json()   # re-sent after a lost reply
    assert again["accepted"] == 0 and again["duplicates"] == 3


def test_bad_readings_are_rejected_not_stored(client, user_headers):
    h = {"X-Device-Key": _pair(client, user_headers, "Clock-skew phone")}
    body = client.post("/api/ingest/readings", headers=h, json={"readings": [_probe(3600), _probe(lat=0.0, lon=0.0), _probe()]}).json()
    assert body["accepted"] == 1 and body["rejected"] == 2
    errors = [x["error"] for x in body["results"] if x["status"] == "rejected"]
    assert any("future" in e for e in errors) and any("GPS" in e for e in errors)


def test_missing_or_wrong_device_key(client):
    assert client.post("/api/ingest/readings", json={"readings": [_probe()]}).status_code == 401
    assert client.post("/api/ingest/readings", headers={"X-Device-Key": "ssk_wrong"}, json={"readings": [_probe()]}).status_code == 401


def test_esp32_node_uses_fixed_location_and_uploads_buffer(client, admin_headers):
    r = client.post("/api/devices", headers=admin_headers, json={"kind": "esp32", "name": "Bench node", "fixed_lat": 17.45, "fixed_lon": 78.39,
                                                                 "network_name": "Panchayat Wi-Fi"})
    assert r.status_code == 201
    key = r.json()["api_key"]
    buffered = [{"seq": i, "ts": _now(-60 + i * 10), "wifi_rssi": -58 - i * 8, "latency_ms": 40, "packet_loss": 0.0, "connected": True} for i in range(4)]
    buffered.append({"seq": 9, "ts": _now(), "connected": False})
    body = client.post("/api/ingest/node", headers={"X-Device-Key": key}, json={"firmware": "1.2.0", "readings": buffered}).json()
    assert body["accepted"] == 5
    # -58, -66 (>= -67: Strong), -74 (Weak), -82 (Dead), link down (Dead)
    assert [x["zone_label"] for x in body["results"]] == ["Strong", "Strong", "Weak", "Dead", "Dead"]
    assert body["operator"] == "Panchayat Wi-Fi" and body["link"] == "wifi"
    dup = client.post("/api/ingest/node", headers={"X-Device-Key": key}, json={"readings": buffered}).json()
    assert dup["duplicates"] == 5
    phone_key = _pair(client, admin_headers, "Not a node")
    assert client.post("/api/ingest/node", headers={"X-Device-Key": phone_key}, json={"readings": buffered}).status_code == 400


def test_radio_readings_use_the_trained_model(client):
    with SessionLocal() as db:
        admin = db.query(User).filter(User.role == "admin").first()
        key, key_hash, prefix = new_device_key()
        db.add(Device(owner_id=admin.id, kind="replay", name="Trace replay (test)", api_key_hash=key_hash, api_key_prefix=prefix, config={}))
        db.commit()
    readings = [
        {"client_uuid": str(uuid.uuid4()), "ts": _now(-20), "lat": 51.9, "lon": -8.48, "operator": "Operator A", "network_type": "LTE",
         "rsrp": -79, "rsrq": -8, "sinr": 21, "rssi": -52, "cqi": 13},
        {"client_uuid": str(uuid.uuid4()), "ts": _now(-15), "lat": 51.9, "lon": -8.48, "operator": "Operator A", "network_type": "LTE",
         "rsrp": -122, "rsrq": -17, "sinr": -7},
    ]
    body = client.post("/api/ingest/readings", headers={"X-Device-Key": key}, json={"readings": readings}).json()
    assert [x["zone_label"] for x in body["results"]] == ["Strong", "Dead"]
    assert body["results"][1]["reasons"] and "RSRP" in body["results"][1]["reasons"][0]


def test_readings_visibility_and_export(client, user_headers, engineer_headers):
    mine = client.get("/api/readings?mine=true&limit=50", headers=user_headers).json()
    assert mine and all(r["source"] == "phone" for r in mine)
    everything = client.get("/api/readings?limit=500", headers=engineer_headers).json()
    assert {r["source"] for r in everything} >= {"phone", "esp32"}
    own_devices = {d["id"] for d in client.get("/api/devices", headers=user_headers).json()}
    user_view = client.get("/api/readings?limit=500", headers=user_headers).json()
    assert not any(r["source"] == "phone" and r["device_id"] not in own_devices for r in user_view)   # no other people's phones
    csv = client.get("/api/readings/export.csv?mine=true", headers=user_headers)
    assert csv.status_code == 200 and csv.text.splitlines()[0].startswith("id,ts,source")


def test_devices_list_and_key_rotation(client, user_headers):
    devices = client.get("/api/devices", headers=user_headers).json()
    assert devices and all(d["kind"] == "phone" for d in devices)
    d = devices[0]
    assert d["online"] is True or d["readings_count"] == 0
    new = client.post(f"/api/devices/{d['id']}/rotate-key", headers=user_headers).json()
    assert new["api_key"].startswith("ssk_") and new["device"]["api_key_prefix"] == new["api_key"][:10]
    renamed = client.patch(f"/api/devices/{d['id']}", headers=user_headers, json={"name": "Field phone"}).json()
    assert renamed["name"] == "Field phone"


def test_probe_endpoints(client, user_headers):
    key = _pair(client, user_headers, "Speed-test phone")
    h = {"X-Device-Key": key}
    ping = client.get("/api/probe/ping")
    assert ping.status_code == 200 and "no-store" in ping.headers["cache-control"]
    dl = client.get("/api/probe/download?bytes=300000", headers=h)
    assert dl.status_code == 200 and len(dl.content) == 300000 and dl.headers["content-type"] == "application/octet-stream"
    assert client.get("/api/probe/download?bytes=300000").status_code == 401        # speed tests need a device key
    up = client.post("/api/probe/upload", headers=h, content=b"x" * 150000)
    assert up.status_code == 200 and up.json()["bytes"] == 150000
    who = client.get("/api/probe/whoami", headers={**h, "CF-Connecting-IP": "49.36.0.10"})   # a Jio address, as the tunnel reports it
    body = who.json()
    assert body["config"]["interval_s"] > 0 and body["carrier"]["ip"].endswith(".x.x") and body["carrier"]["operator"] == "Jio"
    local = client.get("/api/probe/whoami", headers=h).json()
    assert local["carrier"]["kind"] in ("local", "unknown")


def test_forwarded_ip_trusted_only_from_this_pc():
    from app.services.carrier import client_ip
    fwd = {"cf-connecting-ip": "49.36.0.10"}
    assert client_ip(fwd, "127.0.0.1") == "49.36.0.10"          # through the local tunnel
    assert client_ip(fwd, "192.168.1.40") == "192.168.1.40"     # a phone on the LAN cannot choose its carrier
    assert client_ip({}, "203.0.113.9") == "203.0.113.9"
