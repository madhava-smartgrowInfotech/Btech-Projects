"""End-to-end smoke test of the HubOptima API (the layer the React frontend uses).

    python scripts/smoke_test.py                        # in-process (FastAPI TestClient)
    python scripts/smoke_test.py --url http://127.0.0.1:8104 [--frontend http://localhost:5104]

Read-only except for the optimisation calls, which do not write files. Use --jobs to also run a
2-month rolling re-optimisation in the background (rewrites results/rolling.json).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class Http:
    def __init__(self, base):
        self.base = base.rstrip("/")

    def _req(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"} if data else {})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.status, json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"null")

    def get(self, path):
        return self._req("GET", path)

    def post(self, path, body):
        return self._req("POST", path, body)


class Local:
    def __init__(self):
        from fastapi.testclient import TestClient
        from backend.main import app
        self.c = TestClient(app)

    def get(self, path):
        r = self.c.get(path)
        return r.status_code, r.json()

    def post(self, path, body):
        r = self.c.post(path, json=body)
        return r.status_code, r.json()


def check(name, cond, detail=""):
    print(f"  {'ok ' if cond else 'FAIL'}  {name}{('  - ' + detail) if detail else ''}")
    if not cond:
        raise SystemExit(f"smoke test failed at: {name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--frontend")
    ap.add_argument("--jobs", action="store_true")
    a = ap.parse_args()
    api = Http(a.url) if a.url else Local()
    print(f"HubOptima smoke test against {a.url or 'in-process app'}")

    s, h = api.get("/api/health")
    check("health", s == 200 and h["status"] == "ok", h.get("solver", ""))

    s, sm = api.get("/api/summary")
    ds = sm["dataset"]
    check("summary: dataset", s == 200 and ds["regions"] >= 30 and ds["periods"] >= 24, f"{ds['regions']} regions x {ds['periods']} months")
    check("summary: forecaster trained", sm["forecaster"]["trained"])

    s, rg = api.get("/api/regions")
    check("regions with coordinates", s == 200 and len(rg["regions"]) == ds["regions"] and "lat" in rg["regions"][0])

    s, op = api.get("/api/options")
    check("options", s == 200 and op["plan_periods"][0] == op["next_period"] and op["defaults"]["n_hubs"] > 0)

    s, fc = api.get("/api/forecast")
    check("forecast (original contract)", s == 200 and fc["total"] > 0 and len(fc["regions"]) == ds["regions"] and "metrics" in fc,
          f"{fc['period']}: {fc['total']:,} orders")

    s, fm = api.get("/api/forecast/metrics")
    check("forecast metrics", s == 200 and fm["random_forest"]["mape"] > 0 and fm["last_period_detail"][0].get("city"))

    s, cmp = api.get("/api/compare")
    check("compare (original contract)", s == 200 and (not cmp or "proposed" in cmp["methods"]))
    s, sc = api.get("/api/scalability")
    check("scalability", s == 200 and isinstance(sc, list))
    s, ro = api.get("/api/rolling")
    check("rolling (original contract)", s == 200 and (not ro or "timeline" in ro))

    t0 = time.time()
    s, pl = api.post("/api/optimize", {"n_hubs": 4, "period": "2025-12"})
    check("optimize: matheuristic on a past month", s == 200 and not pl.get("error") and pl["kpi"]["n_hubs"] <= 4 and pl["realized"] is True,
          f"{', '.join(pl['kpi']['hub_cities'])} in {time.time() - t0:.1f}s")
    check("optimize: allocation covers every region", len(pl["kpi"]["assignment"]) == ds["regions"] and len(pl["demand_used"]) == ds["regions"])

    s, pl2 = api.post("/api/optimize", {"n_hubs": 6})
    check("optimize: next month on forecast", s == 200 and pl2["realized"] is False and pl2["period"] == op["next_period"])

    if h["has_pulp"]:
        s, ex = api.post("/api/optimize", {"n_hubs": 6, "period": "2025-10", "method": "exact", "time_limit": 30})
        check("optimize: exact MIP", s == 200 and not ex.get("error") and ex["sol"]["status"] in ("Optimal", "Not Solved", "Feasible"),
              ex["sol"]["status"])

    s, bad = api.post("/api/optimize", {"n_hubs": 1, "sla_hours": 5, "sla_hard": True, "period": "2025-12"})
    check("optimize: hard-SLA edge case answers cleanly (plan or error, valid JSON)", s == 200 and (bad.get("error") or bad.get("kpi")),
          bad.get("error") or f"reliability {bad['kpi']['reliability_sla']}")
    s, _ = api.post("/api/optimize", {"n_hubs": 0})
    check("optimize: validation rejects n_hubs=0", s == 422)
    s, _ = api.post("/api/optimize", {"period": "1999-01"})
    check("optimize: unknown month rejected", s == 400)

    s, j = api.get("/api/jobs")
    check("jobs status", s == 200 and set(j) >= {"compare", "rolling"})

    if a.jobs:
        s, r = api.post("/api/rolling/run", {"n_months": 2})
        check("rolling job started", s == 200 and r["started"] == "rolling")
        for _ in range(120):
            time.sleep(1)
            _, j = api.get("/api/jobs")
            if not j["rolling"]["running"]:
                break
        check("rolling job finished", not j["rolling"]["running"] and not j["rolling"]["error"])
        _, ro = api.get("/api/rolling")
        check("rolling results written", len(ro["timeline"]) == 2)

    if a.frontend:
        with urllib.request.urlopen(a.frontend, timeout=10) as r:
            check("frontend serves index.html", r.status == 200 and b'id="root"' in r.read())
        with urllib.request.urlopen(a.frontend.rstrip("/") + "/api/health", timeout=10) as r:
            check("frontend proxies /api to the backend", r.status == 200)

    print("all smoke checks passed")


if __name__ == "__main__":
    main()
