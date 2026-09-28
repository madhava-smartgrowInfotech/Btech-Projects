import json
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..config import ROOT
from ..db import PipelineRun, User, get_db
from ..services.state import store

router = APIRouter(prefix="/api", tags=["pipeline"])


def state():
    s = store.get()
    if s is None:
        raise HTTPException(503, "The pipeline is still loading - try again in a few seconds")
    return s


class RunIn(BaseModel):
    seed: int = Field(42, ge=0, le=10_000_000)
    taxpayers: int = Field(600, ge=150, le=1500)


@router.post("/pipeline/run")
def run(body: RunIn, user: User = Depends(current_user)):
    try:
        run_id = store.start_run(body.seed, body.taxpayers, user.id)
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    return {"run_id": run_id, "status": store.status}


@router.get("/pipeline/status")
def status(user: User = Depends(current_user)):
    s = store.get()
    return {**store.status, "current": None if s is None else {
        "run_key": s["run_key"], "seed": s["meta"]["seed"], "taxpayers": s["stats"]["taxpayers"],
        "dataset": s["dataset"], "generated_at": s["generated_at"]}}


@router.get("/pipeline/runs")
def runs(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(select(PipelineRun).order_by(PipelineRun.id.desc()).limit(10)).all()
    return [{"id": r.id, "seed": r.seed, "taxpayers": r.n_taxpayers, "status": r.status, "message": r.message,
             "started_at": r.started_at, "finished_at": r.finished_at,
             "flagged": (r.stats or {}).get("flagged")} for r in rows]


@router.get("/overview")
def overview(user: User = Depends(current_user)):
    s = state()
    tps = s["taxpayers"]
    top = sorted(tps, key=lambda t: t["rank"])[:8]
    hist = [0] * 10
    for t in tps:
        hist[min(9, int(t["risk"] * 10))] += 1
    ev = s["evaluation"]["taxpayer"]
    k = str(s["evaluation"]["n_fraud"])
    return {
        "stats": s["stats"], "seed": s["meta"]["seed"], "run_key": s["run_key"], "generated_at": s["generated_at"],
        "dataset": s["dataset"], "risk_histogram": hist, "pattern_labels": s["config"]["pattern_labels"],
        "top_taxpayers": [_brief(t) for t in top],
        "top_chains": [_chain_brief(s, c) for c in s["chains"][:5]],
        "headline": {"k": k, "model_precision_at_k": ev["model"]["precision_at_k"][k],
                     "baseline_precision_at_k": ev["rule_baseline"]["precision_at_k"][k],
                     "model_f1": ev["model"]["at_threshold"]["f1"],
                     "baseline_f1": ev["rule_baseline"]["at_threshold"]["f1"]},
    }


def _brief(t):
    return {k: t[k] for k in ("gstin", "legal_name", "sector", "state", "risk", "rank", "flagged", "patterns",
                              "jepa", "behaviour", "network", "invoice", "itc_at_risk")}


def _chain_brief(s, c):
    tps = s["taxpayers"]
    return {k: c.get(k) for k in ("id", "type", "ring", "cluster", "value", "itc", "months", "score", "rank",
                                  "summary")} | {
        "n_invoices": len(c["invoice_ids"]), "n_parties": len(c["nodes"]),
        "path": [{"gstin": tps[v]["gstin"], "legal_name": tps[v]["legal_name"]} for v in c["path"]]}


def _read_json(*parts):
    p = os.path.join(ROOT, *parts)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


@router.get("/metrics")
def metrics(user: User = Depends(current_user)):
    s = state()
    return {"current": {"run_key": s["run_key"], "seed": s["meta"]["seed"], "evaluation": s["evaluation"],
                        "train_info": s["train_info"]},
            "config": s["config"], "training": _read_json("experiments", "metrics.json"),
            "eval_report": _read_json("experiments", "eval", "metrics.json")}
