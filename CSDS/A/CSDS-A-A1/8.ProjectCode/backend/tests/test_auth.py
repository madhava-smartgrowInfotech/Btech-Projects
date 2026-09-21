def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["database"] == "ok"
    assert body["gemini"]["configured"] is False


def test_register_login_me(client):
    payload = {"full_name": "Asha Rao", "email": "asha@example.com", "password": "Secret123"}
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    token = res.json()["access_token"]
    assert res.json()["user"]["language"] == "en"

    dup = client.post("/api/auth/register", json=payload)
    assert dup.status_code == 409
    assert dup.json()["code"] == "email_taken"

    login = client.post("/api/auth/login", json={"email": "ASHA@example.com", "password": "Secret123"})
    assert login.status_code == 200

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "asha@example.com"


def test_bad_credentials_and_missing_token(client):
    res = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "Wrong1234"})
    assert res.status_code == 401
    assert res.json()["code"] == "bad_credentials"
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-token"}).status_code == 401


def test_password_rules(client):
    res = client.post("/api/auth/register", json={"full_name": "X", "email": "weak@example.com", "password": "short"})
    assert res.status_code == 422
    assert "password" in res.json()["detail"].lower()


def test_update_language_and_password(client, auth_headers):
    res = client.patch("/api/users/me", json={"language": "hi"}, headers=auth_headers)
    assert res.status_code == 200 and res.json()["language"] == "hi"
    bad = client.patch("/api/users/me", json={"language": "fr"}, headers=auth_headers)
    assert bad.status_code == 400
    wrong = client.post("/api/users/me/password", json={"current_password": "nope", "new_password": "Another123"},
                        headers=auth_headers)
    assert wrong.status_code == 400
    ok = client.post("/api/users/me/password", json={"current_password": "Secret123", "new_password": "Another123"},
                     headers=auth_headers)
    assert ok.status_code == 204


def test_demo_user_seeded(client):
    res = client.post("/api/auth/login", json={"email": "demo@policylens.app", "password": "Demo@12345"})
    assert res.status_code == 200
