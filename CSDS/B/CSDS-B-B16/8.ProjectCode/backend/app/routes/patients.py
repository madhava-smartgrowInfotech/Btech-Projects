from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import Patient, User, get_db
from .screenings import screening_summary

router = APIRouter(prefix="/api/patients", tags=["patients"])


class PatientIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    age: int = Field(ge=1, le=120)
    sex: str = Field(pattern="^(Male|Female|Other)$")
    code: str | None = None


def patient_dict(p: Patient, with_screenings: bool = False) -> dict:
    d = {"id": p.id, "code": p.code, "name": p.name, "age": p.age, "sex": p.sex,
         "created_at": p.created_at.isoformat() + "Z", "screening_count": len(p.screenings)}
    latest = p.screenings[0] if p.screenings else None
    d["latest_stage"] = latest.stage["stage"] if latest and latest.stage else None
    d["last_screened"] = latest.created_at.isoformat() + "Z" if latest else None
    if with_screenings:
        d["screenings"] = [screening_summary(s) for s in p.screenings]
    return d


@router.get("")
def list_patients(q: str = "", db: Session = Depends(get_db), _: User = Depends(current_user)):
    query = db.query(Patient)
    if q:
        like = f"%{q}%"
        query = query.filter(Patient.name.ilike(like) | Patient.code.ilike(like))
    return [patient_dict(p) for p in query.order_by(Patient.id.desc()).all()]


@router.post("")
def create_patient(body: PatientIn, db: Session = Depends(get_db), _: User = Depends(current_user)):
    code = (body.code or "").strip() or f"RG-{datetime.utcnow():%y%m%d}-{db.query(Patient).count() + 1:04d}"
    if db.query(Patient).filter_by(code=code).first():
        raise HTTPException(409, f"Patient code {code} already exists")
    p = Patient(code=code, name=body.name.strip(), age=body.age, sex=body.sex)
    db.add(p)
    db.commit()
    db.refresh(p)
    return patient_dict(p)


@router.get("/{pid}")
def get_patient(pid: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    p = db.get(Patient, pid)
    if not p:
        raise HTTPException(404, "Patient not found")
    return patient_dict(p, with_screenings=True)
