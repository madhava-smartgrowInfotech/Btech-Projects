"""Download the full datasets into data/raw/ (git-ignored).

Usage: python scripts/download_data.py
- Hypertension & Hypertensive Retinopathy Dataset (Kaggle, CC BY-NC 4.0, ~1 GB): only task 2
  (hypertensive retinopathy classification) is extracted, into data/raw/hr/.
- Heart Disease Dataset (Kaggle): the CSV is already committed at data/heart/heart.csv; a fresh copy is
  placed in data/raw/heart.csv.
Public datasets download without a Kaggle token. If Kaggle ever asks for one, set KAGGLE_USERNAME and
KAGGLE_KEY in .env (https://www.kaggle.com/settings -> API -> Create New Token).
"""
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
load_dotenv(ROOT / ".env")
for k in ("KAGGLE_USERNAME", "KAGGLE_KEY"):
    if not os.getenv(k):
        os.environ.pop(k, None)

import kagglehub  # noqa: E402  (imported after credentials are cleaned up)

HR = "harshwardhanfartale/hypertension-and-hypertensive-retinopathy-dataset"
HEART = "johnsmith88/heart-disease-dataset"


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    if list(RAW.glob("hr/**/2-Groundtruths/*.csv")):
        print("Retinopathy dataset already in data/raw/hr")
    else:
        print("Downloading retinopathy dataset (~1 GB)...")
        src = Path(kagglehub.dataset_download(HR))
        task = next(p for p in src.iterdir() if p.name.startswith("2-Hypertensive Retinopathy"))
        shutil.copytree(task, RAW / "hr" / task.name, dirs_exist_ok=True)
        print("Copied to", RAW / "hr" / task.name)
    src = Path(kagglehub.dataset_download(HEART))
    shutil.copy(next(src.rglob("heart.csv")), RAW / "heart.csv")
    print("Heart CSV at", RAW / "heart.csv")


if __name__ == "__main__":
    main()
