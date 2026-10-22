"""PeerScope ML prediction service (TF-IDF + LogisticRegression, real artifacts)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib

from app.config import METRICS_ARTIFACT, MODEL_ARTIFACT, VECTORIZER_ARTIFACT

_model = None
_vectorizer = None


def artifacts_exist() -> bool:
    return Path(MODEL_ARTIFACT).exists() and Path(VECTORIZER_ARTIFACT).exists()


def _lazy_load():
    global _model, _vectorizer
    if _model is None and Path(MODEL_ARTIFACT).exists():
        _model = joblib.load(MODEL_ARTIFACT)
    if _vectorizer is None and Path(VECTORIZER_ARTIFACT).exists():
        _vectorizer = joblib.load(VECTORIZER_ARTIFACT)
    return _model, _vectorizer


def predict_decision(title: str, summary: str, full_text: str = "") -> dict[str, Any]:
    """Return the historical-decision signal from the trained classifier."""
    model, vec = _lazy_load()
    if model is None or vec is None:
        return {
            "status": "model_unavailable",
            "label": "unavailable",
            "confidence": 0.0,
            "probabilities": {},
            "note": "Trained decision model artifacts not found. Run scripts/train_model.py.",
        }
    blob = f"{title or ''} {summary or ''} {(full_text or '')[:4000]}".strip()
    x = vec.transform([blob])
    label_names: list[str] | None = None
    try:
        label_names = list(load_metrics().get("labels") or [])
    except Exception:
        label_names = None

    def _name(c) -> str:
        try:
            i = int(c)
            if label_names and 0 <= i < len(label_names):
                # classes_ are integer-encoded; metrics labels are in encoder order
                # only when sorted order matches; safer: sort check below.
                pass
        except Exception:
            pass
        return str(c)

    # Build index->name map: LabelEncoder sorts classes alphabetically, and
    # metrics.json stores labels in that same encoder order.
    idx_to_name = {i: n for i, n in enumerate(label_names)} if label_names else {}
    try:
        proba = model.predict_proba(x)[0]
        classes = list(model.classes_)
        best = int(proba.argmax())
        names = [idx_to_name.get(int(c), _name(c)) if str(c).isdigit() else str(c) for c in classes]
        # When classes_ are 0..n-1, idx_to_name maps position directly.
        probs = {str(n): round(float(p), 4) for n, p in zip(names, proba)}
        return {
            "status": "ok",
            "label": str(names[best]),
            "confidence": round(float(proba[best]), 4),
            "probabilities": probs,
            "note": "Historical decision signal learned from prior review records; not a judgment of scientific correctness.",
        }
    except Exception:
        raw = str(model.predict(x)[0])
        label = idx_to_name.get(int(raw), raw) if raw.isdigit() else raw
        return {"status": "ok", "label": label, "confidence": 0.0,
                "probabilities": {label: 1.0}, "note": "Prediction without calibrated probabilities."}


def load_metrics() -> dict[str, Any]:
    if Path(METRICS_ARTIFACT).exists():
        return json.loads(Path(METRICS_ARTIFACT).read_text(encoding="utf-8"))
    return {"status": "missing", "note": "No metrics artifact. Run scripts/train_model.py."}
