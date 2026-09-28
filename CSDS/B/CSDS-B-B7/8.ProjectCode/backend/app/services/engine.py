"""Core prediction and forecasting engine (shared by the API and ml/ scripts).

- Length-of-stay: XGBoost regressor (days) + classifier (long stay), SHAP TreeExplainer for reasons.
- Admissions: XGBoost model on lag features, per facility x ward, direct multi-horizon.
- Census: in-house patients survive by their predicted remaining stay (residual distribution of the
  LOS model); forecast arrivals survive by the ward's length-of-stay curve. Mean and variance are
  summed, giving a 90% band.
"""
import json
import math
from functools import cached_property

import numpy as np
import pandas as pd
import xgboost as xgb

from ..config import (EQUIPMENT, FACILITIES, LONG_STAY_DAYS, MODELS_DIR, NURSE_RATIO, OPERATING_DAY,
                      PROCESSED_DIR, SHIFTS, WARDS)

FLAGS = ["dialysisrenalendstage", "asthma", "irondef", "pneum", "substancedependence",
         "psychologicaldisordermajor", "depress", "psychother", "fibrosisandother", "malnutrition", "hemo"]
NUMERIC = ["hematocrit", "neutrophils", "sodium", "glucose", "bloodureanitro", "creatinine", "bmi",
           "pulse", "respiration", "secondarydiagnosisnonicd9"]
FEATURES = ["rcount", "gender_f"] + FLAGS + NUMERIC + [f"facility_{f}" for f in FACILITIES]
LABELS = {
    "rcount": "Readmissions (last 180 days)", "gender_f": "Female",
    "dialysisrenalendstage": "End-stage renal disease", "asthma": "Asthma", "irondef": "Iron deficiency",
    "pneum": "Pneumonia", "substancedependence": "Substance dependence",
    "psychologicaldisordermajor": "Major psychological disorder", "depress": "Depression",
    "psychother": "Other psychological disorder", "fibrosisandother": "Fibrosis", "malnutrition": "Malnutrition",
    "hemo": "Blood disorder", "hematocrit": "Hematocrit (g/dL)", "neutrophils": "Neutrophils (cells/uL)",
    "sodium": "Sodium (mmol/L)", "glucose": "Glucose (mg/dL)", "bloodureanitro": "Blood urea nitrogen (mg/dL)",
    "creatinine": "Creatinine (mg/dL)", "bmi": "BMI", "pulse": "Pulse (bpm)", "respiration": "Respiration",
    "secondarydiagnosisnonicd9": "Secondary diagnoses",
    **{f"facility_{f}": f"Admitted to Facility {f}" for f in FACILITIES},
}
TRAIN_END_DAY = 274  # admissions before this day train the models; later ones are held out
HORIZON_MAX = 14
Z90 = 1.645
WARN_Z = 1.0  # early warning when P(census > capacity) is about 1 in 6 or more (tuned in ml/eval.py)


def los_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Model feature matrix from raw patient columns (facid, gender, flags, labs...)."""
    X = pd.DataFrame(index=df.index)
    X["rcount"] = df["rcount"].astype(float)
    X["gender_f"] = (df["gender"] == "F").astype(float)
    for c in FLAGS + NUMERIC:
        X[c] = df[c].astype(float)
    for f in FACILITIES:
        X[f"facility_{f}"] = (df["facid"] == f).astype(float)
    return X[FEATURES]


def arrival_matrix(patients: pd.DataFrame, last_day: int) -> dict:
    out = {}
    for f in FACILITIES:
        for w in WARDS:
            g = patients[(patients.facid == f) & (patients.ward == w) & (patients.admit_day <= last_day)]
            out[(f, w)] = np.bincount(g.admit_day, minlength=last_day + 1)[: last_day + 1].astype(float)
    return out


def arrival_features(series: np.ndarray, origin: int, f: str, w: str) -> np.ndarray:
    """Rows for horizons 1..HORIZON_MAX from arrivals observed up to and including `origin`."""
    rows = []
    m7 = series[origin - 6: origin + 1].mean()
    m28 = series[origin - 27: origin + 1].mean()
    for h in range(1, HORIZON_MAX + 1):
        t = origin + h
        k0 = math.ceil(h / 7)
        same = [series[t - 7 * k] for k in range(k0, k0 + 4)]
        rows.append([FACILITIES.index(f), WARDS.index(w), t % 7, h, m7, m28, float(np.mean(same)), series[origin]])
    return np.array(rows)


ARRIVAL_FEATURES = ["facility", "ward", "weekday", "horizon", "mean_7d", "mean_28d", "same_weekday_4w", "last_day"]


def ward_survival(patients: pd.DataFrame) -> dict:
    """S[(facility, ward)][k] = P(length of stay > k), k = 0..40 (training admissions only)."""
    out = {}
    tr = patients[patients.admit_day < TRAIN_END_DAY]
    for f in FACILITIES:
        for w in WARDS:
            los = tr[(tr.facid == f) & (tr.ward == w)].lengthofstay.values
            out[(f, w)] = np.array([(los > k).mean() for k in range(41)])
    return out


class Engine:
    def __init__(self):
        self.patients = pd.read_csv(PROCESSED_DIR / "patients.csv.gz")
        self.config = json.loads((MODELS_DIR / "hospital_config.json").read_text())
        self.meta = json.loads((MODELS_DIR / "los_meta.json").read_text())
        self.reg = xgb.XGBRegressor()
        self.reg.load_model(MODELS_DIR / "los_regressor.json")
        self.clf = xgb.XGBClassifier()
        self.clf.load_model(MODELS_DIR / "los_classifier.json")
        self.arr = xgb.XGBRegressor()
        self.arr.load_model(MODELS_DIR / "arrivals.json")
        self.residuals = np.array(self.meta["residual_quantiles"])
        self.survival = ward_survival(self.patients)
        self.arrivals = arrival_matrix(self.patients, OPERATING_DAY)
        self.patients["pred_los"] = self.reg.predict(los_frame(self.patients)).clip(1, None)

    @cached_property
    def explainer(self):
        import shap
        return shap.TreeExplainer(self.reg)

    # ---------- length of stay ----------
    def predict_one(self, record: dict) -> dict:
        df = pd.DataFrame([record])
        X = los_frame(df)
        days = float(max(1.0, self.reg.predict(X)[0]))
        p_long = float(self.clf.predict_proba(X)[0, 1])
        sv = self.explainer(X)
        contrib = sv.values[0]
        base = float(np.atleast_1d(sv.base_values)[0])
        reasons = []
        for i in np.argsort(-np.abs(contrib)):
            name = FEATURES[i]
            if name.startswith("facility_") and X.iloc[0][name] == 0:
                continue
            reasons.append({"feature": name, "label": LABELS[name], "value": float(X.iloc[0][name]),
                            "impact_days": round(float(contrib[i]), 2)})
            if len(reasons) == 8:
                break
        lo, hi = np.quantile(days + self.residuals, [0.1, 0.9]).clip(1, None)
        return {"predicted_days": round(days, 1), "range_days": [round(float(lo), 1), round(float(hi), 1)],
                "long_stay": p_long >= 0.5, "long_stay_probability": round(p_long, 3),
                "long_stay_threshold_days": LONG_STAY_DAYS, "baseline_days": round(base, 2), "reasons": reasons}

    # ---------- census ----------
    def in_house(self, day: int) -> pd.DataFrame:
        p = self.patients
        return p[(p.admit_day <= day) & (p.discharge_day > day)]

    def actual_census(self, day: int) -> dict:
        h = self.in_house(day)
        c = h.groupby(["facid", "ward"]).size()
        return {(f, w): int(c.get((f, w), 0)) for f in FACILITIES for w in WARDS}

    def forecast_arrivals(self, origin: int) -> dict:
        keys = [(f, w) for f in FACILITIES for w in WARDS]
        X = np.vstack([arrival_features(self.arrivals[k], origin, *k) for k in keys])
        pred = self.arr.predict(X).clip(0, None).reshape(len(keys), HORIZON_MAX)
        return {k: pred[i] for i, k in enumerate(keys)}

    def _stay_probs(self, pred_los: np.ndarray, elapsed: np.ndarray, keys: list, horizon: int) -> np.ndarray:
        """P(patient still in bed at day origin+k), k=1..horizon; shape (n, horizon)."""
        samples = np.clip(np.rint(pred_los[:, None] + self.residuals[None, :]), 1, None)  # stays are whole days
        denom = (samples > elapsed[:, None]).mean(axis=1)
        out = np.empty((len(pred_los), horizon))
        for k in range(1, horizon + 1):
            out[:, k - 1] = (samples > (elapsed + k)[:, None]).mean(axis=1)
        ok = denom > 0
        out[ok] /= denom[ok, None]
        for i in np.where(~ok)[0]:  # model says the stay should be over: fall back to ward curve
            s = self.survival[keys[i]]
            e = min(int(elapsed[i]), 39)
            out[i] = [s[min(e + k, 40)] / max(s[e], 1e-6) for k in range(1, horizon + 1)]
        return out

    def forecast_census(self, origin: int, horizon: int = 14, extra: pd.DataFrame | None = None) -> dict:
        """{(facility, ward): {"current", "mean"[h], "var"[h], "arrivals"[h]}} for days origin+1..origin+h."""
        h = self.in_house(origin)[["facid", "ward", "admit_day", "pred_los"]].copy()
        h["elapsed"] = origin - h.admit_day
        if extra is not None and len(extra):
            h = pd.concat([h, extra[["facid", "ward", "pred_los", "elapsed"]]], ignore_index=True)
        probs = self._stay_probs(h.pred_los.values.astype(float), h.elapsed.values.astype(float),
                                 list(zip(h.facid, h.ward)), horizon)
        arrivals = self.forecast_arrivals(origin)
        out = {}
        for f in FACILITIES:
            for w in WARDS:
                m = ((h.facid == f) & (h.ward == w)).values
                p = probs[m]
                mean = p.sum(axis=0)
                var = (p * (1 - p)).sum(axis=0)
                lam = arrivals[(f, w)][:horizon]
                s = self.survival[(f, w)]
                for k in range(1, horizon + 1):
                    contrib = sum(lam[j - 1] * s[k - j] for j in range(1, k + 1))
                    mean[k - 1] += contrib
                    var[k - 1] += contrib
                out[(f, w)] = {"current": int(m.sum()), "mean": mean, "var": var, "arrivals": lam}
        return out

    # ---------- resources ----------
    def nurses_needed(self, ward: str, patients: float) -> dict:
        return {s: int(math.ceil(max(patients, 0) / NURSE_RATIO[ward][s])) for s in SHIFTS}

    def equipment_needed(self, load_by_ward: dict) -> dict:
        rates = self.config["equipment_rates"]
        return {e: int(math.ceil(sum(load_by_ward[w] * rates[w][e] for w in WARDS) - 1e-9)) for e in EQUIPMENT}


_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = Engine()
    return _engine
