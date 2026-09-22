"""Analytics: KPIs, dead-zone trends, worst areas, time-of-day patterns, operator comparison, complaint funnel."""
from __future__ import annotations

from datetime import timedelta
from statistics import median

import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.db import get_db, utcnow
from ..core.security import get_current_user, has_role
from ..models import Complaint, Device, Reading, User, ZoneState

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _reading_frame(db: Session, operator: str | None, days: int | None, include_sample: bool, cols=None) -> pd.DataFrame:
    cols = cols or [Reading.ts, Reading.h3_cell, Reading.operator, Reading.source, Reading.zone_label, Reading.rsrp,
                    Reading.latency_ms, Reading.dl_mbps, Reading.lat, Reading.lon]
    q = select(*cols).where(Reading.zone_label.is_not(None), ~((Reading.source == "phone") & (Reading.link == "wifi")))
    if operator:
        q = q.where(Reading.operator == operator)
    if days:
        q = q.where(Reading.ts >= utcnow() - timedelta(days=days))
    if not include_sample:
        q = q.where(Reading.source != "sample_dataset")
    return pd.DataFrame(db.execute(q).all(), columns=[c.key for c in cols])


def _complaints(db: Session, operator: str | None, include_sample: bool) -> list[Complaint]:
    q = db.query(Complaint)
    if operator:
        q = q.filter(Complaint.operator == operator)
    if not include_sample:
        q = q.filter(Complaint.source != "sample_dataset")
    return q.all()


def _hours(a, b) -> float | None:
    return (b - a).total_seconds() / 3600 if a and b and b >= a else None


def _med(vals) -> float | None:
    vals = [v for v in vals if v is not None]
    return round(median(vals), 2) if vals else None


@router.get("/summary", summary="Key figures for the dashboard")
def summary(operator: str | None = None, include_sample: bool = True, user: User = Depends(get_current_user),
            db: Session = Depends(get_db)) -> dict:
    now = utcnow()
    base = select(func.count()).select_from(Reading).where(Reading.zone_label.is_not(None))
    if not include_sample:
        base = base.where(Reading.source != "sample_dataset")
    if operator:
        base = base.where(Reading.operator == operator)
    last24 = db.execute(base.where(Reading.ts >= now - timedelta(hours=24))).scalar() or 0
    total = db.execute(base).scalar() or 0
    zq = db.query(ZoneState)
    if operator:
        zq = zq.filter(ZoneState.operator == operator)
    zones = zq.all()
    bad_zones = [z for z in zones if z.label in ("Weak", "Dead")]
    comps = _complaints(db, operator, include_sample)
    open_c = [c for c in comps if c.status in ("detected", "registered", "acknowledged", "in_progress", "resolved")]
    ttr = [_hours(c.registered_at, c.resolved_at) for c in comps if c.resolved_at]
    ttv = [_hours(c.resolved_at, c.verified_at) for c in comps if c.verified_at and c.resolved_at]
    week = [c for c in comps if c.registered_at and c.registered_at >= now - timedelta(days=7)]
    online = db.query(func.count(Device.id)).filter(Device.last_seen_at >= now - timedelta(minutes=3), Device.kind != "replay").scalar() or 0
    mine = None
    if not has_role(user, "engineer"):
        own = [d for (d,) in db.query(Device.id).filter(Device.owner_id == user.id).all()]
        mine = {"readings": db.query(func.count(Reading.id)).filter(Reading.device_id.in_(own)).scalar() or 0,
                "complaints": db.query(func.count(Complaint.id)).filter(Complaint.reporter_user_id == user.id).scalar() or 0}
    return {
        "readings_total": total, "readings_24h": last24, "zones_monitored": len(zones), "zones_bad": len(bad_zones),
        "zones_dead": sum(1 for z in zones if z.label == "Dead"),
        "bad_zone_share": round(len(bad_zones) / len(zones), 3) if zones else None,
        "complaints_open": len(open_c), "complaints_needing_action": sum(1 for c in comps if c.status == "registered"),
        "complaints_registered_7d": len(week), "complaints_verified": sum(1 for c in comps if c.status == "verified"),
        "median_hours_to_resolve": _med(ttr), "median_hours_to_verify": _med(ttv), "devices_online": online, "mine": mine,
    }


@router.get("/trends", summary="Per day: readings by class and complaints registered / resolved")
def trends(operator: str | None = None, days: int = Query(30, ge=1, le=3650), include_sample: bool = True, tz_offset_min: int = 0,
           user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    df = _reading_frame(db, operator, days, include_sample, [Reading.ts, Reading.zone_label])
    out: dict[str, dict] = {}
    if not df.empty:
        day = (pd.to_datetime(df.ts) + pd.Timedelta(minutes=tz_offset_min)).dt.strftime("%Y-%m-%d")
        g = df.assign(day=day).groupby(["day", "zone_label"]).size().unstack(fill_value=0)
        for d, row in g.iterrows():
            n = int(row.sum())
            out[d] = {"day": d, "readings": n, **{k.lower(): int(row.get(k, 0)) for k in ("Strong", "Weak", "Dead")},
                      "weak_share": round(row.get("Weak", 0) / n, 3), "dead_share": round(row.get("Dead", 0) / n, 3),
                      "registered": 0, "resolved": 0}
    since = utcnow() - timedelta(days=days)
    for c in _complaints(db, operator, include_sample):
        for field, key in (("registered_at", "registered"), ("resolved_at", "resolved")):
            t = getattr(c, field)
            if t and t >= since:
                d = (t + timedelta(minutes=tz_offset_min)).strftime("%Y-%m-%d")
                out.setdefault(d, {"day": d, "readings": 0, "strong": 0, "weak": 0, "dead": 0, "weak_share": None, "dead_share": None, "registered": 0, "resolved": 0})
                out[d][key] += 1
    return {"days": [out[k] for k in sorted(out)]}


@router.get("/worst-areas", summary="Zones with the highest share of Weak/Dead readings")
def worst_areas(operator: str | None = None, days: int | None = Query(None, ge=1, le=3650), include_sample: bool = True,
                min_readings: int = Query(20, ge=1), limit: int = Query(10, ge=1, le=50), user: User = Depends(get_current_user),
                db: Session = Depends(get_db)) -> list[dict]:
    df = _reading_frame(db, operator, days, include_sample)
    if df.empty:
        return []
    rows = []
    for (cell, op), g in df.groupby(["h3_cell", "operator"]):
        n = len(g)
        if n < min_readings:
            continue
        c = g.zone_label.value_counts()
        rows.append({"cell": cell, "operator": op, "readings": n, "bad_share": round((c.get("Weak", 0) + c.get("Dead", 0)) / n, 3),
                     "dead_share": round(c.get("Dead", 0) / n, 3), "lat": round(float(g.lat.mean()), 5), "lon": round(float(g.lon.mean()), 5),
                     "median_rsrp": _med(g.rsrp.dropna().tolist()), "median_latency": _med(g.latency_ms.dropna().tolist()),
                     "last": pd.to_datetime(g.ts.max()).isoformat() + "Z", "sources": sorted(g.source.unique().tolist())})
    rows.sort(key=lambda r: (r["bad_share"], r["dead_share"], r["readings"]), reverse=True)
    open_by_zone = {(c.h3_cell, c.operator): c for c in db.query(Complaint).filter(Complaint.status.in_(("detected", "registered", "acknowledged", "in_progress", "resolved"))).all()}
    for r in rows[:limit]:
        c = open_by_zone.get((r["cell"], r["operator"]))
        r["complaint"] = {"id": c.id, "ref_code": c.ref_code, "status": c.status} if c else None
    return rows[:limit]


@router.get("/time-of-day", summary="Share of Weak/Dead readings by weekday and hour (viewer's local time)")
def time_of_day(operator: str | None = None, days: int | None = Query(None, ge=1, le=3650), include_sample: bool = True,
                tz_offset_min: int = 0, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    df = _reading_frame(db, operator, days, include_sample, [Reading.ts, Reading.zone_label])
    cells = []
    if not df.empty:
        t = pd.to_datetime(df.ts) + pd.Timedelta(minutes=tz_offset_min)
        g = df.assign(wd=t.dt.weekday, hr=t.dt.hour, bad=df.zone_label.isin(["Weak", "Dead"])).groupby(["wd", "hr"]).bad.agg(["mean", "size"])
        cells = [{"weekday": int(wd), "hour": int(hr), "bad_share": round(float(r["mean"]), 3), "readings": int(r["size"])} for (wd, hr), r in g.iterrows()]
    return {"cells": cells}


@router.get("/operators", summary="Operator comparison")
def operators(days: int | None = Query(None, ge=1, le=3650), include_sample: bool = True, user: User = Depends(get_current_user),
              db: Session = Depends(get_db)) -> list[dict]:
    df = _reading_frame(db, None, days, include_sample)
    comps = _complaints(db, None, include_sample)
    out = []
    if df.empty:
        return out
    for op, g in df.groupby("operator"):
        n = len(g)
        c = g.zone_label.value_counts()
        oc = [x for x in comps if x.operator == op]
        out.append({"operator": op, "readings": n, "zones": int(g.h3_cell.nunique()),
                    "strong_share": round(c.get("Strong", 0) / n, 3), "weak_share": round(c.get("Weak", 0) / n, 3), "dead_share": round(c.get("Dead", 0) / n, 3),
                    "median_rsrp": _med(g.rsrp.dropna().tolist()), "median_latency": _med(g.latency_ms.dropna().tolist()), "median_dl": _med(g.dl_mbps.dropna().tolist()),
                    "complaints_total": len(oc), "complaints_open": sum(1 for x in oc if x.status in ("registered", "acknowledged", "in_progress", "resolved")),
                    "median_hours_to_resolve": _med([_hours(x.registered_at, x.resolved_at) for x in oc if x.resolved_at]),
                    "sources": sorted(g.source.unique().tolist())})
    return sorted(out, key=lambda r: -r["readings"])


@router.get("/complaint-funnel", summary="Complaints reaching each stage, and the median time between stages")
def funnel(operator: str | None = None, include_sample: bool = True, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    comps = _complaints(db, operator, include_sample)
    stages = [("detected", "detected_at"), ("registered", "registered_at"), ("acknowledged", "acknowledged_at"),
              ("in_progress", "in_progress_at"), ("resolved", "resolved_at"), ("verified", "verified_at")]
    counts = [{"stage": s, "reached": sum(1 for c in comps if getattr(c, f))} for s, f in stages]
    gaps = []
    for (a, fa), (b, fb) in zip(stages, stages[1:]):
        gaps.append({"from": a, "to": b, "median_hours": _med([_hours(getattr(c, fa), getattr(c, fb)) for c in comps if getattr(c, fa) and getattr(c, fb)])})
    return {"stages": counts, "gaps": gaps, "dismissed": sum(1 for c in comps if c.status == "dismissed"),
            "reopened": sum(1 for c in comps if c.reopen_count > 0)}
