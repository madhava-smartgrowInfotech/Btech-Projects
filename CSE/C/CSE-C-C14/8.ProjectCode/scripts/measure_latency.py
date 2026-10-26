"""Measure response times of the running VeriVision AI API -> docs/metrics/latency.json.

Start the API first (python run.py, port 8414) on an otherwise idle machine, then:
    python scripts/measure_latency.py
Uses 127.0.0.1 (not localhost: on this Windows PC 'localhost' adds about 2 s per request through IPv6 fallback).
"""
import glob
import json
import os
import statistics
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.environ.get("API_URL", "http://127.0.0.1:8414")
N = int(os.environ.get("LATENCY_RUNS", "5"))


def timed(fn):
    t = time.perf_counter()
    r = fn()
    return time.perf_counter() - t, r


def stats(xs):
    return {"median": statistics.median(xs), "min": min(xs), "max": max(xs), "runs": len(xs)}


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "data", "cifake", "test", "fake", "*.png")))[:N]
    big = sorted(glob.glob(os.path.join(ROOT, "data", "xdomain", "test", "fake", "*.jpg")))[:N]
    out = {}
    out["health"] = stats([timed(lambda: requests.get(f"{API}/health", timeout=120))[0] for _ in range(N)])
    out["insights"] = stats([timed(lambda: requests.get(f"{API}/api/insights", timeout=120))[0] for _ in range(N)])
    tok = requests.post(f"{API}/api/auth/login", json={"email": "demo@verivision.ai", "password": "Demo@1234"}, timeout=60).json()["token"]
    hdr = {"Authorization": f"Bearer {tok}"}
    for label, fl in (("cifake_32px", files), ("photo_1024px", big)):
        if not fl:
            continue
        pred, ana = [], []
        for p in fl:
            raw = open(p, "rb").read()
            pred.append(timed(lambda: requests.post(f"{API}/api/predict", files={"image": (os.path.basename(p), raw)}, timeout=600))[0])
            ana.append(timed(lambda: requests.post(f"{API}/api/analyze", files={"image": (os.path.basename(p), raw)}, headers=hdr, timeout=900))[0])
        out[f"predict_{label}"] = stats(pred)
        out[f"analyze_{label}"] = stats(ana)
        print(label, "predict median %.1f s, analyze median %.1f s" % (statistics.median(pred), statistics.median(ana)), flush=True)
    # headline numbers used by the documents
    out["predict_s"] = out.get("predict_cifake_32px", {}).get("median")
    out["analyze_s"] = out.get("analyze_cifake_32px", {}).get("median")
    out["machine"] = {"cpu": "Intel Core i5-12500 (6 cores / 12 threads)", "ram_gb": 16, "gpu": "none (CPU inference)"}
    os.makedirs(os.path.join(ROOT, "docs", "metrics"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "docs", "metrics", "latency.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
