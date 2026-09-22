"""UPI Guardian API - FastAPI application entry point."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import router as api_router
from app.core.config import get_settings
from app.core.db import create_all, session_scope
from app.core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging(settings.log_level)
log = get_logger("upi_guardian")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.ml.registry import registry
    from app.seed import seed_if_empty
    from app.services import notifier, scheduler

    create_all()
    registry.load()
    if settings.seed_sample_data:
        with session_scope() as db:
            seed_if_empty(db)
    notifier.bind_loop(asyncio.get_running_loop())
    task = asyncio.create_task(scheduler.run_forever(settings.hold_check_seconds))
    log.info("api started", extra={"port": settings.api_port, "models": registry.status()})
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="UPI Guardian API",
    version="1.0.0",
    description="Pre-transaction risk scoring, scam-SMS checks, intent verification and Delayed Protection for UPI payments.",
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(p) for p in first.get("loc", [])[1:]) or "request"
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "code": "validation_error",
                "message": f"Please check {field}: {first.get('msg', 'invalid value')}.",
                "field": field,
                "errors": [
                    {"loc": e.get("loc"), "msg": e.get("msg"), "type": e.get("type")} for e in exc.errors()
                ],
            }
        },
    )


@app.exception_handler(Exception)
async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled error")
    return JSONResponse(
        status_code=500,
        content={"detail": {"code": "server_error", "message": "Something went wrong on our side. Please try again."}},
    )


app.include_router(api_router, prefix="/api")


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {"name": "UPI Guardian API", "docs": "/docs", "health": "/api/health"}
