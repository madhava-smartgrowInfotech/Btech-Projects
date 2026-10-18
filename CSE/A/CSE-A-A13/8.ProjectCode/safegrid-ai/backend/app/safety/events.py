"""Immutable-style, hash-chained safety event records (tamper-evident audit trail)."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

GENESIS = "0" * 64


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


@dataclass(frozen=True)
class SafetyEvent:
    event_id: int
    run_id: str
    step: int
    sim_time: str
    wall_time: str  # informational, excluded from the hash so reruns are comparable
    payload_json: str
    prev_hash: str
    hash: str

    @staticmethod
    def create(event_id: int, run_id: str, step: int, sim_time: str, wall_time: str,
               payload: dict[str, Any], prev_hash: str) -> "SafetyEvent":
        body = _canonical(payload)
        digest = hashlib.sha256((prev_hash + _canonical([event_id, run_id, step, sim_time]) + body).encode()).hexdigest()
        return SafetyEvent(event_id, run_id, step, sim_time, wall_time, body, prev_hash, digest)

    @property
    def payload(self) -> dict[str, Any]:
        return json.loads(self.payload_json)

    def to_dict(self) -> dict[str, Any]:
        d = {"event_id": self.event_id, "run_id": self.run_id, "step": self.step, "sim_time": self.sim_time,
             "timestamp": self.wall_time, "prev_hash": self.prev_hash, "hash": self.hash}
        d.update(self.payload)
        return d


def verify_chain(events: list[SafetyEvent]) -> bool:
    prev = GENESIS
    for e in events:
        expect = hashlib.sha256((prev + _canonical([e.event_id, e.run_id, e.step, e.sim_time]) + e.payload_json).encode()).hexdigest()
        if e.prev_hash != prev or e.hash != expect:
            return False
        prev = e.hash
    return True


def fingerprint(events: list[SafetyEvent]) -> str:
    return events[-1].hash if events else GENESIS
