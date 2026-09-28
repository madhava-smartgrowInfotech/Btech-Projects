from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import seed_users
from .db import init_db
from .routes import auth, misc, patients, screenings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    seed_users()
    yield


app = FastAPI(title="RetinaGuard API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5216", "http://127.0.0.1:5216"],
                   allow_methods=["*"], allow_headers=["*"])
for r in (auth.router, patients.router, screenings.router, misc.router):
    app.include_router(r)
