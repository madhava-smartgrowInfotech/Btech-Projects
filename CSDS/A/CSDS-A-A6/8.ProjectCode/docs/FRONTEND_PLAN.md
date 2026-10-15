# Frontend Plan - ClauseGuard (Aurora Glass rebuild, kit V1)

Status: **Steps 2-4 done. Kit copied, screens rebuilt and wired, build passes, browser walk 65/65.**
Open items at the bottom of section 6 (Gemini quota blocks a live upload; push needs the owner).

Ports: backend **8106**, frontend **5106** (verified: `/api/health` answered on 8106 during inventory;
both ports are the code defaults - `.env` does not set `BACKEND_PORT` / `FRONTEND_PORT`).

---

## 1. Backend endpoints (inventory)

All routes are under `/api`. Auth = `Authorization: Bearer <token>` (JWT from login/register).

| # | Method | Path | Auth | Request | Response | Errors | Used by UI today |
|---|--------|------|------|---------|----------|--------|------------------|
| 1 | POST | `/api/auth/register` | no | `{email, password (min 6)}` | `{token, email, user_id}` | 400 email exists | Register |
| 2 | POST | `/api/auth/login` | no | `{email, password}` | `{token, email, user_id}` | 401 bad credentials | Login |
| 3 | POST | `/api/contracts/upload` | yes | multipart `file` (.pdf / .docx) | `ContractReport` (see 5) | 400 bad type / parse error, 502 pipeline error, 503 `GEMINI_API_KEY` missing | Upload |
| 4 | GET | `/api/contracts` | yes | - | `ContractSummary[]` `{id, filename, uploaded_at, complexity_grade, complexity_score, flag_count}` | - | My Contracts |
| 5 | GET | `/api/contracts/{id}` | yes | - | `ContractReport` `{id, filename, uploaded_at, complexity_grade, complexity_score, readability_score, legalese_density, cross_reference_count, avg_sentence_length, plain_summary, key_obligations[], combo_flags[], clauses: ClauseSummary[]}` | 404 not yours / missing | Contract Report |
| 6 | GET | `/api/contracts/{id}/clauses/{clauseId}` | yes | - | `Clause` `{id, index_in_doc, page_number, text, clause_type, classification_confidence, classification_method, flags: Flag[]}` | 404 | Clause Detail |
| 7 | GET | `/api/contracts/{id}/graph` | yes | - | `{nodes: [{id, clause_type, flags[], text_preview, risky}], edges: [{source, target, combo_id, reason}], risky_combinations: combo_flags[]}` | 404 | Clause Graph |
| 8 | GET | `/api/eval/metrics` | no | - | `{available: false, message}` **or** `{available: true, generated_at, predatory_detection: {num_examples, precision, recall, f1, per_rule}, cuad_classification: null \| {...}}` | - | Evaluation |
| 9 | GET | `/api/health` | no | - | `{status, gemini_configured, port}` | - | **none** (ops only) |

Nested shapes:
- `ClauseSummary`: `{id, index_in_doc, page_number, clause_type, text_preview, flag_count, max_severity}`
- `Flag`: `{id, rule_id, rule_label, severity, reason, provision, safer_wording}`

Notes:
- `cuad_classification` is `null` in the current `experiments/eval/metrics.json` (needs a live Gemini run).
- No write endpoints beyond auth + upload. No delete, no rename, no re-run.

---

## 2. Features and screens that exist today

| Feature | Route | Access | Current file | Data source (endpoint #) | Today's states |
|---------|-------|--------|--------------|--------------------------|----------------|
| Landing / hero | `/` | public | `pages/Landing.jsx` | none (static copy) | static |
| Sign up | `/register` | public | `pages/Register.jsx` | 1 | error text |
| Log in | `/login` | public | `pages/Login.jsx` | 2 | error text |
| Evaluation results | `/evaluation` | public | `pages/Evaluation.jsx` | 8 | loading, "not yet computed" (CUAD), error |
| Upload contract | `/upload` | auth | `pages/Upload.jsx` | 3 | progress bar, error |
| My contracts | `/contracts` | auth | `pages/ContractList.jsx` | 4 | loading, empty text, error |
| Contract report | `/contracts/:id` | auth | `pages/ContractReport.jsx` | 5 | loading, error |
| Clause detail | `/contracts/:id/clauses/:clauseId` | auth | `pages/ClauseDetail.jsx` | 6 | loading, error |
| Clause graph | `/contracts/:id/graph` | auth | `pages/ClauseGraph.jsx` | 7 | loading, hover, error, "none detected" |
| Navbar + logout | global | - | `components/Navbar.jsx` | - | auth-aware links |
| Auth state | global | - | `AuthContext.jsx`, token in localStorage | - | - |
| Shared status UI | - | - | `components/StatusStates.jsx`, `components/Badges.jsx` | - | - |

Gaps in the current product (to close in the rebuild, no backend change needed):
- **No dark mode, no theme toggle.** Kit `lib/theme.tsx` provides it.
- **No reduced-motion handling, no skeletons** (only text "Loading..." states).
- **No empty state with an action** on My contracts (text only).
- **No 401 handling**: an expired token leaves protected screens showing a raw error.
- Mobile: sidebar/nav is a flat link row; tables (per-rule table on Evaluation) are not responsive.
- No landing page motion or example output (kit `landing/*` pieces are unused today).

---

## 3. Screen map for the rebuild

Every row below is wired to the endpoint in brackets. Each screen gets: skeleton loading, empty state with action,
error state that says what failed + what to do, visible success feedback.

| Screen | Route | Kit pieces to use | Endpoints | Notes |
|--------|-------|-------------------|-----------|-------|
| Landing | `/` | `AppShell`, `motion/*` (FadeIn, SlideUp, Stagger, Reveal, CountUp, MagneticButton, Marquee), `landing/*` (StatsStrip, HowItWorks, ExampleAnswer), `brand/Logo` | none, plus #8 for the stats strip | Aurora Glass hero. Stats strip must show real numbers from #8 (or hide when `available: false`). |
| Register | `/register` | `Card`, `Field`, `Button`, `Toast` | #1 | Labelled inputs, min-6 hint, server error shown inline |
| Login | `/login` | `Card`, `Field`, `Button`, `Toast` | #2 | Same as register; 401 message from server |
| Evaluation | `/evaluation` | `Card`, `StatCard`, `Table`, `Chart` wrapper, `Badge` | #8 | Predatory P/R/F1 + per-rule table; CUAD card shows "not yet computed" with the command |
| Upload | `/upload` | `FileDrop`, `Button`, `Card`, progress, `Toast` | #3 | Client-side type check (.pdf/.docx); 503/502/400 messages mapped to actions; success navigates to report |
| My contracts | `/contracts` | `Table` (or cards on mobile), `Badge`, `EmptyState`, `Skeleton` | #4 | Empty state has "Upload a contract" action |
| Contract report | `/contracts/:id` | `StatCard` x4, `Card`, `Badge`, `Chart` (risk by severity), `Table` (clauses), `Button` (graph) | #5 | Shows complexity grade, 4 metrics with hints, plain summary, key obligations, risky combos, clause list |
| Clause detail | `/contracts/:id/clauses/:clauseId` | `Card`, `Badge`, `Tabs` (Flag / Provision / Safer wording) | #6 | Back link to report; one card per flag |
| Clause graph | `/contracts/:id/graph` | `Card`, `Chart` wrapper or inline SVG, hover card from kit `Popups` | #7 | Node hover shows clause preview; empty state "none detected" |
| Navbar + logout | global | `AppShell`, `Navigation`, `Avatar`, theme toggle (`lib/theme`) | - | Theme toggle persisted; drawer under 768px |
| 401 handling | global | `Toast` | any auth call | Redirect to /login with message |

Global: `ThemeProvider` from kit, `prefers-reduced-motion` respected in every motion helper, heavy pieces (`charts`, `SmoothScroll`/`lenis`, `gsap`) lazy-loaded.

---

## 4. Kit vs. project - conflicts found during inventory (decide at "proceed")

1. **Tailwind version.** Kit `index.css` uses Tailwind **v4** (`@import "tailwindcss"`, `@tailwindcss/vite`).
   Project uses Tailwind **v3** (`tailwind.config.js`, `postcss.config.js`, `tailwindcss ^3.4`).
   Plan: remove v3 configs, switch `vite.config.js` to `@tailwindcss/vite`.
2. **Kit has no Tailwind/PostCSS config at its top level.** Prompt Step 2.2 says to copy them; there are none to copy
   (only `components.json`). Nothing to copy beyond `components.json`.
3. **Stylesheet path.** Prompt says `styles/tokens.css`; the kit ships `src/index.css` only (no `styles/` folder).
   Plan: import `./index.css` from `main.jsx`.
4. **Product name in kit CSS.** The kit header comment says "PolicyLens - V1 Aurora Glass". Rename that comment in the copy
   (kit itself stays untouched).
5. **Path alias.** Kit `components.json` uses `@/` aliases (`@/components`, `@/lib/utils`). Project needs a `@` alias
   in `vite.config.js` (and a `tsconfig` with `paths` for editor support).
6. **Router package.** Kit deps list `react-router`; project uses `react-router-dom` ^6. Plan: keep
   `react-router-dom` (it re-exports `react-router`) to avoid duplicate installs; confirm on Step 2 import check.
7. **JavaScript project, TypeScript kit.** `typescript` is installed, `.tsx` kept as-is per prompt Step 2.4. Existing `.jsx`
   files are migrated screen by screen.

## 5. Repo / environment issues found (need your decision, not changed in Step 1)

- **Resolved:** `.env` is untracked in this repo (it was never committed here), and `.env` is now in `.gitignore`.
  The `.env` file gained `BACKEND_PORT=8106`, `FRONTEND_PORT=5106` and a generated `JWT_SECRET`.
- **Resolved:** `.env` used `GEMINI_MODEL` / `GEMINI_EMBED_MODEL`, which the backend never reads. Added
  `GEMINI_TEXT_MODEL` and `GEMINI_EMBEDDING_MODEL` (same owner-chosen models). The embedding name needs the
  `models/` prefix, so it is `models/gemini-embedding-001`.
- **Not changed:** `.env.example` still says `models/text-embedding-004`, which this key no longer serves.
  It is staged by another session in this repo, so it was left alone. Worth updating.
- **Git scope:** the repo root is `D:/abstracts/Madhav` and is shared with other projects, which have staged changes.
  Commits use explicit pathspecs. `MASTER_PROMPT*.md`, `2.ABSTRACT.docx`, `FRONTEND_PROMPT.md` and `.env` are not committed.
- **Push needs your credentials.** Claude cannot push from this environment.

## 6. Verification plan (Step 4)

- `npm run build` in `frontend/`
- `scripts/smoke_test.py` (exists) - extend if it does not cover upload -> report -> clause -> graph
- Walk every screen at 360 / 768 / 1440, light + dark, check console
- Keyboard: tab order, visible focus, Escape closes modals/drawer
- Tick every row in the feature checklist below as verified

### Feature checklist (Step 4 results)

Verified in Chrome with a Playwright walk (65/65 checks; the script is a local test helper and is not in the repo), against the live backend on 8106 and Vite on 5106:

- [x] Landing page (Aurora Glass), stats strip from #8 (values 100% / 94% / 97%)
- [ ] Register page UI - not walked in the browser; `POST /api/auth/register` verified by `smoke_test.py` steps
- [x] Login (#2), inline error on wrong password, redirect to /app
- [ ] Logout - not walked in the browser
- [x] Evaluation page renders at 360 / 768 / 1440, light and dark (#8)
- [ ] Evaluation per-rule table and CUAD "not measured yet" card - rendered in code, values not asserted
- [x] Upload - file pick, validation, progress and readable failure message (#3)
- [ ] Upload - success redirect to the report: **blocked** - the Gemini key returns 429 (quota exhausted),
      so no new contract can be analysed right now
- [x] Upload - server failure shown as an alert with a next step
- [x] My contracts - list, sortable, row and link to report (#4)
- [ ] My contracts - empty state with action - not walked (only reachable with zero contracts)
- [x] Contract report - grade, four metrics, summary, obligations, risky combinations, severity chart, clause table (#5)
- [x] Clause detail - flags, provision, safer wording, text tab; empty state for a clause with no flags (#6)
- [x] Clause graph - 5 nodes, risky edges, focus shows the clause, combo list (#7)
- [x] Not-found states for unknown contract and clause
- [x] Dark mode toggle, choice persists across reload
- [x] Reduced motion - landing renders with `reduced_motion=reduce`
- [x] 401 on a protected call - session-expired toast and redirect to login
- [x] 360px: no horizontal overflow on public, list, report, graph, upload; drawer opens and Escape closes it
- [x] Legacy URLs `/upload`, `/contracts`, `/contracts/:id` redirect into `/app`

Smoke test (`scripts/smoke_test.py`): health, register and login pass; **upload fails on the Gemini quota**
(429), so the run stops there. It was not changed to pass.

Console: no errors on any walked page except the expected browser log line for the quota 500 on upload.

Deviations from the prompt, decided during the build:
- Routing: app pages live under `/app` (the kit's shell expects it). Old URLs redirect.
- Router: `react-router` (the kit imports it) instead of `react-router-dom`.
- React 19 (required by the latest `react-router`), Tailwind v4 (`@tailwindcss/vite`), as the kit needs.
- The kit was missing `lib/auth`, `lib/api`, `lib/queries`, `lib/gsap` and `AuroraBackground`. Written as small adapters in the copy.
- `ExampleAnswer` (insurance sample copy) dropped; `StatsStrip` and `HowItWorks` rewritten for ClauseGuard.
- SmoothScroll (lenis) not mounted; the kit's shell does not need it.
- Main JS chunk is about 735 kB (235 kB gzip) because framer-motion, Radix and React Query load on every page.
