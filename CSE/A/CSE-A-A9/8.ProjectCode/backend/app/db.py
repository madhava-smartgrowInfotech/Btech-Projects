"""SQLite storage: users, moderator decisions and retraining runs."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from .settings import DATABASE_URL


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20))          # analyst | moderator
    password_hash: Mapped[str] = mapped_column(String(80))


class Review(Base):
    """One moderator decision on an account or a whole botnet cluster."""
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    target_type: Mapped[str] = mapped_column(String(10), index=True)      # account | cluster
    target_id: Mapped[str] = mapped_column(String(32), index=True)
    decision: Mapped[str] = mapped_column(String(10))                      # confirm | dismiss
    note: Mapped[str] = mapped_column(Text, default="")
    score: Mapped[float] = mapped_column(default=0.0)                      # model score when decided
    members: Mapped[list] = mapped_column(JSON, default=list)              # account ids affected
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    used_in_run: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user: Mapped[User] = relationship()


class TrainingRun(Base):
    __tablename__ = "training_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(12), default="running")     # running | done | error
    feedback_labels: Mapped[int] = mapped_column(Integer, default=0)
    best: Mapped[str] = mapped_column(String(12), default="")
    f1_before: Mapped[dict] = mapped_column(JSON, default=dict)
    f1_after: Mapped[dict] = mapped_column(JSON, default=dict)
    message: Mapped[str] = mapped_column(Text, default="")
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


if DATABASE_URL.startswith("sqlite:///"):
    Path(DATABASE_URL[len("sqlite:///"):]).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})


@event.listens_for(engine, "connect")
def _sqlite_pragmas(dbapi_conn, _):
    if DATABASE_URL.startswith("sqlite"):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(engine)
