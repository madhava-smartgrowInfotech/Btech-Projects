"""Shared helpers for the ml/ scripts: paths, dataset roots, splits and cached arrays."""
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services import imaging  # noqa: E402
from app.services.nets import CT_CLASSES, XRAY_CLASSES  # noqa: E402

SEED = 42
CACHE = ROOT / "data" / "raw" / "cache"
SPLITS = ROOT / "experiments" / "splits.json"
MODELS = ROOT / "models"
EXPERIMENTS = ROOT / "experiments"


def dataset_roots():
    """Locations of the three datasets. Override with env vars (used on Kaggle)."""
    paths_file = ROOT / "data" / "raw" / "paths.json"
    found = json.loads(paths_file.read_text()) if paths_file.exists() else {}
    covid = os.getenv("COVID_ROOT") or (found.get("covid19_radiography", "") and os.path.join(found["covid19_radiography"], "COVID-19_Radiography_Dataset"))
    tb = os.getenv("TB_ROOT") or (found.get("tb_chest_xray", "") and os.path.join(found["tb_chest_xray"], "TB_Chest_Radiography_Database"))
    ct = os.getenv("CT_ROOT") or str(ROOT / "data" / "chest_ct")
    return {"covid": covid, "tb": tb, "ct": ct}


def read_gray(root_key, rel):
    path = os.path.join(dataset_roots()[root_key], rel)
    with open(path, "rb") as f:
        gray, _, _ = imaging.load_image(f.read(), path)
    return gray
