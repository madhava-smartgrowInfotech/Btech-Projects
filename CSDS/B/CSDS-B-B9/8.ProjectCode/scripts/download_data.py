"""Download the Kaggle datasets with kagglehub and copy them into data/.

Public datasets download without credentials in most cases; if Kaggle asks for them, create an API token at
https://www.kaggle.com/settings and place kaggle.json in %USERPROFILE%/.kaggle/.
Run:  python scripts/download_data.py [--all-pdfs]
"""
import shutil
import sys
from pathlib import Path

import kagglehub

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def main():
    apt = Path(kagglehub.dataset_download("keithzidandsouza/engineering-aptitude-test-questions"))
    (DATA / "aptitude").mkdir(parents=True, exist_ok=True)
    for f in apt.glob("*.csv"):
        shutil.copy(f, DATA / "aptitude" / f.name)
    res = Path(kagglehub.dataset_download("snehaanbhawal/resume-dataset"))
    (DATA / "resume").mkdir(parents=True, exist_ok=True)
    shutil.copy(res / "Resume" / "Resume.csv", DATA / "resume" / "Resume.csv")
    sample = DATA / "sample" / "resumes"
    sample.mkdir(parents=True, exist_ok=True)
    for cat in sorted((res / "data" / "data").iterdir()):
        pdfs = sorted(cat.glob("*.pdf"))
        if "--all-pdfs" in sys.argv:
            dest = DATA / "raw" / "resumes" / cat.name
            dest.mkdir(parents=True, exist_ok=True)
            for p in pdfs:
                shutil.copy(p, dest / p.name)
        if pdfs:
            shutil.copy(pdfs[0], sample / f"{cat.name}_{pdfs[0].name}")
    print("datasets ready in", DATA)


if __name__ == "__main__":
    main()
