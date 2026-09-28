"""Prepare patient history and the default hospital structure from the raw datasets.

Outputs
  data/processed/patients.csv.gz   one row per stay with admit/discharge day index and ward
  models/hospital_config.json      ward mix, capacity, nurse roster, equipment inventory and usage rates
Seeded (SEED = 42) so the result is reproducible.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.config import (EQUIPMENT, FACILITIES, MODELS_DIR, NURSE_RATIO, OPERATING_DAY,  # noqa: E402
                        PROCESSED_DIR, RAW_DIR, SHIFTS, WARDS)

SEED = 42
FLAGS = ["dialysisrenalendstage", "asthma", "irondef", "pneum", "substancedependence",
         "psychologicaldisordermajor", "depress", "psychother", "fibrosisandother", "malnutrition", "hemo"]
MATERNITY_SHARE = 0.12  # default hospital structure (female admissions only)


def ward_mix():
    beds = pd.read_csv(RAW_DIR / "beds" / "services_weekly.csv")
    adm = beds.groupby("service").patients_admitted.sum()
    icu_share = adm["ICU"] / adm.sum()
    surg_share = adm["surgery"] / adm.sum()
    av = pd.read_csv(RAW_DIR / "av" / "train_data.csv", usecols=["Age"])
    paed_share = av.Age.isin(["0-10", "11-20"]).mean()
    return {"ICU": float(icu_share), "Surgical": float(surg_share),
            "Paediatric": float(paed_share), "Maternity": MATERNITY_SHARE}


def severity_score(d):
    s = d[FLAGS].sum(axis=1) + d.secondarydiagnosisnonicd9 * 0.5
    s += ((d.sodium < 133) | (d.sodium > 145)).astype(int)
    s += (d.creatinine > 1.5).astype(int)
    s += (d.pulse > 100).astype(int)
    s += ((d.respiration < 4) | (d.respiration > 9)).astype(int)
    s += (d.bloodureanitro > 25).astype(int)
    s += d.rcount * 0.5
    return s


def assign_wards(d, mix, rng):
    n = len(d)
    score = severity_score(d) + rng.normal(0, 1.0, n)
    ward = np.array(["General"] * n, dtype=object)
    pct = score.groupby(d.facid.values).rank(ascending=False, pct=True)  # ICU share per facility
    icu = pct <= mix["ICU"]
    ward[icu.values] = "ICU"
    rest = ~icu.values
    u = rng.random(n)
    female = (d.gender == "F").values
    p_mat = mix["Maternity"] / max(female[rest].mean(), 1e-6)  # keep overall maternity share
    p_paed, p_surg = mix["Paediatric"], mix["Surgical"]
    paed = rest & (u < p_paed)
    mat = rest & ~paed & female & (u < p_paed + p_mat * (1 - p_paed))
    p_surg_rest = p_surg / (1 - mix["ICU"] - mix["Paediatric"] - mix["Maternity"])
    surg = rest & ~paed & ~mat & (rng.random(n) < p_surg_rest)
    ward[paed] = "Paediatric"
    ward[mat] = "Maternity"
    ward[surg] = "Surgical"
    return ward


def daily_census(p, first, last):
    """Midnight census per (facility, ward, day): admitted <= day < discharged."""
    days = np.arange(first, last + 1)
    out = {}
    for (f, w), g in p.groupby(["facid", "ward"]):
        a = np.bincount(g.admit_day.clip(upper=last + 1), minlength=last + 2)
        dsc = np.bincount(g.discharge_day.clip(upper=last + 1), minlength=last + 2)
        census = np.cumsum(a - dsc)
        out[(f, w)] = census[days]
    return days, out


def main():
    rng = np.random.default_rng(SEED)
    d = pd.read_csv(RAW_DIR / "los" / "LengthOfStay.csv", parse_dates=["vdate", "discharged"])
    d["rcount"] = d.rcount.replace("5+", "5").astype(int)
    d["admit_day"] = (d.vdate - pd.Timestamp("2012-01-01")).dt.days
    d["discharge_day"] = d.admit_day + d.lengthofstay
    d = d[d.admit_day <= OPERATING_DAY].copy()
    mix = ward_mix()
    d["ward"] = assign_wards(d, mix, rng)
    cols = ["eid", "admit_day", "discharge_day", "lengthofstay", "facid", "ward", "rcount", "gender"] + FLAGS + [
        "hematocrit", "neutrophils", "sodium", "glucose", "bloodureanitro", "creatinine", "bmi", "pulse",
        "respiration", "secondarydiagnosisnonicd9"]
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    d[cols].to_csv(PROCESSED_DIR / "patients.csv.gz", index=False, compression="gzip")

    # Default structure: capacity at the 90th percentile of census, roster and equipment sized to the
    # mean of the last 90 days (equipment +15% buffer) - a static plan, which is what the optimiser is compared against).
    days, census = daily_census(d, 30, OPERATING_DAY)
    recent = days > OPERATING_DAY - 90
    rates = {}
    for w in WARDS:
        g = d[d.ward == w]
        rates[w] = {
            "Ventilator": round(float(g.pneum.mean() + (g.respiration < 4).mean()), 3) if w == "ICU" else 0.0,
            "Cardiac monitor": {"ICU": 1.0, "Surgical": 0.3}.get(w, 0.1),
            "Infusion pump": {"ICU": 2.0, "Surgical": 0.8, "General": 0.5, "Maternity": 0.4, "Paediatric": 0.5}[w],
            "Dialysis machine": round(float(g.dialysisrenalendstage.mean()), 3),
        }
    capacity, roster, inventory, mean_census = {}, {}, {}, {}
    for f in FACILITIES:
        capacity[f], roster[f], mean_census[f] = {}, {}, {}
        for w in WARDS:
            c = census.get((f, w), np.zeros(len(days)))
            capacity[f][w] = int(max(2, math.ceil(np.quantile(c, 0.9))))
            m = float(c[recent].mean())
            mean_census[f][w] = round(m, 1)
            roster[f][w] = {s: int(max(1, math.ceil(m / NURSE_RATIO[w][s]))) for s in SHIFTS}
        inventory[f] = {e: int(max(1, math.ceil(1.15 * sum(mean_census[f][w] * rates[w][e] for w in WARDS))))
                        for e in EQUIPMENT}
    cfg = {"seed": SEED, "ward_mix": mix, "equipment_rates": rates, "capacity": capacity,
           "roster": roster, "inventory": inventory, "mean_census_90d": mean_census,
           "ward_counts": d.ward.value_counts().to_dict()}
    MODELS_DIR.mkdir(exist_ok=True)
    (MODELS_DIR / "hospital_config.json").write_text(json.dumps(cfg, indent=2))
    print(json.dumps({"rows": len(d), "ward_mix": mix, "ward_counts": cfg["ward_counts"], "capacity": capacity}, indent=1))


if __name__ == "__main__":
    main()
