"""Append-only, hash-chained audit records."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


GENESIS_HASH = "0" * 64


def _canonical(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


class AuditLedger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise ValueError(f"Invalid audit JSON on line {line_number}") from error
        return records

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        records = self.read_all()
        previous_hash = records[-1]["record_hash"] if records else GENESIS_HASH
        record = dict(event)
        record["sequence"] = len(records) + 1
        record["previous_hash"] = previous_hash
        record_hash = hashlib.sha256(f"{previous_hash}|{_canonical(record)}".encode("utf-8")).hexdigest()
        record["record_hash"] = record_hash
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        return record

    def verify(self) -> tuple[bool, str]:
        previous_hash = GENESIS_HASH
        try:
            records = self.read_all()
        except ValueError as error:
            return False, str(error)
        for expected_sequence, record in enumerate(records, start=1):
            stored_hash = record.get("record_hash", "")
            payload = {key: value for key, value in record.items() if key != "record_hash"}
            calculated = hashlib.sha256(f"{previous_hash}|{_canonical(payload)}".encode("utf-8")).hexdigest()
            if record.get("sequence") != expected_sequence:
                return False, f"Sequence mismatch at record {expected_sequence}"
            if record.get("previous_hash") != previous_hash or stored_hash != calculated:
                return False, f"Hash-chain verification failed at record {expected_sequence}"
            previous_hash = stored_hash
        return True, f"Verified {len(records)} audit record(s)"

