"""VenturePulse FastAPI application."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator

from app.config import APP_NAME, DEFAULT_K, MAX_DESC_LEN, RETRIEVAL_KS
from app.services.store import ensure_artifacts
from app.services.predictor import predict_one
from app.services.insights import compute_insights

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(APP_NAME)

app = FastAPI(title=APP_NAME)
BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

from app.api_extra import router as extra_router  # additive JSON endpoints for the React frontend
app.include_router(extra_router)

STATES = ["CA", "NY", "MA", "TX", "WA", "IL", "CO", "FL", "PA", "OR", "Other"]
INDUSTRIES = ["Software", "E-Commerce", "FinTech", "HealthTech", "EdTech",
              "CleanTech", "Media", "Mobile", "AI", "Biotech", "Other"]


class PredictPayload(BaseModel):
    funding_total_usd: float = Field(default=1000000, ge=0, le=1e10)
    funding_rounds: float = Field(default=2, ge=0, le=20)
    age_first_funding_year: float = Field(default=1.5, ge=0, le=30)
    age_last_funding_year: float = Field(default=2.5, ge=0, le=30)
    age_first_milestone_year: float = Field(default=1.0, ge=0, le=30)
    age_last_milestone_year: float = Field(default=2.0, ge=0, le=30)
    relationships: float = Field(default=4, ge=0, le=200)
    milestones: float = Field(default=2, ge=0, le=50)
    avg_participants: float = Field(default=3.0, ge=0, le=50)
    has_VC: bool = False
    has_angel: bool = False
    has_roundA: bool = False
    has_roundB: bool = False
    has_roundC: bool = False
    has_roundD: bool = False
    is_top500: bool = False
    state: str = "CA"
    industry_type: str = "Software"
    description: str = ""
    k: int = DEFAULT_K

    @field_validator("description")
    @classmethod
    def check_desc(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) > MAX_DESC_LEN:
            raise ValueError(f"Description must be under {MAX_DESC_LEN} characters.")
        return v

    @field_validator("k")
    @classmethod
    def check_k(cls, v: int) -> int:
        if v not in RETRIEVAL_KS:
            raise ValueError(f"k must be one of {RETRIEVAL_KS}.")
        return v


def _ctx(state: dict) -> dict:
    meta = state["metadata"]
    res = state["results"]
    df = state["train_df"]
    ins = compute_insights(df)
    best = meta["best_model"]
    bm = res["models"][best]
    return {"meta": meta, "results": res, "insights": ins, "best_metrics": bm, "best": best}


@app.get("/api/health")
def health():
    try:
        st = ensure_artifacts()
        return {"status": "ok", "app": APP_NAME, "records": st["metadata"]["n_train"],
                "best_model": st["metadata"]["best_model"]}
    except Exception as e:
        log.exception("health failed")
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


@app.get("/api/model-metrics")
def model_metrics():
    try:
        st = ensure_artifacts()
        return st["results"]
    except Exception as e:
        log.exception("metrics failed")
        return JSONResponse({"detail": str(e)}, status_code=500)


@app.get("/api/insights")
def insights():
    try:
        st = ensure_artifacts()
        return compute_insights(st["train_df"])
    except Exception as e:
        log.exception("insights failed")
        return JSONResponse({"detail": str(e)}, status_code=500)


@app.post("/predict")
async def predict_api(payload: PredictPayload):
    try:
        st = ensure_artifacts()
        out = predict_one(payload.model_dump(), st, k=payload.k)
        return out
    except Exception as e:
        log.exception("prediction failed")
        return JSONResponse({"detail": str(e)}, status_code=500)


@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    st = ensure_artifacts()
    return templates.TemplateResponse(request, "dashboard.html", {"app_name": APP_NAME, **_ctx(st)})


@app.get("/predict", response_class=HTMLResponse)
def predict_form(request: Request):
    st = ensure_artifacts()
    return templates.TemplateResponse(request, "predict.html", {"app_name": APP_NAME,
                                                       "states": STATES, "industries": INDUSTRIES,
                                                       "ks": RETRIEVAL_KS, "default_k": DEFAULT_K})


@app.post("/predict-form", response_class=HTMLResponse)
async def predict_form_post(
    request: Request,
    funding_total_usd: float = Form(default=1000000),
    funding_rounds: float = Form(default=2),
    age_first_funding_year: float = Form(default=1.5),
    age_last_funding_year: float = Form(default=2.5),
    age_first_milestone_year: float = Form(default=1.0),
    age_last_milestone_year: float = Form(default=2.0),
    relationships: float = Form(default=4),
    milestones: float = Form(default=2),
    avg_participants: float = Form(default=3.0),
    state: str = Form(default="CA"),
    industry_type: str = Form(default="Software"),
    description: str = Form(default=""),
    k: int = Form(default=DEFAULT_K),
    has_VC: bool = Form(default=False),
    has_angel: bool = Form(default=False),
    has_roundA: bool = Form(default=False),
    has_roundB: bool = Form(default=False),
    has_roundC: bool = Form(default=False),
    has_roundD: bool = Form(default=False),
    is_top500: bool = Form(default=False),
):
    st = ensure_artifacts()
    description = (description or "").strip()
    if not description:
        return templates.TemplateResponse(request, "predict.html", {"app_name": APP_NAME,
            "states": STATES, "industries": INDUSTRIES, "ks": RETRIEVAL_KS,
            "default_k": DEFAULT_K, "error": "Please enter a startup description (a few sentences)."},
            status_code=400)
    if len(description) > MAX_DESC_LEN:
        return templates.TemplateResponse(request, "predict.html", {"app_name": APP_NAME,
            "states": STATES, "industries": INDUSTRIES, "ks": RETRIEVAL_KS,
            "default_k": DEFAULT_K, "error": f"Description must be under {MAX_DESC_LEN} characters."},
            status_code=400)
    if k not in RETRIEVAL_KS:
        k = DEFAULT_K
    payload = {"funding_total_usd": max(0, funding_total_usd), "funding_rounds": max(0, funding_rounds),
               "age_first_funding_year": max(0, age_first_funding_year),
               "age_last_funding_year": max(0, age_last_funding_year),
               "age_first_milestone_year": max(0, age_first_milestone_year),
               "age_last_milestone_year": max(0, age_last_milestone_year),
               "relationships": max(0, relationships), "milestones": max(0, milestones),
               "avg_participants": max(0, avg_participants), "state": state or "Other",
               "industry_type": industry_type or "Software", "description": description,
               "has_VC": bool(has_VC), "has_angel": bool(has_angel), "has_roundA": bool(has_roundA),
               "has_roundB": bool(has_roundB), "has_roundC": bool(has_roundC),
               "has_roundD": bool(has_roundD), "is_top500": bool(is_top500)}
    try:
        out = predict_one(payload, st, k=k)
    except Exception:
        log.exception("form prediction failed")
        return templates.TemplateResponse(request, "predict.html", {"app_name": APP_NAME,
            "states": STATES, "industries": INDUSTRIES, "ks": RETRIEVAL_KS,
            "default_k": DEFAULT_K, "error": "Prediction failed due to invalid input. Please check values."},
            status_code=400)
    return templates.TemplateResponse(request, "result.html", {"app_name": APP_NAME,
                                                      "result": out, "inputs": payload})


@app.get("/performance", response_class=HTMLResponse)
def performance(request: Request):
    st = ensure_artifacts()
    return templates.TemplateResponse(request, "performance.html", {"app_name": APP_NAME, **_ctx(st)})


@app.get("/insights", response_class=HTMLResponse)
def insights_page(request: Request):
    st = ensure_artifacts()
    return templates.TemplateResponse(request, "insights.html", {"app_name": APP_NAME, **_ctx(st)})
