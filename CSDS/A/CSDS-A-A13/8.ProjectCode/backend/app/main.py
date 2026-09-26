"""SeatWise API entry point: ``uvicorn app.main:app`` from the backend folder."""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import api_router
from app.core.config import get_settings
from app.core.db import SessionLocal, create_all
from app.core.errors import install_error_handlers
from app.core.logging import configure_logging
from app.services.seed import seed_demo_users

log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    create_all()
    if settings.seed_demo_users:
        with SessionLocal() as db:
            seed_demo_users(db, settings)
    log.info("SeatWise API ready", extra={"version": __version__, "port": settings.api_port, "env": settings.app_env})
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title="SeatWise API",
        version=__version__,
        summary="Constraint-optimised, cheat-resistant exam seating plans.",
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )
    install_error_handlers(app)

    request_log = logging.getLogger("app.http")

    @app.middleware("http")
    async def _log_requests(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        if request.url.path.startswith("/api"):
            request_log.info("request", extra={
                "method": request.method, "path": request.url.path, "status": response.status_code,
                "ms": round((time.perf_counter() - started) * 1000)})
        return response

    app.include_router(api_router)
    return app


app = create_app()
