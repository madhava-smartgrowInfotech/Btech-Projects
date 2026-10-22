"""Hybrid Company-Role recommendation (adapts paper Sec 3.8-3.12).
University -> Company, Program -> Role, QS rank -> Company Tier,
GPA proximity -> CGPA proximity, country/budget -> location/salary filters.
"""
import pickle, os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE, "models")

# Delta-max CGPA analogous to paper Eq: Δmax_GPA by QS rank
def delta_max_cgpa(tier):
    if tier == 1:
        return 0.6
    if tier == 2:
        return 1.0
    return 1.5


def load_artifacts():
    with open(os.path.join(MODEL_DIR, "preprocess.pkl"), "rb") as f:
        pre = pickle.load(f)
    with open(os.path.join(MODEL_DIR, "xgb_calibrated.pkl"), "rb") as f:
        xgb = pickle.load(f)
    with open(os.path.join(MODEL_DIR, "knn_residual.pkl"), "rb") as f:
        knn = pickle.load(f)
    with open(os.path.join(MODEL_DIR, "companies.pkl"), "rb") as f:
        comp = pickle.load(f)
    return pre, xgb, knn, comp


def _row_features(profile, company_row, role, pre):
    """Build single-row feature vector for (student, company, role)."""
    try:
        from src.preprocess import build_features
    except ImportError:
        from preprocess import build_features
    import pandas as pd
    df = pd.DataFrame([{
        "CGPA": profile["cgpa"], "Tenth_Percent": profile.get("tenth", 80),
        "Twelfth_Percent": profile.get("twelfth", 80),
        "Aptitude_Score": profile["aptitude"], "Technical_Score": profile["technical"],
        "Communication_Score": profile.get("communication", 70),
        "DSA_Score": profile.get("dsa", profile["technical"]),
        "Projects": profile.get("projects", 1), "Internships": profile.get("internships", 0),
        "Certifications": profile.get("certifications", 1),
        "Backlogs": profile.get("backlogs", 0), "Branch": profile.get("branch", "CSE"),
        "Degree_Type": profile.get("degree", "BTech"),
        "Student_Type": profile.get("stype", "Regular"),
        "Placement_Year": profile.get("year", 2026),
        "Target_Company": company_row["Company"], "Target_Role": role,
        "Target_Tier": company_row["Tier"],
    }])
    comp_df = pre_comp_cache()
    X, _, _, _ = build_features(df, comp_df, freq_maps=pre["freq_maps"],
                                scaler_stats=pre["scaler"])
    return X


_comp_cache = None
def pre_comp_cache():
    global _comp_cache
    if _comp_cache is None:
        import pandas as pd
        _comp_cache = pd.read_csv(os.path.join(BASE, "data", "companies.csv"))
    return _comp_cache


def predict_for(profile, company_row, role):
    pre, xgb, knn, comp = load_artifacts()
    X = _row_features(profile, company_row, role, pre)
    p = float(xgb.predict_proba(X)[0, 1])
    # residual refinement: if borderline, blend with kNN (paper Fig.8)
    if 0.4 <= p <= 0.6:
        pk = float(knn.predict_proba(X)[0, 1])
        p = 0.5 * p + 0.5 * pk
    return round(p, 4)


def recommend(profile, top_k=5, min_package=None, prefer_location=None):
    """Three strategies like paper Table 7: Role-only, Company-only, Hybrid."""
    pre, xgb, knn, comp = load_artifacts()
    base_company = profile.get("target_company")
    base_role = profile.get("target_role", "SDE")
    base_p = 0.0
    if base_company and base_company in comp["Company"].values:
        brow = comp[comp["Company"] == base_company].iloc[0]
        try:
            base_p = predict_for(profile, brow, base_role)
        except Exception:
            base_p = 0.0

    cands = []
    for _, row in comp.iterrows():
        # --- feasibility filters (paper Sec 3.11) ---
        gap = abs(profile["cgpa"] - row["CGPA_Cutoff"])
        if gap > delta_max_cgpa(row["Tier"]):
            continue
        if profile["aptitude"] < row["Apt_Cutoff"] - 15:
            continue
        if profile.get("backlogs", 0) > 2 and row["Tier"] == 1:
            continue
        if min_package and row["Package_LPA"] < min_package:
            continue
        prox = max(0.0, 1 - gap / delta_max_cgpa(row["Tier"]))  # GPA_Proximity Eq.
        roles = list(dict.fromkeys([base_role, "SDE", "Data Analyst", "QA Engineer"]))
        for role in roles:
            try:
                p = predict_for(profile, row, role)
            except Exception:
                continue
            loc_bonus = 0.02 if (prefer_location and row["Location"] == prefer_location) else 0.0
            score = p + 0.05 * prox + loc_bonus
            cands.append({"company": row["Company"], "role": role, "tier": int(row["Tier"]),
                          "package": float(row["Package_LPA"]), "location": row["Location"],
                          "prob": p, "score": round(score, 4), "proximity": round(prox, 3)})

    cands = sorted(cands, key=lambda x: x["score"], reverse=True)
    # Company-only: best role per company collapsed; Role-only: fixed company vary role
    seen, company_only = set(), []
    for c in cands:
        if c["company"] not in seen:
            seen.add(c["company"])
            company_only.append(c)
    role_only = [c for c in cands if (base_company is None or c["company"] == base_company)][:5]
    hybrid = cands[:top_k]
    improved = [c for c in hybrid if c["prob"] > base_p]
    avg_gain = round(float(np.mean([c["prob"] - base_p for c in improved])) if improved else 0.0, 4)
    return {"base_prob": base_p, "company_only": company_only[:top_k],
            "role_only": role_only, "hybrid": hybrid,
            "avg_gain": avg_gain, "match_rate": round(len(improved) / max(1, len(hybrid)), 3)}
