# Frontend Plan - ForgetSafe (CSDS-A-A9)

Design: **V4 - Soft Pastel Calm** · Backend port **8109** · Frontend port **5109**
Project: Privacy-Preserving Machine Unlearning in Federated LLMs - a certified right-to-be-forgotten framework.

The existing app (`python app.py`) is a stdlib `http.server` that serves a single HTML page plus a JSON API.
It stays untouched. The new React frontend lives in `frontend/` and talks to that same JSON API
(Vite dev server proxies `/api` to `127.0.0.1:8109`, so no CORS change and no backend edit is needed).
No FastAPI layer is required - an HTTP API already exists.

## 1. Backend endpoint inventory (`certified_unlearning/web.py`)

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/` | - | Legacy single-page HTML UI (left as is) |
| GET | `/api/health` | - | `{status, service}` |
| GET | `/api/state` | - | `{trained, session_id, metrics, contributions[], active_clients[], latest_certificate, audit{valid, detail, records[]}}` |
| GET | `/api/certificate/latest` | - | Certificate JSON + `audit_valid`, `audit_verification` (download, `Content-Disposition`); 404 `{error}` if none |
| POST | `/api/train` | none | `TrainingMetrics` `{active_clients, epsilon, delta, perplexity, next_character_accuracy, utility_score, model_hash}` |
| POST | `/api/session` | none | `{session_id}` (new engine, audit history preserved) |
| POST | `/api/unlearn` | `{client_id}` | `UnlearningCertificate` (see below); 400 `{error}` if untrained / unknown / already unlearned / last client |
| POST | `/api/generate` | `{seed}` | `{text}` (180 chars); 400 if untrained |
| POST | `/api/audit/verify` | none | `{valid, detail}` |

Errors are always `{error: string}` with 400 / 404 / 500.

Shapes
- `metrics`: active_clients, epsilon, delta, perplexity, next_character_accuracy, utility_score, model_hash
- `contributions[]`: client_id, display_name, domain, record_count, original_norm, clipped_norm, clip_scale, active
- `UnlearningCertificate`: certificate_id, session_id, client_id, client_name, issued_at_utc, status (`CERTIFIED` | `REVIEW_REQUIRED`), method, epsilon, delta, clip_norm, noise_multiplier, residual_influence_l2, reference_retrain_l2, membership_auc_before/after, perplexity_before/after, accuracy_before/after, utility_retention_percent, clients_before/after, model_hash_before/after, audit_record_hash
- `audit.records[]`: sequence, previous_hash, record_hash, event_type (`FEDERATED_TRAINING` | `CLIENT_UNLEARNING`), plus event fields (timestamp_utc / issued_at_utc, client_id, status, ...)

## 2. Existing features and screens (README, legacy UI, desktop GUI)

Legacy web UI has four tabs; the Tkinter GUI and `--demo` mode mirror them.

1. **Federated Training** - train the global model; metric tiles (active clients, DP epsilon, perplexity, next-char accuracy); per-client table (domain, records, clipped L2, clip scale, state); new session.
2. **Certified Unlearning** - choose an active client, execute and certify; certificate view (status, privacy guarantee, utility retained, residual influence, reference-retrain L2, membership AUC before/after, perplexity before/after, audit record hash); download certificate JSON.
3. **Model Explorer** - seed text, generate a sample; method notes.
4. **Compliance Audit** - hash-chained ledger table (sequence, event, time, client, status, hash); verify hash chain with valid/invalid state.
5. Cross-cutting: toast feedback, busy states, new-session reset (audit history preserved).

Out of scope for the web frontend: Tkinter `--desktop` GUI and `--demo` CLI (left untouched and working).

## 3. Screen map (every feature above appears)

| Route | Screen | Wired to | Covers |
|---|---|---|---|
| `/` | Landing page (hero, how it works, guarantees, CTA into the lab) | `GET /api/state` (live counts only, no invented numbers) | brand + intro |
| `/app` | Dashboard / overview | `GET /api/state` | metric tiles, pipeline progress (train, unlearn, verify), latest certificate summary, audit status |
| `/app/training` | Federated Training | `POST /api/train`, `POST /api/session`, `GET /api/state` | feature 1, new session |
| `/app/unlearning` | Certified Unlearning | `POST /api/unlearn`, `GET /api/certificate/latest`, `GET /api/state` | feature 2, certificate + JSON download |
| `/app/explorer` | Model Explorer | `POST /api/generate`, `GET /api/state` | feature 3, method notes |
| `/app/audit` | Compliance Audit | `POST /api/audit/verify`, `GET /api/state` | feature 4 |
| `*` | Not found | - | - |

Shell: kit `AppShell` (sidebar becomes a drawer on small screens), topbar with persisted dark-mode toggle, toasts.
States on every screen: skeleton while loading, empty state with action (e.g. "Train the model"), error state with retry,
success toast.

## 4. Ports / environment

- Backend: `python app.py --port 8109` (existing CLI flag; verified it starts and serves `/api/health`).
- Frontend: Vite dev server on `5109`, proxy `/api` -> `http://127.0.0.1:8109`.
- `.env` currently holds an unrelated shared Gemini key (not used by this code); `BACKEND_PORT=8109` and `FRONTEND_PORT=5109`
  will be added and an `.env.example` created. `.env` is kept out of commits.

## 5. Verification checklist (ticked in Step 4)

- [x] Train model (metrics + client table render)
- [x] New session (resets, audit history preserved)
- [x] Unlearn a client -> certificate renders
- [x] Unlearn error cases (untrained, repeat, last client) show clear errors
- [x] Download certificate JSON
- [x] Generate sample text
- [x] Verify audit hash chain (valid state) and ledger table
- [x] Dark mode persisted, reduced motion, 360 / 768 / 1440 px
- [x] `npm run build`, smoke test, clean console

Verified on Chrome (Playwright) against the live API: every flow above, dark mode persisted across reload, Escape closes
dialogs and the mobile drawer, no horizontal overflow at 360 / 768 / 1440 px in light and dark, console clean
(no errors, no failed requests, no 404s). `npm run build` and `scripts/smoke_test.py` pass.
