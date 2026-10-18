"""SafeGrid-AI FastAPI application entrypoint.  Run:  uvicorn app.main:app --reload --port 8000"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_agents, routes_grid, routes_metrics, routes_safety, routes_simulation
from app.config import get_settings
from app.services.simulation_service import SimulationService


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await app.state.service.stop()


def create_app(service: SimulationService | None = None) -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="SafeGrid-AI", version="1.0.0", lifespan=lifespan,
                  description="Explainable multi-agent power routing with a deterministic Symbolic Safety Shield.")
    app.state.service = service or SimulationService(settings)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=False,
                       allow_methods=["*"], allow_headers=["*"])
    for r in (routes_grid, routes_simulation, routes_agents, routes_safety, routes_metrics):
        app.include_router(r.router)

    @app.websocket("/ws/simulation")
    async def ws_simulation(ws: WebSocket):
        svc: SimulationService = ws.app.state.service
        await ws.accept()
        await svc.hub.add(ws)
        try:
            await ws.send_json({"type": "connected", "data": svc.status()})
            while True:  # clients only listen; any inbound text is treated as a keep-alive ping
                await ws.receive_text()
        except WebSocketDisconnect:
            pass
        except Exception:
            pass
        finally:
            await svc.hub.remove(ws)

    return app


app = create_app()
