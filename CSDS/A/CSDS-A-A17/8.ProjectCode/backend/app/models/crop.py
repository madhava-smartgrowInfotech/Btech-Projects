from datetime import datetime, timezone

from sqlalchemy import String, Float, ForeignKey, DateTime, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CropListing(Base):
    __tablename__ = "crop_listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    crop_type: Mapped[str] = mapped_column(String(60))
    region: Mapped[str] = mapped_column(String(120))
    quantity_kg: Mapped[float] = mapped_column(default=0)
    image_path: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(String(30), default="draft")  # draft | listed | sold
    asking_price: Mapped[float] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    farmer = relationship("User", back_populates="listings", foreign_keys=[farmer_id])
    quality_grade = relationship("QualityGrade", back_populates="listing", uselist=False)


class QualityGrade(Base):
    __tablename__ = "quality_grades"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("crop_listings.id"))
    grade: Mapped[str] = mapped_column(String(10))  # A | B | C | Reject
    confidence: Mapped[float] = mapped_column(default=0)
    probabilities: Mapped[dict] = mapped_column(JSON, default=dict)
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    shap_explanation: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    listing = relationship("CropListing", back_populates="quality_grade")
