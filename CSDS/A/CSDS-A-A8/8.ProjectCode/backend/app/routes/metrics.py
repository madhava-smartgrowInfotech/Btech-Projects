import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..auth import current_user
from ..config import EXPERIMENTS
from ..db import User

router = APIRouter(prefix="/api/metrics", tags=["metrics"])
PLOTS = {"mri_label_efficiency.png", "mri_pretrain_loss.png"}


def _load(name):
    p = EXPERIMENTS / name
    return json.loads(p.read_text()) if p.exists() else None


@router.get("/label-efficiency")
def label_efficiency(user: User = Depends(current_user)):
    m = _load("mri_metrics.json")
    if not m:
        raise HTTPException(404, "No MRI metrics yet - run ml/train_mri.py")
    return {"data": m.get("data"), "finetune": m.get("finetune", {}), "pretrain": m.get("pretrain", {})}


@router.get("/all")
def all_metrics(user: User = Depends(current_user)):
    return {"mri": _load("mri_metrics.json"), "dna": _load("dna_metrics.json"), "eval": _load("eval/metrics.json")}


@router.get("/plot/{name}")
def plot(name: str):
    if name not in PLOTS or not (EXPERIMENTS / name).exists():
        raise HTTPException(404, "Plot not found")
    return FileResponse(EXPERIMENTS / name, media_type="image/png")
