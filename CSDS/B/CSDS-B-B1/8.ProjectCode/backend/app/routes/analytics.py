"""Hotspot map and governance analytics (F7). Computed live from the database on every request."""
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import staff
from ..db import Complaint, Feedback, User, Ward, get_db
from .complaints import CLOSED, sla_map

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _cat(c):
    return c.final_category or (c.ai or {}).get("category")


def _dept(c):
    return c.final_department or (c.ai or {}).get("department")


def _prio(c):
    return c.final_priority or (c.ai or {}).get("priority")


def _days_open(c, now):
    return ((c.resolved_at or now) - c.created_at).total_seconds() / 86400


@router.get("/summary")
def summary(user: User = Depends(staff), db: Session = Depends(get_db)):
    now = datetime.now()
    slas = sla_map(db)
    rows = db.query(Complaint).all()
    resolved = [c for c in rows if c.status == "Resolved" and c.resolved_at]
    open_ = [c for c in rows if c.status not in CLOSED]
    within = [c for c in resolved if _days_open(c, now) <= slas.get(_dept(c), 999)]
    breached_open = [c for c in open_ if _days_open(c, now) > slas.get(_dept(c), 999)]
    # how close the time estimate was on complaints that are now resolved
    errs = [abs(_days_open(c, now) - c.final_days) for c in resolved if c.final_days is not None]
    fb = db.query(Feedback).all()
    acc = {}
    for field in ("category", "department", "priority"):
        f = [x for x in fb if x.field == field]
        acc[field] = {"reviewed": len(f), "accepted": sum(x.action == "accept" for x in f),
                      "rate": round(sum(x.action == "accept" for x in f) / len(f), 3) if f else None}
    return {
        "total": len(rows),
        "open": len(open_),
        "awaiting_review": sum(c.status == "Submitted" for c in rows),
        "filed_last_24h": sum(c.created_at >= now - timedelta(days=1) for c in rows),
        "resolved_last_30d": sum(c.resolved_at >= now - timedelta(days=30) for c in resolved),
        "sla_compliance": round(len(within) / len(resolved), 3) if resolved else None,
        "open_sla_breached": len(breached_open),
        "avg_resolution_days": round(sum(_days_open(c, now) for c in resolved) / len(resolved), 2) if resolved else None,
        "time_estimate_mae_days": round(sum(errs) / len(errs), 2) if errs else None,
        "by_status": dict(Counter(c.status for c in rows)),
        "open_by_priority": dict(Counter(_prio(c) for c in open_)),
        "by_language": dict(Counter(c.language for c in rows)),
        "ai_acceptance": acc,
        "updated_at": now.isoformat(timespec="seconds"),
    }


@router.get("/hotspots")
def hotspots(days: int = 30, category: str = "", user: User = Depends(staff), db: Session = Depends(get_db)):
    now = datetime.now()
    since = now - timedelta(days=days)
    rows = [c for c in db.query(Complaint).filter(Complaint.created_at >= since).all()
            if not category or _cat(c) == category]
    wards = {w.id: w for w in db.query(Ward).all()}
    per = defaultdict(list)
    for c in rows:
        if c.ward_id:
            per[c.ward_id].append(c)
    ward_rows, recurring = [], []
    for wid, cs in per.items():
        cats = Counter(_cat(c) for c in cs)
        top, top_n = cats.most_common(1)[0]
        w = wards[wid]
        ward_rows.append({"ward": w.name, "lat": w.lat, "lng": w.lng, "total": len(cs),
                          "open": sum(c.status not in CLOSED for c in cs),
                          "critical_or_high": sum(_prio(c) in ("High", "Critical") for c in cs),
                          "top_category": top, "top_count": top_n})
        for cat, n in cats.items():
            if n >= 3:  # the same issue reported 3+ times in one ward in the window
                recurring.append({"ward": w.name, "category": cat, "count": n,
                                  "open": sum(c.status not in CLOSED and _cat(c) == cat for c in cs)})
    ward_rows.sort(key=lambda r: -r["total"])
    recurring.sort(key=lambda r: -r["count"])
    points = [{"id": c.id, "tracking_id": c.tracking_id, "lat": c.lat, "lng": c.lng, "category": _cat(c),
               "priority": _prio(c), "status": c.status} for c in rows if c.lat is not None]
    return {"days": days, "wards": ward_rows, "recurring": recurring[:20], "points": points}


@router.get("/sla")
def sla(user: User = Depends(staff), db: Session = Depends(get_db)):
    now = datetime.now()
    slas = sla_map(db)
    out = {d: {"department": d, "sla_days": s, "open": 0, "open_breached": 0, "resolved": 0, "within_sla": 0,
               "total_days": 0.0} for d, s in slas.items()}
    for c in db.query(Complaint).all():
        d = out.get(_dept(c))
        if not d:
            continue
        age = _days_open(c, now)
        if c.status == "Resolved" and c.resolved_at:
            d["resolved"] += 1
            d["total_days"] += age
            d["within_sla"] += age <= d["sla_days"]
        elif c.status not in CLOSED:
            d["open"] += 1
            d["open_breached"] += age > d["sla_days"]
    rows = []
    for d in out.values():
        d["compliance"] = round(d["within_sla"] / d["resolved"], 3) if d["resolved"] else None
        d["avg_days"] = round(d.pop("total_days") / d["resolved"], 2) if d["resolved"] else None
        rows.append(d)
    return sorted(rows, key=lambda r: (r["compliance"] is None, r["compliance"] or 0))


@router.get("/trends")
def trends(weeks: int = 12, user: User = Depends(staff), db: Session = Depends(get_db)):
    now = datetime.now()
    start = (now - timedelta(weeks=weeks)).date()
    start = start - timedelta(days=start.weekday())  # Monday
    labels = [(start + timedelta(weeks=i)) for i in range(weeks + 1)]
    series = defaultdict(lambda: [0] * len(labels))
    for c in db.query(Complaint).filter(Complaint.created_at >= datetime.combine(start, datetime.min.time())).all():
        i = (c.created_at.date() - start).days // 7
        if 0 <= i < len(labels):
            series[_cat(c)][i] += 1
    ordered = sorted(series.items(), key=lambda kv: -sum(kv[1]))
    return {"weeks": [d.isoformat() for d in labels],
            "series": [{"category": k, "counts": v, "total": sum(v)} for k, v in ordered]}
