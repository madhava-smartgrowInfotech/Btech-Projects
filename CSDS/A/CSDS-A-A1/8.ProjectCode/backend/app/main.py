"""PolicyLens API - FastAPI application entry point.

Run with:  uvicorn app.main:app --port 8101   (from the backend/ folder)
"""

from __future__ import annotations

import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api import api_router
from app.core.config import get_settings
from app.core.db import init_db
from app.core.errors import AppError
from app.core.logging import configure_logging, get_logger, log_event

configure_logging()
log = get_logger("app")


def _warm_up() -> None:
    """Load the local models and check which Gemini model is answering, in the background."""
    try:
        from app.ml.local_models import warm_up

        warm_up()
    except Exception as exc:  # noqa: BLE001
        log_event(log, "warm_up_failed", error=str(exc))
    try:
        from app.services.gemini_client import probe_models

        probe_models()
    except Exception as exc:  # noqa: BLE001
        log_event(log, "model_probe_failed", error=str(exc))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    init_db()
    from app.services.seed import seed_all

    seed_all()
    from app.services.ingestion import start_worker

    start_worker()
    threading.Thread(target=_warm_up, name="warm-up", daemon=True).start()
    log_event(log, "startup", port=settings.backend_port, gemini=settings.gemini_configured,
              model=settings.gemini_model, embeddings=settings.embedding_provider)
    yield
    from app.services.ingestion import stop_worker

    stop_worker()


app = FastAPI(
    title="PolicyLens API",
    version=__version__,
    description="Understand your health-insurance policy: clause-cited answers, Policy Card, risk highlights, "
    "Claim Copilot and plan comparison.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_log(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    if request.url.path.startswith("/api") and not request.url.path.startswith("/api/health"):
        log_event(log, "request", method=request.method, path=request.url.path,
                  status=response.status_code, ms=round((time.perf_counter() - start) * 1000))
    return response


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "code": exc.code})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = ".".join(str(p) for p in first.get("loc", []) if p not in ("body", "query", "path"))
    message = str(first.get("msg", "Invalid request")).removeprefix("Value error, ")
    detail = f"{field}: {message}" if field else message
    return JSONResponse(
        status_code=422,
        content={"detail": detail, "code": "validation_error",
                 "errors": [{"field": ".".join(map(str, e.get("loc", []))), "message": e.get("msg")} for e in errors]},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled_error path=%s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong on our side. Please try again.", "code": "server_error"},
    )


app.include_router(api_router)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"name": "PolicyLens API", "version": __version__, "docs": "/docs"}
