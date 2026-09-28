import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # project root, for `ml`

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from sqlalchemy import select  # noqa: E402

from . import state  # noqa: E402
from .auth import hash_password  # noqa: E402
from .db import SessionLocal, User, init_db  # noqa: E402
from .routes import auth, conversations, info, recognize, speech  # noqa: E402

DEMO_EMAIL, DEMO_PASSWORD = "demo@signbridge.app", "demo1234"


def seed_demo_user():
    with SessionLocal() as db:
        if not db.scalar(select(User).where(User.email == DEMO_EMAIL)):
            db.add(User(email=DEMO_EMAIL, name="Demo User", password_hash=hash_password(DEMO_PASSWORD)))
            db.commit()


@asynccontextmanager
async def lifespan(app):
    from .services.recognizer import Recognizer
    from .services.stt import STT

    init_db()
    seed_demo_user()
    state.recognizer = Recognizer()
    state.stt = STT()  # loads in the background
    yield


app = FastAPI(title="SignBridge API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5205", "http://127.0.0.1:5205"],
                   allow_methods=["*"], allow_headers=["*"], expose_headers=["X-Latency-Ms"])
for r in (auth, recognize, speech, conversations, info):
    app.include_router(r.router)
