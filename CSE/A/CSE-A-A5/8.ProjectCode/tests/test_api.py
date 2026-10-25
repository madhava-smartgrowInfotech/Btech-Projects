"""API tests through FastAPI's TestClient (the app is imported in-process)."""
import base64
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cipherguard.api.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _enc_fields(e):
    return {k: e[k] for k in ("ciphertext", "nonce", "tag", "ephemeral_public")}


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok" and r.json()["engine_loaded"] is True


def test_metrics_endpoint(client):
    r = client.get("/api/metrics")
    assert r.status_code == 200 and 0.5 < r.json()["accuracy"] <= 1


def test_score_attack_raises_alert_and_normal_does_not(client):
    client.delete("/api/alerts")
    n = client.post("/api/ids/score", json={"proto": "tcp", "service": "http", "state": "CON", "dur": 0.3, "sbytes": 900, "dbytes": 700,
                                            "rate": 12000, "spkts": 7, "dpkts": 5, "ct_srv_src": 1, "ct_dst_ltm": 1})
    assert n.json()["label"] == "normal" and "alert" not in n.json()
    assert client.get("/api/alerts").json()["total"] == 0
    a = client.post("/api/ids/score", json={"proto": "tcp", "service": "ftp", "state": "RST", "dur": 3.5, "sbytes": 85000, "dbytes": 1200,
                                            "rate": 95000, "spkts": 35, "dpkts": 4, "ct_srv_src": 12, "ct_dst_ltm": 15})
    assert a.json()["label"] == "attack" and "alert" in a.json()
    assert client.get("/api/alerts").json()["total"] == 1
    assert client.delete("/api/alerts").json() == {"cleared": True}


def test_score_rejects_empty_payload(client):
    assert client.post("/api/ids/score", json={}).status_code == 400


def test_batch_scoring_and_validation(client):
    sample = ROOT / "frontend" / "public" / "samples" / "sample_flows.csv"
    r = client.post("/api/ids/score-batch", files={"file": ("sample_flows.csv", sample.read_bytes(), "text/csv")})
    b = r.json()
    assert r.status_code == 200 and b["total"] == 120 and b["attack_count"] + b["normal_count"] == 120
    assert client.post("/api/ids/score-batch", files={"file": ("x.txt", b"hello", "text/plain")}).status_code == 400
    assert client.post("/api/ids/score-batch", files={"file": ("e.csv", b"", "text/csv")}).status_code == 400
    client.delete("/api/alerts")


def test_encrypt_decrypt_round_trip(client):
    e = client.post("/api/crypto/encrypt", json={"plaintext": "hello cloud"}).json()
    assert e["algorithm"] == "AES-256-GCM"
    d = client.post("/api/crypto/decrypt", json=_enc_fields(e))
    assert d.status_code == 200 and d.json() == {"plaintext": "hello cloud", "verified": True}


def test_decrypt_uses_cloud_private_key_when_cache_is_empty(client):
    e = client.post("/api/crypto/encrypt", json={"plaintext": "no cache"}).json()
    from cipherguard.api import main
    main._last_session_keys.clear()  # force the real ECDH path on the cloud side
    d = client.post("/api/crypto/decrypt", json=_enc_fields(e))
    assert d.status_code == 200 and d.json()["plaintext"] == "no cache"


def test_tampered_ciphertext_is_rejected(client):
    e = client.post("/api/crypto/encrypt", json={"plaintext": "do not touch"}).json()
    ct = base64.b64decode(e["ciphertext"])
    e["ciphertext"] = base64.b64encode(bytes([ct[0] ^ 1]) + ct[1:]).decode()
    assert client.post("/api/crypto/decrypt", json=_enc_fields(e)).status_code == 400


def test_crypto_input_validation(client):
    assert client.post("/api/crypto/encrypt", json={"plaintext": ""}).status_code == 400
    assert client.post("/api/crypto/decrypt", json={"ciphertext": "!!", "nonce": "!!", "tag": "!!", "ephemeral_public": "x"}).status_code == 400
    assert client.post("/api/crypto/decrypt", json={"ciphertext": "AA==", "nonce": "AA==", "tag": "AA=="}).status_code == 400


def test_file_encryption_round_trip_and_limits(client):
    r = client.post("/api/crypto/encrypt-file", files={"file": ("note.txt", b"file bytes to protect", "text/plain")}).json()
    assert r["original_size"] == 21
    d = client.post("/api/crypto/decrypt", json=_enc_fields(r))
    assert d.json()["plaintext"] == "file bytes to protect"
    assert client.post("/api/crypto/encrypt-file", files={"file": ("e.bin", b"", "application/octet-stream")}).status_code == 400
    big = b"0" * (5 * 1024 * 1024 + 1)
    assert client.post("/api/crypto/encrypt-file", files={"file": ("big.bin", big, "application/octet-stream")}).status_code == 400
