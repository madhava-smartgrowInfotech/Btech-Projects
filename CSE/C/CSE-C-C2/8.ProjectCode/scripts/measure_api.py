"""Measure the running StoryVox API (documentation run). Writes experiments/api_timing/metrics.json.

Start the server first (isolated data dir recommended), then:
    python scripts/measure_api.py http://127.0.0.1:8402
Uses 127.0.0.1 on purpose: python http clients to 'localhost' add ~2 s per call on this machine (IPv6 fallback).
"""
from __future__ import annotations

import json
import statistics as st
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8402").rstrip("/")
OUT = Path(__file__).resolve().parent.parent / "experiments" / "api_timing"
IDEA = "A young inventor discovers a hidden library."


def call(method: str, path: str, body: dict | None = None, timeout: int = 1800):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            raw = res.read()
            code = res.status
    except urllib.error.HTTPError as exc:
        raw, code = exc.read(), exc.code
    dt = (time.perf_counter() - t0) * 1000
    try:
        payload = json.loads(raw) if raw[:1] in (b"{", b"[") else None
    except Exception:
        payload = None
    return code, dt, payload, len(raw)


def stats(ms: list[float]) -> dict:
    ms = sorted(ms)
    return {"n": len(ms), "median_ms": round(st.median(ms), 2), "p95_ms": round(ms[min(len(ms) - 1, int(0.95 * len(ms)))], 2),
            "min_ms": round(ms[0], 2), "max_ms": round(ms[-1], 2)}


res: dict = {"experiment": "api_timing", "base": BASE, "endpoints": {}, "generate": []}
for name, method, path, body in [
    ("GET /api/health", "GET", "/api/health", None),
    ("GET /api/languages", "GET", "/api/languages", None),
    ("GET /api/meta", "GET", "/api/meta", None),
    ("GET /api/stories", "GET", "/api/stories", None),
    ("GET /api/evaluations", "GET", "/api/evaluations", None),
    ("POST /api/stories/generate (empty prompt, 422)", "POST", "/api/stories/generate",
     {"prompt": "   ", "language_code": "en", "style": "Adventure", "length_option": "Short"}),
]:
    times, codes = [], set()
    for _ in range(30):
        code, dt, _, _ = call(method, path, body)
        times.append(dt)
        codes.add(code)
    res["endpoints"][name] = {**stats(times), "status_codes": sorted(codes)}
    print(name, res["endpoints"][name], flush=True)

# real generation requests, first one is cold (model loading inside the request)
runs = [("en", "Adventure", "Short"), ("en", "Bedtime", "Short"), ("hi", "Adventure", "Short"), ("fr", "Mystery", "Short"),
        ("de", "Fantasy", "Short"), ("es", "Funny", "Short"), ("en", "Adventure", "Medium")]
for i, (lang, style, length) in enumerate(runs):
    code, dt, payload, size = call("POST", "/api/stories/generate",
                                   {"prompt": IDEA, "language_code": lang, "style": style, "length_option": length, "synthesize": True})
    row = {"order": i + 1, "language": lang, "style": style, "length": length, "http_status": code, "request_s": round(dt / 1000, 2), "cold": i == 0}
    if payload and code == 200:
        a = payload.get("audio") or {}
        row.update(story_id=payload["id"], words=payload["word_count"], story_gen_s=payload["generation_time_seconds"],
                   audio_s=a.get("duration_seconds"), tts_s=a.get("synthesis_time_seconds"), rtf=a.get("rtf"), tts_model=a.get("tts_model"),
                   audio_id=a.get("id"))
    res["generate"].append(row)
    print(row, flush=True)
    (OUT).mkdir(parents=True, exist_ok=True)
    (OUT / "metrics.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

# audio download and history after real data exists
first = next((r for r in res["generate"] if r.get("audio_id")), None)
if first:
    dl = []
    for _ in range(10):
        code, dt, _, size = call("GET", f"/api/audio/{first['audio_id']}")
        dl.append(dt)
    res["endpoints"]["GET /api/audio/{id} (WAV download)"] = {**stats(dl), "bytes": size}
    lst = []
    for _ in range(20):
        code, dt, _, _ = call("GET", "/api/stories")
        lst.append(dt)
    res["endpoints"]["GET /api/stories (with data)"] = {**stats(lst)}
    code, dt, payload, _ = call("GET", "/api/stories")
    res["stories_in_db"] = len(payload or [])
try:
    import psutil

    for p in psutil.process_iter(["name", "cmdline", "memory_info"]):
        cmd = " ".join(p.info["cmdline"] or [])
        if "uvicorn" in cmd and "app.main" in cmd:
            res["server_rss_mb"] = round(p.info["memory_info"].rss / 1e6)
except Exception:
    pass
(OUT / "metrics.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
print("saved", OUT / "metrics.json")
