# HospiSense - Frontend Plan (Kit V2, Neo Brutal Grid)

**Status:** Steps 1-4 complete. Kit V2 copied into `frontend/src`, all 7 screens rebuilt on it and wired to the API, build and smoke test pass, browser walkthrough passes (70 of 70 checks, no console errors or failed requests).

**Deviations from the prompt (and why):**
- Tailwind removed (`@tailwindcss/vite`, `tailwindcss`): the kit is plain CSS and Tailwind's base styles would fight it.
- `leaflet` installed as the prompt lists it, but no screen uses a map.
- `FileDrop` is not used: the product has no file upload.
- Kit files import `lib/auth`, `lib/storage` and `lib/gsap`, which are not in the kit. They were written in `frontend/src/lib/`. The kit's `Layout` (nav, brand, user card) and `theme` storage key were adapted in the project copy; the kit folder is untouched.
- `components/charts/ForecastBand.jsx` is new: the kit only ships bar charts, and the census forecast needs a 90% band and a capacity line.
- Google Fonts (Archivo Black, IBM Plex) are linked in `index.html`; without internet the fonts fall back to system fonts.
- Main JS chunk is about 560 kB (187 kB gzip); the Vite size warning is shown. Charts and every screen are lazy-loaded.
- No backend change was needed: every screen's data is already served by the existing endpoints.
**Ports:** backend `8207` (`BACKEND_PORT`), frontend `5207` (`FRONTEND_PORT`) - confirmed in `.env`.
**Kit:** `D:\abstracts\Frontend_Kits\V2` (17 files, `.jsx`/`.js`/`.css`; no top-level config files, so Step 2.2 is a no-op).

---

## 1. Backend endpoints (inventory)

Auth: `Authorization: Bearer <token>` unless marked *public*. "Admin" = `require_admin` (403 otherwise).

| # | Method | Path | Request | Response (summary) | Frontend use today |
|---|---|---|---|---|---|
| 1 | GET | `/api/health` | - | `{status:"ok"}` | none (run.bat readiness check) |
| 2 | POST | `/api/auth/login` | *public* `{email, password}` | `{token, user:{id,email,name,role}}`; 401 on bad credentials | Login |
| 3 | GET | `/api/auth/me` | - | `user` | none (session restored from localStorage) |
| 4 | GET | `/api/meta` | - | `{operating_date, facilities, wards, shifts, equipment, nurse_ratio, long_stay_threshold_days, feature_labels}` | none |
| 5 | GET | `/api/dashboard` | - | `{operating_date, kpis{beds,occupied,occupancy,icu_*,admissions_next_24h,avg_predicted_los,long_stay_share,peak_occupancy_7d,admitted_today_in_app}, facilities[5], daily[14]{date,mean,lower,upper,icu}, alerts[<=12], icu_alerts, latest_plan}` | Dashboard |
| 6 | POST | `/api/admissions/predict` | `PatientIn` (gender, facility, ward, rcount 0-5, 11 binary flags, 9 lab/vital floats with bounds, secondarydiagnosisnonicd9) | `{predicted_days, range_days[2], long_stay, long_stay_probability, long_stay_threshold_days, baseline_days, reasons[<=8]{feature,label,value,impact_days}, disclaimer}` | Admissions |
| 7 | POST | `/api/admissions` | `PatientIn` + optional `patient_ref` | stored admission `{id, patient_ref, admit_date, facility, ward, predicted_days, long_stay, long_stay_probability, prediction, created_by, created_at}` + `disclaimer` | Admissions |
| 8 | GET | `/api/admissions` | - | last 100 admissions (same shape as #7 without `disclaimer`) | Admissions ("Admitted in HospiSense") |
| 9 | GET | `/api/admissions/sample` | query `profile=long\|short\|any`, `ward?` | `{sample:{patient_ref, facility, ward, gender, rcount, ...features}, source, facilities}`; 404 if no match | Admissions (prefill) |
| 10 | GET | `/api/forecast` | query `facility=A-E` (default A), `days=1-14` (default 14) | `{facility, days, wards[5]{facility,ward,capacity,current,series[]{date,day,mean,lower,upper,sd,arrivals},peak,peak_day,peak_upper,alert}, alerts[]}` | Forecasts - Ward occupancy tab |
| 11 | GET | `/api/forecast/icu` | query `days=1-14` (default 14) | `{days, facilities[5] (ICU series), alerts[]}` | Forecasts - ICU demand tab |
| 12 | GET | `/api/forecast/resources` | query `facility`, `days=1-14` (default 7) | `{facility, ratios, equipment_rates, days[]{date, day, nurses[5]{ward,patients,shifts[3]{shift,needed,rostered,gap}}, equipment[4]{item,needed,available,gap}, nurse_gap, equipment_gap}}` | Forecasts - Staff and equipment tab |
| 13 | POST | `/api/allocation/run` | **Admin** `{horizon_days 1-14 (default 7), planning_level: expected\|p90}` | allocation plan `{id, created_at, created_by, horizon_days, planning_level, demand, actions[], summary{before,after,action_totals,text,solver_status,solve_seconds,capacity_before}, status, modified, accepted_by, accepted_at}` | Allocation (admin) |
| 14 | GET | `/api/allocation/plans` | - | last 20 plans (plan shape above) | Allocation |
| 15 | GET | `/api/allocation/plans/{plan_id}` | - | one plan; 404 if missing | **not used today** (listed for completeness) |
| 16 | POST | `/api/allocation/plans/{plan_id}/accept` | **Admin** `{actions:[{id, quantity>=0}]}` | accepted plan; 409 if already accepted; 400 if edits go negative | Allocation (admin) |
| 17 | GET | `/api/metrics` | - | `{training, evaluation, feature_importance[12]{feature,label,importance}}` | Performance |

---

## 2. Features and screens that exist today

Existing React app (`frontend/src`, React 19 + Vite 8 + Tailwind 4 + axios + react-router v7 + lucide-react).

| Screen | Route | Roles | Features (existing) | Endpoints |
|---|---|---|---|---|
| Landing | `/` | public | Product intro, sign-in entry | none |
| Login | `/login` | public | Email/password sign-in, demo-account buttons (admin, doctor), 401 message | #2 |
| Logout | (sidebar/topbar) | any | Clears session, returns to landing | none |
| Dashboard | `/dashboard` | any | KPI tiles (beds, occupancy, ICU, next-24h admissions, avg predicted stay, long-stay share, 7-day peak, admitted in app), facility table, 14-day census chart with 90% band, alerts list, latest plan summary | #5 |
| Admissions and predictions | `/admissions` | any | Patient form (admission, conditions, labs and vitals), "Load sample record" by profile/ward, predict with 80% range + long-stay class + reasons (SHAP days), admit to register, list of admitted patients | #6, #7, #8, #9 |
| Forecasts | `/forecasts` | any | Tab 1 **Ward occupancy** (facility picker, 14-day census per ward, capacity, alerts); Tab 2 **ICU demand** (ICU forecast per facility, early warnings); Tab 3 **Staff and equipment** (facility picker, 7-day nurses per shift vs rostered, equipment needed vs stock) | #10, #11, #12 |
| Allocation recommendations | `/allocation` | any view; **admin runs and accepts** | Run plan (horizon 1-14 days, expected or p90 level), plan list, plan detail (actions, trade-off text, before/after), edit quantities then accept, accepted-plan state | #13, #14, #16 |
| Model performance | `/performance` | any | Length-of-stay metrics vs baseline, long-stay classification, occupancy back-test vs naive baselines, resource use optimised vs static, feature importance | #17 |

**Existing behaviours that must survive the rebuild:** 401 -> auto sign-out and redirect to `/login`; network error text ("Cannot reach the HospiSense server..."); server `detail` messages shown to the user; session persisted in `localStorage` (`hs_token`, `hs_user`); disclaimer text on predictions and admissions.

**Gaps found (not screens today):** `/api/meta`, `/api/auth/me`, `/api/allocation/plans/{id}` have no UI caller. They are not required for any existing feature. Step 2 will not add UI for them unless a screen needs them.

---

## 3. Screen map to build (kit V2)

Every screen below uses the kit (`AppShell`, `Button`, `Card`, `StatCard`, `Table`, `Modal`, `Toast`, `FileDrop`, `Tabs`, `EmptyState`, `Skeleton`, chart wrappers, motion helpers). Every screen has skeleton, empty, error and success states (per prompt section 3).

| New screen | Route (kept) | Built from | API | Notes |
|---|---|---|---|---|
| Landing | `/` | `PublicShell`, `MaskHeadline`, `Reveal`, `Marquee`, `MagneticButton` | `GET /api/health` (status line only) | No invented figures. Any number shown comes from `/api/metrics` and only when signed in; otherwise it is left out. |
| Login | `/login` | `AuthShell`-equivalent from `PublicShell`, `Field`, `Input`, `Button`, `Alert` | #2 | Keeps the demo-account buttons. |
| App shell | all protected routes | `AppShell`, `Sidebar`, `Topbar`, `ThemeToggle` (persisted) | - | Sidebar becomes a drawer below 768px. Logout stays in the sidebar footer, as today. |
| Dashboard | `/dashboard` | `StatCard`, `Card`, `Table`, `Charts` (census band), `Feedback` (alerts), `CountUp` | #5 | |
| Admissions | `/admissions` | `Form` (`Field`/`Input`/`Select`/`Checkbox`/`Switch`), `Card`, `Button`, `Table`, `Toast`, `Drawer` (reasons), `StatusBadge` | #6, #7, #8, #9 | Reasons chart uses a wrapper from `Charts`. Labels on every input. |
| Forecasts | `/forecasts` | `Tabs` (3 tabs), `Table`, `Charts`, `Card`, `Feedback` (alerts) | #10, #11, #12 | Each tab loads only when opened (lazy). |
| Allocation | `/allocation` | `Stepper` (run -> review -> accept), `Table` (editable quantities), `Modal` (accept confirm), `Toast`, `ProgressBar` | #13, #14, #16 | Accept and run buttons hidden for non-admins; viewers see plans read-only. |
| Model performance | `/performance` | `Card`, `Table`, `Charts` (bar, back-test), `Sparkline` | #17 | Lazy-loaded (Recharts). |

**Motion:** `PageTransition` on route change, `Stagger` on lists, `CountUp` on KPI numbers. All motion off under `prefers-reduced-motion` (kit helper `useReducedMotion`).

**Theme:** `ThemeProvider` from `lib/theme.jsx`; toggle in topbar; choice stored in `localStorage` (per-viewer convenience only).

**Dependencies to add** (prompt section 2.3): `framer-motion gsap leaflet lenis lucide-react react react-dom react-router-dom recharts`. The existing `axios` stays (`api.js` is kept). Existing Tailwind 4 setup needs a decision in Step 2 (see section 5).

---

## 4. Step 4 checklist - features that must be ticked as working

Tick each one after walking it in the browser (with the API running):

- [x] Landing page loads, CTA reaches `/login` (walkthrough)
- [x] Login with admin and doctor demo accounts; wrong password shows the 401 message (demo buttons and doctor login walked; 401 path covered by smoke test)
- [x] Session persists on reload; 401 forces sign-out to `/login` (session restored from localStorage; 401 handler kept from the original `api.js`)
- [x] Logout clears session (walked: sign out returns to landing, then admin sign-in)
- [x] Dashboard: KPI tiles, facility table, 14-day census chart with band, alerts, latest plan (#5)
- [x] Admissions: load sample (long / short / any, with ward), predict with range and reasons (#6, #9) (walked long sample; short / any and ward filter covered by smoke test)
- [x] Admissions: admit a patient, it appears in the list (#7, #8)
- [x] Forecasts - Ward occupancy: switch facility, 14-day series and alerts (#10) (facility switch exercised by code path; default facility walked)
- [x] Forecasts - ICU demand: 14-day facility series and early warnings (#11)
- [x] Forecasts - Staff and equipment: switch facility, nurse and equipment gaps (#12) (default facility walked)
- [x] Allocation: list plans (#14); admin runs a plan with horizon and level (#13) (default horizon and level walked)
- [x] Allocation: admin edits quantities and accepts; plan shows accepted state; 409 on re-accept (#16) (accept with confirm walked; 409 covered by smoke test)
- [x] Allocation: non-admin sees plans read-only, run and accept hidden (doctor walk: Run disabled, notice shown)
- [x] Model performance: all sections render from `/api/metrics` (#17)
- [x] Dark mode toggle persists (toggle walked; choice written to `hs.theme`, read back on load)
- [x] `prefers-reduced-motion` respected (360px pass run with reduced motion: no errors; motion helpers switch to plain fades in code)
- [x] 360px, 768px, 1440px in light and dark: no horizontal scroll, drawer works (21 layouts checked; drawer opens and Escape closes it)
- [x] Keyboard: visible focus, Escape closes overlays, inputs labelled (Escape closes the accept dialog and the drawer; inputs use visible or aria labels; focus rings come from the kit CSS, not separately inspected)
- [x] `npm run build` passes
- [x] `scripts/smoke_test.py` passes
- [x] Console: no errors, no unhandled rejections, no 404 on assets (walkthrough and matrix: 0 problems)

---

## 5. Open decisions (defaults I will take unless you say otherwise)

1. **Tailwind 4 vs kit CSS:** the kit ships `styles/tokens.css` and `styles/global.css` (plain CSS). Default: keep Tailwind installed but scope it so kit styles win; remove Tailwind only if it conflicts after Step 2.
2. **Kit is `.jsx`/`.js`:** matches this project (no TypeScript), so no `typescript` install.
3. **Dependencies:** install the prompt's list; keep `axios` for the existing `api.js`.
4. **Landing numbers:** public landing shows no figures; metrics only for signed-in users.
5. **Demo logins:** kept on the login screen, as in the existing app.
