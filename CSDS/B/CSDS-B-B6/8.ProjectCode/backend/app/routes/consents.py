"""Patient consent (FHIR Consent resources) and access requests."""
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user, require
from ..config import CATEGORIES, HOSPITALS
from ..db import AccessRequest, Consent, User, get_db, utcnow
from ..services import ledger, records

router = APIRouter(tags=["consents"])


def view(c: Consent) -> dict:
    return {"id": c.id, "hospital": c.grantee_hospital, "hospital_name": HOSPITALS[c.grantee_hospital]["name"],
            "categories": json.loads(c.categories), "status": c.status, "expires": c.expires,
            "created_at": c.created_at, "updated_at": c.updated_at, "fhir": json.loads(c.fhir_json)}


def fhir_hash(res: dict) -> str:
    return hashlib.sha256(json.dumps(res, sort_keys=True).encode()).hexdigest()


@router.get("/consents")
def list_consents(user: User = Depends(require("patient")), db: Session = Depends(get_db)):
    pid = records.patient_person_id(db, user)
    return [view(c) for c in db.scalars(select(Consent).where(Consent.person_id == pid).order_by(Consent.created_at.desc()))]


class ConsentBody(BaseModel):
    hospital: str
    categories: list[str]
    days: int | None = 90


@router.post("/consents")
def grant(body: ConsentBody, user: User = Depends(require("patient")), db: Session = Depends(get_db)):
    if body.hospital not in HOSPITALS:
        raise HTTPException(400, "Unknown hospital")
    cats = [c for c in body.categories if c in CATEGORIES]
    if not cats:
        raise HTTPException(400, "Choose at least one data category")
    person = records.person_or_404(db, records.patient_person_id(db, user))
    # One active consent per hospital: a new grant replaces the old one.
    for old in db.scalars(select(Consent).where(Consent.person_id == person.id, Consent.grantee_hospital == body.hospital,
                                                Consent.status == "active")):
        revoke_consent(db, old, user.username, "replaced")
    now = datetime.now(timezone.utc)
    expires = (now + timedelta(days=body.days)).isoformat(timespec="seconds") if body.days else None
    cid = str(uuid.uuid4())
    res = records.build_consent_resource(cid, person, body.hospital, cats, "active", now.isoformat(timespec="seconds"), expires)
    c = Consent(id=cid, person_id=person.id, grantee_hospital=body.hospital, categories=json.dumps(cats),
                status="active", expires=expires, fhir_json=json.dumps(res))
    db.add(c)
    for req in db.scalars(select(AccessRequest).where(AccessRequest.person_id == person.id,
                                                      AccessRequest.hospital_key == body.hospital,
                                                      AccessRequest.status == "blocked")):
        req.status = "approved"
    db.commit()
    ledger.append(db, user.username, "consent.grant", person.id,
                  {"consent": cid, "hospital": body.hospital, "categories": cats, "expires": expires, "fhir_sha256": fhir_hash(res)})
    return view(c)


def revoke_consent(db: Session, c: Consent, actor: str, why: str = "revoked by patient"):
    res = json.loads(c.fhir_json)
    res["status"] = "inactive"
    c.status, c.fhir_json, c.updated_at = "inactive", json.dumps(res), utcnow()
    db.commit()
    ledger.append(db, actor, "consent.revoke", c.person_id,
                  {"consent": c.id, "hospital": c.grantee_hospital, "why": why, "fhir_sha256": fhir_hash(res)})


@router.post("/consents/{cid}/revoke")
def revoke(cid: str, user: User = Depends(require("patient")), db: Session = Depends(get_db)):
    c = db.get(Consent, cid)
    if not c or c.person_id != records.patient_person_id(db, user):
        raise HTTPException(404, "Consent not found")
    if c.status != "active":
        raise HTTPException(400, "Consent is already inactive")
    revoke_consent(db, c, user.username)
    return view(c)


@router.get("/access/requests")
def access_requests(user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = select(AccessRequest).order_by(AccessRequest.created_at.desc()).limit(50)
    if user.role == "patient":
        q = q.where(AccessRequest.person_id == records.patient_person_id(db, user))
    elif user.role == "doctor":
        q = q.where(AccessRequest.doctor_username == user.username)
    return [{"id": r.id, "person_id": r.person_id, "doctor": r.doctor_name, "hospital": r.hospital_key,
             "hospital_name": HOSPITALS[r.hospital_key]["name"], "reason": r.reason, "status": r.status,
             "created_at": r.created_at} for r in db.scalars(q)]
