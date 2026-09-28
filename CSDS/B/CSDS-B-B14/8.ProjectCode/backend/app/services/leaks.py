"""Leak detection (RandomForest on logger residuals) and localisation (sensitivity-signature matching)."""
import json

import joblib
import numpy as np
import pandas as pd

from ..config import MODELS
from . import twin

DETECTOR_PATH = MODELS / "leak_detector.joblib"
SIGNATURES_PATH = MODELS / "leak_signatures.json"
SIG_LPS = 10.0

_det = None
_sig = None


def detector():
    global _det
    if _det is None:
        _det = joblib.load(DETECTOR_PATH)
    return _det


def signatures():
    global _sig
    if _sig is None:
        _sig = json.loads(SIGNATURES_PATH.read_text())
    return _sig


def compute_signatures():
    """Noise-free residual each candidate pipe produces for a reference leak (used by ml/train_leak.py)."""
    out = {}
    for p in twin.candidate_pipes():
        wn = twin.copy_network()
        twin.add_leak(wn, p, SIG_LPS)
        out[p] = list(np.round(twin.residuals(twin.sensor_readings(wn, twin.run(wn, snapshot_hour=twin.NIGHT_HOUR))), 5))
    return out


def _prep(v, center):
    z = np.asarray(v, dtype=float) / twin.NOISE_STD
    if center:
        n = len(twin.SENSORS)
        z = z.copy()
        z[:n] = z[:n] - z[:n].mean()
    return z


def rank(res, sigs=None, center=None, top=5):
    if sigs is None or center is None:
        sig = signatures()
        sigs = sigs or sig["pipes"]
        center = sig["center_pressure"] if center is None else center
    r = _prep(res, center)
    scores = []
    for p, s in sigs.items():
        sv = _prep(s, center)
        cos = float(r @ sv / (np.linalg.norm(r) * np.linalg.norm(sv) + 1e-9))
        size = float(max(0.0, (r @ sv) / (sv @ sv)) * SIG_LPS)
        scores.append((cos, p, size))
    scores.sort(reverse=True)
    pz = twin.pipe_zone()
    return [{"pipe": p, "zone": pz[p], "score": round(c, 4), "estimated_lps": round(sz, 1)} for c, p, sz in scores[:top]]


def analyze(res):
    X = pd.DataFrame([res], columns=twin.FEATURES)
    prob = float(detector().predict_proba(X)[0, 1])
    ranked = rank(res)
    zones = {}
    for z in twin.ZONES:
        zones[z] = round(float(res[twin.FEATURES.index(f"q_{z}")]), 2)
    return {"leak_probability": round(prob, 4), "detected": prob >= 0.5, "ranking": ranked,
            "zone_inflow_residual_lps": zones,
            "pressure_residual_m": {s: round(float(res[i]), 3) for i, s in enumerate(twin.SENSORS)}}


def inject(pipe, lps, seed=None):
    """Simulate the loggers with a leak on `pipe` and run detection + localisation on the result."""
    rng = np.random.default_rng(seed)
    res = twin.residuals(twin.observe(pipe, lps, rng))
    out = analyze(res)
    ranks = [r["pipe"] for r in rank(res, top=len(signatures()["pipes"]))]
    out["true_rank"] = ranks.index(pipe) + 1 if pipe in ranks else None
    return out
