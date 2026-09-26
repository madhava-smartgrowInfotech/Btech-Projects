"""Load the tuned engine profile (models/engine_profile.json) and its benchmark run."""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from app.core.config import EXPERIMENTS_DIR, MODELS_DIR, get_settings
from app.services.engine import DEFAULT_HALL_BUDGET, ENGINE_VERSION

log = logging.getLogger("app.ml")
PROFILE_PATH = MODELS_DIR / "engine_profile.json"


@lru_cache
def engine_profile() -> dict:
    """The tuned settings, or safe defaults when the benchmark has not been run."""
    profile = {"engine_version": ENGINE_VERSION, "hall_budget": DEFAULT_HALL_BUDGET, "experiment": None,
               "source": "built-in defaults"}
    if PROFILE_PATH.exists():
        try:
            profile.update(json.loads(PROFILE_PATH.read_text(encoding="utf-8")))
            profile["source"] = str(PROFILE_PATH.relative_to(MODELS_DIR.parent))
        except (OSError, ValueError) as exc:
            log.warning("Could not read the engine profile; using defaults", extra={"error": str(exc)})
    return profile


def hall_budget() -> float:
    """Per-hall solver budget: .env override, else the tuned profile, else the built-in default."""
    override = get_settings().solver_hall_budget
    return float(override) if override else float(engine_profile().get("hall_budget") or DEFAULT_HALL_BUDGET)


def experiment_dir() -> Path | None:
    name = engine_profile().get("experiment")
    if not name:
        return None
    path = (EXPERIMENTS_DIR / name).resolve()
    return path if path.is_dir() and path.parent == EXPERIMENTS_DIR.resolve() else None


@lru_cache
def benchmark_metrics() -> dict | None:
    folder = experiment_dir()
    if folder is None or not (folder / "metrics.json").exists():
        return None
    return json.loads((folder / "metrics.json").read_text(encoding="utf-8"))
