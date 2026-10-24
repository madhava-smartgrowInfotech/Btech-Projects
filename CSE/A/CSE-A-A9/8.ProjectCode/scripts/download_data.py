"""Refresh the committed raw datasets from Kaggle (public datasets, no account token needed for these three).

    pip install kagglehub
    python scripts/download_data.py

The repository already contains everything under data/raw, so this is only needed to re-download it.
After refreshing, rebuild the graph and retrain:  python -m ml.data  then  python -m ml.train
"""
from __future__ import annotations

import shutil
from pathlib import Path

import kagglehub

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

SOURCES = {
    "dhruvb2028/social-circles-facebook": ("facebook", "*.edges"),                        # real topology, SNAP mirror
    "goyaladi/twitter-bot-detection-dataset": (".", "bot_detection_data.csv"),            # CC0
    "free4ever1/instagram-fake-spammer-genuine-accounts": (".", "*.csv"),                 # CC BY 3.0
}


def main() -> None:
    for slug, (sub, pattern) in SOURCES.items():
        print(f"downloading {slug} ...")
        src = Path(kagglehub.dataset_download(slug))
        dst = RAW / sub
        dst.mkdir(parents=True, exist_ok=True)
        for f in src.rglob(pattern):
            name = f.name
            if slug.startswith("goyaladi"):
                name = "twitter_bot_detection.csv"
            elif slug.startswith("free4ever1"):
                name = f"instagram_{f.name}"
            shutil.copy2(f, dst / name)
            print(f"  copied {name}")
    print("done. Next: python -m ml.data && python -m ml.train")


if __name__ == "__main__":
    main()
