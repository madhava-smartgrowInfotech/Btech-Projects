"""QuantPulse FastAPI backend — serves forecasts, metrics, sentiment.

Binds explicitly to 127.0.0.1. If artifacts are missing, trains lightweight
stats on demand; /api/health reports readiness.
"""
from __future__ import annotations
import os, json, re
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from . import config
from . import data_loader, sentiment as sent

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ART = os.path.abspath(config.ARTIFACTS_DIR)
FRONT_DIST = os.path.abspath(os.path.join(APP_DIR, "..", "..", "frontend", "dist"))

app = FastAPI(title="QuantPulse", version="1.0.0",
              description="AI-powered short-term stock trend forecasting")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:8000", "http://127.0.0.1:5173",
                                                  "http://localhost:5404", "http://localhost:8404", "http://127.0.0.1:5404"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

TICKER_RE = re.compile(r"^[A-Za-z]{1,6}$")

_metrics_cache: dict | None = None
_forecast_cache: dict | None = None


def _load_json(name):
    p = os.path.join(ART, name)
    if os.path.exists(p):
        return json.load(open(p))
    return None


def metrics():
    global _metrics_cache
    if _metrics_cache is None:
        _metrics_cache = _load_json("metrics.json") or {}
    return _metrics_cache


def forecasts():
    global _forecast_cache
    if _forecast_cache is None:
        _forecast_cache = _load_json("forecasts.json") or {}
    return _forecast_cache


def _check_ticker(t: str) -> str:
    t = (t or "").strip().upper()
    if not TICKER_RE.match(t):
        raise HTTPException(400, f"Invalid ticker '{t}'. Use 1-6 letters, e.g. TSLA.")
    return t


@app.get("/api/health")
def health():
    m = metrics()
    return {"status": "ok", "product": "QuantPulse", "tickers": sorted(m.keys()) if m else config.get_tickers(),
            "trained": bool(m), "news_source": "newsapi" if config.NEWS_API_KEY else "synthetic-fallback"}


@app.get("/api/tickers")
def tickers():
    m = metrics()
    tickers = sorted(m.keys()) if m else config.get_tickers()
    out = []
    for t in tickers:
        r = m.get(t, {})
        out.append({"ticker": t, "last_close": r.get("last_close"),
                    "trend": r.get("trend"), "mode": r.get("mode")})
    return {"tickers": out}


@app.get("/api/metrics")
def all_metrics():
    m = metrics()
    if not m:
        raise HTTPException(503, "Model artifacts not ready. Run: python -m backend.train")
    return m


@app.get("/api/metrics/{ticker}")
def ticker_metrics(ticker: str):
    t = _check_ticker(ticker)
    m = metrics().get(t)
    if not m:
        raise HTTPException(404, f"No metrics for '{t}'. Configured: {', '.join(sorted(metrics().keys())) or 'none yet'}")
    return {"ticker": t, **m}


@app.get("/api/forecast/{ticker}")
def forecast(ticker: str, horizon: str = Query("short", pattern="^(short|long)$")):
    t = _check_ticker(ticker)
    m = metrics().get(t)
    if not m:
        raise HTTPException(404, f"No forecast for '{t}'. Train the pipeline first.")
    key = "forecast_short" if horizon == "short" else "forecast_long"
    return {"ticker": t, "horizon": horizon, "last_close": m["last_close"],
            "trend": m["trend"], "forecast": m[key]}


@app.get("/api/sentiment/{ticker}")
def sentiment(ticker: str):
    t = _check_ticker(ticker)
    m = metrics().get(t)
    try:
        df, _ = data_loader.load_ticker(t)
        daily, meta = sent.get_daily_sentiment(t, df.index)
        tail = [{"date": d.strftime("%Y-%m-%d"), "score": round(float(v), 3)} for d, v in daily.tail(30).items()]
    except ValueError as e:
        raise HTTPException(400, str(e))
    headlines = (m or {}).get("headlines", sent.recent_headlines(t))
    return {"ticker": t, "meta": meta, "daily": tail, "headlines": headlines}


@app.get("/api/history/{ticker}")
def history(ticker: str, days: int = Query(120, ge=20, le=500)):
    t = _check_ticker(ticker)
    try:
        df, mode = data_loader.load_ticker(t)
    except ValueError as e:
        raise HTTPException(400, str(e))
    d = df.tail(days)
    m = metrics().get(t, {})
    overlay = []
    if m.get("forecast_short"):
        last_date = d.index[-1]
        import pandas as pd
        for i, f in enumerate(m["forecast_short"]):
            overlay.append({"date": (last_date + pd.tseries.offsets.BDay(i + 1)).strftime("%Y-%m-%d"),
                            "predicted_close": f["predicted_close"], "lower": f["lower"], "upper": f["upper"]})
    hist = [{"date": i.strftime("%Y-%m-%d"), "open": round(float(r["Open"]), 2),
             "high": round(float(r["High"]), 2), "low": round(float(r["Low"]), 2),
             "close": round(float(r["Close"]), 2), "volume": int(r["Volume"])} for i, r in d.iterrows()]
    return {"ticker": t, "mode": mode, "history": hist, "forecast_overlay": overlay}


# serve frontend build if present
if os.path.isdir(FRONT_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONT_DIST, "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    def root():
        return FileResponse(os.path.join(FRONT_DIST, "index.html"))

    # Single-page-app fallback: serve built files (favicon...) and let client routes like /app/forecast reload.
    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "Not found")
        f = os.path.abspath(os.path.join(FRONT_DIST, path))
        if f.startswith(FRONT_DIST + os.sep) and os.path.isfile(f):
            return FileResponse(f)
        return FileResponse(os.path.join(FRONT_DIST, "index.html"))
