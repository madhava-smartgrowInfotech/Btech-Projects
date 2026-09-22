from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.core.db import SessionLocal

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    from app.ml.registry import registry

    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok", "models": registry.status()}
