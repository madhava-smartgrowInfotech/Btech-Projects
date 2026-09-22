"""Provision the simulated ESP32 nodes (used when there is no hardware) and hand their keys to the simulator.

Nodes are placed around ESP32_SIMULATOR_LAT/LON when set; otherwise near the most recent phone readings,
otherwise near the sample data. Keys are rotated at every start and written to data/runtime/simulator.json
(git-ignored), which scripts/esp32_simulator.py reads.
"""
from __future__ import annotations

import json
import logging
import math
import os

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.db import utcnow
from ..core.logging import log_event
from ..core.security import new_device_key
from ..models import Device, Reading, User

log = logging.getLogger("signalscout.simulator")

NODE_TEMPLATES = [
    {"name": "Market square node", "network_name": "Market square Wi-Fi", "profile": "strong", "offset_m": (180, 120)},
    {"name": "Health centre node", "network_name": "Health centre Wi-Fi", "profile": "weak", "offset_m": (-260, 90)},
    {"name": "Bus stand node", "network_name": "Bus stand Wi-Fi", "profile": "flaky", "offset_m": (60, -310)},
    {"name": "Water works node", "network_name": "Water works Wi-Fi", "profile": "weak", "offset_m": (420, -60)},
    {"name": "Library node", "network_name": "Library Wi-Fi", "profile": "strong", "offset_m": (-120, -420)},
]
DEFAULT_CENTER = (51.8969, -8.4863)   # the replayed public drive-test area


def _median(db: Session, source: str, days: int | None = None) -> tuple[float, float] | None:
    q = db.query(Reading.lat, Reading.lon).filter(Reading.source == source)
    if source == "phone":
        q = q.filter(Reading.link != "wifi")
    rows = q.order_by(Reading.ts.desc()).limit(300).all()
    if not rows:
        return None
    lats, lons = sorted(r[0] for r in rows), sorted(r[1] for r in rows)
    return lats[len(lats) // 2], lons[len(lons) // 2]


def simulator_center(db: Session) -> tuple[float, float, str]:
    lat, lon = os.environ.get("ESP32_SIMULATOR_LAT", "").strip(), os.environ.get("ESP32_SIMULATOR_LON", "").strip()
    if lat and lon:
        try:
            return float(lat), float(lon), "configured location"
        except ValueError:
            pass
    phone = _median(db, "phone")
    if phone:
        return phone[0], phone[1], "your recent phone readings"
    sample = _median(db, "sample_dataset")
    if sample:
        return sample[0], sample[1], "the sample data area"
    return DEFAULT_CENTER[0], DEFAULT_CENTER[1], "the sample data area"


def _offset(lat: float, lon: float, east_m: float, north_m: float) -> tuple[float, float]:
    return lat + math.degrees(north_m / 6_371_008.8), lon + math.degrees(east_m / (6_371_008.8 * math.cos(math.radians(lat))))


def ensure_simulator_devices(db: Session) -> list[dict]:
    count = max(0, min(int(os.environ.get("ESP32_SIMULATOR_NODES", "3") or 3), len(NODE_TEMPLATES)))
    interval = int(os.environ.get("ESP32_SIMULATOR_INTERVAL_S", "15") or 15)
    admin = db.query(User).filter(User.role == "admin").order_by(User.id).first()
    if not admin or count == 0:
        return []
    lat0, lon0, basis = simulator_center(db)
    existing = db.query(Device).filter(Device.kind == "simulator").order_by(Device.id).all()
    nodes = []
    for i in range(count):
        tpl = NODE_TEMPLATES[i]
        lat, lon = _offset(lat0, lon0, *tpl["offset_m"])
        key, key_hash, prefix = new_device_key()
        if i < len(existing):
            d = existing[i]
            d.api_key_hash, d.api_key_prefix, d.is_active = key_hash, prefix, True
        else:
            d = Device(owner_id=admin.id, kind="simulator", name=tpl["name"], api_key_hash=key_hash, api_key_prefix=prefix,
                       hardware="Simulated ESP32 + NEO-6M", firmware="sim-1.0", config={})
            db.add(d)
        d.fixed_lat, d.fixed_lon = lat, lon
        d.config = {**(d.config or {}), "network_name": tpl["network_name"], "profile": tpl["profile"], "placed_near": basis}
        nodes.append((d, key, tpl))
    for d in existing[count:]:
        d.is_active = False
    db.commit()
    payload = [{"id": d.id, "name": d.name, "key": key, "lat": d.fixed_lat, "lon": d.fixed_lon, "profile": tpl["profile"],
                "network_name": tpl["network_name"], "interval_s": interval, "index": i} for i, (d, key, tpl) in enumerate(nodes)]
    settings.runtime_dir.mkdir(parents=True, exist_ok=True)
    (settings.runtime_dir / "simulator.json").write_text(json.dumps({"written_at": utcnow().isoformat() + "Z", "nodes": payload}, indent=2), encoding="utf-8")
    log_event(log, "simulated nodes ready", nodes=len(payload), placed_near=basis)
    return payload


def reading_center_count(db: Session) -> int:
    return db.query(func.count(Reading.id)).filter(Reading.source == "phone").scalar() or 0
