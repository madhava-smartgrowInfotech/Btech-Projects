from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import current_user, decrypt_text, encrypt_text
from ..db import Patient, SessionLocal, User, audit, iso

router = APIRouter(prefix="/api/patients", tags=["patients"])


class PatientIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(default="", max_length=20)
    age: int = Field(ge=0, le=120)
    sex: Literal["Male", "Female", "Other"]


def scan_brief(s):
    return {"id": s.id, "modality": s.modality, "prediction": s.prediction, "confidence": s.confidence,
            "severity": s.severity, "created_at": iso(s.created_at)}


def patient_out(p: Patient, with_scans=False):
    out = {"id": p.id, "code": p.code, "name": decrypt_text(p.name_enc), "phone": decrypt_text(p.phone_enc),
           "age": p.age, "sex": p.sex, "created_at": iso(p.created_at), "scan_count": len(p.scans)}
    if p.scans:
        out["last_scan"] = scan_brief(p.scans[0])
    if with_scans:
        out["scans"] = [scan_brief(s) for s in p.scans]
    return out


@router.get("")
def list_patients(q: str = "", user: User = Depends(current_user)):
    with SessionLocal() as db:
        items = [patient_out(p) for p in db.query(Patient).order_by(Patient.id.desc()).all()]
    if q:  # names are encrypted, so search after decryption
        ql = q.lower()
        items = [p for p in items if ql in p["name"].lower() or ql in p["code"].lower()]
    return items


@router.post("")
def create_patient(body: PatientIn, user: User = Depends(current_user)):
    with SessionLocal() as db:
        p = Patient(code="", name_enc=encrypt_text(body.name.strip()), phone_enc=encrypt_text(body.phone.strip()),
                    age=body.age, sex=body.sex, created_by=user.id)
        db.add(p)
        db.flush()
        p.code = f"PV-{p.id:05d}"
        db.commit()
        audit(db, user, "patient_create", p.code)
        db.refresh(p)
        return patient_out(p)


@router.get("/{pid}")
def get_patient(pid: int, user: User = Depends(current_user)):
    with SessionLocal() as db:
        p = db.get(Patient, pid)
        if not p:
            raise HTTPException(404, "Patient not found")
        audit(db, user, "patient_view", p.code)
        return patient_out(p, with_scans=True)
