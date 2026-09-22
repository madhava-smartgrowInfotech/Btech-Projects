from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.db import get_db, utcnow
from ..core.security import get_current_user, has_role, new_device_key
from ..models import Device, SyncBatch, User
from ..schemas.devices import DeviceCreate, DeviceOut, DeviceUpdate, DeviceWithKey, PhonePair, SyncBatchOut

router = APIRouter(prefix="/api/devices", tags=["devices"])
ONLINE_WINDOW = {"phone": timedelta(minutes=2), "esp32": timedelta(minutes=3), "simulator": timedelta(minutes=3), "replay": timedelta(0)}


def device_out(d: Device, owner: User | None = None) -> DeviceOut:
    out = DeviceOut.model_validate(d)
    out.owner_name = owner.name if owner else None
    window = ONLINE_WINDOW.get(d.kind, timedelta(minutes=3))
    out.online = bool(d.is_active and d.last_seen_at and utcnow() - d.last_seen_at <= window)
    return out


def _get_owned(db: Session, device_id: int, user: User) -> Device:
    d = db.get(Device, device_id)
    if not d or (d.owner_id != user.id and not has_role(user, "admin")):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Device not found")
    return d


@router.get("", response_model=list[DeviceOut])
def list_devices(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[DeviceOut]:
    q = db.query(Device, User).join(User, User.id == Device.owner_id)
    if not has_role(user, "engineer"):
        q = q.filter(Device.owner_id == user.id)
    return [device_out(d, u) for d, u in q.order_by(Device.created_at.desc()).all()]


@router.post("", response_model=DeviceWithKey, status_code=201)
def create_device(body: DeviceCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DeviceWithKey:
    if (body.fixed_lat is None) != (body.fixed_lon is None):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Give both latitude and longitude, or neither")
    key, key_hash, prefix = new_device_key()
    d = Device(owner_id=user.id, kind=body.kind, name=body.name.strip(), api_key_hash=key_hash, api_key_prefix=prefix,
               fixed_lat=body.fixed_lat, fixed_lon=body.fixed_lon, config={"network_name": body.network_name} if body.network_name else {})
    db.add(d)
    db.commit()
    db.refresh(d)
    return DeviceWithKey(device=device_out(d, user), api_key=key)


@router.post("/phone", response_model=DeviceWithKey, status_code=201)
def pair_phone(body: PhonePair, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DeviceWithKey:
    """Called by the phone probe after sign-in: registers this phone and returns its key (stored in the browser)."""
    key, key_hash, prefix = new_device_key()
    count = db.query(Device).filter(Device.owner_id == user.id, Device.kind == "phone").count()
    d = Device(owner_id=user.id, kind="phone", name=(body.name or f"{user.name.split()[0]}'s phone {count + 1}").strip()[:120],
               api_key_hash=key_hash, api_key_prefix=prefix, hardware=body.hardware, config={})
    db.add(d)
    db.commit()
    db.refresh(d)
    return DeviceWithKey(device=device_out(d, user), api_key=key)


@router.patch("/{device_id}", response_model=DeviceOut)
def update_device(device_id: int, body: DeviceUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DeviceOut:
    d = _get_owned(db, device_id, user)
    data = body.model_dump(exclude_unset=True)
    if "name" in data:
        d.name = data["name"].strip()
    if "fixed_lat" in data or "fixed_lon" in data:
        lat, lon = data.get("fixed_lat", d.fixed_lat), data.get("fixed_lon", d.fixed_lon)
        if (lat is None) != (lon is None):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Give both latitude and longitude, or neither")
        d.fixed_lat, d.fixed_lon = lat, lon
    if "network_name" in data:
        d.config = {**(d.config or {}), "network_name": data["network_name"]}
    if "is_active" in data:
        d.is_active = data["is_active"]
    db.commit()
    db.refresh(d)
    return device_out(d, db.get(User, d.owner_id))


@router.post("/{device_id}/rotate-key", response_model=DeviceWithKey)
def rotate_key(device_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DeviceWithKey:
    d = _get_owned(db, device_id, user)
    key, key_hash, prefix = new_device_key()
    d.api_key_hash, d.api_key_prefix = key_hash, prefix
    db.commit()
    db.refresh(d)
    return DeviceWithKey(device=device_out(d, db.get(User, d.owner_id)), api_key=key)


@router.delete("/{device_id}", status_code=204)
def delete_device(device_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    d = _get_owned(db, device_id, user)
    if d.kind == "replay":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Sample data is removed from Settings, not here")
    db.delete(d)
    db.commit()


@router.get("/{device_id}/sync", response_model=list[SyncBatchOut])
def sync_history(device_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[SyncBatch]:
    d = _get_owned(db, device_id, user) if not has_role(user, "engineer") else db.get(Device, device_id)
    if not d:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Device not found")
    return db.query(SyncBatch).filter(SyncBatch.device_id == d.id).order_by(SyncBatch.ts.desc()).limit(50).all()
