"""Re-download the two Kaggle sources used by SHEGUARD and copy the CSVs this
project actually uses into data/raw/. The files are already committed, so you
only need to run this if you deleted data/raw/ or want a fresh copy.

Usage: python scripts/download_data.py
"""
import shutil
from pathlib import Path

import kagglehub

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("Downloading rajanand/crime-in-india ...")
    p1 = Path(kagglehub.dataset_download("rajanand/crime-in-india"))
    src1 = p1 / "crime" / "42_District_wise_crimes_committed_against_women_2001_2012.csv"
    shutil.copy(src1, RAW_DIR / "district_wise_crimes_against_women_2001_2012.csv")
    print("  ->", RAW_DIR / "district_wise_crimes_against_women_2001_2012.csv")

    print("Downloading balajivaraprasad/crimes-against-women-in-india-2001-2021 ...")
    p2 = Path(kagglehub.dataset_download("balajivaraprasad/crimes-against-women-in-india-2001-2021"))
    shutil.copy(p2 / "CrimesOnWomenData.csv", RAW_DIR / "crimes_against_women_2001_2021.csv")
    shutil.copy(p2 / "description.csv", RAW_DIR / "crimes_against_women_2001_2021_description.csv")
    print("  ->", RAW_DIR / "crimes_against_women_2001_2021.csv")

    print("Done.")


if __name__ == "__main__":
    main()
