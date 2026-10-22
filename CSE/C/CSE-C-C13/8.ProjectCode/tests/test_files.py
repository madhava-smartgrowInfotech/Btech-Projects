"""File-operation tests: upload / list / download / update / delete / shared access."""

from tests.conftest import auth, login_as, upload_ciphertext


def test_upload_list_download_delete(client, owner):
    _, token = owner
    f = upload_ciphertext(client, token, filename="hello.txt")
    assert f["original_filename"] == "hello.txt"

    mine = client.get("/api/files", headers=auth(token)).json()
    assert any(x["id"] == f["id"] for x in mine)

    dl = client.get(f"/api/files/{f['id']}/download", headers=auth(token))
    assert dl.status_code == 200
    assert dl.headers.get("X-CipherVault-SHA256")
    assert dl.headers.get("X-CipherVault-IV")

    assert client.delete(f"/api/files/{f['id']}", headers=auth(token)).status_code == 200
    assert client.get(f"/api/files/{f['id']}", headers=auth(token)).status_code == 404


def test_malformed_upload_rejected(client, owner):
    import io
    _, token = owner
    r = client.post("/api/files/upload", headers=auth(token),
                    files={"ciphertext": ("c.bin", io.BytesIO(b"abc"), "application/octet-stream")},
                    data={"original_filename": "bad.txt", "mime_type": "text/plain",
                          "original_size": "3", "iv": "!!!not-base64!!!",
                          "wrapped_fek": "eA==", "plaintext_sha256": "notahash"})
    assert r.status_code == 400


def test_shared_access_listing(client, owner, viewer_user):
    import base64
    _, o_token = owner
    v, _ = viewer_user
    f = upload_ciphertext(client, o_token, filename="team.txt")
    r = client.post(f"/api/files/{f['id']}/share", headers=auth(o_token),
                    json={"user_id": v["id"], "role": "viewer",
                          "wrapped_fek": base64.b64encode(b"S" * 256).decode()})
    assert r.status_code == 200
    v_token = login_as(client, v)
    shared = client.get("/api/files/shared", headers=auth(v_token)).json()
    assert any(x["id"] == f["id"] and x["effective_role"] == "viewer" for x in shared)
