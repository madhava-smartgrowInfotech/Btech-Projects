from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..ws_manager import manager

router = APIRouter()


@router.websocket("/ws/track/{share_token}")
async def ws_track(websocket: WebSocket, share_token: str):
    """Guardian tracking page connects here to receive live location pushes."""
    await manager.add_viewer(share_token, websocket)
    try:
        while True:
            # Guardians don't send anything; just keep the connection open.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.remove_viewer(share_token, websocket)
