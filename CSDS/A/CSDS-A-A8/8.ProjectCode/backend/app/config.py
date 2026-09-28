import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT / "ml"))

DATA = ROOT / "data"
MODELS = ROOT / "models"
EXPERIMENTS = ROOT / "experiments"

BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8108"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "5108"))
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_HOURS = int(os.getenv("JWT_HOURS", "24"))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(DATA / 'app.db').as_posix()}")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_FALLBACK_MODELS = [m.strip() for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-2.5-flash,gemini-flash-lite-latest").split(",") if m.strip()]
DEMO_EMAIL = os.getenv("DEMO_EMAIL", "demo@biosight.app")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "Demo@1234")
