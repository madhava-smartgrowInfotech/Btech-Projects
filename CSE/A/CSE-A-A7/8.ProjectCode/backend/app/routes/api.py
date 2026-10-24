import json
import time
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user, make_token, user_out, verify_password
from ..db import Override, Patient, User, get_db
from ..services import extract as extractor
from ..services import triage
from ..services.features import ARRIVAL_CODES, FLAGS, PRIORITY_NAMES
from ..services.pdf import build_summary

router = APIRouter(prefix="/api")
ROOT = Path(__file__).resolve().parents[3]
MAX_UPLOAD = 15 * 1024 * 1024


# ---------- schemas ----------
class LoginIn(BaseModel):
    email: str
    password: str


class VitalsIn(BaseModel):
    age: int = Field(ge=0, le=120)
    heart_rate: int = Field(ge=20, le=250)
    sbp: int = Field(ge=40, le=300)
    dbp: int = Field(ge=20, le=200)
    spo2: int = Field(ge=50, le=100)
    temp_c: float = Field(ge=30, le=44)
    resp_rate: int = Field(ge=4, le=70)
    arrival_mode: str = "walk-in"


class PatientIn(BaseModel):
    name: str = ""
    vitals: VitalsIn
    report: dict | None = None
    ocr_seconds: float = 0.0


class OverrideIn(BaseModel):
    priority: int = Field(ge=1, le=5)
    reason: str = ""


# ---------- serializers ----------
def patient_out(p: Patient, full: bool = True) -> dict:
    d = {
        "id": p.id, "name": p.name, "created_at": p.created_at.isoformat(), "source": p.source,
        "priority": p.priority, "priority_name": PRIORITY_NAMES[p.priority], "model_priority": p.model_priority,
        "risk_level": p.risk_level, "confidence": p.confidence, "vitals": p.vitals,
        "overridden": p.priority != p.model_priority or any(o.action == "change" for o in p.overrides),
        "reviewed": len(p.overrides) > 0, "total_seconds": p.total_seconds,
        "headline": [s["label"] for s in p.shap[:3]],
    }
    if full:
        d.update({
            "report": p.report, "fused": p.fused, "probabilities": p.probabilities, "shap": p.shap,
            "ocr_seconds": p.ocr_seconds, "model_seconds": p.model_seconds,
            "overrides": [{"id": o.id, "user_name": o.user_name, "old_priority": o.old_priority,
                           "new_priority": o.new_priority, "action": o.action, "reason": o.reason,
                           "created_at": o.created_at.isoformat()} for o in p.overrides],
        })
    return d


# ---------- routes ----------
@router.get("/health")
def health():
    return {"status": "ok", "model": (ROOT / "models" / "triage_model.joblib").exists()}


@router.get("/public/stats")
def public_stats():
    """Model headline numbers for the landing page (read-only, no patient data)."""
    path = ROOT / "experiments" / "metrics.json"
    if not path.exists():
        return {"available": False}
    m = json.loads(path.read_text())
    return {"available": True, "data": m["data"], "accuracy": m["accuracy"], "within_one_priority": m["within_one_priority"],
            "macro_f1": m["macro_f1"], "n_test": m["n_test"], "model_seconds_per_patient": m["model_seconds_per_patient"]}


SAMPLES = ROOT / "data" / "sample_reports"


@router.get("/samples")
def list_samples(user: User = Depends(current_user)):
    """Sample scanned reports (generated, labelled sample data) with the vitals that go with each."""
    path = SAMPLES / "expected.json"
    if not path.exists():
        return {"items": []}
    exp = json.loads(path.read_text())
    return {"items": [{"filename": f, "vitals": v["vitals"], "kind": "pdf" if f.endswith(".pdf") else "image"}
                      for f, v in exp.items()]}


@router.get("/samples/{filename}")
def get_sample(filename: str, user: User = Depends(current_user)):
    path = (SAMPLES / filename).resolve()
    if SAMPLES.resolve() not in path.parents or not path.is_file() or path.suffix not in (".pdf", ".png"):
        raise HTTPException(404, "Sample not found.")
    return Response(path.read_bytes(), media_type="application/pdf" if path.suffix == ".pdf" else "image/png")


@router.post("/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Email or password is wrong.")
    return {"access_token": make_token(user), "user": user_out(user)}


@router.get("/auth/me")
def me(user: User = Depends(current_user)):
    return user_out(user)


@router.post("/reports/extract")
async def extract_report(file: UploadFile = File(...), user: User = Depends(current_user)):
    data = await file.read()
    if not data:
        raise HTTPException(400, "The file is empty.")
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "File is larger than 15 MB. Upload a smaller scan.")
    try:
        return extractor.extract_report(data, file.filename or "")
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@router.post("/patients")
def create_patient(body: PatientIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if body.vitals.arrival_mode not in ARRIVAL_CODES:
        raise HTTPException(422, "Arrival mode must be walk-in, transfer or ambulance.")
    t0 = time.time()
    report = body.report or {}
    flags = {f: int(bool((report.get("flags") or {}).get(f))) for f in FLAGS}
    try:
        res = triage.predict(body.vitals.model_dump(), flags)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc))
    name = body.name.strip() or f"Patient {db.query(Patient).count() + 1:03d}"
    p = Patient(
        name=name, created_by=user.id, source="live", vitals=body.vitals.model_dump(), report=report or None,
        fused=res["fused"], model_priority=res["priority"], priority=res["priority"], risk_level=res["risk_level"],
        confidence=res["confidence"], probabilities=res["probabilities"], shap=res["shap"],
        ocr_seconds=body.ocr_seconds, model_seconds=res["seconds"],
        total_seconds=round(body.ocr_seconds + (time.time() - t0), 3),
    )
    db.add(p)
    db.commit()
    return patient_out(p)


@router.get("/patients")
def list_patients(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(select(Patient).order_by(Patient.priority, Patient.created_at)).all()
    return {"items": [patient_out(p, full=False) for p in rows]}


@router.get("/patients/{pid}")
def get_patient(pid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    p = db.get(Patient, pid)
    if not p:
        raise HTTPException(404, "Patient not found. They may have been removed.")
    return patient_out(p)


@router.get("/patients/{pid}/summary.pdf")
def summary_pdf(pid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    p = db.get(Patient, pid)
    if not p:
        raise HTTPException(404, "Patient not found.")
    return Response(build_summary(p), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="athena-triage-{p.id}.pdf"'})


@router.post("/patients/{pid}/override")
def override(pid: int, body: OverrideIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    p = db.get(Patient, pid)
    if not p:
        raise HTTPException(404, "Patient not found.")
    action = "accept" if body.priority == p.priority else "change"
    if action == "change" and not body.reason.strip():
        raise HTTPException(422, "Give a reason when changing the priority.")
    db.add(Override(patient_id=p.id, user_id=user.id, user_name=user.name, old_priority=p.priority,
                    new_priority=body.priority, action=action, reason=body.reason.strip()))
    p.priority = body.priority
    p.risk_level = "High" if body.priority <= 2 else "Moderate" if body.priority == 3 else "Low"
    db.commit()
    db.refresh(p)
    return patient_out(p)


@router.get("/metrics")
def metrics(db: Session = Depends(get_db), user: User = Depends(current_user)):
    path = ROOT / "experiments" / "metrics.json"
    offline = json.loads(path.read_text()) if path.exists() else None
    rows = db.scalars(select(Patient)).all()
    live = [p for p in rows if p.source == "live"]
    reviewed = [p for p in rows if p.overrides]
    changed = [p for p in reviewed if any(o.action == "change" for o in p.overrides)]
    dist = {str(i): sum(1 for p in rows if p.priority == i) for i in range(1, 6)}
    secs = [p.total_seconds for p in live if p.total_seconds]
    # accuracy vs recorded outcome on cases that carry one (sample queue cases)
    rec = [p for p in rows if p.recorded_outcome]
    return {
        "offline": offline,
        "live": {
            "patients": len(rows), "live_patients": len(live), "reviewed": len(reviewed),
            "overridden": len(changed),
            "agreement_rate": round(1 - len(changed) / len(reviewed), 4) if reviewed else None,
            "mean_seconds_per_patient": round(sum(secs) / len(secs), 3) if secs else None,
            "priority_distribution": dist,
            "recorded_outcome_cases": len(rec),
            "recorded_outcome_accuracy": round(sum(1 for p in rec if p.model_priority == p.recorded_outcome) / len(rec), 4) if rec else None,
        },
    }
