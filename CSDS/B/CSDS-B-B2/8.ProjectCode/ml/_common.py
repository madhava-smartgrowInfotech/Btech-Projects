"""Shared helpers for the training scripts: paths, run folders, logging, seeding."""
from __future__ import annotations

import json
import logging
import random
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
FIELD = DATA / "field"
EXPERIMENTS = ROOT / "experiments"
MODELS = ROOT / "models"

# The feature and label code lives in the backend package so training and inference share it.
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

SEED = 42


def seed_everything(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
    except ImportError:
        pass


def new_run(prefix: str, out_root: Path | None = None) -> tuple[Path, logging.Logger]:
    """Create experiments/<prefix>_<timestamp>/ and a logger writing to its train.log and the console."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = (out_root or EXPERIMENTS) / f"{prefix}_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(run_dir.name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s  %(message)s", datefmt="%H:%M:%S")
    for handler in (logging.FileHandler(run_dir / "train.log", encoding="utf-8"), logging.StreamHandler(sys.stdout)):
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    return run_dir, logger


def write_json(path: Path, data) -> None:
    def default(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, Path):
            return o.as_posix()
        raise TypeError(type(o))

    path.write_text(json.dumps(data, indent=2, default=default), encoding="utf-8")
