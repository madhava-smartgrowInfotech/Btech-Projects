"""Central configuration, loaded from the project .env file."""
from pathlib import Path
import os
from dotenv import load_dotenv

# backend/app/config.py -> project root is two parents up from backend/
BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


class Settings:
    backend_port = _int("BACKEND_PORT", 8213)
    frontend_port = _int("FRONTEND_PORT", 5213)

    jwt_secret = os.getenv("JWT_SECRET", "dev-insecure-secret-change-me")
    jwt_expire_minutes = _int("JWT_EXPIRE_MINUTES", 720)
    jwt_algorithm = "HS256"

    demo_email = os.getenv("DEMO_EMAIL", "demo@apisentry.local")
    demo_password = os.getenv("DEMO_PASSWORD", "demo12345")

    scope_allowlist = [
        h.strip().lower()
        for h in os.getenv("SCOPE_ALLOWLIST", "localhost,127.0.0.1").split(",")
        if h.strip()
    ]

    demopay_port = _int("DEMOPAY_PORT", 12130)
    vulnbank_port = _int("VULNBANK_PORT", 12131)

    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    gemini_fallback_model = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-flash-lite-latest").strip()
    gemini_timeout = _int("GEMINI_TIMEOUT_SECONDS", 60)

    db_path = DATA_DIR / "app.db"
    database_url = f"sqlite:///{db_path.as_posix()}"


settings = Settings()
