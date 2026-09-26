"""Objective 2 - predict regional demand with a Random Forest.

For every (region, month) we build lag/rolling/seasonal features and train a
RandomForestRegressor to predict next month's orders. Evaluation uses a
time-based split (last `test_months` months are held out) so the score is a
true out-of-sample forecast error. Two naive baselines (last value, 3-month
moving average) show what the model adds.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from . import config

FEATURES = [
    "lag_1", "lag_2", "lag_3", "lag_6", "lag_12", "roll_mean_3", "roll_mean_6",
    "roll_std_3", "trend_3", "month", "quarter", "festival", "promo", "promo_prev",
    "population", "tier", "penetration", "avg_order_value", "return_rate",
]
FESTIVAL_MONTHS = {10, 11, 1, 8}


def build_features(regions: pd.DataFrame, demand: pd.DataFrame) -> pd.DataFrame:
    df = demand.merge(regions[["region_id", "population", "tier", "penetration"]], on="region_id")
    df = df.sort_values(["region_id", "period"]).copy()
    g = df.groupby("region_id")["orders"]
    for k in (1, 2, 3, 6, 12):
        df[f"lag_{k}"] = g.shift(k)
    df["roll_mean_3"] = g.transform(lambda s: s.shift(1).rolling(3).mean())
    df["roll_mean_6"] = g.transform(lambda s: s.shift(1).rolling(6).mean())
    df["roll_std_3"] = g.transform(lambda s: s.shift(1).rolling(3).std())
    df["trend_3"] = df["lag_1"] - df["lag_3"]
    df["quarter"] = (df["month"] - 1) // 3 + 1
    df["festival"] = df["month"].isin(FESTIVAL_MONTHS).astype(int)
    df["promo_prev"] = df.groupby("region_id")["promo"].shift(1)
    df["lag_12"] = df["lag_12"].fillna(df["roll_mean_6"])
    return df.dropna(subset=["lag_3", "roll_mean_3"]).copy()


def _metrics(y_true, y_pred) -> dict:
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    mape = float(np.mean(np.abs(y_true - y_pred) / np.maximum(y_true, 1))) * 100
    return {
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 1),
        "rmse": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 1),
        "mape": round(mape, 2),
        "r2": round(float(r2_score(y_true, y_pred)), 4),
    }


def train_forecaster(regions: pd.DataFrame, demand: pd.DataFrame, test_months: int = 6,
                     verbose: bool = True) -> dict:
    df = build_features(regions, demand)
    periods = sorted(df["period"].unique())
    cutoff = periods[-test_months]
    train, test = df[df.period < cutoff], df[df.period >= cutoff]

    t0 = time.time()
    rf = RandomForestRegressor(n_estimators=400, max_depth=None, min_samples_leaf=2,
                               max_features=0.6, n_jobs=-1, random_state=config.RANDOM_STATE)
    rf.fit(train[FEATURES], train["orders"])
    pred = rf.predict(test[FEATURES])

    results = {
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "train_rows": int(len(train)), "test_rows": int(len(test)),
        "train_periods": f"{periods[0]} to {periods[-test_months-1]}",
        "test_periods": f"{cutoff} to {periods[-1]}",
        "train_seconds": round(time.time() - t0, 1),
        "random_forest": _metrics(test["orders"], pred),
        "baseline_last_value": _metrics(test["orders"], test["lag_1"]),
        "baseline_moving_avg_3": _metrics(test["orders"], test["roll_mean_3"]),
        "feature_importance": sorted(
            [{"feature": f, "importance": round(float(v), 4)} for f, v in zip(FEATURES, rf.feature_importances_)],
            key=lambda x: -x["importance"]),
    }
    # per-region detail for the last test month (used by the web UI)
    last = test[test.period == periods[-1]].copy()
    last["predicted"] = rf.predict(last[FEATURES]).round(0)
    results["last_period"] = periods[-1]
    results["last_period_detail"] = [
        {"region_id": r.region_id, "actual": int(r.orders), "predicted": int(r.predicted),
         "error_pct": round(abs(r.orders - r.predicted) / max(r.orders, 1) * 100, 1)}
        for r in last.itertuples()]

    config.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": rf, "features": FEATURES}, config.FORECAST_MODEL)
    config.FORECAST_METRICS.write_text(json.dumps(results, indent=2))
    if verbose:
        rfm, b1, b2 = results["random_forest"], results["baseline_last_value"], results["baseline_moving_avg_3"]
        print(f"Random Forest   MAE {rfm['mae']:>9}  RMSE {rfm['rmse']:>9}  MAPE {rfm['mape']:>6}%  R2 {rfm['r2']}")
        print(f"Last value      MAE {b1['mae']:>9}  RMSE {b1['rmse']:>9}  MAPE {b1['mape']:>6}%  R2 {b1['r2']}")
        print(f"Moving avg (3)  MAE {b2['mae']:>9}  RMSE {b2['rmse']:>9}  MAPE {b2['mape']:>6}%  R2 {b2['r2']}")
    return results


def load_forecaster():
    if not config.FORECAST_MODEL.exists():
        return None
    return joblib.load(config.FORECAST_MODEL)


def load_forecast_metrics() -> dict:
    return json.loads(config.FORECAST_METRICS.read_text()) if config.FORECAST_METRICS.exists() else {}


def forecast_next_period(regions: pd.DataFrame, demand: pd.DataFrame, model=None,
                         promo_next: int | None = None) -> pd.DataFrame:
    """Forecast orders for the month after the last one in `demand`, per region.

    Returns a DataFrame: region_id, city, period (forecast month), forecast.
    """
    model = model or load_forecaster()
    if model is None:
        raise RuntimeError("No trained forecaster - run `python run.py forecast` first.")
    rf, feats = model["model"], model["features"]
    last_period = pd.Period(demand["period"].max(), freq="M")
    nxt = last_period + 1
    # append a placeholder row for the next month so lag features line up
    tmpl = demand[demand.period == str(last_period)].copy()
    tmpl["period"] = str(nxt)
    tmpl["year"], tmpl["month"] = nxt.year, nxt.month
    tmpl["promo"] = promo_next if promo_next is not None else int(nxt.month in (10, 11))
    tmpl["orders"] = np.nan
    ext = pd.concat([demand, tmpl], ignore_index=True)
    ext["orders"] = ext["orders"].fillna(0)   # placeholder only; lags use real history
    feats_df = build_features(regions, ext)
    row = feats_df[feats_df.period == str(nxt)].copy()
    row["forecast"] = np.maximum(rf.predict(row[feats]).round(0), 0).astype(int)
    out = row[["region_id", "period", "forecast"]].merge(regions[["region_id", "city"]], on="region_id")
    return out.sort_values("region_id").reset_index(drop=True)


def forecast_for_period(regions: pd.DataFrame, demand: pd.DataFrame, period: str, model=None) -> pd.DataFrame:
    """Forecast a historical `period` using only data strictly before it (for back-testing)."""
    hist = demand[demand.period < period]
    return forecast_next_period(regions, hist, model)
