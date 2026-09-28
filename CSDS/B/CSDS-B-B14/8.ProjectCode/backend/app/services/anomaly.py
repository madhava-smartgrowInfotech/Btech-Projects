"""Abnormal consumption per customer meter: IsolationForest on daily usage features vs each meter's baseline."""
import joblib
import numpy as np
import pandas as pd

from ..config import DATA, MODELS

HOURLY_PATH = DATA / "sample" / "meters_hourly.csv"
METERS_PATH = DATA / "sample" / "meters.csv"
MODEL_PATH = MODELS / "anomaly_iforest.joblib"
FEATURES = ["log_total", "log_night", "log_peak", "night_frac"]
BASELINE_DAYS = 14
RECENT_DAYS = 7
NIGHT = [1, 2, 3, 4]

_cache = {}


def load_hourly():
    if "hourly" not in _cache:
        h = pd.read_csv(HOURLY_PATH)
        h["ts"] = pd.to_datetime(h["ts"])
        h["date"] = h["ts"].dt.normalize()
        h["hour"] = h["ts"].dt.hour
        _cache["hourly"] = h
    return _cache["hourly"]


def daily_features(h):
    g = h.groupby(["meter_id", "date"])
    day = g["m3"].sum().rename("total").to_frame()
    day["night"] = h[h.hour.isin(NIGHT)].groupby(["meter_id", "date"])["m3"].min()
    day["peak"] = g["m3"].max()
    day = day.reset_index().sort_values(["meter_id", "date"])
    # baseline per meter and day type (Sunday vs other days) from the first two weeks
    day["daytype"] = (day["date"].dt.dayofweek == 6).astype(int)
    first = day["date"].min()
    base = day[day["date"] < first + pd.Timedelta(days=BASELINE_DAYS)].groupby(["meter_id", "daytype"]).agg(
        b_total=("total", "median"), b_night=("night", "median"), b_peak=("peak", "median")).reset_index()
    day = day.merge(base, on=["meter_id", "daytype"])
    eps = 1e-4
    day["log_total"] = np.log((day.total + eps) / (day.b_total + eps))
    day["log_night"] = np.log((day.night + 0.005) / (day.b_night + 0.005))
    day["log_peak"] = np.log((day.peak + eps) / (day.b_peak + eps))
    day["night_frac"] = day.night * 24 / (day.total + eps)
    return day.sort_values(["meter_id", "date"]).reset_index(drop=True)


def label(row):
    if row.log_night > np.log(2.5) or row.night_frac > 0.9:
        return "night_flow"
    if row.log_peak > np.log(2.5) and row.log_total > np.log(1.25):
        return "burst"
    if row.log_total < np.log(0.5):
        return "suspected_theft"
    return "unusual_pattern"


DESCRIPTIONS = {
    "burst": "Short spike far above this meter's normal peak - possible service-pipe burst.",
    "night_flow": "Flow never drops between 01:00 and 05:00 - likely leak on the customer side.",
    "suspected_theft": "Consumption collapsed versus the meter's own baseline - possible bypass or tampering.",
    "unusual_pattern": "Usage pattern differs from this meter's history.",
}


def scored():
    if "scored" not in _cache:
        day = daily_features(load_hourly())
        model = joblib.load(MODEL_PATH)
        day["score"] = -model.score_samples(day[FEATURES])
        day["anomaly"] = model.predict(day[FEATURES]) == -1
        day["type"] = [label(r) if a else "" for r, a in zip(day.itertuples(), day.anomaly)]
        _cache["scored"] = day
    return _cache["scored"]


def flagged_meters():
    day = scored()
    meters = pd.read_csv(METERS_PATH).set_index("meter_id")
    last = day["date"].max()
    recent = day[(day.date > last - pd.Timedelta(days=RECENT_DAYS)) & day.anomaly]
    out = []
    for mid, g in recent.groupby("meter_id"):
        g = g.sort_values("date")
        named = g[g["type"] != "unusual_pattern"]
        typ = named["type"].mode().iloc[0] if len(named) else "unusual_pattern"
        # a one-off unexplained day is noise; raise the meter only for a named pattern or a repeat
        if typ == "unusual_pattern" and len(g) < 2:
            continue
        m = meters.loc[mid]
        out.append({
            "meter_id": mid, "zone": m.zone, "customer_type": m.type, "type": typ,
            "description": DESCRIPTIONS[typ],
            "anomalous_days": int(len(g)), "since": g.date.min().strftime("%Y-%m-%d"),
            "last_seen": g.date.max().strftime("%Y-%m-%d"),
            "score": round(float(g.score.max()), 4),
            "night_flow_m3h": round(float(g.night.iloc[-1]), 4),
            "baseline_night_m3h": round(float(g.b_night.iloc[-1]), 4),
            "day_total_m3": round(float(g.total.iloc[-1]), 3),
            "baseline_total_m3": round(float(g.b_total.iloc[-1]), 3),
        })
    out.sort(key=lambda r: -r["score"])
    return out


def meter_series(meter_id, days=14):
    h = load_hourly()
    g = h[h.meter_id == meter_id]
    if g.empty:
        return None
    last = g["date"].max()
    g = g[g["date"] > last - pd.Timedelta(days=days)]
    d = scored()
    d = d[d.meter_id == meter_id]
    return {
        "meter_id": meter_id,
        "hourly": [{"ts": t.strftime("%Y-%m-%d %H:%M"), "m3": v} for t, v in zip(g.ts, g.m3)],
        "daily": [{"date": r.date.strftime("%Y-%m-%d"), "total": round(r.total, 3), "night": round(r.night, 4),
                   "anomaly": bool(r.anomaly), "type": r.type, "score": round(r.score, 4)} for r in d.itertuples()],
    }


def summary():
    day = scored()
    last = day["date"].max()
    return {"meters": int(day.meter_id.nunique()), "days": int(day.date.nunique()),
            "data_until": last.strftime("%Y-%m-%d"), "flagged": len(flagged_meters())}
