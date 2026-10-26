"""API validation / edge-case checks for the documentation run. Writes docs/metrics/edge_tests.json.

    .venv\\Scripts\\python.exe scripts\\edge_tests.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

c = TestClient(app)
BASE = {"funding_total_usd": 2500000, "funding_rounds": 2, "industry_type": "Software", "state": "CA",
        "description": "A subscription analytics platform for small retailers.", "k": 50}

CASES = [
    ("valid request", "POST /predict", BASE, 200),
    ("k not in {10,20,30,50}", "POST /predict", {**BASE, "k": 7}, 422),
    ("negative funding", "POST /predict", {**BASE, "funding_total_usd": -5}, 422),
    ("funding above 1e10", "POST /predict", {**BASE, "funding_total_usd": 2e10}, 422),
    ("funding rounds above 20", "POST /predict", {**BASE, "funding_rounds": 25}, 422),
    ("relationships above 200", "POST /predict", {**BASE, "relationships": 500}, 422),
    ("description over 2000 characters", "POST /predict", {**BASE, "description": "x" * 2001}, 422),
    ("empty description (falls back to industry text)", "POST /predict", {**BASE, "description": ""}, 200),
    ("non-numeric funding", "POST /predict", {**BASE, "funding_total_usd": "abc"}, 422),
    ("unknown industry and state (handled by one-hot ignore)", "POST /predict", {**BASE, "industry_type": "Mining", "state": "ZZ"}, 200),
    ("zero funding, zero rounds", "POST /predict", {**BASE, "funding_total_usd": 0, "funding_rounds": 0}, 200),
    ("maximum values", "POST /predict", {**BASE, "funding_total_usd": 1e10, "funding_rounds": 20, "relationships": 200, "milestones": 50}, 200),
    ("empty body (all defaults)", "POST /predict", {}, 200),
]

out = []
for name, route, body, expect in CASES:
    t = time.perf_counter()
    r = c.post("/predict", json=body)
    ms = (time.perf_counter() - t) * 1000
    out.append({"case": name, "route": route, "expected": expect, "got": r.status_code, "pass": r.status_code == expect, "ms": round(ms, 1)})

# form route
r = c.post("/predict-form", data={"description": "", "k": 50})
out.append({"case": "form post with empty description", "route": "POST /predict-form", "expected": 400, "got": r.status_code, "pass": r.status_code == 400, "ms": 0})
r = c.post("/predict-form", data={"description": "A fintech lending tool for consumers.", "k": 99, "funding_total_usd": 900000})
out.append({"case": "form post with bad k (falls back to default)", "route": "POST /predict-form", "expected": 200, "got": r.status_code, "pass": r.status_code == 200, "ms": 0})
for p in ["/api/health", "/api/model-metrics", "/api/insights", "/api/config", "/api/feature-importance?top=5", "/", "/predict", "/performance", "/insights"]:
    r = c.get(p)
    out.append({"case": f"GET {p}", "route": f"GET {p}", "expected": 200, "got": r.status_code, "pass": r.status_code == 200, "ms": 0})
r = c.get("/api/auth/me")
out.append({"case": "auth/me without token", "route": "GET /api/auth/me", "expected": 401, "got": r.status_code, "pass": r.status_code == 401, "ms": 0})
r = c.post("/api/auth/login", json={"email": "demo@venturepulse.com", "password": "wrong"})
out.append({"case": "login with wrong password", "route": "POST /api/auth/login", "expected": 401, "got": r.status_code, "pass": r.status_code == 401, "ms": 0})
r = c.post("/api/auth/login", json={"email": "demo@venturepulse.com", "password": "Demo@1234"})
out.append({"case": "login with demo credentials", "route": "POST /api/auth/login", "expected": 200, "got": r.status_code, "pass": r.status_code == 200, "ms": 0})
tok = r.json().get("token", "") if r.status_code == 200 else ""
r = c.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
out.append({"case": "auth/me with token", "route": "GET /api/auth/me", "expected": 200, "got": r.status_code, "pass": r.status_code == 200, "ms": 0})
import base64
raw = base64.urlsafe_b64decode(tok.encode()).decode()
bad = base64.urlsafe_b64encode((raw[:-1] + ("0" if raw[-1] != "0" else "1")).encode()).decode()   # one signature character changed
r = c.get("/api/auth/me", headers={"Authorization": f"Bearer {bad}"})
out.append({"case": "auth/me with tampered token", "route": "GET /api/auth/me", "expected": 401, "got": r.status_code, "pass": r.status_code == 401, "ms": 0})

res = {"n": len(out), "passed": sum(o["pass"] for o in out), "cases": out}
d = ROOT / "docs" / "metrics"
d.mkdir(parents=True, exist_ok=True)
(d / "edge_tests.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
print(res["passed"], "/", res["n"])
for o in out:
    if not o["pass"]:
        print("FAIL", o)
