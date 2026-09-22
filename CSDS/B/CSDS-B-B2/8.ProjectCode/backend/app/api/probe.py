"""Endpoints the phone probe measures against: latency ping, speed-test payloads, and carrier detection."""
from __future__ import annotations

import os
import time

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.db import get_db
from ..core.security import get_current_device
from ..models import Device
from ..services import settings_service
from ..services.carrier import client_ip, lookup

router = APIRouter(prefix="/api/probe", tags=["phone probe"])
NO_STORE = {"Cache-Control": "no-store, no-transform", "Pragma": "no-cache"}
_BLOCK = os.urandom(1 << 20)          # 1 MiB of random bytes - incompressible, so proxies cannot shrink it
MAX_DOWNLOAD = 5_000_000
MAX_UPLOAD = 2_000_000


@router.get("/ping", summary="Tiny response for round-trip timing (no auth, never cached)")
def ping() -> JSONResponse:
    return JSONResponse({"t": int(time.time() * 1000)}, headers=NO_STORE)


@router.get("/download", summary="Random bytes for the download speed test")
def download(bytes: int = Query(250_000, ge=10_000, le=MAX_DOWNLOAD), device: Device = Depends(get_current_device)) -> Response:
    n = min(bytes, MAX_DOWNLOAD)
    body = (_BLOCK * (n // len(_BLOCK) + 1))[:n]
    return Response(body, media_type="application/octet-stream", headers={**NO_STORE, "Content-Length": str(n), "Content-Encoding": "identity"})


@router.post("/upload", summary="Accepts random bytes for the upload speed test")
async def upload(request: Request, device: Device = Depends(get_current_device)) -> JSONResponse:
    start = time.perf_counter()
    received = 0
    async for chunk in request.stream():
        received += len(chunk)
        if received > MAX_UPLOAD:
            break
    return JSONResponse({"bytes": received, "server_ms": round((time.perf_counter() - start) * 1000, 1)}, headers=NO_STORE)


@router.get("/whoami", summary="Detected carrier and link type for this phone, plus the probe settings")
def whoami(request: Request, device: Device = Depends(get_current_device), db: Session = Depends(get_db)) -> dict:
    ip = client_ip(dict(request.headers), request.client.host if request.client else None)
    info = lookup(ip)
    cfg = settings_service.get_all(db)
    masked = None
    if info.ip and "." in info.ip:
        masked = ".".join(info.ip.split(".")[:2] + ["x", "x"])
    return {
        "device": {"id": device.id, "name": device.name},
        "carrier": {"operator": info.operator, "network_name": info.display_name, "asn": info.asn, "kind": info.kind, "ip": masked},
        "config": {
            "interval_s": settings.probe_interval_s,
            "speedtest_interval_s": settings.probe_speedtest_interval_s,
            "speedtest_max_bytes": settings.probe_speedtest_max_bytes,
            "weak_rtt_ms": cfg["probe_weak_rtt_ms"],
            "weak_dl_mbps": cfg["probe_weak_dl_mbps"],
        },
    }
