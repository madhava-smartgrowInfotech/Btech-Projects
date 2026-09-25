"""Download the CUAD (Contract Understanding Atticus Dataset) v1 corpus.

CUAD is ~40 MB uncompressed, so this repo commits it in full at
data/cuad/CUADv1.json - you normally do NOT need to run this script. Re-run it
only if that file is missing or you want to re-fetch the source.

Source: https://github.com/TheAtticusProject/cuad (CC BY 4.0), the same
source used by the Hugging Face mirror theatticusproject/cuad-qa.
"""
import io
import json
import zipfile
from pathlib import Path

import requests

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_ZIP_URL = "https://raw.githubusercontent.com/The-Atticus-Project/cuad/main/data.zip"
OUT_DIR = ROOT_DIR / "data" / "cuad"
OUT_FILE = OUT_DIR / "CUADv1.json"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if OUT_FILE.exists():
        print(f"Already present: {OUT_FILE}")
        return

    print(f"Downloading CUAD data from {DATA_ZIP_URL} ...")
    resp = requests.get(DATA_ZIP_URL, timeout=120)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        with zf.open("CUADv1.json") as src, open(OUT_FILE, "wb") as dst:
            dst.write(src.read())

    with open(OUT_FILE, encoding="utf-8") as f:
        data = json.load(f)
    print(f"Saved {OUT_FILE} ({len(data['data'])} contracts)")


if __name__ == "__main__":
    main()
