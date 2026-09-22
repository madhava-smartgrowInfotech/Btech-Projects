"""Sandbox money movement. Balances are integer paise; no real money ever moves."""
from __future__ import annotations

import secrets
from datetime import datetime

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import api_error
from app.models import FailedAttempt, Transaction, Wallet, utcnow


def new_reference(db: Session) -> str:
    while True:
        ref = f"{utcnow():%y%m%d}{secrets.randbelow(10**6):06d}"
        if db.scalar(select(Transaction.id).where(Transaction.reference == ref)) is None:
            return ref


def _lock_wallet(db: Session, wallet_id: int) -> Wallet:
    wallet = db.get(Wallet, wallet_id, populate_existing=True)
    if wallet is None:
        raise api_error(status.HTTP_404_NOT_FOUND, "wallet_not_found", "Wallet not found.")
    return wallet


def debit_payer(db: Session, txn: Transaction) -> None:
    payer = _lock_wallet(db, txn.payer_wallet_id)
    if payer.balance_paise < txn.amount_paise:
        db.add(FailedAttempt(user_id=payer.user_id, reason="insufficient_funds"))
        db.commit()
        raise api_error(status.HTTP_400_BAD_REQUEST, "insufficient_funds", "Not enough balance in your sandbox wallet.")
    payer.balance_paise -= txn.amount_paise


def credit_payee(db: Session, txn: Transaction, when: datetime | None = None) -> None:
    payee = _lock_wallet(db, txn.payee_wallet_id)
    payee.balance_paise += txn.amount_paise
    txn.status = "completed"
    txn.completed_at = when or utcnow()


def refund_payer(db: Session, txn: Transaction, new_status: str, reason: str) -> None:
    payer = _lock_wallet(db, txn.payer_wallet_id)
    payer.balance_paise += txn.amount_paise
    txn.status = new_status
    txn.status_reason = reason
    txn.completed_at = utcnow()


def pay_now(db: Session, txn: Transaction) -> None:
    debit_payer(db, txn)
    credit_payee(db, txn)


def reserve_for_hold(db: Session, txn: Transaction) -> None:
    """Money leaves the payer's balance but reaches the payee only when the hold is released."""
    debit_payer(db, txn)
    txn.status = "held"
