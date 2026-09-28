"""Download the Water Potability dataset (Kaggle, CC0) into data/water_potability.csv.

The CSV is already committed; run this only to refresh it.
Needs KAGGLE_USERNAME / KAGGLE_KEY in .env if anonymous download is refused.
"""
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "water_potability.csv"


def main():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                if k.strip().startswith("KAGGLE_") and v.strip():
                    os.environ[k.strip()] = v.strip()
    import kagglehub

    path = Path(kagglehub.dataset_download("adityakadiwal/water-potability"))
    src = next(path.rglob("*.csv"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, OUT)
    print(f"Saved {src.name} -> {OUT}")


if __name__ == "__main__":
    main()
