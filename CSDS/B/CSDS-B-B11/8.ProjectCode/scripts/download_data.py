"""Re-download the Kaggle source datasets into data/raw (they are already committed; this is for reproducibility).

Usage: venv\\Scripts\\python scripts\\download_data.py
Public datasets download without a Kaggle account via kagglehub.
"""
import os
import shutil
from pathlib import Path

import kagglehub

ROOT = Path(__file__).resolve().parents[1]
DATASETS = {
    "batthulavinay/indian-food-nutrition": "indian_food_nutrition",
    "ahsanneural/10k-south-asian-recipes-with-nutrition-and-steps": "south_asian_recipes",
    "umangsinghal5/nutritional-and-carbon-footprint-data-of-indian-diet": "indian_diet_carbon",
}


def main():
    for slug, folder in DATASETS.items():
        src = kagglehub.dataset_download(slug)
        dest = ROOT / "data" / "raw" / folder
        dest.mkdir(parents=True, exist_ok=True)
        for root, _, files in os.walk(src):
            for f in files:
                shutil.copy(os.path.join(root, f), dest / f)
                print(f"{folder}/{f}")


if __name__ == "__main__":
    main()
