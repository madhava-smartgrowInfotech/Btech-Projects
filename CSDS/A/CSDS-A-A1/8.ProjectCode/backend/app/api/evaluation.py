"""Model performance: evaluation runs written by ``ml/run_all.py`` under experiments/."""

from __future__ import annotations

import json
import re
from typing import Any

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.core.errors import NotFound

router = APIRouter(prefix="/evaluation", tags=["model performance"])
_SAFE_RUN = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
_SAFE_FILE = re.compile(r"^[A-Za-z0-9_.-]{1,120}\.png$")


def _run_payload(run: str) -> dict[str, Any]:
    folder = get_settings().experiments_dir / run
    metrics_file = folder / "metrics.json"
    if not metrics_file.exists():
        raise NotFound("Evaluation run not found.")
    metrics = json.loads(metrics_file.read_text(encoding="utf-8"))
    plots = sorted(p.name for p in (folder / "plots").glob("*.png")) if (folder / "plots").exists() else []
    return {"run": run, "metrics": metrics, "plots": plots}


@router.get("/latest")
def latest() -> dict[str, Any]:
    pointer = get_settings().experiments_dir / "latest.json"
    if not pointer.exists():
        raise NotFound("No evaluation has been run yet. Run ml/run_all.py to create one.", code="no_evaluation")
    run = json.loads(pointer.read_text(encoding="utf-8"))["run"]
    return _run_payload(run)


@router.get("/runs")
def runs() -> list[dict[str, Any]]:
    root = get_settings().experiments_dir
    out = []
    for folder in sorted(root.glob("*/metrics.json"), reverse=True) if root.exists() else []:
        try:
            metrics = json.loads(folder.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        out.append({"run": folder.parent.name, "updated_at": metrics.get("updated_at"),
                    "headline": metrics.get("headline", {})})
    return out


@router.get("/runs/{run}")
def run_detail(run: str) -> dict[str, Any]:
    if not _SAFE_RUN.match(run):
        raise NotFound("Evaluation run not found.")
    return _run_payload(run)


@router.get("/runs/{run}/plots/{filename}")
def plot(run: str, filename: str) -> FileResponse:
    if not _SAFE_RUN.match(run) or not _SAFE_FILE.match(filename):
        raise NotFound("Plot not found.")
    path = get_settings().experiments_dir / run / "plots" / filename
    if not path.exists():
        raise NotFound("Plot not found.")
    return FileResponse(path, media_type="image/png")
