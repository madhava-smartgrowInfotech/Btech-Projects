"""Budget CRUD + usage calculations + threshold alerts."""
from __future__ import annotations

from sqlalchemy import and_

from database.database import get_session
from database.models import Budget, Transaction, Notification
from utils.helpers import pct


def set_budget(user_id: int, category: str, budget_amount: float, month: int, year: int) -> int:
    if budget_amount <= 0:
        raise ValueError("budget_amount must be greater than zero")
    with get_session() as session:
        existing = session.query(Budget).filter(
            and_(Budget.user_id == user_id, Budget.category == category,
                 Budget.month == month, Budget.year == year)
        ).first()
        if existing:
            existing.budget_amount = budget_amount
            session.flush()
            return existing.id
        budget = Budget(user_id=user_id, category=category, budget_amount=budget_amount,
                         month=month, year=year)
        session.add(budget)
        session.flush()
        return budget.id


def delete_budget(user_id: int, budget_id: int) -> bool:
    with get_session() as session:
        b = session.query(Budget).filter(
            and_(Budget.id == budget_id, Budget.user_id == user_id)
        ).first()
        if not b:
            return False
        session.delete(b)
        return True


def get_budget_status(user_id: int, month: int, year: int) -> list[dict]:
    """Return per-category budget vs. actual spend for the given month/year."""
    with get_session() as session:
        budgets = session.query(Budget).filter(
            and_(Budget.user_id == user_id, Budget.month == month, Budget.year == year)
        ).all()

        status = []
        for b in budgets:
            spent = session.query(Transaction).filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.category == b.category,
                    Transaction.transaction_type == "expense",
                    Transaction.date >= f"{year:04d}-{month:02d}-01",
                    Transaction.date <= f"{year:04d}-{month:02d}-31",
                )
            ).all()
            actual = sum(t.amount for t in spent)
            used_pct = pct(actual, b.budget_amount)
            status.append({
                "id": b.id, "category": b.category, "budget_amount": b.budget_amount,
                "actual_spent": actual, "remaining": b.budget_amount - actual,
                "percent_used": used_pct,
            })
        return status


def check_and_raise_alerts(user_id: int, month: int, year: int) -> list[str]:
    """Create Notification rows for budgets crossing 75%/90%/100% thresholds.
    Returns the list of new alert messages created this call (avoids duplicate spam
    by checking if an identical unread notification already exists)."""
    created = []
    statuses = get_budget_status(user_id, month, year)
    with get_session() as session:
        for s in statuses:
            pct_used = s["percent_used"]
            if pct_used >= 100:
                msg = f"You have exceeded your {s['category']} budget."
                ntype = "danger"
            elif pct_used >= 90:
                msg = f"Your {s['category']} budget is 90% used."
                ntype = "warning"
            elif pct_used >= 75:
                msg = f"Your {s['category']} budget is 75% used."
                ntype = "warning"
            else:
                continue

            exists = session.query(Notification).filter(
                and_(Notification.user_id == user_id, Notification.message == msg)
            ).first()
            if not exists:
                session.add(Notification(user_id=user_id, message=msg, notification_type=ntype))
                created.append(msg)
    return created
