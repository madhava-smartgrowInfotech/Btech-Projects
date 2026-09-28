"""Build the committed data sample (or download the full dataset).

  python scripts/download_data.py            # sample: 60 VisDrone images + 2 short sequences + USC-SIPI test images
  python scripts/download_data.py --full     # full VisDrone dataset (2.16 GB) into data/raw/ (not committed)

VisDrone comes from Kaggle through kagglehub (public dataset - usually no credentials needed; otherwise set
KAGGLE_USERNAME / KAGGLE_KEY in .env). Selection is deterministic, so re-running gives the same sample.
"""
import argparse
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
SAMPLE = ROOT / "data" / "sample"
HANDLE = "banuprasadb/visdrone-dataset"
LIST_URL = "https://www.kaggle.com/api/v1/datasets/list/" + HANDLE

N_IMAGES = 60                      # still images from the validation split, spread across clips
SEQUENCES = {                      # frames from one flight each (the Kaggle mirror has the still-image split only)
    "city_flight_9999938": ("VisDrone2019-DET-test-dev", "9999938", 40),
    "night_flight_9999952": ("VisDrone2019-DET-test-dev", "9999952", 40),
}
IMG_MAX_SIDE = 1024
SEQ_WIDTH = 640

# USC-SIPI "Miscellaneous" volume, standard test images (https://sipi.usc.edu/database/)
SIPI = {
    "4.2.03": "mandrill.png",
    "4.2.07": "peppers.png",
    "4.2.05": "airplane_f16.png",
    "5.2.10": "stream_bridge.png",
    "5.1.12": "clock.png",
    "7.1.02": "aerial_7.1.02.png",
}


def list_files():
    names, tok = [], None
    while True:
        p = {"pageSize": 200}
        if tok:
            p["pageToken"] = tok
        r = requests.get(LIST_URL, params=p, timeout=60)
        r.raise_for_status()
        r = r.json()
        names += [f["name"] for f in r.get("datasetFiles", [])]
        tok = r.get("nextPageTokenNullable")
        if not tok:
            return names


def fetch(path: str) -> Path:
    import kagglehub
    return Path(kagglehub.dataset_download(HANDLE, path=path))


def save_resized(src: Path, dst: Path, max_side=None, width=None):
    img = cv2.imread(str(src))
    h, w = img.shape[:2]
    s = 1.0
    if max_side and max(h, w) > max_side:
        s = max_side / max(h, w)
    if width:
        s = width / w
    if s != 1.0:
        img = cv2.resize(img, (round(w * s), round(h * s)), interpolation=cv2.INTER_AREA)
    dst.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(dst), img, [cv2.IMWRITE_JPEG_QUALITY, 90])


def sample():
    print("Listing VisDrone files on Kaggle ...")
    names = [n for n in list_files() if n.endswith(".jpg")]
    val = sorted(n for n in names if "/VisDrone2019-DET-val/images/" in n)
    step = len(val) / N_IMAGES
    picks = [val[int(i * step)] for i in range(N_IMAGES)]

    jobs = [(p, SAMPLE / "visdrone" / "images" / Path(p).name, {"max_side": IMG_MAX_SIDE}) for p in picks]
    for seq, (split, clip, n) in SEQUENCES.items():
        frames = sorted(x for x in names if f"/{split}/images/{clip}_" in x)[:n]
        for i, p in enumerate(frames):
            jobs.append((p, SAMPLE / "visdrone" / "sequences" / seq / f"{i:04d}.jpg", {"width": SEQ_WIDTH}))

    def work(job):
        src, dst, kw = job
        if not dst.exists():
            save_resized(fetch(src), dst, **kw)
        return dst

    print(f"Downloading {len(jobs)} VisDrone files ...")
    with ThreadPoolExecutor(8) as ex:
        for i, _ in enumerate(ex.map(work, jobs), 1):
            if i % 20 == 0:
                print(f"  {i}/{len(jobs)}")

    print("Downloading USC-SIPI test images ...")
    out = SAMPLE / "sipi"
    out.mkdir(parents=True, exist_ok=True)
    for code, name in SIPI.items():
        dst = out / name
        if dst.exists():
            continue
        r = requests.get(f"https://sipi.usc.edu/database/download.php?vol=misc&img={code}", timeout=60)
        r.raise_for_status()
        img = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_UNCHANGED)
        if img is None:
            print(f"  could not decode {code}, skipped")
            continue
        cv2.imwrite(str(dst), img)
    print("Sample ready in", SAMPLE)


def full():
    import kagglehub
    path = Path(kagglehub.dataset_download(HANDLE))
    dst = ROOT / "data" / "raw" / "visdrone"
    if not dst.exists():
        shutil.copytree(path, dst)
    print("Full dataset in", dst)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="download the complete dataset into data/raw/")
    args = ap.parse_args()
    if not os.getenv("KAGGLE_USERNAME"):   # kagglehub picks up KAGGLE_USERNAME / KAGGLE_KEY when set
        os.environ.pop("KAGGLE_USERNAME", None)
        os.environ.pop("KAGGLE_KEY", None)
    try:
        full() if args.full else sample()
    except requests.HTTPError as e:
        sys.exit(f"Download failed: {e}. If Kaggle requires sign-in, set KAGGLE_USERNAME and KAGGLE_KEY in .env.")
