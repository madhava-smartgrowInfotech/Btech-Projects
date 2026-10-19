"""QuantPulse smoke test: every API endpoint the frontend uses, plus the website itself.

Usage (with run.bat already running):
    python scripts/smoke_test.py            # API on 8404, website on 5404
    python scripts/smoke_test.py --api-only
Ports come from the project .env (BACKEND_PORT / FRONTEND_PORT).
"""
from __future__ import annotations
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def env_port(name: str, default: int) -> int:
    try:
        for line in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
            if line.startswith(name + "="):
                return int(line.split("=", 1)[1].strip())
    except (OSError, ValueError):
        pass
    return default


API = f"http://127.0.0.1:{env_port('BACKEND_PORT', 8404)}"
WEB = f"http://localhost:{env_port('FRONTEND_PORT', 5404)}"
failures: list[str] = []


def get(url: str, timeout: int = 240):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read(), r.headers.get("content-type", "")
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers.get("content-type", "")


def check(name: str, ok: bool, detail: str = ""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def jget(path: str):
    code, body, _ = get(API + path)
    try:
        return code, json.loads(body)
    except ValueError:
        return code, None


def next_bdays(iso: str, n: int):
    d = date.fromisoformat(iso)
    out = []
    while len(out) < n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            out.append(d.isoformat())
    return out


def main():
    api_only = "--api-only" in sys.argv

    code, h = jget("/api/health")
    check("health ok and trained", code == 200 and h and h["status"] == "ok" and h["trained"] is True, str(h))
    tickers_h = h["tickers"] if h else []

    code, t = jget("/api/tickers")
    rows = t["tickers"] if t else []
    check("tickers lists the universe", code == 200 and len(rows) >= 1 and all("last_close" in r and "trend" in r for r in rows))
    names = [r["ticker"] for r in rows]
    check("tickers match health", sorted(names) == sorted(tickers_h))

    code, m = jget("/api/metrics")
    check("metrics has every ticker", code == 200 and m and sorted(m) == sorted(names))
    if m:
        one = m[names[0]]
        check("metrics shape", all(k in one for k in ("baselines", "deep", "histories", "forecast_short", "forecast_long", "last_close", "trend", "federated_rounds", "sentiment", "mode")))
        check("four deep tiers", all(k in one["deep"] for k in ("lstm", "lstm_attention", "lstm_attention_sentiment", "hybrid_federated")))
        check("five baselines", len(one["baselines"]) == 5)

    tk = names[0]
    code, tm = jget(f"/api/metrics/{tk}")
    check("metrics/{ticker}", code == 200 and tm and tm["ticker"] == tk and tm["last_close"] == m[tk]["last_close"])

    for horizon, n in (("short", 5), ("long", 30)):
        code, f = jget(f"/api/forecast/{tk}?horizon={horizon}")
        ok = code == 200 and f and len(f["forecast"]) == n
        check(f"forecast {horizon} has {n} days", bool(ok))
        if ok:
            check(f"forecast {horizon} band brackets the prediction", all(r["lower"] <= r["predicted_close"] <= r["upper"] for r in f["forecast"]))

    code, hist = jget(f"/api/history/{tk}?days=60")
    ok = code == 200 and hist and len(hist["history"]) == 60
    check("history returns requested days", bool(ok))
    if ok:
        last = hist["history"][-1]["date"]
        expected = next_bdays(last, len(hist["forecast_overlay"]))
        check("overlay dates equal the frontend business-day calendar", [o["date"] for o in hist["forecast_overlay"]] == expected)
        check("history rows have OHLCV", all(k in hist["history"][0] for k in ("open", "high", "low", "close", "volume")))

    code, s = jget(f"/api/sentiment/{tk}")  # first call loads FinBERT, so it can take a minute or two
    ok = code == 200 and s and s["meta"]["n_headlines"] > 0 and len(s["daily"]) > 0 and len(s["headlines"]) > 0
    check("sentiment has meta, daily scores and headlines", bool(ok))
    if ok:
        check("sentiment scores within [-1, 1]", all(-1 <= d["score"] <= 1 for d in s["daily"]) and all(-1 <= x["sentiment_score"] <= 1 for x in s["headlines"]))

    # error paths the UI turns into messages
    check("invalid ticker -> 400", get(API + "/api/forecast/12345")[0] == 400)
    check("unknown ticker -> 404", get(API + "/api/forecast/ZZZZ")[0] == 404)
    check("bad horizon -> 422", get(API + f"/api/forecast/{tk}?horizon=bad")[0] == 422)
    check("history days out of range -> 422", get(API + f"/api/history/{tk}?days=5")[0] == 422)
    check("unknown /api path stays 404", get(API + "/api/nope")[0] == 404)

    if not api_only:
        code, body, ctype = get(WEB + "/")
        check("website serves the app shell", code == 200 and b'id="root"' in body and "html" in ctype)
        code, body, _ = get(WEB + "/api/health")
        check("website proxies /api to the backend", code == 200 and b'"QuantPulse"' in body)
        # built site served by the API itself (only when frontend/dist exists)
        if os.path.isdir(os.path.join(ROOT, "frontend", "dist")):
            code, body, _ = get(API + "/")
            check("API serves the built site", code == 200 and b'id="root"' in body)
            code, body, _ = get(API + "/app/forecast")
            check("API serves client routes (SPA fallback)", code == 200 and b'id="root"' in body)

    print()
    if failures:
        print(f"{len(failures)} check(s) FAILED: " + "; ".join(failures))
        sys.exit(1)
    print("All smoke checks passed.")


if __name__ == "__main__":
    main()
