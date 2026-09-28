import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA = ROOT / "data"
MODELS = ROOT / "models"
DB_URL = f"sqlite:///{(DATA / 'app.db').as_posix()}"

BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8215"))
JWT_SECRET = os.getenv("JWT_SECRET") or "dev-only-secret-set-JWT_SECRET-in-.env"
JWT_HOURS = 24
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
MAX_OVERBOOK = float(os.getenv("MAX_OVERBOOK", "0.15"))
BOOKING_HORIZON_DAYS = 7
DISCLAIMER = ("Decision support only - this is not a diagnosis. A qualified clinician confirms "
              "severity at the hospital. In an emergency call 108.")
