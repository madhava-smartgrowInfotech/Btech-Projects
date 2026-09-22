"""Application settings, read once from the project's .env file (see .env.example)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / ".env", override=False)   # real environment variables win (used by tests)

APP_NAME = "SignalScout"
APP_VERSION = "1.0.0"


def _str(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _int(key: str, default: int) -> int:
    try:
        return int(_str(key, str(default)))
    except ValueError:
        return default


def _float(key: str, default: float) -> float:
    try:
        return float(_str(key, str(default)))
    except ValueError:
        return default


def _bool(key: str, default: bool) -> bool:
    value = _str(key, "")
    return default if not value else value.lower() in {"1", "true", "yes", "on"}


def _database_url() -> str:
    url = _str("DATABASE_URL", "sqlite:///data/app.db")
    prefix = "sqlite:///"
    if url.startswith(prefix) and not url.startswith(prefix + "/") and not Path(url[len(prefix):]).is_absolute():
        url = prefix + (ROOT / url[len(prefix):]).as_posix()   # relative paths are relative to the project root
    return url


@dataclass(frozen=True)
class Settings:
    # server
    backend_host: str = field(default_factory=lambda: _str("BACKEND_HOST", "0.0.0.0"))
    backend_port: int = field(default_factory=lambda: _int("BACKEND_PORT", 8202))
    frontend_port: int = field(default_factory=lambda: _int("FRONTEND_PORT", 5202))
    public_api_url: str = field(default_factory=lambda: _str("PUBLIC_API_URL", "http://localhost:8202"))
    dashboard_url: str = field(default_factory=lambda: _str("DASHBOARD_URL", "http://localhost:5202"))
    cors_origins: tuple[str, ...] = field(default_factory=lambda: tuple(o.strip() for o in _str("CORS_ORIGINS").split(",") if o.strip()))
    tunnel_enabled: bool = field(default_factory=lambda: _bool("TUNNEL_ENABLED", True))

    # security
    jwt_secret: str = field(default_factory=lambda: _str("JWT_SECRET"))
    jwt_expire_hours: int = field(default_factory=lambda: _int("JWT_EXPIRE_HOURS", 12))

    # data
    database_url: str = field(default_factory=_database_url)
    seed_demo_users: bool = field(default_factory=lambda: _bool("SEED_DEMO_USERS", True))
    seed_sample_data: bool = field(default_factory=lambda: _bool("SEED_SAMPLE_DATA", True))

    # zones and complaints (defaults; admins can override in Settings)
    h3_resolution: int = field(default_factory=lambda: _int("H3_RESOLUTION", 9))
    detect_min_readings: int = field(default_factory=lambda: _int("DETECT_MIN_READINGS", 8))
    detect_window_min: int = field(default_factory=lambda: _int("DETECT_WINDOW_MIN", 30))
    detect_bad_share: float = field(default_factory=lambda: _float("DETECT_BAD_SHARE", 0.7))
    detect_persist_min: int = field(default_factory=lambda: _int("DETECT_PERSIST_MIN", 15))
    verify_min_readings: int = field(default_factory=lambda: _int("VERIFY_MIN_READINGS", 5))
    verify_strong_share: float = field(default_factory=lambda: _float("VERIFY_STRONG_SHARE", 0.7))
    verify_reopen_share: float = field(default_factory=lambda: _float("VERIFY_REOPEN_SHARE", 0.5))
    verify_timeout_days: int = field(default_factory=lambda: _int("VERIFY_TIMEOUT_DAYS", 7))

    # phone probe
    probe_interval_s: int = field(default_factory=lambda: _int("PROBE_INTERVAL_S", 10))
    probe_speedtest_interval_s: int = field(default_factory=lambda: _int("PROBE_SPEEDTEST_INTERVAL_S", 60))
    probe_speedtest_max_bytes: int = field(default_factory=lambda: _int("PROBE_SPEEDTEST_MAX_BYTES", 1_000_000))
    probe_weak_rtt_ms: float = field(default_factory=lambda: _float("PROBE_WEAK_RTT_MS", 400))
    probe_weak_dl_mbps: float = field(default_factory=lambda: _float("PROBE_WEAK_DL_MBPS", 2))

    # ESP32 simulator
    esp32_simulator: bool = field(default_factory=lambda: _bool("ESP32_SIMULATOR", True))

    # notifications and optional services
    telegram_bot_token: str = field(default_factory=lambda: _str("TELEGRAM_BOT_TOKEN"))
    telegram_chat_id: str = field(default_factory=lambda: _str("TELEGRAM_CHAT_ID"))
    smtp_host: str = field(default_factory=lambda: _str("SMTP_HOST", "smtp.gmail.com"))
    smtp_port: int = field(default_factory=lambda: _int("SMTP_PORT", 587))
    smtp_user: str = field(default_factory=lambda: _str("SMTP_USER"))
    smtp_password: str = field(default_factory=lambda: _str("SMTP_PASSWORD").replace(" ", ""))
    smtp_from: str = field(default_factory=lambda: _str("SMTP_FROM"))
    desk_email: str = field(default_factory=lambda: _str("DESK_EMAIL"))
    opencellid_api_key: str = field(default_factory=lambda: _str("OPENCELLID_API_KEY"))
    gemini_api_key: str = field(default_factory=lambda: _str("GEMINI_API_KEY"))
    gemini_model: str = field(default_factory=lambda: _str("GEMINI_MODEL", "gemini-3.8-flash"))

    # paths
    root: Path = ROOT
    data_dir: Path = ROOT / "data"
    runtime_dir: Path = ROOT / "data" / "runtime"
    models_dir: Path = ROOT / "models"
    experiments_dir: Path = ROOT / "experiments"
    frontend_dist: Path = ROOT / "frontend" / "dist"
    logs_dir: Path = ROOT / "logs"

    @property
    def allowed_origins(self) -> list[str]:
        base = [f"http://localhost:{self.frontend_port}", f"http://127.0.0.1:{self.frontend_port}",
                f"http://localhost:{self.backend_port}", f"http://127.0.0.1:{self.backend_port}"]
        return base + list(self.cors_origins)


settings = Settings()
