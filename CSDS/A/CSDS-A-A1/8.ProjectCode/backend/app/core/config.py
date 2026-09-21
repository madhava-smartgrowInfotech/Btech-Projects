"""Application settings, read once from the project-root ``.env``."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")


def _path(value: str, default: str) -> Path:
    p = Path(value or default)
    return p if p.is_absolute() else ROOT_DIR / p


def _list(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


LANGUAGE_NAMES = {"en": "English", "hi": "Hindi", "te": "Telugu"}


@dataclass(frozen=True)
class Settings:
    app_name: str = "PolicyLens"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    gemini_lite_model: str = "gemini-3.5-flash-lite"
    gemini_fallback_models: list[str] = field(default_factory=list)
    gemini_timeout_seconds: int = 90
    gemini_embedding_model: str = "gemini-embedding-001"
    llm_max_rpm: int = 10
    embedding_provider: str = "local"
    supported_languages: list[str] = field(default_factory=lambda: ["en", "hi", "te"])
    jwt_secret: str = ""
    jwt_expire_minutes: int = 1440
    backend_port: int = 8101
    frontend_port: int = 5101
    cors_origins: list[str] = field(default_factory=list)
    data_dir: Path = ROOT_DIR / "data"
    models_dir: Path = ROOT_DIR / "models"
    max_upload_mb: int = 25
    log_level: str = "INFO"
    demo_email: str = "demo@policylens.app"
    demo_password: str = "Demo@12345"

    # Derived locations
    @property
    def db_path(self) -> Path:
        return self.data_dir / "app.db"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path.as_posix()}"

    @property
    def chroma_dir(self) -> Path:
        return self.data_dir / "chroma"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def pages_dir(self) -> Path:
        return self.data_dir / "pages"

    @property
    def policies_dir(self) -> Path:
        return self.data_dir / "policies"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def hf_dir(self) -> Path:
        return self.models_dir / "hf"

    @property
    def experiments_dir(self) -> Path:
        return ROOT_DIR / "experiments"

    @property
    def logs_dir(self) -> Path:
        return ROOT_DIR / "logs"

    @property
    def gemini_configured(self) -> bool:
        return bool(self.gemini_api_key)


@lru_cache
def get_settings() -> Settings:
    env = os.environ
    languages = [code for code in _list(env.get("SUPPORTED_LANGUAGES", "en,hi,te")) if code in LANGUAGE_NAMES]
    return Settings(
        gemini_api_key=env.get("GEMINI_API_KEY", "").strip(),
        gemini_model=env.get("GEMINI_MODEL", "gemini-3.8-flash").strip(),
        gemini_lite_model=env.get("GEMINI_LITE_MODEL", "gemini-3.5-flash-lite").strip(),
        gemini_fallback_models=_list(env.get("GEMINI_FALLBACK_MODELS", "gemini-3.6-flash,gemini-3.5-flash-lite")),
        gemini_timeout_seconds=int(env.get("GEMINI_TIMEOUT_SECONDS", "90")),
        gemini_embedding_model=env.get("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001").strip(),
        llm_max_rpm=int(env.get("LLM_MAX_RPM", "10")),
        embedding_provider=env.get("EMBEDDING_PROVIDER", "local").strip().lower(),
        supported_languages=languages or ["en"],
        jwt_secret=env.get("JWT_SECRET", "").strip() or "policylens-local-development-secret",
        jwt_expire_minutes=int(env.get("JWT_EXPIRE_MINUTES", "1440")),
        backend_port=int(env.get("BACKEND_PORT", "8101")),
        frontend_port=int(env.get("FRONTEND_PORT", "5101")),
        cors_origins=_list(env.get("CORS_ORIGINS", "http://localhost:5101,http://127.0.0.1:5101")),
        data_dir=_path(env.get("DATA_DIR", ""), "data"),
        models_dir=_path(env.get("MODELS_DIR", ""), "models"),
        max_upload_mb=int(env.get("MAX_UPLOAD_MB", "25")),
        log_level=env.get("LOG_LEVEL", "INFO").upper(),
        demo_email=env.get("DEMO_EMAIL", "demo@policylens.app").strip().lower(),
        demo_password=env.get("DEMO_PASSWORD", "Demo@12345"),
    )


def project_relative(path: Path) -> str:
    """Store paths relative to the project root when possible (portable), absolute otherwise."""
    try:
        return path.resolve().relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return str(path.resolve())


def ensure_directories(settings: Settings | None = None) -> None:
    s = settings or get_settings()
    for d in (s.data_dir, s.uploads_dir, s.pages_dir, s.chroma_dir, s.cache_dir, s.hf_dir, s.logs_dir):
        d.mkdir(parents=True, exist_ok=True)


# Keep third-party libraries local and quiet.
_s = get_settings()
os.environ.setdefault("HF_HOME", str(_s.hf_dir / "cache"))
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
