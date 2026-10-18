"""
utils.py
--------
Small shared helper functions used across the application:
- friendly error/warning display helpers (Streamlit-safe)
- tenure grouping
- risk-category assignment from a configurable threshold dict
- safe numeric coercion
"""

from __future__ import annotations
import numpy as np
import pandas as pd

DEFAULT_RISK_THRESHOLDS = {"low": 30, "medium": 60, "high": 80}
# Bands: 0-low = Low, low-medium = Medium, medium-high = High, high-100 = Critical

RISK_ORDER = ["Low Risk", "Medium Risk", "High Risk", "Critical Risk"]

RISK_COLORS = {
    "Low Risk": "#2ecc71",
    "Medium Risk": "#f1c40f",
    "High Risk": "#e67e22",
    "Critical Risk": "#e74c3c",
}


def assign_risk_category(probability_pct: float, thresholds: dict = None) -> str:
    """Map a churn probability (0-100) to a risk band using configurable
    thresholds. `thresholds` has keys 'low', 'medium', 'high' marking the
    upper boundary (in %) of the Low, Medium and High bands respectively;
    anything above 'high' is Critical.
    """
    t = thresholds or DEFAULT_RISK_THRESHOLDS
    if probability_pct < t["low"]:
        return "Low Risk"
    elif probability_pct < t["medium"]:
        return "Medium Risk"
    elif probability_pct < t["high"]:
        return "High Risk"
    else:
        return "Critical Risk"


def assign_risk_series(prob_series: pd.Series, thresholds: dict = None) -> pd.Series:
    t = thresholds or DEFAULT_RISK_THRESHOLDS
    return prob_series.apply(lambda p: assign_risk_category(p, t))


def make_tenure_group(tenure: pd.Series) -> pd.Series:
    bins = [-1, 12, 24, 48, np.inf]
    labels = ["0-12 months", "13-24 months", "25-48 months", "49+ months"]
    return pd.cut(tenure, bins=bins, labels=labels)


def make_charge_group(charges: pd.Series, n_bins: int = 4) -> pd.Series:
    try:
        return pd.qcut(charges, q=n_bins, duplicates="drop")
    except Exception:
        return pd.cut(charges, bins=n_bins)


def safe_numeric(series: pd.Series) -> pd.Series:
    """Coerce a column to numeric, turning unparseable values into NaN
    rather than raising -- this is common with the TotalCharges column
    in the public Telco dataset, which contains blank strings."""
    return pd.to_numeric(series, errors="coerce")


def format_pct(x: float) -> str:
    return f"{x:.1f}%"


def safe_divide(a, b):
    return a / b if b else 0.0
