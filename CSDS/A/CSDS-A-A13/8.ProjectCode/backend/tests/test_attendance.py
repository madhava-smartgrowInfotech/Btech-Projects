"""F6 - hall attendance: marking, scanning slips, locking."""
from __future__ import annotations

import pytest

from tests.helpers import import_sample, reset

RULES = {"adjacency": 8, "roll_gap": 5, "department_mix": True, "fill_strategy": "compact", "accessible_per_hall": 2}


@pytest.fixture(scope="module")
def setup(client, admin_headers, invigilator_headers):
    reset(client, admin_headers)
    import_sample(client, admin_headers)
    session = client.get("/api/sessions", headers=admin_headers).json()[2]
    plan = client.post(f"/api/sessions/{session['id']}/plans", headers=admin_headers, json={"rules": RULES, "seed": 3}).json()
    client.post(f"/api/plans/{plan['id']}/publish", headers=admin_headers)
    me = client.get("/api/auth/me", headers=invigilator_headers).json()
    hall, other = plan["halls"][0], plan["halls"][1]
    for h in plan["halls"]:
        if any(i["id"] == me["id"] for i in h["invigilators"]) and h["hall_id"] != hall["hall_id"]:
            client.put(f"/api/plans/{plan['id']}/invigilators", headers=admin_headers,
                       json={"assignments": [{"hall_id": h["hall_id"], "user_ids": []}]})
    client.put(f"/api/plans/{plan['id']}/invigilators", headers=admin_headers,
               json={"assignments": [{"hall_id": hall["hall_id"], "user_ids": [me["id"]]}]})
    seats = client.get(f"/api/plans/{plan['id']}/halls/{hall['hall_id']}", headers=invigilator_headers).json()["seats"]
    other_seats = client.get(f"/api/plans/{plan['id']}/halls/{other['hall_id']}", headers=admin_headers).json()["seats"]
    return {"plan": plan, "hall": hall, "other": other, "seats": seats, "other_seats": other_seats}


def url(s, tail=""):
    return f"/api/plans/{s['plan']['id']}/halls/{s['hall']['hall_id']}/attendance{tail}"


def test_invigilator_sees_their_hall(client, invigilator_headers, setup):
    mine = client.get("/api/attendance/assignments", headers=invigilator_headers).json()
    assert [a["hall"]["id"] for a in mine] == [setup["hall"]["hall_id"]]
    assert mine[0]["total"] == len(setup["seats"]) and mine[0]["unmarked"] == len(setup["seats"])


def test_marking_and_scanning(client, invigilator_headers, setup):
    first, second = setup["seats"][0]["candidate"], setup["seats"][1]["candidate"]
    counts = client.put(url(setup, f"/{first['id']}"), json={"status": "present"}, headers=invigilator_headers).json()
    assert counts["present"] == 1
    scanned = client.post(url(setup, "/scan"), headers=invigilator_headers,
                          json={"code": f"http://192.168.1.20:5113/lookup/{second['roll_no']}"}).json()
    assert scanned["seat"] == setup["seats"][1]["label"] and scanned["counts"]["present"] == 2
    again = client.post(url(setup, "/scan"), headers=invigilator_headers, json={"code": second["roll_no"].lower()}).json()
    assert again["already_present"] is True


def test_scan_in_the_wrong_hall_says_where_to_go(client, invigilator_headers, setup):
    stranger = setup["other_seats"][0]
    response = client.post(url(setup, "/scan"), headers=invigilator_headers, json={"code": stranger["candidate"]["roll_no"]})
    assert response.status_code == 409
    assert setup["other"]["code"] in response.json()["detail"] and stranger["label"] in response.json()["detail"]
    assert client.post(url(setup, "/scan"), headers=invigilator_headers, json={"code": "NOBODY999"}).status_code == 404


def test_submit_locks_the_register(client, admin_headers, invigilator_headers, setup):
    assert client.post(url(setup, "/submit"), headers=invigilator_headers).status_code == 409
    done = client.post(url(setup, "/mark-remaining-absent"), headers=invigilator_headers).json()
    assert done["unmarked"] == 0 and done["present"] == 2
    locked = client.post(url(setup, "/submit"), headers=invigilator_headers).json()
    assert locked["submitted_at"]
    cid = setup["seats"][0]["candidate"]["id"]
    assert client.put(url(setup, f"/{cid}"), json={"status": "absent"}, headers=invigilator_headers).status_code == 409
    assert client.post(url(setup, "/reopen"), headers=invigilator_headers).status_code == 403
    assert client.post(url(setup, "/reopen"), headers=admin_headers).json()["submitted_at"] is None


def test_unassigned_hall_is_forbidden(client, invigilator_headers, setup):
    other = f"/api/plans/{setup['plan']['id']}/halls/{setup['other']['hall_id']}/attendance/scan"
    assert client.post(other, headers=invigilator_headers, json={"code": "X"}).status_code == 403
