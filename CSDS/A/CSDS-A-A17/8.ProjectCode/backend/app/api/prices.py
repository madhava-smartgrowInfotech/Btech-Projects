from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.ml.price.features import CROPS, REGIONS, GRADES
from app.ml.price.infer import predict_price
from app.models.crop import CropListing
from app.schemas.market import PriceRequest, PricePredictionOut

router = APIRouter(prefix="/api/prices", tags=["prices"])


@router.get("/options")
def options():
    return {"crops": CROPS, "regions": REGIONS, "grades": GRADES}


@router.post("/predict", response_model=PricePredictionOut)
def predict(payload: PriceRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    grade = payload.grade
    if payload.listing_id:
        listing = db.get(CropListing, payload.listing_id)
        if listing and listing.quality_grade:
            grade = listing.quality_grade.grade

    result = predict_price(payload.crop_type, payload.region, grade)
    return result
