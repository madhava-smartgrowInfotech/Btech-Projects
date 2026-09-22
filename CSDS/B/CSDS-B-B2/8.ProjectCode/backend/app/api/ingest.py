from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..core.db import get_db, utcnow
from ..core.security import get_current_device
from ..models import Device
from ..schemas.readings import IngestBatch, IngestResult, NodeBatch, ReadingIn
from ..services.carrier import client_ip, lookup
from ..services.ingest import ingest

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])


@router.post("/readings", response_model=IngestResult, summary="Upload a batch of readings (phones, replays) - idempotent by client_uuid")
def ingest_readings(body: IngestBatch, request: Request, device: Device = Depends(get_current_device), db: Session = Depends(get_db)) -> IngestResult:
    carrier = lookup(client_ip(dict(request.headers), request.client.host if request.client else None)) if device.kind == "phone" else None
    return ingest(db, device, body.readings, carrier).result


@router.post("/node", response_model=IngestResult, summary="Upload buffered readings from an ESP32 node (compact format)")
def ingest_node(body: NodeBatch, device: Device = Depends(get_current_device), db: Session = Depends(get_db)) -> IngestResult:
    if device.kind not in ("esp32", "simulator"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="This endpoint is for sensor nodes; phones use /api/ingest/readings")
    now = utcnow()
    items: list[ReadingIn] = []
    for r in body.readings:
        lat, lon = (r.lat, r.lon) if r.lat is not None and r.lon is not None else (device.fixed_lat, device.fixed_lon)
        if lat is None or lon is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="The node sent no GPS position and has no fixed location - set one on the Devices page")
        ts = r.ts or now
        items.append(ReadingIn(
            client_uuid=f"node-{device.id}-{r.seq}-{int(ts.timestamp())}", ts=ts, lat=lat, lon=lon,
            accuracy_m=None if r.lat is not None else 5.0, connected=r.connected,
            wifi_rssi=r.wifi_rssi, ble_rssi=r.ble_rssi, latency_ms=r.latency_ms, packet_loss=r.packet_loss,
            rssi=r.cell_rssi, network_type=r.cell_type if r.cell_rssi is not None else None,
        ))
    config = dict(device.config or {})
    if body.network_name:
        config["network_name"] = body.network_name
    if body.uptime_s is not None:
        config["uptime_s"] = body.uptime_s
    device.config = config
    if body.firmware:
        device.firmware = body.firmware
    return ingest(db, device, items).result
