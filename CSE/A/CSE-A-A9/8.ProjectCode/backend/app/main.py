"""BotGraph API. Run from the project root:  python -m uvicorn backend.app.main:app --port 8309"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import seed_demo_users
from .db import init_db
from .routes import accounts, clusters, core, models, queue
from .services.store import get_store
from .settings import FRONTEND_PORT


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    seed_demo_users()
    get_store()          # load graph, scores and clusters once at start-up
    yield


app = FastAPI(title="BotGraph API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{FRONTEND_PORT}", f"http://127.0.0.1:{FRONTEND_PORT}"],
    allow_methods=["*"], allow_headers=["*"],
)
for r in (core.router, accounts.router, clusters.router, queue.router, models.router):
    app.include_router(r)
