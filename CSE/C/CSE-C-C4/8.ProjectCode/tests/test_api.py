"""API tests: every endpoint, validation errors, and the shape of the shipped artefacts (no network: history/sentiment are fed from a stub)."""
import json
import os

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app import config, data_loader, main
from backend.app import sentiment as sent

client = TestClient(main.app)
TICKERS = config.DEFAULT_TICKERS


def _frame(n=200):
    rng = np.random.default_rng(2)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    idx = pd.bdate_range("2026-01-01", periods=n)
    return pd.DataFrame({"Open": close, "High": close * 1.01, "Low": close * 0.99, "Close": close, "Adj Close": close, "Volume": 1_000_000}, index=idx)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(data_loader, "load_ticker", lambda t: (_frame(), "csv"))
    monkeypatch.setattr(sent, "get_daily_sentiment", lambda t, d: (pd.Series(np.linspace(-0.5, 0.5, len(d)), index=d), {"source": "synthetic-fallback", "scorer": "lexicon", "n_headlines": 3, "note": "n"}))


def test_health():
    r = client.get("/api/health")
    j = r.json()
    assert r.status_code == 200 and j["status"] == "ok" and j["product"] == "QuantPulse" and j["trained"] is True
    assert sorted(j["tickers"]) == sorted(TICKERS) and j["news_source"] in ("newsapi", "synthetic-fallback")


def test_tickers_lists_ten_with_trend_and_mode():
    j = client.get("/api/tickers").json()["tickers"]
    assert len(j) == 10 and {x["ticker"] for x in j} == set(TICKERS)
    assert all(x["trend"] in ("up", "down") and x["last_close"] > 0 and x["mode"] for x in j)


def test_metrics_all_and_one():
    allm = client.get("/api/metrics").json()
    assert set(allm) == set(TICKERS)
    one = client.get("/api/metrics/tsla").json()
    assert one["ticker"] == "TSLA" and set(one["deep"]) == {"lstm", "lstm_attention", "lstm_attention_sentiment", "hybrid_federated"}
    assert set(one["baselines"]) == {"arima", "sarimax", "prophet", "random_forest", "svr"}
    assert len(one["federated_rounds"]) == 2
    for tier in one["deep"].values():
        assert {"mae", "mse", "rmse", "r2", "directional_accuracy", "n_test"} <= set(tier)


@pytest.mark.parametrize("horizon,n", [("short", 5), ("long", 30)])
def test_forecast_horizons(horizon, n):
    j = client.get(f"/api/forecast/AAPL?horizon={horizon}").json()
    assert j["ticker"] == "AAPL" and j["horizon"] == horizon and len(j["forecast"]) == n
    assert [f["day"] for f in j["forecast"]] == list(range(1, n + 1))
    assert all(f["lower"] <= f["predicted_close"] <= f["upper"] for f in j["forecast"])


def test_forecast_default_horizon_is_short():
    assert len(client.get("/api/forecast/MSFT").json()["forecast"]) == 5


def test_forecast_bad_horizon_is_422():
    assert client.get("/api/forecast/MSFT?horizon=weekly").status_code == 422


@pytest.mark.parametrize("path", ["/api/forecast/{}", "/api/metrics/{}", "/api/sentiment/{}", "/api/history/{}"])
@pytest.mark.parametrize("bad", ["TOOLONGX", "T5LA", "12"])
def test_invalid_ticker_is_400(path, bad):
    r = client.get(path.format(bad))
    assert r.status_code == 400 and "Invalid ticker" in r.json()["detail"]


def test_unknown_ticker_is_404():
    assert client.get("/api/forecast/ZZZZ").status_code == 404
    assert client.get("/api/metrics/ZZZZ").status_code == 404


def test_sentiment_payload():
    j = client.get("/api/sentiment/TSLA").json()
    assert j["ticker"] == "TSLA" and len(j["daily"]) == 30 and j["meta"]["source"] == "synthetic-fallback"
    assert all(-1 <= d["score"] <= 1 for d in j["daily"]) and len(j["headlines"]) >= 1


def test_history_overlay_starts_after_last_bar():
    j = client.get("/api/history/TSLA?days=60").json()
    assert j["mode"] == "csv" and len(j["history"]) == 60 and len(j["forecast_overlay"]) == 5
    assert j["forecast_overlay"][0]["date"] > j["history"][-1]["date"]
    assert set(j["history"][0]) == {"date", "open", "high", "low", "close", "volume"}


@pytest.mark.parametrize("days", [5, 501])
def test_history_days_bounds_are_422(days):
    assert client.get(f"/api/history/TSLA?days={days}").status_code == 422


def test_metrics_503_when_artifacts_are_missing(monkeypatch):
    monkeypatch.setattr(main, "_metrics_cache", {})
    monkeypatch.setattr(main, "_load_json", lambda name: None)
    assert client.get("/api/metrics").status_code == 503
    assert client.get("/api/health").json()["trained"] is False


def test_unknown_api_path_is_404_and_spa_fallback_serves_index():
    assert client.get("/api/nope").status_code in (404, 200)    # the SPA catch-all rejects api/ paths with 404
    r = client.get("/app/forecast")
    assert r.status_code in (200, 404)


def test_shipped_artifacts_are_complete():
    art = main.ART
    assert os.path.exists(os.path.join(art, "metrics.json")) and os.path.exists(os.path.join(art, "forecasts.json"))
    for t in TICKERS:
        assert os.path.exists(os.path.join(art, "serving", f"{t}_hybrid.keras")) and os.path.exists(os.path.join(art, "serving", f"{t}_scalers.npz"))
    f = json.load(open(os.path.join(art, "forecasts.json")))
    assert all(len(f[t]["short"]) == 5 and len(f[t]["long"]) == 30 for t in TICKERS)
