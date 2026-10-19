"""StoryVox SQLAlchemy models."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Story(Base):
    __tablename__ = "stories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False, default="Untitled Story")
    story_text: Mapped[str] = mapped_column(Text, nullable=False)
    language_code: Mapped[str] = mapped_column(String(16), nullable=False)
    language_name: Mapped[str] = mapped_column(String(64), nullable=False)
    style: Mapped[str] = mapped_column(String(64), nullable=False, default="Adventure")
    length_option: Mapped[str] = mapped_column(String(16), nullable=False, default="Short")
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow, nullable=False)
    generation_time_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    audio_outputs: Mapped[list["AudioOutput"]] = relationship(
        "AudioOutput", back_populates="story", cascade="all, delete-orphan"
    )


class AudioOutput(Base):
    __tablename__ = "audio_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sample_rate: Mapped[int] = mapped_column(Integer, nullable=False, default=16000)
    tts_model: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    synthesis_time_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rtf: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow, nullable=False)

    story: Mapped[Story] = relationship("Story", back_populates="audio_outputs")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    language_code: Mapped[str] = mapped_column(String(16), nullable=False, default="mixed")
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metrics_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow, nullable=False)
