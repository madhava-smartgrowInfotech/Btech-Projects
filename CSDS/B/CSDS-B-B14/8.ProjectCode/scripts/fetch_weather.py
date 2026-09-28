"""Download daily weather history for the configured city from Open-Meteo and cache it as CSV.

Usage: python scripts/fetch_weather.py [start_date] [end_date]
"""
import csv
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "weather" / "daily_history.csv"


def load_env():
    env = {}
    p = ROOT / ".env"
    if not p.exists():
        p = ROOT / ".env.example"
    for line in p.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def main():
    env = load_env()
    start = sys.argv[1] if len(sys.argv) > 1 else "2024-01-01"
    end = sys.argv[2] if len(sys.argv) > 2 else (date.today() - timedelta(days=7)).isoformat()
    params = {
        "latitude": env.get("CITY_LAT", "17.385"),
        "longitude": env.get("CITY_LON", "78.4867"),
        "start_date": start,
        "end_date": end,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
    }
    url = "https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=60) as r:
        data = json.loads(r.read())
    d = data["daily"]
    rows = {t: (a, b, c) for t, a, b, c in zip(d["time"], d["temperature_2m_max"], d["temperature_2m_min"],
                                                d["precipitation_sum"]) if None not in (a, b, c)}
    # the archive lags a few days behind; fill up to yesterday from the forecast API's recent past
    params2 = {k: params[k] for k in ("latitude", "longitude", "daily", "timezone")}
    params2.update({"past_days": 14, "forecast_days": 1})
    url2 = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params2)
    with urllib.request.urlopen(url2, timeout=60) as r:
        d2 = json.loads(r.read())["daily"]
    today = date.today().isoformat()
    for t, a, b, c in zip(d2["time"], d2["temperature_2m_max"], d2["temperature_2m_min"], d2["precipitation_sum"]):
        if t not in rows and t < today and None not in (a, b, c):
            rows[t] = (a, b, c)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "tmax", "tmin", "precip"])
        for t in sorted(rows):
            w.writerow((t, *rows[t]))
    print(f"Saved {len(rows)} days ({min(rows)} .. {max(rows)}) for {env.get('CITY_NAME', 'city')} -> {OUT}")


if __name__ == "__main__":
    main()
