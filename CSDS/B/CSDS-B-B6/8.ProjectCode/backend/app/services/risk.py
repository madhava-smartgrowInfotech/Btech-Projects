"""Random Forest risk scoring on values read from the unified FHIR record, with per-patient top factors."""
from datetime import date

import joblib
import numpy as np

from ..config import MODELS_DIR

_models = {}
PREGNANCY_CODES = {"72892002", "77386006"}  # normal pregnancy, pregnancy


def model(name: str) -> dict:
    if name not in _models:
        _models[name] = joblib.load(MODELS_DIR / f"{name}_rf.joblib")
    return _models[name]


def _latest(obs: list[tuple[str, dict]], code: str):
    """Latest numeric value for a LOINC code, including blood pressure panel components."""
    best = None
    for hkey, r in obs:
        date_ = r.get("effectiveDateTime", "")
        vals = []
        if any(c.get("code") == code for c in r.get("code", {}).get("coding", [])) and "valueQuantity" in r:
            vals.append(r["valueQuantity"]["value"])
        for comp in r.get("component", []):
            if any(c.get("code") == code for c in comp.get("code", {}).get("coding", [])) and "valueQuantity" in comp:
                vals.append(comp["valueQuantity"]["value"])
        if vals and (best is None or date_ > best[1]):
            best = (float(vals[0]), date_, hkey)
    return best


def extract_features(person: dict, resources: list[tuple[str, dict]]) -> dict:
    obs = [(h, r) for h, r in resources if r["resourceType"] == "Observation"]
    conds = [r for _, r in resources if r["resourceType"] == "Condition"]
    birth = date.fromisoformat(person["birth_date"])
    age = (date.today() - birth).days // 365
    found = {"age": (age, None, None), "sex": (1.0 if person["gender"] == "male" else 0.0, None, None)}
    for key, code in {"sbp": "8480-6", "dbp": "8462-4", "chol": "2093-3", "glucose": "2339-0", "bmi": "39156-5"}.items():
        v = _latest(obs, code)
        found[key] = v if v else (None, None, None)
    preg = 0 if person["gender"] == "male" else sum(
        1 for c in conds if any(x.get("code") in PREGNANCY_CODES for x in c.get("code", {}).get("coding", [])))
    glucose = found["glucose"]
    return {
        "heart": {"age": found["age"], "sex": found["sex"], "trestbps": found["sbp"], "chol": found["chol"],
                  "fbs": ((1.0 if glucose[0] > 120 else 0.0), glucose[1], glucose[2]) if glucose[0] is not None else (None, None, None)},
        "diabetes": {"Pregnancies": (float(preg), None, None), "Glucose": glucose, "BloodPressure": found["dbp"],
                     "BMI": found["bmi"], "Age": found["age"]},
    }


def score(name: str, feats: dict) -> dict:
    m = model(name)
    x, used = [], []
    for i, f in enumerate(m["features"]):
        val, when, hkey = feats[f]
        missing = val is None
        v = m["medians"][i] if missing else float(val)
        x.append(v)
        used.append({"feature": f, "label": m["labels"][f], "value": round(v, 2), "from_record": not missing,
                     "date": when, "hospital": hkey})
    X = np.array([x])
    p = float(m["model"].predict_proba(X)[0, 1])
    # Occlusion explanation: how much does the risk move if this value were replaced by the population median?
    factors = []
    for i, u in enumerate(used):
        if not u["from_record"]:
            continue
        Xi = X.copy()
        Xi[0, i] = m["medians"][i]
        delta = p - float(m["model"].predict_proba(Xi)[0, 1])
        factors.append({**u, "impact": round(delta, 3), "direction": "raises risk" if delta > 0 else "lowers risk"})
    factors.sort(key=lambda f: -abs(f["impact"]))
    level = "high" if p >= 0.6 else "moderate" if p >= 0.3 else "low"
    return {"model": name, "probability": round(p, 3), "level": level, "top_factors": factors[:3], "inputs": used,
            "importance": dict(zip(m["features"], [round(float(v), 3) for v in m["model"].feature_importances_]))}
