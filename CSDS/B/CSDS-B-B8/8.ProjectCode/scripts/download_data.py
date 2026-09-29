"""Download the datasets CareWatch trains on (Kaggle, through kagglehub).

    python scripts/download_data.py            # full HAR set -> data/raw/har (git-ignored)
    python scripts/download_data.py --sample   # also rebuild the committed sample in data/sample/har

The CCTV incident set (data/cctv_lying) and the Fall Detection set (data/fall_detection) are committed;
they are re-downloaded only if missing. Public datasets download without a Kaggle login.
"""
import argparse
import csv
import random
import shutil
from pathlib import Path

import kagglehub

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HAR_CLASSES = ["drinking", "sitting", "sleeping"]  # the HAR actions CareWatch uses
SAMPLE_PER_CLASS = 300
SEED = 42


def fetch(slug):
    print(f"Downloading {slug} ...")
    return Path(kagglehub.dataset_download(slug))


def ensure_committed_sets():
    if not (DATA / "cctv_lying" / "labels").exists():
        src = fetch("simuletic/cctv-incident-dataset-fall-and-lying-down-detection") / "laying_dataset"
        shutil.copytree(src, DATA / "cctv_lying", dirs_exist_ok=True)
    if not (DATA / "fall_detection" / "labels").exists():
        src = fetch("uttejkumarkandagatla/fall-detection-dataset") / "fall_dataset"
        shutil.copytree(src, DATA / "fall_detection", dirs_exist_ok=True)


def har(sample):
    src = fetch("meetnagadia/human-action-recognition-har-dataset") / "Human Action Recognition"
    with open(src / "Training_set.csv", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["label"] in HAR_CLASSES]

    raw = DATA / "raw" / "har"
    (raw / "images").mkdir(parents=True, exist_ok=True)
    for r in rows:
        dst = raw / "images" / r["filename"]
        if not dst.exists():
            shutil.copy2(src / "train" / r["filename"], dst)
    write_csv(raw / "labels.csv", rows)
    print(f"HAR full set: {len(rows)} images -> {raw}")

    if sample:
        rng = random.Random(SEED)
        out = DATA / "sample" / "har"
        if out.exists():
            shutil.rmtree(out)
        (out / "images").mkdir(parents=True)
        picked = []
        for c in HAR_CLASSES:
            cls = sorted((r for r in rows if r["label"] == c), key=lambda r: r["filename"])
            picked += rng.sample(cls, min(SAMPLE_PER_CLASS, len(cls)))
        for r in picked:
            shutil.copy2(raw / "images" / r["filename"], out / "images" / r["filename"])
        write_csv(out / "labels.csv", picked)
        print(f"HAR sample: {len(picked)} images -> {out}")


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["filename", "label"])
        w.writeheader()
        for r in rows:
            w.writerow({"filename": r["filename"], "label": r["label"]})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="rebuild data/sample/har")
    args = ap.parse_args()
    ensure_committed_sets()
    har(args.sample)
