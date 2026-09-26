from app.core.config import get_settings


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_login_and_me(client, admin_headers):
    me = client.get("/api/auth/me", headers=admin_headers).json()
    assert me["email"] == get_settings().demo_admin_email
    assert me["role"] == "admin"


def test_wrong_password_is_rejected(client):
    response = client.post("/api/auth/login", json={"email": get_settings().demo_admin_email, "password": "nope"})
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"]


def test_protected_route_needs_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_register_waits_for_approval_then_admin_approves(client, admin_headers):
    body = {"full_name": "New  Invigilator", "email": "New.Person@Example.org", "password": "long-enough-1"}
    created = client.post("/api/auth/register", json=body)
    assert created.status_code == 201
    assert created.json()["status"] == "pending"
    assert created.json()["full_name"] == "New Invigilator"

    blocked = client.post("/api/auth/login", json={"email": "new.person@example.org", "password": "long-enough-1"})
    assert blocked.status_code == 403

    duplicate = client.post("/api/auth/register", json=body)
    assert duplicate.status_code == 409

    approved = client.patch(f"/api/users/{created.json()['id']}", json={"status": "active"}, headers=admin_headers)
    assert approved.status_code == 200
    ok = client.post("/api/auth/login", json={"email": "new.person@example.org", "password": "long-enough-1"})
    assert ok.status_code == 200


def test_invigilator_cannot_manage_team(client, invigilator_headers):
    assert client.get("/api/users", headers=invigilator_headers).status_code == 403


def test_last_admin_cannot_be_disabled(client, admin_headers):
    me = client.get("/api/auth/me", headers=admin_headers).json()
    response = client.patch(f"/api/users/{me['id']}", json={"status": "disabled"}, headers=admin_headers)
    assert response.status_code == 409


def test_rules_defaults_and_update(client, admin_headers, invigilator_headers):
    rules = client.get("/api/settings/rules", headers=invigilator_headers).json()
    assert rules == {"adjacency": 8, "roll_gap": 5, "department_mix": True,
                     "fill_strategy": "compact", "accessible_per_hall": 2}
    updated = client.put("/api/settings/rules", json={**rules, "roll_gap": 3}, headers=admin_headers)
    assert updated.json()["roll_gap"] == 3
    assert client.put("/api/settings/rules", json={**rules, "adjacency": 6}, headers=admin_headers).status_code == 422
    client.put("/api/settings/rules", json=rules, headers=admin_headers)
