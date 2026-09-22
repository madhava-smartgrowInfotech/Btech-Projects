"""SignalScout API: FastAPI application, lifespan, routers and the built web app."""
from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .api import admin, auth, coverage, devices, ingest, readings, system
from .core.config import APP_NAME, APP_VERSION, settings
from .core.db import SessionLocal, init_db
from .core.logging import log_event, setup_logging
from .ml.registry import load_models
from .seed import seed_demo_users
from .services.sample_data import seed_in_background
from .services.simulator_setup import ensure_simulator_devices

log = logging.getLogger("signalscout")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    if not settings.jwt_secret or settings.jwt_secret.startswith("replace-with"):
        raise RuntimeError("JWT_SECRET is not set - run setup.bat (or scripts/sync_env.py) to create .env")
    init_db()
    if settings.seed_demo_users:
        with SessionLocal() as db:
            seed_demo_users(db)
    load_models()
    if settings.esp32_simulator:
        with SessionLocal() as db:
            ensure_simulator_devices(db)
    if settings.seed_sample_data:
        seed_in_background()
    log_event(log, "started", version=APP_VERSION, port=settings.backend_port, database=settings.database_url.rsplit("/", 1)[-1])
    yield
    log_event(log, "stopped")


app = FastAPI(
    title=f"{APP_NAME} API",
    version=APP_VERSION,
    description="Finds weak and dead mobile-network zones from phone and sensor readings, suggests better-signal "
                "spots and files complaints with technical evidence.",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def request_log(request: Request, call_next):
    start = time.perf_counter()
    request_id = uuid.uuid4().hex[:8]
    try:
        response = await call_next(request)
    except Exception:
        log.exception("unhandled error", extra={"fields": {"request_id": request_id, "path": request.url.path}})
        return JSONResponse({"detail": "Something went wrong on the server - it has been logged."}, status_code=500)
    if request.url.path.startswith("/api/") and request.url.path not in ("/api/health", "/api/probe/ping"):
        log_event(log, "request", request_id=request_id, method=request.method, path=request.url.path,
                  status=response.status_code, ms=round((time.perf_counter() - start) * 1000, 1))
    response.headers["X-Request-ID"] = request_id
    return response


for router in (auth.router, system.router, admin.router, devices.router, ingest.router, readings.router, coverage.router):
    app.include_router(router)


# ---------------------------------------------------------------- web app (production build)
@app.get("/{full_path:path}", include_in_schema=False)
def web_app(full_path: str):
    if full_path.startswith("api/") or full_path == "api":
        return JSONResponse({"detail": "Not found"}, status_code=404)
    dist = settings.frontend_dist
    index = dist / "index.html"
    if not index.exists():
        return JSONResponse({"detail": "The web app is not built yet. Run setup.bat (or: cd frontend && npm run build). "
                                       f"During development open http://localhost:{settings.frontend_port}"}, status_code=404)
    candidate = (dist / full_path).resolve()
    if full_path and candidate.is_file() and dist.resolve() in candidate.parents:
        headers = {"Cache-Control": "no-cache"} if candidate.name in ("sw.js", "manifest.webmanifest", "index.html") else \
                  {"Cache-Control": "public, max-age=31536000, immutable"} if "/assets/" in candidate.as_posix() else {}
        return FileResponse(candidate, headers=headers)
    return FileResponse(index, headers={"Cache-Control": "no-cache"})
