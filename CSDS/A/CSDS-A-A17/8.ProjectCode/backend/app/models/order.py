from datetime import datetime, timezone

from sqlalchemy import String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("crop_listings.id"))
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    distributor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    quantity_kg: Mapped[float] = mapped_column(default=0)
    agreed_price: Mapped[float] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(30), default="placed")  # placed|confirmed|in_transit|delivered|cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
