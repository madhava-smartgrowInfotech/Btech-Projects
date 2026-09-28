"""Zone demand forecasting: XGBoost on consumption lags + calendar + Open-Meteo weather."""
import json
import time
import urllib.parse
import urllib.request
from datetime import date, timedelta

import joblib
import numpy as np
import pandas as pd

from ..config import CITY_LAT, CITY_LON, CITY_NAME, DATA, MODELS
from .twin import ZONE_NAMES, ZONES

HIST_PATH = DATA / "sample" / "zone_consumption_daily.csv"
WEATHER_PATH = DATA / "weather" / "daily_history.csv"
FORECAST_CACHE = DATA / "weather" / "forecast_cache.json"
MODEL_PATH = MODELS / "demand_xgb.joblib"
# the model predicts demand relative to the zone's 28-day level, so weather and calendar effects dominate
FEATURES = ["zone_id", "dow", "month", "r_lag1", "r_lag7", "r_roll7", "tmax", "tmin", "precip", "tmax_anom"]


def load_history():
    h = pd.read_csv(HIST_PATH, parse_dates=["date"])
    w = pd.read_csv(WEATHER_PATH, parse_dates=["date"])
    return h.merge(w, on="date", how="left")


def build_features(df):
    """df: date, zone, consumption_m3, tmax, tmin, precip (sorted). Adds feature columns per zone."""
    out = []
    for z, g in df.sort_values("date").groupby("zone"):
        g = g.copy()
        c = g["consumption_m3"]
        g["zone_id"] = ZONES.index(z)
        g["dow"] = g["date"].dt.dayofweek
        g["month"] = g["date"].dt.month
        g["roll28"] = c.shift(1).rolling(28).mean()
        g["lag7"] = c.shift(7)
        g["r_lag1"] = c.shift(1) / g["roll28"]
        g["r_lag7"] = g["lag7"] / g["roll28"]
        g["r_roll7"] = c.shift(1).rolling(7).mean() / g["roll28"]
        g["tmax_anom"] = g["tmax"] - g["tmax"].shift(1).rolling(28, min_periods=1).mean()
        g["target"] = c / g["roll28"]
        out.append(g)
    return pd.concat(out).sort_values(["date", "zone"])


_model = None


def model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def fetch_weather(start, end):
    """Daily weather for [start, end] from Open-Meteo (forecast API, which also serves the recent past)."""
    key = f"{CITY_LAT},{CITY_LON},{start},{end}"
    cache = {}
    if FORECAST_CACHE.exists():
        try:
            cache = json.loads(FORECAST_CACHE.read_text())
        except ValueError:
            cache = {}
    hit = cache.get(key)
    if hit and time.time() - hit["fetched"] < 3 * 3600:
        return pd.DataFrame(hit["rows"]), hit["source"]
    params = {"latitude": CITY_LAT, "longitude": CITY_LON, "start_date": start, "end_date": end,
              "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum", "timezone": "auto"}
    try:
        with urllib.request.urlopen("https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params),
                                    timeout=15) as r:
            d = json.loads(r.read())["daily"]
        rows = [{"date": t, "tmax": a, "tmin": b, "precip": c or 0.0}
                for t, a, b, c in zip(d["time"], d["temperature_2m_max"], d["temperature_2m_min"], d["precipitation_sum"])]
        if any(r["tmax"] is None for r in rows):
            raise ValueError("incomplete forecast")
        source = f"Open-Meteo forecast ({CITY_NAME})"
        FORECAST_CACHE.parent.mkdir(parents=True, exist_ok=True)
        cache = {key: {"fetched": time.time(), "rows": rows, "source": source}}
        FORECAST_CACHE.write_text(json.dumps(cache))
        return pd.DataFrame(rows), source
    except Exception:
        if hit:
            return pd.DataFrame(hit["rows"]), hit["source"] + " (cached)"
        # offline: fall back to the same calendar days' average from the cached history
        w = pd.read_csv(WEATHER_PATH, parse_dates=["date"])
        w["doy"] = w["date"].dt.dayofyear
        clim = w.groupby("doy")[["tmax", "tmin", "precip"]].mean()
        rows = []
        for d in pd.date_range(start, end):
            v = clim.loc[d.dayofyear]
            rows.append({"date": d.strftime("%Y-%m-%d"), "tmax": round(v.tmax, 1), "tmin": round(v.tmin, 1),
                         "precip": round(v.precip, 1)})
        return pd.DataFrame(rows), "climatology from cached history (offline)"


def recursive_forecast(hist, weather, horizon=7):
    """hist: history frame (date, zone, consumption_m3, tmax, tmin, precip); weather: next days' weather."""
    m = model()
    work = hist[["date", "zone", "consumption_m3", "tmax", "tmin", "precip"]].copy()
    last = work["date"].max()
    preds = []
    for i in range(horizon):
        d = last + timedelta(days=i + 1)
        w = weather.iloc[i]
        new = pd.DataFrame([{"date": d, "zone": z, "consumption_m3": np.nan, "tmax": w.tmax, "tmin": w.tmin,
                             "precip": w.precip} for z in ZONES])
        work = pd.concat([work, new], ignore_index=True)
        f = build_features(work[work["date"] > d - timedelta(days=45)])
        row = f[f["date"] == d]
        yhat = m.predict(row[FEATURES]) * row["roll28"].values
        for z, v in zip(row["zone"], yhat):
            work.loc[(work["date"] == d) & (work["zone"] == z), "consumption_m3"] = float(v)
            preds.append({"date": d.strftime("%Y-%m-%d"), "zone": z, "forecast_m3": round(float(v), 1),
                          "tmax": float(w.tmax), "tmin": float(w.tmin), "precip": float(w.precip)})
    return pd.DataFrame(preds)


def forecast(zone="Z3", horizon=7):
    hist = load_history()
    last = hist["date"].max()
    start = (last + timedelta(days=1)).strftime("%Y-%m-%d")
    end = (last + timedelta(days=horizon)).strftime("%Y-%m-%d")
    weather, source = fetch_weather(start, end)
    fc = recursive_forecast(hist, weather, horizon)
    zf = fc[fc["zone"] == zone].to_dict("records")
    peak = max(zf, key=lambda r: r["forecast_m3"])
    hottest = max(zf, key=lambda r: r["tmax"])
    past = hist[(hist["zone"] == zone) & (hist["date"] > last - timedelta(days=30))]
    metrics = {}
    mp = MODELS.parent / "experiments" / "demand_metrics.json"
    if mp.exists():
        metrics = json.loads(mp.read_text())
    totals = fc.groupby("zone")["forecast_m3"].sum().round(1).to_dict()
    return {
        "zone": zone, "zone_name": ZONE_NAMES[zone],
        "data_until": last.strftime("%Y-%m-%d"),
        "weather_source": source,
        "history": [{"date": r.date.strftime("%Y-%m-%d"), "consumption_m3": r.consumption_m3, "tmax": r.tmax}
                    for r in past.itertuples()],
        "forecast": zf,
        "peak": peak, "hottest": hottest,
        "peak_on_hottest_day": peak["date"] == hottest["date"],
        "avg_last_7": round(float(past.tail(7)["consumption_m3"].mean()), 1),
        "week_totals": totals,
        "mape": metrics.get("xgboost", {}).get("mape_7day_recursive"),
    }


def zones():
    return [{"id": z, "name": ZONE_NAMES[z]} for z in ZONES]


def next_week_by_zone():
    """Forecast total per zone for the coming 7 days (used by dashboard)."""
    hist = load_history()
    last = hist["date"].max()
    weather, source = fetch_weather((last + timedelta(days=1)).strftime("%Y-%m-%d"),
                                    (last + timedelta(days=7)).strftime("%Y-%m-%d"))
    fc = recursive_forecast(hist, weather, 7)
    return fc, source
