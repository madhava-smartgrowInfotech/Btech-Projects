"""Serving store: loads artifacts, trains on first run if missing."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.config import MODELS_DIR, EVAL_DIR
from app.ml.dataset import load_dataset
from app.ml.preprocessing import prepare_frame

log = logging.getLogger(__name__)

STATE = {}


def ensure_artifacts() -> dict:
    if STATE:
        return STATE
    need = ["best_model.joblib", "preprocessor.joblib", "train_fused.npz", "train_frame.pkl", "metadata.json"]
    missing = [f for f in need if not (MODELS_DIR / f).exists()]
    if missing:
        log.info("Artifacts missing (%s); running training pipeline...", missing)
        from app.ml.evaluation import run_evaluation
        df_raw, meta = load_dataset()
        df = prepare_frame(df_raw)
        run_evaluation(df, meta)
    STATE["model"] = joblib.load(MODELS_DIR / "best_model.joblib")
    STATE["pre"] = joblib.load(MODELS_DIR / "preprocessor.joblib")
    STATE["train_fused"] = np.load(MODELS_DIR / "train_fused.npz")["fused"]
    STATE["train_df"] = pd.read_pickle(MODELS_DIR / "train_frame.pkl")
    STATE["metadata"] = json.loads((MODELS_DIR / "metadata.json").read_text(encoding="utf-8"))
    try:
        STATE["results"] = json.loads((MODELS_DIR / "evaluation_results.json").read_text(encoding="utf-8"))
    except Exception:
        STATE["results"] = json.loads((EVAL_DIR / "evaluation_results.json").read_text(encoding="utf-8"))
    return STATE
