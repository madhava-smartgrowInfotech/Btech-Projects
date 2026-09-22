"""ESP32 sensor-node simulator: behaves like firmware/esp32_node over HTTP, for installations without hardware.

    python scripts/esp32_simulator.py --api http://127.0.0.1:8202

Each simulated node measures a community Wi-Fi link (RSSI, BLE beacon RSSI, round-trip latency, packet loss)
at a fixed location and posts to /api/ingest/node with its device key - exactly the firmware's JSON format.
Like the firmware, a node that loses its Wi-Fi keeps readings in a buffer and uploads them, with their
original timestamps, when the link returns. Values come from a seeded random process, so a run can be
reproduced with the same --seed. Node keys are read from data/runtime/simulator.json (written by the API).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import signal
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "data" / "runtime" / "simulator.json"
PROFILES = {
    # base Wi-Fi RSSI, fade sigma, base latency ms, loss, chance per tick of a link drop, drop length (ticks)
    "strong": {"rssi": -57.0, "sigma": 2.0, "latency": 32.0, "loss": 0.002, "drop": 0.002, "drop_len": (2, 4)},
    "weak": {"rssi": -76.0, "sigma": 3.5, "latency": 95.0, "loss": 0.03, "drop": 0.01, "drop_len": (2, 6)},
    "flaky": {"rssi": -68.0, "sigma": 4.0, "latency": 60.0, "loss": 0.05, "drop": 0.03, "drop_len": (4, 12)},
}
running = True


class Node:
    def __init__(self, spec: dict, seed: int):
        self.spec = spec
        self.p = PROFILES.get(spec.get("profile", "strong"), PROFILES["strong"])
        self.rng = np.random.default_rng(seed + 101 * spec["index"])
        self.seq = int(time.time()) % 1_000_000 * 10
        self.fade = 0.0
        self.down_ticks = 0
        self.buffer: list[dict] = []

    def measure(self) -> dict:
        now = datetime.now(timezone.utc)
        hour = datetime.now().hour
        busy = 1.0 + 0.6 * math.exp(-((hour - 20) ** 2) / 8.0)          # evening congestion
        self.fade = 0.8 * self.fade + self.rng.normal(0, self.p["sigma"])
        if self.down_ticks == 0 and self.rng.random() < self.p["drop"]:
            self.down_ticks = int(self.rng.integers(*self.p["drop_len"]))
        connected = self.down_ticks == 0
        if self.down_ticks:
            self.down_ticks -= 1
        self.seq += 1
        rssi = self.p["rssi"] + self.fade - 2.5 * (busy - 1)
        latency = self.p["latency"] * busy * float(self.rng.lognormal(0, 0.25))
        return {
            "seq": self.seq, "ts": now.isoformat(), "connected": connected,
            "wifi_rssi": round(float(np.clip(rssi, -95, -30)), 1) if connected else None,
            "ble_rssi": round(float(np.clip(rssi - 8 + self.rng.normal(0, 3), -100, -40)), 1),
            "latency_ms": round(latency, 1) if connected else None,
            "packet_loss": round(float(np.clip(self.p["loss"] * busy + self.rng.normal(0, 0.01), 0, 1)), 3) if connected else None,
        }


def post(api: str, key: str, body: dict) -> int:
    req = urllib.request.Request(f"{api}/api/ingest/node", data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "X-Device-Key": key})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return 0


def load_nodes(seed: int) -> dict[int, Node]:
    while running:
        if RUNTIME.exists():
            try:
                spec = json.loads(RUNTIME.read_text(encoding="utf-8"))
                return {n["id"]: Node(n, seed) for n in spec["nodes"]}
            except (json.JSONDecodeError, KeyError):
                pass
        time.sleep(2)
    return {}


def main() -> int:
    global running
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--api", default=f"http://127.0.0.1:{os.environ.get('BACKEND_PORT', '8202')}")
    ap.add_argument("--interval", type=float, default=None, help="seconds between readings (default from .env)")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    signal.signal(signal.SIGINT, lambda *_: globals().__setitem__("running", False))
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, lambda *_: globals().__setitem__("running", False))

    nodes = load_nodes(args.seed)
    if not nodes:
        return 0
    interval = args.interval or float(next(iter(nodes.values())).spec.get("interval_s", 15))
    print(f"simulating {len(nodes)} sensor node(s) every {interval:.0f} s: " + ", ".join(n.spec["name"] for n in nodes.values()), flush=True)
    tick = 0
    while running:
        tick += 1
        sent = 0
        for node in list(nodes.values()):
            reading = node.measure()
            node.buffer.append(reading)
            node.buffer = node.buffer[-500:]                  # the firmware's ring buffer size
            if not reading["connected"]:
                continue                                     # link down: keep buffering
            body = {"firmware": "sim-1.0", "uptime_s": tick * int(interval), "network_name": node.spec["network_name"], "readings": node.buffer}
            status = post(args.api, node.spec["key"], body)
            if status == 200:
                if len(node.buffer) > 1:
                    print(f"{node.spec['name']}: link back - uploaded {len(node.buffer)} buffered readings", flush=True)
                sent += len(node.buffer)
                node.buffer = []
            elif status == 401:                              # the API restarted and rotated keys
                nodes = load_nodes(args.seed)
                break
        if tick % 20 == 1:
            print(f"tick {tick}: {sent} reading(s) delivered", flush=True)
        deadline = time.time() + interval
        while running and time.time() < deadline:
            time.sleep(0.5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
