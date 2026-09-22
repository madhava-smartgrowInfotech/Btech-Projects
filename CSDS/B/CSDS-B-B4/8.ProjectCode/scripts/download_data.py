"""Downloads (or re-downloads) the public datasets and verifies them.

The complete datasets are already committed under data/raw/, so you only need this script to
restore or refresh them. Kaggle datasets are fetched with kagglehub when a Kaggle API token is
configured (KAGGLE_API_TOKEN in .env, or ~/.kaggle/kaggle.json); otherwise the public Kaggle
download endpoint is used, which works for these public CC0 datasets without an account.

Usage:
    venv\\Scripts\\python scripts\\download_data.py            # verify, download only what is missing
    venv\\Scripts\\python scripts\\download_data.py --force    # download everything again
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

DATASETS = {
    "payment_fraud_benchmark": {
        "kaggle": "rohit8527kmr7518/digital-payment-fraud-detection-benchmark",
        "files": {"transactions_train.csv": 300113, "transactions_test.csv": 99887},
    },
    "upi_transactions_2024": {
        "kaggle": "skullagos5246/upi-transactions-2024-dataset",
        "files": {"upi_transactions_2024.csv": 250000},
    },
    "sms_spam_collection": {
        "kaggle": "uciml/sms-spam-collection-dataset",
        "files": {"spam.csv": 5572},
    },
}


def count_rows(path: Path) -> int:
    """Counts CSV records (quoted fields may contain newlines, so parse properly)."""
    import csv

    encoding = "latin-1" if path.name == "spam.csv" else "utf-8"
    with path.open(newline="", encoding=encoding) as f:
        return sum(1 for _ in csv.reader(f)) - 1


def fingerprint(path: Path) -> str:
    """Line-ending independent checksum (git may convert LF/CRLF on checkout)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk.replace(b"\r\n", b"\n"))
    return h.hexdigest()[:16]


def verify(name: str) -> bool:
    ok = True
    for filename, expected in DATASETS[name]["files"].items():
        path = RAW / name / filename
        if not path.exists():
            print(f"  [missing] {name}/{filename}")
            ok = False
            continue
        rows = count_rows(path)
        status = "ok" if rows == expected else f"expected {expected} rows"
        if rows != expected:
            ok = False
        print(f"  [{status}] {name}/{filename}: {rows:,} rows, {path.stat().st_size / 1e6:.1f} MB, sha256 {fingerprint(path)}")
    return ok


def download_kagglehub(slug: str, target: Path) -> bool:
    token = os.getenv("KAGGLE_API_TOKEN", "").strip()
    has_json = (Path.home() / ".kaggle" / "kaggle.json").exists()
    if not token and not has_json:
        return False
    try:
        import kagglehub

        path = Path(kagglehub.dataset_download(slug, force_download=True))
    except Exception as exc:  # network or credential problem - fall back to the public endpoint
        print(f"  kagglehub download failed ({exc}); trying the public endpoint")
        return False
    target.mkdir(parents=True, exist_ok=True)
    for f in path.rglob("*.csv"):
        shutil.copy2(f, target / f.name)
    return True


def download_public(slug: str, target: Path) -> None:
    url = f"https://www.kaggle.com/api/v1/datasets/download/{slug}"
    print(f"  downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "upi-guardian-data-script"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = resp.read()
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for member in z.namelist():
            if member.endswith(".csv"):
                with z.open(member) as src, (target / Path(member).name).open("wb") as dst:
                    shutil.copyfileobj(src, dst)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="download even if the files are present")
    args = ap.parse_args()
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
        if os.getenv("KAGGLE_API_TOKEN"):
            os.environ.setdefault("KAGGLE_API_TOKEN", os.environ["KAGGLE_API_TOKEN"])
    except ImportError:
        pass

    all_ok = True
    for name, meta in DATASETS.items():
        print(f"{name}  (kaggle: {meta['kaggle']})")
        if args.force or not verify(name):
            target = RAW / name
            if not download_kagglehub(meta["kaggle"], target):
                download_public(meta["kaggle"], target)
            all_ok &= verify(name)
    scam = RAW / "upi_scam_sms" / "upi_scam_sms.csv"
    if not scam.exists():
        print("upi_scam_sms: generating from scripts/generate_scam_sms.py")
        import subprocess

        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_scam_sms.py")], check=True)
    print("upi_scam_sms:", "ok" if scam.exists() else "missing")
    print("\nAll datasets verified." if all_ok else "\nSome datasets could not be verified - see above.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
