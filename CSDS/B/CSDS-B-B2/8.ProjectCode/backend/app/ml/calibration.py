"""Temperature scaling so the confidence shown with each class matches how often it is right."""
from __future__ import annotations

import numpy as np


def apply_temperature(proba: np.ndarray, temperature: float) -> np.ndarray:
    logp = np.log(np.clip(proba, 1e-9, 1.0)) / temperature
    logp -= logp.max(axis=1, keepdims=True)
    p = np.exp(logp)
    return p / p.sum(axis=1, keepdims=True)


def fit_temperature(proba: np.ndarray, y: np.ndarray) -> float:
    """Pick the temperature that minimises negative log-likelihood on held-out data."""
    best_t, best_nll = 1.0, np.inf
    for t in np.exp(np.linspace(np.log(0.25), np.log(4.0), 121)):
        p = apply_temperature(proba, t)
        nll = -np.mean(np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1.0)))
        if nll < best_nll:
            best_t, best_nll = float(t), nll
    return best_t


def expected_calibration_error(proba: np.ndarray, y: np.ndarray, bins: int = 10) -> tuple[float, list[dict]]:
    conf = proba.max(axis=1)
    pred = proba.argmax(axis=1)
    edges = np.linspace(0, 1, bins + 1)
    ece, table = 0.0, []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (conf > lo) & (conf <= hi)
        if not mask.any():
            continue
        acc, avg = float((pred[mask] == y[mask]).mean()), float(conf[mask].mean())
        ece += mask.mean() * abs(acc - avg)
        table.append({"bin": [round(lo, 2), round(hi, 2)], "count": int(mask.sum()), "accuracy": acc, "confidence": avg})
    return float(ece), table


class CalibratedModel:
    """Wraps any model with predict_proba and applies a fitted temperature."""

    def __init__(self, model, temperature: float = 1.0):
        self.model = model
        self.temperature = temperature

    def predict_proba(self, X) -> np.ndarray:
        return apply_temperature(self.model.predict_proba(X), self.temperature)

    def predict(self, X) -> np.ndarray:
        return self.predict_proba(X).argmax(axis=1)
