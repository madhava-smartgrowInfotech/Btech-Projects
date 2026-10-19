# AegisBallot - Frontend Plan (Kit V1 · Aurora Glass)

Ports (from `.env`): backend **8401**, frontend **5401**. Backend confirmed to start on 8401
(`GET /api/health` -> `{"status":"ok","chain_valid":true,"height":209}`).

The existing app is **server-rendered** (FastAPI + Jinja2, cookie session, HTML form posts). It has
three JSON endpoints and everything else returns HTML or redirects. A React SPA cannot be wired to
that, so Step 3 adds a thin **additive JSON layer** (`app/api_v1.py`, mounted in `app/main.py`)
that calls the *same* services, models and ledger functions. No existing route, service, model or
security function is changed; the Jinja pages keep working and the existing pytest suite stays valid.

## 1. Backend inventory

### 1a. Existing endpoints (all stay as they are)

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/api/health` | none | - | JSON `{status, chain_valid, height}` |
| GET | `/api/chain/verify` | none | - | JSON `validate_chain` result `{valid, height, last_hash}` or `{valid:false, first_invalid, expected, actual, field}` |
| GET | `/api/benchmark/latest` | none | - | JSON `{exists, details, throughput_sync, throughput_async}` |
| GET | `/` | optional | - | HTML home (hero + elections) |
| GET/POST | `/login` | - | form `username`, `password` | HTML / 302 `/dashboard` + cookie `aegis_session`; 401 invalid; 429 after 10 tries/min |
| GET | `/logout` | session | - | 302 `/login` |
| GET | `/dashboard` | session | - | 302 by role -> `/admin` `/auditor` `/voter` |
| GET | `/admin` | ADMIN | - | HTML: voters, votes, turnout, chain, validators, benchmark, elections, 5 blocks, 10 audit rows |
| GET | `/admin/elections` | ADMIN | - | HTML list |
| POST | `/admin/elections/create` | ADMIN | form `title, description, start_time, end_time` | 302; auto-grants eligibility to every voter |
| POST | `/admin/elections/{eid}/status` | ADMIN | form `status` | 302 (DRAFT/OPEN/PAUSED/CLOSED) |
| GET | `/admin/elections/{eid}` | ADMIN | - | HTML: eligible, votes, turnout, candidates, results if CLOSED |
| POST | `/admin/elections/{eid}/candidates/add` | ADMIN | form `name, party, description, manifesto` | 302 |
| POST | `/admin/candidates/{cid}/toggle` | ADMIN | - | 302 |
| GET | `/admin/results/{eid}` | ADMIN | - | HTML tally (any status) |
| GET | `/admin/benchmark` | ADMIN | - | HTML last 5 benchmark runs + details JSON |
| GET | `/voter` | VOTER | - | HTML elections (OPEN/PAUSED/CLOSED) + own participation |
| GET/POST | `/voter/verify/{eid}` | VOTER | form `aadhaar` | HTML; on success issues one-time token (10 min) and renders vote page; 400/403/429 on failure |
| POST | `/voter/cast/{eid}` | VOTER | form `candidate_id, auth_token` | HTML receipt `{ballot_id, tx_hash, block_index, block_hash}`; 400 on rejection |
| GET | `/voter/results/{eid}` | any session | - | HTML tally, only when CLOSED (404 otherwise) |
| GET | `/auditor` | AUDITOR | - | HTML: chain, validators, 20 blocks, 20 txs, 20 audit rows |
| POST | `/auditor/verify` | AUDITOR | - | HTML + audit entry `integrity_check` |
| POST | `/auditor/tamper-test` | AUDITOR | - | HTML + audit entry `tamper_test` |
| GET | `/auditor/block/{bid}` | AUDITOR | - | HTML block + its transactions |

### 1b. JSON endpoints to add (additive, same logic, `/api/...`)

Session = the existing `aegis_session` cookie. Mutating calls also require the session's CSRF token
in `X-CSRF-Token` (the session already carries one; the Jinja app never enforced it). Errors are
`{"detail": "..."}` with the same status codes as the HTML routes.

| Method | Path | Role | Returns / does |
|---|---|---|---|
| POST | `/api/auth/login` | - | `{username,password}` -> sets cookie, `{user, csrf}`; 401/429 as `/login` |
| POST | `/api/auth/logout` | session | destroys session, audit `logout` |
| GET | `/api/auth/me` | session | `{user:{id,username,display_name,role,email}, csrf}` or 401 |
| GET | `/api/public/overview` | none | elections (id,title,description,status,start,end) + ledger height/valid + counts for the landing page |
| GET | `/api/admin/overview` | ADMIN | voters, votes, turnout, chain, validators, latest benchmark, 5 elections, 5 blocks, 10 audit rows |
| GET | `/api/admin/elections` | ADMIN | all elections with candidate/eligible/vote counts |
| POST | `/api/admin/elections` | ADMIN | create (same eligibility fan-out as the form route) |
| GET | `/api/admin/elections/{id}` | ADMIN | election, candidates, eligible, votes, turnout, results when CLOSED |
| POST | `/api/admin/elections/{id}/status` | ADMIN | `{status}` validated against the enum |
| POST | `/api/admin/elections/{id}/candidates` | ADMIN | add candidate |
| POST | `/api/admin/candidates/{cid}/toggle` | ADMIN | activate / deactivate |
| GET | `/api/elections/{id}/results` | ADMIN any status; others CLOSED only | `tally_results` + election |
| GET | `/api/admin/benchmarks` | ADMIN | last 5 `BenchmarkRun` rows with parsed `details_json` |
| GET | `/api/voter/elections` | VOTER | elections + own participation (ballot id) |
| GET | `/api/voter/elections/{id}` | VOTER | election, masked Aadhaar, already-voted flag + ballot id |
| POST | `/api/voter/elections/{id}/verify` | VOTER | `{aadhaar}` -> demo provider checks, issues token -> `{auth_token, expires_in, candidates}` |
| POST | `/api/voter/elections/{id}/cast` | VOTER | `{candidate_id, auth_token}` -> receipt |
| GET | `/api/auditor/overview` | AUDITOR | chain, validators, 20 blocks, 20 txs, 20 audit rows |
| POST | `/api/auditor/verify` | AUDITOR | runs `validate_chain`, audit `integrity_check` |
| POST | `/api/auditor/tamper-test` | AUDITOR | runs `tamper_test_clone`, audit `tamper_test` |
| GET | `/api/auditor/blocks/{index}` | AUDITOR | block + parsed signatures + its transactions |

## 2. Feature / screen inventory (existing product)

1. Landing: hero, three value cards (encrypted ballots, ledger integrity, auditable), "demo verification environment" notice, list of elections.
2. Sign in with demo accounts (admin / auditor / voter1..voter20), rate-limited, role redirect, sign out.
3. **Admin**: dashboard KPIs (voters, votes, turnout, ledger height/health); validators table (3 nodes, quorum 2/3); benchmark summary; recent elections; recent blocks; recent audit events.
4. **Admin**: election list; create election (title, description, start, end); open / pause / close; link to detail and results.
5. **Admin**: election detail (eligible, votes, turnout, candidates, results when closed); add candidate (name, party, description, manifesto); activate / deactivate candidate.
6. **Admin**: results page for any election (rank, candidate, party, votes, share).
7. **Admin**: performance benchmarks (last 5 runs: voters, sync / async throughput, duration, mean / p95 latency, raw details JSON).
8. **Voter**: elections list with status, "Verify & Vote", receipt prefix when already voted, "View Results" when closed, "Not open" when paused.
9. **Voter**: Aadhaar verification (masked Aadhaar on file, 12-digit input, Verhoeff + registry checks, errors, demo labelling).
10. **Voter**: candidate selection + confirmation step, one-time authorization notice (10 min), error on rejection.
11. **Voter**: blockchain receipt (ballot id, tx hash, block number, block hash, non-revealing note); "already voted" screen.
12. **Voter / any**: results of a closed election.
13. **Auditor**: dashboard - chain integrity status, **Verify Ledger Integrity**, **Run Tamper-Detection Demo**, validators, recent blocks, anonymous transactions, audit log.
14. **Auditor**: block detail (index, timestamp, previous hash, merkle root, block hash, validator signatures, transactions).
15. Offline tooling that stays untouched: benchmark CLI, tests, PDF generator, Docker files.

## 3. Screen map (every feature above appears)

| Route | Screen | Role | Features |
|---|---|---|---|
| `/` | Landing (Aurora hero, how-it-works, live stats, elections marquee/list) | public | 1 |
| `/login` | Sign in (glass card, demo-account quick fill) | public | 2 |
| `/app` | Role redirect | any | 2 |
| `/app/admin` | Admin dashboard (StatCards, charts, validators, blocks, audit) | ADMIN | 3 |
| `/app/admin/elections` | Elections + create modal + status actions | ADMIN | 4 |
| `/app/admin/elections/:id` | Election detail, candidates, add-candidate modal, results chart | ADMIN | 5 |
| `/app/results/:id` | Results (table + bar chart), shared by admin and voter | ADMIN / VOTER | 6, 12 |
| `/app/admin/benchmarks` | Benchmarks (throughput / latency charts, run table, raw JSON) | ADMIN | 7 |
| `/app/voter` | My elections | VOTER | 8 |
| `/app/voter/:id/verify` | Aadhaar verification stepper (Verify -> Choose -> Receipt) | VOTER | 9, 10, 11 |
| `/app/auditor` | Auditor dashboard (verify, tamper demo, blocks, txs, log) | AUDITOR | 13 |
| `/app/auditor/blocks/:index` | Block detail | AUDITOR | 14 |
| `*` | 404 | any | - |

Shared: AppShell (sidebar / drawer / bottom bar, breadcrumbs, dark-mode toggle persisted, user menu),
toasts, skeleton / empty / error states, protected-route guard by role.

## 4. Kit adaptations (copies only; the kit folder is never edited)

The kit is product-coupled to PolicyLens. In `frontend/src` I will rewrite: `AppShell` (nav, role-aware,
AegisBallot branding, `lib/auth`), `Logo`, and the three `landing/` pieces. I will add the files the kit
imports but does not ship: `lib/api`, `lib/auth`, `lib/gsap`, `lib/queries`, `components/reactbits/AuroraBackground`,
plus `tsconfig*.json`, `vite.config.ts`, `index.html`. Two kit files are TypeScript, so `typescript` is installed.

## 5. Verification checklist (all verified in Step 4)

Verified with `scripts/smoke_test.py` (44 API checks incl. the full voting flow), the browser walk in
`scripts/capture_screens.py` (every screen, real data, console clean) and a 360 / 768 / 1440 px x light / dark
layout sweep (no horizontal overflow, theme applied, no console errors).

- [x] 1 Landing (hero with live ledger, figures, how-it-works, elections; light and dark)
- [x] 2 Sign in / role redirect / sign out
- [x] 3 Admin dashboard
- [x] 4 Election list, create, open / pause / close
- [x] 5 Election detail, add candidate, toggle candidate
- [x] 6 Admin results
- [x] 7 Benchmarks
- [x] 8 Voter elections list
- [x] 9 Aadhaar verification
- [x] 10 Candidate selection + confirm + one-time authorization (10 min countdown)
- [x] 11 Receipt / already voted
- [x] 12 Voter results
- [x] 13 Auditor dashboard: verify, tamper demo
- [x] 14 Block detail
- [x] 15 Existing tests (17 pytest, run against a scratch DB), benchmark CLI and Jinja pages unaffected

## 6. Build notes

- Frontend: `frontend/` (Vite + React 18 + TypeScript, Tailwind 4). Kit V1 copied into `frontend/src`; AppShell, Logo and landing
  pieces rewritten for AegisBallot; `lib/api|auth|queries|types` and `AuroraBackground` added.
- Backend addition: `app/api_v1.py` (JSON layer, session cookie + `X-CSRF-Token`). `/api/auth/me` returns 200 with `user: null`
  when signed out so the browser console has no expected 401s.
- Dashboard shows "votes across N elections" instead of a turnout percentage: the original per-election eligibility
  makes an overall percentage exceed 100% once several elections exist.
- Browser tooling on this machine: Playwright's own Chromium screenshots fine; installed Chrome hangs in headless screenshots (GPU).
