import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form
from sqlalchemy.orm import Session

from app.core.config import DATA_DIR
from app.core.database import get_db
from app.core.security import require_roles, get_current_user
from app.ml.quality.infer import grade_image
from app.models.crop import CropListing, QualityGrade
from app.models.user import User
from app.schemas.crop import CropListingOut

router = APIRouter(prefix="/api/crops", tags=["crops"])

UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/upload", response_model=CropListingOut)
async def upload_crop(
    crop_type: str = Form(...),
    region: str = Form(...),
    quantity_kg: float = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("farmer")),
):
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Upload a JPEG, PNG or WEBP image")

    raw = await image.read()
    if len(raw) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 8MB)")

    ext = Path(image.filename or "crop.jpg").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    (UPLOAD_DIR / filename).write_bytes(raw)

    listing = CropListing(
        farmer_id=user.id,
        crop_type=crop_type,
        region=region,
        quantity_kg=quantity_kg,
        image_path=f"/uploads/{filename}",
        status="draft",
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)

    result = grade_image(raw)
    quality = QualityGrade(
        listing_id=listing.id,
        grade=result["grade"],
        confidence=result["confidence"],
        probabilities=result["probabilities"],
        features=result["features"],
        shap_explanation=result["shap_explanation"],
    )
    db.add(quality)
    db.commit()
    db.refresh(listing)

    return listing


@router.get("/mine", response_model=list[CropListingOut])
def my_listings(db: Session = Depends(get_db), user: User = Depends(require_roles("farmer"))):
    return (
        db.query(CropListing)
        .filter(CropListing.farmer_id == user.id)
        .order_by(CropListing.created_at.desc())
        .all()
    )


@router.get("/{listing_id}", response_model=CropListingOut)
def get_listing(listing_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    listing = db.get(CropListing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.post("/{listing_id}/list", response_model=CropListingOut)
def publish_listing(
    listing_id: int,
    asking_price: float,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("farmer")),
):
    listing = db.get(CropListing, listing_id)
    if not listing or listing.farmer_id != user.id:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing.status = "listed"
    listing.asking_price = asking_price
    db.commit()
    db.refresh(listing)
    return listing
