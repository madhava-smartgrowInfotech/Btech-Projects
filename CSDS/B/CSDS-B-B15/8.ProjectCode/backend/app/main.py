from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from . import seed
from .db import init_db
from .routes import auth, bookings, console, dashboard, hospitals, referrals
from .services import triage
from .services.queue import hub


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    triage.symptom_vocab()  # load models once at start-up
    seed.run()
    yield


app = FastAPI(title="MediQueue API", version="1.0", lifespan=lifespan)
for r in (auth.router, hospitals.router, bookings.router, console.router, referrals.router, dashboard.router):
    app.include_router(r)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.websocket("/api/ws/hospital/{hid}")
async def queue_socket(ws: WebSocket, hid: int):
    """Pushes a 'queue_changed' event whenever this hospital's queue changes (hid 0 = every hospital)."""
    await hub.connect(hid, ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive pings from the client
    except WebSocketDisconnect:
        hub.disconnect(hid, ws)
