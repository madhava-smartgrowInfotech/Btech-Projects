from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from .config import DATABASE_PATH

DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(f"sqlite:///{DATABASE_PATH}", connect_args={"check_same_thread": False, "timeout": 30})


@event.listens_for(engine, "connect")
def _sqlite_pragmas(conn, _):
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20))  # citizen | officer | admin
    department: Mapped[str | None] = mapped_column(String(60), nullable=True)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)
    sla_days: Mapped[int] = mapped_column(Integer)


class Ward(Base):
    __tablename__ = "wards"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)


class Complaint(Base):
    __tablename__ = "complaints"
    id: Mapped[int] = mapped_column(primary_key=True)
    tracking_id: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    citizen_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(12))
    photo: Mapped[str | None] = mapped_column(String(80), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    ward_id: Mapped[int | None] = mapped_column(ForeignKey("wards.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Submitted", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # AI suggestion (category, department, priority, expected_days, explanations, ...)
    ai: Mapped[dict] = mapped_column(JSON, default=dict)
    extraction: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    extraction_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|done|failed|not_requested
    # officer's final decision
    final_category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    final_department: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    final_priority: Mapped[str | None] = mapped_column(String(12), nullable=True)
    final_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)

    ward = relationship("Ward")
    citizen = relationship("User", foreign_keys=[citizen_id])
    events = relationship("Event", order_by="Event.created_at", cascade="all, delete-orphan")


class Event(Base):
    """Status timeline entries and replies to the citizen."""
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(primary_key=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20))  # status | reply | decision | note
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    message: Mapped[str] = mapped_column(Text, default="")
    public: Mapped[bool] = mapped_column(Boolean, default=True)  # visible to the citizen
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Feedback(Base):
    """Officer accept / override of one AI suggestion - overrides become training labels."""
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(primary_key=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), index=True)
    field: Mapped[str] = mapped_column(String(20))  # category | department | priority
    ai_value: Mapped[str] = mapped_column(String(60))
    officer_value: Mapped[str] = mapped_column(String(60))
    action: Mapped[str] = mapped_column(String(10))  # accept | override
    reason: Mapped[str] = mapped_column(Text, default="")
    officer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    model_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ModelRun(Base):
    __tablename__ = "model_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[int] = mapped_column(Integer)
    labels_used: Mapped[int] = mapped_column(Integer, default=0)
    metrics: Mapped[dict] = mapped_column(JSON)
    triggered_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(engine)
