"""
make_real_subset.py
--------------------
Builds a REAL-data subset in the exact H&M CSV schema the app expects, from the public
H&M Personalized Fashion Recommendations dataset (Kaggle competition data; the parquet mirror on
Hugging Face `dinhlnd1610/HM-Personalized-Fashion-Recommendations` is used for download).

Subset rule (documented in docs/REPORT_FACTS.md):
  * the first transactions shard (transactions/train-00000-of-00007.parquet = 2018-09-20 .. 2019-01-04)
  * the N best-selling articles of that shard, with ALL their transactions
  * customer ids are shortened to their first 16 hex characters (file size only)

    python scripts/make_real_subset.py --raw <folder with articles.parquet + tx0.parquet> [--top 300]

Output: data/real_hm/{transactions_train.csv, articles.csv}  (git-ignored, not redistributed)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--top", type=int, default=300)
    ap.add_argument("--out", default=str(ROOT / "data" / "real_hm"))
    a = ap.parse_args()
    raw, out = Path(a.raw), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    tx = pd.read_parquet(raw / "tx0.parquet")
    art = pd.read_parquet(raw / "articles.parquet")
    print(f"shard rows {len(tx):,}  dates {tx.t_dat.min()} .. {tx.t_dat.max()}  articles sold {tx.article_id.nunique():,}")

    top_ids = tx["article_id"].value_counts().head(a.top).index
    sub = tx[tx["article_id"].isin(top_ids)].copy()
    sub["customer_id"] = sub["customer_id"].str[:16]
    sub = sub.sort_values("t_dat", kind="stable")
    sub.to_csv(out / "transactions_train.csv", index=False)
    art[art["article_id"].isin(top_ids)].to_csv(out / "articles.csv", index=False)
    print(f"subset rows {len(sub):,}  articles {len(top_ids)}  -> {out}")
    print(sub.groupby("sales_channel_id").size())


if __name__ == "__main__":
    main()
