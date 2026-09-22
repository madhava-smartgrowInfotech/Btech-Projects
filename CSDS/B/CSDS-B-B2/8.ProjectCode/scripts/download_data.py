"""Download the public signal-measurement datasets into data/raw/ and verify them.

Usage:
    python scripts/download_data.py            # download (skips datasets that already verify)
    python scripts/download_data.py --verify   # only check files against data/raw/MANIFEST.json
    python scripts/download_data.py --force    # re-download everything

Both datasets are public on Kaggle and download anonymously. If Kaggle ever requires
authentication, set KAGGLE_USERNAME / KAGGLE_KEY in .env and the script falls back to
kagglehub (see docs/04_DATASET.md for how to create a token).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MANIFEST = RAW / "MANIFEST.json"

DATASETS = {
    "cellular_network_analysis": {
        "kaggle": "suraj520/cellular-network-analysis-dataset",
        "title": "Cellular Network Analysis Dataset",
        "license": "CC0-1.0",
        # strip nothing: the archive holds signal_metrics.csv at its root
        "strip_prefix": "",
    },
    "lte_speed": {
        "kaggle": "aeryss/lte-dataset",
        "title": "4G LTE Speed Dataset",
        "license": "CC BY-SA 4.0",
        # the archive holds Dataset/<mobility>/<trace>.csv - keep <mobility>/<trace>.csv
        "strip_prefix": "Dataset/",
    },
}

DOWNLOAD_URL = "https://www.kaggle.com/api/v1/datasets/download/{ref}"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def fetch_zip_anonymous(ref: str) -> bytes:
    req = urllib.request.Request(DOWNLOAD_URL.format(ref=ref), headers={"User-Agent": "SignalScout-data/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    if not data.startswith(b"PK"):
        raise RuntimeError("response is not a zip archive")
    return data


def fetch_with_kagglehub(ref: str, target: Path) -> None:
    import kagglehub  # imported lazily: only needed for the fallback

    src = Path(kagglehub.dataset_download(ref))
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(src, target)
    nested = target / "Dataset"
    if nested.is_dir():  # flatten the LTE archive layout
        for child in nested.iterdir():
            shutil.move(str(child), target / child.name)
        nested.rmdir()


def extract(data: bytes, target: Path, strip_prefix: str) -> None:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename
            if strip_prefix and name.startswith(strip_prefix):
                name = name[len(strip_prefix):]
            dest = target / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(dest, "wb") as out:
                shutil.copyfileobj(src, out)


def file_table(target: Path) -> dict[str, dict]:
    return {
        p.relative_to(RAW).as_posix(): {"bytes": p.stat().st_size, "sha256": sha256(p)}
        for p in sorted(target.rglob("*"))
        if p.is_file()
    }


def verify(name: str, manifest: dict) -> tuple[bool, str]:
    entry = manifest.get("datasets", {}).get(name)
    if not entry:
        return False, "not in manifest"
    bad = []
    for rel, meta in entry["files"].items():
        path = RAW / rel
        if not path.exists():
            bad.append(f"missing {rel}")
        elif path.stat().st_size != meta["bytes"] or sha256(path) != meta["sha256"]:
            bad.append(f"changed {rel}")
    if bad:
        return False, "; ".join(bad[:5]) + (" ..." if len(bad) > 5 else "")
    return True, f"{len(entry['files'])} files OK"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verify", action="store_true", help="only verify files against the manifest")
    parser.add_argument("--force", action="store_true", help="re-download even if files verify")
    args = parser.parse_args()

    load_env()
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {"datasets": {}}

    if args.verify:
        ok_all = True
        for name in DATASETS:
            ok, msg = verify(name, manifest)
            ok_all &= ok
            print(f"[{'OK' if ok else 'FAIL'}] {name}: {msg}")
        return 0 if ok_all else 1

    for name, spec in DATASETS.items():
        target = RAW / name
        if not args.force and name in manifest.get("datasets", {}):
            ok, msg = verify(name, manifest)
            if ok:
                print(f"[SKIP] {name}: already present ({msg})")
                continue
        print(f"[....] {name}: downloading {spec['kaggle']}")
        try:
            extract(fetch_zip_anonymous(spec["kaggle"]), target, spec["strip_prefix"])
        except Exception as exc:  # anonymous download blocked -> authenticated fallback
            print(f"       anonymous download failed ({exc}); trying kagglehub with your Kaggle token")
            if not (os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY")):
                print("       KAGGLE_USERNAME / KAGGLE_KEY are not set - see docs/04_DATASET.md")
                return 1
            fetch_with_kagglehub(spec["kaggle"], target)
        files = file_table(target)
        manifest["datasets"][name] = {
            "title": spec["title"],
            "source": f"https://www.kaggle.com/datasets/{spec['kaggle']}",
            "license": spec["license"],
            "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "total_bytes": sum(f["bytes"] for f in files.values()),
            "files": files,
        }
        print(f"[OK]   {name}: {len(files)} files, {manifest['datasets'][name]['total_bytes'] / 1e6:.1f} MB")

    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Manifest written to {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
