"""Forecast utilities: recursive multi-step forecasts with confidence bands."""
from __future__ import annotations
import numpy as np


def recursive_forecast(model, last_window: np.ndarray, steps: int, residual_std: float, close_scaler) -> list[dict]:
    win = last_window.copy()
    scaled_preds = []
    for _ in range(steps):
        p = float(model.predict(win[np.newaxis], verbose=0).ravel()[0])
        scaled_preds.append(p)
        nxt = win[-1].copy()
        nxt[3] = p  # roll Close forward; keep other features coherent
        # shift other price cols toward predicted close to stay coherent
        nxt[0] = nxt[1] = nxt[2] = p
        win = np.concatenate([win[1:], nxt[np.newaxis]], axis=0)
    preds = close_scaler.inverse_transform(np.array(scaled_preds).reshape(-1, 1)).ravel()
    band = 1.96 * residual_std * np.sqrt(np.arange(1, steps + 1))
    return [{"day": i + 1, "predicted_close": round(float(p), 2),
             "lower": round(float(max(p - b, 0.01)), 2),
             "upper": round(float(p + b), 2)} for i, (p, b) in enumerate(zip(preds, band))]
