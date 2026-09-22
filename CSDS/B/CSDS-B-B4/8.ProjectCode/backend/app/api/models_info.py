"""Model performance: metrics and plots of every trained model (from experiments/)."""
from __future__ import annotations

import json
import re

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse

from app.core.config import EXPERIMENTS_DIR
from app.core.deps import api_error, get_current_user
from app.ml.registry import registry
from app.models import User

router = APIRouter(prefix="/models", tags=["model performance"])
FAMILIES = {
    "behaviour": "m1_behaviour",
    "sms": "m2_sms",
    "sms_comparison": "m2_sms_transformer",
    "risk": "m3_risk",
    "profile": "m0_upi2024",
}
SAFE = re.compile(r"^[a-z0-9_]+$")
SAFE_FILE = re.compile(r"^[a-z0-9_]+\.png$")


def _latest(prefix: str) -> dict | None:
    runs = sorted(p for p in EXPERIMENTS_DIR.glob(f"{prefix}_*/metrics.json") if re.fullmatch(rf"{prefix}_\d{{8}}", p.parent.name))
    if not runs:
        return None
    return json.loads(runs[-1].read_text(encoding="utf-8"))


@router.get("")
def models(_: User = Depends(get_current_user)) -> dict:
    out = {}
    for key, prefix in FAMILIES.items():
        m = _latest(prefix)
        if m:
            m["plot_urls"] = [f"/api/models/{m['run']}/plots/{p}" for p in m.get("plots", [])]
        out[key] = m
    return {"models": out, "loaded": registry.status(), "policy": registry.policy}


@router.get("/{run}/plots/{filename}", include_in_schema=False)
def plot(run: str, filename: str) -> FileResponse:
    if not SAFE.match(run) or not SAFE_FILE.match(filename):
        raise api_error(status.HTTP_404_NOT_FOUND, "plot_not_found", "Plot not found.")
    path = EXPERIMENTS_DIR / run / filename
    if not path.exists():
        raise api_error(status.HTTP_404_NOT_FOUND, "plot_not_found", "Plot not found.")
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})
