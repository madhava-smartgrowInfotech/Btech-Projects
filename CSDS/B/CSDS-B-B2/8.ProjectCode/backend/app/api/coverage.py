"""Coverage map data: hexagon zones, heat points, recent readings, sensor nodes and a live event stream."""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import timedelta

import h3
import pandas as pd
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.db import get_db, utcnow
from ..core.security import get_current_user, get_current_user_sse, has_role
from ..models import Device, Reading, User
from ..services import events
from ..services.sample_data import status as sample_status

router = APIRouter(prefix="/api/coverage", tags=["coverage"])
LABELS = ["Strong", "Weak", "Dead"]


@dataclass
class Filters:
    operator: str | None = None
    sources: str | None = None
    days: int | None = None
    hour_from: int | None = None
    hour_to: int | None = None
    tz_offset_min: int = 0
    include_wifi: bool = False


def filters(operator: str | None = Query(None, description="Only this operator"),
            sources: str | None = Query(None, description="Comma list: phone, esp32, simulator, sample_dataset"),
            days: int | None = Query(None, ge=1, le=3650, description="Only the last N days"),
            hour_from: int | None = Query(None, ge=0, le=23, description="Local hour-of-day window start"),
            hour_to: int | None = Query(None, ge=0, le=24, description="Local hour-of-day window end (exclusive)"),
            tz_offset_min: int = Query(0, ge=-840, le=840, description="Viewer's offset from UTC in minutes (India: 330)"),
            include_wifi: bool = Query(False, description="Include phone readings taken over Wi-Fi")) -> Filters:
    return Filters(operator, sources, days, hour_from, hour_to, tz_offset_min, include_wifi)


COLUMNS = [Reading.id, Reading.ts, Reading.lat, Reading.lon, Reading.h3_cell, Reading.operator, Reading.source, Reading.link,
           Reading.zone_label, Reading.zone_confidence, Reading.rsrp, Reading.latency_ms, Reading.dl_mbps, Reading.wifi_rssi, Reading.device_id]


def load(db: Session, f: Filters, limit: int | None = None, newest_first: bool = False) -> pd.DataFrame:
    q = select(*COLUMNS).where(Reading.zone_label.is_not(None))
    if f.operator:
        q = q.where(Reading.operator == f.operator)
    if f.sources:
        q = q.where(Reading.source.in_([s.strip() for s in f.sources.split(",") if s.strip()]))
    if f.days:
        q = q.where(Reading.ts >= utcnow() - timedelta(days=f.days))
    if not f.include_wifi:
        q = q.where(~((Reading.source == "phone") & (Reading.link == "wifi")))
    if newest_first:
        q = q.order_by(Reading.ts.desc())
    if limit:
        q = q.limit(limit)
    df = pd.DataFrame(db.execute(q).all(), columns=[c.key for c in COLUMNS])
    if df.empty or f.hour_from is None or f.hour_to is None:
        return df
    ts = pd.to_datetime(df.ts)
    local_hour = ((ts.dt.hour * 60 + ts.dt.minute + f.tz_offset_min) // 60) % 24
    lo, hi = f.hour_from, f.hour_to % 24 if f.hour_to != 24 else 24
    keep = (local_hour >= lo) & (local_hour < hi) if lo < hi else (local_hour >= lo) | (local_hour < hi)
    return df[keep.to_numpy()]


def cell_label(strong: int, weak: int, dead: int) -> str:
    """Majority class; ties go to the worse class."""
    counts = {"Dead": dead, "Weak": weak, "Strong": strong}
    return max(counts, key=lambda k: (counts[k], ["Strong", "Weak", "Dead"].index(k)))


def _median(s: pd.Series) -> float | None:
    s = s.dropna()
    return round(float(s.median()), 2) if len(s) else None


@router.get("/summary")
def summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    ops = db.execute(select(Reading.operator, func.count()).where(Reading.zone_label.is_not(None))
                     .where(~((Reading.source == "phone") & (Reading.link == "wifi"))).group_by(Reading.operator)
                     .order_by(func.count().desc())).all()
    srcs = db.execute(select(Reading.source, func.count()).group_by(Reading.source)).all()
    lo = db.execute(select(func.min(Reading.ts), func.max(Reading.ts), func.min(Reading.lat), func.max(Reading.lat),
                           func.min(Reading.lon), func.max(Reading.lon), func.count())).one()
    return {
        "operators": [{"name": o, "readings": n} for o, n in ops],
        "sources": [{"name": s, "readings": n} for s, n in srcs],
        "first_ts": lo[0].isoformat() + "Z" if lo[0] else None, "last_ts": lo[1].isoformat() + "Z" if lo[1] else None,
        "bounds": [[lo[2], lo[4]], [lo[3], lo[5]]] if lo[2] is not None else None, "total": lo[6],
        "sample_data": dict(sample_status),
    }


@router.get("/hex", summary="H3 hexagon zones as GeoJSON with class shares")
def hexes(f: Filters = Depends(filters), resolution: int = Query(None, ge=6, le=11), user: User = Depends(get_current_user),
          db: Session = Depends(get_db)) -> dict:
    res = resolution or settings.h3_resolution
    df = load(db, f)
    features = []
    if not df.empty:
        cells = df.h3_cell if res == settings.h3_resolution else pd.Series([h3.cell_to_parent(c, res) if h3.get_resolution(c) > res
                                                                           else h3.latlng_to_cell(a, b, res) for c, a, b in zip(df.h3_cell, df.lat, df.lon)], index=df.index)
        df = df.assign(cell=cells)
        for cell, g in df.groupby("cell"):
            counts = g.zone_label.value_counts()
            s, w, d = (int(counts.get(k, 0)) for k in LABELS)
            ops = {op: {"n": int(len(og)), "label": cell_label(*(int(og.zone_label.eq(k).sum()) for k in LABELS))} for op, og in g.groupby("operator")}
            boundary = [[lng, lat] for lat, lng in h3.cell_to_boundary(cell)]
            features.append({
                "type": "Feature", "geometry": {"type": "Polygon", "coordinates": [boundary + boundary[:1]]},
                "properties": {"cell": cell, "n": s + w + d, "strong": s, "weak": w, "dead": d, "label": cell_label(s, w, d),
                               "bad_share": round((w + d) / max(s + w + d, 1), 3), "confidence": _median(g.zone_confidence),
                               "median_rsrp": _median(g.rsrp), "median_latency": _median(g.latency_ms), "median_dl": _median(g.dl_mbps),
                               "median_wifi_rssi": _median(g.wifi_rssi), "last_ts": pd.to_datetime(g.ts.max()).isoformat() + "Z",
                               "sources": sorted(g.source.unique().tolist()), "operators": ops,
                               "center": list(h3.cell_to_latlng(cell))},
            })
    return {"type": "FeatureCollection", "features": features, "resolution": res, "readings": int(len(df))}


@router.get("/heat", summary="Weighted points for the heat layer")
def heat(f: Filters = Depends(filters), mode: str = Query("problems", pattern="^(problems|coverage)$"),
         user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    df = load(db, f)
    if df.empty:
        return {"points": [], "mode": mode}
    weights = {"problems": {"Strong": 0.0, "Weak": 0.55, "Dead": 1.0}, "coverage": {"Strong": 1.0, "Weak": 0.45, "Dead": 0.08}}[mode]
    df = df.assign(w=df.zone_label.map(weights).astype(float), glat=df.lat.round(4), glon=df.lon.round(4))
    g = df.groupby(["glat", "glon"]).w.mean().reset_index()
    g = g[g.w > 0].nlargest(30000, "w") if len(g) > 30000 else g[g.w > 0]
    return {"points": g[["glat", "glon", "w"]].round(4).values.tolist(), "mode": mode}


@router.get("/points", summary="Most recent individual readings")
def points(f: Filters = Depends(filters), limit: int = Query(400, ge=1, le=2000), user: User = Depends(get_current_user),
           db: Session = Depends(get_db)) -> list[dict]:
    df = load(db, f, limit=limit, newest_first=True)
    own = set() if has_role(user, "engineer") else {d for (d,) in db.query(Device.id).filter(Device.owner_id == user.id).all()}
    out = []
    for r in df.itertuples():
        out.append({"id": r.id, "ts": pd.to_datetime(r.ts).isoformat() + "Z", "lat": r.lat, "lon": r.lon, "label": r.zone_label,
                    "confidence": None if pd.isna(r.zone_confidence) else r.zone_confidence, "operator": r.operator, "source": r.source,
                    "rsrp": None if pd.isna(r.rsrp) else r.rsrp, "latency_ms": None if pd.isna(r.latency_ms) else r.latency_ms,
                    "dl_mbps": None if pd.isna(r.dl_mbps) else r.dl_mbps, "wifi_rssi": None if pd.isna(r.wifi_rssi) else r.wifi_rssi,
                    "mine": r.device_id in own})
    return out


@router.get("/nodes", summary="Sensor nodes with their latest state")
def nodes(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    out = []
    for d in db.query(Device).filter(Device.kind.in_(("esp32", "simulator")), Device.is_active.is_(True), Device.fixed_lat.is_not(None)).all():
        last = db.query(Reading).filter(Reading.device_id == d.id).order_by(Reading.ts.desc()).first()
        online = bool(d.last_seen_at and utcnow() - d.last_seen_at <= timedelta(minutes=3))
        out.append({"id": d.id, "name": d.name, "kind": d.kind, "lat": d.fixed_lat, "lon": d.fixed_lon, "online": online,
                    "network_name": (d.config or {}).get("network_name"), "last_seen_at": d.last_seen_at.isoformat() + "Z" if d.last_seen_at else None,
                    "label": last.zone_label if last else None, "wifi_rssi": last.wifi_rssi if last else None,
                    "latency_ms": last.latency_ms if last else None})
    return out


@router.get("/stream", summary="Live events (Server-Sent Events): new readings and complaint updates")
async def stream(request: Request, user: User = Depends(get_current_user_sse)) -> StreamingResponse:
    queue = events.subscribe()

    async def gen():
        try:
            yield "retry: 5000\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    ev = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"event: {ev['type']}\ndata: {json.dumps(ev['data'], default=str)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            events.unsubscribe(queue)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"})
