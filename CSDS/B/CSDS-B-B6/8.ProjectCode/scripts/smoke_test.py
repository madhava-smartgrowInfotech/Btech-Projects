"""End-to-end smoke test against the running platform (8206) and hospital servers.

Run after run.bat (or the servers) are up:   venv\\Scripts\\python scripts\\smoke_test.py
"""
import os
import sys

import httpx

API = f"http://127.0.0.1:{os.getenv('BACKEND_PORT', '8206')}/api"
PW = os.getenv("DEMO_PASSWORD", "demo123")
failures = []


def check(name, cond, info=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" - {info}" if info else ""))
    if not cond:
        failures.append(name)


def login(c, user):
    r = c.post(f"{API}/auth/login", json={"username": user, "password": PW})
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['token']}"}


def main():
    c = httpx.Client(timeout=120)
    check("API health", c.get(f"{API}/health").status_code == 200)

    pat = login(c, "patient")
    me = c.get(f"{API}/auth/me", headers=pat).json()
    pid = me["person_id"]
    rec = c.get(f"{API}/records/me", headers=pat).json()
    hospitals = {s["hospital"] for s in rec["sources"] if s["status"] == "online"}
    check("F6 patient sees one timeline from three hospitals", len(hospitals) == 3 and len(rec["timeline"]) > 20,
          f"{len(rec['timeline'])} items from {sorted(hospitals)}")
    check("F2 MPI links patient with confidence scores", all(0 < s["confidence"] <= 1 for s in rec["sources"]),
          str([(s["hospital"], s["confidence"]) for s in rec["sources"]]))

    # Start clean: revoke any consent to Riverside (B) left from an earlier run.
    for cons in c.get(f"{API}/consents", headers=pat).json():
        if cons["hospital"] == "B" and cons["status"] == "active":
            c.post(f"{API}/consents/{cons['id']}/revoke", headers=pat)

    doc = login(c, "dr.riverside")
    found = c.get(f"{API}/mpi/search", params={"q": me["display_name"].split()[-1]}, headers=doc).json()
    check("F2 doctor finds patient through MPI search", any(f["person_id"] == pid for f in found), f"{len(found)} results")

    r = c.post(f"{API}/access/request", json={"person_id": pid, "reason": "Cardiology referral"}, headers=doc)
    check("F4 doctor blocked without consent", r.status_code == 403, r.json().get("detail", "")[:60])
    reqs = c.get(f"{API}/access/requests", headers=pat).json()
    check("F3 patient sees the blocked request", any(q["hospital"] == "B" and q["status"] == "blocked" for q in reqs))

    r = c.post(f"{API}/consents", json={"hospital": "B", "categories": ["encounters", "conditions", "medications", "labs", "allergies"], "days": 30}, headers=pat)
    consent = r.json()
    check("F3 consent granted as FHIR Consent", r.status_code == 200 and consent["fhir"]["resourceType"] == "Consent"
          and consent["fhir"]["status"] == "active")

    r = c.post(f"{API}/access/request", json={"person_id": pid, "reason": "Cardiology referral"}, headers=doc)
    merged = r.json()
    check("F4 doctor gets merged record after consent", r.status_code == 200 and len(merged["timeline"]) == len(rec["timeline"]),
          f"{len(merged.get('timeline', []))} items")

    r = c.get(f"{API}/risk/{pid}", headers=doc)
    risk = r.json()
    check("F7 risk panel (heart + diabetes) with top factors", r.status_code == 200 and risk["heart"]["top_factors"]
          and 0 <= risk["diabetes"]["probability"] <= 1,
          f"heart {risk.get('heart', {}).get('probability')} ({risk.get('heart', {}).get('level')}), "
          f"diabetes {risk.get('diabetes', {}).get('probability')}")

    r = c.get(f"{API}/records/{pid}/bundle", headers=doc)
    check("F6 FHIR bundle download", r.status_code == 200 and r.json()["resourceType"] == "Bundle",
          f"{len(r.json().get('entry', []))} entries")

    staff = login(c, "staff.lakeview")
    hs = c.get(f"{API}/hospitals", headers=staff).json()
    check("F1 three FHIR servers online", sum(h["online"] for h in hs) == 3, str([(h["key"], h["counts"].get("Patient")) for h in hs]))
    local_c = next(s["local_id"] for s in rec["sources"] if s["hospital"] == "C")
    r = c.post(f"{API}/hospitals/C/visits", headers=staff, json={
        "patient_id": local_c, "visit_type": "Cardiology follow-up", "diagnosis": "Hyperlipidemia review",
        "medication": "Atorvastatin 20 MG Oral Tablet", "dosage": "1 tablet at night", "follow_up_days": 14})
    sync = r.json()
    check("F5 hospital records visit and pushes FHIR summary", r.status_code == 200 and sync["sync"]["platform"]["person_id"] == pid,
          f"{sync.get('sync', {}).get('pushed_entries')} entries pushed" if r.status_code == 200 else r.text[:120])

    rem = c.get(f"{API}/reminders", headers=pat).json()
    check("F8 follow-up and medication reminders", any(x["kind"] == "follow-up" for x in rem) and any(x["kind"] == "medication" for x in rem),
          f"{len(rem)} reminders")

    r = c.post(f"{API}/assistant/explain", headers=pat, json={"language": "Telugu"})
    check("F8 assistant explains lipid panel in Telugu", r.status_code == 200 and len(r.json().get("text", "")) > 50,
          r.json().get("title", "") if r.status_code == 200 else r.text[:160])

    c.post(f"{API}/consents/{consent['id']}/revoke", headers=pat)
    r = c.post(f"{API}/access/request", json={"person_id": pid, "reason": "Cardiology referral"}, headers=doc)
    check("F3 access fails after revocation", r.status_code == 403)

    admin = login(c, "admin")
    audit = c.get(f"{API}/audit", headers=admin).json()
    actions = {e["action"] for e in audit["entries"]}
    check("F4 every access audited", {"access.denied", "record.access", "consent.grant", "consent.revoke", "sync.summary"} <= actions)
    check("F3 consent ledger verifies intact", audit["verification"]["intact"], f"{audit['verification']['entries']} entries")

    print(f"\n{'ALL PASSED' if not failures else f'{len(failures)} FAILED: {failures}'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
