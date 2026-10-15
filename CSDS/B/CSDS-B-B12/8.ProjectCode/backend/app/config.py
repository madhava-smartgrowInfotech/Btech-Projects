import os
import pathlib

from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
STORE_DIR = DATA_DIR / "store"
MODELS_DIR = ROOT / "models"
EXPERIMENTS_DIR = ROOT / "experiments"
FONTS_DIR = pathlib.Path(__file__).resolve().parent / "assets" / "fonts"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_FALLBACK_MODELS = [m.strip() for m in os.getenv("GEMINI_FALLBACK_MODELS", "").split(",") if m.strip()]

JWT_SECRET = os.getenv("JWT_SECRET", "")
FERNET_KEY = os.getenv("FERNET_KEY", "")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8212"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "5212"))

_db_url = os.getenv("DATABASE_URL", "sqlite:///data/app.db")
if _db_url.startswith("sqlite:///") and not _db_url.startswith("sqlite:////"):
    _rel = _db_url[len("sqlite:///"):]
    if not pathlib.Path(_rel).is_absolute():
        _db_url = "sqlite:///" + str((ROOT / _rel).as_posix())
DATABASE_URL = _db_url

if not JWT_SECRET or not FERNET_KEY:
    raise RuntimeError("JWT_SECRET and FERNET_KEY must be set in .env (see .env.example)")

DATA_DIR.mkdir(exist_ok=True)
STORE_DIR.mkdir(exist_ok=True)
