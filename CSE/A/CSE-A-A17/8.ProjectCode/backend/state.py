"""
state.py
---------
Process-wide pipeline state. This is the FastAPI equivalent of the Streamlit
`st.session_state` used by app.py: one dict, filled in as the user moves through
the pipeline. The app is a single-user demo, so one shared state is intended.
"""

from __future__ import annotations

import math
import os
import threading
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "models"
BASELINE_MODEL_PATH = MODEL_DIR / "baseline_xgboost.joblib"
ADAPTED_MODEL_PATH = MODEL_DIR / "adapted_xgboost.joblib"
FEATURE_INFO_PATH = MODEL_DIR / "feature_info.joblib"

LOCK = threading.RLock()

_KEYS = [
    "transactions_raw", "articles_raw", "customers_raw",
    "merged", "daily_demand", "feature_table", "feature_mappings",
    "train_df", "test_df", "quality_report",
    "baseline_model", "source_model", "adapted_model", "domain_eval", "domain_run",
    "results", "last_forecast",
]

S: dict = {k: None for k in _KEYS}
S["results"] = {}


def reset_downstream() -> None:
    """A new upload invalidates everything derived from the old data."""
    for k in ["daily_demand", "feature_table", "feature_mappings", "train_df", "test_df",
              "baseline_model", "source_model", "adapted_model", "domain_eval", "domain_run",
              "last_forecast"]:
        S[k] = None
    S["results"] = {}


def load_env_file() -> dict:
    """Minimal .env reader (KEY=VALUE per line) so no extra dependency is needed."""
    out: dict = {}
    path = ROOT / ".env"
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def env(key: str, default: str = "") -> str:
    return os.environ.get(key) or load_env_file().get(key, default)


def clean(obj):
    """Make pandas / numpy values JSON safe (NaN and inf become null, dates become ISO strings)."""
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, pd.DataFrame):
        return clean(obj.to_dict(orient="records"))
    if isinstance(obj, pd.Series):
        return clean(obj.tolist())
    if isinstance(obj, np.ndarray):
        return clean(obj.tolist())
    if isinstance(obj, (pd.Timestamp,)):
        return obj.date().isoformat()
    if obj is pd.NaT:
        return None
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        f = float(obj)
        return None if math.isnan(f) or math.isinf(f) else f
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj
