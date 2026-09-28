import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8217"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "5217"))
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "CallSense@123")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip() or "gemini-flash-latest"
GEMINI_FALLBACK_MODELS = [m.strip() for m in os.getenv(
    "GEMINI_FALLBACK_MODELS", "gemini-flash-lite-latest,gemini-3.1-flash-lite").split(",") if m.strip()]

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small").strip() or "small"
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8").strip() or "int8"
EMOTION_MODEL = os.getenv("EMOTION_MODEL", "superb/wav2vec2-base-superb-er").strip()

_db = os.getenv("DATABASE_URL", "sqlite:///data/app.db")
if _db.startswith("sqlite:///") and not Path(_db[10:]).is_absolute():
    _db = "sqlite:///" + (ROOT / _db[10:]).as_posix()
DATABASE_URL = _db

DATA_DIR = ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
SAMPLE_DIR = DATA_DIR / "sample"
SCRIPTS_FILE = SAMPLE_DIR / "scripts" / "calls.json"
SAMPLE_CALLS_DIR = SAMPLE_DIR / "calls"
MODELS_DIR = ROOT / "models"
EXPERIMENTS_DIR = ROOT / "experiments"

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set. Copy .env.example to .env and set it.")
