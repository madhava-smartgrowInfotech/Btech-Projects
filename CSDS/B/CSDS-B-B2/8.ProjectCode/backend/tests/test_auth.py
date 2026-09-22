from app.seed import DEMO_PASSWORD


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["database"] == "ok"
    assert body["time"].endswith("Z")


def test_demo_accounts_have_roles(client):
    for email, role in [("user@signalscout.demo", "user"), ("engineer@signalscout.demo", "engineer"), ("admin@signalscout.demo", "admin")]:
        r = client.post("/api/auth/login", json={"email": email, "password": DEMO_PASSWORD})
        assert r.status_code == 200
        assert r.json()["user"]["role"] == role


def test_wrong_password_is_rejected(client):
    r = client.post("/api/auth/login", json={"email": "user@signalscout.demo", "password": "wrong-password"})
    assert r.status_code == 401
    assert "incorrect" in r.json()["detail"]


def test_register_login_and_profile(client):
    r = client.post("/api/auth/register", json={"email": "Field.Tester@Example.com", "name": "  Field   Tester ", "password": "strong-pass-1"})
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    assert r.json()["user"]["email"] == "field.tester@example.com"
    assert r.json()["user"]["name"] == "Field Tester"
    assert r.json()["user"]["role"] == "user"

    dup = client.post("/api/auth/register", json={"email": "field.tester@example.com", "name": "Again", "password": "strong-pass-1"})
    assert dup.status_code == 409

    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200 and me.json()["email"] == "field.tester@example.com"

    upd = client.patch("/api/auth/me", headers=headers, json={"notify_email": True, "current_password": "strong-pass-1", "new_password": "stronger-pass-2"})
    assert upd.status_code == 200 and upd.json()["notify_email"] is True
    assert client.post("/api/auth/login", json={"email": "field.tester@example.com", "password": "stronger-pass-2"}).status_code == 200


def test_short_password_and_bad_email_rejected(client):
    assert client.post("/api/auth/register", json={"email": "a@b.com", "name": "Ab", "password": "short"}).status_code == 422
    assert client.post("/api/auth/register", json={"email": "not-an-email", "name": "Ab", "password": "long-enough-1"}).status_code == 422


def test_protected_routes_need_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer nonsense"}).status_code == 401


def test_admin_routes_need_admin_role(client, user_headers, engineer_headers, admin_headers):
    assert client.get("/api/admin/users", headers=user_headers).status_code == 403
    assert client.get("/api/admin/users", headers=engineer_headers).status_code == 403
    r = client.get("/api/admin/users", headers=admin_headers)
    assert r.status_code == 200 and len(r.json()) >= 3


def test_admin_cannot_demote_self(client, admin_headers):
    me = client.get("/api/auth/me", headers=admin_headers).json()
    r = client.patch(f"/api/admin/users/{me['id']}", headers=admin_headers, json={"role": "user"})
    assert r.status_code == 400


def test_demo_password_cannot_change(client, user_headers):
    r = client.patch("/api/auth/me", headers=user_headers, json={"current_password": DEMO_PASSWORD, "new_password": "another-pass-1"})
    assert r.status_code == 403


def test_connect_info(client, user_headers):
    r = client.get("/api/system/connect", headers=user_headers)
    assert r.status_code == 200
    assert r.json()["backend_port"] == 8202 and r.json()["frontend_port"] == 5202


def test_unknown_api_path_is_json_404(client):
    r = client.get("/api/does-not-exist")
    assert r.status_code == 404 and r.json()["detail"] == "Not found"
