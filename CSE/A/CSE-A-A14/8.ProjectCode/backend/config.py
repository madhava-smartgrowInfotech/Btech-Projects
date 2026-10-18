"""Settings read from the project's .env file (no extra dependency needed)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env()

BACKEND_PORT = int(os.environ.get("BACKEND_PORT", "8314"))
FRONTEND_PORT = int(os.environ.get("FRONTEND_PORT", "5314"))
DEMO_EMAIL = os.environ.get("DEMO_EMAIL", "demo@churniq.com")
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "Demo@1234")
AUTH_SECRET = os.environ.get("AUTH_SECRET", "churn-intel-local-dev-secret-change-me")
TOKEN_TTL_SECONDS = 12 * 3600
CORS_ORIGINS = [
    f"http://localhost:{FRONTEND_PORT}",
    f"http://127.0.0.1:{FRONTEND_PORT}",
]
