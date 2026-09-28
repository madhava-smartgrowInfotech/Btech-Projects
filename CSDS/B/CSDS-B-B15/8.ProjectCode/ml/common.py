"""Shared helpers for loading the committed datasets."""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MODELS = ROOT / "models"
EXPERIMENTS = ROOT / "experiments"


def clean_symptom(s: str) -> str:
    s = re.sub(r"\s*_\s*", "_", str(s).strip())
    return re.sub(r"\s+", "_", s).lower()


def load_symptom_rows():
    """Return list of (disease, [symptoms]) from the Disease Symptom Prediction dataset."""
    df = pd.read_csv(DATA / "disease_symptom" / "dataset.csv")
    rows = []
    for _, r in df.iterrows():
        syms = sorted({clean_symptom(v) for v in r.iloc[1:].dropna() if str(v).strip()})
        rows.append((r["Disease"].strip(), syms))
    return rows


def load_severity_weights():
    df = pd.read_csv(DATA / "disease_symptom" / "Symptom-severity.csv")
    return {clean_symptom(s): int(w) for s, w in zip(df["Symptom"], df["weight"])}


def load_noshow():
    df = pd.read_csv(DATA / "noshow" / "KaggleV2-May-2016.csv")
    sched = pd.to_datetime(df["ScheduledDay"]).dt.tz_localize(None).dt.normalize()
    appt = pd.to_datetime(df["AppointmentDay"]).dt.tz_localize(None).dt.normalize()
    out = pd.DataFrame({
        "age": df["Age"].clip(0, 100),
        "is_female": (df["Gender"] == "F").astype(int),
        "lead_days": (appt - sched).dt.days,
        "weekday": appt.dt.weekday,
        "sms_received": df["SMS_received"],
        "scholarship": df["Scholarship"],
        "hypertension": df["Hipertension"],
        "diabetes": df["Diabetes"],
        "alcoholism": df["Alcoholism"],
        "handicap": (df["Handcap"] > 0).astype(int),
        "no_show": (df["No-show"] == "Yes").astype(int),
    })
    return out[out["lead_days"] >= 0].reset_index(drop=True)


NOSHOW_FEATURES = ["age", "is_female", "lead_days", "weekday", "sms_received", "scholarship",
                   "hypertension", "diabetes", "alcoholism", "handicap"]
