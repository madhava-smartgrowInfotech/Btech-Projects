"""A simulated hospital: a small FHIR R4 REST server with its own SQLite database.

Run one process per hospital, e.g.
    set HOSPITAL_KEY=A && python -m uvicorn hospitals.hospital_app:app --port 12061

Every call except /fhir/metadata needs a service token (JWT signed with the shared
secret) whose audience is this hospital and whose SMART-style scope covers the action.
"""
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fhir.resources.R4B import construct_fhir_element

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.config import HOSPITAL_SHARED_SECRET, HOSPITALS, PLATFORM_URL  # noqa: E402
from hospitals.store import connect, upsert  # noqa: E402

KEY = os.getenv("HOSPITAL_KEY", "A").upper()
HOSP = HOSPITALS[KEY]
conn = connect(HOSP["db"])
app = FastAPI(title=f"{HOSP['name']} FHIR R4 server")

SEARCHABLE = {"Patient", "Encounter", "Condition", "MedicationRequest", "Observation",
              "DiagnosticReport", "AllergyIntolerance", "CarePlan"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def outcome(status: int, text: str):
    raise HTTPException(status, detail={"resourceType": "OperationOutcome",
                                        "issue": [{"severity": "error", "code": "processing", "diagnostics": text}]})


def require_scope(needed: str):
    """SMART-on-FHIR style check: token must be for this hospital and carry the scope."""
    def dep(authorization: str = Header(default="")):
        if not authorization.startswith("Bearer "):
            outcome(401, "Missing bearer token")
        try:
            claims = jwt.decode(authorization[7:], HOSPITAL_SHARED_SECRET, algorithms=["HS256"], audience=f"hospital-{KEY}")
        except jwt.PyJWTError as e:
            outcome(401, f"Invalid token: {e}")
        scopes = claims.get("scope", "").split()
        if needed not in scopes and "system/*.*" not in scopes:
            outcome(403, f"Scope {needed} required")
        return claims
    return dep


def searchset(resources: list[dict]) -> dict:
    return {"resourceType": "Bundle", "type": "searchset", "total": len(resources),
            "entry": [{"fullUrl": f"{HOSP['base_url']}/{r['resourceType']}/{r['id']}", "resource": r,
                       "search": {"mode": "match"}} for r in resources]}


def rows(sql: str, args=()) -> list[dict]:
    return [json.loads(r["json"]) for r in conn.execute(sql, args).fetchall()]


@app.get("/fhir/metadata")
def metadata():
    return {"resourceType": "CapabilityStatement", "status": "active", "kind": "instance", "fhirVersion": "4.0.1",
            "date": now_iso(), "format": ["json"], "software": {"name": HOSP["name"]},
            "implementation": {"description": HOSP["name"], "url": HOSP["base_url"]},
            "rest": [{"mode": "server", "security": {"service": [{"text": "SMART-on-FHIR style system scopes (JWT bearer)"}]},
                      "resource": [{"type": t, "interaction": [{"code": "read"}, {"code": "search-type"}]}
                                   for t in sorted(SEARCHABLE)]}]}


@app.get("/fhir/stats")
def stats(_=Depends(require_scope("system/*.read"))):
    counts = {r["type"]: r["n"] for r in conn.execute("SELECT type, COUNT(*) n FROM resources GROUP BY type")}
    return {"hospital": KEY, "name": HOSP["name"], "counts": counts}


@app.get("/fhir/Patient")
def search_patients(name: str = "", birthdate: str = "", _count: int = 1000,
                    _=Depends(require_scope("system/Patient.read"))):
    pats = rows("SELECT json FROM resources WHERE type='Patient' ORDER BY id")
    out = []
    for p in pats:
        full = " ".join(p["name"][0].get("given", []) + [p["name"][0].get("family", "")]).lower()
        if name and name.lower() not in full:
            continue
        if birthdate and p.get("birthDate") != birthdate:
            continue
        out.append(p)
    return searchset(out[:_count])


@app.get("/fhir/{rtype}")
def search(rtype: str, patient: str, _=Depends(require_scope("system/*.read"))):
    if rtype not in SEARCHABLE:
        outcome(404, f"Unsupported resource type {rtype}")
    pid = patient.split("/")[-1]
    return searchset(rows("SELECT json FROM resources WHERE type=? AND patient_id=? ORDER BY date", (rtype, pid)))


@app.get("/fhir/{rtype}/{rid}")
def read(rtype: str, rid: str, _=Depends(require_scope("system/*.read"))):
    found = rows("SELECT json FROM resources WHERE type=? AND id=?", (rtype, rid))
    if not found:
        outcome(404, f"{rtype}/{rid} not found")
    return found[0]


@app.post("/fhir")
async def transaction(request: Request, _=Depends(require_scope("system/*.write"))):
    """Accept a transaction Bundle of new clinical resources recorded at this hospital."""
    bundle = await request.json()
    if bundle.get("resourceType") != "Bundle" or bundle.get("type") != "transaction":
        outcome(400, "Expected a transaction Bundle")
    responses = []
    for entry in bundle.get("entry", []):
        res = entry["resource"]
        res.setdefault("id", str(uuid.uuid4()))
        try:
            construct_fhir_element(res["resourceType"], res)
        except Exception as e:
            outcome(422, f"{res.get('resourceType')} failed FHIR validation: {e}")
        subject = (res.get("subject") or res.get("patient") or {}).get("reference", "")
        pid = subject.split("/")[-1]
        if not rows("SELECT json FROM resources WHERE type='Patient' AND id=?", (pid,)):
            outcome(404, f"Unknown patient {subject}")
        upsert(conn, res, pid)
        responses.append({"response": {"status": "201 Created", "location": f"{res['resourceType']}/{res['id']}"}})
    conn.commit()
    return {"resourceType": "Bundle", "type": "transaction-response", "entry": responses}


def build_summary(pid: str) -> dict:
    """Post-treatment FHIR summary: patient, recent encounters, active problems/meds, latest labs, follow-ups."""
    patient = rows("SELECT json FROM resources WHERE type='Patient' AND id=?", (pid,))
    if not patient:
        outcome(404, f"Patient/{pid} not found")
    by = lambda t, sql_tail="", args=(): rows(  # noqa: E731
        f"SELECT json FROM resources WHERE type=? AND patient_id=? {sql_tail}", (t, pid, *args))
    encounters = by("Encounter", "ORDER BY date DESC LIMIT 3")
    conditions = [c for c in by("Condition") if c.get("clinicalStatus", {}).get("coding", [{}])[0].get("code") == "active"]
    meds = [m for m in by("MedicationRequest") if m.get("status") == "active"]
    labs = by("Observation", "ORDER BY date DESC LIMIT 12")
    plans = [p for p in by("CarePlan") if p.get("status") == "active"]
    resources = patient + encounters + conditions + meds + labs + plans
    bundle = {"resourceType": "Bundle", "id": str(uuid.uuid4()), "type": "collection", "timestamp": now_iso(),
              "meta": {"source": HOSP["base_url"], "tag": [{"system": "urn:unihealth:hospital", "code": KEY, "display": HOSP["name"]}]},
              "entry": [{"fullUrl": f"{HOSP['base_url']}/{r['resourceType']}/{r['id']}", "resource": r} for r in resources]}
    construct_fhir_element("Bundle", bundle)
    return bundle


@app.post("/fhir/Patient/{pid}/$sync-summary")
def sync_summary(pid: str, _=Depends(require_scope("system/*.write"))):
    """Push a post-treatment summary to the UniHealth platform. The originals stay here."""
    bundle = build_summary(pid)
    token = jwt.encode({"iss": f"hospital-{KEY}", "aud": "unihealth-platform", "scope": "system/Bundle.write",
                        "exp": datetime.now(timezone.utc) + timedelta(minutes=2)}, HOSPITAL_SHARED_SECRET, algorithm="HS256")
    r = httpx.post(f"{PLATFORM_URL}/sync", json=bundle, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    if r.status_code >= 400:
        outcome(502, f"Platform rejected summary: {r.text[:300]}")
    return {"pushed_entries": len(bundle["entry"]), "platform": r.json()}
