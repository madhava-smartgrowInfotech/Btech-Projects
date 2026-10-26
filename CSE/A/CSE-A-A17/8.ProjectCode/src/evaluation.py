"""
evaluation.py
---------------
Metrics used everywhere in the app: baseline comparison, XGBoost vs
baselines, and before/after domain adaptation.

A special note on MAPE: regular MAPE divides by the actual value, which
blows up (division by zero) whenever actual demand is 0 -- which happens
a LOT in daily per-article retail data (most products don't sell every
single day). We implement a "safe MAPE" that simply excludes zero-actual
rows from the MAPE calculation, and we report how many rows were excluded
so the number stays honest and interpretable.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


def safe_mape(y_true, y_pred) -> tuple[float, int]:
    """
    WHAT: MAPE that skips rows where actual demand == 0.
    Returns (mape_percentage, num_rows_excluded).
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    nonzero_mask = y_true != 0
    excluded = int((~nonzero_mask).sum())

    if nonzero_mask.sum() == 0:
        return float("nan"), excluded

    ape = np.abs((y_true[nonzero_mask] - y_pred[nonzero_mask]) / y_true[nonzero_mask])
    mape = float(np.mean(ape) * 100)
    return mape, excluded


def evaluate_model(y_true, y_pred) -> dict:
    """Computes the standard metric bundle used throughout the app."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    mape, excluded = safe_mape(y_true, y_pred)
    r2 = float(r2_score(y_true, y_pred)) if len(np.unique(y_true)) > 1 else float("nan")

    return {
        "RMSE": rmse,
        "MAE": mae,
        "MAPE (%)": mape,
        "MAPE_excluded_zero_rows": excluded,
        "R2": r2,
    }


def compare_models(results: dict[str, dict]) -> pd.DataFrame:
    """
    WHAT: Turns a dict of {model_name: metrics_dict} into a tidy
          comparison table for st.dataframe().
    """
    rows = []
    for model_name, metrics in results.items():
        row = {"Model": model_name}
        row.update(metrics)
        rows.append(row)
    return pd.DataFrame(rows)


def improvement_percentage(baseline_value: float, new_value: float) -> float:
    """
    WHAT: % improvement of `new_value` over `baseline_value` for a
          "lower is better" metric (RMSE, MAE, MAPE).
    Formula: ((baseline - new) / baseline) * 100
    Positive = improvement, Negative = got worse. We report exactly what
    the experiment shows -- no rounding up or overstating results.
    """
    if baseline_value == 0 or np.isnan(baseline_value):
        return float("nan")
    return ((baseline_value - new_value) / baseline_value) * 100


def before_after_adaptation_report(before_metrics: dict, after_metrics: dict) -> pd.DataFrame:
    """
    WHAT: Builds the "Before vs After Domain Adaptation" comparison table
          with improvement percentages for RMSE, MAE, and MAPE.
    """
    rows = []
    for metric in ["RMSE", "MAE", "MAPE (%)"]:
        before_val = before_metrics.get(metric, float("nan"))
        after_val = after_metrics.get(metric, float("nan"))
        rows.append(
            {
                "Metric": metric,
                "Before Adaptation": before_val,
                "After Adaptation": after_val,
                "Improvement (%)": improvement_percentage(before_val, after_val),
            }
        )
    # R2: higher is better, so improvement direction flips
    r2_before = before_metrics.get("R2", float("nan"))
    r2_after = after_metrics.get("R2", float("nan"))
    r2_improvement = float("nan")
    if not np.isnan(r2_before) and r2_before != 0:
        r2_improvement = ((r2_after - r2_before) / abs(r2_before)) * 100
    rows.append(
        {
            "Metric": "R2",
            "Before Adaptation": r2_before,
            "After Adaptation": r2_after,
            "Improvement (%)": r2_improvement,
        }
    )
    return pd.DataFrame(rows)
