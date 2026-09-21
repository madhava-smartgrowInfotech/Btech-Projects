"""Aggregation/analytics helpers powering the dashboard and analytics page.
Pure computation over transaction/investment data already scoped by user_id."""
from __future__ import annotations

from datetime import date
import pandas as pd

from services.transaction_service import get_transactions
from services.investment_service import portfolio_summary
from utils.helpers import pct


def transactions_dataframe(user_id: int, start_date=None, end_date=None) -> pd.DataFrame:
    rows = get_transactions(user_id, start_date=start_date, end_date=end_date)
    if not rows:
        return pd.DataFrame(columns=["date", "description", "category", "amount", "transaction_type"])
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


def summary_metrics(user_id: int, month: int, year: int, monthly_income: float) -> dict:
    from utils.helpers import month_bounds
    start, end = month_bounds(year, month)
    df = transactions_dataframe(user_id, start_date=start, end_date=end)

    income = df.loc[df.transaction_type == "income", "amount"].sum() if not df.empty else 0.0
    expenses = df.loc[df.transaction_type == "expense", "amount"].sum() if not df.empty else 0.0
    effective_income = income if income > 0 else monthly_income
    savings = effective_income - expenses
    savings_rate = pct(savings, effective_income) if effective_income else 0.0

    port = portfolio_summary(user_id)

    # All-time totals for net worth (cash position proxy + investments)
    all_df = transactions_dataframe(user_id)
    all_income = all_df.loc[all_df.transaction_type == "income", "amount"].sum() if not all_df.empty else 0.0
    all_expenses = all_df.loc[all_df.transaction_type == "expense", "amount"].sum() if not all_df.empty else 0.0
    cash_position = all_income - all_expenses
    net_worth = cash_position + port["total_current_value"]

    return {
        "monthly_income": effective_income,
        "monthly_expenses": expenses,
        "monthly_savings": savings,
        "savings_rate": savings_rate,
        "investment_value": port["total_current_value"],
        "net_worth": net_worth,
        "total_balance": cash_position,
    }


def spending_by_category(user_id: int, start_date=None, end_date=None) -> pd.DataFrame:
    df = transactions_dataframe(user_id, start_date, end_date)
    if df.empty:
        return pd.DataFrame(columns=["category", "amount"])
    exp = df[df.transaction_type == "expense"]
    if exp.empty:
        return pd.DataFrame(columns=["category", "amount"])
    return exp.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)


def monthly_trend(user_id: int, months_back: int = 6) -> pd.DataFrame:
    df = transactions_dataframe(user_id)
    if df.empty:
        return pd.DataFrame(columns=["month", "income", "expense"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    pivot = df.pivot_table(index="month", columns="transaction_type", values="amount", aggfunc="sum", fill_value=0)
    pivot = pivot.reset_index().sort_values("month").tail(months_back)
    for col in ("income", "expense"):
        if col not in pivot.columns:
            pivot[col] = 0.0
    return pivot[["month", "income", "expense"]]


def analytics_overview(user_id: int, start_date=None, end_date=None) -> dict:
    df = transactions_dataframe(user_id, start_date, end_date)
    if df.empty:
        return {
            "total_income": 0.0, "total_expenses": 0.0, "avg_daily_spending": 0.0,
            "largest_expense": None, "top_category": None, "savings_rate": 0.0,
        }
    income = df.loc[df.transaction_type == "income", "amount"].sum()
    expenses_df = df[df.transaction_type == "expense"]
    expenses = expenses_df["amount"].sum()
    days = max(1, (df["date"].max() - df["date"].min()).days + 1)
    avg_daily = expenses / days
    largest = None
    if not expenses_df.empty:
        row = expenses_df.loc[expenses_df["amount"].idxmax()]
        largest = {"description": row["description"], "amount": row["amount"], "category": row["category"]}
    top_cat = None
    by_cat = spending_by_category(user_id, start_date, end_date)
    if not by_cat.empty:
        top_cat = by_cat.iloc[0]["category"]
    savings_rate = pct(income - expenses, income) if income else 0.0
    return {
        "total_income": income, "total_expenses": expenses, "avg_daily_spending": avg_daily,
        "largest_expense": largest, "top_category": top_cat, "savings_rate": savings_rate,
    }
