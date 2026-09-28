from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import seed
from .config import FRONTEND_PORT
from .routes import analytics, auth, coding, contests, interviews, practice, recruiter, resume
from .services import ai, judge


@asynccontextmanager
async def lifespan(app):
    seed.run()
    yield


app = FastAPI(title="TalentTrack API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[f"http://localhost:{FRONTEND_PORT}", f"http://127.0.0.1:{FRONTEND_PORT}"],
                   allow_methods=["*"], allow_headers=["*"])
for r in (auth, practice, coding, contests, interviews, resume, recruiter, analytics):
    app.include_router(r.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "ai_configured": ai.configured(),
            "languages": {l["id"]: l["available"] for l in judge.available_languages()}}
