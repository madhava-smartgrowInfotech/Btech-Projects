"""Central configuration: loads .env from the project root."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
EXPERIMENTS_DIR = ROOT / "experiments"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
HOSPITAL_SHARED_SECRET = os.getenv("HOSPITAL_SHARED_SECRET", "dev-hospital-secret")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8206"))
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "demo123")

# The three simulated hospitals. Each runs its own FHIR R4 server and SQLite file.
HOSPITALS = {
    "A": {"key": "A", "name": "Northbridge General Hospital", "prefix": "NBG",
          "port": int(os.getenv("HOSPITAL_A_PORT", "12061"))},
    "B": {"key": "B", "name": "Riverside Medical Center", "prefix": "RMC",
          "port": int(os.getenv("HOSPITAL_B_PORT", "12062"))},
    "C": {"key": "C", "name": "Lakeview Clinic", "prefix": "LVC",
          "port": int(os.getenv("HOSPITAL_C_PORT", "12063"))},
}
for _h in HOSPITALS.values():
    _h["base_url"] = f"http://127.0.0.1:{_h['port']}/fhir"
    _h["db"] = DATA_DIR / f"hospital_{_h['key'].lower()}.db"

PLATFORM_URL = f"http://127.0.0.1:{BACKEND_PORT}/api"

# Data categories a patient can share, mapped to FHIR resource types.
CATEGORIES = {
    "encounters": ["Encounter", "CarePlan"],
    "conditions": ["Condition"],
    "medications": ["MedicationRequest"],
    "labs": ["Observation", "DiagnosticReport"],
    "allergies": ["AllergyIntolerance"],
}
TYPE_TO_CATEGORY = {t: c for c, ts in CATEGORIES.items() for t in ts}
