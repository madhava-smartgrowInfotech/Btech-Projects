import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA = ROOT / "data"
MODELS = ROOT / "models"
EXPERIMENTS = ROOT / "experiments"

BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8214"))
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/app.db")
if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite:////"):
    rel = DATABASE_URL[len("sqlite:///"):]
    if not Path(rel).is_absolute():
        DATABASE_URL = "sqlite:///" + str((ROOT / rel).resolve()).replace("\\", "/")

CITY_NAME = os.getenv("CITY_NAME", "Hyderabad")
CITY_LAT = float(os.getenv("CITY_LAT", "17.385"))
CITY_LON = float(os.getenv("CITY_LON", "78.4867"))
