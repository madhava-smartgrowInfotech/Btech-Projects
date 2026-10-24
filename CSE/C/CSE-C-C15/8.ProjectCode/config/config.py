"""SentinelFlow configuration."""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:  # optional: pick up ports from the project .env
    from dotenv import load_dotenv

    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass

HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
PORT = int(os.getenv("BACKEND_PORT", "5000"))

MONITOR_WINDOW_SECONDS = 10
BASELINE_WINDOWS = 12

QUARANTINE_SECONDS = 40

MODEL_PATH = os.path.join(BASE_DIR, "models", "sentinelflow_rf.joblib")
FEATURES_PATH = os.path.join(BASE_DIR, "models", "feature_list.json")
METADATA_PATH = os.path.join(BASE_DIR, "models", "metadata.json")
METRICS_PATH = os.path.join(BASE_DIR, "results", "metrics.json")

DB_PATH = os.path.join(BASE_DIR, "data", "sentinelflow.db")

RANDOM_SEED = 42
TEST_SIZE = 0.2

PRODUCT_NAME = "SentinelFlow"
PRODUCT_TAGLINE = "Real-Time DDoS Detection & Adaptive Mitigation"
