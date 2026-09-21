"""Loads bundled fictional sample data for a user who wants to try the app immediately."""
from __future__ import annotations

import os
from datetime import date, timedelta
import pandas as pd

from services.transaction_service import add_transaction
from services.budget_service import set_budget
from services.goal_service import add_goal
from services.investment_service import add_investment
from utils.helpers import current_month_year

SAMPLE_CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample_transactions.csv")


def load_demo_data(user_id: int) -> None:
    df = pd.read_csv(SAMPLE_CSV, parse_dates=["date"])
    for _, row in df.iterrows():
        add_transaction(
            user_id=user_id, txn_date=row["date"].date(), description=row["description"],
            category=row["category"], amount=float(row["amount"]), transaction_type=row["type"],
        )

    month, year = current_month_year()
    for category, amount in [("Food", 6000), ("Transport", 3000), ("Entertainment", 2500),
                              ("Shopping", 4000), ("Bills", 3000)]:
        set_budget(user_id, category, amount, month, year)

    add_goal(user_id, "Emergency Fund", 100000, 32000, date.today() + timedelta(days=240))
    add_goal(user_id, "New Laptop", 80000, 15000, date.today() + timedelta(days=150))
    add_goal(user_id, "Vacation", 50000, 10000, date.today() + timedelta(days=180))

    add_investment(user_id, "Nifty 50 Index Fund", "NIFTYBEES.NS", "ETF", 40, 220.0, 245.0, date.today() - timedelta(days=200))
    add_investment(user_id, "Gold ETF", "GOLDBEES.NS", "Gold", 25, 52.0, 58.0, date.today() - timedelta(days=300))
    add_investment(user_id, "Fixed Deposit", "", "Fixed Deposit", 1, 50000.0, 53500.0, date.today() - timedelta(days=365))
