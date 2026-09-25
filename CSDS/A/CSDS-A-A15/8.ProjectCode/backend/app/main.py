import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.ml.labels import CLASS_NAMES
from app.routers import analytics, auth, inspections, reports

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(inspections.router)
app.include_router(reports.router)
app.include_router(analytics.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": settings.app_name}


@app.get("/api/public/model-info")
def public_model_info():
    info = {"defect_classes": len(CLASS_NAMES), "test_accuracy": None, "trained_at": None}
    if settings.metrics_path.exists():
        metrics = json.loads(settings.metrics_path.read_text())
        info["test_accuracy"] = metrics.get("test_accuracy")
        info["trained_at"] = metrics.get("trained_at")
    return info
