# APISentry - Frontend Plan (Kit V3, Depth Studio)

**Status:** Step 1 inventory complete. Waiting for "proceed" before Step 2 (kit copy).
**Ports:** backend 8213, frontend 5213 (confirmed in `.env`; backend boots and answers `/api/health`).
**Kit:** `D:\abstracts\Frontend_Kits\V3` (19 files in `src/`, plain `.jsx`).

---

## 1. Backend endpoints

All routes are under `/api`. "Bearer" = `Authorization: Bearer <JWT>`. Response shapes were checked
against a live run of the backend, not only the code.

| Method | Path | Auth | Request | Response (errors) | Old UI | Planned use |
|---|---|---|---|---|---|---|
| GET | `/health` | none | - | `{status, service}` | no | Landing: "API online" badge |
| GET | `/config` | none | - | `{scope_allowlist: string[], gemini_enabled: bool}` | no | Landing scope card; AI tests generator label |
| GET | `/owasp` | none | - | `{top10: [{id, name}], severity_weights: {critical, high, medium, low, info}}` | no | Landing OWASP coverage; finding labels |
| POST | `/auth/register` | none | `{email (3+), password (6+)}` | `{token, email}` (400 if email exists) | yes | Login, Register tab |
| POST | `/auth/login` | none | `{email, password}` | `{token, email}` (401) | yes | Login |
| GET | `/auth/me` | Bearer | - | `{id, email}` (401) | yes | Session restore on load |
| GET | `/targets` | Bearer | - | `Target[]` (see below) | yes | Targets |
| POST | `/targets` | Bearer | `{name, base_url, endpoints: object[], auth: object, known_vulns: object[]}` | `Target` | **no** | Targets, "Manual" tab (gap G1) |
| POST | `/targets/import-spec` | Bearer | `{name, spec_text, base_url?: string\|null, auth: object, known_vulns: object[]}` | `Target` + `spec_kind` (400: bad spec, no base URL, no endpoints) | yes (no known_vulns sent) | Targets, "From spec" tab |
| GET | `/targets/{id}` | Bearer | - | `Target` (404) | no | Not needed; list already carries the same data |
| DELETE | `/targets/{id}` | Bearer | - | `{deleted: id}` (404) | yes | Targets, delete with confirm |
| POST | `/scans` | Bearer | `{target_id, authorized: bool}` | `{id, status: "pending"}` (400 not authorised, 403 out of scope, 404) | yes | Targets, Scan button |
| GET | `/scans` | Bearer | - | `ScanRow[]`: `{id, target_id, target_name, status, progress, score, grade, ai_generated, created_at}` | yes | Scans list |
| GET | `/scans/{id}` | Bearer | - | `{id, status, progress, current_step, score, grade, ai_generated, error, target: {id, name, base_url}, finding_count, severity_counts, created_at, finished_at}` (404) | yes (polled every 1.5 s) | Scan detail, progress |
| GET | `/scans/{id}/findings` | Bearer | - | `Finding[]` sorted by severity: `{id, check_id, title, severity, owasp_id, owasp_name, endpoint, description, evidence: object, curl, recommendation, fix_snippet, vuln_key, source}` | yes | Scan detail, Findings tab |
| POST | `/scans/{id}/ai-tests` | Bearer | - | `{generator: "gemini" \| "builtin", count}` (400 unless scan is done) | yes | AI tests, Generate & run |
| GET | `/scans/{id}/ai-tests` | Bearer | - | `AITest[]`: `{id, name, category, endpoint, rationale, body: object, result: "vulnerable" \| "safe" \| "skipped", detail, generator}` | yes | AI tests tab |
| GET | `/scans/{id}/validation` | Bearer | - | `{total_known, detected_count, missed_count, false_positive_count, detection_rate, detected: {key, name}[], missed: {key, name}[], false_positives: string[], has_known_list}` | yes | Validation tab |
| GET | `/scans/{id}/report.html` | Bearer | - | `text/html` | yes | Report tab, Open HTML |
| GET | `/scans/{id}/report.pdf` | Bearer | - | `application/pdf` (attachment) | yes | Report tab, Download PDF |

**Target object** (`GET /targets`, `POST /targets`, `POST /targets/import-spec`):
`{id, name, base_url, endpoint_count, endpoints: {method, path, id_params, query_params, body_fields, summary, tags, security}[], auth: object, known_vulns: object[], in_scope: bool, last_scan: {id, status, score, grade} | null}`

**Conclusion:** no backend change is needed for any planned screen. The gaps below are all solvable in the UI
against the existing contract.

---

## 2. Features and screens in the existing product

Feature IDs are from `README.md`.

| Feature | Where it lives in the old UI | State in old UI |
|---|---|---|
| F1 Target import (spec paste, base URL, auth JSON) | Targets, "Import target" form | Works. Does not send `known_vulns`. |
| F1 Manual endpoints | none | **API only. Missing from UI (G1).** |
| F2 Scope guard + authorisation confirm | Targets: Scan disabled when out of scope; `window.confirm` before scanning | Works |
| F3 OWASP API Top 10 checks | Results come through Findings | Works (no list of checks shown) |
| F4 AI-generated tests | Scan detail, AI tests tab | Works |
| F5 Security score (0-100, grade, severity weights) | Scan header (score, grade, severity counts), Scans list | Works. **Per-endpoint breakdown is claimed on Landing and README but not shown (G3).** |
| F6 Findings (evidence, curl, fix + snippet) | Scan detail, Findings accordion | Works |
| F7 HTML / PDF reports | Scan detail, Report tab | Works. CLI is out of frontend scope. |
| F8 Validation vs known-vuln list | Scan detail, Validation tab | Works only for seeded targets. **Imported targets cannot set known vulns from the UI (G2).** |
| Auth: register, sign in, sign out, session restore, 401 redirect | Login page, `Protected` route, `api.js` interceptor | Works |
| Target delete | Targets, trash icon | Works (`window.confirm`) |
| Scan progress | Scan detail, polled every 1.5 s | Works |
| Scan history | Scans page | Works |
| Landing / marketing | `/` | Static copy, no live data |
| Not-found redirect | `*` route to `/` | Works |

**Old screens and routes:** Landing `/`, Login `/login`, Targets `/app/targets`, Scans `/app/scans`,
Scan detail `/app/scans/:id`, top nav (Targets, Scans), footer, sign out, `*` to `/`.

---

## 3. Screen map (new build)

Every item below is wired to the API above. Every state is designed: skeleton, empty (with action),
error (says what failed and what to do), success (toast).

1. **Landing `/`** - kit landing and motion pieces, Depth Studio hero (three.js, lazy-loaded, skipped under
   `prefers-reduced-motion`). Live data only: OWASP coverage count and names from `/owasp`, API status from
   `/health`, scope hosts from `/config`. Sign-in CTA.
2. **Login / Register `/login`** - Sign in and Register tabs. Demo credentials pre-filled as before. Inline
   error state. Success toast, then navigate to Targets.
3. **Targets `/app/targets`** - card grid (kit `Card`, `StatCard` for endpoint and vuln counts): name, base URL,
   endpoint count, known-vuln count, in-scope badge, last scan.
   - Actions: **Scan** (kit `Modal` with the authorisation text; sends `authorized: true` only after the user
     confirms; disabled when out of scope), **View last result**, **Delete** (`Modal` confirm).
   - **Import target** opens a `Modal` with `Tabs`:
     - *From spec* - name, base URL, spec textarea with example, auth JSON with example, **known vulns JSON
       (new, optional, G2)**.
     - *Manual* - name, base URL, endpoints JSON array, auth JSON, known vulns JSON. **New (G1).**
   - Empty state: "Import your first target" action.
4. **Scans `/app/scans`** - kit `Table` (cards below 640 px): #, target, status pill (live % while running),
   score, grade. Empty state linking to Targets.
5. **Scan detail `/app/scans/:id`**
   - Header: target name, base URL, scan #.
   - While `pending` / `running`: progress bar and `current_step`, polling `/scans/{id}` every 1.5 s, stopping
     on `done` / `error`.
   - On `error`: the backend `error` message and a link back to Targets.
   - On `done`: score ring, grade, severity counts (kit `charts`), then `Tabs`:
     - **Findings** - severity-sorted accordion (info hidden as before). Each item: description, endpoint,
       OWASP label, curl, evidence, fix and snippet. **Per-endpoint breakdown derived client-side from
       findings (G3).**
     - **AI tests** - "Generate & run" (POST), result badges (vulnerable / safe / skipped), generator label from
       `/config` and the response. Empty state with action.
     - **Validation** - detection rate, missed, false positives, detected and missed lists. "No known-vuln list"
       empty state.
     - **Report** - Open HTML (blob in new tab), Download PDF. Toast on success.
6. **App shell (all `/app/*`)** - kit `AppShell`: sidebar (Targets, Scans), becomes a drawer below 768 px.
   Topbar: theme toggle (kit theme helper, persisted), user email, Sign out. Toast host. Escape closes
   modals and the drawer.
7. **Not found** - redirect to `/` (as before).

**Cross-cutting checks (Step 4):** dark mode, reduced motion, 360 / 768 / 1440 px, visible focus rings, labelled
inputs, no lorem ipsum, no invented numbers.

---

## 4. Gaps and decisions

| ID | Gap | Default I will take | Needs your OK? |
|---|---|---|---|
| G1 | Manual target entry (`POST /targets`) is in the README (F1) but not in the old UI | Add a "Manual" tab to the import modal | No (say so if you want it out) |
| G2 | `known_vulns` cannot be set from the UI, so F8 Validation only works for seeded targets | Add an optional known-vulns JSON field to both forms. The API already accepts it, so no contract change. | No |
| G3 | Per-endpoint breakdown is claimed (Landing, README) but not shown | Derive it client-side from findings grouped by endpoint | No |
| G4 | `docs/PLAN.md` lists `GET /targets/known-vulns`, which does not exist. Only `/owasp` and `/config` exist in `catalog_routes.py`. | Not used by any screen. I will not add it, and I will not edit PLAN.md. | No |

**Kit issues to handle in Step 2:**
- **K1:** The kit has no top-level config files, only `MANIFEST.md`. Nothing to copy beyond `src/`. The
  project's existing `tailwind.config.js` and `postcss.config.js` stay unless the kit components need them.
  I will decide after reading the components.
- **K2:** Name collision. The old `frontend/src/components/ui.jsx` file and the kit's `components/ui/` folder
  both resolve from `'../components/ui'`. I will delete the old file when Step 2 starts, once the old pages
  are no longer needed as a reference.
- **K3:** `main.jsx` imports `index.css`. The kit's `styles/tokens.css` is imported there as well.
- **K4:** `axios` is not in the kit's install list. Keep it, because `api.js` uses it.

---

## 5. Commit and push plan (Step 4)

- **Git root is `D:/abstracts/Madhav`**, a parent repo. This folder is one subfolder of it. Commits are scoped
  to this folder with pathspec `.`.
- **Stage only this folder's product files** (`frontend/`, `docs/`, `run.bat` if changed) instead of
  `git add -A .`. Reason: the memory rules say prompt files must stay out of product commits.
- **Exclude from the commit:** `FRONTEND_PROMPT.md` (untracked), `MASTER_PROMPT.md` and `MASTER_PROMPT_FAST.md`
  (already staged in the index, so they need pathspec exclusions), `2.ABSTRACT.docx`. `.env` and `data/app.db`
  are gitignored.
- **Commit command:** `git commit -m "Rebuild frontend with kit V3" -- . ':!MASTER_PROMPT.md' ':!MASTER_PROMPT_FAST.md' ':!FRONTEND_PROMPT.md' ':!2.ABSTRACT.docx'`
- **No co-author lines.** The prompt forbids them, and the user's instructions take precedence over the
  attribution default.
- **Push:** Claude cannot push from this machine (no stored credentials). You will need to run `! git push`.
  Before that, check for the GH013 push-protection block caused by `.env` in sibling commits.

---

## 6. Step 4 results (kit V3 rebuild)

**Build and smoke:** `npm run build` passes (one chunk-size warning for the shared bundle; the scan detail page,
which pulls in the charts library, is lazy-loaded). `scripts/smoke_test.py` passes end to end.

**Browser walk:** `apisentry_walk.py` drives the live stack (Playwright, Chrome) and passes **62/62 checks**.
It covers every screen at 360, 768 and 1440 px, in light and dark mode, plus reduced motion and the auth guard.

**Feature ticks (Section 2):**

- [x] F1 Target import from spec, including file upload and auth JSON validation
- [x] F1 Manual endpoints (new, G1)
- [x] F2 Scope guard: Scan disabled out of scope; authorisation must be confirmed before POST /scans
- [x] F3 OWASP checks, shown as severity-sorted findings (12 findings on DemoPay)
- [x] F4 AI-generated tests: Generate & run, Vulnerable / Safe results
- [x] F5 Security score: donut, grade, severity counts, per-endpoint breakdown (new, G3)
- [x] F6 Findings: accordion with evidence, curl (copy button), OWASP mapping, fix and snippet
- [x] F7 Reports: HTML opens in a new tab, PDF downloads as apisentry-scan-N.pdf
- [x] F8 Validation: detection rate, missed, false positives; known vulns settable on import (new, G2)
- [x] Auth: sign in, register, sign out, session restore, sign-in guard on /app
- [x] Target delete with confirmation
- [x] Scan progress polling until done or failed; completion toast
- [x] Scan history list (sorted, card view under 640 px)
- [x] Landing page: live OWASP categories, API status and scope hosts
- [~] Not-found redirect to `/`: wired in the router; not exercised in the walk

**Requirements (Section 5):**

- Dark mode works and persists (toggle in topbar, stored as `pg-theme`), checked after reload
- prefers-reduced-motion: landing renders with the static hero fallback; heavy 3D scene is lazy-loaded
- 360 px: sidebar becomes a drawer (opens, Escape closes); wide tables become cards; no horizontal scroll at 360, 768 or 1440
- Keyboard: modal and drawer close on Escape; focus rings come from the kit (`:focus-visible`), not separately tested
- Console: no errors. Remaining warnings come from libraries: a THREE.Clock deprecation inside three.js, and motion.dev's
  notice that reduced motion is on
- No failed requests and no 4xx/5xx responses during the walk

**Changes from the original V3 instructions (for the record):**

- React is 19.3.1, not the existing 18.3.1: `@react-three/fiber` 9.x requires React 19. The kit's install list was run as given.
- Tailwind, PostCSS and autoprefixer were removed. The kit is plain CSS on design tokens and does not use them.
- The kit's `layout.jsx` imported `lib/stats` and carried PhishGuard copy. Both were replaced with APISentry versions in the project copy only.
- The kit folder was not modified. `frontend/src` contains its own copy of every kit file.
