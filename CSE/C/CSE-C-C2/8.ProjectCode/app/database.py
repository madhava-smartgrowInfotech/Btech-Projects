"""StoryVox SQLite database setup."""
from __future__ import annotations

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

Base = declarative_base()
_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        db_path = settings.resolved_db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _SessionLocal


def init_db() -> None:
    from app import models as _models  # noqa: F401  (register tables)

    Base.metadata.create_all(bind=get_engine())
    settings = get_settings()
    settings.resolved_audio_dir.mkdir(parents=True, exist_ok=True)
    settings.resolved_eval_dir.mkdir(parents=True, exist_ok=True)
    settings.resolved_dataset_dir.mkdir(parents=True, exist_ok=True)


def reset_engine() -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
