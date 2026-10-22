# Frontend plan - CareLens AI (SymptoTrackAI: Hybrid RAG Based Symptom Tracking)

Design: **V2 Neo Brutal Grid** (kit `D:\abstracts\Frontend_Kits\V2`, copied into `frontend/src/`).
Ports: backend **8412**, frontend **5412** (Vite dev server proxies `/api` to the backend, so the cookie auth works same-origin).

The codebase calls the product "CareLens AI"; that is the name used on screen. The existing UI is six
server-rendered Jinja pages (`app/templates/*`, `app/static/*`) which this rebuild replaces with the React app.

## 1. Backend endpoints

All JSON. Auth is a JWT in the httponly `carelens_token` cookie (a `Bearer` header is also accepted).
Errors are `{ "detail": "<message>" }` (422 validation errors give `detail` as a list of `{msg, loc}`).

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/api/health` | no | - | `{status, product}` |
| POST | `/api/auth/register` | no | `{email, password(6-128)}` | `{email, token}` + cookie; 400 if email exists |
| POST | `/api/auth/login` | no | `{email, password}` | `{email, token}` + cookie; 401 invalid |
| POST | `/api/auth/logout` | no | - | `{ok}` (clears cookie) |
| GET | `/api/auth/me` | cookie | - | `{email, id}`; 401 if not logged in |
| POST | `/api/chat` | yes | `{query(3-2000)}` | `{answer, top_condition, evidence[], safety_flag(emergency/caution/routine), safety_message, relevance_label, consultation_id, created_at, generated_by}`; 400/503/500 |
| GET | `/api/history?search=` | yes | - | `[{id, symptom_query, generated_response, top_condition, retrieved_evidence[], retrieval_score, safety_flag, created_at}]` (latest 200, newest first) |
| GET | `/api/history/{id}` | yes | - | one consultation (same shape); 404 |
| DELETE | `/api/history/{id}` | yes | - | `{ok}`; 404 |

`evidence[]` item: `{record_id, disease, symptoms, description, guidance, severity, red_flags, relevance(0-1)}`.

Server-rendered pages (`GET /`, `/login`, `/register`, `/dashboard`, `/history`, `/about`) are the old UI; they stay in
the backend untouched but are no longer the product front door.

**Gap:** no endpoint returns model/evaluation metrics. `results/metrics.json` (Top-1/Top-3, F1, MRR, latency) is measured
data used on the About page; I plan to add one thin additive read-only endpoint `GET /api/about/metrics` that serves that file
(and the knowledge-base size), because the SPA cannot read the file otherwise. No existing contract changes.

## 2. Existing features and screens

| # | Feature (from README / HOW_TO_RUN / old UI) | Old screen | Status |
|---|---|---|---|
| F1 | Landing page: product pitch, how it works, create account / sign in | `/` | [x] |
| F2 | Register (email + password, 6+ chars, errors shown) | `/register` | [x] |
| F3 | Sign in (errors shown) | `/login` | [x] |
| F4 | Sign out | dashboard button | [x] |
| F5 | Session check - protected screens redirect to sign in | `/api/auth/me` | [x] |
| F6 | Conversational symptom input (3-2000 chars, typing indicator, error message in chat) | `/dashboard` | [x] |
| F7 | Response: grounded answer text + top condition + relevance label | `/dashboard` | [x] |
| F8 | Possible-condition evidence cards: symptoms, description, guidance, severity, red flags, match relevance % | `/dashboard` | [x] |
| F9 | Safety escalation banners (emergency / caution) + permanent non-diagnosis disclaimer | `/dashboard` | [x] |
| F10 | Recent consultations side panel (last 5) | `/dashboard` | [x] |
| F11 | Consultation history list with search (symptoms / condition) | `/history` | [x] |
| F12 | Consultation detail view (symptoms, answer, evidence) | `/history` modal | [x] |
| F13 | Delete a consultation (with confirmation) | `/history` | [x] |
| F14 | About: what it does / is not / privacy / technology | `/about` | [x] |
| F15 | Evaluation metrics (measured, from `results/metrics.json`) | README only | [x] (new read-only endpoint `GET /api/about/metrics`) |

## 3. Screen map (React Router)

| Route | Screen | Shell | Features | Kit pieces |
|---|---|---|---|---|
| `/` | Landing | PublicShell | F1 | MaskHeadline, Marquee, Reveal, InkRule, CountUp, MagneticButton, Card |
| `/login` | Sign in | PublicShell | F3 | Field/Input, Button, Alert |
| `/register` | Create account | PublicShell | F2 | Field/Input, Button, Alert |
| `/assistant` | Symptom assistant (chat) | AppShell | F5-F10 | Textarea, Card, Badge, Alert, ProgressBar, Skeleton, Tabs |
| `/history` | Consultation history | AppShell | F11, F13 | SearchField, Table, Modal (confirm), EmptyState, ErrorState, Skeleton, Toast |
| `/history/:id` | Consultation detail | AppShell | F12, F13 | Card, Badge, KeyValueList, Breadcrumbs |
| `/about` | About + measured metrics | Public/AppShell | F14, F15 | StatCard, Charts (lazy), Card |
| `*` | Not found | PublicShell | - | EmptyState |

Cross-cutting: theme toggle in topbar (persisted), sidebar to drawer under 900px, toasts for success/failure, route-level lazy loading,
`prefers-reduced-motion` honoured by the kit helpers.

## 4. Kit gaps to adapt in the copy (kit folder untouched)

- `lib/gsap.js`, `lib/storage.js` and `lib/auth` are imported by kit files but not shipped in the kit - they will be written in `frontend/src/lib/`.
- `Layout.jsx` has navigation items from another product (elections/face scan); the copy is re-pointed to this product's routes.
- `Display.jsx` imports `STATUS_LABEL` (format.js) - kept; unused labels are harmless.

## 5. Environment findings

- No `.env` existed and the app ran on port 8000 (`run.bat`, docs, Dockerfile). Plan: add `.env` / `.env.example` with `BACKEND_PORT=8412`, `FRONTEND_PORT=5412`, and update `run.bat` to start backend on 8412 and the Vite frontend on 5412.
- No `.venv`; created one from `requirements.txt` (system Python lacks faiss, rank-bm25, email-validator, transformers). Python 3.11.9, Node 24.19.
- `docs/` was empty; this file is its first content.

## 6. Delivered (verification log)

Everything above is built. Additions beyond the original inventory, chosen as defaults:

- **Demo login** `demo@carelens.ai` / `Demo@1234` - there was none. Created at API startup (`app/demo.py`), seeded with 5 real consultations produced by the actual RAG pipeline over the synthetic knowledge base (`scripts/seed_demo.py`, run by `run.bat`). The login and register screens have a one-click "Continue with demo account" button.
- **`GET /api/about/metrics`** (additive, read-only) - serves `results/metrics.json` + knowledge-base size for the About and Landing pages.
- `.env` / `.env.example` (ports 8412 / 5412), `run.bat` starts API + frontend and reads `.env`; Vite proxies `/api` to the backend.
- Kit gaps filled in the copy: `lib/gsap.js`, `lib/storage.js`, `lib/auth.jsx`; `Layout.jsx` re-pointed at this product.

| Check | Result |
|---|---|
| `npm run build` | passes, route-level code splitting, Recharts in a lazy chunk |
| `scripts/smoke_test.py` | 22/22 pass (auth, chat, evidence, emergency escalation, history search/detail/delete, metrics, registration, isolation, logout) |
| `pytest tests` (backend, untouched) | 9 passed |
| `scripts/capture_screens.py` | 17 screenshots in `docs/screenshots/`, every screen with real data, landing in light + dark; **zero console errors / failed requests** |
| 360 / 768 / 1440 px, light + dark, reduced motion | no horizontal overflow on any route, no console errors |
| Keyboard | Escape closes the delete dialog (asserted in the capture script), focus trap and focus rings from the kit, all inputs labelled |

Known limitations: the evaluation metrics are measured on held-out records from a *synthetic* knowledge base (flagged on the About page), so they are not clinical accuracy. Docker still serves only the legacy Jinja pages on port 8000.
