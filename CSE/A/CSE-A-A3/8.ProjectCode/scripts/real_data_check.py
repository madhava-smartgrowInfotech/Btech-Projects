"""Supplementary check on REAL public benchmark data (not used by the application).

The shipped models are trained on synthetic CSVs (generate_data.py). This script asks two questions the
synthetic hold-out cannot answer:
  (a) how do the same four algorithms, same settings, score when trained and cross-validated on the real
      public datasets with the matching schema (Pima, UCI Cleveland, UCI ILPD, UCI CKD)?
  (b) how do the SHIPPED synthetic-trained models score on those real records (distribution shift)?

Downloads happen once into docs/real_data/ (see REAL_DATA_URLS in the docs); this script only reads them.

    venv\\Scripts\\python scripts\\real_data_check.py        ->  docs/experiments/real_data_results.json
"""
import json
import os
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RD = os.path.join(ROOT, "docs", "real_data")
SEED = 42

BUILDERS = {
    "Logistic Regression": lambda: LogisticRegression(max_iter=1000, random_state=SEED),
    "Decision Tree": lambda: DecisionTreeClassifier(max_depth=6, random_state=SEED),
    "Random Forest": lambda: RandomForestClassifier(n_estimators=200, max_depth=8, random_state=SEED),
    "SVM": lambda: SVC(kernel="rbf", C=1.0, probability=True, random_state=SEED),
}


def load():
    out = {}
    d = pd.read_csv(os.path.join(RD, "pima_diabetes.csv"))
    feats = [c for c in d.columns if c != "Outcome"]
    for c in ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]:
        d[c] = d[c].replace(0, np.nan)  # zeros are recording gaps in Pima
    out["diabetes"] = (d[feats], d["Outcome"].astype(int), "Pima Indians Diabetes (NIDDK), 768 rows")

    h = pd.read_csv(os.path.join(RD, "uci_heart_cleveland.csv"))
    feats = [c for c in h.columns if c != "num"]
    out["heart"] = (h[feats], (h["num"] > 0).astype(int), "UCI Heart Disease, Cleveland, 303 rows")

    l = pd.read_csv(os.path.join(RD, "uci_ilpd_liver.csv"))
    X = pd.DataFrame({
        "Age": l["Age"], "Gender": (l["Gender"] == "Male").astype(int),
        "Total_Bilirubin": l["TB"], "Direct_Bilirubin": l["DB"], "Alkaline_Phosphotase": l["Alkphos"],
        "Alamine_Aminotransferase": l["Sgpt"], "Aspartate_Aminotransferase": l["Sgot"],
        "Total_Protiens": l["TP"], "Albumin": l["ALB"], "Albumin_and_Globulin_Ratio": l["A/G Ratio"]})
    out["liver"] = (X, (l["Selector"] == 1).astype(int), "UCI ILPD (Indian Liver Patient), 583 rows")

    k = pd.read_csv(os.path.join(RD, "uci_ckd.csv"))
    m = {"age": "age", "bp": "blood_pressure", "sg": "specific_gravity", "al": "albumin", "su": "sugar",
         "bgr": "blood_glucose_random", "bu": "blood_urea", "sc": "serum_creatinine", "sod": "sodium",
         "pot": "potassium", "hemo": "hemoglobin", "pcv": "packed_cell_volume"}
    X = k[list(m)].apply(pd.to_numeric, errors="coerce").rename(columns=m)
    y = (k["class"].astype(str).str.strip() == "ckd").astype(int)
    out["kidney"] = (X, y, "UCI Chronic Kidney Disease, 400 rows (12 of 24 attributes)")
    return out


def recode_for_shipped(d, X):
    """Map real-data coding to the coding the synthetic CSVs (and so the shipped models) use."""
    X = X.copy()
    if d == "heart":
        X["cp"] = X["cp"] - 1                       # Cleveland 1-4 -> 0-3
        X["slope"] = X["slope"] - 1                 # 1-3 -> 0-2
        X["thal"] = X["thal"].map({3: 0, 6: 1, 7: 2})  # arbitrary ordinal; thal carries no weight in the generator
    return X


def mets(y, pred, score):
    return {"accuracy": float(accuracy_score(y, pred)), "precision": float(precision_score(y, pred, zero_division=0)),
            "recall": float(recall_score(y, pred, zero_division=0)), "f1": float(f1_score(y, pred, zero_division=0)),
            "roc_auc": float(roc_auc_score(y, score))}


res = {}
for d, (X, y, desc) in load().items():
    print("==", d, desc, flush=True)
    R = {"source": desc, "rows": int(len(y)), "positive": int(y.sum()), "negative": int((1 - y).sum()),
         "missing_cells": int(X.isna().sum().sum()), "majority_rate": float(max(y.mean(), 1 - y.mean()))}
    rskf = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=SEED)
    cv = {}
    for name, b in BUILDERS.items():
        a, f, u = [], [], []
        for tr, te in rskf.split(X, y):
            pipe = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), b())
            pipe.fit(X.iloc[tr], y.iloc[tr])
            p = pipe.predict(X.iloc[te])
            a.append(accuracy_score(y.iloc[te], p))
            f.append(f1_score(y.iloc[te], p))
            u.append(roc_auc_score(y.iloc[te], pipe.predict_proba(X.iloc[te])[:, 1]))
        cv[name] = {"accuracy_mean": float(np.mean(a)), "accuracy_std": float(np.std(a)),
                    "f1_mean": float(np.mean(f)), "f1_std": float(np.std(f)),
                    "auc_mean": float(np.mean(u)), "auc_std": float(np.std(u))}
    R["real_cv"] = cv

    # (b) shipped synthetic-trained model on every real record
    model = joblib.load(os.path.join(ROOT, "models", f"{d}_model.pkl"))
    scaler = joblib.load(os.path.join(ROOT, "models", f"{d}_scaler.pkl"))
    feats = joblib.load(os.path.join(ROOT, "models", f"{d}_features.pkl"))
    Xr = recode_for_shipped(d, X)[feats]
    Xr = Xr.fillna(Xr.median())
    Z = scaler.transform(Xr.values)
    pred = model.predict(Z)
    R["shipped_on_real"] = mets(y.values, pred, model.predict_proba(Z)[:, 1])
    R["shipped_on_real"]["predicted_positive_rate"] = float(pred.mean())
    R["shipped_on_real"]["model"] = type(model).__name__
    res[d] = R
    print({n: round(v["accuracy_mean"], 3) for n, v in cv.items()}, "| shipped on real:",
          {k: round(v, 3) for k, v in R["shipped_on_real"].items() if k != "model"})

os.makedirs(os.path.join(ROOT, "docs", "experiments"), exist_ok=True)
json.dump(res, open(os.path.join(ROOT, "docs", "experiments", "real_data_results.json"), "w"), indent=1)
print("saved docs/experiments/real_data_results.json")
