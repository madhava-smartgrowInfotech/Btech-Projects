# RetinaGuard - Frontend Plan (Aurora Glass, kit V1)

Status: **Done.** Kit V1 copied into `frontend/src/`, every screen wired to the existing API, verified in a browser at 360, 768 and 1440 px in light and dark.

Ports: backend **8216** (`BACKEND_PORT`), frontend **5216** (`FRONTEND_PORT`), both set in `.env`.

No backend logic or API contract changed. The rebuild adds no endpoints.

---

## 1. Backend endpoints (inventory)

Auth: every route except `/api/auth/login`, `/api/health` and `/api/samples/{name}` needs `Authorization: Bearer <jwt>`.
Errors come back as `{"detail": "<text>"}` (422 validation errors give a list of `{loc, msg}`).

| # | Method | Path | Request | Response |
|---|--------|------|---------|----------|
| E1 | POST | `/api/auth/login` | JSON `{email, password}` | `{token, user:{id,email,name,role}}`; 401 `Wrong email or password` |
| E2 | GET | `/api/auth/me` | - | `{id,email,name,role}` (not called by the UI; the user is kept from login) |
| E3 | GET | `/api/patients?q=` | query `q` (name or code, optional) | `[{id,code,name,age,sex,created_at,screening_count,latest_stage,last_screened}]` |
| E4 | POST | `/api/patients` | JSON `{name, age 1-120, sex Male\|Female\|Other, code?}` | patient object as E3; 409 if code exists |
| E5 | GET | `/api/patients/{pid}` | - | patient object + `screenings: [summary]`; 404 |
| E6 | POST | `/api/screenings/image` | multipart `patient_id`, `eye` (Left\|Right), `file` (png/jpg, max 15 MB) | full screening (see E9); 400 bad image, 404 patient, 413 too big, 503 model missing |
| E7 | POST | `/api/screenings/{sid}/clinical` | JSON of 13 clinical fields (`age,sex,cp,trestbps,chol,fbs,restecg,thalach,exang,oldpeak,slope,ca,thal`, numeric, ranges enforced) | full screening with heart risk, factors and combined stage; 422 on bad input, 503 model missing |
| E8 | GET | `/api/screenings?limit=` | query `limit` (max 500) | `[summary]` newest first |
| E9 | GET | `/api/screenings/{sid}` | - | full screening: summary + `patient`, `quality`, `retina`, `clinical`, `heart` (`probability`,`factors`), `stage_detail`, `images` (base64 PNG: `steps`, `wavelet`, `heatmap`, `vessels`) |
| E10 | GET | `/api/screenings/{sid}/report` | - | `application/pdf` (inline) |
| E11 | GET | `/api/metrics` | - | `experiments/eval/metrics.json` (`retina` and `heart` blocks); 404 `No evaluation results yet. Run: python ml/eval.py` |
| E12 | GET | `/api/samples` | - | `[{name, label 0/1, url}]` from the labelled sample split |
| E13 | GET | `/api/samples/{name}` | - | PNG/JPG bytes (no auth needed by the route) |
| E14 | GET | `/api/health` | - | `{status, retina_model, heart_model}` (used by `scripts/smoke_test.py`; not called by the UI) |

---

## 2. Features and screens (inventory and status)

| # | Feature | Screen / route | Endpoints | Status |
|---|---------|----------------|-----------|--------|
| F1 | Landing page with links into the app | `/` (`pages/Landing.tsx`) | - | done |
| F2 | Sign in with demo accounts; wrong-password message | `/login` | E1 | done |
| F3 | Session guard, sign out, expired-session redirect | `App.tsx` `RequireAuth`, `lib/api.ts` 401 interceptor | E1 | done (sign out tested; 401 redirect in code) |
| F4 | Pick a labelled sample fundus image (HR / Normal badge) | `/screening/new` | E12, E13 | done |
| F5 | Upload a fundus image (PNG/JPG, <=15 MB, eye Left/Right) | `/screening/new` | E6 | done |
| F6 | Image quality check (blur / illumination) | `/screenings/:id` | E9 | done |
| F7 | Preprocessing steps view | `/screenings/:id`, tab "Preprocessing" | E9 | done |
| F8 | Haar wavelet sub-band view, levels 1 and 2 | `/screenings/:id`, tab "Wavelets" | E9 | done |
| F9 | Retinopathy probability, Grad-CAM heatmap, vessel map, vessel metrics | `/screenings/:id` | E9 | done |
| F10 | Create a new patient (name, age, sex, optional code) | `/screening/new` | E4 | done |
| F11 | Select an existing patient (`?patient=` preselect) | `/screening/new`, `/patients/:id` link | E3 | done |
| F12 | Clinical form (13 parameters) to heart-disease risk | `/screening/new`, `/screenings/:id` | E7 | done |
| F13 | Top SHAP risk factors (chart with table view) | `/screenings/:id` | E7, E9 | done |
| F14 | Combined risk stage with reasons and recommendations | `/screenings/:id` | E9 | done |
| F15 | Add or edit clinical data after the screening | `/screenings/:id` | E7 | done |
| F16 | Screening PDF report: view and download | `/screenings/:id/report` | E10 | done |
| F17 | Patients list with search by name or code | `/patients` | E3 | done |
| F18 | Recent screenings list | `/patients` | E8 | done |
| F19 | Patient detail with screening history | `/patients/:id` | E5 | done |
| F20 | Model performance: metrics, confusion matrices, ROC curves | `/performance` | E11 | done |
| F21 | Links between result, report, patient and history | all detail screens | - | done |

New items the prompt required (not in the product before): dark mode toggle in the topbar (saved in
`localStorage` as `retinaguard-theme`), reduced-motion support, 360 px layout with a drawer sidebar and bottom bar,
skeleton / empty / error / success states on every screen, toast notifications.

---

## 3. Screen map (as built)

| Screen | Route | Kit components used |
|--------|-------|---------------------|
| Landing | `/` | `AuroraBackground`, `SmoothScroll`, `Marquee`, `StatsStrip`, `HowItWorks`, `Stagger`, `Card`, `Button` |
| Login | `/login` | `Card`, `FormField`, `Input`, `PasswordInput`, `Button` |
| App shell | all signed-in routes | `AppShell`, `Drawer`, `Menu`, `Breadcrumbs`, `Avatar`, `PageTransition` |
| New screening | `/screening/new` | `Segmented`, `Select`, `FileDrop`, `FormField`, `Card`, `Skeleton`, `ErrorState` |
| Result | `/screenings/:id` | `Tabs`, `ChartCard` (SHAP, lazy), `StatCard`, `KeyValueList`, `ProbBar`, `Figure`, `Reveal` |
| Report | `/screenings/:id/report` | `PageHeader`, `Button`, `Skeleton`, `ErrorState` |
| Patients and history | `/patients` | `Table` (cards on phones), `SearchField`, `EmptyState`, `StageBadge` |
| Patient detail | `/patients/:id` | `StatCard`, `Table`, `EmptyState`, `Button` |
| Model performance | `/performance` | `StatCard`, `ChartCard` (ROC, lazy), confusion grid, `EmptyState` |

---

## 4. Decisions made

- **Kit is TSX, project was JSX.** The app is now TypeScript (`tsconfig.json`, `src/vite-env.d.ts`). Old `.jsx` files were
  removed. Backup of the old source is in the session scratchpad and in git history.
- **Landing numbers are fixed, not live.** `/api/metrics` needs sign-in, so the public landing reads
  `lib/landingStats.ts`, with values from `experiments/eval/metrics.json` (same as the README table). Update that file
  if `ml/eval.py` is re-run.
- **Stylesheet.** The kit has no `styles/tokens.css`; its `src/index.css` is imported once in `main.tsx`.
- **Router.** The kit uses `react-router`; `react-router-dom` was removed and imports point at `react-router`.
- **Heavy code is lazy.** Every route is a lazy chunk. Recharts (SHAP and ROC) and the landing's GSAP/Lenis load only where used.
- **Kit adaptations (in this project's copy only, the kit folder is untouched).** `AppShell` rewritten for RetinaGuard
  routes and sign-out; `ExampleAnswer` (policy Q&A) replaced with `ExamplePipeline` (real sample image);
  `StatsStrip` and `HowItWorks` rewritten for this product; `Logo` and theme storage key renamed; missing kit imports
  (`@/lib/api`, `@/lib/auth`, `@/lib/queries`, `@/lib/gsap`, `reactbits/AuroraBackground`) written as adapters.
- **ROC-AUC shown as a decimal** (0.725), matching the README. The old page showed it as a percentage.
- **Secrets.** `.env` holds a live Gemini key and JWT secret. It is not copied into docs or code and is not committed.
- **Commit scope.** Only `frontend/` and `docs/FRONTEND_PLAN.md` are committed. `FRONTEND_PROMPT.md`, `MASTER_PROMPT*.md`,
  `2.ABSTRACT.docx`, `.env` and `.env.example` are left out.

---

## 5. Step 4 verification

- [x] `npm run build` passes. `tsc --noEmit` passes.
- [x] `scripts/smoke_test.py` passes against the running API (23 checks).
- [x] Browser walkthrough (Playwright, Chrome) passes 30 checks: landing, login with wrong and right password, new
      screening with sample, validation, result with SHAP, report PDF, patients with search and empty state, patient
      detail, performance with confusion matrices and ROC, sign out, phone drawer with Escape, reduced motion.
- [x] No horizontal scroll at 360 px (landing, result, performance) and 768 px (patients).
- [x] Console: no page errors. The only errors are the deliberate wrong-password test (401) and a framer-motion dev
      notice that appears when reduced motion is on.
- [x] Every feature F1-F21 ticked off in section 2.
- [x] `docs/03_HOW_TO_RUN.md` still accurate (run steps unchanged), so no edit.
