import json
from datetime import datetime

from sqlalchemy import (Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import DB_PATH

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def now():
    return datetime.utcnow()


def jdump(v):
    return json.dumps(v)


def jload(v, default=None):
    if not v:
        return default
    try:
        return json.loads(v)
    except ValueError:
        return default


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20))  # candidate | recruiter | career | expert
    level: Mapped[int] = mapped_column(Integer, default=1)
    rating: Mapped[int] = mapped_column(Integer, default=1200)
    job_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    target_role: Mapped[str] = mapped_column(String(80), default="")
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), index=True)  # aptitude | technical
    topic: Mapped[str] = mapped_column(String(60), index=True)
    difficulty: Mapped[str] = mapped_column(String(10))
    text: Mapped[str] = mapped_column(Text)
    options: Mapped[str] = mapped_column(Text)  # json list
    answer: Mapped[int] = mapped_column(Integer)
    explanation: Mapped[str] = mapped_column(Text, default="")
    ai_explanation: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(80), default="")


class TestAttempt(Base):
    __tablename__ = "test_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    topic: Mapped[str] = mapped_column(String(60))
    difficulty: Mapped[str] = mapped_column(String(10))
    question_ids: Mapped[str] = mapped_column(Text)
    time_limit_sec: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total: Mapped[int] = mapped_column(Integer, default=0)
    correct: Mapped[int] = mapped_column(Integer, default=0)
    score_pct: Mapped[float] = mapped_column(Float, default=0)


class AnswerLog(Base):
    __tablename__ = "answer_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("test_attempts.id"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    kind: Mapped[str] = mapped_column(String(20))
    topic: Mapped[str] = mapped_column(String(60), index=True)
    chosen: Mapped[int] = mapped_column(Integer, default=-1)
    correct: Mapped[bool] = mapped_column(Boolean, default=False)


class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    problem_slug: Mapped[str] = mapped_column(String(60), index=True)
    language: Mapped[str] = mapped_column(String(10))
    code: Mapped[str] = mapped_column(Text)
    verdict: Mapped[str] = mapped_column(String(30))
    passed: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    time_ms: Mapped[int] = mapped_column(Integer, default=0)
    detail: Mapped[str] = mapped_column(Text, default="")
    contest_id: Mapped[int | None] = mapped_column(ForeignKey("contests.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Contest(Base):
    __tablename__ = "contests"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    start_at: Mapped[datetime] = mapped_column(DateTime)
    end_at: Mapped[datetime] = mapped_column(DateTime)
    problem_slugs: Mapped[str] = mapped_column(Text)  # json list
    rated: Mapped[bool] = mapped_column(Boolean, default=False)  # ratings applied
    rating_changes: Mapped[str] = mapped_column(Text, default="")  # json {user_id: delta}


class Interview(Base):
    __tablename__ = "interviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(10))  # ai | expert
    role: Mapped[str] = mapped_column(String(80))
    level: Mapped[str] = mapped_column(String(20), default="Entry")
    questions: Mapped[str] = mapped_column(Text, default="[]")
    answers: Mapped[str] = mapped_column(Text, default="[]")
    report: Mapped[str] = mapped_column(Text, default="")
    score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0..10
    status: Mapped[str] = mapped_column(String(20), default="in_progress")  # in_progress|completed|requested|scheduled
    expert_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Resume(Base):
    __tablename__ = "resumes"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    filename: Mapped[str] = mapped_column(String(200))
    text: Mapped[str] = mapped_column(Text)
    target_role: Mapped[str] = mapped_column(String(80))
    predicted_role: Mapped[str] = mapped_column(String(80))
    ats_score: Mapped[float] = mapped_column(Float)
    skills: Mapped[str] = mapped_column(Text)  # json list
    report: Mapped[str] = mapped_column(Text)  # json
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Drive(Base):
    __tablename__ = "drives"
    id: Mapped[int] = mapped_column(primary_key=True)
    recruiter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    company: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(80))
    min_level: Mapped[int] = mapped_column(Integer, default=1)
    required_skills: Mapped[str] = mapped_column(Text, default="[]")
    min_readiness: Mapped[float] = mapped_column(Float, default=0)
    min_aptitude: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Application(Base):
    __tablename__ = "applications"
    id: Mapped[int] = mapped_column(primary_key=True)
    drive_id: Mapped[int] = mapped_column(ForeignKey("drives.id"), index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    rank: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0)
    evidence: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(20), default="shortlisted")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(engine)
