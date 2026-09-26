"""Objective 5 - refine the model continuously as new threat data arrives.

`retrain()` merges the base dataset with every URL the community (or a
trusted feed) has confirmed, up-weights those fresh examples and re-runs
the full train/compare cycle. The detector then hot-reloads the new best
model without restarting the web app.
"""
from __future__ import annotations

import threading

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from . import config
from .data import load_dataset
from .features import featurize_urls
from .threat_intel import ThreatIntel
from .train import train_all

_retrain_lock = threading.Lock()


def retrain(ti: ThreatIntel | None = None, max_rows: int | None = None,
            verbose: bool = True) -> dict:
    ti = ti or ThreatIntel()
    if not _retrain_lock.acquire(blocking=False):
        return {"skipped": True, "reason": "a retrain is already running"}
    try:
        base = load_dataset(max_rows=max_rows)
        crowd = ti.training_examples()
        crowd_df = pd.DataFrame(crowd, columns=["url", "label"]).astype({"url": str, "label": int})
        if verbose:
            print(f"Base dataset: {len(base)} rows | crowdsourced confirmed: {len(crowd_df)} rows")

        # remove base rows that the crowd has since re-labelled
        if len(crowd_df):
            base = base[~base["url"].isin(crowd_df["url"])]
        full = pd.concat([base, crowd_df], ignore_index=True)
        weights = np.concatenate([
            np.ones(len(base)), np.full(len(crowd_df), config.CROWD_SAMPLE_WEIGHT)])

        X = featurize_urls(full["url"].tolist())
        y = full["label"].astype(int).to_numpy()
        X_tr, X_te, y_tr, y_te, w_tr, _ = train_test_split(
            X, y, weights, test_size=config.TEST_SIZE,
            random_state=config.RANDOM_STATE, stratify=y)

        # sample weights are passed by duplicating weighted rows (works for every model)
        reps = np.round(w_tr).astype(int)
        X_tr = np.repeat(X_tr, reps, axis=0)
        y_tr = np.repeat(y_tr, reps, axis=0)

        summary = train_all(X_tr, y_tr, X_te, y_te, verbose=verbose, meta={
            "base_rows": int(len(base)),
            "crowd_rows": int(len(crowd_df)),
            "crowd_weight": config.CROWD_SAMPLE_WEIGHT,
        })
        summary["crowd_marked_trained"] = ti.mark_trained()
        return summary
    finally:
        _retrain_lock.release()


def maybe_auto_retrain(ti: ThreatIntel, detector, verbose: bool = False) -> bool:
    """Kick off a background retrain when enough new confirmed URLs accumulated."""
    if ti.pending_training_count() < config.AUTO_RETRAIN_EVERY:
        return False

    def _job():
        retrain(ti, verbose=verbose)
        detector.reload()

    threading.Thread(target=_job, daemon=True, name="phishguard-auto-retrain").start()
    return True
