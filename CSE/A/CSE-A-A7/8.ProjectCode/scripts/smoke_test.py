"""End-to-end smoke test against the running API (default http://localhost:8307).

Flow: login -> extract every sample report (scores extraction vs expected.json) -> create a patient
from one report + vitals -> override it -> queue reorders -> metrics -> summary PDF.
Run:  venv\\Scripts\\python scripts\\smoke_test.py
"""
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8307"
fails = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)


def main():
    r = requests.get(f"{BASE}/api/health", timeout=10)
    check(r.ok and r.json()["model"], "health ok and model present")

    r = requests.post(f"{BASE}/api/auth/login", json={"email": "clinician@athena.health", "password": "wrong"})
    check(r.status_code == 401, "bad password rejected")
    r = requests.post(f"{BASE}/api/auth/login", json={"email": "clinician@athena.health", "password": "Athena@123"})
    check(r.ok, "login")
    H = {"Authorization": f"Bearer {r.json()['access_token']}"}
    check(requests.get(f"{BASE}/api/patients").status_code == 401, "queue requires auth")

    expected = json.loads((ROOT / "data" / "sample_reports" / "expected.json").read_text())
    tp = fp = fn = 0
    first = None
    for fname, exp in expected.items():
        path = ROOT / "data" / "sample_reports" / fname
        mime = "application/pdf" if fname.endswith(".pdf") else "image/png"
        t0 = time.time()
        r = requests.post(f"{BASE}/api/reports/extract", headers=H, files={"file": (fname, path.read_bytes(), mime)}, timeout=120)
        if not r.ok:
            check(False, f"extract {fname}: {r.status_code} {r.text[:100]}")
            continue
        got = {f for f, v in r.json()["flags"].items() if v}
        want = set(exp["flags"])
        tp += len(got & want)
        fp += len(got - want)
        fn += len(want - got)
        print(f"     {fname}: {time.time() - t0:.1f}s  missing={sorted(want - got)} extra={sorted(got - want)}")
        if first is None and fname.startswith("report_01"):
            first = (fname, r.json(), exp)
    prec = tp / max(tp + fp, 1)
    rec = tp / max(tp + fn, 1)
    check(prec >= 0.9 and rec >= 0.9, f"extraction precision {prec:.2f} recall {rec:.2f} over {len(expected)} reports")

    fname, rep, exp = first
    check(all(i["page"] in (1, 2) for i in rep["symptoms"] + rep["findings"]), "extracted items carry page numbers")
    r = requests.post(f"{BASE}/api/patients", headers=H, json={"name": "Smoke patient", "vitals": exp["vitals"], "report": rep,
                                                              "ocr_seconds": rep["seconds"]})
    check(r.ok, f"create patient: {r.status_code}")
    p = r.json()
    check(p["priority"] in (1, 2), f"STEMI case triaged high priority (got {p['priority']})")
    check(len(p["shap"]) >= 3 and abs(p["shap"][0]["impact"]) >= abs(p["shap"][-1]["impact"]), "SHAP list ordered by influence")
    print("     top drivers:", [s["label"] for s in p["shap"][:3]], "priority", p["priority"], "conf", p["confidence"])

    r = requests.post(f"{BASE}/api/patients/{p['id']}/override", headers=H, json={"priority": 5, "reason": ""})
    check(r.status_code == 422, "change without reason rejected")
    new = 1 if p["priority"] != 1 else 2
    r = requests.post(f"{BASE}/api/patients/{p['id']}/override", headers=H, json={"priority": new, "reason": "Smoke test override"})
    check(r.ok and r.json()["priority"] == new and len(r.json()["overrides"]) == 1, "override stored")
    q = requests.get(f"{BASE}/api/patients", headers=H).json()["items"]
    pr = [i["priority"] for i in q]
    check(pr == sorted(pr), "queue ordered by priority")
    check(any(i["id"] == p["id"] and i["priority"] == new for i in q), "queue reflects override")

    m = requests.get(f"{BASE}/api/metrics", headers=H).json()
    check(m["offline"]["accuracy"] > 0.5 and len(m["offline"]["per_class_recall"]) == 5, "metrics: accuracy + per-class recall")
    check(m["live"]["overridden"] >= 1 and m["live"]["mean_seconds_per_patient"] is not None, "metrics: overrides + seconds/patient")
    r = requests.get(f"{BASE}/api/patients/{p['id']}/summary.pdf", headers=H)
    check(r.ok and r.content[:4] == b"%PDF", "summary PDF")
    check(requests.get(f"{BASE}/api/patients/99999", headers=H).status_code == 404, "unknown patient 404")

    print("\nSMOKE TEST", "FAILED" if fails else "PASSED")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
