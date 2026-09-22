"""Database tables (SQLAlchemy 2.x typed mappings)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, TypeDecorator, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

IST = timezone(timedelta(hours=5, minutes=30))


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """Stores naive UTC in SQLite and always returns timezone-aware UTC datetimes."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(80))
    phone: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    pin_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(10), default="user")  # user | admin
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    wallet: Mapped["Wallet"] = relationship(back_populates="user", uselist=False)
    settings: Mapped["UserSettings"] = relationship(back_populates="user", uselist=False)


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    upi_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(80))
    balance_paise: Mapped[int] = mapped_column(Integer, default=0)
    is_merchant: Mapped[bool] = mapped_column(Boolean, default=False)
    merchant_category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    user: Mapped[User] = relationship(back_populates="wallet")


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    language: Mapped[str] = mapped_column(String(2), default="en")  # en | hi | te
    voice_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_speak: Mapped[bool] = mapped_column(Boolean, default=True)
    hold_minutes: Mapped[int] = mapped_column(Integer, default=30)
    trusted_approval_required: Mapped[bool] = mapped_column(Boolean, default=False)
    sandbox_clock: Mapped[str | None] = mapped_column(String(5), nullable=True)  # "HH:MM" or None

    user: Mapped[User] = relationship(back_populates="settings")


class SavedPayee(Base):
    __tablename__ = "saved_payees"
    __table_args__ = (UniqueConstraint("user_id", "payee_wallet_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    payee_wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id", ondelete="CASCADE"))
    nickname: Mapped[str] = mapped_column(String(80))
    relation: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    payee_wallet: Mapped[Wallet] = relationship()


class Transaction(Base):
    """A sandbox payment. Status flow: draft -> completed | held -> released(completed) | cancelled ..."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    payer_wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"), index=True)
    payee_wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"), index=True)
    amount_paise: Mapped[int] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(String(140), nullable=True)
    channel: Mapped[str] = mapped_column(String(10), default="send")  # send | qr | collect
    status: Mapped[str] = mapped_column(String(12), default="draft", index=True)
    device_type: Mapped[str] = mapped_column(String(10), default="mobile")
    geo_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    geo_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    local_time_used: Mapped[str | None] = mapped_column(String(5), nullable=True)
    collect_request_id: Mapped[int | None] = mapped_column(ForeignKey("collect_requests.id"), nullable=True)
    qr_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_reason: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    payer_wallet: Mapped[Wallet] = relationship(foreign_keys=[payer_wallet_id])
    payee_wallet: Mapped[Wallet] = relationship(foreign_keys=[payee_wallet_id])
    assessment: Mapped["RiskAssessment | None"] = relationship(back_populates="transaction", uselist=False)
    hold: Mapped["Hold | None"] = relationship(back_populates="transaction", uselist=False)
    intent: Mapped["IntentCheck | None"] = relationship(back_populates="transaction", uselist=False)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id", ondelete="CASCADE"), unique=True)
    model_version: Mapped[str] = mapped_column(String(60))
    behaviour_score: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[int] = mapped_column(Integer, index=True)
    level: Mapped[str] = mapped_column(String(8), index=True)  # low | medium | high
    final_level: Mapped[str] = mapped_column(String(8))
    action: Mapped[str] = mapped_column(String(8))  # pay | verify | hold | block
    payee_trust: Mapped[int] = mapped_column(Integer)
    features: Mapped[dict[str, Any]] = mapped_column(JSON)
    contributions: Mapped[dict[str, Any]] = mapped_column(JSON)
    reasons: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    guard: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    transaction: Mapped[Transaction] = relationship(back_populates="assessment")


class IntentCheck(Base):
    __tablename__ = "intent_checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id", ondelete="CASCADE"), unique=True)
    purpose: Mapped[str] = mapped_column(String(20))
    answers: Mapped[dict[str, Any]] = mapped_column(JSON)
    matched_scam_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    transaction: Mapped[Transaction] = relationship(back_populates="intent")


class Hold(Base):
    __tablename__ = "holds"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id", ondelete="CASCADE"), unique=True)
    status: Mapped[str] = mapped_column(String(10), default="active", index=True)  # active|released|cancelled|rejected|expired
    hold_minutes: Mapped[int] = mapped_column(Integer)
    hold_until: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    needs_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approval_status: Mapped[str] = mapped_column(String(10), default="none")  # none|pending|approved|rejected
    approver_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    transaction: Mapped[Transaction] = relationship(back_populates="hold")


class CollectRequest(Base):
    __tablename__ = "collect_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"), index=True)
    payer_wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"), index=True)
    amount_paise: Mapped[int] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(String(140), nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="pending", index=True)
    guard: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    requester_wallet: Mapped[Wallet] = relationship(foreign_keys=[requester_wallet_id])
    payer_wallet: Mapped[Wallet] = relationship(foreign_keys=[payer_wallet_id])


class SmsCheck(Base):
    __tablename__ = "sms_checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(2))
    probability: Mapped[float] = mapped_column(Float)
    verdict: Mapped[str] = mapped_column(String(10), index=True)  # safe | suspicious | scam
    scam_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    highlights: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    entities: Mapped[dict[str, Any]] = mapped_column(JSON)
    signals: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)


class ScamReport(Base):
    __tablename__ = "scam_reports"
    __table_args__ = (UniqueConstraint("reporter_user_id", "upi_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    upi_id: Mapped[str] = mapped_column(String(80), index=True)
    category: Mapped[str] = mapped_column(String(30))
    note: Mapped[str | None] = mapped_column(String(280), nullable=True)
    source: Mapped[str] = mapped_column(String(10), default="manual")  # manual | sms | payment | collect
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class TrustedContact(Base):
    __tablename__ = "trusted_contacts"
    __table_args__ = (UniqueConstraint("user_id", "contact_user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    contact_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    relation: Mapped[str | None] = mapped_column(String(30), nullable=True)
    can_approve: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    contact: Mapped[User] = relationship(foreign_keys=[contact_user_id])
    owner: Mapped[User] = relationship(foreign_keys=[user_id])


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    read_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)


class FailedAttempt(Base):
    __tablename__ = "failed_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    reason: Mapped[str] = mapped_column(String(20))  # wrong_pin | insufficient_funds
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)


class AppSetting(Base):
    """Global settings changed by admins (for example the risk policy thresholds)."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)
