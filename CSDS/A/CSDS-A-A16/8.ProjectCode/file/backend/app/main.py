from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import CORS_ORIGINS, MEDIA_DIR
from app.db import Base, engine
from app.ml.inference import load_model
from app.routers import auth, analyze, history, health

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mosaic API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/api/media/thumbs", StaticFiles(directory=str(MEDIA_DIR)), name="thumbs")

app.include_router(auth.router)
app.include_router(analyze.router)
app.include_router(history.router)
app.include_router(health.router)


@app.on_event("startup")
def _load_model_on_startup():
    try:
        load_model()
    except FileNotFoundError:
        pass
