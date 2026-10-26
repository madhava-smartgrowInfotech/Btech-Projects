"""Pin the price data used by the documentation experiments (Yahoo Finance daily OHLCV, unadjusted Close).

    experiments/data_snapshot/<T>.csv       2024-09-09 .. 2026-10-23  (the QuantPulse window; shipped models trained on rows up to 2026-09-08)
    experiments/data_snapshot/mil/<T>.csv   2016-01-01 .. 2023-12-31  (the multiple-instance-learning study, overlaps the FNSPID news)

The application re-downloads and overwrites ``data/*.csv`` on every API call, so the experiments never read that folder.
"""
import os
import sys

import pandas as pd
import yfinance as yf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TICKERS = ["TSLA", "AAPL", "AMZN", "MSFT", "GOOGL", "NVDA", "META", "FDX", "IBM", "ORCL"]


def pull(t, start, end):
    df = yf.download(t, start=start, end=end, progress=False, auto_adjust=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df = df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]].dropna()
    df.index.name = "Date"
    return df


def main():
    a = os.path.join(ROOT, "experiments", "data_snapshot")
    b = os.path.join(a, "mil")
    os.makedirs(b, exist_ok=True)
    for t in TICKERS:
        d1 = pull(t, "2024-09-09", "2026-10-24")
        d1.to_csv(os.path.join(a, f"{t}.csv"))
        d2 = pull(t, "2016-01-01", "2024-01-01")
        d2.to_csv(os.path.join(b, f"{t}.csv"))
        print(t, len(d1), d1.index[0].date(), d1.index[-1].date(), "|", len(d2), d2.index[0].date(), d2.index[-1].date(), flush=True)


if __name__ == "__main__":
    sys.exit(main())
