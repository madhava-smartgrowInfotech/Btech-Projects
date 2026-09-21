"""CRUD + query helpers for transactions. Every query is scoped by user_id."""
from __future__ import annotations

from datetime import date
from sqlalchemy import and_

from database.database import get_session
from database.models import Transaction

DEFAULT_CATEGORIES = [
    "Food", "Shopping", "Transport", "Education", "Entertainment", "Bills",
    "Healthcare", "Rent", "Travel", "Investments", "Salary", "Other",
]


def add_transaction(
    user_id: int, txn_date: date, description: str, category: str,
    amount: float, transaction_type: str, payment_method: str = "Other", notes: str = "",
) -> int:
    if transaction_type not in ("income", "expense"):
        raise ValueError("transaction_type must be 'income' or 'expense'")
    if amount <= 0:
        raise ValueError("amount must be greater than zero")

    with get_session() as session:
        txn = Transaction(
            user_id=user_id, date=txn_date, description=description.strip(),
            category=category, amount=float(amount), transaction_type=transaction_type,
            payment_method=payment_method, notes=notes,
        )
        session.add(txn)
        session.flush()
        return txn.id


def update_transaction(user_id: int, txn_id: int, **fields) -> bool:
    with get_session() as session:
        txn = session.query(Transaction).filter(
            and_(Transaction.id == txn_id, Transaction.user_id == user_id)
        ).first()
        if not txn:
            return False
        for key, value in fields.items():
            if hasattr(txn, key) and key not in ("id", "user_id"):
                setattr(txn, key, value)
        return True


def delete_transaction(user_id: int, txn_id: int) -> bool:
    with get_session() as session:
        txn = session.query(Transaction).filter(
            and_(Transaction.id == txn_id, Transaction.user_id == user_id)
        ).first()
        if not txn:
            return False
        session.delete(txn)
        return True


def get_transactions(
    user_id: int, start_date: date | None = None, end_date: date | None = None,
    category: str | None = None, transaction_type: str | None = None,
) -> list[dict]:
    with get_session() as session:
        query = session.query(Transaction).filter(Transaction.user_id == user_id)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        if category and category != "All":
            query = query.filter(Transaction.category == category)
        if transaction_type and transaction_type != "All":
            query = query.filter(Transaction.transaction_type == transaction_type)
        rows = query.order_by(Transaction.date.desc()).all()
        return [_to_dict(r) for r in rows]


def get_all_categories(user_id: int) -> list[str]:
    """Union of default categories and any custom categories the user has used."""
    with get_session() as session:
        used = {
            r[0] for r in session.query(Transaction.category)
            .filter(Transaction.user_id == user_id).distinct().all()
        }
    return sorted(set(DEFAULT_CATEGORIES) | used, key=lambda c: (c not in DEFAULT_CATEGORIES, c))


def _to_dict(txn: Transaction) -> dict:
    return {
        "id": txn.id, "date": txn.date, "description": txn.description,
        "category": txn.category, "amount": txn.amount,
        "transaction_type": txn.transaction_type,
        "payment_method": txn.payment_method, "notes": txn.notes,
    }
