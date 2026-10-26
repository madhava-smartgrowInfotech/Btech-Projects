"""Unit tests for the QuantPulse pipeline modules: data loader, windows and scalers, metrics, FedAvg, forecast, baselines, sentiment."""
import numpy as np
import pandas as pd
import pytest

from backend.app import baselines as bl
from backend.app import config, data_loader, federated as fed, forecast as fc, models_dl as mdl
from backend.app import sentiment as sent


def _walk(n=300, seed=1, start=100.0):
    rng = np.random.default_rng(seed)
    close = start * np.exp(np.cumsum(rng.normal(0.0004, 0.01, n)))
    idx = pd.bdate_range("2024-01-02", periods=n)
    df = pd.DataFrame({"Open": close * 0.999, "High": close * 1.005, "Low": close * 0.995, "Close": close, "Adj Close": close,
                       "Volume": rng.integers(1_000_000, 2_000_000, n)}, index=idx)
    df.index.name = "Date"
    return df


# ------------------------------------------------------------------ data loader
@pytest.mark.parametrize("bad", ["", "   ", "TSLA1", "12", "TOOLONGX", "BR-K", None])
def test_load_ticker_rejects_invalid_symbols(bad):
    with pytest.raises(ValueError):
        data_loader.load_ticker(bad)


def test_synthetic_series_is_a_valid_ohlcv_frame():
    df = data_loader._synthetic_series("TSLA", seed=3, n=200)
    assert list(df.columns) == ["Close", "Open", "High", "Low", "Volume", "Adj Close"]
    assert len(df) == 200 and (df[["Open", "High", "Low", "Close"]] > 0).all().all()
    assert (df["High"] >= df[["Open", "Close"]].max(axis=1) - 1e-9).all()
    assert (df["Low"] <= df[["Open", "Close"]].min(axis=1) + 1e-9).all()


def test_synthetic_series_same_seed_same_prices():
    a = data_loader._synthetic_series("AAPL", seed=9, n=120)
    b = data_loader._synthetic_series("AAPL", seed=9, n=120)
    assert np.allclose(a.Close.to_numpy(), b.Close.to_numpy())


def test_loader_falls_back_to_bundled_csv_then_to_labelled_synthetic(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path))
    monkeypatch.setitem(__import__("sys").modules, "yfinance", None)   # import fails -> live pull skipped
    df, mode = data_loader.load_ticker("zzzz")
    assert mode == "synthetic" and len(df) == 500
    assert open(tmp_path / "ZZZZ.csv").readline().startswith("# synthetic: true")
    _walk(120).to_csv(tmp_path / "AAAA.csv")
    df, mode = data_loader.load_ticker("aaaa")
    assert mode == "csv" and len(df) == 120


def test_universe_marks_invalid_tickers(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path))
    monkeypatch.setitem(__import__("sys").modules, "yfinance", None)
    out = data_loader.load_universe(["BAD1", "OKAY"])
    assert out["BAD1"] == {"error": "invalid ticker"} and out["OKAY"]["mode"] == "synthetic"


def test_ticker_list_from_environment(monkeypatch):
    monkeypatch.setenv("QP_TICKERS", " tsla, msft ,, ibm")
    assert config.get_tickers() == ["TSLA", "MSFT", "IBM"]
    monkeypatch.delenv("QP_TICKERS")
    assert config.get_tickers() == config.DEFAULT_TICKERS and len(config.DEFAULT_TICKERS) == 10


# ------------------------------------------------------------------ windows, scalers, metrics
def test_make_windows_shapes_and_target_is_next_close():
    raw = np.arange(60 * 5, dtype=float).reshape(60, 5)
    X, y, idx = mdl.make_windows(raw, 20)
    assert X.shape == (40, 20, 5) and y.shape == (40,) and idx[0] == 20
    assert y[0] == raw[20, 3] and np.array_equal(X[0], raw[:20])


def test_scalers_are_fit_on_train_rows_only_and_clip_test_values():
    raw = np.column_stack([np.linspace(10, 20, 100)] * 5)
    sc = mdl.fit_scalers(raw[:80])
    out = mdl.apply_scalers(raw, sc)
    assert out[:80].min() == pytest.approx(0.0) and out[79].max() == pytest.approx(1.0)
    assert out[80:].max() == 1.0          # the future rises above the training maximum and is clipped
    assert (out[80:] == 1.0).all()


def test_split_is_chronological_80_20():
    X = np.zeros((100, 20, 5)); y = np.arange(100.0); idx = np.arange(100)
    (a, ya, _), (b, yb, _) = mdl.scale_split(X, y, idx, 120)
    assert len(a) == 80 and len(b) == 20 and ya.max() < yb.min()


def test_prepare_features_adds_sentiment_column():
    df = _walk(30)
    assert mdl.prepare_features(df, None).shape == (30, 5)
    assert mdl.prepare_features(df, np.zeros(30)).shape == (30, 6)


def test_evaluate_dl_perfect_prediction():
    from sklearn.preprocessing import MinMaxScaler
    close = np.linspace(100, 160, 50).reshape(-1, 1)
    sc = MinMaxScaler().fit(close)
    scaled = sc.transform(close).ravel()
    m = mdl.evaluate_dl(scaled, scaled, sc)
    assert m["mae"] == pytest.approx(0, abs=1e-9) and m["r2"] == pytest.approx(1.0) and m["directional_accuracy"] == 1.0 and m["n_test"] == 50


def test_directional_accuracy_of_a_constant_high_prediction_is_the_up_share():
    from sklearn.preprocessing import MinMaxScaler
    rng = np.random.default_rng(0)
    close = (100 + np.cumsum(rng.normal(0, 1, 200))).reshape(-1, 1)
    sc = MinMaxScaler().fit(close)
    yt = sc.transform(close).ravel()
    m = mdl.evaluate_dl(yt, np.full_like(yt, 2.0), sc)         # always predicts a level above every price: "up" every day
    assert m["directional_accuracy"] == pytest.approx((np.diff(close.ravel()) > 0).mean())


def test_baseline_metrics_helper():
    y = np.array([1.0, 2.0, 3.0, 2.0])
    m = bl._metrics(y, y)
    assert m["mae"] == 0 and m["directional_accuracy"] == 1.0 and m["n_test"] == 4
    m2 = bl._metrics(y, y + 1)
    assert m2["mae"] == pytest.approx(1.0) and m2["rmse"] == pytest.approx(1.0)


def test_baseline_split_and_lag_features():
    tr, te = bl._split(np.arange(100.0))
    assert len(tr) == 80 and len(te) == 20
    X, y = bl._lag_xy(np.arange(50.0), 20)
    assert X.shape == (30, 20) and y[0] == 20 and X[0, -1] == 19


def test_run_all_baselines_on_a_random_walk(monkeypatch):
    df = _walk(260)
    out = {"rf": bl.run_rf(df.Close.to_numpy()), "svr": bl.run_svr(df.Close.to_numpy()), "arima": bl.run_arima(df.Close.to_numpy())}
    for r in out.values():
        assert set(r["metrics"]) >= {"mae", "mse", "rmse", "r2", "directional_accuracy", "n_test"}
        assert np.isfinite(r["metrics"]["mae"])


# ------------------------------------------------------------------ models and federated averaging
def test_model_output_shapes_and_short_training():
    for build in (mdl.build_lstm, mdl.build_attention_lstm):
        m = build((config.WINDOW, 6))
        X = np.random.default_rng(0).random((64, config.WINDOW, 6), dtype=np.float32)
        y = X[:, -1, 3]
        assert m.predict(X, verbose=0).shape == (64, 1)
        h = mdl.train_model(m, X, y, epochs=2)
        assert len(h.history["loss"]) <= 2


def test_fedavg_weights_by_sample_count():
    a = [np.array([[0.0, 0.0]]), np.array([1.0])]
    b = [np.array([[4.0, 8.0]]), np.array([5.0])]
    out = fed.fedavg([a, b], [1, 3])
    assert np.allclose(out[0], [[3.0, 6.0]]) and np.allclose(out[1], [4.0])


def test_run_federated_returns_global_model_and_round_losses():
    rng = np.random.default_rng(0)
    clients = {t: (rng.random((40, config.WINDOW, 6), dtype=np.float32), rng.random(40).astype(np.float32)) for t in ("A", "B")}
    model, hist = fed.run_federated(mdl.build_lstm, clients, rounds=2, local_epochs=1, input_shape=(config.WINDOW, 6))
    assert [r["round"] for r in hist["rounds"]] == [1, 2] and all(np.isfinite(r["mean_local_loss"]) for r in hist["rounds"])
    assert model.predict(clients["A"][0][:3], verbose=0).shape == (3, 1)


# ------------------------------------------------------------------ forecast
class _Const:
    def __init__(self, v): self.v = v
    def predict(self, x, verbose=0): return np.full((len(x), 1), self.v)


def test_recursive_forecast_length_band_growth_and_floor():
    from sklearn.preprocessing import MinMaxScaler
    sc = MinMaxScaler().fit(np.array([[100.0], [200.0]]))
    win = np.full((config.WINDOW, 6), 0.5)
    out = fc.recursive_forecast(_Const(0.5), win, 30, 2.0, sc)
    assert len(out) == 30 and out[0]["day"] == 1 and out[-1]["day"] == 30
    widths = [o["upper"] - o["lower"] for o in out]
    assert all(b > a for a, b in zip(widths, widths[1:]))
    assert all(o["lower"] <= o["predicted_close"] <= o["upper"] for o in out)
    assert out[0]["predicted_close"] == pytest.approx(150.0)
    low = fc.recursive_forecast(_Const(0.0), win, 5, 500.0, sc)     # huge uncertainty: lower band floors at 0.01
    assert min(o["lower"] for o in low) == 0.01


# ------------------------------------------------------------------ sentiment
def test_lexicon_scorer_sign_and_range():
    assert sent._lexicon_score("AAPL beats earnings and record growth") > 0
    assert sent._lexicon_score("ACME cuts forecast as weak demand drops margins") < 0
    assert sent._lexicon_score("market trades flat") == 0
    assert -1 <= sent._lexicon_score("beats upgrade growth record buyback surge strong") <= 1


def test_score_headlines_falls_back_to_lexicon(monkeypatch):
    monkeypatch.setattr(sent, "_finbert", False)
    scores, scorer = sent.score_headlines(["TSLA beats estimates", "TSLA slides on weak guidance"])
    assert scorer == "lexicon" and scores[0] > 0 > scores[1]


def test_daily_sentiment_without_news_key_uses_labelled_synthetic_headlines(monkeypatch):
    monkeypatch.setattr(config, "NEWS_API_KEY", "")
    monkeypatch.setattr(sent, "_finbert", False)
    dates = pd.bdate_range("2025-01-01", periods=200)
    s, meta = sent.get_daily_sentiment("TSLA", dates)
    assert meta["source"] == "synthetic-fallback" and "NEWSAPI_KEY" in meta["note"]
    assert len(s) == 200 and s.between(-1, 1).all()
    assert (s.iloc[:100] == 0).all()                    # headlines are generated for the last 90 trading days only
    assert (s.iloc[-90:] != 0).any()


def test_recent_headlines_schema(monkeypatch):
    monkeypatch.setattr(config, "NEWS_API_KEY", "")
    hs = sent.recent_headlines("MSFT", n=5)
    assert len(hs) == 5 and all(set(h) == {"headline", "sentiment_score"} and -1 <= h["sentiment_score"] <= 1 for h in hs)
