"""
Data preparation helper: checks for UNSW-NB15 CSVs in data/raw, else notes synthetic fallback.
Run with: python scripts/prepare_data.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cipherguard.ids.synthetic import generate_synthetic

base = Path(__file__).resolve().parents[1]
raw = base / "data" / "raw"
raw.mkdir(parents=True, exist_ok=True)
csvs = list(raw.glob("*.csv"))
print(f"Found {len(csvs)} CSVs in {raw}")
for c in csvs:
    print(" -", c.name)
if not csvs:
    print("No CSVs found. Generating synthetic demo dataset...")
    df = generate_synthetic(n_normal=6000, n_attack=6000)
    out = raw / "synthetic_demo.csv"
    df.to_csv(out, index=False)
    print(f"Synthetic saved to {out} ({len(df)} rows)")
    print("To use real UNSW-NB15: download UNSW_NB15_training-set.csv and UNSW_NB15_testing-set.csv from https://research.unsw.edu.au/projects/unsw-nb15-dataset and drop them into data/raw/, then run: python -m cipherguard.ids.train")
else:
    print("Place additional UNSW-NB15 CSVs into data/raw/ and retrain with: python -m cipherguard.ids.train")
