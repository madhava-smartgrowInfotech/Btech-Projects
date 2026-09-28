"""Inter-hospital referrals with patient consent before the clinical summary is shared."""
import json
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..auth import can_manage_hospital, current_user
from ..db import Booking, Hospital, Referral, User, get_db
from ..services import triage
from ..services.queue import hub
from ..services.recommend import recommend
from .bookings import booking_dict, create_booking

router = APIRouter(prefix="/api/referrals", tags=["referrals"])


def referral_dict(db: Session, r: Referral, viewer: User) -> dict:
    frm, to = db.get(Hospital, r.from_hospital_id), db.get(Hospital, r.to_hospital_id)
    # the receiving hospital only sees the clinical summary once the patient has consented
    receiving_only = viewer.role == "staff" and viewer.hospital_id == r.to_hospital_id \
        and viewer.hospital_id != r.from_hospital_id
    share = r.consent or not receiving_only
    new_b = db.get(Booking, r.new_booking_id) if r.new_booking_id else None
    return {"id": r.id, "booking_id": r.booking_id, "patient_name": r.patient_name if share else "(awaiting consent)",
            "from_hospital": {"id": frm.id, "name": frm.name}, "to_hospital": {"id": to.id, "name": to.name},
            "specialty": r.specialty, "reason": r.reason, "summary": json.loads(r.summary) if share else None,
            "consent": r.consent, "consent_at": r.consent_at.isoformat(timespec="minutes") if r.consent_at else None,
            "status": r.status, "new_booking": booking_dict(db, new_b) if new_b else None,
            "created_at": r.created_at.isoformat(timespec="minutes"),
            "updated_at": r.updated_at.isoformat(timespec="minutes")}


def load(db: Session, rid: int) -> Referral:
    r = db.get(Referral, rid)
    if not r:
        raise HTTPException(404, "Referral not found")
    return r


@router.get("/targets")
def targets(booking_id: int, specialty: str | None = None, user: User = Depends(current_user),
            db: Session = Depends(get_db)):
    b = db.get(Booking, booking_id)
    if not b or not can_manage_hospital(user, b.hospital_id):
        raise HTTPException(404, "Booking not found")
    h = db.get(Hospital, b.hospital_id)
    spec = specialty or b.specialty or "General Medicine"
    sev = "severe" if b.severity == "critical" else b.severity
    recs = recommend(db, h.lat, h.lon, sev, spec, date.today(), limit=8)
    return {"specialty": spec, "hospitals": [r for r in recs if r["id"] != h.id][:6]}


class ReferralIn(BaseModel):
    booking_id: int
    to_hospital_id: int
    specialty: str | None = None
    reason: str = Field(min_length=3, max_length=500)
    notes: str = Field(default="", max_length=2000)
    consent_confirmed: bool = False  # for walk-in patients without an app account: consent taken in person


@router.post("")
async def create(body: ReferralIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    b = db.get(Booking, body.booking_id)
    if not b:
        raise HTTPException(404, "Booking not found")
    if user.role not in ("staff", "admin") or not can_manage_hospital(user, b.hospital_id):
        raise HTTPException(403, "Only the treating hospital can refer this patient")
    if b.hospital_id == body.to_hospital_id or not db.get(Hospital, body.to_hospital_id):
        raise HTTPException(422, "Choose a different receiving hospital")
    if b.patient_id is None and not body.consent_confirmed:
        raise HTTPException(422, "Confirm that the patient consented to sharing their summary")
    frm = db.get(Hospital, b.hospital_id)
    summary = {
        "patient": b.patient_name, "age": b.age, "gender": b.gender, "visit_date": b.date,
        "referring_hospital": frm.name, "symptoms": [triage.label(s) for s in json.loads(b.symptoms)],
        "ai_severity": b.severity, "ai_possible_condition": b.condition, "clinician_notes": body.notes,
        "disclaimer": "AI fields are decision support for the receiving clinician, not a diagnosis.",
    }
    consented = b.patient_id is None and body.consent_confirmed
    r = Referral(booking_id=b.id, patient_id=b.patient_id, patient_name=b.patient_name, from_hospital_id=frm.id,
                 to_hospital_id=body.to_hospital_id, specialty=body.specialty or b.specialty or "General Medicine",
                 reason=body.reason, summary=json.dumps(summary), consent=consented,
                 consent_at=datetime.now() if consented else None,
                 status="sent" if consented else "pending_consent", created_by=user.id)
    db.add(r)
    db.flush()
    b.referral_id = r.id
    if b.status in ("waiting", "called"):
        b.status, b.completed_at = "referred", datetime.now()
    db.commit()
    await hub.notify(frm.id)
    return referral_dict(db, r, user)


@router.get("")
def list_referrals(user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = select(Referral).order_by(Referral.id.desc()).limit(200)
    if user.role == "patient":
        q = q.where(Referral.patient_id == user.id)
    elif user.role == "staff":
        q = q.where(or_(Referral.from_hospital_id == user.hospital_id, Referral.to_hospital_id == user.hospital_id))
    return [referral_dict(db, r, user) for r in db.scalars(q).all()]


class ConsentIn(BaseModel):
    consent: bool


@router.post("/{rid}/consent")
def consent(rid: int, body: ConsentIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    r = load(db, rid)
    if r.patient_id != user.id:
        raise HTTPException(403, "Only the patient can give consent")
    if r.status != "pending_consent":
        raise HTTPException(409, f"Referral is already {r.status}")
    r.consent = body.consent
    r.consent_at = datetime.now()
    r.status = "sent" if body.consent else "declined"
    r.updated_at = datetime.now()
    db.commit()
    return referral_dict(db, r, user)


def receiving(db: Session, user: User, r: Referral):
    if not can_manage_hospital(user, r.to_hospital_id):
        raise HTTPException(403, "Only the receiving hospital can do this")


@router.post("/{rid}/accept")
async def accept(rid: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    r = load(db, rid)
    receiving(db, user, r)
    if r.status != "sent":
        raise HTTPException(409, "Referral must be consented and sent before it can be accepted")
    src = db.get(Booking, r.booking_id)
    to = db.get(Hospital, r.to_hospital_id)
    b, info = create_booking(db, to, date.today(), json.loads(src.symptoms) or ["fatigue"], r.patient_name,
                             src.age, src.gender, r.patient_id, referral_id=r.id,
                             notes=f"Referred from {db.get(Hospital, r.from_hospital_id).name}: {r.reason}")
    r.status, r.new_booking_id, r.updated_at = "accepted", b.id, datetime.now()
    db.commit()
    await hub.notify(to.id)
    return {**referral_dict(db, r, user), "allocation": info["reason"]}


@router.post("/{rid}/complete")
def complete(rid: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    r = load(db, rid)
    receiving(db, user, r)
    if r.status != "accepted":
        raise HTTPException(409, "Only accepted referrals can be completed")
    r.status, r.updated_at = "completed", datetime.now()
    db.commit()
    return referral_dict(db, r, user)


@router.post("/{rid}/decline")
def decline(rid: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    r = load(db, rid)
    receiving(db, user, r)
    if r.status not in ("sent", "pending_consent"):
        raise HTTPException(409, f"Referral is already {r.status}")
    r.status, r.updated_at = "declined", datetime.now()
    db.commit()
    return referral_dict(db, r, user)
