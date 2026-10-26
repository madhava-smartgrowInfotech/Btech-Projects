"""Measure API latency against a running backend (default http://127.0.0.1:8410).

    .venv\\Scripts\\python.exe scripts\\measure_latency.py [base_url]

Uses 127.0.0.1 (not "localhost") because the IPv6 fallback adds ~2 s per request on this machine.
Writes evaluation/latency.json.
"""
from __future__ import annotations

import json
import platform
import statistics as st
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8410"
PAYLOAD = {"funding_total_usd": 2500000, "funding_rounds": 2, "relationships": 6, "milestones": 2,
           "has_VC": True, "has_roundA": True, "state": "CA", "industry_type": "Software",
           "description": "Cloud analytics platform for small businesses with subscription revenue and early enterprise pilots.",
           "k": 50}


def timed(fn, n):
    xs = []
    for _ in range(n):
        t = time.perf_counter(); r = fn(); xs.append((time.perf_counter() - t) * 1000)
        assert r.status_code == 200, r.text[:200]
    xs.sort()
    return {"n": n, "median_ms": round(st.median(xs), 1), "mean_ms": round(st.mean(xs), 1),
            "p95_ms": round(xs[int(0.95 * (n - 1))], 1), "max_ms": round(xs[-1], 1)}


def main() -> None:
    s = requests.Session()
    s.get(f"{BASE}/api/health")  # warm-up (loads model + embedder)
    s.post(f"{BASE}/predict", json=PAYLOAD)
    out = {"base": BASE, "python": platform.python_version(), "machine": platform.processor(),
           "health": timed(lambda: s.get(f"{BASE}/api/health"), 50),
           "model_metrics": timed(lambda: s.get(f"{BASE}/api/model-metrics"), 50),
           "insights": timed(lambda: s.get(f"{BASE}/api/insights"), 30)}
    for k in (10, 50):
        out[f"predict_k{k}"] = timed(lambda: s.post(f"{BASE}/predict", json={**PAYLOAD, "k": k}), 30)
    OUT = ROOT / "evaluation" / "latency.json"
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
