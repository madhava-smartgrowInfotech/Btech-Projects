"""Rebuild every model from the committed datasets, in order (about 3 minutes on a laptop CPU).

    python ml/train_all.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ["prepare_data.py", "train_classifier.py", "train_throughput_model.py", "train_gp.py"]


def main() -> int:
    for step in STEPS:
        print(f"\n=== {step} ===", flush=True)
        if subprocess.run([sys.executable, str(HERE / step)], cwd=HERE.parent).returncode != 0:
            print(f"{step} failed - stopping")
            return 1
    print("\nAll models trained. Results are in experiments/ and the files the app loads are in models/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
