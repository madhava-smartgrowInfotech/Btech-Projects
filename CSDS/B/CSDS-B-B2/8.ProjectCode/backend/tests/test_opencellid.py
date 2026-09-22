"""OpenCelliD tower lookup: off without a key; with a key, nearest-first, serving cells marked, areas cached."""
from __future__ import annotations

from app.services import opencellid


def _complaint(client, headers, lat, lon):
    r = client.post("/api/complaints", headers=headers, json={"lat": lat, "lon": lon, "operator": "Vi", "note": "No signal at the bus stop"})
    assert r.status_code == 201
    return r.json()["id"]


def test_towers_off_without_key(client, user_headers, monkeypatch):
    monkeypatch.setattr(opencellid, "api_key", lambda: "")
    cid = _complaint(client, user_headers, 19.0760, 72.8777)
    r = client.get(f"/api/complaints/{cid}/towers", headers=user_headers)
    assert r.status_code == 200 and r.json() == {"enabled": False, "towers": []}


def test_towers_nearest_first_and_cached(client, user_headers, monkeypatch):
    monkeypatch.setattr(opencellid, "api_key", lambda: "test-key")
    lat, lon = 19.1000, 72.9000
    calls = []

    def fake_fetch(box):
        calls.append(box)
        assert box[0] < lat < box[2] and box[1] < lon < box[3]
        return [
            {"radio": "LTE", "mcc": 404, "mnc": 45, "lac": 11, "cellid": 501, "lat": lat + 0.006, "lon": lon, "range": 900},   # ~670 m
            {"radio": "GSM", "mcc": 404, "mnc": 45, "lac": 11, "cellid": 502, "lat": lat + 0.002, "lon": lon, "range": ""},    # ~220 m
            {"radio": "LTE", "mcc": 404, "mnc": 45, "lac": 11, "cellid": 503, "lat": lat + 0.05, "lon": lon},                  # outside 1 km
            {"radio": "LTE", "mcc": 404, "mnc": 45, "lac": 11, "lat": lat, "lon": lon},                                         # no cell id: skipped
        ]

    monkeypatch.setattr(opencellid, "_fetch", fake_fetch)
    cid = _complaint(client, user_headers, lat, lon)
    body = client.get(f"/api/complaints/{cid}/towers", headers=user_headers).json()
    assert body["enabled"] is True
    assert [t["cell"] for t in body["towers"]] == [502, 501]
    # distances are from the zone centre (the H3 cell), which is within ~200 m of the reported point
    assert body["towers"][0]["distance_m"] < body["towers"][1]["distance_m"] <= 1000 and body["towers"][1]["range_m"] == 900
    assert not any(t["serving"] for t in body["towers"])
    client.get(f"/api/complaints/{cid}/towers", headers=user_headers)
    assert len(calls) == 1, "the area should be served from the cache the second time"


def test_towers_api_error_is_reported(client, user_headers, monkeypatch):
    monkeypatch.setattr(opencellid, "api_key", lambda: "test-key")

    def failing(box):
        raise opencellid.OpenCellIdError("OpenCelliD: Invalid token")

    monkeypatch.setattr(opencellid, "_fetch", failing)
    cid = _complaint(client, user_headers, 12.9716, 77.5946)
    body = client.get(f"/api/complaints/{cid}/towers", headers=user_headers).json()
    assert body["enabled"] is True and body["towers"] == [] and "Invalid token" in body["error"]
