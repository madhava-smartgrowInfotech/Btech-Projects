import json

from fastapi import APIRouter, HTTPException

from ..config import ROOT

router = APIRouter(prefix="/api", tags=["evaluation"])

METRICS_PATH = ROOT / "experiments" / "eval" / "metrics.json"


@router.get("/evaluation")
def evaluation():
    """Read-only: the measured results written by ml/eval.py (public, used by the landing page)."""
    if not METRICS_PATH.exists():
        raise HTTPException(404, "No evaluation results yet. Run ml/eval.py first.")
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
