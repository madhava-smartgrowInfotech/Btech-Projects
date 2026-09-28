"""Generate sample consumption data (seeded), driven by the real Open-Meteo weather history.

Outputs (all clearly sample data):
  data/sample/zone_consumption_daily.csv  - billed consumption per zone per day
  data/sample/meters.csv                  - 150 customer meters (zone, type)
  data/sample/meters_hourly.csv           - hourly readings for the last 45 days
  data/sample/meter_anomaly_truth.csv     - injected anomalies (for evaluation only)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.twin import DIURNAL, ZONE_BASE_M3_DAY, ZONES  # noqa: E402

OUT = ROOT / "data" / "sample"
TEMP_COEF = {"Z1": 0.018, "Z2": 0.02, "Z3": 0.034, "Z4": 0.015, "Z5": 0.022}  # +x per degC above 30
DOW = [1.0, 0.99, 0.99, 1.0, 1.01, 1.04, 1.06]
COMMERCIAL = [0.2, 0.2, 0.2, 0.2, 0.25, 0.4, 0.8, 1.2, 1.6, 1.8, 1.8, 1.7,
              1.6, 1.6, 1.7, 1.7, 1.6, 1.4, 1.1, 0.8, 0.5, 0.35, 0.25, 0.2]
COMMERCIAL = [v / (sum(COMMERCIAL) / 24) for v in COMMERCIAL]
METER_DAYS = 45


def zone_history(weather, rng):
    rows = []
    n = len(weather)
    for z in ZONES:
        e = 0.0
        for i, w in enumerate(weather.itertuples()):
            e = 0.6 * e + rng.normal(0, 0.018)
            dow = DOW[pd.Timestamp(w.date).dayofweek]
            temp = 1 + TEMP_COEF[z] * (w.tmax - 30.0)
            rain = 1 - 0.06 * min(w.precip / 10.0, 1.0)
            growth = 1 + 0.03 * (i - n) / 365.0
            rows.append((w.date, z, round(ZONE_BASE_M3_DAY[z] * dow * temp * rain * growth * (1 + e), 1)))
    return pd.DataFrame(rows, columns=["date", "zone", "consumption_m3"])


def meters(hist, rng):
    ids, zone_of, kind, base = [], [], [], []
    for i in range(150):
        z = ZONES[i % 5]
        k = "commercial" if rng.random() < 0.15 else "residential"
        ids.append(f"M{1001 + i}")
        zone_of.append(z)
        kind.append(k)
        base.append(round(rng.uniform(3.0, 8.0) if k == "commercial" else rng.uniform(0.45, 1.3), 3))
    m = pd.DataFrame({"meter_id": ids, "zone": zone_of, "type": kind, "base_m3_day": base})
    dates = sorted(hist["date"].unique())[-METER_DAYS:]
    zfac = hist.pivot(index="date", columns="zone", values="consumption_m3")
    zfac = (zfac / zfac.mean()).loc[dates]
    truth = []
    plan = {}
    anomalous = rng.choice(len(m), 15, replace=False)
    for j, idx in enumerate(anomalous):
        typ = ["night_flow", "burst", "theft"][j % 3]
        start = int(rng.integers(METER_DAYS - 20, METER_DAYS - 3))
        plan[idx] = (typ, start)
    readings = []
    for idx, r in m.iterrows():
        prof = COMMERCIAL if r.type == "commercial" else DIURNAL
        typ, start = plan.get(idx, (None, None))
        extra_night = rng.uniform(0.035, 0.08)
        theft_f = rng.uniform(0.08, 0.3)
        for di, d in enumerate(dates):
            day = r.base_m3_day * float(zfac.loc[d, r.zone]) * (0.3 if r.type == "commercial" and pd.Timestamp(d).dayofweek == 6 else 1.0)
            h = day / 24.0 * np.array(prof) * rng.lognormal(0, 0.18, 24)
            anom = False
            if typ == "night_flow" and di >= start:
                h = h + extra_night
                anom = True
            elif typ == "theft" and di >= start:
                h = h * theft_f
                anom = True
            elif typ == "burst" and di == start:
                s = int(rng.integers(0, 20))
                h[s:s + int(rng.integers(3, 6))] += rng.uniform(0.6, 1.6) * max(1, r.base_m3_day / 2)
                anom = True
            if anom:
                truth.append((r.meter_id, d, typ))
            for hr in range(24):
                readings.append((r.meter_id, f"{d} {hr:02d}:00", round(float(h[hr]), 4)))
    return m, pd.DataFrame(readings, columns=["meter_id", "ts", "m3"]), pd.DataFrame(truth, columns=["meter_id", "date", "type"])


def main():
    rng = np.random.default_rng(42)
    weather = pd.read_csv(ROOT / "data" / "weather" / "daily_history.csv")
    OUT.mkdir(parents=True, exist_ok=True)
    hist = zone_history(weather, rng)
    hist.to_csv(OUT / "zone_consumption_daily.csv", index=False)
    m, hourly, truth = meters(hist, rng)
    m.to_csv(OUT / "meters.csv", index=False)
    hourly.to_csv(OUT / "meters_hourly.csv", index=False)
    truth.to_csv(OUT / "meter_anomaly_truth.csv", index=False)
    print(f"zone history {len(hist)} rows, meters {len(m)}, hourly {len(hourly)}, anomalous meter-days {len(truth)}")


if __name__ == "__main__":
    main()
