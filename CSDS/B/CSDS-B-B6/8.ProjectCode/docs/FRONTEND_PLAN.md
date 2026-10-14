# UniHealth - Frontend Plan (V1 Aurora Glass)

Step 1 inventory, the screen map that was built, and the checklist ticked in Step 4.

**Ports:** backend `8206` (`BACKEND_PORT`), frontend `5206` (`FRONTEND_PORT`), hospital FHIR `12061` / `12062` / `12063`. Confirmed in `.env`.

**Hard boundaries kept:** no backend logic or API contract changes. The kit folder `D:\abstracts\Frontend_Kits\V1` was only read. `frontend/src` is self-contained (no imports from outside the project).

---

## 1. Backend endpoints

### 1a. Platform API - `/api` (port 8206)

Auth = `Authorization: Bearer <token>` from `POST /api/auth/login`. Roles: `patient`, `doctor`, `staff`, `admin`.

| Method | Path | Role | Request | Response |
|---|---|---|---|---|
| GET | `/api/health` | public | - | `{status}` |
| POST | `/api/auth/login` | public | `{username, password}` | `{token, user:{username, role, display_name, hospital, hospital_name}}`; 401 on bad credentials |
| GET | `/api/auth/me` | any | - | user view (+ `person_id` for patients) |
| GET | `/api/mpi/search` | doctor, admin | query: `q`, `birth_date` | list (max 25) of `{person_id, name, birth_date, gender, match, hospitals:[{key, name, local_id, confidence}]}` |
| POST | `/api/mpi/rebuild` | admin | - | rebuild counts (`records`, `persons`, `linked_persons`) |
| GET | `/api/mpi/persons` | admin | - | `[{person_id, name, birth_date, gender, links:[{hospital, local_id, name, birth_date, phone, confidence}]}]` |
| GET | `/api/hospitals` | any | - | `[{key, name, base_url, online, counts, fhir_version?, error?}]` |
| GET | `/api/hospitals/{key}/patients` | staff, admin | query: `q` | `[{hospital, local_id, given, family, name, birth_date, gender, phone}]` |
| POST | `/api/hospitals/{key}/visits` | staff, admin | `{patient_id, visit_type, diagnosis (required), medication, dosage, follow_up_days}` | `{created: Bundle, sync: {pushed_entries, platform}}`; 400 if no diagnosis |
| POST | `/api/hospitals/{key}/patients/{pid}/sync` | staff, admin | - | `{pushed_entries, platform}` |
| POST | `/api/sync` | hospital JWT (`system/Bundle.write`) | FHIR `collection` Bundle | `{summary_id, person_id, entries, reminders_added}`; 401/403/422 |
| GET | `/api/sync` | staff, admin | - | list (max 50) `[{id, person_id, hospital, hospital_name, local_id, entries, received_at}]` |
| GET | `/api/reminders` | patient | - | `[{id, kind, text, due, done, state, source}]` |
| POST | `/api/reminders` | patient | `{text, due, kind?}` | updated reminder list |
| POST | `/api/reminders/{rid}/toggle` | patient | - | updated reminder list |
| GET | `/api/records/{person_id}` | patient (`me` or own id), doctor (consent) | - | `{person, categories, sources, timeline, counts}` |
| POST | `/api/access/request` | doctor | `{person_id, reason}` | same record shape; 403 "Access blocked..." when no consent (request still logged as `blocked`) |
| GET | `/api/records/{person_id}/bundle` | patient, doctor (consent) | - | FHIR Bundle file download |
| GET | `/api/risk/{person_id}` | doctor (consent for labs + conditions) | - | `{person, heart, diabetes, disclaimer}` |
| POST | `/api/assistant/{explain\|summary\|ask}` | patient, doctor (consent) | `{person_id, language, report_id?, question?}` | `{title?, values?, language, text, disclaimer}`; 400 if empty question |
| GET | `/api/consents` | patient | - | `[{id, hospital, hospital_name, categories, status, expires, created_at, updated_at, fhir}]` |
| POST | `/api/consents` | patient | `{hospital, categories[], days?}` | consent view; 400 unknown hospital or no category |
| POST | `/api/consents/{cid}/revoke` | patient | - | consent view; 400 if already inactive |
| GET | `/api/access/requests` | patient, doctor | - | `[{id, person_id, doctor, hospital, hospital_name, reason, status, created_at}]` |
| GET | `/api/audit` | any | - | `{entries:[{id, ts, actor, action, person_id, detail, hash, prev_hash}], verification}` (scoped by role, max 300) |
| GET | `/api/audit/verify` | any | - | `{intact, entries, head?, broken_at?, position?}` |

### 1b. Hospital FHIR R4 servers - ports 12061 / 12062 / 12063

Called by the platform only, never by the browser.

| Method | Path | Notes |
|---|---|---|
| GET | `/fhir/metadata` | CapabilityStatement (public) |
| GET | `/fhir/stats` | counts per resource type (`system/*.read`) |
| GET | `/fhir/Patient` | searchset Bundle, `name`, `birthdate`, `_count` |
| GET | `/fhir/{rtype}?patient=` | searchset Bundle (`system/*.read`) |
| GET | `/fhir/{rtype}/{rid}` | FHIR resource |
| POST | `/fhir` | transaction Bundle in, transaction-response out (`system/*.write`) |
| POST | `/fhir/Patient/{pid}/$sync-summary` | builds a summary and pushes it to the platform |

---

## 2. Existing features and screens (inventory)

| # | Feature | Screen before the rebuild | Endpoints |
|---|---|---|---|
| F1 | Three hospitals, status and counts | Hospital console - FHIR servers | `/hospitals` |
| F2 | Master Patient Index: search, linkage, rebuild | Doctor search; Hospital console - MPI (admin) | `/mpi/search`, `/mpi/persons`, `/mpi/rebuild` |
| F3 | Consent: grant, list, revoke; audit ledger | Patient - consents; Audit | `/consents`, `/consents/{id}/revoke`, `/audit` |
| F4 | Secure retrieval: access request, consent block, merged timeline, sources | Doctor - access request; Patient + Doctor - timeline and sources | `/access/request`, `/records/{id}`, `/access/requests` |
| F5 | Post-treatment sync: record a visit, push summary, list summaries | Hospital console - patients, visit form, summaries | `/hospitals/{key}/patients`, `/hospitals/{key}/visits`, `/hospitals/{key}/patients/{pid}/sync`, `/sync` |
| F6 | Unified record: timeline and FHIR download | Patient + Doctor | `/records/{id}`, `/records/{id}/bundle` |
| F7 | Heart and diabetes risk with top factors | Doctor only (unchanged) | `/risk/{id}` |
| F8 | AI assistant and reminders | Patient + Doctor - assistant; Patient - reminders | `/assistant/{kind}`, `/reminders`, `/reminders/{id}/toggle` |
| - | Login, role routing, logout | Login | `/auth/login` |
| - | Landing with measured results | Landing | none (reads `src/data/evaluation.json`) |

---

## 3. Screen map as built

| Route | Screen | Built with (kit components unless noted) | Wired to |
|---|---|---|---|
| `/` | Landing: hero, measured stats, how it works, consent-check example, feature grid | `AuroraBackground`, `SmoothScroll`, `FadeIn`, `SlideUp`, `Parallax`, `Stagger`, `Reveal`, `CountUp`, `Card`, `Button` | none (stats from `src/data/evaluation.json`) |
| `/login` | Sign in, demo accounts | `Card`, `FormField`, `Input`, `PasswordInput`, `Button` | `/auth/login` |
| `/patient` | Record: 3 stat tiles, Tabs (Timeline, Consents, Assistant, Reminders) | `AppShell`, `PageHeader`, `StatCard`, `Tabs`, `TabPanel`, `Table` components, `Timeline`, `Select`, `SearchField`, `Checkbox`, `Modal`, `ConfirmModal`, `EmptyState`, `ErrorState`, `CardsSkeleton`, `toast` | `/records/me`, `/records/me/bundle`, `/consents`, `/access/requests`, `/reminders`, `/assistant/me/*` |
| `/doctor` | MPI search, access request (granted / blocked), sources, risk, timeline, assistant | `AppShell`, `ChartCard`, `ProgressBar`, `InlineLoader`, `EmptyState`, `ErrorState`; `RiskPanel` lazy-loaded | `/mpi/search`, `/access/request`, `/records/{id}`, `/records/{id}/bundle`, `/risk/{id}`, `/assistant/*` |
| `/hospital` | FHIR servers, patients, visit modal, push summary, summaries, MPI (admin) | `AppShell`, `StatCard`, `Table`, `Modal`, `Switch`, `SearchField`, `Select`, `toast` | `/hospitals`, `/hospitals/{key}/patients`, `/hospitals/{key}/visits`, `/hospitals/{key}/patients/{pid}/sync`, `/sync`, `/mpi/persons`, `/mpi/rebuild` |
| `/audit` | Verification banner, filterable ledger | `AppShell`, `Table`, `Badge`, `SearchField`, `Button` | `/audit` (its `verification` field) |

**Decisions made during the build**
- The risk panel stays doctor-only, as it was before. The patient page does not show it.
- The landing page's measured numbers come from `experiments/eval/metrics.json`, copied into `src/data/evaluation.json`. Nothing is invented; the consent-check example has no patient data.
- The kit's PolicyLens-specific landing and nav copy was rewritten for UniHealth in the project's copy only.
- `Settings` was removed from the account menu (no such screen exists).
- The session stays in `localStorage` as before. `/auth/me` is not called; an expired token is handled by the first 401, which signs the user out.

---

## 4. Feature checklist (verified in Step 4)

Verified by `scripts/smoke_test.py` (17/17 checks pass against the running servers) and by a browser walkthrough of every role (27/27 checks, plus 6 more for push summary, FHIR download, filters and the assistant).

- [x] F1 Hospitals status and counts (`/hospitals`)
- [x] F2 MPI search, linkage view with confidence, rebuild (`/mpi/search`, `/mpi/persons`, `/mpi/rebuild`)
- [x] F3 Grant consent, list consents, revoke with confirmation (`/consents`, `/consents/{id}/revoke`)
- [x] F3 Audit ledger list and chain verification (`/audit`)
- [x] F4 Doctor access request, granted path (`/access/request`)
- [x] F4 Doctor access request, blocked path with the API's message (403)
- [x] F4 Access request history for the patient (`/access/requests`)
- [x] F4 Merged timeline and record sources (`/records/{id}`)
- [x] F5 Hospital patient list and filter (`/hospitals/{key}/patients`)
- [x] F5 Record a visit in a modal; the server pushes the summary (`/hospitals/{key}/visits`)
- [x] F5 Push summary for a selected patient (`/hospitals/{key}/patients/{pid}/sync`)
- [x] F5 Summaries pushed list (`/sync`)
- [x] F6 Timeline filters by category, hospital and text
- [x] F6 FHIR Bundle download (`/records/{id}/bundle`)
- [x] F7 Heart and diabetes risk with top factors (`/risk/{id}`)
- [x] F8 AI assistant: explain, summary, ask, language selector (`/assistant/{kind}`)
- [x] F8 Reminders: list, add, mark done (`/reminders`, `/reminders/{id}/toggle`)
- [x] Login, logout, role routing
- [x] Landing page with the Aurora Glass look

---

## 5. Non-negotiables, as checked

| Requirement | How it was checked |
|---|---|
| Every state designed (skeleton, empty with action, error that says what failed, success feedback) | Built into each screen; success toasts seen in the walkthrough |
| Dark mode, toggle in the topbar, persisted | Screenshots in dark and light; theme stored in `localStorage` |
| `prefers-reduced-motion` respected; heavy parts lazy-loaded | Rendered under reduced motion with no errors; risk panel and landing are separate chunks |
| Responsive from 360px; sidebar becomes a drawer; tables become cards | No horizontal scroll at 360, 768 and 1440 in both themes; bottom bar on phones |
| Keyboard and focus: visible rings, Escape closes overlays, labelled inputs | Escape closes the visit modal (verified); labels via `FormField` |
| Real data only | No lorem ipsum; numbers come from the API or the measured evaluation file |

---

## 6. Kit notes and deviations

1. **No `styles/tokens.css` in the kit.** The stylesheet is `src/index.css`, imported once in `main.tsx`.
2. **No Tailwind/PostCSS config at the kit root.** The kit uses the `@tailwindcss/vite` plugin already in `vite.config.js`. Only `components.json` was copied.
3. **Kit imports that were missing from the kit folder** were written as project copies: `lib/api.ts`, `lib/auth.tsx`, `lib/queries.ts`, `lib/gsap.ts`, and `components/reactbits/AuroraBackground.tsx`.
4. **React upgraded from 18 to 19.** The kit's `react-router` and `radix-ui` versions require React 19. `react-router-dom` was replaced by `react-router`.
5. **`src/components/ui/Feedback.tsx` re-exports `Toaster` and `toast`** from `Toast.tsx`, so screens import them from one place.
6. **`FileDrop` is unused.** The product has no upload feature, so nothing was invented for it.
7. **Commit scope:** the git repo root is `D:/abstracts/Madhav`. Commits use the `-- .` pathspec, and `FRONTEND_PROMPT.md` (the prompt copy) is not committed.

## 7. Known limits

- The main JavaScript bundle is about 1.07 MB (335 KB gzipped). Vite warns above 500 KB. The cause is that the kit's `StatCard` imports `recharts`, which every page uses. Splitting it would mean making the stat tiles' sparkline lazy.
- Accessibility was checked for keyboard close, labels and focus rings, but not with a screen reader.
- The browser console shows one 403 during the walkthrough. That is the expected log for the blocked doctor request.
