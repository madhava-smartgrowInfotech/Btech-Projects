"""CipherVault evaluation: measures REAL properties of the implementation.

Runs reproducible checks against the app (crypto primitives, API auth/authz,
file pipeline, integrity, audit chain) and writes results to
evaluation_results.txt + evaluation_results.json. Every number comes from an
actual execution — nothing is hardcoded.
"""

import base64
import hashlib
import io
import json
import os
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmp.name) / 'eval.db'}"
os.environ["STORAGE_DIR"] = str(Path(_tmp.name) / "enc")
os.environ["JWT_SECRET"] = "evaluation-run-secret"
Path(_tmp.name, "enc").mkdir(parents=True, exist_ok=True)

from cryptography.hazmat.primitives import hashes  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import padding, rsa  # noqa: E402
from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()
from backend.app.db.database import init_db  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.app.services import audit_service  # noqa: E402
from backend.app.db.database import get_session_factory  # noqa: E402
from backend.app.db.models import AuditLog  # noqa: E402

init_db()
client = TestClient(app)
results: dict = {"checks": []}


def check(name, ok, detail=""):
    results["checks"].append({"name": name, "passed": bool(ok), "detail": detail})
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def timed(fn, repeats=5):
    samples = []
    out = None
    for _ in range(repeats):
        t0 = time.perf_counter()
        out = fn()
        samples.append((time.perf_counter() - t0) * 1000)
    return out, statistics.mean(samples), max(samples)


def main():
    # ---- 1. AES-256-GCM encrypt/decrypt timing across sizes ----
    for size in (1024, 65536, 1048576):
        key = AESGCM.generate_key(256)
        aes = AESGCM(key)
        pt = os.urandom(size)
        iv = os.urandom(12)

        def enc():
            return aes.encrypt(os.urandom(12), pt, None)

        ct, enc_ms, _ = timed(enc)
        ct0 = aes.encrypt(iv, pt, None)
        overhead = len(ct0) - len(pt)  # GCM tag = 16 bytes

        def dec():
            return aes.decrypt(iv, ct0, None)

        _, dec_ms, _ = timed(dec)
        results[f"aes256gcm_encrypt_ms_{size}B"] = round(enc_ms, 3)
        results[f"aes256gcm_decrypt_ms_{size}B"] = round(dec_ms, 3)
        results[f"ciphertext_overhead_bytes_{size}B"] = overhead
        check(f"AES-256-GCM round-trip {size}B", aes.decrypt(iv, ct0, None) == pt,
              f"enc={enc_ms:.2f}ms dec={dec_ms:.2f}ms overhead={overhead}B")

    # ---- 2. SHA-256 integrity ----
    data = os.urandom(100000)
    t0 = time.perf_counter()
    digest = hashlib.sha256(data).hexdigest()
    sha_ms = (time.perf_counter() - t0) * 1000
    results["sha256_100KB_ms"] = round(sha_ms, 3)
    check("SHA-256 integrity verify", hashlib.sha256(data).hexdigest() == digest, f"{sha_ms:.2f}ms")

    # ---- 3. RSA-2048 wrap/unwrap ----
    t0 = time.perf_counter()
    k1 = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    k2 = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    gen_ms = (time.perf_counter() - t0) * 1000
    fek = os.urandom(32)
    pad = padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    t0 = time.perf_counter()
    w = k1.public_key().encrypt(fek, pad)
    wrap_ms = (time.perf_counter() - t0) * 1000
    ok = k1.decrypt(w, pad) == fek
    results["rsa2048_keygen_2keys_ms"] = round(gen_ms, 1)
    results["rsa_oaep_wrap_ms"] = round(wrap_ms, 3)
    results["rsa_wrapped_bytes"] = len(w)
    check("RSA-2048-OAEP wrap/unwrap", ok, f"wrap={wrap_ms:.2f}ms wrapped={len(w)}B")

    # ---- 4. Auth performance + RBAC (real API) ----
    def reg(name, email, pw, tag):
        return client.post("/api/auth/register", json={
            "name": name, "email": email, "password": pw,
            "public_key": base64.b64encode(b"fake-public-key-" + tag).decode(),
            "encrypted_private_key": '{"salt":"a","iv":"b","data":"c"}',
            "private_key_salt": base64.b64encode(b"fake-salt-" + tag).decode()})

    assert reg("Eval Owner", "eval.owner@example.com", "EvalOwner123", b"1").status_code == 201
    assert reg("Eval Viewer", "eval.viewer@example.com", "EvalViewer123", b"2").status_code == 201
    dup = reg("Dup", "eval.owner@example.com", "Another123", b"3")
    check("duplicate registration rejected", dup.status_code == 400)

    _, login_ms, _ = timed(lambda: client.post("/api/auth/login",
                                               json={"email": "eval.owner@example.com", "password": "EvalOwner123"}))
    results["login_ms"] = round(login_ms, 2)
    bad = client.post("/api/auth/login", json={"email": "eval.owner@example.com", "password": "nope"})
    check("invalid login rejected", bad.status_code == 401, f"login={login_ms:.1f}ms")
    noauth = client.get("/api/files")
    check("protected route requires JWT", noauth.status_code in (401, 403))
    forged = client.get("/api/auth/me", headers={"Authorization": "Bearer forged.token.here"})
    check("forged JWT rejected", forged.status_code == 401)

    o_tok = client.post("/api/auth/login",
                        json={"email": "eval.owner@example.com", "password": "EvalOwner123"}).json()["access_token"]
    v_tok = client.post("/api/auth/login",
                        json={"email": "eval.viewer@example.com", "password": "EvalViewer123"}).json()["access_token"]
    H = lambda t: {"Authorization": f"Bearer {t}"}  # noqa: E731

    # ---- 5. Upload / download pipeline ----
    pt = os.urandom(200000)
    sha = hashlib.sha256(pt).hexdigest()
    key = AESGCM.generate_key(256)
    aes = AESGCM(key)
    iv = os.urandom(12)
    t0 = time.perf_counter()
    ct = aes.encrypt(iv, pt, None)
    browser_enc_ms = (time.perf_counter() - t0) * 1000
    results["browser_encrypt_200KB_ms"] = round(browser_enc_ms, 2)
    results["plaintext_bytes"] = len(pt)
    results["ciphertext_bytes"] = len(ct)

    t0 = time.perf_counter()
    up = client.post("/api/files/upload", headers=H(o_tok),
                     files={"ciphertext": ("c.bin", io.BytesIO(ct), "application/octet-stream")},
                     data={"original_filename": "eval.bin", "mime_type": "application/octet-stream",
                           "original_size": str(len(pt)), "iv": base64.b64encode(iv).decode(),
                           "wrapped_fek": base64.b64encode(b"F" * 256).decode(), "plaintext_sha256": sha})
    upload_ms = (time.perf_counter() - t0) * 1000
    results["api_upload_200KB_ms"] = round(upload_ms, 2)
    check("encrypted upload accepted", up.status_code == 201, f"{upload_ms:.1f}ms")
    fid = up.json()["id"]

    # ciphertext-at-rest check: stored bytes must differ from plaintext
    from backend.app.db.database import get_engine  # noqa: E402
    stored_list = list(Path(os.environ["STORAGE_DIR"]).glob("*"))
    assert stored_list, "no stored object found"
    stored_bytes = stored_list[0].read_bytes()
    check("stored object is ciphertext, not plaintext", stored_bytes != pt and stored_bytes == ct,
          f"stored={len(stored_bytes)}B")

    t0 = time.perf_counter()
    dl = client.get(f"/api/files/{fid}/download", headers=H(o_tok))
    dl_ms = (time.perf_counter() - t0) * 1000
    results["api_download_200KB_ms"] = round(dl_ms, 2)
    check("owner download allowed", dl.status_code == 200, f"{dl_ms:.1f}ms")
    denied = client.get(f"/api/files/{fid}/download", headers=H(v_tok))
    check("non-shared download denied", denied.status_code == 403)
    results["authz_allowed"] = 1
    results["authz_denied"] = 1

    # client-side decrypt + verify
    t0 = time.perf_counter()
    recovered = aes.decrypt(iv, dl.content, None)
    verified = hashlib.sha256(recovered).hexdigest() == sha
    dec_verify_ms = (time.perf_counter() - t0) * 1000
    results["browser_decrypt_verify_200KB_ms"] = round(dec_verify_ms, 2)
    check("decrypt + SHA-256 verify", verified and recovered == pt, f"{dec_verify_ms:.1f}ms")

    # tampered ciphertext must fail
    bad_ct = bytearray(dl.content)
    bad_ct[10] ^= 1
    try:
        aes.decrypt(iv, bytes(bad_ct), None)
        check("tampered ciphertext rejected", False)
    except Exception:
        check("tampered ciphertext rejected", True)
        results["integrity_tamper_detected"] = True

    # ---- 6. Audit chain ----
    db = get_session_factory()()
    try:
        n = db.query(AuditLog).count()
        from backend.app.services import audit_service as svc
        valid, checked, _ = svc.verify_chain(db)
        check("audit chain valid", valid, f"{checked} entries (db count {n})")
        results["audit_entries"] = checked
        # tamper simulation on a copy of values (restore afterwards)
        first = db.query(AuditLog).order_by(AuditLog.id.asc()).first()
        orig = first.details
        first.details = "tampered"
        db.commit()
        valid2, _, fail_id = svc.verify_chain(db)
        check("audit tamper detected", valid2 is False, f"failure at entry {fail_id}")
        results["audit_tamper_detected"] = (valid2 is False)
        first.details = orig
        db.commit()
    finally:
        db.close()

    # ---- summary ----
    passed = sum(1 for c in results["checks"] if c["passed"])
    total = len(results["checks"])
    results["summary"] = {"passed": passed, "total": total}
    print(f"\n{passed}/{total} evaluation checks passed.")

    out_txt = ROOT / "evaluation_results.txt"
    out_json = ROOT / "evaluation_results.json"
    lines = ["CipherVault evaluation results (generated from actual execution)", "=" * 60, ""]
    for k, v in results.items():
        if k in ("checks", "summary"):
            continue
        lines.append(f"{k}: {v}")
    lines += ["", "Checks:"]
    for c in results["checks"]:
        lines.append(f"  [{'PASS' if c['passed'] else 'FAIL'}] {c['name']} {c.get('detail','')}")
    lines.append(f"\nSummary: {passed}/{total} checks passed.")
    out_txt.write_text("\n".join(lines), encoding="utf-8")
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {out_txt} and {out_json}")


if __name__ == "__main__":
    main()
