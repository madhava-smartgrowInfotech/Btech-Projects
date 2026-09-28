from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from .auth import hash_password
from .config import DEMO_EMAIL, DEMO_PASSWORD, FRONTEND_PORT
from .db import SessionLocal, User, init_db
from .routes import auth, dna, history, metrics, mri, str_routes


@asynccontextmanager
async def lifespan(_app):
    init_db()
    with SessionLocal() as db:
        if not db.scalar(select(User).where(User.email == DEMO_EMAIL)):
            db.add(User(name="Demo Analyst", email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD)))
            db.commit()
    yield


app = FastAPI(title="BioSight API", version="1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware,
                   allow_origins=[f"http://localhost:{FRONTEND_PORT}", f"http://127.0.0.1:{FRONTEND_PORT}"],
                   allow_methods=["*"], allow_headers=["*"])
for r in (auth, mri, dna, str_routes, metrics, history):
    app.include_router(r.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "BioSight"}
