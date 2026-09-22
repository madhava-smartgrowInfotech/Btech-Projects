"""Creating users with their sandbox wallet and default settings."""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_secret
from app.models import User, UserSettings, Wallet

UPI_HANDLE = "upg"


def make_upi_id(db: Session, full_name: str, phone: str) -> str:
    first = re.sub(r"[^a-z]", "", full_name.split()[0].lower()) or "user"
    base = f"{first[:14]}.{phone[-4:]}"
    candidate = f"{base}@{UPI_HANDLE}"
    n = 1
    while db.scalar(select(Wallet.id).where(Wallet.upi_id == candidate)) is not None:
        n += 1
        candidate = f"{base}{n}@{UPI_HANDLE}"
    return candidate


def create_account(
    db: Session,
    *,
    full_name: str,
    phone: str,
    password: str,
    pin: str,
    email: str | None = None,
    language: str = "en",
    role: str = "user",
    is_sample: bool = False,
    balance_rupees: int | None = None,
    upi_id: str | None = None,
    is_merchant: bool = False,
    merchant_category: str | None = None,
    display_name: str | None = None,
    password_hash: str | None = None,
    pin_hash: str | None = None,
) -> User:
    settings = get_settings()
    user = User(
        full_name=full_name,
        phone=phone,
        email=email.lower() if email else None,
        password_hash=password_hash or hash_secret(password),
        pin_hash=pin_hash or hash_secret(pin),
        role=role,
        is_sample=is_sample,
    )
    db.add(user)
    db.flush()
    wallet = Wallet(
        user_id=user.id,
        upi_id=upi_id or make_upi_id(db, full_name, phone),
        display_name=display_name or full_name,
        balance_paise=(settings.sandbox_start_balance if balance_rupees is None else balance_rupees) * 100,
        is_merchant=is_merchant,
        merchant_category=merchant_category,
    )
    db.add(wallet)
    db.add(
        UserSettings(
            user_id=user.id,
            language=language,
            hold_minutes=settings.hold_minutes_default,
        )
    )
    db.flush()
    return user


def me_payload(user: User) -> dict:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "phone": user.phone,
        "email": user.email,
        "role": user.role,
        "is_sample": user.is_sample,
        "upi_id": user.wallet.upi_id,
        "balance": user.wallet.balance_paise / 100,
        "language": user.settings.language if user.settings else "en",
        "created_at": user.created_at,
    }
