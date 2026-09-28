"""Re-download the Kaggle datasets into data/ (they are already committed; use this to refresh them).

Needs Kaggle credentials if kagglehub asks for them (KAGGLE_USERNAME / KAGGLE_KEY in .env).
The OpenStreetMap hospitals are refreshed separately with scripts/fetch_hospitals.py.
"""
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
import kagglehub  # noqa: E402  (after credentials are in the environment)

DATASETS = {
    "itachi9604/disease-symptom-description-dataset": "disease_symptom",
    "ebrahimelgazar/doctor-specialist-recommendation-system": "doctor_specialist",
    "joniarroba/noshowappointments": "noshow",
}

for slug, folder in DATASETS.items():
    src = Path(kagglehub.dataset_download(slug))
    dst = ROOT / "data" / folder
    dst.mkdir(parents=True, exist_ok=True)
    for f in src.iterdir():
        if f.is_file():
            shutil.copy(f, dst / f.name)
    print(f"{slug} -> {dst} ({', '.join(os.listdir(dst))})")
