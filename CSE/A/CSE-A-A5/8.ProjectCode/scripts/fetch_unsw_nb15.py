"""Download the official UNSW-NB15 training / testing partition used by the experiments.

Source: the "standard" configuration of the Hugging Face dataset lacg030175/UNSW-NB15, which repackages
the original UNSW Canberra training set (175,341 flows) and testing set (82,332 flows) with all 42
flow features this project uses plus `attack_cat` and `label`.
UNSW-NB15 was created by N. Moustafa and J. Slay (UNSW Canberra Cyber Range Lab, 2015); cite the
original paper when you use it. The files are written to data/external/unsw_nb15/ (git-ignored).

    python scripts/fetch_unsw_nb15.py
"""
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "external" / "unsw_nb15"
BASE = "https://huggingface.co/datasets/lacg030175/UNSW-NB15/resolve/main/standard/"
FILES = {"train.parquet": "train-00000-of-00001.parquet", "test.parquet": "test-00000-of-00001.parquet"}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for local, remote in FILES.items():
        dest = OUT / local
        if dest.exists() and dest.stat().st_size > 1_000_000:
            print(f"have {dest.name} ({dest.stat().st_size:,} bytes)")
            continue
        print(f"downloading {remote} ...")
        urllib.request.urlretrieve(BASE + remote, dest)
        print(f"saved {dest} ({dest.stat().st_size:,} bytes)")
    try:
        import pandas as pd
        tr, te = pd.read_parquet(OUT / "train.parquet"), pd.read_parquet(OUT / "test.parquet")
        print(f"train {tr.shape}, test {te.shape}")
    except Exception as exc:  # pyarrow missing is the usual cause
        print(f"downloaded, but could not read the parquet files ({exc}); pip install 'pyarrow<18'")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
