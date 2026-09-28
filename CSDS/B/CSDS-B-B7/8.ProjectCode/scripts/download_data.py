"""Re-download the three public Kaggle datasets into data/raw/ (they are already committed).

Uses kagglehub; public datasets download without credentials. If Kaggle asks for them, set
KAGGLE_USERNAME / KAGGLE_KEY in .env (see .env.example).
"""
import shutil
from pathlib import Path

import kagglehub
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
RAW = ROOT / "data" / "raw"
SOURCES = {
    "los": ("aayushchou/hospital-length-of-stay-dataset-microsoft", ["LengthOfStay.csv"]),
    "av": ("nehaprabhavalkar/av-healthcare-analytics-ii", ["train_data.csv", "train_data_dictionary.csv"]),
    "beds": ("jaderz/hospital-beds-management", ["services_weekly.csv"]),
}

for folder, (handle, files) in SOURCES.items():
    path = Path(kagglehub.dataset_download(handle))
    (RAW / folder).mkdir(parents=True, exist_ok=True)
    for name in files:
        src = next(path.rglob(name))
        shutil.copy(src, RAW / folder / name)
        print(f"{handle}: {name} -> data/raw/{folder}/")
