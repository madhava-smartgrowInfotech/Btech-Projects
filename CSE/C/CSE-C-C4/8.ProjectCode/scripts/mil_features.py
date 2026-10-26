"""Step 2 of the multiple-instance-learning study: bag the real headlines per ticker and trading day and embed them.

Input   data/external/news_10tickers.parquet     (scripts/extract_news.py)
        experiments/data_snapshot/mil/<T>.csv    (scripts/fetch_snapshot.py)
Output  data/external/mil_instances.parquet      one row per (ticker, trading day, headline)
        data/external/mil_features.npy           float16 [n_unique_headlines, 771] = 3 FinBERT-tone probabilities + 768-d [CLS] vector

A headline belongs to the bag of the first trading day whose 16:00 New-York close is not earlier than its timestamp,
so a bag only contains news that was public before that day's close. Day-level stamps (exact UTC midnight) are placed
in the bag of that calendar day (or the next trading day), i.e. also known by that day's close.

    .venv/Scripts/python.exe scripts/mil_features.py
"""
import os
import sys
import time

import torch  # noqa: E402  (before sklearn / transformers on this machine)
import numpy as np
import pandas as pd
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.path.join(ROOT, "data", "external")
PRICES = os.path.join(ROOT, "experiments", "data_snapshot", "mil")
TICKERS = ["TSLA", "AAPL", "AMZN", "MSFT", "GOOGL", "NVDA", "META", "FDX", "IBM", "ORCL"]


def bag_days():
    news = pd.read_parquet(os.path.join(EXT, "news_10tickers.parquet"))
    cal = pd.read_csv(os.path.join(PRICES, "AAPL.csv"), index_col=0, parse_dates=True).index.normalize()
    ts = pd.to_datetime(news["date"], utc=True)
    day_level = (ts.dt.hour == 0) & (ts.dt.minute == 0) & (ts.dt.second == 0)
    ny = ts.dt.tz_convert("America/New_York")
    cal_date = ny.dt.normalize().dt.tz_localize(None)
    after_close = (ny.dt.hour > 16) | ((ny.dt.hour == 16) & (ny.dt.minute > 0))
    cal_date = cal_date + pd.to_timedelta(after_close.astype(int), unit="D")
    utc_date = ts.dt.normalize().dt.tz_localize(None)
    d = np.where(day_level, utc_date, cal_date)
    d = pd.DatetimeIndex(d)
    pos = cal.searchsorted(d)                       # first trading day >= d
    ok = (pos < len(cal)) & (d >= cal[0])
    news = news.loc[ok].copy()
    news["day"] = cal[pos[ok]]
    news["day_level"] = day_level[ok].to_numpy()
    news = news[news.ticker.isin(TICKERS)]
    news = news.drop_duplicates(["ticker", "day", "headline"]).sort_values(["ticker", "day"]).reset_index(drop=True)
    return news


def embed(texts, batch=64, max_len=64):
    tok = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")
    model = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone").eval()
    id2 = {int(k): v.lower() for k, v in model.config.id2label.items()}
    order = [id2[i] for i in range(3)]
    print("FinBERT label order", order, flush=True)
    perm = {"positive": 0, "neutral": 1, "negative": 2}
    idx_map = [order.index(k) for k in ("positive", "neutral", "negative")]
    torch.set_num_threads(max(2, (os.cpu_count() or 8) - 2))
    lens = np.array([len(t) for t in texts])
    out = np.zeros((len(texts), 771), np.float16)
    srt = np.argsort(lens)
    t0 = time.time()
    with torch.no_grad():
        for b in range(0, len(srt), batch):
            ids = srt[b:b + batch]
            enc = tok([texts[i] for i in ids], padding=True, truncation=True, max_length=max_len, return_tensors="pt")
            res = model(**enc, output_hidden_states=True)
            p = torch.softmax(res.logits, -1)[:, idx_map].numpy()
            cls = res.hidden_states[-1][:, 0, :].numpy()
            out[ids, :3] = p
            out[ids, 3:] = cls
            if (b // batch) % 50 == 0:
                print(f"  {b}/{len(srt)}  {time.time() - t0:.0f}s", flush=True)
    return out


def main():
    news = bag_days()
    print(len(news), "headline rows;", news.headline.nunique(), "unique headlines", flush=True)
    print(news.groupby("ticker").size().to_string(), flush=True)
    uniq = news.headline.drop_duplicates().tolist()
    tid = {h: i for i, h in enumerate(uniq)}
    news["text_id"] = news.headline.map(tid).astype(np.int32)
    feats = embed(uniq)
    news[["ticker", "day", "text_id", "day_level", "headline"]].to_parquet(os.path.join(EXT, "mil_instances.parquet"))
    np.save(os.path.join(EXT, "mil_features.npy"), feats)
    print("saved", feats.shape, flush=True)


if __name__ == "__main__":
    sys.exit(main())
