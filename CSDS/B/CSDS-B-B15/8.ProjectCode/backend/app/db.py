from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import DB_URL

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Hospital(Base):
    __tablename__ = "hospitals"
    id: Mapped[int] = mapped_column(primary_key=True)
    osm_id: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(200))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    address: Mapped[str] = mapped_column(String(300), default="")
    ownership: Mapped[str] = mapped_column(String(20), default="private")
    specialties: Mapped[str] = mapped_column(Text, default="")  # comma separated
    has_emergency: Mapped[bool] = mapped_column(Boolean, default=False)
    op_limit: Mapped[int] = mapped_column(Integer, default=60)
    emergency_quota: Mapped[int] = mapped_column(Integer, default=6)
    avg_consult_min: Mapped[float] = mapped_column(Float, default=4.0)
    op_start: Mapped[str] = mapped_column(String(5), default="09:00")

    def specialty_list(self):
        return [s for s in self.specialties.split(",") if s]


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(10))  # patient | staff | admin
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey("hospitals.id"), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(1), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)


class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[int] = mapped_column(primary_key=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"), index=True)
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    patient_name: Mapped[str] = mapped_column(String(120))
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(1), nullable=True)
    date: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    requested_date: Mapped[str] = mapped_column(String(10))
    token: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(10), default="op")  # op | emergency
    uses_quota: Mapped[bool] = mapped_column(Boolean, default=False)  # counted against emergency quota
    severity: Mapped[str] = mapped_column(String(10))
    priority: Mapped[int] = mapped_column(Integer)  # 0 = first
    symptoms: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    condition: Mapped[str] = mapped_column(String(80), default="")
    specialty: Mapped[str] = mapped_column(String(40), default="")
    noshow_prob: Mapped[float] = mapped_column(Float, default=0.2)
    status: Mapped[str] = mapped_column(String(12), default="waiting")  # waiting|called|done|no_show|referred
    notes: Mapped[str] = mapped_column(Text, default="")
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
    referral_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    called_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Referral(Base):
    __tablename__ = "referrals"
    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"))
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    patient_name: Mapped[str] = mapped_column(String(120))
    from_hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"))
    to_hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"))
    specialty: Mapped[str] = mapped_column(String(40))
    reason: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text)  # JSON clinical summary shared after consent
    consent: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending_consent")
    # pending_consent -> sent -> accepted -> completed  (or declined)
    new_booking_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(engine)
