"""F8 - analytics and the engine benchmark view."""
from __future__ import annotations

import pytest

from tests.helpers import import_sample, reset

RULES = {"adjacency": 8, "roll_gap": 5, "department_mix": True, "fill_strategy": "compact", "accessible_per_hall": 2}


@pytest.fixture(scope="module")
def plan(client, admin_headers):
    reset(client, admin_headers)
    import_sample(client, admin_headers)
    session = client.get("/api/sessions", headers=admin_headers).json()[0]
    plan = client.post(f"/api/sessions/{session['id']}/plans", headers=admin_headers, json={"rules": RULES, "seed": 8}).json()
    client.post(f"/api/plans/{plan['id']}/publish", headers=admin_headers)
    return plan


def test_overview(client, admin_headers, plan):
    data = client.get("/api/analytics/overview", headers=admin_headers).json()
    assert data["counts"]["published"] == 1 and data["counts"]["seated"] == plan["candidates"]
    assert data["totals"]["conflicts_avoided"] == plan["conflicts_avoided"] > 0
    assert data["totals"]["same_paper_pairs"] == 0 and data["totals"]["hard_ok_rate"] == 1
    assert len(data["sessions"]) == 6 and data["sessions"][0]["published_plan"]["id"] == plan["id"]
    assert data["hall_usage"] and data["attendance"]["total"] == plan["candidates"]


def test_plan_analytics(client, admin_headers, plan):
    data = client.get(f"/api/analytics/plans/{plan['id']}", headers=admin_headers).json()
    assert len(data["halls"]) == plan["halls_used"]
    same_paper = next(c for c in data["comparison"] if c["measure"] == "Same paper")
    assert same_paper["seatwise"] == 0 and same_paper["baseline"] > 0
    pairs = data["neighbour_pairs"]
    assert pairs["same_paper"] + pairs["same_department"] + pairs["mixed"] == pairs["total"]


def test_engine_benchmark_is_served(client, admin_headers):
    data = client.get("/api/analytics/engine", headers=admin_headers).json()
    assert data["available"] is True
    assert data["metrics"]["headline"]["all_hard_rules_satisfied"] is True
    assert data["profile"]["hall_budget"] > 0
    png = client.get(data["plots"][0], headers=admin_headers)
    assert png.status_code == 200 and png.content.startswith(b"\x89PNG")
    assert client.get("/api/analytics/engine/plots/..%2F..%2Fsecret.png", headers=admin_headers).status_code == 404


def test_invigilators_cannot_see_analytics(client, invigilator_headers):
    assert client.get("/api/analytics/overview", headers=invigilator_headers).status_code == 403
