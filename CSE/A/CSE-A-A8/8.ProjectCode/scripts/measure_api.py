"""
measure_api.py - API latency of the LabLens backend on 127.0.0.1.

Copies the product modules to a temporary folder (so the real database is untouched), starts
uvicorn there on port 8397, seeds the five sample reports, then times each endpoint.
Writes experiments/lablens/api_latency.json.

    python -X utf8 scripts/measure_api.py
"""

import json
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
PORT = 8397
BASE = f"http://127.0.0.1:{PORT}"


def main():
    tmp = Path(tempfile.mkdtemp(prefix="lablens_api_"))
    for f in ROOT.glob("*.py"):
        shutil.copy(f, tmp / f.name)
    shutil.copytree(ROOT / "backend", tmp / "backend", ignore=shutil.ignore_patterns("__pycache__"))
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", str(PORT), "--host", "127.0.0.1", "--log-level", "warning"],
        cwd=tmp,
    )
    try:
        with httpx.Client(base_url=BASE, timeout=60) as c:
            for _ in range(60):
                try:
                    if c.get("/api/health").status_code == 200:
                        break
                except Exception:
                    time.sleep(0.5)
            tok = c.post("/api/auth/login", json={"email": "demo@lablens.com", "password": "Demo@1234"}).json()["token"]
            c.headers["Authorization"] = f"Bearer {tok}"
            t = time.perf_counter()
            seeded = c.post("/api/demo/seed").json()
            seed_s = time.perf_counter() - t
            ids = [r["report_id"] for r in seeded["created"]]
            sys.path.insert(0, str(ROOT / "backend"))
            sys.path.insert(0, str(ROOT))
            from backend.demo_data import render_pdf
            from datetime import datetime
            pdf = render_pdf(2, datetime(2026, 8, 2))
            calls = {
                "GET /api/health": lambda: c.get("/api/health"),
                "POST /api/auth/login": lambda: c.post("/api/auth/login", json={"email": "demo@lablens.com", "password": "Demo@1234"}),
                "GET /api/dashboard": lambda: c.get("/api/dashboard"),
                "GET /api/reports": lambda: c.get("/api/reports"),
                "GET /api/reports/{id}": lambda: c.get(f"/api/reports/{ids[2]}"),
                "GET /api/trends": lambda: c.get("/api/trends", params={"test": "Hemoglobin"}),
                "GET /api/compare": lambda: c.get("/api/compare", params={"a": ids[0], "b": ids[4]}),
                "GET /api/insights": lambda: c.get("/api/insights"),
                "POST /api/reports (PDF upload)": lambda: c.post("/api/reports", files={"file": ("r.pdf", pdf, "application/pdf")}),
            }
            out = {"seed_five_reports_s": round(seed_s, 2), "endpoints": {}}
            for name, fn in calls.items():
                n = 30 if "upload" in name else 100
                ts = []
                for _ in range(n):
                    t0 = time.perf_counter()
                    r = fn()
                    ts.append((time.perf_counter() - t0) * 1000)
                    assert r.status_code == 200, (name, r.status_code)
                out["endpoints"][name] = {"median_ms": round(statistics.median(ts), 1), "p95_ms": round(float(np.percentile(ts, 95)), 1),
                                          "max_ms": round(max(ts), 1), "n": n}
        (ROOT / "experiments" / "lablens" / "api_latency.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(json.dumps(out, indent=1))
    finally:
        server.terminate()


if __name__ == "__main__":
    main()
