"""Download the full datasets from Kaggle (only needed to re-train; the app runs on the committed sample).

  python scripts/download_data.py
Then:  python ml/prepare_data.py  ->  python ml/train_mri.py

LGG brain MRI (mateuszbuda/lgg-mri-segmentation, CC BY-NC-SA 4.0, ~1 GB) -> data/raw/lgg/kaggle_3m
DNA classification (miadul/dna-classification-dataset)                   -> data/dna/synthetic_dna_dataset.csv
Public datasets download without a Kaggle token; if Kaggle asks for one, put kaggle.json in ~/.kaggle/.
"""
import shutil
from pathlib import Path

import kagglehub

ROOT = Path(__file__).resolve().parents[1]


def main():
    lgg = Path(kagglehub.dataset_download("mateuszbuda/lgg-mri-segmentation"))
    src = next(p for p in lgg.rglob("kaggle_3m") if p.is_dir())
    dst = ROOT / "data" / "raw" / "lgg" / "kaggle_3m"
    if not dst.exists():
        shutil.copytree(src, dst)
    print(f"LGG MRI -> {dst}")

    dna = Path(kagglehub.dataset_download("miadul/dna-classification-dataset"))
    csv = next(dna.rglob("*.csv"))
    out = ROOT / "data" / "dna" / "synthetic_dna_dataset.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(csv, out)
    print(f"DNA dataset -> {out}")


if __name__ == "__main__":
    main()
