# Frontend Plan - CipherVault (Kit V3, Depth Studio)

Batch CSE-C-C13 - ports: backend **8413**, frontend **5413**.

## 1. Backend endpoint inventory

All routes except `/api/health`, `/api/config`, `/api/auth/register`, `/api/auth/login` need `Authorization: Bearer <jwt>`.

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/health` | - | `{status, app}` |
| GET | `/api/config` | - | `{app, max_upload_mb}` |
| POST | `/api/auth/register` | JSON `{name, email, password(8+), public_key, encrypted_private_key, private_key_salt}` | 201 `UserOut` |
| POST | `/api/auth/login` | JSON `{email, password}` | `{access_token, token_type}`; 401 bad creds; 429 throttled |
| GET | `/api/auth/me` | - | `UserOut {id,name,email,role,public_key,has_private_key,is_active,created_at}` |
| PUT | `/api/auth/keys` | JSON `{public_key, encrypted_private_key, private_key_salt}` | `UserOut` |
| GET | `/api/auth/key-bundle` | - | `{bundle}` (JSON string of password-encrypted private key); 404 if none |
| POST | `/api/auth/logout` | - | `{message}` (writes audit event) |
| GET | `/api/users?q=` | query text | `UserOut[]` (max 50, active only) |
| GET | `/api/users/{id}/public-key` | - | `{user_id,email,public_key}` |
| POST | `/api/files/upload` | multipart `ciphertext`, `original_filename`, `mime_type`, `original_size`, `iv`, `wrapped_fek`, `plaintext_sha256` | 201 file object |
| GET | `/api/files` | - | owned files `FileOut[]` |
| GET | `/api/files/shared` | - | files shared with caller `FileOut[]` |
| GET | `/api/files/{id}` | - | `FileOut + {iv, wrapped_fek}`; 403 audited |
| GET | `/api/files/{id}/download` | - | ciphertext bytes + headers `X-CipherVault-{IV,Wrapped-FEK,SHA256,Filename,MIME}` |
| PUT | `/api/files/{id}` | multipart `ciphertext`, `iv`, `plaintext_sha256`, `original_size`, optional `wrapped_fek` (owner) | file object; owner/editor only |
| DELETE | `/api/files/{id}` | - | `{message}`; owner only |
| POST | `/api/files/{id}/share` | JSON `{user_id\|email, role: viewer\|editor, wrapped_fek}` | `{message,user_id,role}`; 409 if already shared |
| GET | `/api/files/{id}/permissions` | - | `[{user_id,user_name,user_email,role,created_at}]` (owner row first) |
| PUT | `/api/files/{id}/permissions/{uid}` | JSON `{role}` | `{message,user_id,role}`; owner only |
| DELETE | `/api/files/{id}/permissions/{uid}` | - | `{message}`; owner only |
| GET | `/api/audit?limit=&action=` | limit <= 500 | `AuditOut[]` (global, newest first) |
| GET | `/api/audit/file/{id}` | - | per-file events; owner only |
| GET | `/api/audit/verify` | - | `{valid,checked,failure_at,message}` |

`FileOut`: `id, original_filename, mime_type, encrypted_size, original_size, owner_id, owner_name, owner_email, effective_role, plaintext_sha256, created_at, updated_at`.

No new endpoints needed. All crypto (AES-256-GCM, RSA-2048-OAEP, PBKDF2) runs in the browser; ported 1:1 from `frontend/crypto.js` into `frontend/src/lib/vaultCrypto.js`.

## 2. Existing features / screens (old vanilla React+htm UI)

1. Register - generates RSA key pair in browser, password-protects private key, then logs in
2. Login - JWT in sessionStorage, then unlocks private key from `/api/auth/key-bundle`
3. Unlock vault card (shown if page reload dropped the in-memory private key)
4. Dashboard - total / owned / shared counts, plaintext bytes, security chips, Verify audit chain, recent activity (8 events)
5. My Files - list, upload & encrypt, refresh, download+decrypt+SHA-256 verify, details, share, delete
6. Shared with me - list, download, details
7. File details - metadata, SHA-256, role, access list, owner-only per-file audit history, decrypt & download
8. Share modal - grant viewer/editor (re-wrap FEK locally), change role, revoke
9. Audit logs - 200 latest events, refresh, verify chain
10. Security / profile - account, key status, lock local key, sign out, protection explainer
11. Sign out (audited)
12. *Backend feature the old UI never exposed:* `PUT /api/files/{id}` update content (Owner/Editor) - added as "Replace content" in the new UI.

## 3. Screen map (every feature above must land somewhere)

| Route | Screen | Covers |
|---|---|---|
| `/` | Landing (three.js hero, scroll story, how it works, RBAC, audit chain, CTA) | marketing; live `/api/config` limit |
| `/login`, `/register` | Auth (one page, tabs) | 1, 2 |
| (overlay) | Unlock-vault modal when key not in memory | 3 |
| `/app` | Dashboard: StatCards (CountUp), audit activity chart, role donut, security status, verify chain, recent activity | 4 |
| `/app/files` | My Files: FileDrop upload, search, table/cards, actions | 5 |
| `/app/shared` | Shared with me | 6 |
| `/app/files/:id` | File detail: metadata, integrity, access list, file audit timeline, download, replace content | 7, 12 |
| (modal) | Share manager: grant / change role / revoke | 8 |
| `/app/audit` | Audit log with action filter, verify chain, hash display | 9 |
| `/app/security` | Security profile: account, key status, lock key, sign out, protection explainer | 10, 11 |
| `*` | 404 | - |

Shell: kit `AppShell` (sidebar becomes drawer <= 900px), theme toggle in topbar (persisted), toasts.

## 4. Build / run decisions

- `frontend/` is rebuilt as Vite + React (JavaScript). The old static UI (`app.js`, `crypto.js`, `styles.css`, `index.html`) is replaced; its crypto logic is ported, not changed. Git history keeps the old files.
- Dev: Vite on **5413**, proxies `/api` to **8413** (no CORS change). Production-style: `npm run build` -> `frontend/dist`; backend serves `dist` if present (static path change only).
- `.env` / `.env.example`: `APP_PORT=8413`, `FRONTEND_PORT=5413`. `run.bat` starts both.
- `docs/03_HOW_TO_RUN.md` does not exist in this project; the run guide is root `HOW_TO_RUN.md` - updated there.
- The prompt says code lives in `8.ProjectCode/CipherVault/`; it actually lives directly in `8.ProjectCode/`. Frontend goes in `8.ProjectCode/frontend/`.

## 5. Verification checklist (all verified by `scripts/smoke_test.py` + manual walk)

- [x] 1 Register (keys generated in browser, auto-unlock)
- [x] 2 Login + unlock (wrong password shows an error)
- [x] 3 Unlock dialog after reload / lock (wrong and right password)
- [x] 4 Dashboard + verify chain (stat cards, event trend, role donut, recent activity)
- [x] 5 My Files: upload / download (decrypt + SHA-256) / details / share / delete (confirm dialog)
- [x] 6 Shared with me (viewer sees no share/delete actions)
- [x] 7 File details + owner-only audit history
- [x] 8 Share: grant / change role / revoke (unknown-user and duplicate errors handled)
- [x] 9 Audit logs: search, action + result filters, verify chain
- [x] 10 Security profile + lock key
- [x] 11 Sign out (audited) + route guard
- [x] 12 Replace content (PUT) round-trips and keeps shares working

## 6. What changed beyond the screens

| Item | Detail |
|---|---|
| Demo login (new) | Sign-in page "Try the demo": Owner / Editor / Viewer. First click registers `owner|editor|viewer@example.com` (fictional), uploads 5 synthetic files, shares them, has the editor update one and the viewer attempt a denied delete. |
| Seed script fix | `scripts/seed_demo.py` used `@example.local`, which the backend's email validator rejects. Switched to `@example.com`. |
| Ports | `.env` / `.env.example`: `APP_PORT=8413`, `FRONTEND_PORT=5413`; Dockerfile, compose, run-docker.bat, e2e/seed scripts and `config.py` default updated. |
| Backend edit (serving only) | `backend/app/main.py`: static frontend dir is now `frontend/dist`; CORS origins now 8413/5413. No API or logic change. |
| Docker | Dockerfile is multi-stage and builds the Vite app. |
| New scripts | `scripts/smoke_test.py` (API e2e + browser walk), `scripts/capture_screens.py` -> `docs/screenshots/`. |

## 7. Results

- `npm run build`: OK. 3D scene, charts and every page are lazy chunks.
- `scripts/smoke_test.py`: API 17/17, browser walk 18/18, also run against the built app served by the backend on 8413.
- `pytest -q`: 21 passed.
- Console: no errors, no failed asset requests. The only 4xx responses are intentional API answers (first demo run probes a login that returns 401, and the seeded viewer's denied delete returns 403, which is what puts "Access denied" in the audit log).
- Viewports 360 / 768 / 1440 in light and dark: no horizontal overflow on any route; sidebar becomes a drawer below 900 px; tables become cards below 640 px.
- `prefers-reduced-motion`: static hero image instead of WebGL, no Lenis smooth scroll, entrance motion reduced to fades.
- Keyboard: skip link, visible focus rings, Escape closes dialogs, focus trapped in dialogs, labelled inputs.
