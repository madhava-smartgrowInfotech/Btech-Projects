import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _key(client, name="rx", bits=2048):
    r = client.post("/api/keys/generate", json={"name": name, "bits": bits})
    assert r.status_code == 200, r.text
    return r.json()


def test_health_and_auth_required(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    r = client.get("/api/keys", headers={"Authorization": ""})
    assert r.status_code in (401, 403)


def test_register_login_validation(client):
    assert client.post("/api/auth/register", json={"username": "ab", "password": "longenough1"}).status_code == 422
    assert client.post("/api/auth/register", json={"username": "tester_1", "password": "short"}).status_code == 422
    assert client.post("/api/auth/register", json={"username": "tester_1", "password": "longenough1"}).status_code == 200
    assert client.post("/api/auth/register", json={"username": "tester_1", "password": "longenough1"}).status_code == 409
    assert client.post("/api/auth/login", json={"username": "tester_1", "password": "wrong-pass-1"}).status_code == 401


def test_key_lifecycle(client):
    k = _key(client, "lifecycle", 2048)
    assert k["has_private"] and k["bits"] == 2048
    assert client.post("/api/keys/generate", json={"name": "bad", "bits": 1024}).status_code == 400
    pub = client.get(f"/api/keys/{k['id']}/export?part=public").text
    imp = client.post("/api/keys/import", json={"name": "pub only", "pem": pub}).json()
    assert imp["has_private"] is False and imp["fingerprint"] == k["fingerprint"]
    assert client.get(f"/api/keys/{imp['id']}/export?part=private").status_code == 400
    assert client.post("/api/keys/import", json={"name": "junk", "pem": "x" * 40}).status_code == 400
    assert client.delete(f"/api/keys/{imp['id']}").status_code == 200
    assert client.get(f"/api/keys/{imp['id']}/export").status_code == 404


def test_send_receive_end_to_end(client):
    k = _key(client, "e2e", 3072)
    pdf = ROOT / "data" / "payloads" / "confidential_memo.pdf"
    sent = client.post("/api/send", data={"key_id": k["id"], "payload_sample": pdf.name,
                                          "cover_sample": "astronaut_512x512.png"})
    assert sent.status_code == 200, sent.text
    s = sent.json()
    assert s["quality"]["psnr_db"] > 50 and s["quality"]["max_abs_change"] == 1
    assert s["input_sha256"] == hashlib.sha256(pdf.read_bytes()).hexdigest()
    stego = client.get(f"/api/ops/{s['op_id']}/stego").content
    assert stego[:8] == b"\x89PNG\r\n\x1a\n"
    got = client.post("/api/receive", data={"key_id": k["id"]}, files={"stego": ("r.png", stego, "image/png")})
    assert got.status_code == 200, got.text
    g = got.json()
    assert g["hash_match"] and g["gcm_verified"] and g["output_sha256"] == s["input_sha256"]
    assert client.get(f"/api/ops/{g['op_id']}/restored").content == pdf.read_bytes()
    assert client.get(f"/api/analysis/{s['op_id']}").json()["capacity"]["bundle_bytes"] == s["bundle_bytes"]


def test_receive_failure_paths(client):
    k, other = _key(client, "right"), _key(client, "wrong")
    s = client.post("/api/send", data={"key_id": k["id"], "payload_sample": "meeting_notes.txt",
                                       "cover_sample": "coffee_600x400.png"}).json()
    stego = client.get(f"/api/ops/{s['op_id']}/stego").content
    cover = client.get(f"/api/ops/{s['op_id']}/cover").content
    bad = client.post("/api/receive", data={"key_id": other["id"]}, files={"stego": ("r.png", stego, "image/png")})
    assert bad.status_code == 400 and "not the key" in bad.json()["detail"]
    plain = client.post("/api/receive", data={"key_id": k["id"]}, files={"stego": ("c.png", cover, "image/png")})
    assert plain.status_code == 400
    notimg = client.post("/api/receive", data={"key_id": k["id"]}, files={"stego": ("x.png", b"zzz", "image/png")})
    assert notimg.status_code == 400
    log = client.get("/api/log?op=receive").json()
    assert any(not e["ok"] for e in log)


def test_capacity_check_blocks_oversize(client):
    k = _key(client, "tiny")
    r = client.post("/api/send", data={"key_id": k["id"], "payload_sample": "confidential_memo.pdf",
                                       "cover_sample": "coffee_small_200x200.png"})
    assert r.status_code == 400 and "holds only" in r.json()["detail"]


def test_sample_names_cannot_escape_folder(client):
    assert client.get("/api/samples/covers/..%2F..%2F.env").status_code == 404
    assert client.get("/api/samples/payloads/..%5C..%5C.env").status_code == 404


def test_empty_upload_rejected(client):
    k = _key(client, "uploads")
    r = client.post("/api/send", data={"key_id": k["id"], "cover_sample": "coffee_600x400.png"},
                    files={"payload": ("empty.bin", b"", "application/octet-stream")})
    assert r.status_code == 400


def test_analysis_images_and_robustness(client):
    k = _key(client, "analysis")
    s = client.post("/api/send", data={"key_id": k["id"], "payload_sample": "accounts.csv",
                                       "cover_sample": "rocket_640x427.png"}).json()
    for name in ("histogram.png", "bitplanes.png"):
        assert client.get(f"/api/analysis/{s['op_id']}/{name}").content[:4] == b"\x89PNG"
    rob = client.post(f"/api/robustness/{s['op_id']}").json()
    status = {r["attack"]: r["status"] for r in rob["results"]}
    assert status["png_resave"] == "recovered" and status["jpeg_q95"] == "lost"
    assert client.get(f"/api/robustness/{s['op_id']}").json()["survived"]


def test_log_never_contains_key_material(client):
    blob = str(client.get("/api/log?limit=500").json())
    assert "BEGIN" not in blob and "PRIVATE" not in blob
