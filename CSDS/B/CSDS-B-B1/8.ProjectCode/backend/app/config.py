import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
UPLOAD_DIR = DATA_DIR / "uploads"
CACHE_DIR = DATA_DIR / "cache"
MODELS_DIR = ROOT / "models"
EXPERIMENTS_DIR = ROOT / "experiments"

DATABASE_PATH = ROOT / os.getenv("DATABASE_PATH", "data/app.db")
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_HOURS = 12
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-flash-lite-latest")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8201"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "5201"))

SEED = 42
FEEDBACK_WEIGHT = 10.0  # an officer-confirmed label counts as much as 10 dataset rows

for d in (UPLOAD_DIR, CACHE_DIR, MODELS_DIR, EXPERIMENTS_DIR):
    d.mkdir(parents=True, exist_ok=True)
