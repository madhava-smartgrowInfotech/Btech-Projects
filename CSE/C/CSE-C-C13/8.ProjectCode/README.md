# CipherVault — Secure File Storage

CipherVault is a secure file-storage web application that protects sensitive files from
unauthorized access, data leakage, and tampering. Files are **encrypted in the browser
before upload** — the server stores ciphertext only and never sees plaintext.

## Problem being solved

Conventional file-sharing tools expose plaintext to servers, admins, and database backups.
CipherVault moves encryption to the trusted endpoint (your browser) so a compromised
server or leaked database still does not reveal file contents.

## Key features

- User registration & secure login (bcrypt + JWT)
- Client-side AES-256-GCM file encryption (Web Crypto API)
- RSA-2048-OAEP file-key wrapping per recipient
- Password-protected private keys (PBKDF2-HMAC-SHA-256 + AES-GCM)
- Encrypted upload / local decrypting download
- Owner / Editor / Viewer role-based access, enforced server-side
- Controlled file sharing with re-wrapped keys (plaintext keys never sent)
- SHA-256 integrity verification on every download
- Tamper-evident hash-chained audit log + verification UI
- Landing page (three.js hero), dashboard with charts, file details, sharing management, security profile
- Replace file content (Owner/Editor): re-encrypts with the existing file key so shares keep working
- One-click demo accounts (Owner / Editor / Viewer) with synthetic data
- Dark / light mode, reduced-motion support, responsive down to 360 px
- Local deployment (SQLite by default, PostgreSQL via Docker)

## Security model

| Property | How it holds |
|---|---|
| Plaintext never reaches the backend | Browser encrypts with AES-256-GCM; upload carries ciphertext only |
| Server cannot directly read files | It holds ciphertext + RSA-wrapped keys, not private keys |
| Passwords protected | bcrypt hashes (cost 12); never logged or returned |
| API access controlled | JWT (expiring) on all routes; ownership + RBAC checked server-side |
| Keys protected | RSA-2048-OAEP/SHA-256 wrapping; private keys AES-GCM-encrypted with PBKDF2-derived key |
| Integrity | SHA-256 of plaintext stored; AES-GCM tag + hash verified on download |
| Accountability | Every sensitive action audited; audit chain hash-linked and verifiable |

No unrealistic claims are made: CipherVault raises the bar substantially for local
deployment, but endpoint security (your device/browser) and secret management still matter.

## Architecture

```
Browser / React frontend (trusted crypto endpoint, Vite dev server :5413)
        |  HTTP localhost (/api proxied to :8413)
        v
FastAPI backend (auth, RBAC, metadata, ciphertext store, audit)
        +-- PostgreSQL (Docker) or SQLite (one-click local)
        +-- storage/encrypted (ciphertext files only)
```

The storage layer is a small filesystem module, so it can later be swapped for
S3-compatible object storage without changing the API.

## Technology stack

Backend: Python 3.11+, FastAPI, Uvicorn, SQLAlchemy, PostgreSQL (psycopg) / SQLite,
Pydantic, PyJWT, bcrypt, cryptography. Frontend: React 19 + Vite, React Router, Framer Motion, GSAP,
three.js (landing hero), Recharts, Web Crypto API, built on the V3 "Depth Studio" design kit.
Tests: pytest + httpx (backend), Playwright smoke test (UI).

## Project structure

```
CipherVault/
  backend/app/{main.py,core,db,api,schemas,services}
  frontend/                 # Vite + React app (src/pages, src/features, src/lib, kit in src/components)
  storage/encrypted/   # ciphertext only
  scripts/{evaluate.py,seed_demo.py,e2e_check.py,smoke_test.py,capture_screens.py}
  tests/               # auth, RBAC, crypto, files, audit
  docs/                # FRONTEND_PLAN.md, screenshots/ (current UI)
  screenshots/         # screenshots of the previous UI
  Dockerfile  docker-compose.yml  run.bat  run-docker.bat
  requirements.txt  .env.example  README.md  HOW_TO_RUN.md
```

## Local setup

See **HOW_TO_RUN.md**. Quickest path: double-click `run.bat`, open `http://localhost:5413`, and click
**Try the demo** on the sign-in page.

## Docker setup

Recommended if Docker Desktop is installed:

```
docker compose build
docker compose up
```

App: `http://localhost:8413`. PostgreSQL runs as a separate service with a persistent volume.

## API overview

Interactive docs: `http://localhost:8413/docs` (when running).

- `GET /api/health`, `GET /api/config`
- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`, `PUT /api/auth/keys`, `GET /api/auth/key-bundle`, `POST /api/auth/logout`
- `GET /api/users`, `GET /api/users/{id}/public-key`
- `POST /api/files/upload`, `GET /api/files`, `GET /api/files/shared`, `GET /api/files/{id}`, `GET /api/files/{id}/download`, `PUT /api/files/{id}`, `DELETE /api/files/{id}`
- `POST /api/files/{id}/share`, `GET /api/files/{id}/permissions`, `PUT /api/files/{id}/permissions/{uid}`, `DELETE /api/files/{id}/permissions/{uid}`
- `GET /api/audit`, `GET /api/audit/file/{id}`, `GET /api/audit/verify`

## Encryption workflow

Upload: read file → random 256-bit FEK + 12-byte IV → AES-256-GCM encrypt →
SHA-256(plaintext) → wrap FEK with owner's RSA public key → send ciphertext + metadata.
Download: permission check → return ciphertext → unwrap FEK with private key →
AES-GCM decrypt → SHA-256 compare → save only on success.

## RBAC model

- **Owner**: read, upload/update, delete, share, revoke, view file audit history.
- **Editor**: read/download + update content where granted. No sharing, no delete.
- **Viewer**: read/download only.
All checks are enforced in the backend; the UI additionally hides unavailable actions.

## Audit-log design

Each event stores UTC timestamp, user, file, action, success, IP, details, `previous_hash`,
`current_hash = SHA256(prev | ts | user | file | action | success | details)`.
`GET /api/audit/verify` recomputes the chain; the UI reports valid / integrity failure.
This is a hash-chained audit log (not a blockchain).

## Testing

```
pip install -r requirements.txt
pytest -q
```

Covers authentication, RBAC, AES/RSA primitives, file operations, and audit chaining/tamper detection.

## Evaluation

```
python scripts/evaluate.py
```

Runs real measurements (crypto timings, upload/download timings, sizes, auth latency,
authz allow/deny, integrity and tamper checks) and writes `evaluation_results.txt` /
`evaluation_results.json`. All numbers are produced by execution.

## Limitations

- Local deployment: no multi-server replication; backups are the operator's job.
- Private keys live encrypted server-side and decrypted in browser memory — endpoint compromise is out of scope.
- File size cap (default 25 MB, configurable) suits local demonstration workloads.
- No at-rest encryption of the ciphertext store beyond the file encryption itself.
- Password recovery is impossible without the password (by design — nobody holds your key).

## Future extensibility

- Swap `storage/encrypted` for S3-compatible object storage.
- Add WebAuthn/passkeys, TOTP 2FA, admin console, key rotation UX, chunked large-file pipeline.
