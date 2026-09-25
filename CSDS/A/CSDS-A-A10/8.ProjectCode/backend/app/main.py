from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, beds, dashboard, departments, labs, visits, ws
from app.core.config import settings
from app.core.database import Base, engine
from app.ml.predictor import ensure_models_trained

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # Vite falls back to the next free port when 5173 is taken, so match any
    # localhost port in dev rather than hardcoding one.
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    ensure_models_trained()


app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(visits.router)
app.include_router(beds.router)
app.include_router(labs.router)
app.include_router(dashboard.router)
app.include_router(ws.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.app_name}
