"""Application settings, read once from the root .env file."""
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
LOGS_DIR = ROOT_DIR / "logs"
ASSETS_DIR = BACKEND_DIR / "app" / "assets"

load_dotenv(ROOT_DIR / ".env", override=False)


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None or value == "" else value.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    return int(value) if value else default


def _float(name: str) -> float | None:
    value = os.getenv(name, "").strip()
    return float(value) if value else None


def _database_url(raw: str) -> str:
    prefix = "sqlite:///"
    if raw.startswith(prefix) and not raw.startswith(prefix + "/") and ":" not in raw[len(prefix):]:
        path = ROOT_DIR / raw[len(prefix):]
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"{prefix}{path.as_posix()}"
    return raw


@dataclass(frozen=True)
class Settings:
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    api_host: str = field(default_factory=lambda: os.getenv("API_HOST", "127.0.0.1"))
    api_port: int = field(default_factory=lambda: _int("API_PORT", 8113))
    web_port: int = field(default_factory=lambda: _int("WEB_PORT", 5113))
    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET", ""))
    jwt_expire_minutes: int = field(default_factory=lambda: _int("JWT_EXPIRE_MINUTES", 720))
    database_url: str = field(default_factory=lambda: _database_url(os.getenv("DATABASE_URL", "sqlite:///data/app.db")))
    cors_origins: tuple[str, ...] = field(default_factory=lambda: tuple(
        o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5113,http://127.0.0.1:5113").split(",") if o.strip()))
    public_base_url: str = field(default_factory=lambda: os.getenv("PUBLIC_BASE_URL", "http://localhost:5113").rstrip("/"))
    seed_demo_users: bool = field(default_factory=lambda: _bool("SEED_DEMO_USERS", True))
    demo_admin_email: str = field(default_factory=lambda: os.getenv("DEMO_ADMIN_EMAIL", "admin@seatwise.local"))
    demo_invigilator_email: str = field(default_factory=lambda: os.getenv("DEMO_INVIGILATOR_EMAIL", "invigilator@seatwise.local"))
    demo_password: str = field(default_factory=lambda: os.getenv("DEMO_PASSWORD", "SeatWise@2026"))
    solver_threads: int = field(default_factory=lambda: _int("SOLVER_THREADS", 0))
    solver_hall_budget: float | None = field(default_factory=lambda: _float("SOLVER_HALL_BUDGET"))
    solver_max_retries: int = field(default_factory=lambda: _int("SOLVER_MAX_RETRIES", 5))
    lookup_rate_limit_per_minute: int = field(default_factory=lambda: _int("LOOKUP_RATE_LIMIT_PER_MINUTE", 30))

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if len(settings.jwt_secret) < 32 or settings.jwt_secret.startswith("change-me"):
        raise RuntimeError("JWT_SECRET in .env is missing or too short. Run setup.bat to generate one.")
    return settings
