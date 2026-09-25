from datetime import datetime

from pydantic import BaseModel


class OrderCreate(BaseModel):
    listing_id: int
    quantity_kg: float
    agreed_price: float


class OrderOut(BaseModel):
    id: int
    listing_id: int
    buyer_id: int
    distributor_id: int | None
    quantity_kg: float
    agreed_price: float
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: str
