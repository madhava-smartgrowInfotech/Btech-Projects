"""Writes docs/REPORT_FACTS.md from docs/metrics/metrics.json and the project files.   python -m scripts.docs.make_report_facts"""

import os

from . import facts as F


def main():
    A, C, E, R, T, S, K = F.AES, F.CRY, F.E2E, F.RBAC, F.TAMPER, F.SCALE, F.CONC
    L = []
    w = L.append
    w("# REPORT FACTS - CipherVault (CSE-C-C13)\n")
    w("Single reference for every document. All numbers come from `docs/metrics/metrics.json` (scripts/measure_metrics.py, "
      f"run {F.ENV['date']}), `evaluation_results.txt` (scripts/evaluate.py), the test runs below or the code itself.\n")
    w("## 1. Project\n")
    w(f"- Title: {F.TITLE}\n- Product: CipherVault. Batch {F.BATCH_NO} ({F.SECTION}); guide {F.GUIDE}")
    w("- Students: " + "; ".join(f"{n} ({r})" for n, r in F.STUDENTS))
    w(f"- Ports: backend {F.API_PORT}, frontend {F.WEB_PORT}. Stack: FastAPI, SQLAlchemy (SQLite default, PostgreSQL via Docker), PyJWT, bcrypt (cost {F.BCRYPT_COST}), "
      "React 19 + Vite 8, Web Crypto API, Recharts, three.js, Framer Motion.")
    w(f"- Base paper (declared): {F.BASE_PAPER}")
    w(f"- Closest-architecture paper (downloaded, `archived_base_papers/`): {F.NEAR_PAPER}")
    w("- **No ML model and no dataset.** The system is cryptographic and access-control software; there is no training, accuracy or F1. "
      "Demo data are fictional files created by the in-app demo login (5 synthetic files; accounts owner|editor|viewer@example.com).\n")
    w("## 2. Architecture\n")
    w("- Browser (React + Web Crypto) is the trusted crypto endpoint: generates RSA-2048-OAEP key pair at registration, encrypts the private key with a PBKDF2-HMAC-SHA-256 "
      f"({F.PBKDF2_ITER:,} iterations, 16-byte salt) derived AES-256-GCM key, encrypts each file with a fresh random 256-bit AES-GCM key (FEK) and 12-byte IV, "
      "computes SHA-256 of the plaintext, wraps the FEK with the owner's (later each recipient's) RSA public key, uploads ciphertext + IV + wrapped FEK + hash.")
    w("- FastAPI backend: auth (bcrypt, JWT HS256, "
      f"{F.JWT_MINUTES} min expiry, in-memory login throttle {F.LOGIN_LIMIT[0]} attempts / {F.LOGIN_LIMIT[1]} s per IP+email), RBAC (owner / editor / viewer, checked per request), ciphertext store on filesystem "
      f"(`storage/encrypted/<random 32-hex name>`), SQL metadata, hash-chained audit log. Upload limit {F.UPLOAD_LIMIT_MB} MB (413 above, measured).")
    w("- Server never receives plaintext or private keys. Server holds: password hashes, RSA public keys, password-encrypted private-key bundles, ciphertext, IV, per-recipient wrapped FEKs, plaintext SHA-256, audit log.")
    w("- RBAC: owner = read/update/delete/share/change role/revoke/file-audit; editor = read + update; viewer = read; stranger = nothing. Global `users.role` column exists (default 'user') but is not used for decisions.")
    w("- Audit: `current_hash = SHA-256(prev|iso-timestamp|user|file|action|success|details)`, first entry prev='GENESIS'; `/api/audit/verify` recomputes the chain and itself logs an event.\n")
    w("## 3. Endpoints (24)\n")
    w("health, config; auth: register, login, me, PUT keys, key-bundle, logout; users: list(q), public-key; files: upload, list, shared, get, download, PUT update, delete; "
      "sharing: share, list permissions, PUT change role, DELETE revoke; audit: list, per-file, verify. Full table in `docs/FRONTEND_PLAN.md`.\n")
    w("## 4. Database (4 tables)\n")
    w("users(id, name, email unique, password_hash, role, public_key, encrypted_private_key, private_key_salt, is_active, created_at, updated_at); "
      "files(id, owner_id FK, original_filename, stored_filename unique, mime_type, encrypted_size, original_size, iv, owner_wrapped_fek, plaintext_sha256, timestamps; index owner+created); "
      "file_permissions(id, file_id FK, user_id FK, role viewer|editor, wrapped_fek, timestamps; unique(file_id,user_id)); "
      "audit_logs(id, timestamp_utc, user_id FK null, file_id FK null, action, success, ip_address, details<=2000, previous_hash, current_hash; indexes).\n")
    w("## 5. Measured results (host: i5-12500, 6C/12T, 15.7 GB, Windows 11, Chrome " + F.BR["browser_version"] + ", loopback 127.0.0.1; other sessions were using the CPU - treat as indicative, run-to-run spread up to ~3x at 10 MB)\n")
    w("### 5.1 Browser Web Crypto (median ms per operation; 1 KiB and 64 KiB timed in batches of 200 because Chrome's clock is 0.1 ms)\n")
    w("| Size | AES-256-GCM encrypt | decrypt | SHA-256 | overhead B |\n|---|---|---|---|---|")
    for s, lab in (("1024", "1 KiB"), ("65536", "64 KiB"), ("1048576", "1 MiB"), ("10485760", "10 MiB"), ("26214400", "25 MiB")):
        v = A[s]
        w(f"| {lab} | {F.ms(v['encrypt']['median'])} | {F.ms(v['decrypt']['median'])} | {F.ms(v['sha256']['median'])} | {v['overhead']} |")
    w(f"\nRSA-2048 key generation median {F.ms(C['rsa_keygen']['median'])} ms (n=12, p95 {F.ms(C['rsa_keygen']['p95'])}); RSA-OAEP wrap {F.ms(C['rsa_wrap']['median'])} ms; unwrap {F.ms(C['rsa_unwrap']['median'])} ms; "
      f"wrapped FEK {C['rsa_wrapped_bytes']} B; PBKDF2 120k iterations median {F.ms(C['pbkdf2_120k']['median'])} ms.\n")
    w("### 5.2 End-to-end browser pipeline vs plain (unencrypted) transfer on the same endpoint (median / p95 ms)\n")
    w("| Size | encrypted upload | plain upload | encrypted download+decrypt+verify | plain download | AES only enc / dec |\n|---|---|---|---|---|---|")
    for s, lab in (("1024", "1 KiB"), ("1048576", "1 MiB"), ("10485760", "10 MiB")):
        v = E[s]
        w(f"| {lab} | {F.ms(v['encrypted_up']['median'])} / {F.ms(v['encrypted_up']['p95'])} | {F.ms(v['plain_up']['median'])} / {F.ms(v['plain_up']['p95'])} | "
          f"{F.ms(v['encrypted_down']['median'])} / {F.ms(v['encrypted_down']['p95'])} | {F.ms(v['plain_down']['median'])} / {F.ms(v['plain_down']['p95'])} | "
          f"{F.ms(v['enc_only']['median'])} / {F.ms(v['dec_only']['median'])} |")
    w("\n### 5.3 API latency over loopback (median / p95 ms)\n")
    for k, lab in (("login_ms", "login (bcrypt cost 12)"), ("login_fail_ms", "failed login"), ("me_ms", "GET /auth/me"), ("health_ms", "GET /health"), ("list_files_ms", "list files (65 owned files)")):
        v = F.API[k]
        w(f"- {lab}: {F.ms(v['median'])} / {F.ms(v['p95'])} (n={v['n']})")
    for k, lab in (("upload_ms", "upload"), ("download_ms", "download")):
        w(f"- {lab}: " + "; ".join(f"{int(s) // 1024 if int(s) < 1048576 else round(int(s) / 1048576, 1)} {'KiB' if int(s) < 1048576 else 'MiB'}: {F.ms(v['median'])} / {F.ms(v['p95'])}" for s, v in F.API[k].items()))
    w(f"- share {F.ms(F.API['share_ms'])} ms; change role {F.ms(F.API['change_role_ms'])}; revoke {F.ms(F.API['revoke_ms'])}; download after revoke -> HTTP {F.API['download_after_revoke_status']}; upload > 25 MB -> HTTP {F.API['upload_limit_check']['over_25MB_status']}")
    w(f"- audit write (one logged event, failed login of unknown user): median {F.ms(F.M['audit_write_ms']['median'])} ms, p95 {F.ms(F.M['audit_write_ms']['p95'])}\n")
    w("### 5.4 Access control (live API, expected vs observed)\n")
    w(f"- RBAC matrix 4 principals x 9 operations = {R['total']} cells, {R['matched']} matched ({F.pct(R['accuracy'])}); unauthenticated requests -> {set(R['unauthenticated_statuses'])}; "
      f"forged / expired / wrong-secret / alg=none tokens -> {R['forged_token_status']} / {R['expired_token_status']} / {R['wrong_secret_token_status']} / {R['alg_none_token_status']}.")
    w("- This is exhaustive over the implemented operations on one file, not a user study; the base-paper-like figure of 98.6% (IJEDR, 900 attempts by 50 users) is a different experiment.\n")
    w("### 5.5 Integrity and tamper evidence\n")
    w(f"- Ciphertext bit flips: {T['ciphertext_bitflip']['detected']}/{T['ciphertext_bitflip']['trials']} detected by AES-GCM; wrong key rejected: {T['wrong_key_rejected']}.")
    for k, v in T["audit_tamper"].items():
        w(f"- Audit {k}: {v['detected']}/{v['trials']} detected")
    w(f"- A rewrite that recomputes every later hash is detected: {T['audit_rechain_attack_detected']} (False = NOT detected: the chain has no secret key or external anchor).")
    w("- **Tail truncation is not detected** (0/199): the verifier only checks internal consistency.")
    w("- Chain verification time grows linearly: " + "; ".join(f"{n} entries {v['verify_ms_median']} ms" for n, v in S.items()) + ".")
    w(f"- **Defect found:** concurrent audit writers fork the chain. {K['4_workers']['requests']} concurrent failed logins (4 workers) -> chain valid after: {K['4_workers']['chain_valid_after']} "
      f"(first bad entry {K['4_workers']['failure_at']}). `record_event` reads the last hash and commits without a lock; single-writer assumption. Documented, not fixed.\n")
    w("## 6. Tests\n")
    w(f"- pytest: {F.PYTEST_PASSED}/{F.PYTEST_TOTAL} passed in about {F.PYTEST_SECONDS:.0f} s (auth 6, crypto 5, files 3, rbac 5, audit 2).")
    w(f"- scripts/evaluate.py: {F.EVAL_PASSED}/{F.EVAL_TOTAL} checks (note: its 'browser_*' timings are Python `cryptography` timings, not browser timings - superseded by 5.1).")
    w(f"- scripts/smoke_test.py: API end-to-end {F.E2E_PASSED}/{F.E2E_TOTAL}; real-browser UI walk {F.UI_PASSED}/{F.UI_TOTAL} (against backend 8413 + Vite 5413).")
    w("- Not tested: multi-user load, >25 MB files, Firefox/Safari, PostgreSQL path, Docker build, accessibility audit with a screen reader.\n")
    w("## 7. Code size\n")
    w(f"- Backend {F.LOC['backend_py']['lines']} lines / {F.LOC['backend_py']['files']} files; tests {F.LOC['tests_py']['lines']} / {F.LOC['tests_py']['files']}; frontend src {F.LOC['frontend_src']['lines']} / {F.LOC['frontend_src']['files']}; scripts {F.LOC['scripts_py']['lines']} / {F.LOC['scripts_py']['files']}.\n")
    w("## 8. Known limitations (from code)\n")
    w("- Revocation deletes the server-side wrapped FEK but cannot recall a key or ciphertext the user already downloaded; no re-keying on revoke.\n"
      "- An editor's update re-encrypts under the existing FEK with a fresh IV (random 96-bit IV, same key: collision bound applies to very many updates).\n"
      "- Server serves the JavaScript that does the crypto: a compromised server could ship malicious JS (the MEGA-style trust problem).\n"
      "- File name, size, MIME type, owner and timestamps are stored in clear metadata; password loss = data loss; no MFA; JWT in sessionStorage (XSS exposure); in-memory throttle resets on restart; "
      "`GET /api/audit` shows the global event list to any authenticated user; whole-file in-memory encryption (25 MB cap), no chunking; SQLite default.\n"
      "- `PUT /api/files/{id}` by an editor does not validate the new ciphertext/IV pairing (server cannot); the client verifies SHA-256 on download.\n")
    w("## 9. Screenshot inventory (`docs/screenshots/`, 1440x900 unless noted, real demo data)\n")
    for f in sorted(os.listdir(F.SHOTS)):
        w(f"- {f}")
    w("\nOlder 9 screenshots of the previous UI sit in `screenshots/` (not used).\n")
    w("## 10. Literature (verified)\n")
    w(f"- Base paper: {F.BASE_PAPER} Uses ECC-based dual-attribute ABE + ClinicalBERT + Hyperledger Fabric for EHR; crypto timings on HPE server (E5-2620 v3) and Raspberry Pi 3 B+ (OpenSSL); no file-storage product, no audit-log latency, no RBAC.")
    w(f"- {F.NEAR_PAPER} Reports (50 users, 3 roles): +320 ms upload for a 10 MB file, 98.6% access-control accuracy (13 misclassified of 900), 0 exposure events in 30 days, 100% audit tamper detection (50 events), PBKDF2 310,000 iterations, 4 MB chunking, TOTP MFA, ECDSA-signed log entries, S3 + Vault.")
    w("- Geocrypt (Thenmozhi, Saralesh, Sakthi), ITM Web of Conferences 82, 03019, 2026, doi 10.1051/itmconf/20268203019: RSA + geo/time access + Ethereum smart contracts (Truffle, Ganache).")
    w("- Saginayev et al., Computing & Engineering 2(2):1-7, 2024, doi 10.51301/ce.2024.i2.01: AES-256 + RSA + SHA-256 hybrid cloud storage.")
    w("- Backendal, Haller, Paterson, 'MEGA: Malleable Encryption Goes Awry', IEEE S&P 2023, pp. 146-163.")
    w("- Batch survey items 2-4 (IRJMETS 2026 'Secure file storage on cloud using AES encryption'; ICPCSN 2026 'Secure cloud-based file storage system with enhanced data integrity and access control'; "
      "'An integrated image encryption and secure transmission scheme ... chaotic mapping') could NOT be located online: listed with 'not independently verified', no results quoted.\n")
    out = os.path.join(F.DOCS, "REPORT_FACTS.md")
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
