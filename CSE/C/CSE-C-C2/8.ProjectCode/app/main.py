"""StoryVox FastAPI application entrypoint."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import BASE_DIR
from app.database import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("storyvox")

FRONTEND_DIR = BASE_DIR / "frontend"
FRONTEND_DIST = FRONTEND_DIR / "dist"


def create_app() -> FastAPI:
    init_db()
    application = FastAPI(title="StoryVox", version="1.0.0",
                          description="StoryVox - multilingual AI storytelling with natural speech narration.")
    application.include_router(router)

    # Serve the built React app (frontend/dist) when present; in development Vite serves it on its own port.
    if (FRONTEND_DIST / "assets").exists():
        application.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @application.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found.")
        index = FRONTEND_DIST / "index.html"
        if not index.exists():
            return {"app": "StoryVox", "docs": "/docs", "frontend": "run `npm run build` in frontend/ or use the Vite dev server"}
        candidate = (FRONTEND_DIST / path).resolve()
        if path and FRONTEND_DIST.resolve() in candidate.parents and candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(index), media_type="text/html")

    logger.info("StoryVox ready. Frontend: %s", FRONTEND_DIST)
    return application


app = create_app()
