from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from ..auth import current_user
from ..db import Alert, SessionLocal
from ..services.monitor import monitor

router = APIRouter(prefix="/api/monitor", tags=["monitor"], dependencies=[Depends(current_user)])


class StartIn(BaseModel):
    source: str | None = None


class RecordIn(BaseModel):
    label: str
    seconds: float = 5


def pending_alert():
    with SessionLocal() as db:
        a = db.query(Alert).filter(Alert.status == "pending", Alert.kind == "fall") \
            .order_by(Alert.id.desc()).first()
        if not a:
            return None
        left = max(0.0, (a.deadline - datetime.now()).total_seconds())
        return {"id": a.id, "detected_at": a.detected_at.isoformat(), "seconds_left": round(left, 1)}


@router.post("/start")
def start(body: StartIn):
    try:
        monitor.start(body.source)
    except Exception as e:
        raise HTTPException(400, str(e))
    return monitor.get_state()


@router.post("/stop")
def stop():
    monitor.stop()
    return monitor.get_state()


@router.get("/state")
def state():
    return {**monitor.get_state(), "alert": pending_alert()}


@router.get("/frame.jpg")
def frame():
    if monitor.jpeg is None:
        raise HTTPException(404, "Privacy mode is on - video is not shown")
    return Response(monitor.jpeg, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


@router.post("/record")
def record(body: RecordIn):
    try:
        monitor.record(body.label, min(max(body.seconds, 2), 30))
    except (ValueError, RuntimeError) as e:
        raise HTTPException(400, str(e))
    return {"recording": body.label}
