"""QuantPulse configuration — single source of truth for tickers and hyperparameters."""
from __future__ import annotations
import os

APP_NAME = "QuantPulse"
API_HOST = "127.0.0.1"
API_PORT = int(os.getenv("QUANTPULSE_PORT", "8000"))

# Default 10-ticker tech-heavy universe.
# Assumption (documented in README): "Google" -> GOOGL, "Meta/or Airbnb" -> META,
# "Oracle" -> ORCL. All configurable via QP_TICKERS env var (comma-separated).
DEFAULT_TICKERS = ["TSLA", "AAPL", "AMZN", "MSFT", "GOOGL", "NVDA", "META", "FDX", "IBM", "ORCL"]

def get_tickers() -> list[str]:
    raw = os.getenv("QP_TICKERS", "")
    if raw.strip():
        return [t.strip().upper() for t in raw.split(",") if t.strip()]
    return list(DEFAULT_TICKERS)

WINDOW = 20            # sliding window (trading days)
TRAIN_SPLIT = 0.8      # chronological 80/20 split
BATCH_SIZE = 32
EPOCHS = 50
LSTM_UNITS = 64
ATTENTION_HEADS = 4
FORECAST_HORIZONS = {"short": 5, "long": 30}
RANDOM_STATE = 42
NEWS_API_KEY = os.getenv("NEWSAPI_KEY", "")
NEWS_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "news_cache")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "artifacts")
