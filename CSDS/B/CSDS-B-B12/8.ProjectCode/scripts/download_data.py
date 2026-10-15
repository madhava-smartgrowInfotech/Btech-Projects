"""Download the public chest-imaging datasets with kagglehub and link them under data/raw/.

Usage:  python scripts/download_data.py
Needs a Kaggle account for some datasets: put kaggle.json in ~/.kaggle/ or set
KAGGLE_USERNAME / KAGGLE_KEY. The CT dataset and a sample of each X-ray dataset
are already committed under data/, so this is only needed for full training.
"""
import json
import pathlib

import kagglehub

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

DATASETS = {
    "covid19_radiography": "tawsifurrahman/covid19-radiography-database",
    "tb_chest_xray": "tawsifurrahman/tuberculosis-tb-chest-xray-dataset",
    "chest_ct": "mohamedhanyyy/chest-ctscan-images",
}


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, handle in DATASETS.items():
        print(f"Downloading {handle} ...")
        paths[name] = kagglehub.dataset_download(handle)
        print(f"  -> {paths[name]}")
    (RAW / "paths.json").write_text(json.dumps(paths, indent=2))
    print(f"Dataset locations written to {RAW / 'paths.json'}")


if __name__ == "__main__":
    main()
