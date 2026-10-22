"""Smoke test for the FastAPI layer: exercises every endpoint the React frontend calls.

Usage (backend running on BACKEND_PORT, default 8405):
    python scripts/smoke_test.py            # against the running server
    python scripts/smoke_test.py --inprocess  # no server needed (uses FastAPI TestClient)
"""
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = os.environ.get("BACKEND_PORT", "8405")
BASE = f"http://localhost:{PORT}"

PROFILE = {"cgpa": 8.4, "tenth": 88, "twelfth": 86, "aptitude": 82, "technical": 84, "communication": 75,
           "dsa": 80, "projects": 3, "internships": 1, "certifications": 2, "backlogs": 0, "branch": "CSE", "degree": "BTech"}

failures = []


def check(name, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")
    if not cond:
        failures.append(name)


if "--inprocess" in sys.argv:
    sys.path.insert(0, ROOT)
    from fastapi.testclient import TestClient
    from backend.main import app
    client = TestClient(app)

    def call(method, path, body=None):
        r = client.request(method, path, json=body)
        return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else r.content)
else:
    def call(method, path, body=None):
        req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
                return r.status, (json.loads(raw) if r.headers.get_content_type() == "application/json" else raw)
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")


s, d = call("GET", "/api/health")
check("health", s == 200 and d["models_ready"] is True, str(d))

s, meta = call("GET", "/api/meta")
check("meta", s == 200 and "CSE" in meta["branches"] and len(meta["companies"]) >= 30, f"{len(meta['companies'])} companies")

s, comps = call("GET", "/api/companies")
check("companies", s == 200 and len(comps) == len(meta["companies"]) and "CGPA_Cutoff" in comps[0])

s, m = call("GET", "/api/metrics")
check("metrics", s == 200 and "hybrid_xgb_knn" in m["results"] and "cv_xgb_9fold" in m)

s, st = call("GET", "/api/stats")
check("stats", s == 200 and st["total"] > 0 and 0 < st["placed_rate"] < 1 and len(st["by_branch"]) == 6)

for plot in ("prob_hist", "pca", "shap"):
    s, raw = call("GET", f"/api/plots/{plot}")
    check(f"plot {plot}", s == 200 and raw[:4] == b"\x89PNG")
s, _ = call("GET", "/api/plots/nope")
check("plot unknown -> 404", s == 404)

s, p = call("POST", "/api/predict", {**PROFILE, "target_company": "Infosys", "target_role": "SDE"})
check("predict", s == 200 and 0 <= p["placement_probability"] <= 1 and p["eligible"] == (p["placement_probability"] >= 0.5) and p["tips"], f"p={p.get('placement_probability')}")
s, _ = call("POST", "/api/predict", {**PROFILE, "target_company": "Nope Inc"})
check("predict unknown company -> 404", s == 404)
s, _ = call("POST", "/api/predict", {**PROFILE, "cgpa": 14, "target_company": "Infosys"})
check("predict invalid cgpa -> 422", s == 422)

s, r = call("POST", "/api/recommend", {"cgpa": 7.2, "aptitude": 65, "technical": 65, "branch": "CSE", "target_company": "Google", "target_role": "SDE", "location": "Hyderabad"})
check("recommend", s == 200 and len(r["hybrid"]) == 5 and {"base_prob", "avg_gain", "match_rate", "company_only", "role_only"} <= set(r), f"base={r.get('base_prob')}")

s, sl = call("POST", "/api/recruiter/shortlist", {"min_cgpa": 8.5, "min_apt": 70, "branch": "CSE"})
check("shortlist", s == 200 and sl["total_matches"] >= len(sl["students"]) > 0 and all(x["Branch"] == "CSE" and x["CGPA"] >= 8.5 for x in sl["students"]), f"{sl.get('total_matches')} matches")
s, sl = call("POST", "/api/recruiter/shortlist", {"min_cgpa": 10, "min_apt": 100, "branch": "ALL"})
check("shortlist empty", s == 200 and sl["total_matches"] == 0 and sl["students"] == [])

print(f"\n{'ALL PASSED' if not failures else 'FAILED: ' + ', '.join(failures)}")
sys.exit(1 if failures else 0)
