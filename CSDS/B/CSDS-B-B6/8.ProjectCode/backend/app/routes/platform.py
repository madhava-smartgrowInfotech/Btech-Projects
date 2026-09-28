"""Login, Master Patient Index, hospital console, post-treatment sync, reminders and the audit ledger."""
import json
import uuid
from datetime import date, datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fhir.resources.R4B import construct_fhir_element
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import check_password, current_user, make_token, require
from ..config import HOSPITAL_SHARED_SECRET, HOSPITALS
from ..db import LedgerEntry, Person, Reminder, SyncedSummary, User, get_db
from ..services import fhir_client, ledger, mpi, records
from ..services import reminders as reminder_svc

router = APIRouter()


# ---------- auth ----------

class LoginBody(BaseModel):
    username: str
    password: str


def user_view(u: User) -> dict:
    return {"username": u.username, "role": u.role, "display_name": u.display_name, "hospital": u.hospital_key,
            "hospital_name": HOSPITALS[u.hospital_key]["name"] if u.hospital_key else None}


@router.post("/auth/login", tags=["auth"])
def login(body: LoginBody, db: Session = Depends(get_db)):
    u = db.scalar(select(User).where(User.username == body.username.strip().lower()))
    if not u or not check_password(body.password, u.password_hash):
        raise HTTPException(401, "Wrong username or password")
    ledger.append(db, u.username, "auth.login", None, {"role": u.role})
    return {"token": make_token(u), "user": user_view(u)}


@router.get("/auth/me", tags=["auth"])
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    out = user_view(user)
    if user.role == "patient":
        out["person_id"] = records.patient_person_id(db, user)
    return out


# ---------- Master Patient Index ----------

def hospital_error(e: fhir_client.HospitalError):
    raise HTTPException(502, str(e))


@router.get("/mpi/search", tags=["mpi"])
def mpi_search(q: str = "", birth_date: str = "", user: User = Depends(require("doctor", "admin")), db: Session = Depends(get_db)):
    try:
        results = mpi.search(db, q, birth_date)
    except fhir_client.HospitalError as e:
        hospital_error(e)
    ledger.append(db, user.username, "mpi.search", None, {"q": q, "birth_date": birth_date, "results": len(results)})
    return results


@router.post("/mpi/rebuild", tags=["mpi"])
def mpi_rebuild(user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    try:
        out = mpi.rebuild(db)
    except fhir_client.HospitalError as e:
        hospital_error(e)
    ledger.append(db, user.username, "mpi.rebuild", None, out)
    return out


@router.get("/mpi/persons", tags=["mpi"])
def mpi_persons(user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    try:
        mpi.ensure(db)
    except fhir_client.HospitalError as e:
        hospital_error(e)
    out = []
    for p in db.scalars(select(Person).order_by(Person.display_name)):
        ls = mpi.links(db, p.id)
        out.append({"person_id": p.id, "name": p.display_name, "birth_date": p.birth_date, "gender": p.gender,
                    "links": [{"hospital": l.hospital_key, "local_id": l.local_id, "name": l.name, "birth_date": l.birth_date,
                               "phone": l.phone, "confidence": l.score} for l in ls]})
    return sorted(out, key=lambda p: (-len(p["links"]), p["name"]))


# ---------- hospitals (console) ----------

@router.get("/hospitals", tags=["hospitals"])
def hospitals(user: User = Depends(current_user)):
    out = []
    for k, h in HOSPITALS.items():
        item = {"key": k, "name": h["name"], "base_url": h["base_url"], "online": False, "counts": {}}
        try:
            meta = fhir_client.metadata(k)
            item.update(online=True, fhir_version=meta.get("fhirVersion"),
                        counts=fhir_client.get(k, "/stats")["counts"])
        except fhir_client.HospitalError as e:
            item["error"] = str(e)
        out.append(item)
    return out


def staff_for(user: User, key: str):
    if key not in HOSPITALS:
        raise HTTPException(404, "Unknown hospital")
    if user.role == "staff" and user.hospital_key != key:
        raise HTTPException(403, "Records staff can only work on their own hospital")


@router.get("/hospitals/{key}/patients", tags=["hospitals"])
def hospital_patients(key: str, q: str = "", user: User = Depends(require("staff", "admin")), db: Session = Depends(get_db)):
    staff_for(user, key)
    try:
        pats = fhir_client.bundle_resources(fhir_client.get(key, "/Patient", scope="system/Patient.read", name=q, _count=500))
    except fhir_client.HospitalError as e:
        hospital_error(e)
    return [mpi.record_from_patient(key, p) for p in pats]


class VisitBody(BaseModel):
    patient_id: str
    visit_type: str = "Outpatient consultation"
    diagnosis: str
    medication: str = ""
    dosage: str = ""
    follow_up_days: int | None = 30


@router.post("/hospitals/{key}/visits", tags=["hospitals"])
def record_visit(key: str, body: VisitBody, user: User = Depends(require("staff", "admin")), db: Session = Depends(get_db)):
    """Record a treatment episode at the hospital (stays there), then the hospital pushes a FHIR summary."""
    staff_for(user, key)
    if not body.diagnosis.strip():
        raise HTTPException(400, "Diagnosis is required")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    subj = {"reference": f"Patient/{body.patient_id}"}
    enc_id = str(uuid.uuid4())
    entries = [
        {"resourceType": "Encounter", "id": enc_id, "status": "finished",
         "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB"},
         "type": [{"text": body.visit_type}], "subject": subj, "period": {"start": now, "end": now},
         "reasonCode": [{"text": body.diagnosis}], "serviceProvider": {"display": HOSPITALS[key]["name"]}},
        {"resourceType": "Condition", "id": str(uuid.uuid4()), "subject": subj, "encounter": {"reference": f"Encounter/{enc_id}"},
         "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
         "verificationStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]},
         "code": {"text": body.diagnosis}, "onsetDateTime": now, "recordedDate": now},
    ]
    if body.medication.strip():
        entries.append({"resourceType": "MedicationRequest", "id": str(uuid.uuid4()), "status": "active", "intent": "order",
                        "medicationCodeableConcept": {"text": body.medication}, "subject": subj,
                        "encounter": {"reference": f"Encounter/{enc_id}"}, "authoredOn": now,
                        "dosageInstruction": [{"text": body.dosage or "As directed"}]})
    if body.follow_up_days:
        due = (date.today() + timedelta(days=body.follow_up_days)).isoformat()
        entries.append({"resourceType": "CarePlan", "id": str(uuid.uuid4()), "status": "active", "intent": "plan",
                        "subject": subj, "encounter": {"reference": f"Encounter/{enc_id}"},
                        "category": [{"text": "Follow-up"}], "period": {"start": due},
                        "description": f"Follow-up visit at {HOSPITALS[key]['name']} for {body.diagnosis}"})
    tx = {"resourceType": "Bundle", "type": "transaction",
          "entry": [{"resource": r, "request": {"method": "POST", "url": r["resourceType"]}} for r in entries]}
    try:
        created = fhir_client.post(key, "", tx)
        pushed = fhir_client.post(key, f"/Patient/{body.patient_id}/$sync-summary")
    except fhir_client.HospitalError as e:
        hospital_error(e)
    ledger.append(db, user.username, "hospital.visit", pushed["platform"].get("person_id"),
                  {"hospital": key, "patient": body.patient_id, "created": len(created["entry"])})
    return {"created": created, "sync": pushed}


@router.post("/hospitals/{key}/patients/{pid}/sync", tags=["hospitals"])
def push_summary(key: str, pid: str, user: User = Depends(require("staff", "admin"))):
    staff_for(user, key)
    try:
        return fhir_client.post(key, f"/Patient/{pid}/$sync-summary")
    except fhir_client.HospitalError as e:
        hospital_error(e)


# ---------- post-treatment sync (called by hospitals) ----------

@router.post("/sync", tags=["sync"])
async def receive_summary(request: Request, authorization: str = Header(default=""), db: Session = Depends(get_db)):
    """A hospital pushes a FHIR summary Bundle. The platform keeps a copy; the original stays at the hospital."""
    try:
        claims = jwt.decode(authorization.removeprefix("Bearer "), HOSPITAL_SHARED_SECRET, algorithms=["HS256"],
                            audience="unihealth-platform")
    except jwt.PyJWTError as e:
        raise HTTPException(401, f"Invalid hospital token: {e}")
    if "system/Bundle.write" not in claims.get("scope", "").split():
        raise HTTPException(403, "Scope system/Bundle.write required")
    hkey = claims["iss"].removeprefix("hospital-")
    if hkey not in HOSPITALS:
        raise HTTPException(403, "Unknown hospital")
    bundle = await request.json()
    try:
        construct_fhir_element("Bundle", bundle)
    except Exception as e:
        raise HTTPException(422, f"Summary failed FHIR validation: {str(e)[:300]}")
    resources = fhir_client.bundle_resources(bundle)
    patient = next((r for r in resources if r["resourceType"] == "Patient"), None)
    if not patient:
        raise HTTPException(422, "Summary must contain the Patient resource")
    person_id = mpi.person_for_local(db, hkey, patient["id"])
    if not person_id:  # new patient at that hospital: re-run linkage
        mpi.rebuild(db)
        person_id = mpi.person_for_local(db, hkey, patient["id"])
    s = SyncedSummary(person_id=person_id, hospital_key=hkey, local_id=patient["id"], bundle_json=json.dumps(bundle),
                      entries=len(resources))
    db.add(s)
    db.commit()
    added = reminder_svc.from_resources(db, person_id, [(hkey, r) for r in resources]) if person_id else 0
    ledger.append(db, f"hospital-{hkey}", "sync.summary", person_id,
                  {"hospital": hkey, "local_id": patient["id"], "entries": len(resources), "bundle": bundle.get("id"),
                   "reminders_added": added})
    return {"summary_id": s.id, "person_id": person_id, "entries": len(resources), "reminders_added": added}


@router.get("/sync", tags=["sync"])
def list_summaries(user: User = Depends(require("staff", "admin")), db: Session = Depends(get_db)):
    q = select(SyncedSummary).order_by(SyncedSummary.id.desc()).limit(50)
    if user.role == "staff":
        q = q.where(SyncedSummary.hospital_key == user.hospital_key)
    return [{"id": s.id, "person_id": s.person_id, "hospital": s.hospital_key, "hospital_name": HOSPITALS[s.hospital_key]["name"],
             "local_id": s.local_id, "entries": s.entries, "received_at": s.received_at} for s in db.scalars(q)]


# ---------- reminders ----------

@router.get("/reminders", tags=["reminders"])
def get_reminders(user: User = Depends(require("patient")), db: Session = Depends(get_db)):
    return reminder_svc.listing(db, records.patient_person_id(db, user))


class ReminderBody(BaseModel):
    text: str
    due: str
    kind: str = "custom"


@router.post("/reminders", tags=["reminders"])
def add_reminder(body: ReminderBody, user: User = Depends(require("patient")), db: Session = Depends(get_db)):
    if not body.text.strip():
        raise HTTPException(400, "Reminder text is required")
    pid = records.patient_person_id(db, user)
    db.add(Reminder(person_id=pid, kind=body.kind, text=body.text.strip(), due=body.due[:10],
                    source_key=f"custom:{uuid.uuid4()}", source="Added by you"))
    db.commit()
    return reminder_svc.listing(db, pid)


@router.post("/reminders/{rid}/toggle", tags=["reminders"])
def toggle_reminder(rid: int, user: User = Depends(require("patient")), db: Session = Depends(get_db)):
    pid = records.patient_person_id(db, user)
    r = db.get(Reminder, rid)
    if not r or r.person_id != pid:
        raise HTTPException(404, "Reminder not found")
    r.done = not r.done
    db.commit()
    return reminder_svc.listing(db, pid)


# ---------- audit ----------

@router.get("/audit", tags=["audit"])
def audit(user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = select(LedgerEntry).order_by(LedgerEntry.id.desc()).limit(300)
    if user.role == "patient":
        q = q.where(LedgerEntry.person_id == records.patient_person_id(db, user))
    elif user.role in ("doctor", "staff"):
        q = q.where(LedgerEntry.actor == user.username)
    entries = [{"id": e.id, "ts": e.ts, "actor": e.actor, "action": e.action, "person_id": e.person_id,
                "detail": json.loads(e.detail), "hash": e.hash, "prev_hash": e.prev_hash} for e in db.scalars(q)]
    return {"entries": entries, "verification": ledger.verify(db)}


@router.get("/audit/verify", tags=["audit"])
def audit_verify(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return ledger.verify(db)
