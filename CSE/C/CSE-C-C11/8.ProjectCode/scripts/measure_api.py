"""Measure FINJARVIS API response times on 127.0.0.1 against a throw-away database. Writes experiments/api_latency.json.

    .venv\\Scripts\\python.exe scripts\\measure_api.py

127.0.0.1 is used on purpose: on this Windows machine 'localhost' adds ~2 s per call (IPv6 fallback).
"""
from __future__ import annotations

import json
import os
import platform
import socket
import statistics
import subprocess
import sys
import tempfile
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPS = 30


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def timeit(fn, reps=REPS):
    ts = []
    for _ in range(reps):
        t0 = time.perf_counter()
        r = fn()
        ts.append((time.perf_counter() - t0) * 1000)
        assert r.status_code < 400, (r.status_code, r.text[:200])
    ts.sort()
    return {"n": reps, "median_ms": round(statistics.median(ts), 1), "p95_ms": round(ts[int(0.95 * (reps - 1))], 1),
            "min_ms": round(ts[0], 1), "max_ms": round(ts[-1], 1)}


def main() -> int:
    port = free_port()
    tmp = tempfile.mkdtemp(prefix="finjarvis_lat_")
    env = {**os.environ, "FINJARVIS_DB": os.path.join(tmp, "lat.db"), "PYTHONIOENCODING": "utf-8"}
    server = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", str(port)],
                              cwd=ROOT, env=env, stdout=open(os.path.join(tmp, "server.log"), "w"), stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}/api"
    try:
        for _ in range(90):
            try:
                if requests.get(f"{base}/health", timeout=1).ok:
                    break
            except requests.RequestException:
                time.sleep(1)
        s = requests.Session()
        t0 = time.perf_counter()
        r = s.post(f"{base}/auth/login", json={"identifier": "demo", "password": "Demo@1234"})
        login_first = (time.perf_counter() - t0) * 1000
        h = {"Authorization": f"Bearer {r.json()['token']}"}
        out: dict = {"host": "127.0.0.1", "reps": REPS, "login_first_ms": round(login_first, 1)}
        out["login (bcrypt verify)"] = timeit(lambda: s.post(f"{base}/auth/login", json={"identifier": "demo", "password": "Demo@1234"}))
        for name, path in [("GET /health", "/health"), ("GET /dashboard", "/dashboard"), ("GET /transactions", "/transactions"),
                           ("GET /analytics", "/analytics"), ("GET /budgets", "/budgets"), ("GET /goals", "/goals"),
                           ("GET /investments", "/investments"), ("GET /assistant/insights", "/assistant/insights"),
                           ("GET /notifications", "/notifications"), ("GET /meta", "/meta")]:
            out[name] = timeit(lambda p=path: s.get(f"{base}{p}", headers=h))
        out["POST /transactions/predict-category"] = timeit(lambda: s.post(f"{base}/transactions/predict-category", headers=h, json={"description": "Swiggy dinner order"}))
        out["POST /assistant/ask (analytics)"] = timeit(lambda: s.post(f"{base}/assistant/ask", headers=h, json={"question": "Where am I spending the most money?"}))
        out["POST /assistant/ask (health)"] = timeit(lambda: s.post(f"{base}/assistant/ask", headers=h, json={"question": "What is my financial health?"}))

        ids = []

        def add():
            r = s.post(f"{base}/transactions", headers=h, json={"date": "2026-10-20", "description": "Swiggy dinner order", "amount": 321,
                                                              "transaction_type": "expense", "category": "Auto-detect"})
            if r.ok:
                ids.append(r.json()["id"])
            return r

        out["POST /transactions (auto-categorise)"] = timeit(add)
        for i in ids:
            s.delete(f"{base}/transactions/{i}", headers=h)
        for kind in ("csv", "excel", "pdf"):
            out[f"GET /reports/{kind}"] = timeit(lambda k=kind: s.get(f"{base}/reports/{k}", headers=h), reps=10)
        csv = "date,description,amount,category,type\n" + "\n".join(f"2026-09-{(i % 28) + 1:02d},Swiggy order {i},{100 + i},,expense" for i in range(100))
        out["POST /transactions/import/preview (100 rows)"] = timeit(
            lambda: s.post(f"{base}/transactions/import/preview", headers=h, files={"file": ("p.csv", csv.encode(), "text/csv")}), reps=10)
        dash = s.get(f"{base}/dashboard", headers=h).json()
        out["demo_dashboard"] = {"health_score": dash["health"]["score"], "rating": dash["health"]["rating"],
                                 "metrics": dash["metrics"], "alerts": len(dash["alerts"])}
        out["machine"] = {"cpu": platform.processor(), "os": platform.platform(), "python": sys.version.split()[0]}
        with open(os.path.join(ROOT, "experiments", "api_latency.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        for k, v in out.items():
            if isinstance(v, dict) and "median_ms" in v:
                print(f"{k:50s} median {v['median_ms']:8.1f} ms  p95 {v['p95_ms']:8.1f} ms")
        return 0
    finally:
        server.terminate()


if __name__ == "__main__":
    sys.exit(main())
