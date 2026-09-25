from datetime import datetime

from pydantic import BaseModel


class SensorReadingOut(BaseModel):
    temperature_c: float
    humidity_pct: float
    shock_g: float
    is_anomaly: bool
    recorded_at: datetime

    class Config:
        from_attributes = True


class ShipmentOut(BaseModel):
    id: int
    origin: str
    destination: str
    stage: str
    order_id: int | None

    class Config:
        from_attributes = True
