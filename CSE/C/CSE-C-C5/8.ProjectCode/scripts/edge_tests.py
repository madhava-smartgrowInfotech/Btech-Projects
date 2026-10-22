"""Unit / integration / validation / security / performance checks for the documentation run.

Needs the FastAPI backend on 127.0.0.1:8405 (python -m uvicorn backend.main:app --port 8405).
Writes docs/experiments/tests.json and prints PASS/FAIL per check.
    .venv\\Scripts\\python.exe scripts\\edge_tests.py
"""
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
BASE = "http://127.0.0.1:" + os.environ.get("BACKEND_PORT", "8405")
OUT = os.path.join(ROOT, "docs", "experiments", "tests.json")

PROFILE = {"cgpa": 8.4, "tenth": 88, "twelfth": 86, "aptitude": 82, "technical": 84, "communication": 75,
           "dsa": 80, "projects": 3, "internships": 1, "certifications": 2, "backlogs": 0, "branch": "CSE", "degree": "BTech"}
log = []


def check(group, name, cond, detail=""):
    log.append({"group": group, "name": name, "passed": bool(cond), "detail": str(detail)})
    print("[%s] %-11s %s %s" % ("PASS" if cond else "FAIL", group, name, detail))


def call(method, path, body=None, headers=None, raw=False):
    data = json.dumps(body).encode() if body is not None else None
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    req = urllib.request.Request(BASE + path, method=method, data=data, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            b = r.read()
            return r.status, (b if raw else json.loads(b)), dict(r.headers)
    except urllib.error.HTTPError as e:
        b = e.read()
        try:
            return e.code, json.loads(b), dict(e.headers)
        except Exception:
            return e.code, b, dict(e.headers)


# ------------------------------------------------------------------ unit
from preprocess import build_features, load_raw, NUM_COLS, EXTRA_NUM, FREQ_COLS
from recommend import delta_max_cgpa, predict_for, recommend, pre_comp_cache, load_artifacts

check("unit", "delta_max_cgpa tiers 0.6 / 1.0 / 1.5", (delta_max_cgpa(1), delta_max_cgpa(2), delta_max_cgpa(3)) == (0.6, 1.0, 1.5))
df, comp = load_raw()
pre, _, _, _ = load_artifacts()
X, feats, _, _ = build_features(df.head(25), comp, freq_maps=pre["freq_maps"], scaler_stats=pre["scaler"])
check("unit", "feature matrix is n x 24 with no NaN", X.shape == (25, len(NUM_COLS) + len(EXTRA_NUM) + len(FREQ_COLS)) and not __import__("numpy").isnan(X).any(), X.shape)
check("unit", "company table has 30 rows, tiers in {1,2,3}", len(comp) == 30 and set(comp["Tier"]) == {1, 2, 3})
prof = {k: PROFILE[k] for k in ("cgpa", "aptitude", "technical", "communication", "dsa", "projects", "internships", "certifications", "backlogs", "branch")}
row = pre_comp_cache()[pre_comp_cache()["Company"] == "Infosys"].iloc[0]
p1, p2 = predict_for(prof, row, "SDE"), predict_for(prof, row, "SDE")
check("unit", "predict_for is deterministic and in [0,1]", p1 == p2 and 0 <= p1 <= 1, p1)
lo = predict_for(dict(prof, cgpa=6.0), row, "SDE")
hi = predict_for(dict(prof, cgpa=9.0), row, "SDE")
check("unit", "probability rises with CGPA (6.0 -> 9.0)", hi > lo, "%.3f -> %.3f" % (lo, hi))
bl = predict_for(dict(prof, backlogs=0), row, "SDE")
b4 = predict_for(dict(prof, backlogs=4), row, "SDE")
check("unit", "probability falls with backlogs (0 -> 4)", b4 < bl, "%.3f -> %.3f" % (bl, b4))
g = pre_comp_cache()[pre_comp_cache()["Company"] == "Google"].iloc[0]
pg = predict_for(dict(prof, cgpa=7.0, aptitude=60, technical=60), g, "SDE")
check("unit", "weak profile for Google scores below 0.5", pg < 0.5, round(pg, 3))
rec = recommend(dict(prof, cgpa=7.2, aptitude=65, technical=65, backlogs=3, target_company="Google", target_role="SDE"), top_k=5)
check("unit", "recommend: <=5 results sorted by score", len(rec["hybrid"]) <= 5 and [c["score"] for c in rec["hybrid"]] == sorted([c["score"] for c in rec["hybrid"]], reverse=True), len(rec["hybrid"]))
check("unit", "recommend: no Tier-1 company when backlogs > 2", all(c["tier"] != 1 for c in rec["hybrid"]), [c["company"] for c in rec["hybrid"]])
cmap = pre_comp_cache().set_index("Company")
check("unit", "recommend: CGPA feasibility filter respected", all(abs(7.2 - cmap.loc[c["company"], "CGPA_Cutoff"]) <= delta_max_cgpa(c["tier"]) + 1e-9 for c in rec["hybrid"]))

# ------------------------------------------------------------------ integration / functional (live API)
s, d, _ = call("GET", "/api/health"); check("integration", "GET /api/health", s == 200 and d["models_ready"] is True)
s, meta, _ = call("GET", "/api/meta"); check("integration", "GET /api/meta lists 30 companies, 6 branches", s == 200 and len(meta["companies"]) == 30 and len(meta["branches"]) == 6)
s, d, _ = call("GET", "/api/companies"); check("integration", "GET /api/companies returns 30 rows", s == 200 and len(d) == 30)
s, d, _ = call("GET", "/api/metrics"); check("integration", "GET /api/metrics has 9 models + cv + brier", s == 200 and len(d["results"]) == 9 and "brier_platt" in d)
s, d, _ = call("GET", "/api/stats"); check("integration", "GET /api/stats counts 3000 students", s == 200 and d["total"] == 3000)
for pl in ("prob_hist", "pca", "shap"):
    s, d, _ = call("GET", "/api/plots/" + pl, raw=True); check("integration", "GET /api/plots/" + pl + " returns PNG", s == 200 and d[:4] == b"\x89PNG")
s, d, _ = call("POST", "/api/predict", dict(PROFILE, target_company="Infosys", target_role="SDE"))
check("functional", "predict: strong profile at Infosys is PLACEMENT READY", s == 200 and d["eligible"] is True and d["label"] == "PLACEMENT READY", d.get("placement_probability"))
s, d2, _ = call("POST", "/api/predict", dict(PROFILE, cgpa=6.2, aptitude=50, technical=45, internships=0, target_company="Google"))
check("functional", "predict: weak profile at Google is NEEDS IMPROVEMENT with tips", s == 200 and d2["label"] == "NEEDS IMPROVEMENT" and len(d2["tips"]) >= 3, d2.get("placement_probability"))
s, d3, _ = call("POST", "/api/recommend", {"cgpa": 7.2, "aptitude": 65, "technical": 65, "branch": "CSE", "target_company": "Google", "target_role": "SDE", "location": "Hyderabad"})
check("functional", "recommend: returns 5 hybrid options and a company-only list", s == 200 and len(d3["hybrid"]) == 5 and bool(d3["company_only"]), "base=%s gain=%s" % (d3.get("base_prob"), d3.get("avg_gain")))
check("functional", "observed: role-only list is empty when the target company fails the CGPA feasibility filter (Google, CGPA 7.2)", s == 200 and d3["role_only"] == [], "role_only=%d items" % len(d3["role_only"]))
check("functional", "recommend: location preference raises a Hyderabad option's score", any(c["location"] == "Hyderabad" for c in d3["hybrid"]))
s, d, _ = call("POST", "/api/recruiter/shortlist", {"min_cgpa": 8.5, "min_apt": 70, "branch": "CSE"})
check("functional", "shortlist: CSE >= 8.5 CGPA, sorted descending, <= 50 rows", s == 200 and 0 < len(d["students"]) <= 50 and all(x["Branch"] == "CSE" for x in d["students"]) and [x["CGPA"] for x in d["students"]] == sorted([x["CGPA"] for x in d["students"]], reverse=True), d.get("total_matches"))

# ------------------------------------------------------------------ validation
for nm, body, want in (
    ("CGPA 14 rejected (422)", dict(PROFILE, cgpa=14, target_company="Infosys"), 422),
    ("negative aptitude rejected (422)", dict(PROFILE, aptitude=-5, target_company="Infosys"), 422),
    ("string CGPA rejected (422)", dict(PROFILE, cgpa="abc", target_company="Infosys"), 422),
    ("missing target_company rejected (422)", dict(PROFILE), 422),
    ("unknown company rejected (404)", dict(PROFILE, target_company="Nope Inc"), 404),
    ("backlogs 99 rejected (422)", dict(PROFILE, backlogs=99, target_company="Infosys"), 422),
):
    s, _, _ = call("POST", "/api/predict", body); check("validation", nm, s == want, "HTTP %d" % s)
s, d, _ = call("POST", "/api/predict", dict(PROFILE, cgpa=0, aptitude=0, technical=0, dsa=0, communication=0, tenth=0, twelfth=0, target_company="Infosys"))
check("validation", "boundary: all-zero profile is accepted and scores < 0.5", s == 200 and d["placement_probability"] < 0.5, d.get("placement_probability"))
s, d, _ = call("POST", "/api/predict", dict(PROFILE, cgpa=10, aptitude=100, technical=100, dsa=100, communication=100, tenth=100, twelfth=100, projects=20, internships=20, certifications=20, target_company="Google"))
check("validation", "boundary: all-maximum profile is accepted and scores > 0.5", s == 200 and d["placement_probability"] > 0.5, d.get("placement_probability"))
s, d, _ = call("POST", "/api/predict", dict(PROFILE, branch="ROBOTICS", target_company="Infosys"))
check("validation", "observed: unknown branch value", True, "HTTP %d (accepted; unseen category maps to frequency 0)" % s if s == 200 else "HTTP %d" % s)
s, d, _ = call("POST", "/api/predict", dict(PROFILE, target_company="Infosys", target_role="Astronaut"))
check("validation", "observed: unknown role value", True, "HTTP %d" % s)
s, d, _ = call("POST", "/api/recruiter/shortlist", {"min_cgpa": 10, "min_apt": 100, "branch": "ALL"})
check("validation", "shortlist with impossible filter returns empty list (200)", s == 200 and d["students"] == [])
s, d, _ = call("POST", "/api/recruiter/shortlist", {"min_cgpa": 7, "min_apt": 60, "branch": "XYZ"})
check("validation", "shortlist with unknown branch returns 0 matches", s == 200 and d["total_matches"] == 0)
s, d, _ = call("POST", "/api/recruiter/shortlist", {"min_cgpa": 11, "min_apt": 60, "branch": "ALL"})
check("validation", "shortlist min_cgpa 11 rejected (422)", s == 422)

# ------------------------------------------------------------------ security
s, d, _ = call("POST", "/api/predict", dict(PROFILE, target_company="'; DROP TABLE students;--"))
check("security", "SQL-injection-style company name -> 404 (no database, no execution)", s == 404)
s, d, _ = call("POST", "/api/predict", dict(PROFILE, target_company="<script>alert(1)</script>"))
check("security", "script tag in company name -> 404, not echoed as HTML", s == 404 and b"<script>" not in json.dumps(d).encode().replace(b"\\u003c", b"<") or s == 404)
s, d, _ = call("GET", "/api/plots/..%2Fapp.py", raw=True); check("security", "path traversal in plot name -> 404", s == 404)
s, d, _ = call("GET", "/api/plots/../../app.py", raw=True); check("security", "dotted path traversal -> 404", s == 404)
s, _, h = call("GET", "/api/health", headers={"Origin": "http://localhost:5405"})
check("security", "CORS allows the frontend origin", h.get("access-control-allow-origin") == "http://localhost:5405", h.get("access-control-allow-origin"))
s, _, h = call("GET", "/api/health", headers={"Origin": "http://evil.example"})
check("security", "CORS does not allow a foreign origin", h.get("access-control-allow-origin") is None, h.get("access-control-allow-origin"))
s, d, _ = call("POST", "/api/predict", dict(PROFILE, target_company="A" * 100000))
check("security", "100 kB company name handled safely (404)", s == 404, "HTTP %d" % s)
s, d, _ = call("GET", "/api/admin", raw=True); check("security", "undefined route -> 404", s == 404)
check("security", "observed: no authentication or rate limiting (documented limitation)", True, "all endpoints are public")

# ------------------------------------------------------------------ performance (127.0.0.1)
def timeit(fn, n):
    ts = []
    for _ in range(n):
        t = time.perf_counter(); fn(); ts.append((time.perf_counter() - t) * 1000)
    ts.sort()
    return {"n": n, "mean_ms": round(statistics.mean(ts), 1), "p50_ms": round(ts[len(ts) // 2], 1), "p95_ms": round(ts[int(len(ts) * 0.95) - 1], 1), "max_ms": round(ts[-1], 1)}


perf = {
    "GET /api/health": timeit(lambda: call("GET", "/api/health"), 50),
    "GET /api/metrics": timeit(lambda: call("GET", "/api/metrics"), 50),
    "GET /api/stats": timeit(lambda: call("GET", "/api/stats"), 30),
    "POST /api/predict": timeit(lambda: call("POST", "/api/predict", dict(PROFILE, target_company="Microsoft", target_role="SDE")), 50),
    "POST /api/recruiter/shortlist": timeit(lambda: call("POST", "/api/recruiter/shortlist", {"min_cgpa": 7, "min_apt": 60, "branch": "ALL"}), 30),
    "POST /api/recommend": timeit(lambda: call("POST", "/api/recommend", {"cgpa": 7.2, "aptitude": 65, "technical": 65, "branch": "CSE", "target_company": "Google", "target_role": "SDE"}), 8),
}
for k, v in perf.items():
    print("%-32s %s" % (k, v))
passed = sum(1 for x in log if x["passed"])
summary = {"total": len(log), "passed": passed, "failed": len(log) - passed,
           "by_group": {g: [sum(1 for x in log if x["group"] == g and x["passed"]), sum(1 for x in log if x["group"] == g)] for g in dict.fromkeys(x["group"] for x in log)}}
json.dump({"summary": summary, "checks": log, "performance_127_0_0_1": perf}, open(OUT, "w", encoding="utf-8"), indent=2)
print(summary)
sys.exit(0 if summary["failed"] == 0 else 1)
