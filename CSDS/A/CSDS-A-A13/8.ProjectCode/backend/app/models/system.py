"""Import history, audit trail and stored settings."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._common import utcnow


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))
    filename: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20))
    rows_total: Mapped[int] = mapped_column(Integer, default=0)
    rows_valid: Mapped[int] = mapped_column(Integer, default=0)
    report: Mapped[dict] = mapped_column(JSON, default=dict)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), default=None)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    committed_at: Mapped[datetime | None] = mapped_column(default=None)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    at: Mapped[datetime] = mapped_column(default=utcnow, index=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), default=None)
    action: Mapped[str] = mapped_column(String(40), index=True)
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("plans.id", ondelete="SET NULL"), default=None, index=True)
    summary: Mapped[str] = mapped_column(String(300), default="")
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class AppSetting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)
