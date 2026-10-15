"""
SkillVerse web API
==================
Thin FastAPI layer over the existing Python modules (services/, ai/, graph/, database/).
No business logic is rewritten here - routes call the same functions the Streamlit pages call.

Run from the project root:  python -m uvicorn backend.main:app --port 8203
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)  # the default SQLite path (sqlite:///knowledgex.db) is relative to the project root

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(ROOT, ".env"))

from contextlib import asynccontextmanager  # noqa: E402

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from database.database import init_db  # noqa: E402
from database.seed import seed_all  # noqa: E402
from backend.routers import auth, student, market, mentors, practice, admin  # noqa: E402

FRONTEND_PORT = os.getenv("FRONTEND_PORT", "5203")


@asynccontextmanager
async def lifespan(_app):
    init_db()
    seed_all()  # no-op when the database is already seeded
    yield


app = FastAPI(title="SkillVerse API", version="1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{FRONTEND_PORT}", f"http://127.0.0.1:{FRONTEND_PORT}"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled(_request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": f"The server hit an unexpected error: {exc}"})


@app.get("/api/health")
def health():
    return {"status": "ok"}


for module in (auth, student, market, mentors, practice, admin):
    app.include_router(module.router, prefix="/api")
