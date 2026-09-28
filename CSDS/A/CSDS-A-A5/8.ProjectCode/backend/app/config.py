"""Settings read from the project-root .env file."""
import os

from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(ROOT, ".env"))


def _get(key, default=""):
    return os.getenv(key, default).strip()


GEMINI_API_KEY = _get("GEMINI_API_KEY")
GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-3.8-flash")
GEMINI_FALLBACK_MODELS = [m.strip() for m in _get("GEMINI_FALLBACK_MODELS", "gemini-3.5-flash-lite,gemini-flash-latest").split(",") if m.strip()]
GEMINI_TIMEOUT_SECONDS = int(_get("GEMINI_TIMEOUT_SECONDS", "60"))
JWT_SECRET = _get("JWT_SECRET") or "change-me-run-setup-bat"
JWT_EXPIRE_MINUTES = int(_get("JWT_EXPIRE_MINUTES", "720"))
BACKEND_PORT = int(_get("BACKEND_PORT", "8105"))
FRONTEND_PORT = int(_get("FRONTEND_PORT", "5105"))
CORS_ORIGINS = [o.strip() for o in _get("CORS_ORIGINS", f"http://localhost:{FRONTEND_PORT},http://127.0.0.1:{FRONTEND_PORT}").split(",") if o.strip()]
DEMO_EMAIL = _get("DEMO_EMAIL", "demo@taxsentinel.app")
DEMO_PASSWORD = _get("DEMO_PASSWORD", "Demo@1234")
DATA_DIR = os.path.join(ROOT, "data")
BASE_DATASET = os.path.join(DATA_DIR, "generated")
WORKSPACE = os.path.join(DATA_DIR, "workspace")
MODEL_PATH = os.path.join(ROOT, "models", "jepa.pt")
DB_PATH = os.path.join(DATA_DIR, "app.db")
