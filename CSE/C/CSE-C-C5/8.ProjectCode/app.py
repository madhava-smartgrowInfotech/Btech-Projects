"""Smart Campus Placement System — Flask app.
Hybrid XGBoost+kNN placement prediction + hybrid Company-Role recommendation.
Run: python app.py  (then open http://127.0.0.1:5000)
"""
import os, json, pickle
import pandas as pd
from flask import Flask, render_template, request, jsonify

from src.recommend import predict_for, recommend, load_artifacts, pre_comp_cache

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)


def get_companies():
    return pre_comp_cache()


@app.route("/")
def index():
    try:
        with open(os.path.join(BASE, "models", "metrics.json")) as f:
            m = json.load(f)
    except Exception:
        m = {"results": {}, "note": "Run: python src/generate_dataset.py; python src/preprocess.py; python src/hybrid_model.py"}
    comps = get_companies().to_dict("records") if os.path.exists(os.path.join(BASE, "data", "companies.csv")) else []
    return render_template("index.html", metrics=m, companies=comps)


@app.route("/predict", methods=["GET", "POST"])
def predict():
    comps = get_companies()
    result = None
    if request.method == "POST":
        f = request.form
        profile = {
            "cgpa": float(f.get("cgpa", 8.0)), "tenth": float(f.get("tenth", 85)),
            "twelfth": float(f.get("twelfth", 85)),
            "aptitude": float(f.get("aptitude", 70)),
            "technical": float(f.get("technical", 70)),
            "communication": float(f.get("communication", 70)),
            "dsa": float(f.get("dsa", 70)),
            "projects": int(f.get("projects", 1)),
            "internships": int(f.get("internships", 0)),
            "certifications": int(f.get("certifications", 1)),
            "backlogs": int(f.get("backlogs", 0)),
            "branch": f.get("branch", "CSE"), "degree": f.get("degree", "BTech"),
            "stype": "Regular", "year": 2026,
        }
        cname = f.get("target_company", comps.iloc[0]["Company"])
        role = f.get("target_role", "SDE")
        row = comps[comps["Company"] == cname].iloc[0]
        p = predict_for(profile, row, role)
        label = "PLACEMENT READY ✅" if p >= 0.5 else "NEEDS IMPROVEMENT ⚠️"
        tips = []
        if profile["cgpa"] < float(row["CGPA_Cutoff"]):
            tips.append(f"CGPA {profile['cgpa']} below {cname} cutoff {row['CGPA_Cutoff']} — target Tier-2/3 companies.")
        if profile["aptitude"] < float(row["Apt_Cutoff"]):
            tips.append("Improve aptitude (target 75+) via weekly mock tests.")
        if profile["technical"] < float(row["Tech_Cutoff"]):
            tips.append("Strengthen DSA + core subjects; build 2+ projects.")
        if profile["internships"] == 0:
            tips.append("Get at least 1 internship — strongly boosts probability.")
        if not tips:
            tips.append("Strong profile — apply and prepare for interviews.")
        result = {"prob": p, "label": label, "company": cname, "role": role,
                  "profile": profile, "tips": tips}
    return render_template("predict.html", companies=comps.to_dict("records"),
                           roles=["SDE", "Data Analyst", "ML Engineer", "QA Engineer",
                                  "DevOps", "Support Engineer"], result=result)


@app.route("/recommend", methods=["GET", "POST"])
def recommend_page():
    comps = get_companies()
    out = None
    if request.method == "POST":
        f = request.form
        profile = {
            "cgpa": float(f.get("cgpa", 7.5)), "aptitude": float(f.get("aptitude", 65)),
            "technical": float(f.get("technical", 65)),
            "communication": float(f.get("communication", 65)),
            "dsa": float(f.get("dsa", 65)),
            "projects": int(f.get("projects", 1)), "internships": int(f.get("internships", 0)),
            "certifications": int(f.get("certifications", 1)),
            "backlogs": int(f.get("backlogs", 0)), "branch": f.get("branch", "CSE"),
            "target_company": f.get("target_company"), "target_role": f.get("target_role", "SDE"),
        }
        out = recommend(profile, top_k=5,
                        prefer_location=f.get("location") or None)
    return render_template("recommend.html", companies=comps.to_dict("records"), out=out)


@app.route("/dashboard")
def dashboard():
    try:
        with open(os.path.join(BASE, "models", "metrics.json")) as f:
            m = json.load(f)
    except Exception:
        m = {"results": {}}
    # placement stats from dataset
    try:
        df = pd.read_csv(os.path.join(BASE, "data", "placement_dataset.csv"))
        stats = {"total": len(df), "placed_rate": round(df["Placed"].mean(), 3),
                 "avg_cgpa": round(df["CGPA"].mean(), 2),
                 "by_branch": df.groupby("Branch")["Placed"].mean().round(3).to_dict()}
    except Exception:
        stats = {}
    return render_template("dashboard.html", metrics=m, stats=stats)


@app.route("/recruiter", methods=["GET", "POST"])
def recruiter():
    out = None
    try:
        df = pd.read_csv(os.path.join(BASE, "data", "placement_dataset.csv"))
    except Exception:
        df = pd.DataFrame()
    if request.method == "POST" and len(df):
        cg = float(request.form.get("min_cgpa", 7.0))
        skill = float(request.form.get("min_apt", 60))
        branch = request.form.get("branch", "ALL")
        q = df[(df["CGPA"] >= cg) & (df["Aptitude_Score"] >= skill)]
        if branch != "ALL":
            q = q[q["Branch"] == branch]
        out = q.sort_values(["CGPA", "Technical_Score"], ascending=False).head(50).to_dict("records")
    return render_template("recruiter.html", out=out)


@app.route("/api/predict", methods=["POST"])
def api_predict():
    d = request.get_json(force=True)
    comps = get_companies()
    row = comps[comps["Company"] == d["target_company"]].iloc[0]
    p = predict_for(d, row, d.get("target_role", "SDE"))
    return jsonify({"placement_probability": p, "eligible": bool(p >= 0.5)})


if __name__ == "__main__":
    app.run(debug=True)
