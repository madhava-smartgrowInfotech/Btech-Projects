from fastapi import APIRouter

from app.ml.inference import model_is_loaded
from app.schemas import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", model_loaded=model_is_loaded())
