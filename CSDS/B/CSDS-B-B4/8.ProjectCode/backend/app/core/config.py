"""Application settings, read once from the project's .env file."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT_DIR / "backend"
DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = ROOT_DIR / "models"
EXPERIMENTS_DIR = ROOT_DIR / "experiments"
ASSETS_DIR = BACKEND_DIR / "app" / "assets"

load_dotenv(ROOT_DIR / ".env")


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    value = os.getenv(name)
    try:
        return int(value) if value not in (None, "") else default
    except ValueError:
        return default


def _path(name: str, default: str) -> Path:
    raw = os.getenv(name) or default
    path = Path(raw)
    return path if path.is_absolute() else ROOT_DIR / path


@dataclass(frozen=True)
class Settings:
    api_host: str = field(default_factory=lambda: os.getenv("API_HOST", "127.0.0.1"))
    api_port: int = field(default_factory=lambda: _int("API_PORT", 8204))
    frontend_port: int = field(default_factory=lambda: _int("FRONTEND_PORT", 5204))
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            o.strip()
            for o in os.getenv("CORS_ORIGINS", "http://localhost:5204,http://127.0.0.1:5204").split(",")
            if o.strip()
        )
    )
    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET", ""))
    jwt_expire_minutes: int = field(default_factory=lambda: _int("JWT_EXPIRE_MINUTES", 720))
    database_path: Path = field(default_factory=lambda: _path("DATABASE_PATH", "data/app.db"))
    seed_sample_data: bool = field(default_factory=lambda: _bool("SEED_SAMPLE_DATA", True))
    sandbox_start_balance: int = field(default_factory=lambda: _int("SANDBOX_START_BALANCE", 50000))
    risk_medium_threshold: int = field(default_factory=lambda: _int("RISK_MEDIUM_THRESHOLD", 35))
    risk_high_threshold: int = field(default_factory=lambda: _int("RISK_HIGH_THRESHOLD", 70))
    hold_minutes_default: int = field(default_factory=lambda: _int("HOLD_MINUTES_DEFAULT", 30))
    hold_check_seconds: int = field(default_factory=lambda: _int("HOLD_CHECK_SECONDS", 5))
    tts_enabled: bool = field(default_factory=lambda: _bool("TTS_ENABLED", True))
    voice_cache_dir: Path = field(default_factory=lambda: _path("VOICE_CACHE_DIR", "data/voice_cache"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path.as_posix()}"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.jwt_secret or settings.jwt_secret.startswith("change-me"):
        raise RuntimeError(
            "JWT_SECRET is not set. Run setup.bat (it creates .env with a random secret) "
            "or set JWT_SECRET in .env yourself."
        )
    return settings
