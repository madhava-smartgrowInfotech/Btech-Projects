"""Generate the synthetic triage dataset (seeded, reproducible).

SYNTHETIC DATA: rows are simulated from clinical archetypes and a severity score; the
`priority` column plays the role of the clinician-recorded outcome. It is not patient data.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.features import FLAGS, VITALS  # noqa: E402

SEED = 7307
N = 6000

# archetype -> (weight, flag probabilities, vital shifts)
ARCH = {
    "minor": (0.34, {"vomiting": .08, "abd_pain": .08, "fever": .12, "trauma": .12, "fracture": .03,
                     "hypertension": .15, "diabetes": .08}, dict(hr=0, sbp=0, spo2=0, temp=0, rr=0)),
    "cardiac": (0.14, {"chest_pain": .8, "dyspnea": .35, "syncope": .15, "st_elevation": .22, "cardiac_hx": .5,
                       "hypertension": .5, "diabetes": .3, "lab_troponin_high": .35, "anticoagulant": .1},
                dict(hr=8, sbp=5, spo2=-1, temp=0, rr=2)),
    "respiratory": (0.12, {"dyspnea": .9, "fever": .4, "infiltrate": .4, "copd": .5, "chest_pain": .15,
                           "lab_wbc_high": .3}, dict(hr=10, sbp=0, spo2=-5, temp=0.5, rr=7)),
    "neuro": (0.08, {"stroke_signs": .5, "altered_mental": .35, "severe_headache": .45, "ct_hemorrhage": .12,
                     "prior_stroke": .2, "hypertension": .6, "anticoagulant": .15, "vomiting": .25},
              dict(hr=0, sbp=22, spo2=-1, temp=0, rr=1)),
    "trauma": (0.12, {"trauma": .95, "fracture": .45, "bleeding": .35, "free_fluid": .08, "lab_hgb_low": .12,
                      "abd_pain": .2, "anticoagulant": .08}, dict(hr=12, sbp=-6, spo2=-1, temp=0, rr=3)),
    "infection": (0.10, {"fever": .85, "altered_mental": .15, "lab_wbc_high": .65, "lab_lactate_high": .22,
                         "vomiting": .25, "diabetes": .25, "lab_creatinine_high": .2},
                  dict(hr=18, sbp=-12, spo2=-2, temp=1.4, rr=5)),
    "abdominal": (0.10, {"abd_pain": .95, "vomiting": .55, "fever": .2, "free_fluid": .12, "bleeding": .1,
                         "lab_wbc_high": .3, "lab_lactate_high": .1, "lab_hgb_low": .08},
                  dict(hr=8, sbp=-3, spo2=0, temp=0.3, rr=2)),
}

SCORE_VITALS = None  # documented below in severity()


def severity(r):
    s = 0.0
    hr, sbp, spo2, t, rr, age = r["heart_rate"], r["sbp"], r["spo2"], r["temp_c"], r["resp_rate"], r["age"]
    s += 2 if hr > 130 else 1 if hr > 110 else 1.5 if hr < 45 else 0
    s += 3 if sbp < 90 else 1.5 if sbp < 100 else 1 if sbp > 180 else 0
    s += 3.5 if spo2 < 90 else 1.5 if spo2 < 94 else 0
    s += 1.5 if t > 39.5 else 0.7 if t > 38.3 else 1.5 if t < 35 else 0
    s += 2 if rr > 28 else 1 if rr > 22 else 0
    s += 0.8 if age > 75 else 0
    s += {0: 0, 1: 0.5, 2: 0.8}[int(r["arrival_code"])]
    w = dict(st_elevation=4, ct_hemorrhage=4, stroke_signs=3, altered_mental=2.5, chest_pain=1.2, dyspnea=1.5,
             syncope=1.5, bleeding=1.5, trauma=1, fever=.4, abd_pain=.6, infiltrate=1, fracture=.8,
             free_fluid=2, lab_troponin_high=2.5, lab_lactate_high=2.5, lab_wbc_high=.7, lab_glucose_abn=1,
             lab_creatinine_high=.8, lab_hgb_low=1, cardiac_hx=.5, copd=.4, anticoagulant=.5, diabetes=.3,
             hypertension=.2, prior_stroke=.3, severe_headache=.8, vomiting=.2)
    for k, v in w.items():
        s += v * r[k]
    return s


def to_priority(s):
    return np.select([s >= 8, s >= 5.2, s >= 3.0, s >= 1.2], [1, 2, 3, 4], default=5)


def generate(n=N, seed=SEED):
    rng = np.random.default_rng(seed)
    names = list(ARCH)
    p = np.array([ARCH[k][0] for k in names])
    kinds = rng.choice(len(names), size=n, p=p / p.sum())
    rows = []
    for k in kinds:
        _, probs, sh = ARCH[names[k]]
        age = int(np.clip(rng.gamma(4.2, 11) + 3, 1, 98))
        arrival = rng.choice(["walk-in", "ambulance", "transfer"],
                             p=[.55, .35, .10] if names[k] in ("minor", "abdominal") else [.25, .6, .15])
        arrival_code = {"walk-in": 0, "transfer": 1, "ambulance": 2}[arrival]
        r = dict(
            age=age,
            heart_rate=int(np.clip(rng.normal(82 + sh["hr"], 14), 35, 190)),
            sbp=int(np.clip(rng.normal(124 + sh["sbp"] + (age - 45) * 0.25, 17), 60, 240)),
            spo2=int(np.clip(rng.normal(97.5 + sh["spo2"], 2.0), 70, 100)),
            temp_c=round(float(np.clip(rng.normal(36.8 + sh["temp"], 0.5), 33.5, 41.5)), 1),
            resp_rate=int(np.clip(rng.normal(16 + sh["rr"], 3), 6, 50)),
            arrival_code=arrival_code,
        )
        r["dbp"] = int(np.clip(r["sbp"] * 0.62 + rng.normal(0, 7), 30, 140))
        for f in FLAGS:
            base = 0.02 if f.startswith("lab_") or f in ("hypertension", "diabetes") else 0.01
            r[f] = int(rng.random() < probs.get(f, base + (0.04 if f in ("hypertension", "diabetes") else 0)))
        r["arch"] = names[k]
        r["arrival_mode"] = arrival
        s = severity(r) + rng.normal(0, 0.4)
        r["priority"] = int(to_priority(np.array([s]))[0])
        rows.append(r)
    df = pd.DataFrame(rows)
    return df[VITALS + FLAGS + ["arrival_mode", "arch", "priority"]]


if __name__ == "__main__":
    out = ROOT / "data" / "sample" / "triage_synthetic.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df = generate()
    df.to_csv(out, index=False)
    print(out, df.shape)
    print(df["priority"].value_counts(normalize=True).sort_index().round(3).to_string())
