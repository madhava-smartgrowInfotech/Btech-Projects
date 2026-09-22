"""CivicPulse API.  Run: venv\\Scripts\\python -m uvicorn app.main:app --port 8201 (from backend/)."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import FRONTEND_PORT
from .db import init_db
from .routes import analytics, auth_admin, complaints, model, officer
from .services.predictor import get_predictor
from .services.seed import run_seed


@asynccontextmanager
async def lifespan(_app):
    init_db()
    run_seed(get_predictor())  # departments, wards, demo accounts, sample history (first run only)
    yield


app = FastAPI(title="CivicPulse API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[f"http://localhost:{FRONTEND_PORT}",
                                                  f"http://127.0.0.1:{FRONTEND_PORT}"],
                   allow_methods=["*"], allow_headers=["*"])
for r in (auth_admin, complaints, officer, model, analytics):  # complaints before officer: /complaints/mine
    app.include_router(r.router)
