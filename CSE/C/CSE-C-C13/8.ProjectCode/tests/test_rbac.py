"""Authorization (RBAC) tests: owner / editor / viewer enforcement."""

import base64

from tests.conftest import auth, login_as, upload_ciphertext


def _share(client, owner_token, file_id, target_id, role="viewer"):
    return client.post(f"/api/files/{file_id}/share", headers=auth(owner_token), json={
        "user_id": target_id, "role": role, "wrapped_fek": base64.b64encode(b"R" * 256).decode()})


def test_owner_full_access(client, owner):
    _, token = owner
    f = upload_ciphertext(client, token)
    assert f["effective_role"] == "owner"
    assert client.get(f"/api/files/{f['id']}", headers=auth(token)).status_code == 200
    assert client.get(f"/api/files/{f['id']}/download", headers=auth(token)).status_code == 200


def test_viewer_read_only(client, owner, viewer_user):
    _, o_token = owner
    v, _ = viewer_user
    f = upload_ciphertext(client, o_token, filename="shared-doc.txt")
    assert _share(client, o_token, f["id"], v["id"], "viewer").status_code == 200

    v_token = login_as(client, v)
    assert client.get(f"/api/files/{f['id']}", headers=auth(v_token)).status_code == 200
    assert client.get(f"/api/files/{f['id']}/download", headers=auth(v_token)).status_code == 200
    # viewer cannot delete or manage access
    assert client.delete(f"/api/files/{f['id']}", headers=auth(v_token)).status_code == 403
    assert client.put(f"/api/files/{f['id']}/permissions/{v['id']}", headers=auth(v_token),
                      json={"role": "editor"}).status_code == 403


def test_editor_can_update_but_not_delete(client, owner, editor_user):
    import io
    _, o_token = owner
    e, _ = editor_user
    f = upload_ciphertext(client, o_token, filename="editable.txt")
    assert _share(client, o_token, f["id"], e["id"], "editor").status_code == 200
    e_token = login_as(client, e)
    # editor update allowed
    r = client.put(f"/api/files/{f['id']}", headers=auth(e_token),
                   files={"ciphertext": ("c.bin", io.BytesIO(b"Y" * 40), "application/octet-stream")},
                   data={"iv": base64.b64encode(b"012345678901").decode(),
                         "plaintext_sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
                         "original_size": "5"})
    assert r.status_code == 200, r.text
    # editor cannot delete
    assert client.delete(f"/api/files/{f['id']}", headers=auth(e_token)).status_code == 403


def test_unauthorized_user_rejected(client, owner, viewer_user):
    _, o_token = owner
    v, _ = viewer_user
    f = upload_ciphertext(client, o_token, filename="private.txt")
    v_token = login_as(client, v)
    assert client.get(f"/api/files/{f['id']}", headers=auth(v_token)).status_code == 403
    assert client.get(f"/api/files/{f['id']}/download", headers=auth(v_token)).status_code == 403
    # unauthorized attempt is audited
    events = client.get("/api/audit?limit=500", headers=auth(o_token)).json()
    assert any(e["action"] == "unauthorized_access" and e["file_id"] == f["id"] for e in events)


def test_owner_can_change_role_and_revoke(client, owner, viewer_user):
    _, o_token = owner
    v, _ = viewer_user
    f = upload_ciphertext(client, o_token, filename="role-change.txt")
    assert _share(client, o_token, f["id"], v["id"], "viewer").status_code == 200
    assert client.put(f"/api/files/{f['id']}/permissions/{v['id']}", headers=auth(o_token),
                      json={"role": "editor"}).status_code == 200
    assert client.delete(f"/api/files/{f['id']}/permissions/{v['id']}", headers=auth(o_token)).status_code == 200
    v_token = login_as(client, v)
    assert client.get(f"/api/files/{f['id']}", headers=auth(v_token)).status_code == 403
