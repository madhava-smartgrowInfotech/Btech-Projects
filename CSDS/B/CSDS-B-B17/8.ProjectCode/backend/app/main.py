from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import seed_users
from .config import FRONTEND_PORT
from .db import init_db
from .routes import calls, misc, studio
from .services import pipeline


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    seed_users()
    pipeline.start_worker()
    pipeline.warm_up()
    yield


app = FastAPI(title="CallSense API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware,
                   allow_origins=[f"http://localhost:{FRONTEND_PORT}", f"http://127.0.0.1:{FRONTEND_PORT}"],
                   allow_methods=["*"], allow_headers=["*"])
for r in (misc.router, calls.router, studio.router):
    app.include_router(r)
