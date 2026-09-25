import datetime as dt

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import ENCODER_VERSION, MODEL_VERSION, SEED_TYPES
from app.core.inference import get_global_feature_importance, get_model_metrics, models_loaded, run_prediction
from app.models.db import PredictionRecord, get_session
from app.models.schemas import HealthResponse, HistoryItem, ModelInfoResponse, PredictionResponse, StatsResponse

router = APIRouter(prefix="/api")

MAX_IMAGE_BYTES = 8 * 1024 * 1024


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok" if models_loaded() else "degraded",
        model_version=MODEL_VERSION,
        encoder_version=ENCODER_VERSION,
    )


@router.get("/seed-types")
def seed_types():
    return {"seed_types": SEED_TYPES}


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    image: UploadFile = File(...),
    soil_moisture: float = Form(...),
    temperature: float = Form(...),
    humidity: float = Form(...),
    rainfall: float = Form(...),
    soil_ph: float = Form(...),
    seed_type: str = Form(...),
    session: Session = Depends(get_session),
):
    if seed_type not in SEED_TYPES:
        raise HTTPException(status_code=422, detail=f"seed_type must be one of {SEED_TYPES}")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=422, detail="Uploaded image is empty")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 8MB)")

    try:
        result = run_prediction(image_bytes, soil_moisture, temperature, humidity, rainfall, soil_ph, seed_type)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not process image: {e}")

    record = PredictionRecord(
        seed_type=seed_type,
        soil_moisture=soil_moisture,
        temperature=temperature,
        humidity=humidity,
        rainfall=rainfall,
        soil_ph=soil_ph,
        prediction=result["prediction"],
        confidence=result["confidence"],
        probability_germinate=result["probability_germinate"],
        risk_level=result["risk_level"],
        morphological_features=result["morphological_features"],
        embedding_summary=result["embedding_summary"],
        explanation=result["explanation"],
        thumbnail_data_url=result["thumbnail_data_url"],
    )
    session.add(record)
    session.commit()
    session.refresh(record)

    return PredictionResponse(id=record.id, created_at=record.created_at, **result)


@router.get("/history", response_model=list[HistoryItem])
def history(limit: int = 20, session: Session = Depends(get_session)):
    limit = max(1, min(limit, 200))
    records = (
        session.query(PredictionRecord)
        .order_by(PredictionRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    return records


@router.get("/history/{record_id}", response_model=PredictionResponse)
def history_detail(record_id: str, session: Session = Depends(get_session)):
    record = session.get(PredictionRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return PredictionResponse(
        id=record.id,
        prediction=record.prediction,
        confidence=record.confidence,
        probability_germinate=record.probability_germinate,
        risk_level=record.risk_level,
        morphological_features=record.morphological_features,
        embedding_summary=record.embedding_summary,
        explanation=record.explanation,
        seed_type=record.seed_type,
        soil_moisture=record.soil_moisture,
        temperature=record.temperature,
        humidity=record.humidity,
        rainfall=record.rainfall,
        soil_ph=record.soil_ph,
        created_at=record.created_at,
        thumbnail_data_url=record.thumbnail_data_url,
    )


@router.delete("/history/{record_id}")
def delete_history(record_id: str, session: Session = Depends(get_session)):
    record = session.get(PredictionRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Prediction not found")
    session.delete(record)
    session.commit()
    return {"deleted": record_id}


@router.get("/stats", response_model=StatsResponse)
def stats(session: Session = Depends(get_session)):
    total = session.query(func.count(PredictionRecord.id)).scalar() or 0

    if total == 0:
        return StatsResponse(
            total_predictions=0, germination_rate=0.0, avg_confidence=0.0,
            seed_type_breakdown={}, trend=[], model_metrics=get_model_metrics(),
        )

    germinated = session.query(func.count(PredictionRecord.id)).filter(
        PredictionRecord.prediction == "germinate"
    ).scalar() or 0
    avg_conf = session.query(func.avg(PredictionRecord.confidence)).scalar() or 0.0

    breakdown_rows = (
        session.query(PredictionRecord.seed_type, func.count(PredictionRecord.id))
        .group_by(PredictionRecord.seed_type)
        .all()
    )
    breakdown = {name: count for name, count in breakdown_rows}

    trend_rows = (
        session.query(func.date(PredictionRecord.created_at), func.count(PredictionRecord.id))
        .group_by(func.date(PredictionRecord.created_at))
        .order_by(func.date(PredictionRecord.created_at))
        .limit(30)
        .all()
    )
    trend = [{"date": str(d), "count": c} for d, c in trend_rows]

    return StatsResponse(
        total_predictions=total,
        germination_rate=round(germinated / total, 4),
        avg_confidence=round(float(avg_conf), 4),
        seed_type_breakdown=breakdown,
        trend=trend,
        model_metrics=get_model_metrics(),
    )


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info():
    architecture = {
        "pipeline": [
            "Morphological trait extraction (OpenCV contour segmentation)",
            "Self-supervised JEPA patch encoder (context/target/predictor, EMA target)",
            "Feature fusion (image embedding + morphology + environmental data)",
            "Gradient-boosted fusion classifier (XGBoost)",
            "Contribution-based explanation generation",
        ],
        "encoder": {
            "type": "JEPA (Joint-Embedding Predictive Architecture)",
            "version": ENCODER_VERSION,
            "patch_size": 8,
            "embedding_dim": 48,
        },
        "classifier": {
            "type": "XGBoost gradient-boosted trees",
            "version": MODEL_VERSION,
        },
    }
    return ModelInfoResponse(
        architecture=architecture,
        global_feature_importance=get_global_feature_importance(),
        metrics=get_model_metrics(),
    )
