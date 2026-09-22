"""Trains every UPI Guardian model in the right order and writes the model cards.

    1. profile_upi2024.py   UPI Transactions 2024 label check + behaviour profiles
    2. train_behaviour.py   M1 behaviour model (Digital Payment Fraud Detection Benchmark)
    3. train_sms.py         M2 SMS scam classifier (SMS Spam Collection + Indian UPI-scam set)
    4. train_risk.py        M3 payment risk model (scenario simulator using M1 + M2)

Run: venv\\Scripts\\python ml\\train_all.py   (about 15 minutes on a 6-core CPU)
Add --skip-nn to leave out the contrastive network comparison in step 2.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ML = Path(__file__).resolve().parent
ROOT = ML.parent


def step(script: str, *args: str) -> None:
    print(f"\n=== {script} {' '.join(args)} ===", flush=True)
    started = time.time()
    result = subprocess.run([sys.executable, str(ML / script), *args], cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"{script} failed with exit code {result.returncode}")
    print(f"=== {script} finished in {time.time() - started:.0f}s ===", flush=True)


def latest(family_prefix: str) -> Path:
    runs = sorted((ROOT / "experiments").glob(f"{family_prefix}_*/metrics.json"))
    if not runs:
        raise SystemExit(f"no metrics for {family_prefix}")
    return runs[-1]


def write_model_cards() -> None:
    cards = {}
    for key, prefix in [("profile", "m0_upi2024"), ("behaviour", "m1_behaviour"), ("sms", "m2_sms"), ("risk", "m3_risk")]:
        path = latest(prefix)
        cards[key] = {"run": path.parent.name, "metrics_file": path.relative_to(ROOT).as_posix()}
    (ROOT / "models" / "model_cards.json").write_text(json.dumps(cards, indent=2), encoding="utf-8")
    print("model cards written to models/model_cards.json")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-nn", action="store_true")
    args = ap.parse_args()
    (ROOT / "models").mkdir(exist_ok=True)
    step("profile_upi2024.py")
    step("train_behaviour.py", *(["--skip-nn"] if args.skip_nn else []))
    step("train_sms.py")
    step("train_risk.py", "--regenerate")
    write_model_cards()
    print("\nAll models trained. Restart the API (run.bat) to load them.")


if __name__ == "__main__":
    main()
