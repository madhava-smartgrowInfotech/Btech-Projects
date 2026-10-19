"""
Measures the running API (real model, real files, real database) and records the sample predictions.

    python scripts/measure_api.py [--base http://localhost:8312] [--rounds 10]

Writes experiments/api_latency.json and experiments/sample_predictions.json, then deletes the scans it created.
Requires the API to be running (run.bat or uvicorn).
"""

import argparse
import json
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smoke_test import DEMO, SAMPLES, Client  # noqa: E402

SAMPLE_META = [
    ("normal_pa.jpg", "Normal PA chest radiograph"),
    ("lobar_pneumonia.jpg", "X-ray of lobar pneumonia"),
    ("influenza_pa.jpg", "Chest radiograph in influenza"),
    ("bocavirus_pneumonia.jpg", "Human bocavirus 1 pneumonia"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8312")
    ap.add_argument("--rounds", type=int, default=10)
    a = ap.parse_args()
    c = Client(a.base)
    st, _ = c.json("POST", "/api/auth/login", DEMO)
    assert st == 200, f"login failed: {st}"
    health = c.call("GET", "/api/health")[1]
    print("health", health)

    created, times, samples = [], [], []
    for r in range(a.rounds):
        for fn, caption in SAMPLE_META:
            with open(os.path.join(SAMPLES, fn), "rb") as f:
                data = f.read()
            t0 = time.perf_counter()
            st, rec = c.upload(fn, data)
            dt = (time.perf_counter() - t0) * 1000
            assert st == 201, (st, rec)
            created.append(rec["id"])
            if r > 0:  # the first round warms the model and the file cache
                times.append(dt)
            if r == 1:
                samples.append({"file": fn, "caption": caption, "prediction": rec["prediction"], "confidence": rec["confidence"],
                                "probabilities": rec["probabilities"], "ms": dt})
    hist, rec_t = [], []
    for _ in range(30):
        t0 = time.perf_counter(); c.call("GET", "/api/predictions"); hist.append((time.perf_counter() - t0) * 1000)
    for _ in range(30):
        t0 = time.perf_counter(); c.call("GET", f"/api/predictions/{created[-1]}"); rec_t.append((time.perf_counter() - t0) * 1000)

    times_sorted = sorted(times)
    p95 = times_sorted[min(len(times_sorted) - 1, int(0.95 * len(times_sorted)))]
    res = {
        "base": a.base, "requests": len(times), "warmup_requests_excluded": len(SAMPLE_META),
        "mean_ms": statistics.mean(times), "median_ms": statistics.median(times), "p95_ms": p95, "max_ms": max(times), "min_ms": min(times),
        "history_calls": len(hist), "history_mean_ms": statistics.mean(hist), "record_calls": len(rec_t), "record_mean_ms": statistics.mean(rec_t),
        "model_demo_mode": health.get("demo_mode"),
    }
    json.dump(res, open(os.path.join(ROOT, "experiments", "api_latency.json"), "w"), indent=2)
    json.dump(samples, open(os.path.join(ROOT, "experiments", "sample_predictions.json"), "w"), indent=2)
    for i in created:
        c.call("DELETE", f"/api/predictions/{i}")
    print(json.dumps(res, indent=1))
    for s in samples:
        print(s["file"], s["prediction"], f"{s['confidence']:.3f}")


if __name__ == "__main__":
    main()
