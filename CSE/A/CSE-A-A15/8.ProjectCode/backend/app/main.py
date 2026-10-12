from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from .auth import hash_pw
from .config import FRONTEND_PORT
from .db import SessionLocal, User, init_db
from .routes import analysis, auth, keys, ops, samples

DEMO_USER, DEMO_PASSWORD = "demo", "Demo@12345"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with SessionLocal() as db:
        if not db.scalar(select(User).where(User.username == DEMO_USER)):
            db.add(User(username=DEMO_USER, pw_hash=hash_pw(DEMO_PASSWORD)))
            db.commit()
    yield


app = FastAPI(title="CipherVeil", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[f"http://localhost:{FRONTEND_PORT}", f"http://127.0.0.1:{FRONTEND_PORT}"],
                   allow_methods=["*"], allow_headers=["*"])
for r in (auth.router, keys.router, samples.router, ops.router, analysis.router):
    app.include_router(r)


@app.get("/api/health")
def health():
    return {"status": "ok"}
