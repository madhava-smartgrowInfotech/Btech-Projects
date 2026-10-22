"""Preprocessing: frequency encoding + standardization + feature engineering.
Mirrors base paper Sec 2.5-2.6."""
import pandas as pd
import numpy as np
import os, pickle

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
MODEL_DIR = os.path.join(BASE, "models")

FREQ_COLS = ["Branch", "Target_Company", "Target_Role", "Degree_Type", "Student_Type"]
NUM_COLS = ["CGPA", "Tenth_Percent", "Twelfth_Percent", "Aptitude_Score",
            "Technical_Score", "Communication_Score", "DSA_Score",
            "Projects", "Internships", "Certifications", "Backlogs",
            "Placement_Year", "Target_Tier"]
EXTRA_NUM = ["Skill_Index", "Company_Hiring_Rate", "CGPA_x_Tier",
             "CGPA_Gap", "Apt_Gap", "Tech_Gap"]


def load_raw():
    df = pd.read_csv(os.path.join(DATA, "placement_dataset.csv"))
    comp = pd.read_csv(os.path.join(DATA, "companies.csv"))
    return df, comp


def build_features(df, comp, freq_maps=None, scaler_stats=None, fit=False):
    m = df.merge(comp, left_on="Target_Company", right_on="Company", how="left")
    out = df.copy()
    out["Skill_Index"] = (0.4 * out["Technical_Score"] + 0.3 * out["Aptitude_Score"]
                          + 0.15 * out["Communication_Score"] + 0.15 * out["DSA_Score"]) / 100.0
    out["Company_Hiring_Rate"] = m["Hiring_Rate"].astype(float).values
    out["CGPA_x_Tier"] = out["CGPA"] * out["Target_Tier"]  # interaction like Program x QS Rank
    out["CGPA_Gap"] = out["CGPA"] - m["CGPA_Cutoff"].astype(float).values
    out["Apt_Gap"] = out["Aptitude_Score"] - m["Apt_Cutoff"].astype(float).values
    out["Tech_Gap"] = out["Technical_Score"] - m["Tech_Cutoff"].astype(float).values

    if fit:
        freq_maps = {c: (out[c].value_counts(normalize=True).to_dict()) for c in FREQ_COLS}
        scaler_stats = {}
        for c in NUM_COLS + EXTRA_NUM:
            mu, sd = out[c].mean(), out[c].std() + 1e-9
            scaler_stats[c] = (mu, sd)

    for c in FREQ_COLS:
        mp = freq_maps[c]
        out[c + "_freq"] = out[c].map(mp).fillna(0.0)

    for c in NUM_COLS + EXTRA_NUM:
        mu, sd = scaler_stats[c]
        out[c + "_std"] = (out[c] - mu) / sd

    feat = [c + "_std" for c in NUM_COLS + EXTRA_NUM] + [c + "_freq" for c in FREQ_COLS]
    X = out[feat].values.astype(float)
    return X, feat, freq_maps, scaler_stats


def save_artifacts(freq_maps, scaler_stats, feat_names):
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(os.path.join(MODEL_DIR, "preprocess.pkl"), "wb") as f:
        pickle.dump({"freq_maps": freq_maps, "scaler": scaler_stats,
                     "features": feat_names, "num": NUM_COLS, "extra": EXTRA_NUM,
                     "freq_cols": FREQ_COLS}, f)


if __name__ == "__main__":
    df, comp = load_raw()
    X, feats, fm, sc = build_features(df, comp, fit=True)
    save_artifacts(fm, sc, feats)
    print("Features:", feats, "X:", X.shape)
