"""F7 - public seat lookup and QR slips."""
from __future__ import annotations

import pytest

from app.api import public
from tests.helpers import import_sample, reset

RULES = {"adjacency": 8, "roll_gap": 5, "department_mix": True, "fill_strategy": "compact", "accessible_per_hall": 2}


@pytest.fixture(scope="module")
def plans(client, admin_headers):
    reset(client, admin_headers)
    import_sample(client, admin_headers)
    sessions = client.get("/api/sessions", headers=admin_headers).json()
    published = client.post(f"/api/sessions/{sessions[0]['id']}/plans", headers=admin_headers,
                            json={"rules": RULES, "seed": 5}).json()
    client.post(f"/api/plans/{published['id']}/publish", headers=admin_headers)
    draft = client.post(f"/api/sessions/{sessions[1]['id']}/plans", headers=admin_headers,
                        json={"rules": RULES, "seed": 6}).json()
    hall = published["halls"][0]
    seat = client.get(f"/api/plans/{published['id']}/halls/{hall['hall_id']}", headers=admin_headers).json()["seats"][0]
    return {"published": published, "draft": draft, "seat": seat, "hall": hall}


def test_lookup_shows_published_seat_only(client, plans):
    roll = plans["seat"]["candidate"]["roll_no"]
    result = client.get(f"/api/public/lookup/{roll.lower()}").json()   # IDs are case-insensitive, no sign-in
    assert result["candidate"]["roll_no"] == roll
    assert result["candidate"]["name"].endswith(".")                 # shortened name only
    assert [s["plan_id"] for s in result["seats"]] == [plans["published"]["id"]]
    seat = result["seats"][0]
    assert seat["seat"]["label"] == plans["seat"]["label"] and seat["hall"]["code"] == plans["hall"]["code"]
    assert "email" not in str(result) and "date_of_birth" not in str(result)


def test_unknown_id_and_unpublished_plan(client, plans):
    assert client.get("/api/public/lookup/NOPE0000").status_code == 404
    roll = plans["seat"]["candidate"]["roll_no"]
    assert client.get(f"/api/public/slip/{roll}/{plans['draft']['id']}.pdf").status_code == 404


def test_slip_and_qr(client, plans):
    roll = plans["seat"]["candidate"]["roll_no"]
    pdf = client.get(f"/api/public/slip/{roll}/{plans['published']['id']}.pdf")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    png = client.get(f"/api/public/qr/{roll}.png")
    assert png.status_code == 200 and png.content.startswith(b"\x89PNG")


def test_engine_summary_for_the_home_page(client):
    summary = client.get("/api/public/engine-summary").json()
    assert summary["available"] is True
    assert summary["same_paper_pairs"] == 0 and summary["conflicts_avoided"] > 0 and summary["runs"] > 0


def test_lookups_are_rate_limited(client, plans, monkeypatch):
    monkeypatch.setattr(public, "_limiter", public.RateLimiter(3))
    roll = plans["seat"]["candidate"]["roll_no"]
    codes = [client.get(f"/api/public/lookup/{roll}").status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]
