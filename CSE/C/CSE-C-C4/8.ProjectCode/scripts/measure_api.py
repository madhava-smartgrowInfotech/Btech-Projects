"""Measure QuantPulse API latency on 127.0.0.1 (localhost adds ~2 s per call here through an IPv6 fallback).

    python scripts/measure_api.py            # needs the API on port 8404; writes experiments/api_latency/metrics.json

The history and sentiment endpoints are measured with fewer calls because history re-downloads prices from Yahoo Finance on
every request and the first sentiment call loads FinBERT-tone.
"""
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "http://127.0.0.1:8404"
OUT = os.path.join(ROOT, "experiments", "api_latency")

# (name, path, calls)
ENDPOINTS = [
    ("health", "/api/health", 50),
    ("tickers", "/api/tickers", 50),
    ("metrics_all", "/api/metrics", 30),
    ("metrics_one", "/api/metrics/TSLA", 50),
    ("forecast_short", "/api/forecast/TSLA?horizon=short", 50),
    ("forecast_long", "/api/forecast/TSLA?horizon=long", 50),
    ("history_120d", "/api/history/TSLA?days=120", 8),
    ("sentiment", "/api/sentiment/TSLA", 8),
    ("error_invalid_ticker", "/api/forecast/T5LA", 30),
    ("error_unknown_ticker", "/api/forecast/ZZZZ", 30),
    ("frontend_index", "/", 30),
]


def call(path):
    t = time.perf_counter()
    try:
        with urllib.request.urlopen(API + path, timeout=300) as r:
            body = r.read()
            code = r.status
    except urllib.error.HTTPError as e:
        body, code = e.read(), e.code
    return (time.perf_counter() - t) * 1000, code, len(body)


def main():
    out = {"host": API, "endpoints": {}}
    for name, path, n in ENDPOINTS:
        first = call(path)
        ts = [call(path)[0] for _ in range(n)]
        ts.sort()
        out["endpoints"][name] = {"path": path, "status": first[1], "bytes": first[2], "n": n, "first_ms": first[0],
                                  "median_ms": statistics.median(ts), "p95_ms": ts[int(0.95 * (len(ts) - 1))], "max_ms": ts[-1], "mean_ms": statistics.fmean(ts)}
        e = out["endpoints"][name]
        print(f"{name:22s} {e['status']}  first {e['first_ms']:8.1f}  median {e['median_ms']:8.1f}  p95 {e['p95_ms']:8.1f} ms  {e['bytes']:>8d} B", flush=True)
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, "metrics.json"), "w"), indent=1)


if __name__ == "__main__":
    sys.exit(main())
