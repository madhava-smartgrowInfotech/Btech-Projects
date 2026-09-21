from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.core.config import get_settings
from app.core.db import SessionLocal

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, Any]:
    settings = get_settings()
    db_ok = True
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - health must never raise
        db_ok = False

    from app.ml.local_models import models_status
    from app.ml.retrieval.dense_index import vector_store_status
    from app.services.gemini_client import model_health
    from app.services.ingestion import worker_status

    return {
        "status": "ok" if db_ok else "degraded",
        "version": __version__,
        "database": "ok" if db_ok else "error",
        "vector_store": vector_store_status(),
        "local_models": models_status(),
        "ingestion": worker_status(),
        "gemini": {
            "configured": settings.gemini_configured,
            "model": settings.gemini_model,
            "fallback_models": settings.gemini_fallback_models,
            "availability": model_health() if settings.gemini_configured else {},
        },
        "embedding_provider": settings.embedding_provider,
        "languages": settings.supported_languages,
    }
