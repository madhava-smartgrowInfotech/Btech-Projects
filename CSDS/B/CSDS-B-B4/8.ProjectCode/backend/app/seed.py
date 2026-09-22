"""Clearly labelled sample data for the sandbox, loaded on first start.

Sample accounts are flagged ``is_sample`` and shown with a "Sample" badge in the app.
Everything is generated from a fixed seed so every fresh install looks the same.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import SavedPayee, TrustedContact, User
from app.services.accounts import create_account

log = get_logger("upi_guardian.seed")

SAMPLE_PASSWORD = "Guardian@123"
SAMPLE_PIN = "1234"
ADMIN_PASSWORD = "Admin@1234"

# (key, full name, phone, email, upi id, balance, role, merchant category, account age days)
ACCOUNTS = [
    ("demo", "Meera Sharma", "9000000001", "demo@upiguardian.app", "meera@upg", 85000, "user", None, 900),
    ("family", "Arjun Sharma", "9000000002", "family@upiguardian.app", "arjun@upg", 60000, "user", None, 1200),
    ("admin", "Fraud Risk Desk", "9000000009", "admin@upiguardian.app", "riskdesk@upg", 0, "admin", None, 1500),
    ("ravi", "Ravi Kumar", "9000000011", None, "ravi.kumar@upg", 42000, "user", None, 1100),
    ("priya", "Priya Sharma", "9000000012", None, "priya@upg", 38000, "user", None, 1300),
    ("grocery", "Lakshmi General Stores", "9000000021", None, "lakshmistores@upg", 120000, "user", "grocery", 1600),
    ("power", "Sunrise Power Bills", "9000000022", None, "sunrisepower@upg", 500000, "user", "utilities", 2000),
    ("tea", "Anand Tea Stall", "9000000023", None, "anandtea@upg", 15000, "user", "food", 700),
    ("pharmacy", "Care Plus Pharmacy", "9000000024", None, "careplus@upg", 90000, "user", "healthcare", 1000),
    ("vikram", "Vikram Rao", "9000000031", None, "vikram.4411@upg", 8000, "user", None, 12),
    ("kyc", "KYC Help Desk", "9000000041", None, "kyc.helpdesk@upg", 2000, "user", None, 2),
    ("refund", "Refund Desk", "9000000042", None, "refund.desk@upg", 1500, "user", None, 5),
    ("lucky", "Lucky Draw Rewards", "9000000043", None, "luckydraw.winner@upg", 500, "user", None, 1),
    ("cashback", "Cashback Offers", "9000000044", None, "cashback.offer@upg", 800, "user", None, 3),
] + [
    (f"community{i}", name, f"90000001{i:02d}", None, None, 30000, "user", None, age)
    for i, (name, age) in enumerate(
        [
            ("Kavya Reddy", 800), ("Suresh Babu", 1400), ("Anita Desai", 600), ("Farhan Ali", 950),
            ("Deepa Nair", 1250), ("Rahul Mehta", 400), ("Sneha Iyer", 1800), ("Imran Khan", 700),
            ("Pooja Gupta", 1000), ("Venkat Rao", 1500), ("Harish Patel", 300), ("Nisha Verma", 1100),
        ],
        start=1,
    )
]

SAVED_PAYEES = [
    ("demo", "ravi", "Ravi (friend)", "friend"),
    ("demo", "priya", "Priya (sister)", "family"),
    ("demo", "family", "Arjun (son)", "family"),
    ("demo", "grocery", "Lakshmi Stores", "shop"),
    ("demo", "power", "Electricity bill", "bill"),
    ("demo", "tea", "Anand Tea", "shop"),
    ("demo", "pharmacy", "Care Plus Pharmacy", "shop"),
    ("family", "demo", "Mom", "family"),
]


def seed_if_empty(db: Session) -> bool:
    if db.scalar(select(func.count(User.id))) > 0:
        return False
    from datetime import timedelta

    from app.models import utcnow

    from app.core.security import hash_secret

    hashes = {"user": hash_secret(SAMPLE_PASSWORD), "admin": hash_secret(ADMIN_PASSWORD), "pin": hash_secret(SAMPLE_PIN)}
    users: dict[str, User] = {}
    for key, name, phone, email, upi, balance, role, category, age_days in ACCOUNTS:
        user = create_account(
            db,
            full_name=name,
            phone=phone,
            email=email,
            password="",
            pin="",
            password_hash=hashes[role],
            pin_hash=hashes["pin"],
            role=role,
            is_sample=True,
            balance_rupees=balance,
            upi_id=upi,
            is_merchant=category is not None,
            merchant_category=category,
        )
        created = utcnow() - timedelta(days=age_days)
        user.created_at = created
        user.wallet.created_at = created
        users[key] = user

    for owner, payee, nickname, relation in SAVED_PAYEES:
        db.add(
            SavedPayee(
                user_id=users[owner].id,
                payee_wallet_id=users[payee].wallet.id,
                nickname=nickname,
                relation=relation,
                created_at=users[owner].created_at + timedelta(days=30),
            )
        )
    db.add(TrustedContact(user_id=users["demo"].id, contact_user_id=users["family"].id, relation="son", can_approve=True))
    db.flush()

    from app.ml.registry import registry

    if registry.available("behaviour") and registry.available("risk"):
        from app.services.sample_activity import generate_sample_activity

        generate_sample_activity(db, users)
    else:
        log.warning("models missing - sample activity skipped (run ml/train_all.py, then reset the sandbox)")
    log.info("sample data loaded", extra={"accounts": len(users)})
    return True
