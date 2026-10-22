"""Economic-indicator forecasting for FinSight AI.

The Census Income dataset is cross-sectional (one row per person, no genuine
time dimension), so it cannot legitimately forecast time into the future.
A separate monthly Household Financial Conditions Index series is therefore
used for the forecasting component.

SOURCE: synthetic illustrative series with a documented schema
(see data/README.md). The series is modelled with statsmodels
ExponentialSmoothing (Holt-Winters) — the simplest valid approach.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

from statsmodels.tsa.holtwinters import ExponentialSmoothing

RANDOM_STATE = 42
FORECAST_HORIZON = 12


def build_index_series() -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_STATE)
    dates = pd.date_range("2015-01-01", "2025-12-01", freq="MS")
    t = np.arange(len(dates))
    trend = 100 + 0.35 * t
    seasonal = 4.0 * np.sin(2 * np.pi * (dates.month - 1) / 12)
    noise = rng.normal(0, 1.6, size=len(dates))
    shock = np.zeros(len(dates))
    # Mild, documented downturn mid-2020 (illustrative, not a causal claim).
    shock[(dates >= "2020-03-01") & (dates <= "2020-08-01")] = -7.0
    values = trend + seasonal + shock + noise
    return pd.DataFrame({"date": dates, "index_value": np.round(values, 2)})


def fit_forecast(df: pd.DataFrame, horizon: int = FORECAST_HORIZON) -> dict:
    series = df.set_index("date")["index_value"].asfreq("MS")
    model = ExponentialSmoothing(
        series, trend="add", seasonal="add", seasonal_periods=12,
        initialization_method="estimated",
    )
    fit = model.fit(optimized=True)
    fc = fit.forecast(horizon)
    resid_std = float(np.std(fit.resid.dropna())) if len(fit.resid.dropna()) else 2.0
    last_date = series.index[-1]
    future_dates = pd.date_range(
        last_date + pd.offsets.MonthBegin(1), periods=horizon, freq="MS"
    )
    fc_vals = [round(float(v), 2) for v in fc.values]
    lower = [round(float(v - 1.96 * resid_std), 2) for v in fc.values]
    upper = [round(float(v + 1.96 * resid_std), 2) for v in fc.values]
    direction = "upward" if fc_vals[-1] > float(series.values[-1]) else (
        "downward" if fc_vals[-1] < float(series.values[-1]) else "stable")
    pct_change = round(
        100 * (fc_vals[-1] - float(series.values[-1])) / float(series.values[-1]), 2)
    fitted = [round(float(v), 2) for v in fit.fittedvalues.values]
    return {
        "method": "Holt-Winters Exponential Smoothing (additive trend + seasonality)",
        "source_note": "Illustrative monthly Household Financial Conditions Index, 2015-2025 (synthetic series, documented in data/README.md).",
        "history": [
            {"date": d.strftime("%Y-%m"), "value": float(v)}
            for d, v in zip(series.index, series.values)
        ],
        "fitted": fitted,
        "forecast": [
            {"date": d.strftime("%Y-%m"), "value": v, "lower": lo, "upper": hi}
            for d, v, lo, hi in zip(future_dates, fc_vals, lower, upper)
        ],
        "horizon_months": horizon,
        "trend_direction": direction,
        "forecast_pct_change": pct_change,
        "residual_std": round(resid_std, 3),
        "interpretation": (
            f"The index is projected to move {direction} over the next {horizon} months "
            f"({pct_change:+.2f}% from {float(series.values[-1]):.1f} to {fc_vals[-1]:.1f}). "
            "This is a statistical extrapolation of past patterns, not a guarantee of "
            "any individual's future finances."
        ),
    }


def main():
    root = Path(__file__).resolve().parents[1]
    df = build_index_series()
    payload = fit_forecast(df)
    out = root / "artifacts" / "forecast.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {out} ({len(payload['history'])} history + {len(payload['forecast'])} forecast)")


if __name__ == "__main__":
    main()
