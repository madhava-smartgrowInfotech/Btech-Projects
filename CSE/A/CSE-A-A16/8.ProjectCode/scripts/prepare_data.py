"""Copy an evenly spaced subset of the Kaggle "ASL Alphabet" training set into data/<CLASS>/.

The Kaggle images come from video, so neighbouring files are near-duplicates; sampling every Nth file
gives more variety per image. Usage:
    python scripts/prepare_data.py [archive_dir] [per_class]
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "archive" / "asl_alphabet_train" / "asl_alphabet_train"
per_class = int(sys.argv[2]) if len(sys.argv) > 2 else 250
dst = ROOT / "data"

if not src.is_dir():
    sys.exit(f"Source folder not found: {src}")

total = 0
for folder in sorted(p for p in src.iterdir() if p.is_dir()):
    files = sorted(folder.glob("*.jpg"))
    if not files:
        continue
    step = max(1, len(files) // per_class)
    picked = files[::step][:per_class]
    out = dst / folder.name
    out.mkdir(parents=True, exist_ok=True)
    for f in picked:
        shutil.copy2(f, out / f.name)
    total += len(picked)
    print(f"{folder.name:8s} {len(picked)} of {len(files)}")
print(f"copied {total} images into {dst}")
