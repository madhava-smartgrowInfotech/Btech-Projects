from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.inference import load_models
from app.models.db import init_db

app = FastAPI(title="SeedIQ API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    try:
        load_models()
    except RuntimeError as e:
        # Server still starts so /api/health reports "degraded" instead of
        # the process failing outright if artifacts haven't been built yet.
        print(f"[startup] {e}")


app.include_router(router)


@app.get("/")
def root():
    return {"service": "SeedIQ API", "docs": "/docs"}
