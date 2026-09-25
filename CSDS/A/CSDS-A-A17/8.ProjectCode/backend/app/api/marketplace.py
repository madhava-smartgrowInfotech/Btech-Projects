from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.crop import CropListing
from app.models.iot import Shipment
from app.models.order import Order
from app.models.user import User
from app.schemas.crop import CropListingOut
from app.schemas.order import OrderCreate, OrderOut, OrderStatusUpdate

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])


@router.get("/listings", response_model=list[CropListingOut])
def browse_listings(
    crop_type: str | None = None,
    region: str | None = None,
    grade: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(CropListing).filter(CropListing.status == "listed")
    if crop_type:
        query = query.filter(CropListing.crop_type == crop_type)
    if region:
        query = query.filter(CropListing.region == region)
    listings = query.order_by(CropListing.created_at.desc()).all()
    if grade:
        listings = [l for l in listings if l.quality_grade and l.quality_grade.grade == grade]
    return listings


@router.get("/listings/{listing_id}", response_model=CropListingOut)
def listing_detail(listing_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    listing = db.get(CropListing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.post("/orders", response_model=OrderOut)
def place_order(payload: OrderCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("buyer"))):
    listing = db.get(CropListing, payload.listing_id)
    if not listing or listing.status != "listed":
        raise HTTPException(status_code=400, detail="Listing is not available")

    order = Order(
        listing_id=listing.id,
        buyer_id=user.id,
        quantity_kg=payload.quantity_kg,
        agreed_price=payload.agreed_price,
        status="placed",
    )
    listing.status = "sold"
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/orders/mine", response_model=list[OrderOut])
def my_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role == "buyer":
        return db.query(Order).filter(Order.buyer_id == user.id).order_by(Order.created_at.desc()).all()
    if user.role == "farmer":
        listing_ids = [l.id for l in db.query(CropListing).filter(CropListing.farmer_id == user.id).all()]
        return (
            db.query(Order)
            .filter(Order.listing_id.in_(listing_ids) if listing_ids else False)
            .order_by(Order.created_at.desc())
            .all()
        )
    if user.role == "distributor":
        return (
            db.query(Order)
            .filter((Order.distributor_id == user.id) | (Order.status == "confirmed"))
            .order_by(Order.created_at.desc())
            .all()
        )
    return db.query(Order).order_by(Order.created_at.desc()).limit(50).all()


VALID_TRANSITIONS = {
    "placed": {"confirmed", "cancelled"},
    "confirmed": {"in_transit", "cancelled"},
    "in_transit": {"delivered"},
}


@router.patch("/orders/{order_id}/status", response_model=OrderOut)
def update_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status not in VALID_TRANSITIONS or payload.status not in VALID_TRANSITIONS.get(order.status, set()):
        raise HTTPException(status_code=400, detail=f"Cannot move order from {order.status} to {payload.status}")

    listing = db.get(CropListing, order.listing_id)
    is_owning_farmer = user.role == "farmer" and listing is not None and listing.farmer_id == user.id
    is_owning_distributor = user.role == "distributor" and order.distributor_id == user.id

    if payload.status in {"confirmed", "cancelled"} and not (is_owning_farmer or user.role == "admin"):
        raise HTTPException(status_code=403, detail="Only the listing's farmer can update this order")

    if payload.status == "delivered" and not (is_owning_distributor or user.role == "admin"):
        raise HTTPException(status_code=403, detail="Only the assigned distributor can mark this delivered")

    order.status = payload.status

    if payload.status == "in_transit":
        if user.role != "distributor":
            raise HTTPException(status_code=403, detail="Only a distributor can start transit")
        order.distributor_id = user.id
        buyer = db.get(User, order.buyer_id)
        shipment = Shipment(
            order_id=order.id,
            distributor_id=user.id,
            origin=listing.region if listing else "",
            destination=buyer.region if buyer else "",
            stage="in_transit",
            seed=order.id * 97 + 13,
        )
        db.add(shipment)

    if payload.status == "delivered":
        shipment = db.query(Shipment).filter(Shipment.order_id == order.id).first()
        if shipment:
            shipment.stage = "delivered"

    db.commit()
    db.refresh(order)
    return order
