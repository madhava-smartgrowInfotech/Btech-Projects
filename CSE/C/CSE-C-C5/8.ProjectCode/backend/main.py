"""Thin FastAPI layer over the existing Smart Campus Placement System code.

It imports the original `src.recommend` functions (predict_for / recommend / pre_comp_cache) and reads the same
data/, models/ and static/ files the Flask app (app.py) uses. No model logic is rewritten here.
Run: uvicorn backend.main:app --port 8405
"""
import json
import os
import sys

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from src.recommend import predict_for, pre_comp_cache, recommend  # noqa: E402


def _env(name, default):
    """Read a value from the process env, falling back to the project .env file."""
    if os.environ.get(name):
        return os.environ[name]
    try:
        with open(os.path.join(BASE, ".env"), encoding="utf-8") as f:
            for line in f:
                k, _, v = line.strip().partition("=")
                if k == name and v:
                    return v
    except OSError:
        pass
    return default


FRONTEND_PORT = _env("FRONTEND_PORT", "5405")

BRANCHES = ["CSE", "IT", "ECE", "EEE", "MECH", "CIVIL"]
DEGREES = ["BTech", "MTech"]
PREDICT_ROLES = ["SDE", "Data Analyst", "ML Engineer", "QA Engineer", "DevOps", "Support Engineer"]
RECOMMEND_ROLES = ["SDE", "Data Analyst", "ML Engineer", "QA Engineer"]
LOCATIONS = ["Hyderabad", "Bangalore", "Chennai", "Pune", "Mumbai", "Noida"]
PLOTS = {"prob_hist": "prob_hist.png", "pca": "pca.png", "shap": "shap.png"}

app = FastAPI(title="Smart Campus Placement System API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{FRONTEND_PORT}", f"http://127.0.0.1:{FRONTEND_PORT}"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- request models (defaults mirror the Flask forms) ----------
class Profile(BaseModel):
    cgpa: float = Field(8.0, ge=0, le=10)
    tenth: float = Field(85, ge=0, le=100)
    twelfth: float = Field(85, ge=0, le=100)
    aptitude: float = Field(70, ge=0, le=100)
    technical: float = Field(70, ge=0, le=100)
    communication: float = Field(70, ge=0, le=100)
    dsa: float = Field(70, ge=0, le=100)
    projects: int = Field(1, ge=0, le=20)
    internships: int = Field(0, ge=0, le=20)
    certifications: int = Field(1, ge=0, le=20)
    backlogs: int = Field(0, ge=0, le=20)
    branch: str = "CSE"
    degree: str = "BTech"


class PredictIn(Profile):
    target_company: str
    target_role: str = "SDE"


class RecommendIn(BaseModel):
    cgpa: float = Field(7.5, ge=0, le=10)
    aptitude: float = Field(65, ge=0, le=100)
    technical: float = Field(65, ge=0, le=100)
    communication: float = Field(65, ge=0, le=100)
    dsa: float = Field(65, ge=0, le=100)
    projects: int = Field(1, ge=0, le=20)
    internships: int = Field(0, ge=0, le=20)
    certifications: int = Field(1, ge=0, le=20)
    backlogs: int = Field(0, ge=0, le=20)
    branch: str = "CSE"
    target_company: str | None = None
    target_role: str = "SDE"
    location: str | None = None


class ShortlistIn(BaseModel):
    min_cgpa: float = Field(7.0, ge=0, le=10)
    min_apt: float = Field(60, ge=0, le=100)
    branch: str = "ALL"


# ---------- helpers ----------
def _companies() -> pd.DataFrame:
    return pre_comp_cache()


def _company_row(name: str):
    comps = _companies()
    hit = comps[comps["Company"] == name]
    if hit.empty:
        raise HTTPException(404, f"Unknown company '{name}'")
    return hit.iloc[0]


def _records(df: pd.DataFrame):
    return json.loads(df.to_json(orient="records"))


def _dataset() -> pd.DataFrame:
    try:
        return pd.read_csv(os.path.join(BASE, "data", "placement_dataset.csv"))
    except OSError:
        raise HTTPException(503, "data/placement_dataset.csv is missing - run python src/generate_dataset.py")


def _tips(profile: dict, row) -> list[str]:
    """Same skill-gap rules as app.py's /predict route."""
    tips = []
    if profile["cgpa"] < float(row["CGPA_Cutoff"]):
        tips.append(f"CGPA {profile['cgpa']} below {row['Company']} cutoff {row['CGPA_Cutoff']} - target Tier-2/3 companies.")
    if profile["aptitude"] < float(row["Apt_Cutoff"]):
        tips.append("Improve aptitude (target 75+) via weekly mock tests.")
    if profile["technical"] < float(row["Tech_Cutoff"]):
        tips.append("Strengthen DSA + core subjects; build 2+ projects.")
    if profile["internships"] == 0:
        tips.append("Get at least 1 internship - strongly boosts probability.")
    if not tips:
        tips.append("Strong profile - apply and prepare for interviews.")
    return tips


# ---------- endpoints ----------
@app.get("/api/health")
def health():
    models = os.path.join(BASE, "models")
    ready = all(os.path.exists(os.path.join(models, f)) for f in ("preprocess.pkl", "xgb_calibrated.pkl", "knn_residual.pkl", "companies.pkl"))
    return {"status": "ok", "models_ready": ready}


@app.get("/api/meta")
def meta():
    return {"branches": BRANCHES, "degrees": DEGREES, "predict_roles": PREDICT_ROLES,
            "recommend_roles": RECOMMEND_ROLES, "locations": LOCATIONS,
            "companies": _companies()["Company"].tolist()}


@app.get("/api/companies")
def companies():
    return _records(_companies())


@app.get("/api/metrics")
def metrics():
    try:
        with open(os.path.join(BASE, "models", "metrics.json"), encoding="utf-8") as f:
            return json.load(f)
    except OSError:
        raise HTTPException(503, "models/metrics.json is missing - run python src/hybrid_model.py")


@app.get("/api/stats")
def stats():
    df = _dataset()
    return {"total": int(len(df)), "placed_rate": round(float(df["Placed"].mean()), 3),
            "avg_cgpa": round(float(df["CGPA"].mean()), 2),
            "by_branch": df.groupby("Branch")["Placed"].mean().round(3).to_dict()}


@app.get("/api/plots/{name}")
def plot(name: str):
    if name not in PLOTS:
        raise HTTPException(404, "Unknown plot")
    path = os.path.join(BASE, "static", PLOTS[name])
    if not os.path.exists(path):
        raise HTTPException(404, "Plot image not generated - run python src/hybrid_model.py")
    return FileResponse(path, media_type="image/png")


@app.post("/api/predict")
def predict(body: PredictIn):
    row = _company_row(body.target_company)
    profile = body.model_dump(exclude={"target_company", "target_role"})
    profile.update(stype="Regular", year=2026)
    try:
        p = predict_for(profile, row, body.target_role)
    except Exception as e:  # the model code raises plain exceptions for unseen values
        raise HTTPException(422, f"Prediction failed: {e}")
    return {"placement_probability": p, "eligible": bool(p >= 0.5),
            "label": "PLACEMENT READY" if p >= 0.5 else "NEEDS IMPROVEMENT",
            "company": row["Company"], "role": body.target_role,
            "company_detail": json.loads(row.to_json()), "tips": _tips(profile, row)}


@app.post("/api/recommend")
def recommend_endpoint(body: RecommendIn):
    if body.target_company and body.target_company not in _companies()["Company"].values:
        raise HTTPException(404, f"Unknown company '{body.target_company}'")
    profile = body.model_dump(exclude={"location"})
    try:
        return recommend(profile, top_k=5, prefer_location=body.location or None)
    except Exception as e:
        raise HTTPException(422, f"Recommendation failed: {e}")


@app.post("/api/recruiter/shortlist")
def shortlist(body: ShortlistIn):
    df = _dataset()
    q = df[(df["CGPA"] >= body.min_cgpa) & (df["Aptitude_Score"] >= body.min_apt)]
    if body.branch != "ALL":
        q = q[q["Branch"] == body.branch]
    top = q.sort_values(["CGPA", "Technical_Score"], ascending=False).head(50)
    return {"total_matches": int(len(q)), "students": _records(top)}
