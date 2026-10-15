"""Read-only numbers for the public landing page (measured results of the shipped model)."""
import json

from fastapi import APIRouter

from ..config import EXPERIMENTS_DIR

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/stats")
def stats():
    path = EXPERIMENTS_DIR / "eval" / "metrics.json"
    if not path.exists():
        return {"available": False}
    m = json.loads(path.read_text(encoding="utf-8"))
    hitl = m.get("human_in_the_loop") or {}
    return {
        "available": True,
        "model_version": m.get("model_version"),
        "evaluated_at": m.get("evaluated_at"),
        "category": {"accuracy": m["category"]["test"]["accuracy"], "n": m["category"]["test"]["n"],
                     "by_language": m["category"]["by_language"]},
        "department": {"accuracy": m["department"]["test"]["accuracy"],
                       "top3": m["department"].get("top3_accuracy")},
        "priority": {"accuracy": m["priority"]["test"]["accuracy"]},
        "resolution": {"median_abs_error_days": m["resolution"]["median_abs_error_days"],
                       "rows_test": m["resolution"]["rows_test"]},
        "explanations": {"lime_drop": m["explanations"]["lime_faithfulness"]["mean_confidence_drop_removing_top3_lime_words"],
                         "random_drop": m["explanations"]["lime_faithfulness"]["mean_confidence_drop_removing_3_random_words"]},
        "latency_ms": m.get("latency", {}).get("with_explanations_ms_median"),
        "agreement_after_feedback": (hitl.get("after") or {}).get("agreement_on_corrected"),
    }
