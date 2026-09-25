from datetime import datetime, timezone

from sqlalchemy import ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DeliveryRecommendation(Base):
    __tablename__ = "delivery_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("crop_listings.id"))
    ranked_buyers: Mapped[dict] = mapped_column(JSON, default=dict)
    best_route: Mapped[dict] = mapped_column(JSON, default=dict)
    best_sell_day: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
