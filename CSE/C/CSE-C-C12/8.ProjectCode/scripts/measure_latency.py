"""Measure HTTP latency of the running API on 127.0.0.1 (localhost adds ~2 s per call on this PC through IPv6 fallback).

    python scripts/measure_latency.py <label>        # writes docs/metrics/latency_<label>.json
Needs the backend on 8412. The label records which generator the backend was started with (e.g. fallback, flan-t5).
"""
import json
import os
import statistics as st
import sys
import time
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_data import LAY  # noqa: E402

API = os.getenv("CARELENS_API", "http://127.0.0.1:8412")
OUT = Path(__file__).resolve().parent.parent / "docs" / "metrics"


def call(op, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method, headers={"Content-Type": "application/json"} if data else {})
    t0 = time.perf_counter()
    with op.open(req, timeout=300) as r:
        raw = r.read()
    return (time.perf_counter() - t0) * 1000, json.loads(raw) if raw[:1] in (b"{", b"[") else raw


def summary(a):
    a = sorted(a)
    return {"n": len(a), "mean": round(st.mean(a), 1), "median": round(st.median(a), 1), "p95": round(a[int(0.95 * (len(a) - 1))], 1), "max": round(a[-1], 1), "min": round(a[0], 1)}


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
    out = {"label": label}
    out["health_ms"] = summary([call(op, "GET", "/api/health")[0] for _ in range(20)])
    out["login_ms"] = summary([call(op, "POST", "/api/auth/login", {"email": "demo@carelens.ai", "password": "Demo@1234"})[0] for _ in range(5)])
    cold, d = call(op, "POST", "/api/chat", {"query": "I have a runny nose and a sore throat"})
    out["chat_first_request_ms"] = round(cold, 1)
    times, gen = [], set()
    for _, q in LAY[:30]:
        ms, d = call(op, "POST", "/api/chat", {"query": q})
        times.append(ms)
        gen.add(d["generated_by"])
    out["chat_ms"] = summary(times)
    out["generated_by_seen"] = sorted(gen)
    out["history_list_ms"] = summary([call(op, "GET", "/api/history")[0] for _ in range(20)])
    ms, d = call(op, "GET", "/api/history")
    out["history_rows_at_end"] = len(d)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"latency_{label}.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
