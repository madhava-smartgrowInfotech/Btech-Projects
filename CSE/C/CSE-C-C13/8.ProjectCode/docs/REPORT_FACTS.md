# REPORT FACTS - CipherVault (CSE-C-C13)

Single reference for every document. All numbers come from `docs/metrics/metrics.json` (scripts/measure_metrics.py, run 2026-10-22), `evaluation_results.txt` (scripts/evaluate.py), the test runs below or the code itself.

## 1. Project

- Title: Secure File Storage System with Encryption and Role-Based Access Control (RBAC)
- Product: CipherVault. Batch C13 (CSE-C); guide D V V Deepthi
- Students: Pramod Reddy Yalala (23K91A05J9); Pendela Vyshnavi (23K91A05J1); Luke Abraham Sam (23K91A05D4); Mudavath Suresh (23K91A05G2)
- Ports: backend 8413, frontend 5413. Stack: FastAPI, SQLAlchemy (SQLite default, PostgreSQL via Docker), PyJWT, bcrypt (cost 12), React 19 + Vite 8, Web Crypto API, Recharts, three.js, Framer Motion.
- Base paper (declared): A. Nekouie, M. Vafaei Jahan, M. H. Moattar and R. Sheibani, "Secure electronic health record access control via blockchain, dual-attribute encryption, and large language model-based attribute extraction," Scientific Reports, vol. 16, art. 8673, 2026, doi: 10.1038/s41598-026-39690-2.
- Closest-architecture paper (downloaded, `archived_base_papers/`): G. Sowmiya, R. Nivas and E. Vikram, "Secure cloud file storage architecture with client-side encryption and access control," Int. J. Eng. Develop. Res. (IJEDR), vol. 14, no. 2, pp. 576-579, Apr. 2026, paper IJEDR2602501.
- **No ML model and no dataset.** The system is cryptographic and access-control software; there is no training, accuracy or F1. Demo data are fictional files created by the in-app demo login (5 synthetic files; accounts owner|editor|viewer@example.com).

## 2. Architecture

- Browser (React + Web Crypto) is the trusted crypto endpoint: generates RSA-2048-OAEP key pair at registration, encrypts the private key with a PBKDF2-HMAC-SHA-256 (120,000 iterations, 16-byte salt) derived AES-256-GCM key, encrypts each file with a fresh random 256-bit AES-GCM key (FEK) and 12-byte IV, computes SHA-256 of the plaintext, wraps the FEK with the owner's (later each recipient's) RSA public key, uploads ciphertext + IV + wrapped FEK + hash.
- FastAPI backend: auth (bcrypt, JWT HS256, 120 min expiry, in-memory login throttle 20 attempts / 300 s per IP+email), RBAC (owner / editor / viewer, checked per request), ciphertext store on filesystem (`storage/encrypted/<random 32-hex name>`), SQL metadata, hash-chained audit log. Upload limit 25 MB (413 above, measured).
- Server never receives plaintext or private keys. Server holds: password hashes, RSA public keys, password-encrypted private-key bundles, ciphertext, IV, per-recipient wrapped FEKs, plaintext SHA-256, audit log.
- RBAC: owner = read/update/delete/share/change role/revoke/file-audit; editor = read + update; viewer = read; stranger = nothing. Global `users.role` column exists (default 'user') but is not used for decisions.
- Audit: `current_hash = SHA-256(prev|iso-timestamp|user|file|action|success|details)`, first entry prev='GENESIS'; `/api/audit/verify` recomputes the chain and itself logs an event.

## 3. Endpoints (24)

health, config; auth: register, login, me, PUT keys, key-bundle, logout; users: list(q), public-key; files: upload, list, shared, get, download, PUT update, delete; sharing: share, list permissions, PUT change role, DELETE revoke; audit: list, per-file, verify. Full table in `docs/FRONTEND_PLAN.md`.

## 4. Database (4 tables)

users(id, name, email unique, password_hash, role, public_key, encrypted_private_key, private_key_salt, is_active, created_at, updated_at); files(id, owner_id FK, original_filename, stored_filename unique, mime_type, encrypted_size, original_size, iv, owner_wrapped_fek, plaintext_sha256, timestamps; index owner+created); file_permissions(id, file_id FK, user_id FK, role viewer|editor, wrapped_fek, timestamps; unique(file_id,user_id)); audit_logs(id, timestamp_utc, user_id FK null, file_id FK null, action, success, ip_address, details<=2000, previous_hash, current_hash; indexes).

## 5. Measured results (host: i5-12500, 6C/12T, 15.7 GB, Windows 11, Chrome 155.0.8059.85, loopback 127.0.0.1; other sessions were using the CPU - treat as indicative, run-to-run spread up to ~3x at 10 MB)

### 5.1 Browser Web Crypto (median ms per operation; 1 KiB and 64 KiB timed in batches of 200 because Chrome's clock is 0.1 ms)

| Size | AES-256-GCM encrypt | decrypt | SHA-256 | overhead B |
|---|---|---|---|---|
| 1 KiB | 0.008 | 0.009 | 0.006 | 16 |
| 64 KiB | 0.059 | 0.066 | 0.043 | 16 |
| 1 MiB | 2.40 | 2.00 | 1.30 | 16 |
| 10 MiB | 23.8 | 26.2 | 12.9 | 16 |
| 25 MiB | 53.8 | 50.9 | 26.4 | 16 |

RSA-2048 key generation median 102 ms (n=12, p95 158); RSA-OAEP wrap 0.030 ms; unwrap 0.71 ms; wrapped FEK 256 B; PBKDF2 120k iterations median 32.8 ms.

### 5.2 End-to-end browser pipeline vs plain (unencrypted) transfer on the same endpoint (median / p95 ms)

| Size | encrypted upload | plain upload | encrypted download+decrypt+verify | plain download | AES only enc / dec |
|---|---|---|---|---|---|
| 1 KiB | 30.4 / 82.5 | 28.9 / 73.7 | 30.4 / 48.4 | 28.6 / 94.6 | 0.000 / 0.10 |
| 1 MiB | 63.0 / 107 | 52.9 / 97.8 | 61.0 / 161 | 51.0 / 94.5 | 2.10 / 2.00 |
| 10 MiB | 209 / 352 | 194 / 258 | 184 / 236 | 157 / 197 | 20.8 / 16.9 |

### 5.3 API latency over loopback (median / p95 ms)

- login (bcrypt cost 12): 308 / 349 (n=15)
- failed login: 326 / 372 (n=10)
- GET /auth/me: 6.32 / 17.7 (n=60)
- GET /health: 1.68 / 2.69 (n=60)
- list files (65 owned files): 40.3 / 58.9 (n=20)
- upload: 1 KiB: 27.2 / 38.3; 64 KiB: 32.4 / 44.4; 1.0 MiB: 44.5 / 70.3; 10.0 MiB: 139 / 163; 25.0 MiB: 288 / 339
- download: 1 KiB: 21.7 / 32.4; 64 KiB: 12.1 / 28.1; 1.0 MiB: 22.4 / 34.0; 10.0 MiB: 102 / 228; 25.0 MiB: 177 / 194
- share 37.8 ms; change role 22.7; revoke 24.7; download after revoke -> HTTP 403; upload > 25 MB -> HTTP 413
- audit write (one logged event, failed login of unknown user): median 19.0 ms, p95 90.0

### 5.4 Access control (live API, expected vs observed)

- RBAC matrix 4 principals x 9 operations = 36 cells, 36 matched (100.0%); unauthenticated requests -> {401}; forged / expired / wrong-secret / alg=none tokens -> 401 / 401 / 401 / 401.
- This is exhaustive over the implemented operations on one file, not a user study; the base-paper-like figure of 98.6% (IJEDR, 900 attempts by 50 users) is a different experiment.

### 5.5 Integrity and tamper evidence

- Ciphertext bit flips: 2000/2000 detected by AES-GCM; wrong key rejected: True.
- Audit edit_details: 200/200 detected
- Audit edit_action: 200/200 detected
- Audit edit_success: 200/200 detected
- Audit edit_user: 200/200 detected
- Audit edit_hash: 200/200 detected
- Audit delete_entry_middle: 199/199 detected
- Audit swap_adjacent: 200/200 detected
- Audit insert_forged_entry: 200/200 detected
- Audit truncate_tail: 0/199 detected
- A rewrite that recomputes every later hash is detected: False (False = NOT detected: the chain has no secret key or external anchor).
- **Tail truncation is not detected** (0/199): the verifier only checks internal consistency.
- Chain verification time grows linearly: 461 entries 27.2 ms; 500 entries 20.6 ms; 1000 entries 93.6 ms; 2000 entries 80.8 ms; 5000 entries 403.6 ms.
- **Defect found:** concurrent audit writers fork the chain. 100 concurrent failed logins (4 workers) -> chain valid after: False (first bad entry 5047). `record_event` reads the last hash and commits without a lock; single-writer assumption. Documented, not fixed.

## 6. Tests

- pytest: 21/21 passed in about 13 s (auth 6, crypto 5, files 3, rbac 5, audit 2).
- scripts/evaluate.py: 17/17 checks (note: its 'browser_*' timings are Python `cryptography` timings, not browser timings - superseded by 5.1).
- scripts/smoke_test.py: API end-to-end 17/17; real-browser UI walk 18/18 (against backend 8413 + Vite 5413).
- Not tested: multi-user load, >25 MB files, Firefox/Safari, PostgreSQL path, Docker build, accessibility audit with a screen reader.

## 7. Code size

- Backend 1184 lines / 20 files; tests 371 / 7; frontend src 6831 / 39; scripts 1470 / 6.

## 8. Known limitations (from code)

- Revocation deletes the server-side wrapped FEK but cannot recall a key or ciphertext the user already downloaded; no re-keying on revoke.
- An editor's update re-encrypts under the existing FEK with a fresh IV (random 96-bit IV, same key: collision bound applies to very many updates).
- Server serves the JavaScript that does the crypto: a compromised server could ship malicious JS (the MEGA-style trust problem).
- File name, size, MIME type, owner and timestamps are stored in clear metadata; password loss = data loss; no MFA; JWT in sessionStorage (XSS exposure); in-memory throttle resets on restart; `GET /api/audit` shows the global event list to any authenticated user; whole-file in-memory encryption (25 MB cap), no chunking; SQLite default.
- `PUT /api/files/{id}` by an editor does not validate the new ciphertext/IV pairing (server cannot); the client verifies SHA-256 on download.

## 9. Screenshot inventory (`docs/screenshots/`, 1440x900 unless noted, real demo data)

- 01_landing-dark.png
- 01_landing-light.png
- 02_landing-how-it-works-dark.png
- 03_landing-features-dark.png
- 04_sign-in.png
- 05_register.png
- 06_dashboard.png
- 07_my-files.png
- 08_file-detail.png
- 09_share-access.png
- 10_audit-log.png
- 11_security.png
- 12_unlock-vault.png
- 13_shared-with-me.png
- 14_dashboard-light.png
- 15_mobile-dashboard-360.png
- 16_mobile-nav-drawer-360.png

Older 9 screenshots of the previous UI sit in `screenshots/` (not used).

## 10. Literature (verified)

- Base paper: A. Nekouie, M. Vafaei Jahan, M. H. Moattar and R. Sheibani, "Secure electronic health record access control via blockchain, dual-attribute encryption, and large language model-based attribute extraction," Scientific Reports, vol. 16, art. 8673, 2026, doi: 10.1038/s41598-026-39690-2. Uses ECC-based dual-attribute ABE + ClinicalBERT + Hyperledger Fabric for EHR; crypto timings on HPE server (E5-2620 v3) and Raspberry Pi 3 B+ (OpenSSL); no file-storage product, no audit-log latency, no RBAC.
- G. Sowmiya, R. Nivas and E. Vikram, "Secure cloud file storage architecture with client-side encryption and access control," Int. J. Eng. Develop. Res. (IJEDR), vol. 14, no. 2, pp. 576-579, Apr. 2026, paper IJEDR2602501. Reports (50 users, 3 roles): +320 ms upload for a 10 MB file, 98.6% access-control accuracy (13 misclassified of 900), 0 exposure events in 30 days, 100% audit tamper detection (50 events), PBKDF2 310,000 iterations, 4 MB chunking, TOTP MFA, ECDSA-signed log entries, S3 + Vault.
- Geocrypt (Thenmozhi, Saralesh, Sakthi), ITM Web of Conferences 82, 03019, 2026, doi 10.1051/itmconf/20268203019: RSA + geo/time access + Ethereum smart contracts (Truffle, Ganache).
- Saginayev et al., Computing & Engineering 2(2):1-7, 2024, doi 10.51301/ce.2024.i2.01: AES-256 + RSA + SHA-256 hybrid cloud storage.
- Backendal, Haller, Paterson, 'MEGA: Malleable Encryption Goes Awry', IEEE S&P 2023, pp. 146-163.
- Batch survey items 2-4 (IRJMETS 2026 'Secure file storage on cloud using AES encryption'; ICPCSN 2026 'Secure cloud-based file storage system with enhanced data integrity and access control'; 'An integrated image encryption and secure transmission scheme ... chaotic mapping') could NOT be located online: listed with 'not independently verified', no results quoted.


## 11. Further findings recorded while writing the documents (from reading the code and the metrics)

- The same password is sent to the server for the bcrypt check and is the secret that unlocks the stored private-key bundle (a hostile or logging server could try it against the bundle).
- `plaintext_sha256` is stored unsalted next to the ciphertext, so a server-side reader can confirm a guess of a file's exact contents.
- Login for an unknown e-mail takes about 19 ms against about 326 ms for a wrong password on an existing account (bcrypt skipped): account existence is observable by timing.
- The unencrypted "plain" baseline was accepted by the same upload endpoint: the server cannot enforce that clients encrypt.
- The client IP is taken from `X-Forwarded-For` unconditionally (weakens the audit IP and the throttle); the throttle counts successful logins too and its 429 path was never exercised by the measurements.
- `GET /api/files/{id}/permissions` is open to any role on the file (matrix: editor and viewer get 200); `delete_file` writes its audit event before removing the file.
- `cryptography` is in requirements.txt but no server route imports it (tests and the seed script do); `alembic` is a dependency without migration scripts.
- `test_expired_or_invalid_jwt_rejected` sends only a malformed token; expiry, wrong secret and alg=none were checked separately in the measurement run.
- Documents built: 3 decks (16/20/28 slides), chapter documents 9-15, full report 94 pages (Word count), IEEE paper 6 pages (4,582 words, 20 references); `scripts/verify_docs.py` passes.
