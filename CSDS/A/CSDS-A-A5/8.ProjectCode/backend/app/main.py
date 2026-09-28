"""TaxSentinel API."""
import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from .auth import hash_password
from .config import CORS_ORIGINS, DEMO_EMAIL, DEMO_PASSWORD, GEMINI_API_KEY
from .db import SessionLocal, User, init_db
from .routes import auth, explanations, investigate, pipeline
from .services.state import store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app):
    init_db()
    db = SessionLocal()
    if not db.scalar(select(User).where(User.email == DEMO_EMAIL)):
        db.add(User(email=DEMO_EMAIL, name="Demo Analyst", password_hash=hash_password(DEMO_PASSWORD)))
        db.commit()
    db.close()
    threading.Thread(target=store.load, daemon=True).start()
    yield


app = FastAPI(title="TaxSentinel API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"])
for r in (auth.router, pipeline.router, investigate.router, explanations.router):
    app.include_router(r)


@app.get("/api/health")
def health():
    return {"status": "ok", "pipeline_ready": store.get() is not None, "gemini_configured": bool(GEMINI_API_KEY)}
