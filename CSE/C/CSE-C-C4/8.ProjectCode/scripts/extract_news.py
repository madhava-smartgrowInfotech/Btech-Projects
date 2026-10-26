"""Extract real financial-news headlines for the ten QuantPulse tickers from the public FNSPID news portion.

Source: Zihan1004/FNSPID news (mirrored inside idleengine/financial-news-multisource, subset ``fnspid_news``).
Only the shards that reach 2023 are read (027-031); each row is kept when its ``stocks`` list names one of the ten
tickers (``FB`` is the pre-2022 symbol of META). The text is cut to its first line (the headline, at most 300
characters), so no article bodies are stored.

    .venv/Scripts/python.exe scripts/extract_news.py            # writes data/external/news_10tickers.parquet
"""
import json
import os
import re
import sys

import pandas as pd
import pyarrow.parquet as pq
from huggingface_hub import HfFileSystem

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "external", "news_10tickers.parquet")
TICKERS = ["TSLA", "AAPL", "AMZN", "MSFT", "GOOGL", "NVDA", "META", "FB", "FDX", "IBM", "ORCL"]
SHARDS = [27, 28, 29, 30, 31]
BASE = "datasets/idleengine/financial-news-multisource/data/fnspid_news/fnspid_news.{:03d}.parquet"
PAT = re.compile(r'"(' + "|".join(TICKERS) + r')"')
START = "2016-01-01"


def main():
    fs = HfFileSystem()
    rows = []
    for k in SHARDS:
        path = BASE.format(k)
        n_in = n_keep = 0
        with fs.open(path, "rb") as f:
            pf = pq.ParquetFile(f)
            for batch in pf.iter_batches(batch_size=20000, columns=["date", "text", "extra_fields"]):
                d = batch.to_pydict()
                for date, text, ex in zip(d["date"], d["text"], d["extra_fields"]):
                    n_in += 1
                    if date < START or not ex or not PAT.search(ex):
                        continue
                    try:
                        stocks = json.loads(ex).get("stocks") or []
                    except Exception:
                        continue
                    hit = [s for s in stocks if s in TICKERS]
                    if not hit:
                        continue
                    head = (text or "").strip().split("\n")[0][:300]
                    if len(head) < 12:
                        continue
                    for s in hit:
                        rows.append((date, "META" if s == "FB" else s, head))
                    n_keep += 1
        print(f"shard {k}: read {n_in:,} rows, kept {n_keep:,}", flush=True)
        pd.DataFrame(rows, columns=["date", "ticker", "headline"]).to_parquet(OUT + ".partial")
    df = pd.DataFrame(rows, columns=["date", "ticker", "headline"])
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    df = df.dropna().drop_duplicates(["ticker", "headline", "date"]).sort_values("date")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    df.to_parquet(OUT)
    print(len(df), "rows ->", OUT)
    print(df.groupby("ticker").size().to_string())
    print(df.groupby(df.date.dt.year).size().to_string())


if __name__ == "__main__":
    sys.exit(main())
