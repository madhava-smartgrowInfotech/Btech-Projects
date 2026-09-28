from datetime import date as Date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import can_manage_hospital, current_user
from ..db import Hospital, User, get_db
from ..services import triage
from ..services.queue import hub, today_str
from ..services.recommend import recommend
from ..services.scheduling import day_stats, hard_cap

router = APIRouter(prefix="/api", tags=["hospitals"])

ALL_SPECIALTIES = ["General Medicine", "Pulmonology", "Cardiology", "Neurology", "Gastroenterology", "Hepatology",
                   "Endocrinology", "Dermatology", "ENT", "Rheumatology", "Gynecology", "Pediatrics", "Allergy",
                   "Vascular Surgery"]


def hospital_dict(db: Session, h: Hospital, day: str | None = None) -> dict:
    s = day_stats(db, h.id, day or today_str())
    return {"id": h.id, "name": h.name, "lat": h.lat, "lon": h.lon, "address": h.address, "ownership": h.ownership,
            "specialties": h.specialty_list(), "has_emergency": h.has_emergency, "op_limit": h.op_limit,
            "emergency_quota": h.emergency_quota, "avg_consult_min": h.avg_consult_min, "op_start": h.op_start,
            "booked": s["booked"], "expected_attendance": round(s["expected"], 1), "quota_used": s["quota_used"],
            "hard_cap": hard_cap(h)}


@router.get("/hospitals")
def list_hospitals(db: Session = Depends(get_db)):
    return [hospital_dict(db, h) for h in db.scalars(select(Hospital).order_by(Hospital.name)).all()]


@router.get("/specialties")
def specialties():
    return ALL_SPECIALTIES


@router.get("/hospitals/{hid}")
def get_hospital(hid: int, db: Session = Depends(get_db)):
    h = db.get(Hospital, hid)
    if not h:
        raise HTTPException(404, "Hospital not found")
    return hospital_dict(db, h)


class HospitalPatch(BaseModel):
    op_limit: int | None = Field(default=None, ge=1, le=2000)
    emergency_quota: int | None = Field(default=None, ge=0, le=500)
    avg_consult_min: float | None = Field(default=None, ge=0.5, le=60)
    op_start: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    specialties: list[str] | None = None
    has_emergency: bool | None = None


@router.patch("/hospitals/{hid}")
async def update_hospital(hid: int, body: HospitalPatch, user: User = Depends(current_user),
                          db: Session = Depends(get_db)):
    h = db.get(Hospital, hid)
    if not h:
        raise HTTPException(404, "Hospital not found")
    if not can_manage_hospital(user, hid):
        raise HTTPException(403, "You can only configure your own hospital")
    data = body.model_dump(exclude_none=True)
    if "specialties" in data:
        bad = [s for s in data["specialties"] if s not in ALL_SPECIALTIES]
        if bad:
            raise HTTPException(422, f"Unknown specialties: {bad}")
        data["specialties"] = ",".join(s for s in ALL_SPECIALTIES if s in data["specialties"])
    for k, v in data.items():
        setattr(h, k, v)
    db.commit()
    await hub.notify(hid)
    return hospital_dict(db, h)


# --- triage and recommendation -------------------------------------------------------------

@router.get("/symptoms")
def symptoms():
    return triage.symptom_vocab()


class TextIn(BaseModel):
    text: str = Field(min_length=2, max_length=1000)


@router.post("/triage/map-text")
def map_text(body: TextIn):
    return triage.map_text(body.text)


class TriageIn(BaseModel):
    symptoms: list[str]


@router.post("/triage")
def classify(body: TriageIn):
    try:
        return triage.classify(body.symptoms)
    except ValueError as e:
        raise HTTPException(422, str(e))


class RecommendIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    severity: str = Field(pattern="^(mild|moderate|severe|critical)$")
    specialty: str = "General Medicine"
    date: Date | None = None
    limit: int = Field(default=5, ge=1, le=20)
    exclude: list[int] = []


@router.post("/recommend")
def recommend_hospitals(body: RecommendIn, db: Session = Depends(get_db)):
    day = body.date or Date.today()
    recs = recommend(db, body.lat, body.lon, body.severity, body.specialty, day, body.limit + len(body.exclude))
    return [r for r in recs if r["id"] not in body.exclude][:body.limit]
