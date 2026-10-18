"""
risk_segmentation.py
----------------------
Scores an entire customer dataframe and segments it into risk bands
using the configurable thresholds from utils.py. Produces the
customer-level risk table used by the Customer Risk and Dashboard pages.
"""

from __future__ import annotations
import pandas as pd
import numpy as np

from prediction import score_customers
from utils import assign_risk_series, RISK_ORDER


def build_risk_table(
    df: pd.DataFrame, feature_cols: list, preprocessor, model,
    id_col: str | None, thresholds: dict,
    display_cols: list | None = None,
) -> pd.DataFrame:
    """Score every row in df and return a risk-annotated table with the
    core display columns the UI needs."""
    work = df.copy()
    proba = score_customers(work[feature_cols], preprocessor, model)

    result = pd.DataFrame()
    result["customerID"] = work[id_col].values if id_col and id_col in work.columns else np.arange(len(work))
    result["churn_probability"] = proba
    result["risk_category"] = assign_risk_series(result["churn_probability"], thresholds)

    if display_cols:
        for c in display_cols:
            if c in work.columns:
                result[c] = work[c].values

    result["risk_category"] = pd.Categorical(result["risk_category"], categories=RISK_ORDER, ordered=True)
    return result.sort_values("churn_probability", ascending=False).reset_index(drop=True)


def risk_distribution_summary(risk_table: pd.DataFrame) -> dict:
    total = len(risk_table)
    counts = risk_table["risk_category"].value_counts().reindex(RISK_ORDER, fill_value=0)
    return {
        "total": total,
        "counts": counts.to_dict(),
        "percentages": {k: round(100 * v / total, 1) if total else 0 for k, v in counts.items()},
        "avg_probability": round(risk_table["churn_probability"].mean(), 2) if total else 0,
    }
