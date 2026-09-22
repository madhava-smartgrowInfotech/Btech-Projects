"""Known cell-tower positions near a place, from OpenCelliD. Active only when OPENCELLID_API_KEY is set.

Towers are cached in the cell_towers table and an area is fetched from the API at most once a week,
which keeps well inside the free daily request limit.
"""
from __future__ import annotations

import json
import logging
import math
import threading
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.db import utcnow
from ..models import CellTower

log = logging.getLogger("signalscout.opencellid")
API = "https://opencellid.org/cell/getInArea"
REFRESH = timedelta(days=7)
MAX_RADIUS_M = 1000          # the API accepts at most 4 km² per request (a 2 km x 2 km box)
_fetched: dict[str, datetime] = {}
_lock = threading.Lock()


class OpenCellIdError(Exception):
    pass


def api_key() -> str:
    return settings.opencellid_api_key


def enabled() -> bool:
    return bool(api_key())


def _box(lat: float, lon: float, radius_m: float) -> tuple[float, float, float, float]:
    dlat = radius_m / 111_320
    dlon = radius_m / (111_320 * max(math.cos(math.radians(lat)), 0.01))
    return lat - dlat, lon - dlon, lat + dlat, lon + dlon


def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(a))


def _fetch(box: tuple[float, float, float, float]) -> list[dict]:
    """Calls the OpenCelliD API; returns the raw cell records."""
    query = urllib.parse.urlencode({"key": api_key(), "BBOX": ",".join(f"{v:.6f}" for v in box), "format": "json", "limit": 50})
    req = urllib.request.Request(f"{API}?{query}", headers={"User-Agent": "SignalScout/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise OpenCellIdError(f"OpenCelliD could not be reached ({exc.__class__.__name__})") from exc
    if isinstance(data, dict) and data.get("error"):
        raise OpenCellIdError(f"OpenCelliD: {data['error']}")
    return data.get("cells", []) if isinstance(data, dict) else []


def _store(db: Session, cells: list[dict]) -> None:
    for c in cells:
        try:
            mcc, mnc, cell = int(c["mcc"]), int(c["mnc"]), int(c.get("cellid") or c.get("cid"))
            area = int(c.get("lac") or c.get("tac") or 0)
            lat, lon = float(c["lat"]), float(c["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        row = db.query(CellTower).filter_by(mcc=mcc, mnc=mnc, area=area, cell=cell).first() or CellTower(mcc=mcc, mnc=mnc, area=area, cell=cell)
        row.radio, row.lat, row.lon = c.get("radio"), lat, lon
        row.range_m = float(c["range"]) if c.get("range") not in (None, "") else None
        row.fetched_at = utcnow()
        db.add(row)
    db.commit()


def towers_near(db: Session, lat: float, lon: float, radius_m: float = MAX_RADIUS_M, serving: set[int] | None = None) -> list[dict]:
    """Towers within radius_m, nearest first. Fetches the area from OpenCelliD when it is not cached."""
    radius_m = min(radius_m, MAX_RADIUS_M)
    box = _box(lat, lon, radius_m)
    key = f"{lat:.3f},{lon:.3f},{int(radius_m)}"
    with _lock:
        stale = key not in _fetched or utcnow() - _fetched[key] > REFRESH
    if stale:
        cells = _fetch(box)
        _store(db, cells)
        with _lock:
            _fetched[key] = utcnow()
        log.info("opencellid area=%s towers=%d", key, len(cells))
    rows = (db.query(CellTower).filter(CellTower.lat.between(box[0], box[2]), CellTower.lon.between(box[1], box[3])).all())
    out = []
    for r in rows:
        d = _distance_m(lat, lon, r.lat, r.lon)
        if d <= radius_m:
            out.append({"radio": r.radio, "mcc": r.mcc, "mnc": r.mnc, "area": r.area, "cell": r.cell, "lat": r.lat, "lon": r.lon,
                        "range_m": r.range_m, "distance_m": round(d), "serving": bool(serving and r.cell in serving)})
    return sorted(out, key=lambda t: t["distance_m"])
