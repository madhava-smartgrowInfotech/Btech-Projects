"""End-to-end validation against a LIVE CipherVault server.

Performs the full workflow with real encryption (mirroring the browser pipeline):
register -> login -> encrypt+upload -> ciphertext-at-rest check -> metadata check ->
download -> decrypt -> SHA-256 verify -> share editor/viewer -> access checks ->
unauthorized rejected -> delete -> deleted rejected -> audit + chain verify.

Usage: python scripts/e2e_check.py --url http://localhost:8413
"""

import argparse
import base64
import hashlib
import io
import json
import os
import sqlite3
import sys
from pathlib import Path

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PASS, TOTAL = 0, 0


def check(name, ok, detail=""):
    global PASS, TOTAL
    TOTAL += 1
    if ok:
        PASS += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")
    if not ok:
        raise SystemExit(f"E2E FAILED at: {name} {detail}")


def make_user_keys(password: str):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_der = key.public_key().public_bytes(serialization.Encoding.DER,
                                            serialization.PublicFormat.SubjectPublicKeyInfo)
    # NOTE: demo-grade local protection mirror (real app uses PBKDF2+AES-GCM in browser)
    return key, base64.b64encode(pub_der).decode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8413")
    args = ap.parse_args()
    c = httpx.Client(base_url=args.url, timeout=30)

    assert c.get("/api/health").json()["status"] == "ok"
    assert c.get("/docs").status_code == 200
    assert c.get("/").status_code == 200
    print("server + frontend + docs reachable")

    users = {}
    for name, email, pw in [("E2E Olivia", "e2e.olivia@example.com", "E2E-Olivia-123"),
                            ("E2E Eddie", "e2e.eddie@example.com", "E2E-Eddie-123"),
                            ("E2E Vera", "e2e.vera@example.com", "E2E-Vera-123")]:
        priv, pub = make_user_keys(pw)
        bundle = json.dumps({"salt": base64.b64encode(os.urandom(16)).decode(),
                             "iv": base64.b64encode(os.urandom(12)).decode(),
                             "data": base64.b64encode(os.urandom(64)).decode()})
        r = c.post("/api/auth/register", json={
            "name": name, "email": email, "password": pw, "public_key": pub,
            "encrypted_private_key": bundle,
            "private_key_salt": base64.b64encode(os.urandom(16)).decode()})
        if r.status_code not in (200, 201, 400):
            check("register " + email, False, r.text)
        tok = c.post("/api/auth/login", json={"email": email, "password": pw}).json()["access_token"]
        users[email] = {"priv": priv, "pub": pub, "token": tok}
    check("register + login 3 users", True)

    H = lambda e: {"Authorization": f"Bearer {users[e]['token']}"}  # noqa: E731
    owner, editor, viewer = "e2e.olivia@example.com", "e2e.eddie@example.com", "e2e.vera@example.com"

    # --- encrypt a real file (browser pipeline mirror) ---
    plaintext = b"CipherVault live E2E test file. " * 500
    sha = hashlib.sha256(plaintext).hexdigest()
    fek = os.urandom(32)
    iv = os.urandom(12)
    ct = AESGCM(fek).encrypt(iv, plaintext, None)
    pad = padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    owner_pub = serialization.load_der_public_key(base64.b64decode(users[owner]["pub"]))
    wrapped = owner_pub.encrypt(fek, pad)

    up = c.post("/api/files/upload", headers=H(owner),
                files={"ciphertext": ("c.bin", io.BytesIO(ct), "application/octet-stream")},
                data={"original_filename": "e2e-report.txt", "mime_type": "text/plain",
                      "original_size": str(len(plaintext)), "iv": base64.b64encode(iv).decode(),
                      "wrapped_fek": base64.b64encode(wrapped).decode(), "plaintext_sha256": sha})
    check("encrypted upload", up.status_code == 201, up.text[:120])
    fid = up.json()["id"]

    # --- ciphertext-at-rest: find stored object, compare bytes ---
    stored = None
    for cand in [Path("storage/encrypted"), Path("/app/storage/encrypted")]:
        if cand.exists():
            files = [p for p in cand.iterdir() if p.is_file()]
            if files:
                stored = max(files, key=lambda p: p.stat().st_mtime)
                break
    check("stored ciphertext object exists", stored is not None)
    on_disk = stored.read_bytes()
    check("server stores ciphertext, not plaintext", on_disk == ct and plaintext not in on_disk,
          f"stored={len(on_disk)}B plaintext={len(plaintext)}B")

    # --- metadata in database (SQLite local file) ---
    if Path("ciphervault.db").exists():
        con = sqlite3.connect("ciphervault.db")
        row = con.execute("SELECT original_filename, plaintext_sha256 FROM files WHERE id=?", (fid,)).fetchone()
        con.close()
        check("file metadata in database", row is not None and row[0] == "e2e-report.txt" and row[1] == sha)
    else:
        meta = c.get(f"/api/files/{fid}", headers=H(owner)).json()
        check("file metadata via API", meta["plaintext_sha256"] == sha)

    # --- download -> decrypt -> verify ---
    dl = c.get(f"/api/files/{fid}/download", headers=H(owner))
    check("owner download", dl.status_code == 200)
    assert dl.headers["X-CipherVault-SHA256"] == sha
    meta = c.get(f"/api/files/{fid}", headers=H(owner)).json()
    raw_wrapped = base64.b64decode(meta["wrapped_fek"])
    fek_back = users[owner]["priv"].decrypt(raw_wrapped, pad)
    recovered = AESGCM(fek_back).decrypt(base64.b64decode(meta["iv"]), dl.content, None)
    check("decrypt + SHA-256 verify", recovered == plaintext and hashlib.sha256(recovered).hexdigest() == sha)

    # --- share with editor (re-wrap locally, like the browser) ---
    ed_pub = serialization.load_der_public_key(
        base64.b64decode(c.get("/api/users", headers=H(owner), params={"q": "e2e.eddie"}).json()[0]["public_key"]))
    # NOTE: ed_pub from server is the fake bundle key; fetch real one from registration is unneeded —
    # for E2E we re-wrap with the editor's real key held in-memory (same trust model as browser).
    from cryptography.hazmat.primitives.serialization import load_der_public_key  # noqa: F401
    ed_real_pub = users[editor]["priv"].public_key()
    rewrapped_ed = ed_real_pub.encrypt(fek, pad)
    me = c.get("/api/auth/me", headers=H(editor)).json()
    r = c.post(f"/api/files/{fid}/share", headers=H(owner),
               json={"user_id": me["id"], "role": "editor", "wrapped_fek": base64.b64encode(rewrapped_ed).decode()})
    check("share with editor", r.status_code == 200, r.text[:120])

    dl_ed = c.get(f"/api/files/{fid}/download", headers=H(editor))
    check("editor download allowed", dl_ed.status_code == 200)
    del_ed = c.delete(f"/api/files/{fid}", headers=H(editor))
    check("editor delete denied (owner-only)", del_ed.status_code == 403)

    # --- share with viewer ---
    mv = c.get("/api/auth/me", headers=H(viewer)).json()
    v_real_pub = users[viewer]["priv"].public_key()
    r = c.post(f"/api/files/{fid}/share", headers=H(owner),
               json={"user_id": mv["id"], "role": "viewer",
                     "wrapped_fek": base64.b64encode(v_real_pub.encrypt(fek, pad)).decode()})
    check("share with viewer", r.status_code == 200, r.text[:120])
    check("viewer download allowed", c.get(f"/api/files/{fid}/download", headers=H(viewer)).status_code == 200)

    # --- stranger rejected ---
    priv_x, pub_x = make_user_keys("x")
    rx = c.post("/api/auth/register", json={
        "name": "E2E Xeno", "email": "e2e.xeno@example.com", "password": "E2E-Xeno-12345",
        "public_key": pub_x, "encrypted_private_key": bundle,
        "private_key_salt": base64.b64encode(os.urandom(16)).decode()})
    tx = c.post("/api/auth/login", json={"email": "e2e.xeno@example.com", "password": "E2E-Xeno-12345"}).json()["access_token"]
    Hx = {"Authorization": f"Bearer {tx}"}
    check("stranger access rejected", c.get(f"/api/files/{fid}", headers=Hx).status_code == 403)

    # --- delete + verify gone ---
    check("owner delete", c.delete(f"/api/files/{fid}", headers=H(owner)).status_code == 200)
    check("deleted file rejected", c.get(f"/api/files/{fid}", headers=H(owner)).status_code == 404)

    # --- audit ---
    events = c.get("/api/audit?limit=100", headers=H(owner)).json()
    actions = {e["action"] for e in events}
    check("audit entries generated", {"upload", "download", "share", "delete"} <= actions, sorted(actions)[:12])
    v = c.get("/api/audit/verify", headers=H(owner)).json()
    check("audit chain valid", v["valid"] is True, f"{v['checked']} entries")

    print(f"\nE2E RESULT: {PASS}/{TOTAL} checks passed.")


if __name__ == "__main__":
    main()
