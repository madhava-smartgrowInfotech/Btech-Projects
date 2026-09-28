import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8216"))
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "RetinaGuard@123")

_db = os.getenv("DATABASE_URL", "sqlite:///data/app.db")
if _db.startswith("sqlite:///") and not Path(_db[10:]).is_absolute():
    _db = "sqlite:///" + (ROOT / _db[10:]).as_posix()
DATABASE_URL = _db

DATA_DIR = ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
SAMPLE_DIR = DATA_DIR / "sample"
MODELS_DIR = ROOT / "models"
EXPERIMENTS_DIR = ROOT / "experiments"

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set. Copy .env.example to .env and set it.")
