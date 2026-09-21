"""
Spending prediction using a simple linear-trend model over monthly totals.

This intentionally avoids fancy time-series machinery: with only a handful of
months of local transaction history, a robust linear regression on monthly
totals (falling back to a plain average) is more honest than an elaborate
model that would just be overfitting noise. If there isn't enough history,
we say so explicitly instead of inventing a number.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MIN_MONTHS_REQUIRED = 3


def _monthly_totals(df: pd.DataFrame, transaction_type: str) -> pd.Series:
    subset = df[df.transaction_type == transaction_type].copy()
    if subset.empty:
        return pd.Series(dtype=float)
    subset["month"] = pd.to_datetime(subset["date"]).dt.to_period("M")
    return subset.groupby("month")["amount"].sum().sort_index()


def predict_next_month_expense(df: pd.DataFrame) -> dict:
    """Predict next month's total expense. df must have columns:
    date, amount, transaction_type, category."""
    totals = _monthly_totals(df, "expense")
    if len(totals) < MIN_MONTHS_REQUIRED:
        return {
            "available": False,
            "message": f"Need at least {MIN_MONTHS_REQUIRED} months of transaction "
                       f"history for a reliable prediction (currently have {len(totals)}).",
        }

    y = totals.values.astype(float)
    x = np.arange(len(y))
    # Simple least-squares linear fit; clip prediction at 0 (can't spend negative money)
    slope, intercept = np.polyfit(x, y, 1)
    next_x = len(y)
    predicted = max(0.0, slope * next_x + intercept)

    return {
        "available": True,
        "predicted_next_month_expense": round(predicted, 2),
        "recent_average": round(float(np.mean(y[-3:])), 2),
        "trend": "increasing" if slope > 1 else ("decreasing" if slope < -1 else "stable"),
        "months_used": len(y),
    }


def predict_category_spending(df: pd.DataFrame) -> dict:
    """Predict next month's spend per category using each category's own trend."""
    exp = df[df.transaction_type == "expense"].copy()
    if exp.empty:
        return {"available": False, "message": "No expense history available yet."}

    exp["month"] = pd.to_datetime(exp["date"]).dt.to_period("M")
    pivot = exp.pivot_table(index="month", columns="category", values="amount", aggfunc="sum", fill_value=0.0)
    pivot = pivot.sort_index()

    if len(pivot) < MIN_MONTHS_REQUIRED:
        return {
            "available": False,
            "message": f"Need at least {MIN_MONTHS_REQUIRED} months of history per category "
                       f"for reliable predictions (currently have {len(pivot)} months).",
        }

    predictions = {}
    x = np.arange(len(pivot))
    for category in pivot.columns:
        y = pivot[category].values.astype(float)
        slope, intercept = np.polyfit(x, y, 1)
        predictions[category] = round(max(0.0, slope * len(y) + intercept), 2)

    return {"available": True, "predictions": predictions, "months_used": len(pivot)}


def check_budget_overrun_risk(predicted_category_spend: dict, budgets: list[dict]) -> list[dict]:
    """Compare predicted next-month category spend against configured budgets."""
    risks = []
    budget_by_cat = {b["category"]: b["budget_amount"] for b in budgets}
    for category, predicted in predicted_category_spend.items():
        budget = budget_by_cat.get(category)
        if budget and predicted > budget:
            risks.append({
                "category": category, "predicted_spend": predicted, "budget": budget,
                "overrun_amount": round(predicted - budget, 2),
            })
    return risks
