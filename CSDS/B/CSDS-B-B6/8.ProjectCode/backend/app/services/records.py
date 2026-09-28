"""Consent checks, FHIR retrieval from every hospital that holds a person's records, and the merged timeline."""
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from fastapi import HTTPException
from fhir.resources.R4B import construct_fhir_element
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import CATEGORIES, HOSPITALS, TYPE_TO_CATEGORY
from ..db import Consent, Person, SyncedSummary, User
from . import fhir_client, mpi


# ---------- consent ----------

def active_consent(db: Session, person_id: str, hospital_key: str) -> Consent | None:
    now = datetime.now(timezone.utc).isoformat()
    for c in db.scalars(select(Consent).where(Consent.person_id == person_id, Consent.grantee_hospital == hospital_key,
                                              Consent.status == "active").order_by(Consent.created_at.desc())):
        if not c.expires or c.expires > now:
            return c
    return None


def build_consent_resource(cid: str, person: Person, hospital_key: str, categories: list[str], status: str,
                           start: str, expires: str | None) -> dict:
    """FHIR R4 Consent: the patient permits one hospital to access the chosen data categories."""
    period = {"start": start}
    if expires:
        period["end"] = expires
    res = {
        "resourceType": "Consent", "id": cid, "status": status,
        "scope": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/consentscope", "code": "patient-privacy"}]},
        "category": [{"coding": [{"system": "http://loinc.org", "code": "59284-0", "display": "Patient Consent"}]}],
        "patient": {"reference": f"Patient/{person.id}", "display": person.display_name},
        "dateTime": start,
        "organization": [{"display": "UniHealth"}],
        "policy": [{"uri": "urn:unihealth:policy:cross-hospital-record-sharing"}],
        "provision": {
            "type": "permit", "period": period,
            "actor": [{"role": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType", "code": "IRCP"}]},
                       "reference": {"identifier": {"system": "urn:unihealth:hospital", "value": hospital_key},
                                     "display": HOSPITALS[hospital_key]["name"]}}],
            "action": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/consentaction", "code": "access"}]}],
            "class": [{"system": "http://hl7.org/fhir/resource-types", "code": t} for c in categories for t in CATEGORIES[c]],
        },
    }
    construct_fhir_element("Consent", res)  # validate
    return res


# ---------- retrieval ----------

def person_or_404(db: Session, person_id: str) -> Person:
    mpi.ensure(db)
    p = db.get(Person, person_id)
    if not p:
        raise HTTPException(404, "Person not found in the Master Patient Index")
    return p


def patient_person_id(db: Session, user: User) -> str:
    pid = mpi.person_for_local(db, user.hospital_key, user.local_patient_id)
    if not pid:
        raise HTTPException(404, "Your hospital record is not linked yet")
    return pid


def fetch_resources(db: Session, person_id: str, categories: list[str]) -> tuple[list[tuple[str, dict]], list[dict]]:
    """Pull resources over FHIR REST from each linked hospital. Falls back to synced summaries if a hospital is down."""
    types = [t for c in categories for t in CATEGORIES[c]]
    links = mpi.links(db, person_id)

    def fetch(link, t):
        return fhir_client.bundle_resources(fhir_client.get(link.hospital_key, f"/{t}", patient=f"Patient/{link.local_id}"))

    # All hospital x resource-type searches run in parallel.
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = {(l.hospital_key, t): pool.submit(fetch, l, t) for l in links for t in types}
    out, sources = [], []
    for link in links:
        src = {"hospital": link.hospital_key, "name": HOSPITALS[link.hospital_key]["name"], "local_id": link.local_id,
               "confidence": link.score, "status": "online", "counts": {}}
        try:
            for t in types:
                res = futures[(link.hospital_key, t)].result()
                src["counts"][t] = len(res)
                out += [(link.hospital_key, r) for r in res]
        except fhir_client.HospitalError as e:
            src["status"] = f"offline - showing last synced summary ({e})"
        sources.append(src)
    # Add synced summary copies (deduplicated below against live hospital data).
    for s in db.scalars(select(SyncedSummary).where(SyncedSummary.person_id == person_id)):
        for r in fhir_client.bundle_resources(json.loads(s.bundle_json)):
            if r["resourceType"] in types:
                out.append((s.hospital_key, r))
    seen, merged = set(), []
    for hkey, r in out:
        k = (r["resourceType"], r["id"])
        if k not in seen:
            seen.add(k)
            merged.append((hkey, r))
    return merged, sources


def _text(cc: dict | None) -> str:
    if not cc:
        return ""
    return cc.get("text") or next((c.get("display") for c in cc.get("coding", []) if c.get("display")), "")


def _code(cc: dict | None) -> str:
    return next((c.get("code") for c in (cc or {}).get("coding", [])), "")


def obs_value(r: dict) -> str:
    if "valueQuantity" in r:
        q = r["valueQuantity"]
        return f"{round(q.get('value', 0), 2)} {q.get('unit', '')}".strip()
    if "valueCodeableConcept" in r:
        return _text(r["valueCodeableConcept"])
    if r.get("component"):
        vals = {_code(c["code"]): c.get("valueQuantity", {}).get("value") for c in r["component"]}
        if "8480-6" in vals and "8462-4" in vals:
            return f"{round(vals['8480-6'])}/{round(vals['8462-4'])} mmHg"
        return ", ".join(f"{_text(c['code'])}: {c.get('valueQuantity', {}).get('value')}" for c in r["component"])
    return r.get("valueString", "")


def timeline_item(hkey: str, r: dict) -> dict:
    t = r["resourceType"]
    item = {"id": r["id"], "type": t, "category": TYPE_TO_CATEGORY.get(t, "other"), "hospital": hkey,
            "hospital_name": HOSPITALS[hkey]["name"], "date": None, "title": "", "value": "", "status": ""}
    if t == "Encounter":
        item.update(date=r.get("period", {}).get("start"), title=_text((r.get("type") or [{}])[0]) or "Visit",
                    value=_text((r.get("reasonCode") or [{}])[0]), status=r.get("status", ""))
    elif t == "Condition":
        item.update(date=r.get("onsetDateTime") or r.get("recordedDate"), title=_text(r.get("code")),
                    status=_code(r.get("clinicalStatus")))
    elif t == "MedicationRequest":
        dose = (r.get("dosageInstruction") or [{}])[0]
        item.update(date=r.get("authoredOn"), title=_text(r.get("medicationCodeableConcept")),
                    value=dose.get("text", "") or ("as needed" if dose.get("asNeededBoolean") else ""), status=r.get("status", ""))
    elif t == "Observation":
        item.update(date=r.get("effectiveDateTime"), title=_text(r.get("code")), value=obs_value(r),
                    status=_code((r.get("category") or [{}])[0]), code=_code(r.get("code")))
    elif t == "DiagnosticReport":
        item.update(date=r.get("effectiveDateTime") or r.get("issued"), title=_text(r.get("code")),
                    value=f"{len(r.get('result', []))} results", status=r.get("status", ""), code=_code(r.get("code")),
                    results=[x["reference"].split("/")[-1] for x in r.get("result", [])])
    elif t == "AllergyIntolerance":
        item.update(date=r.get("recordedDate"), title=_text(r.get("code")), value=r.get("criticality", ""),
                    status=_code(r.get("clinicalStatus")))
    elif t == "CarePlan":
        item.update(date=r.get("period", {}).get("start"), title=r.get("description") or "Care plan",
                    value=_text((r.get("category") or [{}])[0]), status=r.get("status", ""))
    return item


def build_record(db: Session, person: Person, categories: list[str]) -> dict:
    merged, sources = fetch_resources(db, person.id, categories)
    timeline = sorted((timeline_item(h, r) for h, r in merged), key=lambda i: i["date"] or "", reverse=True)
    return {"person": {"id": person.id, "name": person.display_name, "birth_date": person.birth_date, "gender": person.gender},
            "categories": categories, "sources": sources, "timeline": timeline,
            "counts": {c: sum(1 for i in timeline if i["category"] == c) for c in categories},
            "_resources": merged}


def as_bundle(record: dict) -> dict:
    """The unified record as a FHIR R4 Bundle (collection), validated."""
    bundle = {"resourceType": "Bundle", "id": str(uuid.uuid4()), "type": "collection",
              "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "meta": {"tag": [{"system": "urn:unihealth", "code": "unified-record", "display": f"UniHealth record {record['person']['id']}"}]},
              "entry": [{"fullUrl": f"{HOSPITALS[h]['base_url']}/{r['resourceType']}/{r['id']}", "resource": r}
                        for h, r in record["_resources"]]}
    construct_fhir_element("Bundle", bundle)
    return bundle
