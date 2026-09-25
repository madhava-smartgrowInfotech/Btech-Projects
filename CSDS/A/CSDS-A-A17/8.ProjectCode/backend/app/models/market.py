from datetime import datetime, timezone

from sqlalchemy import String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Town(Base):
    __tablename__ = "towns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    region: Mapped[str] = mapped_column(String(120))
    lat: Mapped[float] = mapped_column(default=0)
    lon: Mapped[float] = mapped_column(default=0)
    is_market: Mapped[bool] = mapped_column(default=True)


class PricePrediction(Base):
    __tablename__ = "price_predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("crop_listings.id"), nullable=True)
    crop_type: Mapped[str] = mapped_column(String(60))
    region: Mapped[str] = mapped_column(String(120))
    grade: Mapped[str] = mapped_column(String(10))
    current_price: Mapped[float] = mapped_column(default=0)
    confidence_low: Mapped[float] = mapped_column(default=0)
    confidence_high: Mapped[float] = mapped_column(default=0)
    forecast: Mapped[dict] = mapped_column(JSON, default=dict)  # {day_offset: price}
    shap_explanation: Mapped[dict] = mapped_column(JSON, default=dict)
    best_sell_day: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
