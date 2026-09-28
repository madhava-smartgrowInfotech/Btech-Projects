"""Train the zone demand forecaster (XGBoost) and report MAPE on the last 90 days."""
import json
import sys
from datetime import timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services import demand  # noqa: E402

TEST_DAYS = 90


def mape(y, p):
    y, p = np.asarray(y), np.asarray(p)
    return float(np.mean(np.abs((y - p) / y)) * 100)


def main():
    hist = demand.load_history()
    feats = demand.build_features(hist).dropna(subset=demand.FEATURES + ["consumption_m3"])
    cutoff = hist["date"].max() - timedelta(days=TEST_DAYS)
    tr, te = feats[feats["date"] <= cutoff], feats[feats["date"] > cutoff]
    m = XGBRegressor(n_estimators=400, learning_rate=0.04, max_depth=3, subsample=0.8, colsample_bytree=0.9,
                     random_state=42, n_jobs=4)
    m.fit(tr[demand.FEATURES], tr["target"])
    one_day = mape(te["consumption_m3"], m.predict(te[demand.FEATURES]) * te["roll28"])
    naive = mape(te["consumption_m3"], te["lag7"])
    (ROOT / "models").mkdir(exist_ok=True)
    joblib.dump(m, demand.MODEL_PATH)
    demand._model = m

    # 7-day recursive forecasts from weekly origins inside the test window, using actual weather
    errs, per_zone = [], {z: [] for z in demand.ZONES}
    origins = pd.date_range(cutoff, hist["date"].max() - timedelta(days=7), freq="7D")
    for o in origins:
        past = hist[hist["date"] <= o]
        fut = hist[(hist["date"] > o) & (hist["date"] <= o + timedelta(days=7))]
        weather = fut.drop_duplicates("date").sort_values("date")[["tmax", "tmin", "precip"]].reset_index(drop=True)
        fc = demand.recursive_forecast(past, weather, 7)
        fc["date"] = pd.to_datetime(fc["date"])
        j = fc.merge(fut, on=["date", "zone"])
        errs.extend(list(np.abs(j["forecast_m3"] - j["consumption_m3"]) / j["consumption_m3"]))
        for z, g in j.groupby("zone"):
            per_zone[z].extend(list(np.abs(g["forecast_m3"] - g["consumption_m3"]) / g["consumption_m3"]))
    metrics = {
        "test_days": TEST_DAYS, "features": demand.FEATURES,
        "xgboost": {"mape_1day": round(one_day, 2), "mape_7day_recursive": round(float(np.mean(errs)) * 100, 2),
                    "mape_7day_by_zone": {z: round(float(np.mean(v)) * 100, 2) for z, v in per_zone.items()}},
        "seasonal_naive_lag7": {"mape_1day": round(naive, 2)},
        "feature_importance": {f: round(float(v), 4) for f, v in zip(demand.FEATURES, m.feature_importances_)},
    }
    print(json.dumps(metrics, indent=1))
    (ROOT / "experiments").mkdir(exist_ok=True)
    (ROOT / "experiments" / "demand_metrics.json").write_text(json.dumps(metrics, indent=1))


if __name__ == "__main__":
    main()
