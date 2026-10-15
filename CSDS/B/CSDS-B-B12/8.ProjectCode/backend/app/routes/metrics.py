import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..auth import current_user
from ..config import EXPERIMENTS_DIR

router = APIRouter(prefix="/api/metrics", tags=["metrics"])
EVAL = EXPERIMENTS_DIR / "eval"


@router.get("")
def metrics(user=Depends(current_user)):
    path = EVAL / "metrics.json"
    if not path.exists():
        raise HTTPException(404, "No evaluation yet - run python ml/eval.py")
    out = json.loads(path.read_text())
    out["training"] = {}
    for name in ("xray", "ct", "unet"):
        f = EXPERIMENTS_DIR / f"{name}_training.json"
        if f.exists():
            out["training"][name] = json.loads(f.read_text())
    return out


@router.get("/figure/{name}")
def figure(name: str, user=Depends(current_user)):
    path = EVAL / name
    if not name.endswith(".png") or "/" in name or "\\" in name or not path.exists():
        raise HTTPException(404, "Figure not found")
    return FileResponse(path, media_type="image/png")
