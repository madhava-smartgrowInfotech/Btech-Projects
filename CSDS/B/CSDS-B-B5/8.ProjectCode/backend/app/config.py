import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8205"))

DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
EXPERIMENTS_DIR = ROOT / "experiments"
DB_PATH = DATA_DIR / "app.db"
