"""Shared helpers: reset the workspace and import the committed sample data."""
from __future__ import annotations

from pathlib import Path

from app.core.config import DATA_DIR

SAMPLE = DATA_DIR / "sample"


def reset(client, headers) -> None:
    response = client.post("/api/settings/reset-workspace", json={"confirm": "RESET"}, headers=headers)
    assert response.status_code == 200, response.text


def upload(client, headers, kind: str, name: str, content: bytes, mode: str = "update"):
    return client.post(f"/api/imports/{kind}/validate", headers=headers, data={"mode": mode},
                       files={"file": (name, content)})


def import_sample(client, headers) -> dict:
    path: Path = SAMPLE / "seatwise_sample_workbook.xlsx"
    checked = upload(client, headers, "workbook", path.name, path.read_bytes())
    assert checked.status_code == 200, checked.text
    body = checked.json()
    assert body["report"]["errors"] == 0, body["report"]["issues"][:5]
    committed = client.post(f"/api/imports/{body['id']}/commit", headers=headers)
    assert committed.status_code == 200, committed.text
    return committed.json()


def csv_bytes(header: str, *rows: str) -> bytes:
    return ("\n".join([header, *rows]) + "\n").encode()
