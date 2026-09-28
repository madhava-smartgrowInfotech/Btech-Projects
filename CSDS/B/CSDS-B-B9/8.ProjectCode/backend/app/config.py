import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA = ROOT / "data"
MODELS = ROOT / "models"
DB_PATH = DATA / "app.db"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
JWT_SECRET = os.getenv("JWT_SECRET", "").strip() or "dev-only-secret-set-JWT_SECRET-in-env"
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8209"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "5209"))
JUDGE_TIME_LIMIT = float(os.getenv("JUDGE_TIME_LIMIT_SEC", "2") or 2)
JUDGE_MAX_OUTPUT = int(os.getenv("JUDGE_MAX_OUTPUT_KB", "8192") or 8192) * 1024
GXX_PATH = os.getenv("GXX_PATH", "").strip()
JAVAC_PATH = os.getenv("JAVAC_PATH", "").strip()
JAVA_PATH = os.getenv("JAVA_PATH", "").strip()
