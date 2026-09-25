from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import admin, auth, crops, delivery, iot, marketplace, prices
from app.core.config import DATA_DIR, settings
from app.core.database import Base, engine
from app import models  # noqa: F401  ensures models are registered before create_all

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

(DATA_DIR / "uploads").mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(DATA_DIR / "uploads")), name="uploads")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.app_name}


app.include_router(auth.router)
app.include_router(crops.router)
app.include_router(prices.router)
app.include_router(delivery.router)
app.include_router(iot.router)
app.include_router(marketplace.router)
app.include_router(admin.router)
