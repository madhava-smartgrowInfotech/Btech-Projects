"""Unified record, doctor access requests, FHIR export, risk prediction and AI assistant."""
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import current_user, require
from ..config import CATEGORIES
from ..db import AccessRequest, User, get_db
from ..services import assistant, ledger, records, risk
from ..services import reminders as reminder_svc

router = APIRouter(tags=["records"])


def authorize(db: Session, user: User, person_id: str, action: str, reason: str = ""):
    """Patients see their own record. Doctors need an active consent for their hospital. Every decision is audited."""
    if user.role == "patient":
        own = records.patient_person_id(db, user)
        if person_id not in ("me", own):
            raise HTTPException(403, "Patients can only open their own record")
        return records.person_or_404(db, own), list(CATEGORIES), None
    if user.role == "doctor":
        person = records.person_or_404(db, person_id)
        consent = records.active_consent(db, person_id, user.hospital_key)
        if not consent:
            ledger.append(db, user.username, "access.denied", person_id,
                          {"hospital": user.hospital_key, "action": action, "reason": reason or "no active consent"})
            raise HTTPException(403, "Access blocked: the patient has not granted consent to your hospital. "
                                     "Ask the patient to approve your request.")
        return person, json.loads(consent.categories), consent.id
    raise HTTPException(403, "Only the patient or a consented doctor can open clinical records")


def public(record: dict) -> dict:
    return {k: v for k, v in record.items() if not k.startswith("_")}


def load(db: Session, user: User, person_id: str, action: str, reason: str = "", need: list[str] | None = None):
    person, cats, consent_id = authorize(db, user, person_id, action, reason)
    if need:
        missing = [c for c in need if c not in cats]
        if missing:
            ledger.append(db, user.username, "access.denied", person.id, {"action": action, "reason": f"consent excludes {missing}"})
            raise HTTPException(403, f"Consent does not cover: {', '.join(missing)}")
    rec = records.build_record(db, person, cats)
    ledger.append(db, user.username, action, person.id,
                  {"consent": consent_id, "categories": cats, "reason": reason,
                   "hospitals": [s["hospital"] for s in rec["sources"]], "items": len(rec["timeline"])})
    return rec


@router.get("/records/{person_id}")
def get_record(person_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    rec = load(db, user, person_id, "record.view")
    if user.role == "patient":
        reminder_svc.from_resources(db, rec["person"]["id"], rec["_resources"])
    return public(rec)


class AccessBody(BaseModel):
    person_id: str
    reason: str = "Continuity of care"


@router.post("/access/request")
def request_access(body: AccessBody, user: User = Depends(require("doctor")), db: Session = Depends(get_db)):
    """Doctor asks for a patient's history. Blocked (and queued for the patient) until consent exists."""
    records.person_or_404(db, body.person_id)
    allowed = records.active_consent(db, body.person_id, user.hospital_key) is not None
    db.add(AccessRequest(person_id=body.person_id, doctor_username=user.username, doctor_name=user.display_name,
                         hospital_key=user.hospital_key, reason=body.reason, status="granted" if allowed else "blocked"))
    db.commit()
    return public(load(db, user, body.person_id, "record.access", body.reason))


@router.get("/records/{person_id}/bundle")
def export_bundle(person_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    rec = load(db, user, person_id, "record.export")
    return JSONResponse(records.as_bundle(rec), headers={
        "Content-Disposition": f'attachment; filename="unihealth-{rec["person"]["id"]}.fhir.json"'})


@router.get("/risk/{person_id}")
def risk_panel(person_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    rec = load(db, user, person_id, "risk.assess", need=["labs", "conditions"])
    feats = risk.extract_features(rec["person"], rec["_resources"])
    return {"person": rec["person"], "heart": risk.score("heart", feats["heart"]),
            "diabetes": risk.score("diabetes", feats["diabetes"]),
            "disclaimer": "Decision support only - not a diagnosis. Review with a qualified clinician."}


class AssistantBody(BaseModel):
    person_id: str = "me"
    language: str = "English"
    report_id: str | None = None
    question: str = ""


@router.post("/assistant/{kind}")
def run_assistant(kind: str, body: AssistantBody, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if kind not in ("explain", "summary", "ask"):
        raise HTTPException(404, "Unknown assistant action")
    if kind == "ask" and not body.question.strip():
        raise HTTPException(400, "Please type a question")
    rec = load(db, user, body.person_id, f"assistant.{kind}")
    tl = rec["timeline"]
    if kind == "explain":
        out = assistant.explain_report(tl, body.report_id, body.language)
    elif kind == "summary":
        out = assistant.summarise(tl, body.language)
    else:
        out = assistant.ask(tl, body.question, body.language)
    out["disclaimer"] = "AI-generated explanation to support you and your doctor - not a diagnosis."
    return out
