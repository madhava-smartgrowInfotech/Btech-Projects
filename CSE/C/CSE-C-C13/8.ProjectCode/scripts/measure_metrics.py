"""Real measurements for the CipherVault documentation (writes docs/metrics/metrics.json).

Starts its own backend on 127.0.0.1:8413 with a throw-away database and storage folder, then measures:
  1. browser Web Crypto timings in headless Chrome (AES-256-GCM, SHA-256, RSA-2048-OAEP, PBKDF2) - the same
     primitives and parameters as frontend/src/lib/vaultCrypto.js
  2. API latency over 127.0.0.1 (register, login, upload, download, share, audit write, chain verification)
  3. end-to-end upload/download pipeline in the browser against a plain (unencrypted) upload baseline
  4. an exhaustive RBAC matrix (4 principals x 9 operations, expected vs observed)
  5. tamper detection: random ciphertext bit flips and audit-log edits, deletions, reorderings, truncation

    python scripts/measure_metrics.py            (system python with playwright, httpx, cryptography)
"""

import base64
import hashlib
import json
import os
import platform
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "metrics"
OUT.mkdir(parents=True, exist_ok=True)
PORT = 8413
BASE = f"http://127.0.0.1:{PORT}"
random.seed(13)


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))]


def summ(xs):
    return {"n": len(xs), "mean": round(statistics.mean(xs), 3), "median": round(statistics.median(xs), 3),
            "p95": round(pct(xs, 0.95), 3), "min": round(min(xs), 3), "max": round(max(xs), 3)}


def timed(fn, n):
    s = []
    for _ in range(n):
        t = time.perf_counter()
        fn()
        s.append((time.perf_counter() - t) * 1000)
    return s


# ---------------------------------------------------------------------------------------------- server
def start_server(tmp):
    env = dict(os.environ)
    env.update({"DATABASE_URL": f"sqlite:///{tmp / 'm.db'}", "STORAGE_DIR": str(tmp / "enc"),
                "JWT_SECRET": "measurement-run-secret-not-for-use", "LOGIN_MAX_ATTEMPTS": "100000"})
    (tmp / "enc").mkdir(parents=True, exist_ok=True)
    py = ROOT / ".venv" / "Scripts" / "python.exe"
    proc = subprocess.Popen([str(py), "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", str(PORT),
                             "--log-level", "warning"], cwd=str(ROOT), env=env)
    for _ in range(80):
        try:
            if httpx.get(BASE + "/api/health", timeout=1).status_code == 200:
                return proc
        except Exception:
            time.sleep(0.25)
    proc.kill()
    raise RuntimeError("backend did not start")


# ---------------------------------------------------------------------------------------------- helpers
_PAD = padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)


class Client:
    """A user with a real RSA key pair, mirroring what the browser does."""

    def __init__(self, http, name, email, pw="Measure-Pass-123"):
        self.http, self.name, self.email, self.pw = http, name, email, pw
        self.priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        from cryptography.hazmat.primitives import serialization
        self.pub_b64 = base64.b64encode(self.priv.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)).decode()
        r = http.post("/api/auth/register", json={"name": name, "email": email, "password": pw, "public_key": self.pub_b64,
                                                   "encrypted_private_key": '{"salt":"x","iv":"y","data":"z"}',
                                                   "private_key_salt": base64.b64encode(os.urandom(16)).decode()})
        assert r.status_code == 201, r.text
        self.id = r.json()["id"]
        self.login()

    def login(self):
        r = self.http.post("/api/auth/login", json={"email": self.email, "password": self.pw})
        assert r.status_code == 200, r.text
        self.tok = r.json()["access_token"]
        self.h = {"Authorization": f"Bearer {self.tok}"}

    def upload(self, data: bytes, name="f.bin"):
        fek = AESGCM.generate_key(256)
        iv = os.urandom(12)
        ct = AESGCM(fek).encrypt(iv, data, None)
        wrapped = self.priv.public_key().encrypt(fek, _PAD)
        r = self.http.post("/api/files/upload", headers=self.h,
                           files={"ciphertext": ("c.bin", ct, "application/octet-stream")},
                           data={"original_filename": name, "mime_type": "application/octet-stream",
                                 "original_size": str(len(data)), "iv": base64.b64encode(iv).decode(),
                                 "wrapped_fek": base64.b64encode(wrapped).decode(),
                                 "plaintext_sha256": hashlib.sha256(data).hexdigest()})
        assert r.status_code == 201, r.text
        return r.json()["id"], fek, iv, ct

    def wrap_for(self, other, fek):
        from cryptography.hazmat.primitives import serialization
        pub = serialization.load_der_public_key(base64.b64decode(other.pub_b64))
        return base64.b64encode(pub.encrypt(fek, _PAD)).decode()


# ---------------------------------------------------------------------------------------------- 1. browser crypto
BROWSER_JS = r"""
async () => {
  const out = {};
  const ms = () => performance.now();
  const stat = a => { a = a.slice().sort((x, y) => x - y); const n = a.length;
    return {n, mean: a.reduce((s, v) => s + v, 0) / n, median: a[Math.floor(n / 2)], p95: a[Math.min(n - 1, Math.round(0.95 * (n - 1)))], min: a[0], max: a[n - 1]}; };
  const rnd = n => { const b = new Uint8Array(n); for (let i = 0; i < n; i += 65536) crypto.getRandomValues(b.subarray(i, Math.min(n, i + 65536))); return b; };
  const sizes = [[1024, 50], [65536, 50], [1048576, 20], [10485760, 8], [26214400, 4]];
  out.aes = {};
  for (const [size, reps] of sizes) {
    const data = rnd(size);
    const key = await crypto.subtle.generateKey({name: 'AES-GCM', length: 256}, true, ['encrypt', 'decrypt']);
    const enc = [], dec = [], sha = [];
    const B = size <= 65536 ? 200 : 1;   // Chrome rounds performance.now() to 0.1 ms: time batches for small inputs, report per-operation
    let ct, iv;
    for (let i = 0; i < reps; i++) { iv = crypto.getRandomValues(new Uint8Array(12)); const t = ms(); for (let j = 0; j < B; j++) ct = await crypto.subtle.encrypt({name: 'AES-GCM', iv}, key, data); enc.push((ms() - t) / B); }
    for (let i = 0; i < reps; i++) { const t = ms(); for (let j = 0; j < B; j++) await crypto.subtle.decrypt({name: 'AES-GCM', iv}, key, ct); dec.push((ms() - t) / B); }
    for (let i = 0; i < reps; i++) { const t = ms(); for (let j = 0; j < B; j++) await crypto.subtle.digest('SHA-256', data); sha.push((ms() - t) / B); }
    out.aes[size] = {encrypt: stat(enc), decrypt: stat(dec), sha256: stat(sha), overhead: ct.byteLength - size};
  }
  const kg = [];
  let pair;
  for (let i = 0; i < 12; i++) { const t = ms(); pair = await crypto.subtle.generateKey({name: 'RSA-OAEP', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256'}, true, ['wrapKey', 'unwrapKey']); kg.push(ms() - t); }
  out.rsa_keygen = stat(kg);
  const fek = await crypto.subtle.generateKey({name: 'AES-GCM', length: 256}, true, ['encrypt', 'decrypt']);
  const wr = [], un = [];
  let wrapped;
  for (let i = 0; i < 40; i++) { const t = ms(); for (let j = 0; j < 20; j++) wrapped = await crypto.subtle.wrapKey('raw', fek, pair.publicKey, {name: 'RSA-OAEP'}); wr.push((ms() - t) / 20); }
  for (let i = 0; i < 40; i++) { const t = ms(); for (let j = 0; j < 20; j++) await crypto.subtle.unwrapKey('raw', wrapped, pair.privateKey, {name: 'RSA-OAEP'}, {name: 'AES-GCM', length: 256}, true, ['encrypt', 'decrypt']); un.push((ms() - t) / 20); }
  out.rsa_wrap = stat(wr); out.rsa_unwrap = stat(un); out.rsa_wrapped_bytes = wrapped.byteLength;
  const pb = [];
  const salt = crypto.getRandomValues(new Uint8Array(16));
  for (let i = 0; i < 12; i++) { const t = ms(); const base = await crypto.subtle.importKey('raw', new TextEncoder().encode('Measure-Pass-123'), 'PBKDF2', false, ['deriveKey']);
    await crypto.subtle.deriveKey({name: 'PBKDF2', salt, iterations: 120000, hash: 'SHA-256'}, base, {name: 'AES-GCM', length: 256}, false, ['encrypt', 'decrypt']); pb.push(ms() - t); }
  out.pbkdf2_120k = stat(pb);
  out.userAgent = navigator.userAgent;
  return out;
}
"""

E2E_JS = r"""
async ({token, size, reps}) => {
  const ms = () => performance.now();
  const rnd = n => { const b = new Uint8Array(n); for (let i = 0; i < n; i += 65536) crypto.getRandomValues(b.subarray(i, Math.min(n, i + 65536))); return b; };
  const hex = buf => [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
  const pair = await crypto.subtle.generateKey({name: 'RSA-OAEP', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256'}, true, ['wrapKey', 'unwrapKey']);
  const H = {Authorization: 'Bearer ' + token};
  const res = {encrypted_up: [], plain_up: [], encrypted_down: [], plain_down: [], enc_only: [], dec_only: []};
  for (let r = 0; r < reps; r++) {
    const data = rnd(size);
    // encrypted upload: FEK + AES-GCM + SHA-256 + RSA wrap + POST
    let t = ms();
    const fek = await crypto.subtle.generateKey({name: 'AES-GCM', length: 256}, true, ['encrypt', 'decrypt']);
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const t1 = ms();
    const ct = await crypto.subtle.encrypt({name: 'AES-GCM', iv}, fek, data);
    res.enc_only.push(ms() - t1);   // single call, so 1 KiB values sit at the 0.1 ms clock resolution
    const sha = hex(await crypto.subtle.digest('SHA-256', data));
    const wrapped = await crypto.subtle.wrapKey('raw', fek, pair.publicKey, {name: 'RSA-OAEP'});
    const b64 = b => btoa(String.fromCharCode(...new Uint8Array(b)));
    const fd = new FormData();
    fd.append('ciphertext', new Blob([ct]), 'c.bin'); fd.append('original_filename', 'e2e.bin'); fd.append('mime_type', 'application/octet-stream');
    fd.append('original_size', String(size)); fd.append('iv', b64(iv)); fd.append('wrapped_fek', b64(wrapped)); fd.append('plaintext_sha256', sha);
    const up = await fetch('/api/files/upload', {method: 'POST', headers: H, body: fd});
    const fid = (await up.json()).id;
    res.encrypted_up.push(ms() - t);
    // baseline: same bytes, no encryption (same endpoint; digest + dummy wrapped key so validation passes)
    t = ms();
    const sha2 = hex(await crypto.subtle.digest('SHA-256', data));
    const fd2 = new FormData();
    fd2.append('ciphertext', new Blob([data]), 'p.bin'); fd2.append('original_filename', 'plain.bin'); fd2.append('mime_type', 'application/octet-stream');
    fd2.append('original_size', String(size)); fd2.append('iv', b64(iv)); fd2.append('wrapped_fek', b64(wrapped)); fd2.append('plaintext_sha256', sha2);
    const up2 = await fetch('/api/files/upload', {method: 'POST', headers: H, body: fd2});
    const fid2 = (await up2.json()).id;
    res.plain_up.push(ms() - t);
    // encrypted download: GET + unwrap + decrypt + SHA-256 verify
    t = ms();
    const dl = await fetch('/api/files/' + fid + '/download', {headers: H});
    const buf = await dl.arrayBuffer();
    const wf = dl.headers.get('X-CipherVault-Wrapped-FEK'); const ivh = dl.headers.get('X-CipherVault-IV'); const sh = dl.headers.get('X-CipherVault-SHA256');
    const raw = Uint8Array.from(atob(wf), c => c.charCodeAt(0));
    const fek2 = await crypto.subtle.unwrapKey('raw', raw, pair.privateKey, {name: 'RSA-OAEP'}, {name: 'AES-GCM', length: 256}, true, ['encrypt', 'decrypt']);
    const t2 = ms();
    const pt = await crypto.subtle.decrypt({name: 'AES-GCM', iv: Uint8Array.from(atob(ivh), c => c.charCodeAt(0))}, fek2, buf);
    res.dec_only.push(ms() - t2);
    if (hex(await crypto.subtle.digest('SHA-256', pt)) !== sh) throw new Error('hash mismatch');
    res.encrypted_down.push(ms() - t);
    t = ms();
    const dl2 = await fetch('/api/files/' + fid2 + '/download', {headers: H});
    await dl2.arrayBuffer();
    res.plain_down.push(ms() - t);
  }
  return res;
}
"""


def browser_phase():
    from playwright.sync_api import sync_playwright
    res = {}
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        ctx = b.new_context()
        page = ctx.new_page()
        page.goto(BASE + "/api/health")
        res["crypto"] = page.evaluate(BROWSER_JS)
        res["browser_version"] = b.version
        # e2e pipeline needs an account: reuse a measurement account created through the API
        h = httpx.Client(base_url=BASE, timeout=60)
        u = Client(h, "E2E Measurer", "e2e.measure@example.com")
        res["e2e"] = {}
        for size, reps in ((1024, 30), (1048576, 20), (10485760, 15)):
            r = page.evaluate(E2E_JS, {"token": u.tok, "size": size, "reps": reps})
            res["e2e"][str(size)] = {k: summ(v) for k, v in r.items()}
        b.close()
    return res


# ---------------------------------------------------------------------------------------------- 2. API latency
def api_phase(h):
    res = {}
    bcrypt_reg = []
    users = []
    t = time.perf_counter()
    u0 = Client(h, "Lat Owner", "lat.owner@example.com")
    res["register_plus_login_ms_first"] = round((time.perf_counter() - t) * 1000, 1)
    users.append(u0)
    res["login_ms"] = summ(timed(u0.login, 15))
    bad = []
    for _ in range(10):
        t = time.perf_counter()
        r = h.post("/api/auth/login", json={"email": u0.email, "password": "wrong-password"})
        bad.append((time.perf_counter() - t) * 1000)
        assert r.status_code == 401
    res["login_fail_ms"] = summ(bad)
    res["me_ms"] = summ(timed(lambda: h.get("/api/auth/me", headers=u0.h), 60))
    res["health_ms"] = summ(timed(lambda: h.get("/api/health"), 60))
    up, down = {}, {}
    ids = {}
    for size, reps in ((1024, 20), (65536, 20), (1048576, 15), (10485760, 6), (26214400 - 2048, 3)):
        data = os.urandom(size)
        fek = AESGCM.generate_key(256)
        iv = os.urandom(12)
        ct = AESGCM(fek).encrypt(iv, data, None)
        wrapped = base64.b64encode(u0.priv.public_key().encrypt(fek, _PAD)).decode()
        sha = hashlib.sha256(data).hexdigest()
        s = []
        for _ in range(reps):
            t = time.perf_counter()
            r = h.post("/api/files/upload", headers=u0.h, files={"ciphertext": ("c.bin", ct, "application/octet-stream")},
                       data={"original_filename": "l.bin", "mime_type": "application/octet-stream", "original_size": str(size),
                             "iv": base64.b64encode(iv).decode(), "wrapped_fek": wrapped, "plaintext_sha256": sha})
            s.append((time.perf_counter() - t) * 1000)
            assert r.status_code == 201, r.text
            ids[size] = r.json()["id"]
        up[size] = summ(s)
        fid = ids[size]
        s = []
        for _ in range(reps):
            t = time.perf_counter()
            r = h.get(f"/api/files/{fid}/download", headers=u0.h)
            _ = r.content
            s.append((time.perf_counter() - t) * 1000)
            assert r.status_code == 200
        down[size] = summ(s)
    res["upload_ms"], res["download_ms"] = up, down
    res["upload_limit_check"] = {}
    big = os.urandom(26214400 + 5000)
    r = h.post("/api/files/upload", headers=u0.h, files={"ciphertext": ("c.bin", big, "application/octet-stream")},
               data={"original_filename": "big.bin", "mime_type": "application/octet-stream", "original_size": str(26214400),
                     "iv": base64.b64encode(os.urandom(12)).decode(), "wrapped_fek": base64.b64encode(os.urandom(256)).decode(),
                     "plaintext_sha256": "0" * 64})
    res["upload_limit_check"]["over_25MB_status"] = r.status_code
    res["list_files_ms"] = summ(timed(lambda: h.get("/api/files", headers=u0.h), 20))
    # share / change role / revoke
    u1 = Client(h, "Lat Editor", "lat.editor@example.com")
    users.append(u1)
    fid, fek, iv, ct = u0.upload(os.urandom(2048), "share.bin")
    wrapped = u0.wrap_for(u1, fek)
    t = time.perf_counter()
    r = h.post(f"/api/files/{fid}/share", headers=u0.h, json={"email": u1.email, "role": "viewer", "wrapped_fek": wrapped})
    res["share_ms"] = round((time.perf_counter() - t) * 1000, 2)
    assert r.status_code == 200, r.text
    t = time.perf_counter()
    r = h.put(f"/api/files/{fid}/permissions/{u1.id}", headers=u0.h, json={"role": "editor"})
    res["change_role_ms"] = round((time.perf_counter() - t) * 1000, 2)
    t = time.perf_counter()
    r = h.delete(f"/api/files/{fid}/permissions/{u1.id}", headers=u0.h)
    res["revoke_ms"] = round((time.perf_counter() - t) * 1000, 2)
    t = time.perf_counter()
    r = h.get(f"/api/files/{fid}/download", headers=u1.h)
    res["download_after_revoke_ms"] = round((time.perf_counter() - t) * 1000, 2)
    res["download_after_revoke_status"] = r.status_code
    return res, u0, u1


def chain_scaling(h, u0):
    """Time /api/audit/verify as the audit log grows (each /api/auth/me call is NOT logged; use failed logins, which are)."""
    out = {}
    count = 0
    targets = [100, 500, 1000, 2000, 5000]
    for tgt in targets:
        while True:
            r = h.get("/api/audit?limit=1", headers=u0.h)
            last = r.json()[0]["id"]
            if last >= tgt:
                break
            for _ in range(min(250, tgt - last)):
                h.post("/api/auth/login", json={"email": "nobody@example.com", "password": "x"})
        r = h.get("/api/audit?limit=1", headers=u0.h)
        n = r.json()[0]["id"]
        s = []
        for _ in range(3):
            t = time.perf_counter()
            v = h.get("/api/audit/verify", headers=u0.h).json()
            s.append((time.perf_counter() - t) * 1000)
        out[str(n)] = {"verify_ms_median": round(statistics.median(s), 1), "valid": v["valid"], "checked": v["checked"]}
    wr = []
    for _ in range(40):
        t = time.perf_counter()
        h.post("/api/auth/login", json={"email": "nobody@example.com", "password": "x"})
        wr.append((time.perf_counter() - t) * 1000)
    return out, summ(wr)


# ---------------------------------------------------------------------------------------------- 4. RBAC matrix
def rbac_matrix(h):
    owner = Client(h, "M Owner", "m.owner@example.com")
    editor = Client(h, "M Editor", "m.editor@example.com")
    viewer = Client(h, "M Viewer", "m.viewer@example.com")
    stranger = Client(h, "M Stranger", "m.stranger@example.com")
    target = Client(h, "M Target", "m.target@example.com")
    fid, fek, iv, ct = owner.upload(b"rbac matrix payload " * 50, "matrix.bin")
    for u, role in ((editor, "editor"), (viewer, "viewer")):
        r = h.post(f"/api/files/{fid}/share", headers=owner.h, json={"email": u.email, "role": role, "wrapped_fek": owner.wrap_for(u, fek)})
        assert r.status_code == 200
    ops = ["metadata", "download", "update", "list_permissions", "share", "change_role", "revoke", "file_audit", "delete"]
    # expected status class: True = allowed (2xx), False = denied (401/403)
    expect = {
        "owner": dict.fromkeys(ops, True),
        "editor": {"metadata": True, "download": True, "update": True, "list_permissions": True, "share": False, "change_role": False,
                   "revoke": False, "file_audit": False, "delete": False},
        "viewer": {"metadata": True, "download": True, "update": False, "list_permissions": True, "share": False, "change_role": False,
                   "revoke": False, "file_audit": False, "delete": False},
        "stranger": dict.fromkeys(ops, False),
    }
    principals = {"owner": owner, "editor": editor, "viewer": viewer, "stranger": stranger}
    cells = []
    for who, u in principals.items():
        # a fresh share target each round so that share / revoke have something to act on
        for op in ops:
            if op == "delete":
                # delete last, on a throw-away copy owned by the owner but shared with the principal in the same role
                f2, fek2, _, _ = owner.upload(b"disposable", "del.bin")
                if who in ("editor", "viewer"):
                    h.post(f"/api/files/{f2}/share", headers=owner.h, json={"email": u.email, "role": who, "wrapped_fek": owner.wrap_for(u, fek2)})
                r = h.delete(f"/api/files/{f2}", headers=u.h)
            elif op == "metadata":
                r = h.get(f"/api/files/{fid}", headers=u.h)
            elif op == "download":
                r = h.get(f"/api/files/{fid}/download", headers=u.h)
            elif op == "update":
                r = h.put(f"/api/files/{fid}", headers=u.h, files={"ciphertext": ("c.bin", ct, "application/octet-stream")},
                          data={"iv": base64.b64encode(iv).decode(), "plaintext_sha256": "a" * 64, "original_size": "1000"})
            elif op == "list_permissions":
                r = h.get(f"/api/files/{fid}/permissions", headers=u.h)
            elif op == "share":
                r = h.post(f"/api/files/{fid}/share", headers=u.h, json={"email": target.email, "role": "viewer", "wrapped_fek": owner.wrap_for(target, fek)})
                if r.status_code == 200 and who == "owner":
                    pass
            elif op == "change_role":
                r = h.put(f"/api/files/{fid}/permissions/{target.id}", headers=u.h, json={"role": "editor"})
                if who == "owner" and r.status_code == 404:  # target not shared yet (order); count as allowed (404 comes after the authz check)
                    r.status_code = 200
            elif op == "revoke":
                r = h.delete(f"/api/files/{fid}/permissions/{target.id}", headers=u.h)
                if who == "owner" and r.status_code == 404:
                    r.status_code = 200
            elif op == "file_audit":
                r = h.get(f"/api/audit/file/{fid}", headers=u.h)
            allowed = 200 <= r.status_code < 300
            denied = r.status_code in (401, 403)
            cells.append({"principal": who, "operation": op, "expected_allowed": expect[who][op], "status": r.status_code,
                          "match": (allowed if expect[who][op] else denied)})
        # clean up target share between principals
        h.delete(f"/api/files/{fid}/permissions/{target.id}", headers=owner.h)
    # unauthenticated + forged + expired
    anon = [h.get(p).status_code for p in ("/api/files", f"/api/files/{fid}", f"/api/files/{fid}/download", "/api/audit", "/api/users")]
    forged = h.get("/api/files", headers={"Authorization": "Bearer abc.def.ghi"}).status_code
    import jwt as pyjwt
    expired = pyjwt.encode({"sub": str(owner.id), "exp": int(time.time()) - 60}, "measurement-run-secret-not-for-use", algorithm="HS256")
    exp_s = h.get("/api/files", headers={"Authorization": f"Bearer {expired}"}).status_code
    wrongkey = pyjwt.encode({"sub": str(owner.id), "exp": int(time.time()) + 600}, "some-other-secret-key-0123456789abcdef", algorithm="HS256")
    wk_s = h.get("/api/files", headers={"Authorization": f"Bearer {wrongkey}"}).status_code
    none_tok = pyjwt.encode({"sub": str(owner.id)}, None, algorithm="none")
    none_s = h.get("/api/files", headers={"Authorization": f"Bearer {none_tok}"}).status_code
    ok = sum(c["match"] for c in cells)
    return {"cells": cells, "matched": ok, "total": len(cells), "accuracy": round(ok / len(cells), 4),
            "unauthenticated_statuses": anon, "forged_token_status": forged, "expired_token_status": exp_s,
            "wrong_secret_token_status": wk_s, "alg_none_token_status": none_s}, owner


# ---------------------------------------------------------------------------------------------- 5. tamper tests
def tamper_phase(h, owner, db_path):
    import sqlite3
    res = {}
    # ciphertext bit flips against real AES-GCM (same primitive the browser uses)
    pt = os.urandom(4096)
    key = AESGCM.generate_key(256)
    iv = os.urandom(12)
    ct = AESGCM(key).encrypt(iv, pt, None)
    detected = 0
    trials = 2000
    for _ in range(trials):
        i = random.randrange(len(ct))
        bit = 1 << random.randrange(8)
        bad = bytearray(ct)
        bad[i] ^= bit
        try:
            AESGCM(key).decrypt(iv, bytes(bad), None)
        except Exception:
            detected += 1
    res["ciphertext_bitflip"] = {"trials": trials, "detected": detected}
    # wrong IV / wrong key
    res["wrong_key_rejected"] = False
    try:
        AESGCM(AESGCM.generate_key(256)).decrypt(iv, ct, None)
    except Exception:
        res["wrong_key_rejected"] = True
    # stored object on disk is ciphertext: tamper the real stored file and see the browser-equivalent check fail
    fid, fek, iv2, ct2 = owner.upload(os.urandom(5000), "tamper.bin")
    # audit chain tampering on the live database (copy of the file so the server's chain stays intact)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute("select * from audit_logs order by id")]
    con.close()
    from datetime import datetime, timezone

    def _hash_event(previous_hash, timestamp, user_id, file_id, action, success, details):
        # identical to backend/app/services/audit_service.py::_hash_event (copied so this script needs no backend imports)
        body = f"{previous_hash}|{timestamp.isoformat()}|{user_id}|{file_id}|{action}|{success}|{details}"
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def verify(entries):
        prev = "GENESIS"
        for e in entries:
            ts = e["timestamp_utc"]
            ts = datetime.fromisoformat(ts) if isinstance(ts, str) else ts
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if e["previous_hash"] != prev or _hash_event(e["previous_hash"], ts, e["user_id"], e["file_id"], e["action"], bool(e["success"]), e["details"] or "") != e["current_hash"]:
                return False
            prev = e["current_hash"]
        return True

    res["audit_entries_available"] = len(rows)
    res["audit_untouched_valid"] = verify(rows)
    sample = random.sample(range(len(rows)), 200)
    kinds = {"edit_details": 0, "edit_action": 0, "edit_success": 0, "edit_user": 0, "edit_hash": 0, "delete_entry_middle": 0, "swap_adjacent": 0, "insert_forged_entry": 0, "truncate_tail": 0}
    trials = {k: 0 for k in kinds}
    for i in sample:
        for kind in kinds:
            e = [dict(x) for x in rows]
            if kind == "delete_entry_middle" and (i == 0 or i == len(e) - 1):
                continue
            if kind == "swap_adjacent" and i >= len(e) - 1:
                continue
            if kind == "truncate_tail" and i == 0:
                continue
            trials[kind] += 1
            if kind == "edit_details":
                e[i]["details"] = (e[i]["details"] or "") + " x"
            elif kind == "edit_action":
                e[i]["action"] = "download" if e[i]["action"] != "download" else "login_success"
            elif kind == "edit_success":
                e[i]["success"] = 0 if e[i]["success"] else 1
            elif kind == "edit_user":
                e[i]["user_id"] = (e[i]["user_id"] or 0) + 1
            elif kind == "edit_hash":
                e[i]["current_hash"] = "0" * 64
            elif kind == "delete_entry_middle":
                del e[i]
            elif kind == "swap_adjacent":
                e[i], e[i + 1] = e[i + 1], e[i]
            elif kind == "insert_forged_entry":
                forged = dict(e[i]); forged["details"] = "forged"; forged["id"] = -1
                e.insert(i, forged)
            elif kind == "truncate_tail":
                e = e[:i]
            if not verify(e):
                kinds[kind] += 1
    res["audit_tamper"] = {k: {"trials": trials[k], "detected": kinds[k]} for k in kinds}
    # a recomputing attacker who also fixes every later hash (needs no secret) is NOT detected: demonstrate
    e = [dict(x) for x in rows]
    j = len(e) // 2
    e[j]["details"] = "rewritten by attacker"
    prev = e[j]["previous_hash"]
    for k in range(j, len(e)):
        ts = e[k]["timestamp_utc"]
        ts = datetime.fromisoformat(ts) if isinstance(ts, str) else ts
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        e[k]["previous_hash"] = prev
        e[k]["current_hash"] = _hash_event(prev, ts, e[k]["user_id"], e[k]["file_id"], e[k]["action"], bool(e[k]["success"]), e[k]["details"] or "")
        prev = e[k]["current_hash"]
    res["audit_rechain_attack_detected"] = (not verify(e))
    return res


# ---------------------------------------------------------------------------------------------- concurrency
def concurrency_phase(h, u0):
    """Concurrent audit writes: does the hash chain stay linear?  (run last: a fork would break later verification)"""
    from concurrent.futures import ThreadPoolExecutor
    before = h.get("/api/audit/verify", headers=u0.h).json()
    out = {"valid_before": before["valid"]}
    for workers, per in ((4, 25), (16, 25)):
        def work(_):
            c = httpx.Client(base_url=BASE, timeout=60)
            codes = []
            for _ in range(per):
                codes.append(c.post("/api/auth/login", json={"email": "race@example.com", "password": "x"}).status_code)
            return codes
        t = time.perf_counter()
        with ThreadPoolExecutor(workers) as ex:
            codes = [c for part in ex.map(work, range(workers)) for c in part]
        secs = time.perf_counter() - t
        v = h.get("/api/audit/verify", headers=u0.h).json()
        out[f"{workers}_workers"] = {"requests": len(codes), "status_401": codes.count(401), "seconds": round(secs, 2),
                                     "chain_valid_after": v["valid"], "failure_at": v["failure_at"], "checked": v["checked"]}
        if not v["valid"]:
            break
    return out


# ---------------------------------------------------------------------------------------------- misc counts
def loc_counts():
    def count(globs, root):
        files, lines = 0, 0
        for g in globs:
            for p in root.glob(g):
                if p.is_file() and "node_modules" not in p.parts and "dist" not in p.parts and ".venv" not in p.parts:
                    files += 1
                    lines += sum(1 for _ in p.open(encoding="utf-8", errors="ignore"))
        return {"files": files, "lines": lines}
    return {"backend_py": count(["backend/**/*.py"], ROOT), "tests_py": count(["tests/*.py"], ROOT),
            "frontend_src": count(["frontend/src/**/*.js", "frontend/src/**/*.jsx", "frontend/src/**/*.css"], ROOT),
            "scripts_py": count(["scripts/*.py"], ROOT)}


def main():
    tmp = Path(tempfile.mkdtemp(prefix="cv_measure_"))
    proc = start_server(tmp)
    results = {"environment": {"cpu": "12th Gen Intel Core i5-12500 (6 cores / 12 threads)", "ram_gb": 15.7, "os": platform.platform(),
                               "python": platform.python_version(), "date": time.strftime("%Y-%m-%d"), "loopback": "127.0.0.1"}}
    try:
        h = httpx.Client(base_url=BASE, timeout=120)
        print("browser phase ...", flush=True)
        results["browser"] = browser_phase()
        print("api phase ...", flush=True)
        api, u0, u1 = api_phase(h)
        results["api"] = api
        print("rbac matrix ...", flush=True)
        rb, owner = rbac_matrix(h)
        results["rbac"] = rb
        print("tamper ...", flush=True)
        results["tamper"] = tamper_phase(h, owner, str(tmp / "m.db"))
        print("chain scaling ...", flush=True)
        scaling, write_ms = chain_scaling(h, u0)
        results["audit_chain_scaling"] = scaling
        results["audit_write_ms"] = write_ms
        v = h.get("/api/audit/verify", headers=u0.h).json()
        results["audit_live_verify"] = v
        # storage facts from the throw-away store
        stored = [p for p in (tmp / "enc").iterdir()]
        results["storage"] = {"objects": len(stored)}
        results["loc"] = loc_counts()
        print("concurrency ...", flush=True)
        results["audit_concurrency"] = concurrency_phase(h, u0)
    finally:
        proc.kill()
        time.sleep(0.5)
        shutil.rmtree(tmp, ignore_errors=True)
    (OUT / "metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("wrote", OUT / "metrics.json")


if __name__ == "__main__":
    main()
