from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, utcnow


class Translation(Base):
    """Cached translation of generated content (Policy Card, risks) into an answer language."""

    __tablename__ = "translations"
    __table_args__ = (UniqueConstraint("source_type", "source_key", "language", name="uq_translation"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_type: Mapped[str] = mapped_column(String(30))  # card | risks
    source_key: Mapped[str] = mapped_column(String(100))  # e.g. "<document id>:<content hash>"
    language: Mapped[str] = mapped_column(String(8))
    content: Mapped[dict[str, Any]] = mapped_column(JSON)
    model: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
