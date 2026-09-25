"""Nuvara API entry point."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import ALLOWED_ORIGINS
from .db import Base, SessionLocal, engine
from .recommender.orchestrator import orchestrator
from .recommender.traffic_manager import traffic_manager
from .routers import catalog, events, feedback, recommendations, simulate, traffic, users
from .seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_database(db)
        orchestrator.build(db)
    finally:
        db.close()

    traffic_manager.start()
    try:
        yield
    finally:
        await traffic_manager.stop()


app = FastAPI(
    title="Nuvara API",
    version="1.0.0",
    description=(
        "Storefront and intelligence services for Nuvara: multi-agent "
        "recommendations, explainability, the self-learning weight loop, the "
        "digital twin simulation lab and the traffic control centre."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (catalog, users, events, recommendations, feedback, simulate, traffic):
    app.include_router(module.router, prefix="/api")


@app.get("/api/health", tags=["meta"])
def health():
    return {
        "ok": True,
        "engine_ready": orchestrator.ready,
        "catalog_size": len(orchestrator.products),
        "population_size": len(orchestrator.users),
        "live_weights": orchestrator.weights,
        "learning_step": orchestrator.step,
        "traffic_status": traffic_manager.state.status,
    }


@app.websocket("/ws/traffic")
async def traffic_socket(websocket: WebSocket):
    await websocket.accept()
    await traffic_manager.connect(websocket)
    try:
        while True:
            # The push loop does the sending; this read keeps the connection
            # alive and surfaces a client disconnect promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except (asyncio.CancelledError, RuntimeError):
        pass
    except Exception:
        pass
    finally:
        traffic_manager.disconnect(websocket)


@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc: RequestValidationError):
    """Flatten FastAPI's list-shaped validation errors into the contract's
    `{detail: string}` so the frontend only ever parses one error shape."""
    parts = []
    for error in exc.errors():
        location = ".".join(str(p) for p in error.get("loc", []) if p != "body")
        parts.append(f"{location}: {error.get('msg')}" if location else str(error.get("msg")))
    return JSONResponse(status_code=422, content={"detail": "; ".join(parts) or "Invalid request"})
