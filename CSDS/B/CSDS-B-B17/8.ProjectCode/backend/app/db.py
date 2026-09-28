from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from .config import DATA_DIR, DATABASE_URL

DATA_DIR.mkdir(parents=True, exist_ok=True)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20))  # supervisor | agent
    password_hash: Mapped[str] = mapped_column(String(100))


class Call(Base):
    __tablename__ = "calls"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    audio_path: Mapped[str] = mapped_column(String(400))
    source: Mapped[str] = mapped_column(String(20), default="upload")  # upload | microphone | sample
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
    agent_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued | processing | done | failed
    stage: Mapped[str] = mapped_column(String(80), default="")
    error: Mapped[str] = mapped_column(Text, default="")
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    channels: Mapped[int | None] = mapped_column(Integer, nullable=True)
    segments: Mapped[list | None] = mapped_column(JSON, nullable=True)
    transcript_text: Mapped[str] = mapped_column(Text, default="")
    intent: Mapped[str | None] = mapped_column(String(60), nullable=True)
    intent_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    intent_top: Mapped[list | None] = mapped_column(JSON, nullable=True)
    topic: Mapped[str | None] = mapped_column(String(60), nullable=True)
    keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    sentiment: Mapped[float | None] = mapped_column(Float, nullable=True)  # mean customer sentiment, -1..1
    sentiment_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    flags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    summary_error: Mapped[str] = mapped_column(Text, default="")
    scorecard: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reference: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # sample calls: script lines + intent
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    agent: Mapped[User | None] = relationship(foreign_keys=[agent_id])


def init_db():
    Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
