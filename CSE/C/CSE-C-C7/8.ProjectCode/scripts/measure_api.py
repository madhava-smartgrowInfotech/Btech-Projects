"""
Measures the running API (real model, real SQLite file, loopback) and writes experiments/api_latency.json.

    python scripts/measure_api.py [--base http://127.0.0.1:8407] [--rounds 30]

Uses 127.0.0.1 (not 'localhost': on this machine localhost adds ~2 s per call through an IPv6 fallback).
Creates one throw-away account; the account stays in the SQLite file like any other registered learner.
"""
import argparse
import json
import os
import statistics
import time
import uuid

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def timed(fn, n):
    ms = []
    for _ in range(n):
        t0 = time.perf_counter()
        r = fn()
        ms.append((time.perf_counter() - t0) * 1000)
        assert r.status_code == 200, (r.status_code, r.text[:200])
    ms.sort()
    return {"n": n, "mean_ms": round(statistics.mean(ms), 1), "median_ms": round(statistics.median(ms), 1),
            "p95_ms": round(ms[min(n - 1, int(0.95 * n))], 1), "max_ms": round(max(ms), 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8407")
    ap.add_argument("--rounds", type=int, default=30)
    a = ap.parse_args()
    s = requests.Session()
    email = f"latency_{uuid.uuid4().hex[:8]}@example.com"
    out = {"base": a.base, "rounds": a.rounds, "endpoints": {}}
    out["endpoints"]["POST /api/auth/register"] = timed(lambda: s.post(a.base + "/api/auth/register", json={"name": "Latency Probe", "email": email, "password": "secret123", "confirm_password": "secret123"}), 1)
    prof = {"education": "Bachelor's Degree", "skill_level": "Beginner", "interests": "python, data science, machine learning", "preferred_topics": "Machine Learning, Data Analysis",
            "learning_style": "Self-paced", "goals": "get a data job, build portfolio", "course_preferences": "hands-on labs, short videos", "weekly_hours": 6, "age_band": "25-34", "gender": "F"}
    out["endpoints"]["PUT /api/profile"] = timed(lambda: s.put(a.base + "/api/profile", json=prof), 5)
    for _ in range(3):  # warm-up: model bundle load, first TF-IDF fit
        s.get(a.base + "/api/recommendations?top_n=8")
    ids = [x["course"]["id"] for x in s.get(a.base + "/api/recommendations?top_n=8").json()["recommendations"]]
    for ev in ("open", "start", "quiz", "content", "complete"):
        s.post(a.base + "/api/interactions", json={"course_id": ids[0], "event_type": ev, "value": 1.0})
    out["endpoints"]["POST /api/auth/login"] = timed(lambda: requests.post(a.base + "/api/auth/login", json={"email": email, "password": "secret123"}), 10)
    for label, fn in (
        ("GET /api/health", lambda: requests.get(a.base + "/api/health")),
        ("GET /api/courses", lambda: s.get(a.base + "/api/courses")),
        ("GET /api/courses/{id}", lambda: s.get(a.base + f"/api/courses/{ids[0]}")),
        ("GET /api/recommendations?top_n=8", lambda: s.get(a.base + "/api/recommendations?top_n=8")),
        ("GET /api/recommendations?top_n=24", lambda: s.get(a.base + "/api/recommendations?top_n=24")),
        ("GET /api/learning-path", lambda: s.get(a.base + "/api/learning-path")),
        ("GET /api/insights", lambda: s.get(a.base + "/api/insights")),
        ("GET /api/activity", lambda: s.get(a.base + "/api/activity")),
        ("GET /api/metrics", lambda: s.get(a.base + "/api/metrics")),
    ):
        out["endpoints"][label] = timed(fn, a.rounds)
    out["interactions_logged_by_probe"] = 5
    json.dump(out, open(os.path.join(ROOT, "experiments", "api_latency.json"), "w"), indent=2)
    for k, v in out["endpoints"].items():
        print(f"{k:40s} mean {v['mean_ms']:8.1f} ms  p95 {v['p95_ms']:8.1f} ms  (n={v['n']})")


if __name__ == "__main__":
    main()
