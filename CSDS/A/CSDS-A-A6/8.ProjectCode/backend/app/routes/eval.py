import json

from fastapi import APIRouter

from ..config import EXPERIMENTS_DIR

router = APIRouter(prefix="/api/eval", tags=["eval"])

METRICS_PATH = EXPERIMENTS_DIR / "metrics.json"


@router.get("/metrics")
def get_metrics():
    if not METRICS_PATH.exists():
        return {
            "available": False,
            "message": "No evaluation results yet. Run `python ml/eval.py` from the backend venv.",
        }
    with open(METRICS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    data["available"] = True
    return data
