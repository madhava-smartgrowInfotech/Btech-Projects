from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.database import init_db
from app.routes import about, auth, chat, history, pages
from app.demo import ensure_demo_user

app = FastAPI(title="CareLens AI")
BASE = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(history.router)
app.include_router(about.router)

@app.on_event("startup")
def startup():
    init_db()
    ensure_demo_user()

@app.get("/api/health")
def health():
    return {"status": "ok", "product": "CareLens AI"}
