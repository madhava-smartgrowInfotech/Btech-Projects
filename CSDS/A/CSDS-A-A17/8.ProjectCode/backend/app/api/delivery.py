from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.ml.delivery.recommend import recommend
from app.models.crop import CropListing
from app.models.delivery import DeliveryRecommendation
from app.models.user import User
from app.schemas.delivery import DeliveryRecommendationOut

router = APIRouter(prefix="/api/delivery", tags=["delivery"])


@router.get("/{listing_id}/recommend", response_model=DeliveryRecommendationOut)
def get_recommendation(listing_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("farmer"))):
    listing = db.get(CropListing, listing_id)
    if not listing or listing.farmer_id != user.id:
        raise HTTPException(status_code=404, detail="Listing not found")

    grade = listing.quality_grade.grade if listing.quality_grade else "B"
    result = recommend(db, listing.crop_type, listing.region, grade, listing.quantity_kg)

    rec = DeliveryRecommendation(
        listing_id=listing.id,
        ranked_buyers=result["ranked_buyers"],
        best_route=result["best_route"],
        best_sell_day=result["best_sell_day"],
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec
