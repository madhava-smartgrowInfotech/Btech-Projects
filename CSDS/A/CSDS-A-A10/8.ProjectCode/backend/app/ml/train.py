"""
Trains the two models MedFlow's prediction service depends on:

1. Wait-time regressor — predicts how many minutes a newly queued patient
   will wait, given how busy their department currently is, the time of
   day and their triage priority.
2. Triage classifier — learns to approximate a clinical early-warning
   score (a NEWS2-style composite of vital signs) so it can flag
   critical/urgent patients directly from vitals without hand-written
   if/else rules.

Hospitals rarely release real patient-flow datasets, so both models are
trained on synthetically generated but clinically-plausible data (the
triage labels come from a real early-warning scoring formula, and the
queueing data follows standard M/M/c waiting-time behaviour with noise).
Re-run this file any time the feature schema changes:  python -m app.ml.train
"""
from __future__ import annotations

import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
os.makedirs(ARTIFACT_DIR, exist_ok=True)

RNG = np.random.default_rng(42)

DEPARTMENT_TYPES = ["opd", "laboratory", "pharmacy", "ward", "icu", "emergency"]
PRIORITIES = ["normal", "urgent", "critical"]


# --------------------------------------------------------------------------
# 1. Wait-time regression model
# --------------------------------------------------------------------------
def _simulate_wait_dataset(n: int = 12000) -> pd.DataFrame:
    dept_type = RNG.choice(DEPARTMENT_TYPES, size=n, p=[0.35, 0.2, 0.15, 0.15, 0.05, 0.1])
    queue_ahead = RNG.poisson(lam=6, size=n).clip(0, 60)
    hour = RNG.integers(0, 24, size=n)
    priority = RNG.choice(PRIORITIES, size=n, p=[0.7, 0.22, 0.08])
    avg_service = RNG.normal(15, 5, size=n).clip(4, 40)
    servers = RNG.integers(1, 6, size=n)

    # base wait follows queue theory: (people ahead / servers) * service time
    base_wait = (queue_ahead / servers) * avg_service

    # rush-hour multiplier (9-12 and 17-19 busier)
    rush = np.where(((hour >= 9) & (hour <= 12)) | ((hour >= 17) & (hour <= 19)), 1.35, 1.0)

    # priority discount: urgent/critical patients get bumped ahead
    priority_factor = np.select(
        [priority == "critical", priority == "urgent"],
        [0.15, 0.5],
        default=1.0,
    )

    noise = RNG.normal(0, 4, size=n)
    wait_minutes = (base_wait * rush * priority_factor + noise).clip(0, 240)

    return pd.DataFrame(
        {
            "department_type": dept_type,
            "queue_ahead": queue_ahead,
            "hour": hour,
            "priority": priority,
            "avg_service_minutes": avg_service,
            "servers": servers,
            "wait_minutes": wait_minutes,
        }
    )


def train_wait_time_model() -> dict:
    df = _simulate_wait_dataset()

    dept_encoder = LabelEncoder().fit(DEPARTMENT_TYPES)
    priority_encoder = LabelEncoder().fit(PRIORITIES)

    X = pd.DataFrame(
        {
            "department_type": dept_encoder.transform(df["department_type"]),
            "queue_ahead": df["queue_ahead"],
            "hour": df["hour"],
            "priority": priority_encoder.transform(df["priority"]),
            "avg_service_minutes": df["avg_service_minutes"],
            "servers": df["servers"],
        }
    )
    y = df["wait_minutes"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)

    model = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)

    joblib.dump(
        {"model": model, "dept_encoder": dept_encoder, "priority_encoder": priority_encoder},
        os.path.join(ARTIFACT_DIR, "wait_time_model.joblib"),
    )
    return {"r2_score": float(score), "n_samples": len(df)}


# --------------------------------------------------------------------------
# 2. Triage classification model
# --------------------------------------------------------------------------
def _early_warning_score(row) -> int:
    """A simplified NEWS2-style composite early warning score (0-20)."""
    score = 0
    rr, spo2, temp, sbp, hr, age = (
        row["respiratory_rate"],
        row["spo2"],
        row["temperature_c"],
        row["systolic_bp"],
        row["heart_rate"],
        row["age"],
    )

    if rr <= 8 or rr >= 25:
        score += 3
    elif rr >= 21 or rr <= 11:
        score += 1

    if spo2 <= 91:
        score += 3
    elif spo2 <= 93:
        score += 2
    elif spo2 <= 95:
        score += 1

    if temp <= 35.0 or temp >= 39.1:
        score += 2
    elif temp >= 38.1 or temp <= 36.0:
        score += 1

    if sbp <= 90 or sbp >= 220:
        score += 3
    elif sbp <= 100:
        score += 2
    elif sbp <= 110:
        score += 1

    if hr <= 40 or hr >= 131:
        score += 3
    elif hr >= 111 or hr <= 50:
        score += 1

    if age >= 75:
        score += 1

    return score


def _simulate_vitals_dataset(n: int = 15000) -> pd.DataFrame:
    age = RNG.integers(0, 95, size=n)
    heart_rate = RNG.normal(80, 22, size=n).clip(30, 190)
    systolic_bp = RNG.normal(120, 24, size=n).clip(60, 230)
    spo2 = RNG.normal(96, 4, size=n).clip(70, 100)
    temperature_c = RNG.normal(37.0, 1.1, size=n).clip(33, 41.5)
    respiratory_rate = RNG.normal(17, 5, size=n).clip(6, 40)

    df = pd.DataFrame(
        {
            "age": age,
            "heart_rate": heart_rate,
            "systolic_bp": systolic_bp,
            "spo2": spo2,
            "temperature_c": temperature_c,
            "respiratory_rate": respiratory_rate,
        }
    )
    df["ews"] = df.apply(_early_warning_score, axis=1)
    df["priority"] = pd.cut(
        df["ews"], bins=[-1, 3, 6, 100], labels=["normal", "urgent", "critical"]
    ).astype(str)
    return df


def train_triage_model() -> dict:
    df = _simulate_vitals_dataset()
    feature_cols = ["age", "heart_rate", "systolic_bp", "spo2", "temperature_c", "respiratory_rate"]
    X = df[feature_cols]

    priority_encoder = LabelEncoder().fit(PRIORITIES)
    y = priority_encoder.transform(df["priority"])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )

    model = GradientBoostingClassifier(n_estimators=150, max_depth=3, random_state=42)
    model.fit(X_train, y_train)
    accuracy = model.score(X_test, y_test)

    joblib.dump(
        {"model": model, "priority_encoder": priority_encoder, "feature_cols": feature_cols},
        os.path.join(ARTIFACT_DIR, "triage_model.joblib"),
    )
    return {"accuracy": float(accuracy), "n_samples": len(df)}


def train_all() -> None:
    wait_metrics = train_wait_time_model()
    triage_metrics = train_triage_model()
    print(f"[wait-time model]  R^2={wait_metrics['r2_score']:.3f}  samples={wait_metrics['n_samples']}")
    print(f"[triage model]     accuracy={triage_metrics['accuracy']:.3f}  samples={triage_metrics['n_samples']}")


if __name__ == "__main__":
    train_all()
