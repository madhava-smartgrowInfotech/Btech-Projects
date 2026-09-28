"""Live UAV link.

UAV sender node  --(WebSocket uplink, ciphertext only)-->  hub  -->  ground-station node(s)
The sender encrypts every frame with a fresh nonce; each ground station decrypts with its own copy of the key.
Packet = 4-byte big-endian header length | JSON header | raw cipher bytes.
"""
import asyncio
import base64
import json
import os
import struct
import time
from collections import deque

import cv2
import numpy as np

from . import cipher as C
from .imaging import jpg_bytes, read_path, sequence_frames


def pack(header: dict, payload: bytes) -> bytes:
    h = json.dumps(header).encode()
    return struct.pack(">I", len(h)) + h + payload


def unpack(msg: bytes):
    n = struct.unpack(">I", msg[:4])[0]
    return json.loads(msg[4:4 + n]), msg[4 + n:]


def encrypt_frame(frame: np.ndarray, key: str, seq_no: int, source: str) -> bytes:
    nonce = C.new_nonce()
    t0 = time.time()
    enc = C.encrypt(frame, key, nonce)
    enc_ms = (time.time() - t0) * 1000
    header = {"frame": seq_no, "nonce": nonce, "shape": list(frame.shape), "t_capture": t0 * 1000,
              "enc_ms": enc_ms, "key_fp": C.key_fingerprint(key), "source": source}
    return pack(header, enc.tobytes())


def fit_width(img: np.ndarray, width: int) -> np.ndarray:
    if img.shape[1] == width:
        return img
    h = max(2, round(img.shape[0] * width / img.shape[1]))
    return cv2.resize(img, (width, h), interpolation=cv2.INTER_AREA)


class Window:
    """Rolling 2-second window for FPS / throughput / latency."""

    def __init__(self):
        self.items = deque()

    def add(self, nbytes, latency):
        now = time.time()
        self.items.append((now, nbytes, latency))
        while self.items and now - self.items[0][0] > 2.0:
            self.items.popleft()

    def stats(self):
        if len(self.items) < 2:
            return {"fps": 0.0, "throughput_mbps": 0.0, "latency_ms": self.items[-1][2] if self.items else 0.0}
        span = max(self.items[-1][0] - self.items[0][0], 1e-6)
        return {"fps": (len(self.items) - 1) / span,
                "throughput_mbps": sum(i[1] for i in list(self.items)[1:]) * 8 / 1e6 / span,
                "latency_ms": float(np.mean([i[2] for i in self.items]))}


class Channel:
    def __init__(self):
        self.grounds = set()        # asyncio.Queue per ground station
        self.sender_task = None
        self.sender_info = {}
        self.uplink_window = Window()

    def publish(self, packet: bytes):
        for q in list(self.grounds):
            if q.full():
                try:
                    q.get_nowait()   # drop the oldest frame - live video prefers fresh frames
                except asyncio.QueueEmpty:
                    pass
            q.put_nowait(packet)


class Hub:
    def __init__(self):
        self.channels = {}

    def channel(self, user_id: int) -> Channel:
        return self.channels.setdefault(user_id, Channel())


hub = Hub()


def ground_decode(packet: bytes, key: str) -> dict:
    header, payload = unpack(packet)
    enc = np.frombuffer(payload, np.uint8).reshape(header["shape"])
    t0 = time.time()
    dec = C.decrypt(enc, key, header["nonce"])
    dec_ms = (time.time() - t0) * 1000
    small = fit_width(enc, min(320, enc.shape[1]))
    return {
        "frame": header["frame"], "source": header["source"],
        "width": int(enc.shape[1]), "height": int(enc.shape[0]),
        "enc_ms": header["enc_ms"], "dec_ms": dec_ms,
        "latency_ms": time.time() * 1000 - header["t_capture"],
        "bytes": len(payload), "key_match": header["key_fp"] == C.key_fingerprint(key),
        "cipher": "data:image/jpeg;base64," + base64.b64encode(jpg_bytes(small, 70)).decode(),
        "plain": "data:image/jpeg;base64," + base64.b64encode(jpg_bytes(dec, 82)).decode(),
    }


async def run_sender(ch: Channel, user_token: str, sequence: str, key: str, fps: float, width: int):
    """Built-in UAV sender: reads a drone sequence, encrypts each frame and streams it over the uplink."""
    from websockets.asyncio.client import connect

    frames = sequence_frames(sequence)
    port = int(os.getenv("BACKEND_PORT", "8210"))
    url = f"ws://127.0.0.1:{port}/api/live/uplink?token={user_token}"
    info = ch.sender_info
    info.update({"running": True, "sequence": sequence, "frames_sent": 0, "error": None, "width": width,
                 "target_fps": fps})
    period = 1.0 / fps
    try:
        async with connect(url, max_size=None) as ws:
            i = 0
            while True:
                t0 = time.time()
                img, _ = await asyncio.to_thread(read_path, frames[i % len(frames)], False)
                img = fit_width(img, width)
                packet = await asyncio.to_thread(encrypt_frame, img, key, i, f"{sequence}/{frames[i % len(frames)].name}")
                await ws.send(packet)
                i += 1
                info["frames_sent"] = i
                info["last_enc_ms"] = unpack(packet)[0]["enc_ms"]
                info["bytes_per_frame"] = len(packet)
                await asyncio.sleep(max(0.0, period - (time.time() - t0)))
    except asyncio.CancelledError:
        pass
    except Exception as e:  # surfaced in the UI through /status
        info["error"] = str(e)
    finally:
        info["running"] = False
