import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import can_manage_hospital, require_role
from ..db import Booking, Hospital, User, get_db
from ..services import triage
from ..services.queue import consult_minutes, current_called, hub, ordered_waiting, today_str
from ..services.scheduling import day_stats, next_token
from .bookings import booking_dict

router = APIRouter(prefix="/api/console", tags=["console"])
staff_or_admin = require_role("staff", "admin")


def get_managed(db: Session, user: User, hid: int) -> Hospital:
    h = db.get(Hospital, hid)
    if not h:
        raise HTTPException(404, "Hospital not found")
    if not can_manage_hospital(user, hid):
        raise HTTPException(403, "You can only manage your own hospital")
    return h


def queue_view(db: Session, h: Hospital, day: str) -> dict:
    waiting = ordered_waiting(db, h.id, day)
    finished = db.scalars(select(Booking).where(Booking.hospital_id == h.id, Booking.date == day,
                                                Booking.status.in_(("done", "no_show", "referred")))
                          .order_by(Booking.completed_at.desc().nullslast(), Booking.id.desc()).limit(30)).all()
    s = day_stats(db, h.id, day)
    mix = {}
    for b in db.scalars(select(Booking).where(Booking.hospital_id == h.id, Booking.date == day)).all():
        mix[b.severity] = mix.get(b.severity, 0) + 1
    return {
        "hospital": {"id": h.id, "name": h.name, "op_limit": h.op_limit, "emergency_quota": h.emergency_quota,
                     "avg_consult_min": h.avg_consult_min, "op_start": h.op_start, "specialties": h.specialty_list(),
                     "has_emergency": h.has_emergency},
        "date": day, "booked": s["booked"], "expected_attendance": round(s["expected"], 1),
        "quota_used": s["quota_used"], "consult_min": consult_minutes(db, h, day), "severity_mix": mix,
        "called": [booking_dict(db, b) for b in current_called(db, h.id, day)],
        "waiting": [booking_dict(db, b) for b in waiting],
        "finished": [booking_dict(db, b) for b in finished],
    }


@router.get("/{hid}")
def get_queue(hid: int, date: str | None = None, user: User = Depends(staff_or_admin), db: Session = Depends(get_db)):
    h = get_managed(db, user, hid)
    return queue_view(db, h, date or today_str())


@router.post("/{hid}/call-next")
async def call_next(hid: int, user: User = Depends(staff_or_admin), db: Session = Depends(get_db)):
    h = get_managed(db, user, hid)
    day = today_str()
    now = datetime.now()
    for b in current_called(db, hid, day):
        b.status, b.completed_at = "done", now
    waiting = ordered_waiting(db, hid, day)
    called = None
    if waiting:
        called = waiting[0]
        called.status, called.called_at = "called", now
    db.commit()
    await hub.notify(hid)
    return {"called": booking_dict(db, called) if called else None, "queue": queue_view(db, h, day)}


class StatusIn(BaseModel):
    status: str = Field(pattern="^(done|no_show)$")


@router.post("/bookings/{bid}/status")
async def set_status(bid: int, body: StatusIn, user: User = Depends(staff_or_admin), db: Session = Depends(get_db)):
    b = db.get(Booking, bid)
    if not b:
        raise HTTPException(404, "Booking not found")
    get_managed(db, user, b.hospital_id)
    if b.status not in ("waiting", "called"):
        raise HTTPException(409, f"Booking is already {b.status}")
    b.status, b.completed_at = body.status, datetime.now()
    db.commit()
    await hub.notify(b.hospital_id)
    return booking_dict(db, b)


class EmergencyIn(BaseModel):
    patient_name: str = Field(min_length=1, max_length=120)
    age: int | None = Field(default=None, ge=0, le=120)
    gender: str | None = Field(default=None, pattern="^[MF]$")
    symptoms: list[str] = []
    notes: str = ""


@router.post("/{hid}/emergency")
async def add_emergency(hid: int, body: EmergencyIn, user: User = Depends(staff_or_admin),
                        db: Session = Depends(get_db)):
    h = get_managed(db, user, hid)
    day = today_str()
    try:
        t = triage.classify(body.symptoms) if body.symptoms else None
    except ValueError as e:
        raise HTTPException(422, str(e))
    quota_used = day_stats(db, hid, day)["quota_used"]
    b = Booking(hospital_id=hid, patient_name=body.patient_name, age=body.age, gender=body.gender, date=day,
                requested_date=day, token=next_token(db, hid, day), kind="emergency", uses_quota=True,
                severity=t["severity"] if t else "critical", priority=-1,
                symptoms=json.dumps([s["key"] for s in t["symptoms"]] if t else []),
                condition=t["condition"] if t else "", specialty=t["specialty"] if t else "Emergency",
                noshow_prob=0.0, notes=body.notes)
    db.add(b)
    db.commit()
    await hub.notify(hid)
    over = quota_used + 1 > h.emergency_quota
    return {**booking_dict(db, b),
            "quota_note": f"emergency {quota_used + 1}/{h.emergency_quota}" + (" - quota exceeded, still admitted" if over else "")}
