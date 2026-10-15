import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import FRONTEND_PORT, GEMINI_API_KEY
from .db import init_db
from .routes import auth_routes, metrics, patients, scans
from .services.pipeline import engine

app = FastAPI(title="PulmoVision API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=[f"http://localhost:{FRONTEND_PORT}", f"http://127.0.0.1:{FRONTEND_PORT}"],
                   allow_methods=["*"], allow_headers=["*"], expose_headers=["X-AI-Status"])
for r in (auth_routes, patients, scans, metrics):
    app.include_router(r.router)


@app.on_event("startup")
def startup():
    init_db()
    threading.Thread(target=engine.load, daemon=True).start()  # warm the models in the background


@app.get("/api/health")
def health():
    return {"status": "ok", "models_loaded": engine.loaded, "gemini_configured": bool(GEMINI_API_KEY)}
