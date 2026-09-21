"""Shared setup for the evaluation scripts: import path, evaluation data, sample document ids."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EVAL_DIR = ROOT / "data" / "eval"


def load_jsonl(name: str) -> list[dict[str, Any]]:
    path = EVAL_DIR / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_json(name: str) -> Any:
    return json.loads((EVAL_DIR / name).read_text(encoding="utf-8"))


def prepare_app() -> dict[str, int]:
    """Make sure the database, sample policies and search index exist; return {slug: document id}."""
    from sqlalchemy import select

    from app.core.db import SessionLocal, init_db
    from app.core.logging import configure_logging
    from app.ml.retrieval import dense_index
    from app.models import Document
    from app.services import ingestion
    from app.services.seed import seed_all

    configure_logging()
    init_db()
    ingestion.start_worker()
    seed_all()
    ingestion.wait_until_idle(timeout=1800)
    with SessionLocal() as db:
        docs = db.scalars(select(Document).where(Document.is_sample.is_(True))).all()
        mapping = {d.sample_slug: d.id for d in docs if d.status == "ready"}
        for d in docs:
            if d.status == "ready" and dense_index.count_for(d.id) == 0:
                dense_index.index_document(d.id)
    missing = [slug for slug in ("star-health-family-health-optima", "hdfc-ergo-optima-secure",
                                 "niva-bupa-reassure-2", "care-health-care-supreme") if slug not in mapping]
    if missing:
        raise SystemExit(f"Sample policies not ready: {missing}. Run scripts/init_app.py first.")
    return mapping
