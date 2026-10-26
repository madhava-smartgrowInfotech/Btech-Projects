"""Measure FlowSense API response times against a running backend (use 127.0.0.1, not localhost).

Usage: python scripts/measure_api.py [http://127.0.0.1:8310]   ->  experiments/api_latency/metrics.json
"""
from __future__ import annotations

import json
import statistics as st
import sys
import time
import urllib.request
from pathlib import Path

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8310").rstrip("/")
TOKEN = None


def call(method, path, body=None):
    h = {"Content-Type": "application/json"}
    if TOKEN:
        h["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(BASE + path, data=None if body is None else json.dumps(body).encode(), method=method, headers=h)
    t = time.perf_counter()
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.loads(r.read())
    return (time.perf_counter() - t) * 1000, data


def bench(name, method, path, body=None, n=20):
    ts = [call(method, path, body)[0] for _ in range(n)]
    ts.sort()
    return dict(endpoint=f"{name}: {method} {path}", n=n, mean_ms=st.mean(ts), median_ms=st.median(ts), p95_ms=ts[min(n - 1, int(0.95 * n))], max_ms=ts[-1])


if __name__ == "__main__":
    for _ in range(90):
        if call("GET", "/api/health")[1]["predictor_ready"]:
            break
        time.sleep(1)
    global_token = call("POST", "/api/auth/login", call("GET", "/api/auth/demo")[1])[1]["token"]
    TOKEN = global_token
    call("POST", "/api/live/reset")
    rows = [bench("health", "GET", "/api/health"),
            bench("login", "POST", "/api/auth/login", call("GET", "/api/auth/demo")[1]),
            bench("meta", "GET", "/api/meta"),
            bench("pulse", "GET", "/api/public/pulse"),
            bench("live snapshot", "GET", "/api/live"),
            bench("live step 2 s", "POST", "/api/live/step", {"seconds": 2}),
            bench("live step 60 s", "POST", "/api/live/step", {"seconds": 60}, n=10),
            bench("live step 300 s", "POST", "/api/live/step", {"seconds": 300}, n=5),
            bench("prediction", "GET", "/api/prediction"),
            bench("prediction live", "GET", "/api/prediction/live"),
            bench("violations", "GET", "/api/violations"),
            bench("vision synthetic", "GET", "/api/vision/synthetic?vehicles=9&ambulance=true&flash=A&seed=3"),
            bench("vision sample (YOLOv8)", "GET", "/api/vision/sample?conf=0.3", n=10)]
    t0 = time.perf_counter()
    call("POST", "/api/benchmark", {"grid": "2x2", "seconds": 1800, "demand": 1.35, "seeds": 3, "start_hour": 8, "use_ml": True})
    rows.append(dict(endpoint="POST /api/benchmark (4 ctrl x 3 seeds x 1800 s, first call)", n=1,
                     mean_ms=(time.perf_counter() - t0) * 1000))
    t0 = time.perf_counter()
    call("POST", "/api/benchmark", {"grid": "2x2", "seconds": 1800, "demand": 1.35, "seeds": 3, "start_hour": 8, "use_ml": True})
    rows.append(dict(endpoint="POST /api/benchmark (cached)", n=1, mean_ms=(time.perf_counter() - t0) * 1000))
    t0 = time.perf_counter()
    call("POST", "/api/benchmark/sweep", {"grid": "2x2", "use_ml": True})
    rows.append(dict(endpoint="POST /api/benchmark/sweep (5 demand levels x 4 ctrl)", n=1, mean_ms=(time.perf_counter() - t0) * 1000))
    out = Path(__file__).resolve().parent.parent / "experiments" / "api_latency"
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(dict(base=BASE, results=rows), indent=2), encoding="utf-8")
    for r in rows:
        print(f"{r['endpoint']:70s} mean {r['mean_ms']:8.1f} ms" + (f"  p95 {r['p95_ms']:.1f}" if 'p95_ms' in r else ""))
