"""Central settings and hospital structure constants."""
import os
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = ROOT / "models"
EXPERIMENTS_DIR = ROOT / "experiments"

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "12"))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'app.db').as_posix()}")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8207"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "5207"))

FACILITIES = ["A", "B", "C", "D", "E"]
WARDS = ["General", "Surgical", "Maternity", "Paediatric", "ICU"]
SHIFTS = ["Day", "Evening", "Night"]

# Patients per nurse, by ward and shift (default hospital structure).
NURSE_RATIO = {
    "General": {"Day": 6, "Evening": 6, "Night": 8},
    "Surgical": {"Day": 5, "Evening": 5, "Night": 7},
    "Maternity": {"Day": 4, "Evening": 4, "Night": 5},
    "Paediatric": {"Day": 4, "Evening": 4, "Night": 5},
    "ICU": {"Day": 2, "Evening": 2, "Night": 2},
}

EQUIPMENT = ["Ventilator", "Cardiac monitor", "Infusion pump", "Dialysis machine"]

# Beds may be converted between these ward pairs inside one facility (from -> to).
CONVERTIBLE = [
    ("General", "Surgical"), ("Surgical", "General"),
    ("General", "Maternity"), ("Maternity", "General"),
    ("General", "Paediatric"), ("Paediatric", "General"),
    ("Surgical", "ICU"),  # step-up conversion, limited by ICU_CONVERSION_LIMIT
]
ICU_CONVERSION_LIMIT = 0.25  # at most +25% of a facility's ICU beds by conversion

# History: day index 0 = first admission day in the source data.
# Day OPERATING_DAY is "today"; dates are shown shifted so that it maps to OPERATING_DATE
# (the shift is a multiple of 7 days, so weekdays are preserved).
OPERATING_DAY = 365
OPERATING_DATE = date(2026, 9, 28)
LONG_STAY_DAYS = 5  # a stay longer than this is a "long stay"


def day_to_date(day: int) -> date:
    return OPERATING_DATE + timedelta(days=int(day) - OPERATING_DAY)
