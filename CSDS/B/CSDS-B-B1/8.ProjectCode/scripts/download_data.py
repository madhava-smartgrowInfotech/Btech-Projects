"""Download every dataset CivicPulse trains on into data/raw/.

    python scripts/download_data.py            # all sources
    python scripts/download_data.py --skip-nyc # Kaggle sources only

Kaggle datasets are public and are fetched with kagglehub (no token needed for
public data; set KAGGLE_USERNAME/KAGGLE_KEY if your network requires it).
NYC 311 comes from the city's open-data API (no key).
"""
import argparse
import json
import shutil
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
sys.path.insert(0, str(ROOT / "backend"))
from app.services.taxonomy import NYC_TYPES  # noqa: E402

NYC_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
# One year of requests that were opened and closed, sampled month by month so
# weekday / seasonal patterns are represented. ~700 rows per type per month.
NYC_MONTHS = pd.date_range("2025-03-01", "2026-03-01", freq="MS")
NYC_ROWS_PER_MONTH = 700


def kaggle_file(handle, path):
    import kagglehub

    return Path(kagglehub.dataset_download(handle, path=path))


def download_kaggle():
    RAW.mkdir(parents=True, exist_ok=True)
    print("Kaggle: CivicComp-HiEn (complaint CSV only - the 1.1 GB model weights are not needed)")
    src = kaggle_file("shyamtripathi373/civiccomp-hien-hindienglish-civic-complaints",
                      "annotated_complaints_with_severity.csv")
    pd.read_csv(src).to_csv(RAW / "civiccomp_hien.csv.gz", index=False, compression="gzip")

    print("Kaggle: Citizen Grievance Dataset")
    for name, out in [("grievances_synthetic.csv", "citizen_grievance.csv"),
                      ("grievances_holdout_templates.csv", "citizen_grievance_holdout.csv")]:
        shutil.copy(kaggle_file("abhisheksingh016/citizen-grievance-dataset", name), RAW / out)

    print("Kaggle: Indian Citizen Complaint")
    src = kaggle_file("shebinsam2004/indian-citizen-complaint", "fine_tuning_grievances.csv")
    pd.read_csv(src).to_csv(RAW / "indian_citizen_complaint.csv.gz", index=False, compression="gzip")


def nyc_fetch(complaint_type, start, end):
    where = (f"complaint_type='{complaint_type}' AND closed_date IS NOT NULL AND "
             f"created_date >= '{start:%Y-%m-%dT00:00:00}' AND created_date < '{end:%Y-%m-%dT00:00:00}'")
    q = {"$select": "unique_key,complaint_type,descriptor,agency,borough,created_date,closed_date",
         "$where": where, "$limit": str(NYC_ROWS_PER_MONTH)}
    url = NYC_URL + "?" + urllib.parse.urlencode(q)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                return json.load(r)
        except Exception as e:  # network hiccups / API throttling
            if attempt == 3:
                print(f"  ! {complaint_type} {start:%Y-%m}: {e}")
                return []
            time.sleep(5 * (attempt + 1))


def download_nyc():
    types = sorted({t for ts in NYC_TYPES.values() for t in ts})
    jobs = [(t, s, e) for t in types for s, e in zip(NYC_MONTHS[:-1], NYC_MONTHS[1:])]
    print(f"NYC 311: {len(jobs)} requests ({len(types)} complaint types x 12 months)")
    rows = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for i, part in enumerate(pool.map(lambda j: nyc_fetch(*j), jobs), 1):
            rows.extend(part)
            if i % 40 == 0:
                print(f"  {i}/{len(jobs)} requests, {len(rows)} rows")
    df = pd.DataFrame(rows).drop_duplicates("unique_key")
    df.to_csv(RAW / "nyc311_resolution.csv.gz", index=False, compression="gzip")
    print(f"NYC 311: saved {len(df)} rows")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-nyc", action="store_true")
    ap.add_argument("--skip-kaggle", action="store_true")
    a = ap.parse_args()
    if not a.skip_kaggle:
        download_kaggle()
    if not a.skip_nyc:
        download_nyc()
    print("Done ->", RAW)
