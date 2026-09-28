"""HospiSense API."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import FRONTEND_PORT, JWT_SECRET
from .db import init_db
from .routes import admissions, allocation, auth, forecast, overview
from .services.engine import get_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is missing - copy .env.example to .env (setup.bat does this)")
    init_db()
    get_engine()  # load models and history once
    yield


app = FastAPI(title="HospiSense API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[f"http://localhost:{FRONTEND_PORT}", f"http://127.0.0.1:{FRONTEND_PORT}"],
                   allow_methods=["*"], allow_headers=["*"])
for r in (auth, admissions, forecast, allocation, overview):
    app.include_router(r.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
