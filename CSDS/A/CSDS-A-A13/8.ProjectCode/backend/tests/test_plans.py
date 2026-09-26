"""F2/F3/F4 - plan generation, audit and reproducibility, hall maps and manual moves."""
from __future__ import annotations

import pytest

from tests.helpers import import_sample, reset

RULES = {"adjacency": 8, "roll_gap": 5, "department_mix": True, "fill_strategy": "compact", "accessible_per_hall": 2}


@pytest.fixture(scope="module")
def world(client, admin_headers):
    reset(client, admin_headers)
    import_sample(client, admin_headers)
    sessions = client.get("/api/sessions", headers=admin_headers).json()
    first = client.post(f"/api/sessions/{sessions[0]['id']}/plans", headers=admin_headers,
                        json={"rules": RULES, "seed": 12345})
    assert first.status_code == 201, first.text
    return {"sessions": sessions, "plan": first.json()}


def test_generated_plan_meets_every_rule(world):
    plan = world["plan"]
    assert plan["hard_ok"] is True
    assert plan["same_paper_pairs"] == 0 and plan["roll_gap_violations"] == 0 and plan["accessible_violations"] == 0
    assert plan["candidates"] == world["sessions"][0]["candidates"]
    assert plan["conflicts_avoided"] > 500
    assert plan["solve_ms"] < 30_000
    assert all(h["invigilators"] for h in plan["halls"])
    assert plan["status"] == "draft" and plan["version"] == 1


def test_same_seed_gives_same_plan_and_verify_confirms(client, admin_headers, world):
    session_id = world["sessions"][0]["id"]
    again = client.post(f"/api/sessions/{session_id}/plans", headers=admin_headers, json={"rules": RULES, "seed": 12345})
    assert again.status_code == 201
    assert again.json()["solver_hash"] == world["plan"]["solver_hash"]
    assert again.json()["version"] == 2
    verdict = client.post(f"/api/plans/{world['plan']['id']}/verify", headers=admin_headers).json()
    assert verdict["reproduced"] is True and verdict["data_unchanged"] is True
    other = client.post(f"/api/sessions/{session_id}/plans", headers=admin_headers, json={"rules": RULES, "seed": 999})
    assert other.json()["solver_hash"] != world["plan"]["solver_hash"]


def test_publish_replaces_previous_version(client, admin_headers, world):
    session_id = world["sessions"][0]["id"]
    versions = client.get(f"/api/sessions/{session_id}/plans", headers=admin_headers).json()
    oldest, newest = versions[-1], versions[0]
    assert client.post(f"/api/plans/{oldest['id']}/publish", headers=admin_headers).json()["status"] == "published"
    assert client.post(f"/api/plans/{newest['id']}/publish", headers=admin_headers).json()["status"] == "published"
    statuses = {p["id"]: p["status"] for p in client.get(f"/api/sessions/{session_id}/plans", headers=admin_headers).json()}
    assert statuses[oldest["id"]] == "archived" and statuses[newest["id"]] == "published"
    assert client.delete(f"/api/plans/{newest['id']}", headers=admin_headers).status_code == 409
    assert client.delete(f"/api/plans/{oldest['id']}", headers=admin_headers).status_code == 204


def _published(client, headers, world):
    session_id = world["sessions"][0]["id"]
    plans = client.get(f"/api/sessions/{session_id}/plans", headers=headers).json()
    return next(p for p in plans if p["status"] == "published")


def test_hall_map_and_moves_follow_the_rules(client, admin_headers, world):
    plan = client.get(f"/api/plans/{_published(client, admin_headers, world)['id']}", headers=admin_headers).json()
    hall = plan["halls"][0]
    view = client.get(f"/api/plans/{plan['id']}/halls/{hall['hall_id']}", headers=admin_headers).json()
    assert len(view["seats"]) == hall["placed"]
    assert view["violations"] == []
    seat = view["seats"][0]["label"]
    options = client.get(f"/api/plans/{plan['id']}/halls/{hall['hall_id']}/swap-check",
                         params={"seat": seat}, headers=admin_headers).json()
    bad = next(t for t in options["targets"] if not t["ok"] and any("both write" in r for r in t["reasons"]))
    blocked = client.post(f"/api/plans/{plan['id']}/swap", headers=admin_headers,
                          json={"hall_id": hall["hall_id"], "from_seat": seat, "to_seat": bad["seat"]})
    assert blocked.status_code == 409
    assert "both write" in blocked.json()["detail"]
    good = next(t for t in options["targets"] if t["ok"])
    moved = client.post(f"/api/plans/{plan['id']}/swap", headers=admin_headers,
                        json={"hall_id": hall["hall_id"], "from_seat": seat, "to_seat": good["seat"]})
    assert moved.status_code == 200, moved.text
    assert moved.json()["hard_ok"] is True
    after = client.get(f"/api/plans/{plan['id']}", headers=admin_headers).json()
    assert after["swaps"] == 1 and after["assignment_hash"] != plan["assignment_hash"]
    assert after["solver_hash"] == plan["solver_hash"]
    trail = client.get("/api/audit", params={"plan_id": plan["id"]}, headers=admin_headers).json()
    assert any(e["action"] == "plan.seat_moved" for e in trail)


def test_invigilators_only_see_their_halls(client, admin_headers, invigilator_headers, world):
    plan = client.get(f"/api/plans/{_published(client, admin_headers, world)['id']}", headers=admin_headers).json()
    me = client.get("/api/auth/me", headers=invigilator_headers).json()
    mine = [h for h in plan["halls"] if any(i["id"] == me["id"] for i in h["invigilators"])]
    other = [h for h in plan["halls"] if h not in mine]
    if other:
        assert client.get(f"/api/plans/{plan['id']}/halls/{other[0]['hall_id']}", headers=invigilator_headers).status_code == 403
    target = plan["halls"][0]
    client.put(f"/api/plans/{plan['id']}/invigilators", headers=admin_headers,
               json={"assignments": [{"hall_id": target["hall_id"], "user_ids": [me["id"]]}]})
    assert client.get(f"/api/plans/{plan['id']}/halls/{target['hall_id']}", headers=invigilator_headers).status_code == 200
    assert client.get(f"/api/plans/{plan['id']}/halls/{target['hall_id']}/swap-check", params={"seat": "A1"},
                      headers=invigilator_headers).status_code == 403


def test_impossible_request_explains_why(client, admin_headers, world):
    halls = client.get("/api/halls", headers=admin_headers).json()
    smallest = min(halls, key=lambda h: h["capacity"])
    response = client.post(f"/api/sessions/{world['sessions'][1]['id']}/plans", headers=admin_headers,
                           json={"rules": RULES, "hall_ids": [smallest["id"]]})
    assert response.status_code == 422
    assert "usable seats" in response.json()["detail"]
    trail = client.get("/api/audit", params={"action": "plan.failed"}, headers=admin_headers).json()
    assert trail and "reasons" in trail[0]["details"]
