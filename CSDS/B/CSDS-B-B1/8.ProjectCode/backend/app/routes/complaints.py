"""Citizen intake (F1) + the AI pipeline run on every new complaint (F2-F5)."""
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..auth import current_user, require
from ..config import UPLOAD_DIR
from ..db import Complaint, Department, Event, SessionLocal, User, get_db
from ..services import gemini
from ..services.predictor import get_predictor
from ..services.seed import nearest_ward
from ..services.textutil import detect_language

router = APIRouter(prefix="/api", tags=["complaints"])
IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_PHOTO = 8 * 1024 * 1024
CLOSED = ("Resolved", "Rejected")


def sla_map(db):
    return {d.name: d.sla_days for d in db.query(Department).all()}


def run_extraction(complaint_id: int):
    """Gemini structured extraction, run after the citizen already has a tracking ID."""
    db = SessionLocal()
    try:
        c = db.get(Complaint, complaint_id)
        try:
            c.extraction, c.extraction_status = gemini.extract_details(c.text), "done"
        except Exception as e:  # keep the complaint flowing even if the API is down
            c.extraction, c.extraction_status = {"error": str(e)[:300]}, "failed"
        db.commit()
    finally:
        db.close()


def current_view(c: Complaint, slas: dict) -> dict:
    """What the office currently believes: officer decision if made, else the AI suggestion."""
    ai = c.ai or {}
    dept = c.final_department or ai.get("department")
    days = c.final_days if c.final_days is not None else ai.get("expected_days")
    sla = slas.get(dept)
    age = ((c.resolved_at or datetime.now()) - c.created_at).total_seconds() / 86400
    return {
        "category": c.final_category or ai.get("category"),
        "department": dept,
        "priority": c.final_priority or ai.get("priority"),
        "expected_days": days,
        "expected_by": (c.created_at + timedelta(days=days)).isoformat() if days is not None else None,
        "sla_days": sla,
        "sla_due": (c.created_at + timedelta(days=sla)).isoformat() if sla else None,
        "sla_breach_risk": bool(days is not None and sla and days > sla),
        "sla_breached": bool(sla and age > sla),
        "age_days": round(age, 1),
        "decided": c.final_department is not None,
    }


def citizen_view(c: Complaint, slas: dict) -> dict:
    cur = current_view(c, slas)
    return {
        "id": c.id, "tracking_id": c.tracking_id, "text": c.text, "language": c.language,
        "photo_url": f"/api/photos/{c.photo}" if c.photo else None, "lat": c.lat, "lng": c.lng,
        "ward": c.ward.name if c.ward else None, "status": c.status,
        "created_at": c.created_at.isoformat(), "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
        # the citizen sees department / timeline only after an officer confirms them
        "department": cur["department"] if cur["decided"] else None,
        "expected_days": cur["expected_days"] if cur["decided"] else None,
        "expected_by": cur["expected_by"] if cur["decided"] else None,
        "timeline": [{"kind": e.kind, "status": e.status, "message": e.message, "at": e.created_at.isoformat()}
                     for e in c.events if e.public],
        "is_sample": c.is_sample,
    }


@router.post("/complaints")
def create_complaint(bg: BackgroundTasks, text: str = Form(...), lat: float | None = Form(None),
                     lng: float | None = Form(None), photo: UploadFile | None = File(None),
                     user: User = Depends(require("citizen")), db: Session = Depends(get_db)):
    text = text.strip()
    if len(text) < 15:
        raise HTTPException(400, "Please describe the problem in at least a few words (15+ characters).")
    if len(text) > 4000:
        raise HTTPException(400, "Please keep the description under 4000 characters.")
    fname = None
    if photo is not None and photo.filename:
        if photo.content_type not in IMAGE_TYPES:
            raise HTTPException(400, "Photo must be a JPG, PNG or WebP image.")
        data = photo.file.read(MAX_PHOTO + 1)
        if len(data) > MAX_PHOTO:
            raise HTTPException(400, "Photo must be smaller than 8 MB.")
        fname = uuid.uuid4().hex + IMAGE_TYPES[photo.content_type]
        (UPLOAD_DIR / fname).write_bytes(data)

    now = datetime.now().replace(microsecond=0)
    ai = get_predictor().predict(text, now)
    slas = sla_map(db)
    ai["sla_days"] = slas[ai["department"]]
    ai["sla_breach_risk"] = ai["expected_days"] > ai["sla_days"]
    ward = nearest_ward(db, lat, lng)
    c = Complaint(tracking_id=uuid.uuid4().hex[:12], citizen_id=user.id, text=text, language=detect_language(text),
                  photo=fname, lat=lat, lng=lng, ward_id=ward.id if ward else None, created_at=now, ai=ai,
                  extraction_status="pending")
    c.events.append(Event(kind="status", status="Submitted", created_at=now,
                          message="Complaint received. An officer will review it shortly."))
    db.add(c)
    db.flush()
    c.tracking_id = f"CP-{now:%y%m}-{c.id:05d}"
    db.commit()
    bg.add_task(run_extraction, c.id)
    return citizen_view(c, slas)


@router.get("/complaints/mine")
def my_complaints(user: User = Depends(current_user), db: Session = Depends(get_db)):
    slas = sla_map(db)
    rows = db.query(Complaint).filter_by(citizen_id=user.id).order_by(Complaint.created_at.desc()).all()
    return [citizen_view(c, slas) for c in rows]


@router.get("/complaints/track/{tracking_id}")
def track(tracking_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    c = db.query(Complaint).filter_by(tracking_id=tracking_id.strip().upper()).first()
    if not c or (user.role == "citizen" and c.citizen_id != user.id):
        raise HTTPException(404, "No complaint with that tracking ID on your account.")
    return citizen_view(c, sla_map(db))


@router.get("/photos/{name}")
def photo(name: str):
    path = UPLOAD_DIR / name
    if "/" in name or "\\" in name or not path.is_file():
        raise HTTPException(404, "Photo not found")
    return FileResponse(path)
