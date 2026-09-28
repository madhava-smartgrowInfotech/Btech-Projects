import json
from datetime import date, timedelta
from datetime import date as Date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import can_manage_hospital, current_user
from ..db import Booking, Hospital, User, get_db
from ..services import noshow, triage
from ..services.queue import booking_status, hub
from ..services.scheduling import allocate, next_token

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


def booking_dict(db: Session, b: Booking) -> dict:
    return {**booking_status(db, b), "id": b.id, "patient_name": b.patient_name, "age": b.age, "gender": b.gender,
            "kind": b.kind, "requested_date": b.requested_date, "moved": b.date != b.requested_date,
            "symptoms": [triage.label(s) for s in json.loads(b.symptoms)], "condition": b.condition,
            "specialty": b.specialty, "noshow_prob": b.noshow_prob, "uses_quota": b.uses_quota,
            "is_sample": b.is_sample, "referral_id": b.referral_id, "notes": b.notes,
            "created_at": b.created_at.isoformat(timespec="minutes")}


def create_booking(db: Session, h: Hospital, requested: date, symptoms: list[str], name: str,
                   age: int | None, gender: str | None, patient_id: int | None, referral_id: int | None = None,
                   notes: str = "") -> tuple[Booking, dict]:
    try:
        t = triage.classify(symptoms)
    except ValueError as e:
        raise HTTPException(422, str(e))
    today = date.today()
    p = noshow.predict(age, gender, requested, today)
    alloc = allocate(db, h, requested, p, t["severity"], today)
    if alloc["date"] is None:
        raise HTTPException(409, f"{h.name} is {alloc['reason']}. Please choose another hospital.")
    if alloc["date"] != requested:
        p = noshow.predict(age, gender, alloc["date"], today)
    day = alloc["date"].isoformat()
    b = Booking(hospital_id=h.id, patient_id=patient_id, patient_name=name, age=age, gender=gender, date=day,
                requested_date=requested.isoformat(), token=next_token(db, h.id, day), kind="op",
                uses_quota=alloc["uses_quota"], severity=t["severity"], priority=triage.PRIORITY[t["severity"]],
                symptoms=json.dumps([s["key"] for s in t["symptoms"]]), condition=t["condition"],
                specialty=t["specialty"], noshow_prob=p, referral_id=referral_id, notes=notes)
    db.add(b)
    db.commit()
    return b, {"reason": alloc["reason"], "triage": t}


class BookingIn(BaseModel):
    hospital_id: int
    date: Date
    symptoms: list[str] = Field(min_length=1)
    patient_name: str | None = None
    age: int | None = Field(default=None, ge=0, le=120)
    gender: str | None = Field(default=None, pattern="^[MF]$")


@router.post("")
async def book(body: BookingIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "patient":
        raise HTTPException(403, "Only patients book visits here; hospital staff add patients from the console")
    today = date.today()
    if body.date < today or body.date > today + timedelta(days=30):
        raise HTTPException(422, "Choose a date between today and 30 days from now")
    h = db.get(Hospital, body.hospital_id)
    if not h:
        raise HTTPException(404, "Hospital not found")
    b, info = create_booking(db, h, body.date, body.symptoms, (body.patient_name or user.name).strip(),
                             body.age if body.age is not None else user.age, body.gender or user.gender, user.id)
    await hub.notify(h.id)
    return {**booking_dict(db, b), "allocation": info["reason"], "advice": info["triage"]["advice"],
            "disclaimer": info["triage"]["disclaimer"]}


@router.get("/mine")
def my_bookings(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Booking).where(Booking.patient_id == user.id)
                      .order_by(Booking.date.desc(), Booking.id.desc()).limit(50)).all()
    return [booking_dict(db, b) for b in rows]


@router.get("/{bid}")
def get_booking(bid: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    b = db.get(Booking, bid)
    if not b:
        raise HTTPException(404, "Booking not found")
    if b.patient_id != user.id and not can_manage_hospital(user, b.hospital_id):
        raise HTTPException(403, "Not your booking")
    return booking_dict(db, b)
