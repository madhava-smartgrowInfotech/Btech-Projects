import json
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import current_user
from ..config import EXPERIMENTS_DIR
from ..db import ActivitySegment, Alert, InactivityWarning, get_db
from ..services.settings import get_settings

router = APIRouter(prefix="/api", tags=["reports"], dependencies=[Depends(current_user)])


@router.get("/reports/daily")
def daily(day: str | None = None, db: Session = Depends(get_db)):
    try:
        d = date.fromisoformat(day) if day else date.today()
    except ValueError:
        raise HTTPException(400, "day must be YYYY-MM-DD")
    start = datetime.combine(d, datetime.min.time())
    end = start + timedelta(days=1)
    segs = db.query(ActivitySegment).filter(ActivitySegment.start < end, ActivitySegment.end > start) \
        .order_by(ActivitySegment.start).all()
    totals, timeline = {}, []
    for s in segs:
        a, b = max(s.start, start), min(s.end, end)
        sec = (b - a).total_seconds()
        if sec <= 0:
            continue
        totals[s.activity] = totals.get(s.activity, 0) + sec
        timeline.append({"activity": s.activity, "start": a.isoformat(), "end": b.isoformat(), "seconds": round(sec, 1)})
    warnings = db.query(InactivityWarning).filter(InactivityWarning.started_at >= start,
                                                  InactivityWarning.started_at < end).all()
    alerts = db.query(Alert).filter(Alert.detected_at >= start, Alert.detected_at < end, Alert.kind == "fall").all()
    present = sum(v for k, v in totals.items() if k != "away")
    active = sum(totals.get(k, 0) for k in ("walking", "picking_up", "drinking"))
    return {
        "day": d.isoformat(),
        "totals": {k: round(v, 1) for k, v in sorted(totals.items(), key=lambda x: -x[1])},
        "monitored_seconds": round(sum(totals.values()), 1),
        "present_seconds": round(present, 1),
        "active_seconds": round(active, 1),
        "timeline": timeline,
        "inactivity_threshold_minutes": get_settings()["inactivity_minutes"],
        "warnings": [{"id": w.id, "activity": w.activity, "started_at": w.started_at.isoformat(),
                      "ended_at": w.ended_at.isoformat() if w.ended_at else None, "minutes": w.minutes}
                     for w in warnings],
        "falls": [{"id": a.id, "status": a.status, "detected_at": a.detected_at.isoformat()} for a in alerts],
    }


@router.get("/reports/days")
def days_with_data(db: Session = Depends(get_db)):
    rows = db.query(ActivitySegment.start).all()
    return sorted({r[0].date().isoformat() for r in rows}, reverse=True)[:60]


def read_json(p):
    return json.loads(p.read_text()) if p.exists() else None


@router.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    sent = db.query(Alert).filter(Alert.kind == "fall", Alert.sent_at.isnot(None)).all()
    det = [a.detection_latency_ms for a in sent if a.detection_latency_ms is not None]
    disp = [a.dispatch_ms for a in sent if a.dispatch_ms is not None]
    live = {
        "fall_alerts": db.query(Alert).filter(Alert.kind == "fall").count(),
        "sent": len(sent),
        "cancelled_im_ok": db.query(Alert).filter(Alert.kind == "fall", Alert.status == "cancelled").count(),
        "mean_detection_latency_ms": round(sum(det) / len(det), 1) if det else None,
        "mean_dispatch_ms": round(sum(disp) / len(disp), 1) if disp else None,
    }
    return {"training": read_json(EXPERIMENTS_DIR / "metrics.json"),
            "evaluation": read_json(EXPERIMENTS_DIR / "eval" / "metrics.json"),
            "live": live}
