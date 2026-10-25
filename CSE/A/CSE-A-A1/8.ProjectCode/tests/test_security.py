import os
import uuid

from conftest import upload
from db import get_db


def test_passwords_are_stored_hashed(client):
    n = "u_" + uuid.uuid4().hex[:8]
    client.post("/api/auth/register", json={"username": n, "password": "PlainText#1"})
    conn = get_db()
    h = conn.execute("SELECT password_hash FROM users WHERE username=?", (n,)).fetchone()["password_hash"]
    conn.close()
    assert "PlainText#1" not in h and h.split(":")[0] in ("scrypt", "pbkdf2")


def test_sql_injection_in_login_and_register_is_inert(client):
    payload = "' OR '1'='1' --"
    assert client.post("/api/auth/login", json={"username": payload, "password": payload}).status_code == 401
    assert client.post("/api/auth/register", json={"username": payload, "password": "x"}).status_code == 201
    conn = get_db()
    assert conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"] >= 1   # the users table still exists
    conn.close()


def test_sql_injection_in_question_is_stored_literally(user, sample_bytes):
    c = user["client"]
    upload(c, sample_bytes)
    q = "x'); DROP TABLE queries;--"
    assert c.post("/api/ask", json={"question": q}).status_code == 200
    assert c.get("/api/ask/history").json()[0]["question"] == q


def test_path_traversal_in_filename_stays_inside_user_folder(user, tmp_root):
    r = upload(user["client"], b"Graphs are non linear data structures with vertices and edges to study.", "../../evil.txt")
    assert r.status_code == 201
    assert r.json()["document"]["filename"] == "evil.txt"
    folder = os.path.join(tmp_root, "uploads", str(user["id"]))
    assert "evil.txt" in os.listdir(folder)
    assert not os.path.exists(os.path.join(tmp_root, "evil.txt"))


def test_filename_with_only_dots_is_rejected(user):
    assert upload(user["client"], b"abc", "..").status_code == 400


def test_double_extension_exe_is_rejected(user):
    assert upload(user["client"], b"abc", "notes.txt.exe").status_code == 400


def test_session_cookie_flags(client):
    n = "u_" + uuid.uuid4().hex[:8]
    client.post("/api/auth/register", json={"username": n, "password": "p"})
    r = client.post("/api/auth/login", json={"username": n, "password": "p"})
    cookie = r.headers["set-cookie"].lower()
    assert "alip_session" in cookie and "httponly" in cookie and "samesite=lax" in cookie
    assert "secure" not in cookie       # known limitation: https_only=False (local demo deployment)


def test_tampered_session_cookie_is_ignored(client):
    client.cookies.set("alip_session", "eyJ1c2VyX2lkIjogMX0=.abc.def")
    assert client.get("/api/auth/me").json() is None
    assert client.get("/api/dashboard").status_code == 401


def test_script_in_subject_is_returned_as_plain_json_text(user):
    r = upload(user["client"], b"Trees have a root node and child nodes connected by edges in a hierarchy.", "t.txt",
               "<script>alert(1)</script>")
    assert r.json()["document"]["subject"] == "<script>alert(1)</script>"      # stored verbatim, React escapes on render
    assert r.headers["content-type"].startswith("application/json")


def test_cors_only_allows_the_frontend_origin(client):
    ok = client.options("/api/health", headers={"Origin": "http://localhost:5301", "Access-Control-Request-Method": "GET"})
    bad = client.options("/api/health", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5301"
    assert "access-control-allow-origin" not in bad.headers


def test_known_limitation_same_filename_shares_one_file_on_disk(user, tmp_root):
    """Two uploads with the same name map to one path: deleting one document removes the other one's file."""
    c = user["client"]
    text = b"Queues are first in first out structures used by schedulers to serve requests in order."
    a = upload(c, text, "same.txt").json()["document"]
    b = upload(c, text, "same.txt").json()["document"]
    folder = os.path.join(tmp_root, "uploads", str(user["id"]))
    assert os.listdir(folder).count("same.txt") == 1 and a["id"] != b["id"]
    c.delete(f"/api/documents/{a['id']}")
    assert "same.txt" not in os.listdir(folder)
    assert len(c.get("/api/documents").json()) == 1       # the other document row (and its chunks) still exist
