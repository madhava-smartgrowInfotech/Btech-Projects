import asyncio

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.security import get_current_user
from app.ml.iot.simulate import ShipmentSensorState
from app.models.iot import SensorReading, Shipment
from app.models.order import Order
from app.models.user import User
from app.schemas.iot import SensorReadingOut, ShipmentOut

router = APIRouter(prefix="/api/iot", tags=["iot"])


@router.get("/shipments", response_model=list[ShipmentOut])
def list_shipments(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Shipment).filter(Shipment.stage == "in_transit")
    if user.role == "distributor":
        query = query.filter(Shipment.distributor_id == user.id)
    return query.order_by(Shipment.created_at.desc()).all()


@router.get("/shipments/{shipment_id}/history", response_model=list[SensorReadingOut])
def shipment_history(shipment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    shipment = db.get(Shipment, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return (
        db.query(SensorReading)
        .filter(SensorReading.shipment_id == shipment_id)
        .order_by(SensorReading.recorded_at.desc())
        .limit(60)
        .all()
    )


@router.websocket("/ws/iot/{shipment_id}")
async def ws_iot(websocket: WebSocket, shipment_id: int):
    await websocket.accept()
    db = SessionLocal()
    try:
        shipment = db.get(Shipment, shipment_id)
        if not shipment:
            await websocket.close(code=4004)
            return
        state = ShipmentSensorState(seed=shipment.seed or shipment_id)
        while True:
            reading = state.step()
            row = SensorReading(shipment_id=shipment_id, **reading)
            db.add(row)
            db.commit()
            await websocket.send_json(reading)
            await asyncio.sleep(1.4)
    except WebSocketDisconnect:
        pass
    finally:
        db.close()
