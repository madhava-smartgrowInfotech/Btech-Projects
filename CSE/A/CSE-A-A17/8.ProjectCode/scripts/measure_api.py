"""
measure_api.py
---------------
Times every stage of the TrendCast pipeline through the running API (use 127.0.0.1, not "localhost": on this
machine localhost adds ~2 s per request through an IPv6 fallback) and writes experiments/api_timing/metrics.json.

    python scripts/measure_api.py [--base http://127.0.0.1:8317] [--data data/real_hm] [--repeats 20]
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent


def timed(fn):
    t0 = time.perf_counter()
    r = fn()
    return time.perf_counter() - t0, r


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8317")
    ap.add_argument("--data", default=str(ROOT / "data" / "real_hm"))
    ap.add_argument("--repeats", type=int, default=20)
    a = ap.parse_args()
    api, data = a.base.rstrip("/") + "/api", Path(a.data)
    out: dict = {"stages_seconds": {}, "latency_ms": {}}

    def stage(name, fn):
        s, r = timed(fn)
        assert r.ok, (name, r.status_code, r.text[:200])
        out["stages_seconds"][name] = round(s, 3)
        print(f"{name:28s} {s:8.2f} s")
        return r

    with open(data / "transactions_train.csv", "rb") as t, open(data / "articles.csv", "rb") as ar:
        stage("upload+clean+merge (684k rows)", lambda: requests.post(f"{api}/data/upload", files={"transactions": t, "articles": ar}, data={"sample_rows": 0}, timeout=600))
    stage("explore (aggregate daily)", lambda: requests.get(f"{api}/explore", timeout=300))
    stage("build features", lambda: requests.post(f"{api}/features/build", timeout=600))
    stage("moving-average baseline", lambda: requests.post(f"{api}/training/baseline", json={"train_fraction": 0.8}, timeout=300))
    stage("train XGBoost (default)", lambda: requests.post(f"{api}/training/xgboost", json={"train_fraction": 0.8, "tune": False}, timeout=600))
    stage("train XGBoost (tuned)", lambda: requests.post(f"{api}/training/xgboost", json={"train_fraction": 0.8, "tune": True}, timeout=900))
    stage("domain adaptation run", lambda: requests.post(f"{api}/domain/run", json={"domain_col": "sales_channel_id", "source": 2, "target": 1}, timeout=900))
    # leave the retrained default model in place for the latency loop
    stage("train XGBoost (default, again)", lambda: requests.post(f"{api}/training/xgboost", json={"train_fraction": 0.8, "tune": False}, timeout=600))
    arts = requests.get(f"{api}/forecast/articles", timeout=60).json()["articles"]
    aid = arts[0]["id"]

    def loop(name, fn, n):
        ms = []
        for _ in range(n):
            s, r = timed(fn)
            assert r.ok, (name, r.status_code)
            ms.append(s * 1000)
        ms.sort()
        out["latency_ms"][name] = {"n": n, "median": round(statistics.median(ms), 1), "p95": round(ms[int(0.95 * (n - 1))], 1), "max": round(ms[-1], 1)}
        print(f"{name:28s} median {out['latency_ms'][name]['median']:8.1f} ms  p95 {out['latency_ms'][name]['p95']:8.1f} ms")

    loop("GET /api/health", lambda: requests.get(f"{api}/health", timeout=30), a.repeats)
    loop("GET /api/state", lambda: requests.get(f"{api}/state", timeout=30), a.repeats)
    loop("GET /api/evaluation", lambda: requests.get(f"{api}/evaluation", timeout=60), a.repeats)
    for h in (7, 14, 30):
        loop(f"POST /api/forecast ({h} d)", lambda h=h: requests.post(f"{api}/forecast", json={"article_id": aid, "horizon": h}, timeout=120), a.repeats)
    out["note"] = "Measured on 127.0.0.1 with other jobs running on the same machine; real H&M subset of 684,392 transaction rows."
    d = ROOT / "experiments" / "api_timing"
    d.mkdir(parents=True, exist_ok=True)
    (d / "metrics.json").write_text(json.dumps(out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
