from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base, utcnow


class ZoneState(Base):
    """Live state of one H3 hexagon for one operator, updated as readings arrive."""
    __tablename__ = "zone_states"

    h3_cell: Mapped[str] = mapped_column(String(20), primary_key=True)
    operator: Mapped[str] = mapped_column(String(80), primary_key=True)
    label: Mapped[str | None] = mapped_column(String(10), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    readings_window: Mapped[int] = mapped_column(Integer, default=0)
    bad_share: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_rsrp: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_latency: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_dl: Mapped[float | None] = mapped_column(Float, nullable=True)
    first_bad_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_reading_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    open_complaint_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
