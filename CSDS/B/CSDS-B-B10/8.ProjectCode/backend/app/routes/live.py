import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..auth import current_user, make_token, user_from_token
from ..db import SessionLocal, User
from ..services import cipher as C
from ..services.imaging import decode, list_sequences, sequence_frames
from ..services.live import Window, encrypt_frame, fit_width, ground_decode, hub, run_sender, unpack

router = APIRouter(prefix="/api/live", tags=["live"])


class StartIn(BaseModel):
    sequence: str
    key: str
    fps: float = 12
    width: int = 480


def _ws_user(token: str) -> User:
    with SessionLocal() as db:
        return user_from_token(token or "", db)


@router.get("/sequences")
def sequences(user: User = Depends(current_user)):
    return list_sequences()


@router.post("/start")
async def start(body: StartIn, user: User = Depends(current_user)):
    try:
        C.parse_key(body.key)
        sequence_frames(body.sequence)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not (1 <= body.fps <= 30) or not (64 <= body.width <= 1280):
        raise HTTPException(400, "FPS must be 1-30 and width 64-1280")
    ch = hub.channel(user.id)
    if ch.sender_task and not ch.sender_task.done():
        ch.sender_task.cancel()
        await asyncio.sleep(0.05)
    ch.sender_task = asyncio.create_task(run_sender(ch, make_token(user), body.sequence, body.key, body.fps, body.width - body.width % 2))
    return {"started": True}


@router.post("/stop")
async def stop(user: User = Depends(current_user)):
    ch = hub.channel(user.id)
    if ch.sender_task and not ch.sender_task.done():
        ch.sender_task.cancel()
    return {"stopped": True}


@router.get("/status")
def status(user: User = Depends(current_user)):
    ch = hub.channel(user.id)
    return {"sender": ch.sender_info, "uplink": ch.uplink_window.stats(), "ground_stations": len(ch.grounds)}


@router.websocket("/uplink")
async def uplink(ws: WebSocket, token: str = ""):
    """Receives ciphertext packets from a UAV sender and relays them to this operator's ground stations."""
    try:
        user = _ws_user(token)
    except HTTPException:
        await ws.close(code=4401)
        return
    await ws.accept()
    ch = hub.channel(user.id)
    try:
        while True:
            packet = await ws.receive_bytes()
            header, payload = unpack(packet)
            ch.uplink_window.add(len(payload), 0)
            ch.publish(packet)
    except WebSocketDisconnect:
        pass


@router.websocket("/ground")
async def ground(ws: WebSocket, token: str = ""):
    """Ground station: first message is {"key": "<hex>"}; then decrypted frames and link stats are pushed."""
    try:
        user = _ws_user(token)
    except HTTPException:
        await ws.close(code=4401)
        return
    await ws.accept()
    try:
        key = json.loads(await ws.receive_text()).get("key", "")
        C.parse_key(key)
    except Exception:
        await ws.send_json({"error": "Ground station needs a valid 256-bit key (64 hex characters)"})
        await ws.close()
        return
    ch = hub.channel(user.id)
    q: asyncio.Queue = asyncio.Queue(maxsize=2)
    ch.grounds.add(q)
    win = Window()
    await ws.send_json({"ready": True})
    try:
        while True:
            packet = await q.get()
            out = await asyncio.to_thread(ground_decode, packet, key)
            win.add(out["bytes"], out["latency_ms"])
            out.update(win.stats())
            await ws.send_json(out)
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        ch.grounds.discard(q)


@router.websocket("/camera")
async def camera(ws: WebSocket, token: str = ""):
    """UAV encoder fed by a webcam: first message {"key", "width"}, then JPEG frames; frames go out encrypted."""
    try:
        user = _ws_user(token)
    except HTTPException:
        await ws.close(code=4401)
        return
    await ws.accept()
    try:
        cfg = json.loads(await ws.receive_text())
        key = cfg.get("key", "")
        C.parse_key(key)
        width = int(cfg.get("width", 480))
    except Exception:
        await ws.send_json({"error": "Camera sender needs a valid 256-bit key"})
        await ws.close()
        return
    ch = hub.channel(user.id)
    i = 0
    try:
        while True:
            data = await ws.receive_bytes()
            img, _ = decode(data, limit=False)
            img = fit_width(img, width - width % 2)
            packet = await asyncio.to_thread(encrypt_frame, img, key, i, "webcam")
            i += 1
            header, payload = unpack(packet)
            ch.uplink_window.add(len(payload), 0)
            ch.publish(packet)
            await ws.send_json({"frame": i, "enc_ms": header["enc_ms"], "bytes": len(payload)})
    except WebSocketDisconnect:
        pass
