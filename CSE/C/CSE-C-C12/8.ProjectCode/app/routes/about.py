import json
from fastapi import APIRouter, HTTPException
from app.config import BASE_DIR, settings

router = APIRouter(prefix="/api/about", tags=["about"])

@router.get("/metrics")
def metrics():
    """Read-only: measured retrieval metrics from scripts/evaluate.py plus knowledge-base size."""
    path = BASE_DIR / "results" / "metrics.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Evaluation metrics not generated yet. Run scripts/evaluate.py.")
    data = json.loads(path.read_text(encoding="utf-8"))
    kb = BASE_DIR / "data" / "processed" / "knowledge_base.json"
    records = json.loads(kb.read_text(encoding="utf-8")) if kb.exists() else []
    data["kb_records"] = len(records)
    data["kb_conditions"] = len({r.get("disease") for r in records})
    data["data_source"] = settings.DATA_SOURCE_LABEL
    return data
