import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
FOODS_CSV = DATA_DIR / "processed" / "foods.csv"
DB_PATH = Path(os.getenv("NUTRISENSE_DB", str(DATA_DIR / "app.db")))
MODEL_PATH = ROOT / "models" / "swap_kmeans.joblib"

BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8211"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "5211"))

# If no secret is configured, tokens are signed with a per-process random key (users re-login after restart).
JWT_SECRET = os.getenv("JWT_SECRET") or secrets.token_hex(32)
JWT_HOURS = 24 * 7

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip()
GEMINI_FALLBACK_MODELS = [m.strip() for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-2.5-flash,gemini-2.0-flash").split(",") if m.strip()]
USDA_API_KEY = os.getenv("USDA_API_KEY", "").strip() or "DEMO_KEY"

DEMO_EMAIL = "demo@nutrisense.app"
DEMO_PASSWORD = "Demo@1234"
