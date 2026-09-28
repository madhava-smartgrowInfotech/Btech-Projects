from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .config import DATABASE_URL, DATA

DATA.mkdir(exist_ok=True)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20))  # engineer | manager
    password_hash: Mapped[str] = mapped_column(String(200))


class QualityCheck(Base):
    __tablename__ = "quality_checks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    user_email: Mapped[str] = mapped_column(String(120))
    sample_name: Mapped[str] = mapped_column(String(120))
    values: Mapped[dict] = mapped_column(JSON)
    potable: Mapped[bool] = mapped_column(Boolean)
    confidence: Mapped[float] = mapped_column(Float)
    exceeded: Mapped[int] = mapped_column(Integer, default=0)


class LeakEvent(Base):
    __tablename__ = "leak_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    pipe: Mapped[str] = mapped_column(String(20))
    zone: Mapped[str] = mapped_column(String(10))
    leak_lps: Mapped[float] = mapped_column(Float)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    detected: Mapped[bool] = mapped_column(Boolean)
    probability: Mapped[float] = mapped_column(Float)
    top_pipe: Mapped[str] = mapped_column(String(20))
    true_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result: Mapped[dict] = mapped_column(JSON)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    kind: Mapped[str] = mapped_column(String(20))  # leak | anomaly | imbalance | quality
    severity: Mapped[str] = mapped_column(String(10))  # high | medium | low
    zone: Mapped[str] = mapped_column(String(10), default="")
    title: Mapped[str] = mapped_column(String(200))
    detail: Mapped[str] = mapped_column(Text, default="")
    ref: Mapped[str] = mapped_column(String(80), default="", index=True)
    open: Mapped[bool] = mapped_column(Boolean, default=True)


DEMO_USERS = [
    ("engineer@aquavision.local", "Network Engineer", "engineer", "engineer123"),
    ("manager@aquavision.local", "Operations Manager", "manager", "manager123"),
]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from .auth import hash_password

    Base.metadata.create_all(engine)
    with Session(engine) as db:
        for email, name, role, pw in DEMO_USERS:
            if not db.scalar(select(User).where(User.email == email)):
                db.add(User(email=email, name=name, role=role, password_hash=hash_password(pw)))
        db.commit()


def add_alert(db, kind, severity, title, detail="", zone="", ref=""):
    """Create an alert unless an open one with the same ref exists."""
    if ref and db.scalar(select(Alert).where(Alert.ref == ref, Alert.open.is_(True))):
        return None
    a = Alert(kind=kind, severity=severity, title=title, detail=detail, zone=zone, ref=ref)
    db.add(a)
    db.commit()
    return a
