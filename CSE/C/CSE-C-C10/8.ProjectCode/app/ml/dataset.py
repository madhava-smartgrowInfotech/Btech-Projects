"""Dataset loading with Kaggle-attempt + synthetic fallback (same schema)."""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

from app.config import (
    DATA_RAW,
    DATA_SAMPLE,
    RANDOM_STATE,
    KAGGLE_DATASET,
    TARGET_COL_CANDIDATES,
)

log = logging.getLogger(__name__)

EXPECTED_COLUMNS = [
    "age_first_funding_year", "age_last_funding_year",
    "age_first_milestone_year", "age_last_milestone_year",
    "relationships", "funding_rounds", "funding_total_usd", "milestones",
    "avg_participants", "has_VC", "has_angel", "has_roundA", "has_roundB",
    "has_roundC", "has_roundD", "is_top500",
    "state", "industry_type", "description", "status",
]

STATES = ["CA", "NY", "MA", "TX", "WA", "IL", "CO", "FL", "PA", "OR"]
INDUSTRIES = ["Software", "E-Commerce", "FinTech", "HealthTech", "EdTech",
              "CleanTech", "Media", "Mobile", "AI", "Biotech"]

DESC_TEMPLATES_SUCCESS = [
    "This company builds a {industry} platform for {market} with a subscription business model, proprietary {tech} technology, growing traction and repeat customers.",
    "A {industry} service targeting {market}, offering differentiated {tech} features, early revenue, partnerships and expanding market opportunity.",
    "This company operates a {industry} marketplace for {market} with improving unit economics, scalable {tech} infrastructure and a focused growth plan.",
]
DESC_TEMPLATES_FAILURE = [
    "This company offers a {industry} product for {market} with mixed early traction, evolving pricing and ongoing efforts to find repeatable growth.",
    "A {industry} offering aimed at {market} with a developing business model, early {tech} capabilities and gradual user adoption.",
    "This company built a {industry} tool for {market} and is working through positioning, pricing and partnership challenges.",
]
DESC_TEMPLATES_SHARED = [
    "This company is a {industry} venture serving {market}, building {tech} products and iterating on product, pricing and distribution.",
    "A {industry} startup focused on {market}, developing {tech} solutions and pursuing partnerships and customer growth.",
    "This company provides {industry} services to {market} with an emphasis on {tech}, customer feedback and operational execution.",
]
MARKETS = ["small businesses", "enterprises", "consumers", "clinics", "schools", "retailers", "developers"]
TECHS = ["cloud analytics", "mobile payments", "machine learning", "logistics optimization", "content delivery"]


def find_local_csv() -> Path | None:
    if not DATA_RAW.exists():
        return None
    cands = [p for p in sorted(DATA_RAW.glob("*.csv"))
             if "sample" not in p.name.lower() and "synthetic" not in p.name.lower()]
    if not cands:
        return None
    # prefer the largest file (a real dataset over fragments)
    try:
        return max(cands, key=lambda p: p.stat().st_size)
    except Exception:
        return cands[0]


def try_kaggle_download() -> Path | None:
    """Attempt Kaggle download via kagglehub or kaggle CLI. Returns csv path or None."""
    try:
        import kagglehub  # type: ignore
        try:
            path = kagglehub.dataset_download(KAGGLE_DATASET)
            p = Path(path)
            csvs = list(p.glob("*.csv")) if p.is_dir() else [p]
            if csvs:
                dest = DATA_RAW / csvs[0].name
                DATA_RAW.mkdir(parents=True, exist_ok=True)
                if str(csvs[0]) != str(dest):
                    import shutil
                    shutil.copy(csvs[0], dest)
                log.info("Kaggle dataset downloaded via kagglehub.")
                return dest
        except Exception as e:
            log.info("kagglehub download unavailable: %s", e)
    except Exception:
        log.info("kagglehub not installed.")
    return None


def detect_target_column(df: pd.DataFrame) -> str | None:
    cols = {c.strip(): c for c in df.columns}
    for cand in TARGET_COL_CANDIDATES:
        if cand in cols:
            return cols[cand]
    for c in df.columns:
        if "status" in c.lower() or "outcome" in c.lower():
            return c
    return None


def map_target(series: pd.Series) -> pd.Series:
    def conv(v):
        s = str(v).strip().lower()
        if s in ("acquired", "success", "1", "true", "yes", "ipo", "acquisition"):
            return 1
        if s in ("closed", "failure", "0", "false", "no", "close"):
            return 0
        return np.nan
    return series.apply(conv)


def generate_synthetic(n: int = 1400, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    success = rng.random(n) < 0.42
    rows = []
    for i in range(n):
        s = bool(success[i])
        industry = str(rng.choice(INDUSTRIES))
        state = str(rng.choice(STATES))
        funding_rounds = int(np.clip(rng.poisson(2.2 if s else 1.8) + (1 if (s and rng.random() < 0.3) else 0), 0, 8))
        funding_total = float(np.clip(rng.lognormal(13.8 if s else 13.2, 1.5), 5e3, 9e7))
        relationships = int(np.clip(rng.poisson(5 if s else 4), 0, 30))
        milestones = int(np.clip(rng.poisson(2.6 if s else 1.8), 0, 10))
        age_first_fund = float(np.clip(rng.normal(1.7 if s else 1.9, 1.2), 0, 8))
        age_last_fund = float(age_first_fund + np.clip(rng.exponential(1.3 if s else 1.0), 0, 7))
        age_first_ms = float(np.clip(rng.normal(1.3 if s else 1.5, 1.1), 0, 8))
        age_last_ms = float(age_first_ms + np.clip(rng.exponential(1.1 if s else 0.9), 0, 7))
        avg_part = float(np.clip(rng.normal(4.0 if s else 3.4, 2.0), 1, 12))
        has_vc = int(rng.random() < (0.60 if s else 0.40))
        has_angel = int(rng.random() < (0.50 if s else 0.40))
        rA = int(rng.random() < (0.60 if s else 0.45))
        rB = int(rng.random() < (0.40 if s else 0.25))
        rC = int(rng.random() < (0.25 if s else 0.12))
        rD = int(rng.random() < (0.12 if s else 0.06))
        top500 = int(rng.random() < (0.20 if s else 0.12))
        u = rng.random()
        if u < 0.35:
            pool = DESC_TEMPLATES_SHARED
        elif u < 0.80:
            pool = DESC_TEMPLATES_SUCCESS if s else DESC_TEMPLATES_FAILURE
        else:  # cross-assigned wording keeps text from perfectly separating classes
            pool = DESC_TEMPLATES_FAILURE if s else DESC_TEMPLATES_SUCCESS
        tpl = str(rng.choice(pool))
        desc = tpl.format(industry=industry.lower(), market=str(rng.choice(MARKETS)), tech=str(rng.choice(TECHS)))
        rows.append({
            "age_first_funding_year": age_first_fund,
            "age_last_funding_year": age_last_fund,
            "age_first_milestone_year": age_first_ms,
            "age_last_milestone_year": age_last_ms,
            "relationships": relationships,
            "funding_rounds": funding_rounds,
            "funding_total_usd": funding_total,
            "milestones": milestones,
            "avg_participants": avg_part,
            "has_VC": has_vc, "has_angel": has_angel,
            "has_roundA": rA, "has_roundB": rB, "has_roundC": rC, "has_roundD": rD,
            "is_top500": top500,
            "state": state, "industry_type": industry,
            "description": desc,
            "status": "acquired" if s else "closed",
        })
    return pd.DataFrame(rows)


def clean_text(t: str) -> str:
    if not isinstance(t, str):
        return ""
    t = re.sub(r"\b[A-Z][a-zA-Z0-9&'\-]*(?:\s+[A-Z][a-zA-Z0-9&'\-]*){0,3}\s+(Inc|LLC|Labs|Technologies|Systems)\b", "this company", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:2000]


def normalize_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    # unify known variants
    rename = {}
    for c in df.columns:
        lc = c.lower().strip()
        if lc in ("state_code", "statecode", "region"):
            rename[c] = "state"
        if lc in ("category", "industry", "sector"):
            rename[c] = "industry_type"
        if lc in ("funding_total", "total_funding_usd"):
            rename[c] = "funding_total_usd"
    if rename:
        df = df.rename(columns=rename)
    target = detect_target_column(df)
    if target is None:
        raise ValueError("No outcome column found (expected a status-like column).")
    if target != "status":
        df = df.rename(columns={target: "status"})
    # ensure expected columns exist
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            if col == "description":
                df[col] = ""
            elif col in ("state", "industry_type"):
                df[col] = "Unknown"
            else:
                df[col] = 0
    return df, "status"


def load_dataset(force_synthetic: bool = False) -> tuple[pd.DataFrame, dict]:
    """Returns (df, meta). meta includes source + target mapping info."""
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    meta: dict = {"kaggle_source": KAGGLE_DATASET, "synthetic_fallback": False}
    if not force_synthetic:
        local = find_local_csv()
        if local is not None:
            try:
                df = pd.read_csv(local)
                df, _ = normalize_frame(df)
                meta.update({"source": f"local_csv:{local.name}"})
                return df, meta
            except Exception as e:
                log.warning("Local CSV failed (%s); continuing.", e)
        dl = try_kaggle_download()
        if dl is not None:
            try:
                df = pd.read_csv(dl)
                df, _ = normalize_frame(df)
                meta.update({"source": "kaggle"})
                return df, meta
            except Exception as e:
                log.warning("Kaggle CSV failed (%s); using synthetic fallback.", e)
    df = generate_synthetic()
    meta.update({"source": "synthetic_fallback", "synthetic_fallback": True,
                 "note": "Public dataset unavailable; generated realistic synthetic data with the same schema."})
    # persist sample for transparency
    DATA_SAMPLE.mkdir(parents=True, exist_ok=True)
    df.head(50).to_csv(DATA_SAMPLE / "sample_startups.csv", index=False)
    (DATA_RAW / "SYNTHETIC_FALLBACK.txt").write_text(
        "Synthetic fallback dataset in use (same schema as Startup Success Prediction). See README.", encoding="utf-8")
    return df, meta
