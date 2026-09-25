"""Geocode every (state, district) pair in the committed crime dataset once,
via OpenStreetMap Nominatim (respecting its 1 request/second limit), and cache
the result to data/districts_geocoded.csv. Safe to re-run: rows already in the
cache are skipped, so an interrupted run just resumes.

Usage: python scripts/geocode_districts.py
"""
import time
from pathlib import Path

import httpx
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC_CSV = ROOT / "data" / "raw" / "district_wise_crimes_against_women_2001_2012.csv"
OUT_CSV = ROOT / "data" / "districts_geocoded.csv"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "SHEGUARD-safety-app/1.0 (district geocoding for area-risk model)"}


def load_cache():
    if OUT_CSV.exists():
        return pd.read_csv(OUT_CSV)
    return pd.DataFrame(columns=["state", "district", "lat", "lng"])


def geocode(query: str):
    with httpx.Client(timeout=15, headers=HEADERS) as client:
        resp = client.get(NOMINATIM_URL, params={"q": query, "format": "json", "limit": 1, "countrycodes": "in"})
        resp.raise_for_status()
        results = resp.json()
    if not results:
        return None
    return float(results[0]["lat"]), float(results[0]["lon"])


def main():
    df = pd.read_csv(SRC_CSV)
    df = df[~df["DISTRICT"].str.contains("TOTAL", case=False, na=False)]
    pairs = df[["STATE/UT", "DISTRICT"]].drop_duplicates().values.tolist()

    cache = load_cache()
    done = set(zip(cache["state"], cache["district"]))

    rows = cache.to_dict("records")
    total = len(pairs)
    for i, (state, district) in enumerate(pairs, 1):
        if (state, district) in done:
            continue
        query = f"{district.title()}, {state.title()}, India"
        try:
            result = geocode(query)
        except httpx.HTTPError as e:
            print(f"[{i}/{total}] ERROR {query}: {e}")
            result = None

        if result:
            lat, lng = result
            print(f"[{i}/{total}] OK {query} -> {lat:.4f},{lng:.4f}")
            rows.append({"state": state, "district": district, "lat": lat, "lng": lng})
        else:
            print(f"[{i}/{total}] MISS {query}")

        # Persist incrementally so an interrupted run keeps its progress.
        pd.DataFrame(rows).to_csv(OUT_CSV, index=False)
        time.sleep(1.1)

    print(f"Done. Geocoded {len(rows)}/{total} districts -> {OUT_CSV}")


if __name__ == "__main__":
    main()
