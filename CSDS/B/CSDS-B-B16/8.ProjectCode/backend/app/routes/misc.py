import csv
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..auth import current_user
from ..config import EXPERIMENTS_DIR, SAMPLE_DIR
from ..db import User

router = APIRouter(prefix="/api", tags=["misc"])

FUNDUS_SAMPLES = SAMPLE_DIR / "fundus"


@router.get("/health")
def health():
    from ..config import MODELS_DIR
    return {"status": "ok", "retina_model": (MODELS_DIR / "lenet_hr.pt").exists(),
            "heart_model": (MODELS_DIR / "heart_rf.joblib").exists()}


@router.get("/samples")
def samples(_: User = Depends(current_user)):
    """Labelled sample fundus images from the held-out test split (sample data, for demonstration)."""
    labels = FUNDUS_SAMPLES / "labels.csv"
    if not labels.exists():
        return []
    with labels.open() as f:
        return [{"name": r["image"], "label": int(r["hypertensive_retinopathy"]), "url": f"/api/samples/{r['image']}"}
                for r in csv.DictReader(f)]


@router.get("/samples/{name}")
def sample_file(name: str):
    path = (FUNDUS_SAMPLES / name).resolve()
    if path.parent != FUNDUS_SAMPLES.resolve() or not path.exists() or path.suffix.lower() not in (".png", ".jpg", ".jpeg"):
        raise HTTPException(404, "Sample not found")
    return FileResponse(path)


@router.get("/metrics")
def metrics(_: User = Depends(current_user)):
    ev = EXPERIMENTS_DIR / "eval" / "metrics.json"
    if ev.exists():
        return json.loads(ev.read_text())
    out = {}
    for key in ("retina", "heart"):
        p = EXPERIMENTS_DIR / key / "metrics.json"
        if p.exists():
            out[key] = json.loads(p.read_text())
    if not out:
        raise HTTPException(404, "No evaluation results yet. Run: python ml/eval.py")
    return out
