"""Download the Kaggle "Hospital Triage and Patient History Data" set into data/raw/ (git-ignored).

NOT used by the current build, which trains on a seeded synthetic dataset (ml/make_data.py). This is the
starting point for retraining on real triage records. UNTESTED against the live dataset.

Set a Kaggle API token first:  set KAGGLE_API_TOKEN=<token>   (or save it to ~/.kaggle/access_token)
Then:  venv\\Scripts\\python scripts\\download_data.py
Source: https://www.kaggle.com/datasets/maalona/hospital-triage-and-patient-history-data (licence not stated).
"""
import shutil
from pathlib import Path

import kagglehub

DEST = Path(__file__).resolve().parents[1] / "data" / "raw"

if __name__ == "__main__":
    src = Path(kagglehub.dataset_download("maalona/hospital-triage-and-patient-history-data"))
    DEST.mkdir(parents=True, exist_ok=True)
    for f in src.rglob("*"):
        if f.is_file():
            shutil.copy2(f, DEST / f.name)
    print("copied", len(list(DEST.iterdir())), "files to", DEST)
