import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8315"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "5315"))
JWT_SECRET = os.getenv("JWT_SECRET", "")
if len(JWT_SECRET) < 16:
    raise RuntimeError("JWT_SECRET missing or too short in .env")

DATA_DIR = ROOT / "data"
COVERS_DIR = DATA_DIR / "covers"
PAYLOADS_DIR = DATA_DIR / "payloads"
OUTPUTS_DIR = DATA_DIR / "outputs"
for d in (DATA_DIR, OUTPUTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

_db = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
if _db.startswith("sqlite:///./"):
    _db = "sqlite:///" + (ROOT / _db[len("sqlite:///./"):]).as_posix()
DATABASE_URL = _db

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
