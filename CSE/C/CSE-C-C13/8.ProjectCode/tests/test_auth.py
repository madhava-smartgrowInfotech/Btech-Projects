"""Authentication tests."""

from tests.conftest import auth


def test_register_and_login(client):
    r = client.post("/api/auth/register", json={
        "name": "Tara Tester", "email": "tara.tester@example.com", "password": "StrongPass123",
        "public_key": "cHViLWtleQ==", "encrypted_private_key": '{"salt":"a","iv":"b","data":"c"}',
        "private_key_salt": "c2FsdA=="})
    assert r.status_code == 201, r.text
    assert "password" not in r.text.lower() or "password_hash" not in r.text
    body = r.json()
    assert body["email"] == "tara.tester@example.com"

    ok = client.post("/api/auth/login", json={"email": "tara.tester@example.com", "password": "StrongPass123"})
    assert ok.status_code == 200
    assert "access_token" in ok.json()

    me = client.get("/api/auth/me", headers=auth(ok.json()["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == "tara.tester@example.com"


def test_duplicate_registration_rejected(client, owner):
    user, _ = owner
    r = client.post("/api/auth/register", json={
        "name": "Dup", "email": user["email"], "password": "AnotherPass123",
        "public_key": "ZHVwbGljYXRlLWtleQ==", "encrypted_private_key": '{"salt":"a","iv":"b","data":"c"}',
        "private_key_salt": "ZHVwbGljYXRlLXNhbHQ="})
    assert r.status_code == 400


def test_invalid_login_rejected(client, owner):
    user, _ = owner
    r = client.post("/api/auth/login", json={"email": user["email"], "password": "WrongPassword!"})
    assert r.status_code == 401


def test_protected_route_without_jwt(client):
    assert client.get("/api/auth/me").status_code in (401, 403)
    assert client.get("/api/files").status_code in (401, 403)


def test_expired_or_invalid_jwt_rejected(client):
    assert client.get("/api/auth/me", headers=auth("this.is.not.a.token")).status_code == 401


def test_password_never_returned(client, owner):
    _, token = owner
    me = client.get("/api/auth/me", headers=auth(token)).json()
    assert "password_hash" not in me
    assert "password" not in me
