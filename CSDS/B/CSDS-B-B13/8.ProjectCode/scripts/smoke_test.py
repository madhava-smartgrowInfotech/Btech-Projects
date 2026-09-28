"""End-to-end smoke test: drives the running APISentry API through the whole flow.

Usage: python scripts/smoke_test.py
Requires the backend (port 8213) and both practice targets (12130/12131) running.
Exits non-zero on any failure.
"""
import os
import sys
import time

import httpx

BACKEND = os.getenv("APISENTRY_URL", "http://localhost:8213")
DEMO_EMAIL = os.getenv("DEMO_EMAIL", "demo@apisentry.local")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "demo12345")

PASS, FAIL = "PASS", "FAIL"
failures = []


def check(name, ok, detail=""):
    print(f"[{PASS if ok else FAIL}] {name}" + (f" - {detail}" if detail else ""))
    if not ok:
        failures.append(name)
    return ok


def main():
    c = httpx.Client(base_url=BACKEND, timeout=60)

    # 1. health
    r = c.get("/api/health")
    check("backend health", r.status_code == 200 and r.json().get("status") == "ok")

    # 2. auth (login demo; register if needed)
    r = c.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    if r.status_code != 200:
        r = c.post("/api/auth/register",
                   json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    check("login/register demo user", r.status_code == 200, f"status {r.status_code}")
    token = r.json()["token"]
    c.headers["Authorization"] = f"Bearer {token}"

    r = c.get("/api/auth/me")
    check("auth/me works", r.status_code == 200 and r.json().get("email") == DEMO_EMAIL)

    # 3. targets seeded
    r = c.get("/api/targets")
    targets = r.json()
    names = {t["name"]: t for t in targets}
    check("DemoPay + VulnBank seeded", "DemoPay" in names and "VulnBank" in names,
          f"targets: {list(names)}")
    demopay = names["DemoPay"]
    check("DemoPay reports endpoints", demopay["endpoint_count"] >= 8,
          f'{demopay["endpoint_count"]} endpoints')
    check("DemoPay in scope", demopay["in_scope"] is True)

    # 3b. F1 import flow (import the committed spec fresh)
    spec_text = open(os.path.join(os.path.dirname(__file__), "..", "targets",
                                  "demopay_openapi.json"), encoding="utf-8").read()
    r = c.post("/api/targets/import-spec",
               json={"name": "DemoPay (imported)", "spec_text": spec_text,
                     "auth": demopay["auth"],
                     "known_vulns": demopay["known_vulns"]})
    check("import OpenAPI spec (F1)", r.status_code == 200,
          f"status {r.status_code}: {r.text[:120]}")

    # 4. scope guard: refuse a scan without authorisation confirmation
    r = c.post("/api/scans", json={"target_id": demopay["id"], "authorized": False})
    check("scope guard blocks unauthorised scan (F2)", r.status_code == 400)

    # 5. run a scan on DemoPay
    r = c.post("/api/scans", json={"target_id": demopay["id"], "authorized": True})
    check("start scan", r.status_code == 200, r.text[:120])
    scan_id = r.json()["id"]

    status, scan = "pending", {}
    for _ in range(60):
        scan = c.get(f"/api/scans/{scan_id}").json()
        status = scan["status"]
        if status in ("done", "error"):
            break
        time.sleep(1)
    check("scan completes", status == "done", f'status={status} err={scan.get("error")}')

    print(f"    -> score {scan['score']}/100 grade {scan['grade']} "
          f"({scan['finding_count']} findings) {scan['severity_counts']}")
    check("score is grade D (~38)", scan["grade"] == "D" and 30 <= scan["score"] <= 45,
          f"score {scan['score']} grade {scan['grade']}")

    # 6. findings content
    findings = c.get(f"/api/scans/{scan_id}/findings").json()
    keys = {f["vuln_key"] for f in findings}
    check("BOLA on /accounts/{id} detected",
          "bola:/accounts/{account_id}" in keys)
    check("missing rate limit on /login detected", "rate_limit:/login" in keys)
    check("findings carry curl + recommendation (F6)",
          all(f["recommendation"] for f in findings if f["severity"] != "info")
          and any(f["curl"] for f in findings))

    # 7. AI-generated business-logic tests (F4)
    r = c.post(f"/api/scans/{scan_id}/ai-tests")
    check("run AI-generated tests (F4)", r.status_code == 200, r.text[:120])
    ai = c.get(f"/api/scans/{scan_id}/ai-tests").json()
    vuln = [t for t in ai if t["result"] == "vulnerable"]
    check("AI tests ran and found business-logic flaws",
          len(ai) >= 1 and len(vuln) >= 1,
          f"{len(ai)} tests, {len(vuln)} vulnerable, gen={ai[0]['generator'] if ai else '-'}")

    # 8. validation (F8)
    v = c.get(f"/api/scans/{scan_id}/validation").json()
    print(f"    -> detection {v['detection_rate']}% "
          f"({v['detected_count']}/{v['total_known']}), "
          f"false positives {v['false_positive_count']}")
    check("validation detection rate high (F8)",
          v["detection_rate"] >= 90 and v["false_positive_count"] == 0)

    # 9. reports (F7)
    r = c.get(f"/api/scans/{scan_id}/report.html")
    check("HTML report", r.status_code == 200 and "APISentry" in r.text)
    r = c.get(f"/api/scans/{scan_id}/report.pdf")
    check("PDF report", r.status_code == 200 and r.content[:4] == b"%PDF")

    print()
    if failures:
        print(f"SMOKE TEST FAILED: {len(failures)} check(s) failed: {failures}")
        sys.exit(1)
    print("SMOKE TEST PASSED - all checks green.")


if __name__ == "__main__":
    main()
