from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.core.deps import DB

router = APIRouter(tags=["health"])


@router.get("/health", summary="Service health")
def health(db: DB) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "version": __version__, "database": "ok"}
