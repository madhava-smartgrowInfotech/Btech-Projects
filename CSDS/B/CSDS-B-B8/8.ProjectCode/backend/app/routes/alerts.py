from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..auth import current_user
from ..config import SNAPSHOT_DIR
from ..db import Alert, User, get_db
from ..services.alerts import dispatch

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def alert_out(a):
    left = max(0.0, (a.deadline - datetime.now()).total_seconds()) if a.status == "pending" and a.deadline else 0
    total = (a.sent_at - a.detected_at).total_seconds() * 1000 if a.sent_at else None
    return {
        "id": a.id, "kind": a.kind, "status": a.status, "detected_at": a.detected_at.isoformat(),
        "impact_at": a.impact_at.isoformat() if a.impact_at else None,
        "deadline": a.deadline.isoformat() if a.deadline else None, "seconds_left": round(left, 1),
        "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None, "resolved_by": a.resolved_by,
        "sent_at": a.sent_at.isoformat() if a.sent_at else None,
        "detection_latency_ms": a.detection_latency_ms, "dispatch_ms": a.dispatch_ms,
        "detected_to_sent_ms": round(total, 1) if total is not None else None,
        "has_snapshot": bool(a.snapshot), "channels": a.channels or {}, "details": a.details or {},
    }


@router.get("")
def list_alerts(limit: int = 100, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return [alert_out(a) for a in db.query(Alert).order_by(Alert.id.desc()).limit(limit)]


@router.post("/{alert_id}/ok")
def im_ok(alert_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    a = db.get(Alert, alert_id)
    if not a:
        raise HTTPException(404, "Alert not found")
    if a.status != "pending":
        raise HTTPException(400, f"Alert is already {a.status}")
    a.status = "cancelled"
    a.resolved_at = datetime.now()
    a.resolved_by = user.name
    db.commit()
    return alert_out(a)


@router.post("/test")
def test_alert(db: Session = Depends(get_db), user: User = Depends(current_user)):
    a = Alert(kind="test", status="sending", detected_at=datetime.now(), deadline=datetime.now())
    db.add(a)
    db.commit()
    dispatch(a.id)
    db.refresh(a)
    return alert_out(a)


@router.get("/{alert_id}/snapshot")
def snapshot(alert_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    a = db.get(Alert, alert_id)
    if not a or not a.snapshot or not (SNAPSHOT_DIR / a.snapshot).exists():
        raise HTTPException(404, "No snapshot for this alert")
    return FileResponse(SNAPSHOT_DIR / a.snapshot, media_type="image/jpeg")
