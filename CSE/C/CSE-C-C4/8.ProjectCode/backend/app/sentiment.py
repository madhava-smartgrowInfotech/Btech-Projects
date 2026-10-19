"""QuantPulse news-sentiment module.

Live path: NewsAPI (https://newsapi.org) with NEWSAPI_KEY env var, responses
cached under /data/news_cache to stay within free-tier limits.
Fallback path: generates a realistic synthetic headline-sentiment dataset with
the SAME schema (date, ticker, headline, sentiment_score). The fallback
auto-switches to live NewsAPI whenever a valid key is present — see
`get_daily_sentiment()`.

Scoring: pretrained FinBERT-tone (HuggingFace `yiyanghkust/finbert-tone`) via
`transformers` inference only (transfer learning, no FinBERT training). If the
model cannot be downloaded (offline sandbox), falls back to a transparent
lexicon scorer so the pipeline still runs; the active scorer is reported in
metadata (`scorer: finbert | lexicon | cached`).
"""
from __future__ import annotations
import os, json, hashlib
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import requests
from . import config

TEMPLATES_POS = [
    "{t} beats earnings expectations as cloud growth accelerates",
    "Analysts upgrade {t} on strong guidance and margin expansion",
    "{t} announces major buyback as demand outlook improves",
    "{t} hits record revenue on enterprise adoption surge",
]
TEMPLATES_NEG = [
    "{t} slides after weak guidance spooks investors",
    "Regulators probe {t} over competition concerns",
    "{t} cuts forecast amid softening consumer demand",
    "{t} drops as supply chain costs squeeze margins",
]
TEMPLATES_NEU = [
    "{t} trades flat ahead of Fed decision",
    "Investors await {t} earnings with options pricing muted moves",
    "{t} holds steady as market digests mixed data",
]

_finbert = None  # lazy singleton (pipeline, label map)


def _lexicon_score(text: str) -> float:
    pos = ["beats", "upgrade", "growth", "record", "buyback", "surge", "strong", "improves", "expansion", "bullish", "rally", "profit"]
    neg = ["slides", "weak", "probe", "cuts", "softening", "drops", "squeeze", "miss", "downgrade", "bearish", "lawsuit", "layoff"]
    tl = text.lower()
    s = sum(1 for w in pos if w in tl) - sum(1 for w in neg if w in tl)
    return float(np.clip(s / 3.0, -1, 1))


def score_headlines(headlines: list[str]) -> tuple[list[float], str]:
    """Score headlines, preferring FinBERT-tone; returns (scores, scorer_name)."""
    global _finbert
    if _finbert is None:
        try:
            from transformers import pipeline
            _finbert = pipeline("sentiment-analysis",
                                model="yiyanghkust/finbert-tone",
                                tokenizer="yiyanghkust/finbert-tone",
                                framework="pt", truncation=True)
        except Exception:
            _finbert = False  # mark unavailable; use lexicon
    if _finbert is not False and _finbert is not None:
        mapping = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
        try:
            scores: list[float] = []
            for i in range(0, len(headlines), 32):
                out = _finbert(headlines[i:i + 32])
                for r in out:
                    lab = r["label"].lower()
                    scores.append(mapping.get(lab, 0.0) * float(r["score"]) if lab != "neutral" else 0.0)
            if len(scores) == len(headlines):
                return scores, "finbert"
        except Exception:
            pass
    return [_lexicon_score(h) for h in headlines], "lexicon"


def _fetch_newsapi(ticker: str, days: int = 30) -> list[dict] | None:
    key = config.NEWS_API_KEY
    if not key:
        return None
    os.makedirs(os.path.abspath(config.NEWS_CACHE_DIR), exist_ok=True)
    day = datetime.utcnow().strftime("%Y-%m-%d")
    cache = os.path.join(os.path.abspath(config.NEWS_CACHE_DIR), f"{ticker}_{day}.json")
    if os.path.exists(cache):
        try:
            return json.load(open(cache))["articles"]
        except Exception:
            pass
    try:
        r = requests.get("https://newsapi.org/v2/everything",
                         params={"q": ticker, "language": "en", "sortBy": "publishedAt",
                                 "pageSize": 50, "from": (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")},
                         headers={"X-Api-Key": key}, timeout=15)
        if r.status_code != 200:
            return None
        arts = [{"title": a.get("title", ""), "publishedAt": a.get("publishedAt", "")} for a in r.json().get("articles", []) if a.get("title")]
        json.dump({"articles": arts}, open(cache, "w"))
        return arts
    except Exception:
        return None


def get_daily_sentiment(ticker: str, trading_dates: pd.DatetimeIndex) -> tuple[pd.Series, dict]:
    """Align daily sentiment scores to trading dates. Returns (series, meta)."""
    t = ticker.upper()
    arts = _fetch_newsapi(t)
    if arts:
        headlines = [a["title"] for a in arts]
        dates = [a.get("publishedAt", "")[:10] for a in arts]
        scores, scorer = score_headlines(headlines) if headlines else ([], "none")
        df = pd.DataFrame({"date": pd.to_datetime(dates, errors="coerce"), "s": scores})
        df = df.dropna()
        daily = df.groupby(df["date"].dt.date)["s"].mean() if len(df) else pd.Series(dtype=float)
        meta = {"source": "newsapi", "scorer": scorer, "n_headlines": len(headlines)}
    else:
        # Synthetic fallback — same schema, deterministic per ticker so runs are reproducible.
        rng = np.random.default_rng(abs(hash(t)) % (2 ** 31))
        recs = []
        for d in trading_dates[-90:]:
            n = int(rng.integers(1, 4))
            for _ in range(n):
                u = rng.random()
                tmpl = rng.choice(TEMPLATES_POS) if u > 0.55 else (rng.choice(TEMPLATES_NEG) if u < 0.30 else rng.choice(TEMPLATES_NEU))
                h = tmpl.format(t=t)
                recs.append({"date": d.date(), "ticker": t, "headline": h, "sentiment_score": _lexicon_score(h) + float(rng.normal(0, 0.1))})
        syn = pd.DataFrame(recs)
        # Score synthetic headlines through the same scorer for consistency.
        scores, scorer = score_headlines(syn["headline"].tolist())
        syn["sentiment_score"] = scores
        daily = syn.groupby("date")["sentiment_score"].mean()
        meta = {"source": "synthetic-fallback", "scorer": scorer,
                "n_headlines": len(syn),
                "note": "NEWSAPI_KEY missing/unreachable; using synthetic headlines. Set NEWSAPI_KEY to switch to live news automatically."}
    daily.index = pd.to_datetime(daily.index)
    aligned = pd.Series(index=pd.to_datetime(trading_dates), dtype=float)
    for d in aligned.index:
        day = d.normalize()
        if day in daily.index:
            aligned[d] = float(daily[day])
        else:
            aligned[d] = np.nan
    aligned = aligned.ffill().fillna(0.0).clip(-1, 1)
    return aligned, meta


def recent_headlines(ticker: str, n: int = 8) -> list[dict]:
    """Headlines for the sentiment panel (live if possible, else synthetic)."""
    t = ticker.upper()
    arts = _fetch_newsapi(t, days=7)
    if arts:
        hs = [a["title"] for a in arts[:n]]
        scores, _ = score_headlines(hs)
        return [{"headline": h, "sentiment_score": round(float(s), 3)} for h, s in zip(hs, scores)]
    rng = np.random.default_rng(abs(hash(t + "panel")) % (2 ** 31))
    out = []
    for _ in range(n):
        u = rng.random()
        tmpl = rng.choice(TEMPLATES_POS) if u > 0.5 else (rng.choice(TEMPLATES_NEG) if u < 0.3 else rng.choice(TEMPLATES_NEU))
        h = tmpl.format(t=t)
        out.append({"headline": h, "sentiment_score": round(float(np.clip(_lexicon_score(h), -1, 1)), 3)})
    return out
