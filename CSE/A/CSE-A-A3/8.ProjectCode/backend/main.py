"""Thin JSON API over the existing Flask project (app.py).

app.py is imported, not modified: its trained model bundles, field metadata and training report
are reused so predictions are identical to the Flask pages.
Run:  uvicorn backend.main:api --port 8303
"""
import math
import os
import re
import sys
import warnings

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
warnings.filterwarnings("ignore")

import app as flask_app  # noqa: E402  (existing project module; importing does not start the server)

BUNDLES = flask_app.BUNDLES
FIELD_META = flask_app.FIELD_META
TITLES = flask_app.DISEASE_TITLES
REPORT = flask_app.TRAINING_REPORT

# data/<disease>.csv target column; value 1 is "Positive (High Risk)" exactly as in app.py
TARGETS = {"diabetes": "Outcome", "heart": "target", "liver": "Dataset", "kidney": "classification"}
BLURBS = {
    "diabetes": "Glucose, BMI, insulin and related indicators.",
    "heart": "Blood pressure, cholesterol, ECG and related indicators.",
    "liver": "Bilirubin, liver enzymes and protein levels.",
    "kidney": "Creatinine, urea, hemoglobin and related indicators.",
}

DATA = {d: pd.read_csv(os.path.join(ROOT, "data", f"{d}.csv")) for d in BUNDLES}

api = FastAPI(title="Multi-Disease Prediction API", version="1.0")
api.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5303", "http://127.0.0.1:5303"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _best(d):
    name = REPORT[d]["best_model"]
    return name, REPORT[d]["all_results"][name]


def _options(feature, label, series):
    """Dropdown options for categorical inputs, taken from the label text or the dataset."""
    pairs = re.findall(r"(\d)\s*=\s*([A-Za-z]+)", label)
    if pairs:
        return [{"value": int(v), "label": t} for v, t in sorted(pairs)]
    vals = sorted(series.unique())
    if all(float(v).is_integer() for v in vals) and len(vals) <= 6:
        return [{"value": int(v), "label": str(int(v))} for v in vals]
    return None


def _fields(d):
    features = BUNDLES[d][2]
    out = []
    for f in features:
        label, placeholder, kind = FIELD_META[d][f]
        s = DATA[d][f]
        out.append(
            {
                "name": f,
                "label": label,
                "placeholder": placeholder,
                "type": kind,
                "min": float(s.min()),
                "max": float(s.max()),
                "median": float(s.median()),
                "options": _options(f, label, s),
            }
        )
    return out


def _summary(d):
    name, m = _best(d)
    return {
        "key": d,
        "title": TITLES[d],
        "blurb": BLURBS[d],
        "best_model": name,
        "accuracy": m["accuracy"],
        "f1": m["f1"],
        "n_features": len(BUNDLES[d][2]),
    }


def _check(d):
    if d not in BUNDLES:
        raise HTTPException(404, f"Unknown condition '{d}'. Use one of: {', '.join(BUNDLES)}.")


@api.get("/api/health")
def health():
    return {"status": "ok", "diseases": list(BUNDLES)}


@api.get("/api/diseases")
def diseases():
    return [_summary(d) for d in BUNDLES]


@api.get("/api/diseases/{d}")
def disease(d: str):
    _check(d)
    name, m = _best(d)
    return {**_summary(d), "metrics": m, "fields": _fields(d), "algorithms": REPORT[d]["all_results"]}


@api.get("/api/diseases/{d}/sample")
def sample(d: str, outcome: int | None = None):
    """A real row from the training dataset, to pre-fill the form."""
    _check(d)
    df = DATA[d]
    if outcome in (0, 1):
        df = df[df[TARGETS[d]] == outcome]
    row = df.sample(1).iloc[0]
    feats = BUNDLES[d][2]
    return {"values": {f: float(row[f]) for f in feats}, "label": int(row[TARGETS[d]])}


class PredictBody(BaseModel):
    values: dict[str, float | int | str | None]


@api.post("/api/predict/{d}")
def predict(d: str, body: PredictBody):
    _check(d)
    model, scaler, features = BUNDLES[d]
    values, missing = [], []
    for f in features:
        raw = body.values.get(f)
        try:
            v = float(raw)
            if not math.isfinite(v):
                raise ValueError
        except (TypeError, ValueError):
            missing.append(FIELD_META[d][f][0])
            continue
        values.append(v)
    if missing:
        raise HTTPException(422, "Please enter a valid number for: " + ", ".join(missing) + ".")

    # same steps as app.handle_prediction
    X_scaled = scaler.transform(np.array(values).reshape(1, -1))
    pred = int(model.predict(X_scaled)[0])
    probability = None
    if hasattr(model, "predict_proba"):
        probability = round(float(max(model.predict_proba(X_scaled)[0])) * 100, 2)
    name, m = _best(d)
    return {
        "disease": d,
        "title": TITLES[d],
        "positive": pred == 1,
        "result": "Positive (High Risk)" if pred == 1 else "Negative (Low Risk)",
        "probability": probability,
        "model": name,
        "accuracy": m["accuracy"],
    }


@api.get("/api/report")
def report():
    return REPORT


@api.get("/api/datasets")
def datasets():
    out = []
    for d, df in DATA.items():
        t = TARGETS[d]
        pos = int((df[t] == 1).sum())
        out.append(
            {
                "key": d,
                "title": TITLES[d],
                "rows": int(len(df)),
                "positive": pos,
                "negative": int(len(df)) - pos,
                "target": t,
                "features": BUNDLES[d][2],
                "synthetic": True,
            }
        )
    return out
