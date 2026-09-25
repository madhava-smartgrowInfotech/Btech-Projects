import json

from fastapi import WebSocket


class TrackingConnectionManager:
    """Keeps guardian WebSocket viewers grouped by emergency-session share token
    and broadcasts location updates pushed by the session owner."""

    def __init__(self):
        self._viewers: dict[str, set[WebSocket]] = {}

    async def add_viewer(self, share_token: str, ws: WebSocket):
        await ws.accept()
        self._viewers.setdefault(share_token, set()).add(ws)

    def remove_viewer(self, share_token: str, ws: WebSocket):
        conns = self._viewers.get(share_token)
        if conns and ws in conns:
            conns.remove(ws)
            if not conns:
                self._viewers.pop(share_token, None)

    async def broadcast(self, share_token: str, payload: dict):
        conns = list(self._viewers.get(share_token, set()))
        message = json.dumps(payload)
        for ws in conns:
            try:
                await ws.send_text(message)
            except Exception:
                self.remove_viewer(share_token, ws)


manager = TrackingConnectionManager()
