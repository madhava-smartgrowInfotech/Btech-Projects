"""Officer workbench (F6) - review AI suggestions, accept / override, update status, reply (F8)."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import staff
from ..db import Complaint, Event, Feedback, User, get_db
from ..services import gemini
from ..services.predictor import get_predictor
from ..services.taxonomy import CATEGORIES, DEPARTMENTS, PRIORITIES
from .complaints import CLOSED, current_view, run_extraction, sla_map

router = APIRouter(prefix="/api", tags=["officer"])
STATUSES = ["Submitted", "Assigned", "In Progress", "Resolved", "Rejected"]
PRIORITY_RANK = {p: i for i, p in enumerate(PRIORITIES)}


def queue_item(c: Complaint, slas):
    ai = c.ai or {}
    words = (ai.get("explanations") or {}).get("category_words") or []
    return {
        "id": c.id, "tracking_id": c.tracking_id, "text": c.text[:260], "language": c.language,
        "ward": c.ward.name if c.ward else None, "status": c.status, "created_at": c.created_at.isoformat(),
        "has_photo": bool(c.photo), "is_sample": c.is_sample, "extraction_status": c.extraction_status,
        "ai": {k: ai.get(k) for k in ("category", "category_confidence", "department", "department_confidence",
                                      "priority", "priority_confidence", "expected_days", "sla_breach_risk")},
        "top_words": [w["word"] for w in words if w["weight"] > 0][:4],
        "current": current_view(c, slas),
    }


@router.get("/officer/queue")
def queue(status: str = "Submitted", department: str = "", priority: str = "", q: str = "",
          user: User = Depends(staff), db: Session = Depends(get_db)):
    slas = sla_map(db)
    query = db.query(Complaint)
    if status == "Open":
        query = query.filter(Complaint.status.notin_(CLOSED))
    elif status:
        query = query.filter(Complaint.status == status)
    if q:
        query = query.filter((Complaint.text.contains(q)) | (Complaint.tracking_id.contains(q.upper())))
    rows = query.order_by(Complaint.created_at.desc()).limit(600).all()
    items = [queue_item(c, slas) for c in rows]
    if department:
        items = [i for i in items if i["current"]["department"] == department]
    if priority:
        items = [i for i in items if i["current"]["priority"] == priority]
    # most urgent first, then oldest first
    items.sort(key=lambda i: (-PRIORITY_RANK.get(i["current"]["priority"], 0), i["created_at"]))
    counts = dict(db.query(Complaint.status, func.count()).group_by(Complaint.status).all())
    return {"items": items[:200], "total": len(items), "counts": {s: counts.get(s, 0) for s in STATUSES}}


def _get(db, cid) -> Complaint:
    c = db.get(Complaint, cid)
    if not c:
        raise HTTPException(404, "Complaint not found")
    return c


@router.get("/complaints/{cid}")
def detail(cid: int, user: User = Depends(staff), db: Session = Depends(get_db)):
    c = _get(db, cid)
    ai = dict(c.ai or {})
    if "explanations" not in ai:  # sample history rows are explained on first open
        ai["explanations"] = get_predictor().predict(c.text, c.created_at)["explanations"]
        ai["explained_with_version"] = get_predictor().version
        c.ai = ai
        db.commit()
    slas = sla_map(db)
    fb = db.query(Feedback).filter_by(complaint_id=c.id).order_by(Feedback.created_at).all()
    names = dict(db.query(User.id, User.name).all())
    return {
        "id": c.id, "tracking_id": c.tracking_id, "text": c.text, "language": c.language,
        "photo_url": f"/api/photos/{c.photo}" if c.photo else None, "lat": c.lat, "lng": c.lng,
        "ward": c.ward.name if c.ward else None, "status": c.status, "is_sample": c.is_sample,
        "created_at": c.created_at.isoformat(), "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
        "citizen": c.citizen.name, "ai": ai, "extraction": c.extraction, "extraction_status": c.extraction_status,
        "final": {"category": c.final_category, "department": c.final_department, "priority": c.final_priority,
                  "expected_days": c.final_days, "reviewed_by": names.get(c.reviewed_by),
                  "reviewed_at": c.reviewed_at.isoformat() if c.reviewed_at else None},
        "current": current_view(c, slas),
        "feedback": [{"field": f.field, "ai_value": f.ai_value, "officer_value": f.officer_value, "action": f.action,
                      "reason": f.reason, "officer": names.get(f.officer_id), "at": f.created_at.isoformat()}
                     for f in fb],
        "events": [{"kind": e.kind, "status": e.status, "message": e.message, "public": e.public,
                    "actor": names.get(e.actor_id), "at": e.created_at.isoformat()} for e in c.events],
        "statuses": STATUSES,
    }


class Decision(BaseModel):
    category: str
    department: str
    priority: str
    reasons: dict[str, str] = {}
    note: str = ""


@router.post("/complaints/{cid}/decision")
def decide(cid: int, body: Decision, user: User = Depends(staff), db: Session = Depends(get_db)):
    c = _get(db, cid)
    if c.status in CLOSED:
        raise HTTPException(400, f"This complaint is already {c.status.lower()}.")
    if body.category not in CATEGORIES or body.department not in DEPARTMENTS or body.priority not in PRIORITIES:
        raise HTTPException(400, "Unknown category, department or priority.")
    ai = c.ai or {}
    chosen = {"category": body.category, "department": body.department, "priority": body.priority}
    overrides = []
    for field, value in chosen.items():
        action = "accept" if value == ai.get(field) else "override"
        reason = (body.reasons.get(field) or "").strip()
        if action == "override":
            if len(reason) < 3:
                raise HTTPException(400, f"Please give a reason for changing the {field}.")
            overrides.append(f"{field}: {ai.get(field)} -> {value} ({reason})")
        db.add(Feedback(complaint_id=c.id, field=field, ai_value=str(ai.get(field)), officer_value=value,
                        action=action, reason=reason, officer_id=user.id, model_version=ai.get("model_version")))
    days = ai.get("expected_days")
    if body.category != ai.get("category") or body.priority != ai.get("priority"):
        days = round(get_predictor().expected_days(body.category, body.priority, c.created_at)[0], 1)
    c.final_category, c.final_department, c.final_priority, c.final_days = (
        body.category, body.department, body.priority, days)
    c.reviewed_by, c.reviewed_at = user.id, datetime.now()
    first = c.status == "Submitted"
    if first:
        c.status = "Assigned"
    c.events.append(Event(kind="decision", public=False, actor_id=user.id,
                          message="Accepted all AI suggestions" if not overrides
                          else "Overrides: " + "; ".join(overrides)))
    c.events.append(Event(kind="status", status=c.status, actor_id=user.id,
                          message=f"Assigned to the {body.department} department. Expected resolution in about "
                                  f"{days:g} days." + (f" Note: {body.note.strip()}" if body.note.strip() else "")))
    db.commit()
    return detail(cid, user, db)


class StatusChange(BaseModel):
    status: str
    note: str = ""


@router.post("/complaints/{cid}/status")
def change_status(cid: int, body: StatusChange, user: User = Depends(staff), db: Session = Depends(get_db)):
    c = _get(db, cid)
    if body.status not in ("In Progress", "Resolved", "Rejected"):
        raise HTTPException(400, "Status must be In Progress, Resolved or Rejected.")
    if body.status != "Rejected" and c.final_department is None:
        raise HTTPException(400, "Review the AI suggestions (accept or override) before updating the status.")
    if c.status in CLOSED:
        raise HTTPException(400, f"This complaint is already {c.status.lower()}.")
    if body.status == "Rejected" and len(body.note.strip()) < 3:
        raise HTTPException(400, "Please give the citizen a reason for rejecting the complaint.")
    c.status = body.status
    if body.status in CLOSED:
        c.resolved_at = datetime.now()
    default = {"In Progress": "Field team is working on it", "Resolved": "Issue resolved",
               "Rejected": "Complaint closed"}[body.status]
    c.events.append(Event(kind="status", status=body.status, actor_id=user.id, message=body.note.strip() or default))
    db.commit()
    return detail(cid, user, db)


@router.post("/complaints/{cid}/extract")
def extract(cid: int, user: User = Depends(staff), db: Session = Depends(get_db)):
    _get(db, cid)
    run_extraction(cid)
    db.expire_all()
    c = _get(db, cid)
    if c.extraction_status != "done":
        raise HTTPException(503, (c.extraction or {}).get("error", "Extraction failed"))
    return {"extraction": c.extraction, "extraction_status": c.extraction_status}


class DraftRequest(BaseModel):
    note: str = ""


@router.post("/complaints/{cid}/draft-reply")
def draft(cid: int, body: DraftRequest, user: User = Depends(staff), db: Session = Depends(get_db)):
    c = _get(db, cid)
    cur = current_view(c, sla_map(db))
    try:
        return gemini.draft_reply(text=c.text, language=c.language, tracking_id=c.tracking_id, status=c.status,
                                  department=cur["department"], expected_days=cur["expected_days"],
                                  officer_note=body.note)
    except gemini.GeminiUnavailable as e:
        raise HTTPException(503, str(e))


class Reply(BaseModel):
    message: str


@router.post("/complaints/{cid}/reply")
def reply(cid: int, body: Reply, user: User = Depends(staff), db: Session = Depends(get_db)):
    c = _get(db, cid)
    msg = body.message.strip()
    if len(msg) < 5:
        raise HTTPException(400, "The reply is empty.")
    c.events.append(Event(kind="reply", status=c.status, actor_id=user.id, message=msg))
    db.commit()
    return detail(cid, user, db)
