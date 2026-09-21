from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, utcnow


class Comparison(Base):
    __tablename__ = "comparisons"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    policy_a_id: Mapped[int] = mapped_column(ForeignKey("policies.id", ondelete="CASCADE"))
    policy_b_id: Mapped[int] = mapped_column(ForeignKey("policies.id", ondelete="CASCADE"))
    language: Mapped[str] = mapped_column(String(8), default="en")
    result: Mapped[dict[str, Any]] = mapped_column(JSON)
    model: Mapped[str | None] = mapped_column(String(80))
    total_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
