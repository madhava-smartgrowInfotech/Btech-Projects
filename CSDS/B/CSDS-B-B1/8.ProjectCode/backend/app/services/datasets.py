"""Load the raw datasets into one tidy training table with fixed, seeded splits."""
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from ..config import RAW_DIR, SEED
from .taxonomy import CATEGORY_TO_DEPT, CIVICCOMP_PRIMARY, CIVICCOMP_SECONDARY, GRIEVANCE, INDIAN, NYC_TYPES

CRITICAL_SCORE = 11  # CivicComp HIGH rows with severity_score >= 11 (~2.4% of rows) become Critical


def _civiccomp_category(row):
    return CIVICCOMP_SECONDARY.get(row.category_secondary) or CIVICCOMP_PRIMARY.get(row.category_primary)


def _priority(row):
    if row.severity == "HIGH":
        return "Critical" if row.severity_score >= CRITICAL_SCORE else "High"
    return {"LOW": "Low", "MEDIUM": "Medium"}[row.severity]


def load_civiccomp():
    """16k real complaints, each in English, Hindi and Hinglish -> 48k rows."""
    df = pd.read_csv(RAW_DIR / "civiccomp_hien.csv.gz")
    df["category"] = df.apply(_civiccomp_category, axis=1)
    df["priority"] = df.apply(_priority, axis=1)
    # split by complaint id so the three translations of one complaint stay together
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED)
    _, test_idx = next(gss.split(df, groups=df.original_id))
    df["split"] = "train"
    df.loc[df.index[test_idx], "split"] = "test"
    parts = []
    for col, lang in [("text_en", "English"), ("Hindi", "Hindi"), ("Hinglish", "Hinglish")]:
        p = df[["original_id", "category", "priority", "split", "Complain_date"]].copy()
        p["text"] = df[col].astype(str)
        p["lang"] = lang
        parts.append(p)
    out = pd.concat(parts, ignore_index=True).rename(columns={"original_id": "group"})
    out["source"] = "civiccomp"
    return out[out.text.str.len() > 5]


def load_grievance():
    df = pd.read_csv(RAW_DIR / "citizen_grievance.csv")
    rng = np.random.default_rng(SEED)
    df["split"] = np.where(rng.random(len(df)) < 0.2, "test", "train")
    hold = pd.read_csv(RAW_DIR / "citizen_grievance_holdout.csv")
    hold["split"] = "holdout"
    df = pd.concat([df, hold], ignore_index=True)
    df["category"] = df.category.map(GRIEVANCE)
    df["group"] = df.grievance_id
    df["lang"] = None  # mixed-script; detected per row later
    df["source"] = "grievance"
    return df[["group", "text", "category", "split", "lang", "source"]]


def load_indian():
    df = pd.read_csv(RAW_DIR / "indian_citizen_complaint.csv.gz")
    rng = np.random.default_rng(SEED + 1)
    df["split"] = np.where(rng.random(len(df)) < 0.2, "test", "train")
    df["category"] = df.label.map(INDIAN)
    # these are long write-ups; the opening paragraph carries the topic
    df["text"] = df.text.astype(str).str.slice(0, 700)
    df["group"] = "IC" + df.id.astype(str)
    df["lang"] = "English"
    df["source"] = "indian_complaint"
    return df[["group", "text", "category", "split", "lang", "source"]]


def load_text_dataset():
    """Rows: text, category, department, split (train/test/holdout), lang, source."""
    from .textutil import detect_language

    df = pd.concat([load_civiccomp(), load_grievance(), load_indian()], ignore_index=True)
    df = df[df.category.notna()].copy()
    df["department"] = df.category.map(CATEGORY_TO_DEPT)
    missing = df.lang.isna()
    df.loc[missing, "lang"] = df.loc[missing, "text"].map(detect_language)
    return df.reset_index(drop=True)


def load_nyc():
    """NYC 311 closed requests -> category, created time and days to close."""
    df = pd.read_csv(RAW_DIR / "nyc311_resolution.csv.gz")
    df["created"] = pd.to_datetime(df.created_date, errors="coerce")
    df["closed"] = pd.to_datetime(df.closed_date, errors="coerce")
    df["days"] = (df.closed - df.created).dt.total_seconds() / 86400
    df = df[(df.days > 0) & (df.days <= 180)].copy()
    rows = []
    for cat, types in NYC_TYPES.items():
        part = df[df.complaint_type.isin(types)].copy()
        part["category"] = cat
        rows.append(part)
    out = pd.concat(rows, ignore_index=True)
    out["text"] = out.complaint_type.astype(str) + " - " + out.descriptor.fillna("").astype(str)
    # time-based split: the last two months are the test set
    out["split"] = np.where(out.created >= "2026-01-01", "test", "train")
    return out[["category", "text", "created", "days", "split", "complaint_type"]]
