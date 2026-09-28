"""Download the raw datasets used by SignBridge (via kagglehub) into data/raw/.

Only needed to rebuild the committed landmark files - the app itself runs on the
committed data in data/ and the trained models in models/.

    python scripts/download_data.py
"""
import json
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import kagglehub
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ml.vocab import WORDS  # noqa: E402

RAW = ROOT / "data" / "raw"
INCLUDE = "swaptr/indian-sign-language-mediapipe-holistic-landmarks"
LETTERS = "prathumarikeri/indian-sign-language-isl"
WORDS_VIDEOS = "kaushikyh/indian-sign-language-words-with-landmarks"


def list_include_files():
    url = f"https://www.kaggle.com/api/v1/datasets/list/{INCLUDE}"
    files, token = [], None
    while True:
        params = {"pageSize": 1000}
        if token:
            params["pageToken"] = token
        data = requests.get(url, params=params, timeout=60).json()
        files += [f["name"] for f in data["datasetFiles"]]
        token = data.get("nextPageToken")
        if not token:
            return files


def download_include_subset():
    """Only the parquet takes for the chosen vocabulary (the full set is 3.5 GB)."""
    wanted = {w["source"] for w in WORDS}
    files = [f for f in list_include_files() if f.endswith(".parquet") and "/".join(f.split("/")[1:3]) in wanted]
    out = RAW / "include"
    todo = [f for f in files if not (out / f).exists()]
    print(f"INCLUDE subset: {len(files)} takes ({len(todo)} to download)")

    def fetch(name):
        src = kagglehub.dataset_download(INCLUDE, path=name)
        dst = out / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)

    with ThreadPoolExecutor(8) as pool:
        list(pool.map(fetch, todo))
    (out / "files.json").write_text(json.dumps(files, indent=0))


def download_full(handle, name):
    src = Path(kagglehub.dataset_download(handle))
    dst = RAW / name
    if not dst.exists():
        shutil.copytree(src, dst)
    print(f"{handle} -> {dst}")


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    download_include_subset()
    download_full(LETTERS, "letters")
    download_full(WORDS_VIDEOS, "word_videos")
