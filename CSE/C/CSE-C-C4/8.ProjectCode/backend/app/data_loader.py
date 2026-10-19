"""QuantPulse OHLCV data loader.

Preference order:
  1. Live pull via yfinance (Yahoo Finance).
  2. Bundled CSVs in /data (saved from a previous live pull).
  3. Clearly-labeled synthetic-but-realistic series (geometric Brownian motion
     with regime shifts, volatility clustering, volume correlation) so the
     pipeline still runs end-to-end. Synthetic files are marked with
     `synthetic: true` in their header comment and in metadata.

Never fabricates prices silently: every return includes a `mode` field
("live" | "csv" | "synthetic").
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from . import config

PERIOD = "2y"
INTERVAL = "1d"


def _synthetic_series(ticker: str, seed: int, n: int = 500) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base = {"TSLA": 220, "AAPL": 180, "AMZN": 140, "MSFT": 330, "GOOGL": 135,
            "NVDA": 480, "META": 320, "FDX": 250, "IBM": 145, "ORCL": 110}.get(ticker, 150.0)
    # regime-switching drift + GARCH-like volatility clustering
    rets, vol = [], 0.02
    drift_regime = 0.0004
    for i in range(n):
        if i % 120 == 0:
            drift_regime = float(rng.normal(0.0003, 0.0006))
        vol = 0.012 + 0.85 * vol + 0.1 * abs(float(rng.normal(0, 0.02)))
        vol = float(np.clip(vol, 0.008, 0.06))
        rets.append(float(rng.normal(drift_regime, vol)))
    close = base * np.exp(np.cumsum(rets))
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)
    df = pd.DataFrame(index=dates)
    df["Close"] = close
    spread = np.abs(rng.normal(0.004, 0.002, n))
    df["Open"] = df["Close"].shift(1).fillna(df["Close"]) * (1 + rng.normal(0, 0.003, n))
    df["High"] = np.maximum(df["Open"], df["Close"]) * (1 + spread / 2)
    df["Low"] = np.minimum(df["Open"], df["Close"]) * (1 - spread / 2)
    vol_base = {"NVDA": 45e6, "TSLA": 100e6, "AAPL": 60e6}.get(ticker, 8e6)
    df["Volume"] = (vol_base * (1 + 2 * np.abs(rets) / 0.03) * rng.lognormal(0, 0.25, n)).astype(int)
    df["Adj Close"] = df["Close"]
    df.index.name = "Date"
    return df


def load_ticker(ticker: str) -> tuple[pd.DataFrame, str]:
    """Returns (ohlcv DataFrame, mode). Raises ValueError on invalid ticker."""
    t = (ticker or "").strip().upper()
    if not t or not t.isalpha() or len(t) > 6:
        raise ValueError(f"Invalid ticker '{ticker}'. Use 1-6 letters, e.g. TSLA.")
    data_dir = os.path.abspath(config.DATA_DIR)
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, f"{t}.csv")

    # 1) live yfinance pull
    try:
        import yfinance as yf
        df = yf.download(t, period=PERIOD, interval=INTERVAL, progress=False, auto_adjust=False)
        if df is not None and len(df) > 60 and "Close" in df.columns:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0] for c in df.columns]
            df = df[["Open", "High", "Low", "Close", "Adj Close" if "Adj Close" in df.columns else "Close", "Volume"]].dropna()
            if "Adj Close" not in df.columns:
                df["Adj Close"] = df["Close"]
            df.to_csv(csv_path)
            return df, "live"
    except Exception:
        pass

    # 2) bundled CSV
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            if len(df) > 60:
                return df, "csv"
        except Exception:
            pass

    # 3) synthetic fallback (clearly labeled)
    seed = abs(hash(t)) % (2 ** 31)
    df = _synthetic_series(t, seed)
    with open(csv_path, "w") as f:
        f.write("# synthetic: true — generated fallback (no network/CSV available)\n")
        df.to_csv(f)
    return df, "synthetic"


def load_universe(tickers: list[str] | None = None) -> dict[str, dict]:
    tickers = tickers or config.get_tickers()
    out: dict[str, dict] = {}
    for t in tickers:
        try:
            df, mode = load_ticker(t)
            out[t] = {"data": df, "mode": mode}
        except ValueError:
            out[t] = {"error": "invalid ticker"}
    return out
