"""Measures response times of the API endpoints that do not call Gemini, on 127.0.0.1.

    python scripts\\measure_api.py [contract_id]

Needs the backend on 8106 and the demo user created by capture_screens.py (its contract id is read from
experiments/ui/state.json). 127.0.0.1 is used on purpose: 'localhost' adds ~2 s per call here (IPv6 fallback).
Writes experiments/api/metrics.json. Upload latency is not measured here: it is dominated by Gemini calls
and is taken from the real uploads in experiments/ui/state.json.
"""
from __future__ import annotations

import json
import statistics as st
import sys
import time
import uuid
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8106"
EMAIL, PASSWORD = "neha.legal@example.com", "clauseguard-demo-1"
N = 30


def timeit(fn, n=N):
    out = []
    for _ in range(n):
        t = time.perf_counter()
        r = fn()
        out.append((time.perf_counter() - t) * 1000)
    out.sort()
    return {"n": n, "status": r.status_code, "median_ms": round(st.median(out), 1), "p95_ms": round(out[int(0.95 * (len(out) - 1))], 1), "max_ms": round(out[-1], 1)}


def main():
    state = json.loads((ROOT / "experiments/ui/state.json").read_text())
    cid = int(sys.argv[1]) if len(sys.argv) > 1 else state["uploads"]["freelance"]["contract_id"]
    s = requests.Session()
    res = {}
    res["GET /api/health"] = timeit(lambda: s.get(f"{BASE}/api/health"))
    login = s.post(f"{BASE}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}).json()
    h = {"Authorization": f"Bearer {login['token']}"}
    res["POST /api/auth/login (bcrypt check)"] = timeit(lambda: s.post(f"{BASE}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}), n=10)
    res["POST /api/auth/register (bcrypt hash)"] = timeit(
        lambda: s.post(f"{BASE}/api/auth/register", json={"email": f"load-{uuid.uuid4().hex[:10]}@example.com", "password": "load-test-pw"}), n=10)
    res["GET /api/contracts"] = timeit(lambda: s.get(f"{BASE}/api/contracts", headers=h))
    res["GET /api/contracts/{id} (report)"] = timeit(lambda: s.get(f"{BASE}/api/contracts/{cid}", headers=h))
    rep = s.get(f"{BASE}/api/contracts/{cid}", headers=h).json()
    clause_id = next(c["id"] for c in rep["clauses"] if c["flag_count"])
    res["GET /api/contracts/{id}/clauses/{cid}"] = timeit(lambda: s.get(f"{BASE}/api/contracts/{cid}/clauses/{clause_id}", headers=h))
    res["GET /api/contracts/{id}/graph"] = timeit(lambda: s.get(f"{BASE}/api/contracts/{cid}/graph", headers=h))
    res["GET /api/eval/metrics"] = timeit(lambda: s.get(f"{BASE}/api/eval/metrics"))
    res["GET /api/contracts (no token -> 403)"] = timeit(lambda: s.get(f"{BASE}/api/contracts"), n=10)
    res["GET /api/contracts/999999 (404)"] = timeit(lambda: s.get(f"{BASE}/api/contracts/999999", headers=h), n=10)
    wrong = timeit(lambda: s.post(f"{BASE}/api/contracts/upload", headers=h, files={"file": ("a.txt", b"x", "text/plain")}), n=10)
    res["POST /api/contracts/upload wrong type (400)"] = wrong
    out = {"contract_id": cid, "clauses_in_contract": len(rep["clauses"]), "endpoints": res, "uploads": state["uploads"]}
    (ROOT / "experiments" / "api").mkdir(parents=True, exist_ok=True)
    (ROOT / "experiments" / "api" / "metrics.json").write_text(json.dumps(out, indent=2))
    for k, v in res.items():
        print(f"{k:55s} {v['status']}  median {v['median_ms']:7.1f} ms   p95 {v['p95_ms']:7.1f} ms")


if __name__ == "__main__":
    main()
