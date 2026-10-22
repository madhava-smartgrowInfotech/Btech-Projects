"""Demo data for the web app, built on the project's own sample CSV and services.

utils.demo_data.load_demo_data loads the bundled CSV with its original dates (June-August 2026), so
on any later day the current month is empty. This version shifts those dates forward by whole months
so the newest sample month is the current month, then calls the same service functions. The seeded
demo account also gets a few earlier synthetic months so every chart and the ML prediction have
history to show.
"""
from __future__ import annotations

import calendar
import random
from datetime import date, timedelta

import pandas as pd

from auth.authentication import login, signup
from database.database import get_session
from database.models import Transaction, User
from services.budget_service import check_and_raise_alerts, set_budget
from services.goal_service import add_goal
from services.investment_service import add_investment
from services.transaction_service import add_transaction
from utils.helpers import current_month_year
from utils.demo_data import SAMPLE_CSV

DEMO_NAME = "Aarav Mehta"
DEMO_EMAIL = "demo@finjarvis.com"
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "Demo@1234"


def _shift_months(d: date, months: int) -> date:
    idx = d.year * 12 + (d.month - 1) + months
    year, month = divmod(idx, 12)
    month += 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def load_demo(user_id: int, extra_months: int = 0) -> dict:
    """Load shifted sample data (+ optional earlier synthetic months). Returns counts."""
    df = pd.read_csv(SAMPLE_CSV, parse_dates=["date"])
    today = date.today()
    newest = df["date"].max().date()
    shift = (today.year * 12 + today.month) - (newest.year * 12 + newest.month)

    count = 0
    first_month = None
    for _, row in df.iterrows():
        d = _shift_months(row["date"].date(), shift)
        if d > today:  # keep the demo free of future-dated rows
            d = today
        first_month = d if first_month is None or d < first_month else first_month
        add_transaction(user_id, d, row["description"], row["category"], float(row["amount"]), row["type"],
                        payment_method=_method(row["description"]))
        count += 1

    if extra_months and first_month:
        count += _synthetic_months(user_id, first_month, extra_months)

    month, year = current_month_year()
    for category, amount in [("Food", 6000), ("Transport", 3000), ("Entertainment", 2500),
                             ("Shopping", 4000), ("Bills", 3000)]:
        set_budget(user_id, category, amount, month, year)

    add_goal(user_id, "Emergency Fund", 100000, 32000, today + timedelta(days=240))
    add_goal(user_id, "New Laptop", 80000, 15000, today + timedelta(days=150))
    add_goal(user_id, "Vacation", 50000, 10000, today + timedelta(days=180))

    add_investment(user_id, "Nifty 50 Index Fund", "NIFTYBEES.NS", "ETF", 40, 220.0, 245.0, today - timedelta(days=200))
    add_investment(user_id, "Gold ETF", "GOLDBEES.NS", "Gold", 25, 52.0, 58.0, today - timedelta(days=300))
    add_investment(user_id, "Fixed Deposit", "", "Fixed Deposit", 1, 50000.0, 53500.0, today - timedelta(days=365))
    add_investment(user_id, "HDFC Bank", "HDFCBANK.NS", "Stock", 12, 1480.0, 1625.0, today - timedelta(days=150))

    check_and_raise_alerts(user_id, month, year)
    return {"transactions": count}


def _method(description: str) -> str:
    d = description.lower()
    if any(k in d for k in ("salary", "rent", "emi", "sip")):
        return "Bank Transfer"
    if any(k in d for k in ("swiggy", "zomato", "uber", "ola", "movie", "netflix", "spotify")):
        return "UPI"
    if any(k in d for k in ("amazon", "flipkart", "myntra")):
        return "Card"
    return "UPI"


def _synthetic_months(user_id: int, before: date, months: int) -> int:
    """Fictional, seeded earlier months with a gentle upward spending trend."""
    rng = random.Random(411)
    templates = [
        ("Swiggy order", "Food", 380, "UPI"), ("Zomato order", "Food", 520, "UPI"),
        ("Grocery store", "Food", 1800, "Card"), ("Uber ride", "Transport", 260, "UPI"),
        ("Petrol pump", "Transport", 1500, "Card"), ("Netflix subscription", "Entertainment", 649, "Card"),
        ("Movie tickets", "Entertainment", 700, "UPI"), ("Amazon purchase", "Shopping", 2200, "Card"),
        ("Electricity bill", "Bills", 1650, "UPI"), ("Mobile recharge", "Bills", 599, "UPI"),
        ("Pharmacy", "Healthcare", 450, "Cash"),
    ]
    total = 0
    for back in range(1, months + 1):
        month_start = _shift_months(date(before.year, before.month, 1), -back)
        last = calendar.monthrange(month_start.year, month_start.month)[1]
        add_transaction(user_id, month_start.replace(day=1), "Monthly salary", "Salary", 65000, "income",
                        payment_method="Bank Transfer")
        add_transaction(user_id, month_start.replace(day=2), "House rent", "Rent", 18000, "expense",
                        payment_method="Bank Transfer")
        total += 2
        growth = 1 + 0.04 * (months - back)  # older months a little cheaper
        for desc, cat, base, method in templates:
            if rng.random() < 0.8:
                amount = round(base * growth * rng.uniform(0.85, 1.2), 0)
                add_transaction(user_id, month_start.replace(day=rng.randint(3, last)), desc, cat, amount,
                                "expense", payment_method=method)
                total += 1
    return total


def ensure_demo_user() -> int | None:
    """Create the demo account (demo@finjarvis.com / Demo@1234) with synthetic data if missing."""
    result = login(DEMO_USERNAME, DEMO_PASSWORD)
    if result.success:
        user_id = result.user_id
    else:
        res = signup(DEMO_NAME, DEMO_EMAIL, DEMO_USERNAME, DEMO_PASSWORD, DEMO_PASSWORD)
        if not res.success:
            return None  # username taken by a real user with another password: leave it alone
        user_id = res.user_id
        with get_session() as session:
            u = session.query(User).filter(User.id == user_id).first()
            u.monthly_income = 65000.0
            u.savings_target = 20000.0
    with get_session() as session:
        has_data = session.query(Transaction).filter(Transaction.user_id == user_id).first() is not None
    if not has_data:
        load_demo(user_id, extra_months=3)
    return user_id
