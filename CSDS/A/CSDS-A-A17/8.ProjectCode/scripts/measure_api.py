"""Measure response times of the running API on 127.0.0.1 (not 'localhost': IPv6 fallback adds ~2 s per call on this machine).

    venv\\Scripts\\python scripts/measure_api.py   -> experiments/api_latency/metrics.json
"""
from __future__ import annotations

import platform
import statistics
import time

import httpx

from exp_common import PROJECT, save

API = "http://127.0.0.1:8000/api"
PHOTOS = PROJECT / "docs" / "sample_inputs"
N = 30


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))]


def timed(fn, n=N):
    out = []
    for _ in range(n):
        t = time.perf_counter()
        r = fn()
        out.append((time.perf_counter() - t) * 1000)
        assert r.status_code == 200, (r.status_code, r.text[:200])
    return {"n": n, "median_ms": round(statistics.median(out), 1), "p95_ms": round(pct(out, 95), 1), "max_ms": round(max(out), 1), "mean_ms": round(statistics.mean(out), 1)}


def main():
    c = httpx.Client(timeout=120)
    tok = lambda e: {"Authorization": "Bearer " + c.post(f"{API}/auth/login", json={"email": e, "password": "cropsight123"}).json()["access_token"]}
    f, b, a = tok("farmer@cropsight.dev"), tok("buyer1@cropsight.dev"), tok("admin@cropsight.dev")
    photo = sorted(PHOTOS.glob("tomato_*.jpg"))[0]
    img = photo.read_bytes()
    lid = c.get(f"{API}/crops/mine", headers=f).json()[0]["id"]
    res = {
        "environment": {"cpu": platform.processor(), "python": platform.python_version(), "os": platform.platform(), "note": "API and client on the same machine over 127.0.0.1; other jobs were running on the machine"},
        "photo_bytes": len(img),
        "login": timed(lambda: c.post(f"{API}/auth/login", json={"email": "farmer@cropsight.dev", "password": "cropsight123"})),
        "health": timed(lambda: c.get(f"{API}/health")),
        "upload_and_grade": timed(lambda: c.post(f"{API}/crops/upload", headers=f, data={"crop_type": "Tomato", "region": "Sunridge Valley", "quantity_kg": 100}, files={"image": ("t.jpg", img, "image/jpeg")}), n=20),
        "price_predict": timed(lambda: c.post(f"{API}/prices/predict", headers=f, json={"crop_type": "Tomato", "region": "Sunridge Valley", "grade": "B"})),
        "delivery_recommend": timed(lambda: c.get(f"{API}/delivery/{lid}/recommend", headers=f)),
        "marketplace_listings": timed(lambda: c.get(f"{API}/marketplace/listings", headers=b)),
        "admin_overview": timed(lambda: c.get(f"{API}/admin/overview", headers=a)),
        "admin_model_insights": timed(lambda: c.get(f"{API}/admin/model-insights", headers=a)),
    }
    save("api_latency", res)
    for k, v in res.items():
        if isinstance(v, dict) and "median_ms" in v:
            print(k, v)


if __name__ == "__main__":
    main()
