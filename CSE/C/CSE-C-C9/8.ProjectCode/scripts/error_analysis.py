"""Error analysis of the selected model on the held-out test split, plus real sample predictions from the API.

Reproduces the stratified 80/20 split of scripts/train.py, loads models/best_model.pkl and writes
  artifacts/error_analysis.json     (group-wise error rates, confident mistakes)
  artifacts/sample_predictions.json (five profiles sent to the running API on http://127.0.0.1:8409)

    python scripts/error_analysis.py        (run in the project .venv)
"""
import json
import sys
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import requests
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from feature_engineering import (COLUMN_NAMES, TARGET_COL, POSITIVE_LABEL, RANDOM_STATE,  # noqa: E402
                                 clean_frame, add_derived_features)

API = "http://127.0.0.1:8409"
SHOW = ["age", "workclass", "education", "marital-status", "occupation", "relationship", "sex", "capital-gain", "capital-loss", "hours-per-week"]


def load():
    raw = ROOT / "data" / "raw"
    tr = pd.read_csv(raw / "adult.data", header=None, names=COLUMN_NAMES, skipinitialspace=True)
    te = pd.read_csv(raw / "adult.test", header=None, names=COLUMN_NAMES, skipinitialspace=True, skiprows=1)
    return pd.concat([tr, te], ignore_index=True)


def rates(y, pred):
    y, pred = np.asarray(y), np.asarray(pred)
    tp = int(((y == 1) & (pred == 1)).sum()); fn = int(((y == 1) & (pred == 0)).sum())
    fp = int(((y == 0) & (pred == 1)).sum()); tn = int(((y == 0) & (pred == 0)).sum())
    n = len(y)
    return {"n": n, "actual_pos_rate": round((tp + fn) / n, 4), "pred_pos_rate": round((tp + fp) / n, 4),
            "recall": round(tp / (tp + fn), 4) if tp + fn else None,
            "precision": round(tp / (tp + fp), 4) if tp + fp else None,
            "fpr": round(fp / (fp + tn), 4) if fp + tn else None,
            "accuracy": round((tp + tn) / n, 4)}


def main():
    df = add_derived_features(clean_frame(load()).dropna(subset=[TARGET_COL]))
    y = (df[TARGET_COL] == POSITIVE_LABEL).astype(int)
    X = df.drop(columns=[TARGET_COL])
    _, X_te, _, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)
    pipe = joblib.load(ROOT / "models" / "best_model.pkl")
    p = pipe.predict_proba(X_te)[:, 1]
    pred = (p >= 0.5).astype(int)
    T = X_te.copy()
    T["y"], T["p"], T["pred"] = y_te.values, p, pred

    groups = {}
    for col, label in (("sex", "Sex"), ("race", "Race"), ("education-tier", "Education tier"), ("age-band", "Age band"),
                       ("region", "Region of origin"), ("employment-stability", "Employment type")):
        g = {}
        for k, sub in T.groupby(col):
            if len(sub) >= 30:
                g[str(k)] = rates(sub["y"], sub["pred"])
        groups[label] = g
    ms = {}
    for k, sub in T.assign(ms=np.where(T["marital-status"] == "Married-civ-spouse", "Married-civ-spouse", "All other statuses")).groupby("ms"):
        ms[k] = rates(sub["y"], sub["pred"])
    groups["Marital status"] = ms

    def pick(mask, ascending, k=5):
        sub = T[mask].sort_values("p", ascending=ascending).head(k)
        rows = []
        for _, r in sub.iterrows():
            row = {c: (r[c].item() if hasattr(r[c], "item") else r[c]) for c in SHOW}
            row["p"] = round(float(r["p"]), 4)
            rows.append(row)
        return rows

    fp_rows = pick((T["y"] == 0) & (T["pred"] == 1), False)       # most confident false positives
    fn_rows = pick((T["y"] == 1) & (T["pred"] == 0), True)        # most confident false negatives
    # confidence summary
    conf = np.where(pred == 1, p, 1 - p)
    ok = pred == y_te.values
    summary = {"n_wrong": int((~ok).sum()), "n_right": int(ok.sum()),
               "mean_confidence_right": round(float(conf[ok].mean()), 4), "mean_confidence_wrong": round(float(conf[~ok].mean()), 4),
               "wrong_with_conf_ge_0.9": int(((~ok) & (conf >= 0.9)).sum()), "right_with_conf_ge_0.9": int((ok & (conf >= 0.9)).sum()),
               "wrong_with_conf_lt_0.6": int(((~ok) & (conf < 0.6)).sum()),
               "borderline_0.35_0.65": int(((p >= 0.35) & (p <= 0.65)).sum())}
    # accuracy among rows with extreme capital gains (spike at 99,999 is a known Adult quirk)
    spike = T["capital-gain"] >= 99999
    summary["rows_gain_99999_in_test"] = int(spike.sum())
    summary["gain_99999_positive_rate"] = round(float(T.loc[spike, "y"].mean()), 4) if spike.any() else None
    out = {"test_rows": int(len(T)), "groups": groups, "confident_false_positives": fp_rows,
           "confident_false_negatives": fn_rows, "summary": summary}
    (ROOT / "artifacts" / "error_analysis.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(summary, indent=2))
    for g, d in groups.items():
        print(g, {k: (v["n"], v["recall"], v["fpr"], v["pred_pos_rate"]) for k, v in d.items()})

    # ---- real API samples
    profiles = [
        ("A", "Adult row 1 (Census sample record)", {"age": 39, "workclass": "State-gov", "education": "Bachelors", "marital-status": "Never-married",
                                                 "occupation": "Adm-clerical", "relationship": "Not-in-family", "race": "White", "sex": "Male",
                                                 "native-country": "United-States", "capital-gain": 2174, "capital-loss": 0, "hours-per-week": 40}),
        ("B", "Mid-career manager", {"age": 52, "workclass": "Private", "education": "Masters", "marital-status": "Married-civ-spouse",
                                    "occupation": "Exec-managerial", "relationship": "Husband", "race": "White", "sex": "Male",
                                    "native-country": "United-States", "capital-gain": 7688, "capital-loss": 0, "hours-per-week": 50}),
        ("C", "Dual-income household, sales", {"age": 34, "workclass": "Local-gov", "education": "Some-college", "marital-status": "Married-civ-spouse",
                                              "occupation": "Sales", "relationship": "Wife", "race": "White", "sex": "Female",
                                              "native-country": "United-States", "capital-gain": 0, "capital-loss": 0, "hours-per-week": 42}),
        ("D", "Young part-time worker", {"age": 22, "workclass": "Private", "education": "HS-grad", "marital-status": "Never-married",
                                        "occupation": "Other-service", "relationship": "Own-child", "race": "Black", "sex": "Female",
                                        "native-country": "United-States", "capital-gain": 0, "capital-loss": 0, "hours-per-week": 20}),
        ("E", "Professional with investment losses", {"age": 45, "workclass": "Self-emp-inc", "education": "Doctorate", "marital-status": "Divorced",
                                                     "occupation": "Prof-specialty", "relationship": "Not-in-family", "race": "Asian-Pac-Islander", "sex": "Male",
                                                     "native-country": "India", "capital-gain": 0, "capital-loss": 1902, "hours-per-week": 55}),
    ]
    samples = []
    for sid, name, prof in profiles:
        r = requests.post(API + "/api/predict", json=prof, timeout=60).json()["result"]
        top = (r["shap"]["positives"][:2] + r["shap"]["negatives"][:1])
        samples.append({"id": sid, "name": name, "inputs": prof, "proba": r["proba"], "strength_pct": r["strength_pct"], "profile": r["profile"], "risk": r["risk"],
                        "top_drivers": [{"label": d["label"], "shap": d["shap"]} for d in top]})
        print(sid, r["proba"], r["profile"], r["risk"])
    (ROOT / "artifacts" / "sample_predictions.json").write_text(json.dumps(samples, indent=2))


if __name__ == "__main__":
    main()
