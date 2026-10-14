# NutriSense - Frontend Plan (kit V1 · Aurora Glass)

Step 1 inventory. Source of truth for the rebuild: every row below must be ticked in Step 4.

Ports: backend **8211**, frontend **5211** (confirmed in `.env`; backend health check returned `ok`, 890 dishes, swap model loaded).

---

## 1. Backend endpoints (`/api`) - no changes planned

Auth = `Authorization: Bearer <token>`. "Profile required" = the user must have saved a profile (400 otherwise).

| # | Method | Path | Request | Response | Used by current UI |
|---|---|---|---|---|---|
| E01 | GET | `/health` | - | `{status, foods, swap_model, gemini_configured}` | no |
| E02 | POST | `/auth/register` | `{name, email, password}` (password ≥ 6) | `{token, user{id,name,email,has_profile}}` | yes |
| E03 | POST | `/auth/login` | `{email, password}` | `{token, user{...}}` | yes |
| E04 | GET | `/auth/me` | auth | `user{...}` | no (UI reads localStorage) |
| E05 | GET | `/profile/options` | - | `{activity, allergies, conditions, diet_type, cuisine, goal}` | yes |
| E06 | GET | `/profile` | auth | `{profile: {...} \| null}` | yes |
| E07 | PUT | `/profile` | `{age 18-90, gender, height_cm 120-230, weight_kg 30-250, activity, diet_type, cuisine, allergies[], conditions[], goal}` | `{profile, targets}` | yes |
| E08 | GET | `/targets` | auth + profile | `{bmi, bmi_category, bmr, tdee, goal_adjust, adaptive_adjust, kcal, calorie_floor, floor_applied, macros_pct, protein_g, carbs_g, fat_g, fibre_g, sodium_max_mg, sugar_max_g, gl_max, exclude_fried_rich, goal_rate_kg_week, notes[], disclaimer}` | yes (via E07 result, Dashboard) |
| E09 | POST | `/plans` | optional `{seed}` | plan `{id, created_at, start_date, target_kcal, seed, targets, days[7]{day, date, weekday, meals{breakfast,lunch,snack,dinner: [dish]}}}`; 422 on planner error | yes |
| E10 | GET | `/plans/latest` | auth + profile | `{plan: plan \| null}` | yes |
| E11 | GET | `/plans/{id}` | auth + profile | plan | no (UI uses `latest`) |
| E12 | GET | `/plans/{id}/swap-options?day&meal&index` | auth + profile | `{original: dish, options: [{food_id, name, grams, servings, kcal, protein, carbs, fat, fibre, sugar, sodium, gl, same_cluster, similarity, kcal_diff}]}` | yes |
| E13 | POST | `/plans/{id}/swap` | `{day, meal, index, food_id, grams}` | updated plan | yes |
| E14 | GET | `/recipes/{food_id}?grams` | auth + profile | `{food_id, name, grams, nutrients, ingredients[{item, quantity}], steps[], prep_minutes, cook_minutes, health_tips[], typical_minutes_dataset, warnings[], model, cached}` (503 if Gemini unavailable) | yes |
| E15 | GET | `/foods/search?q&limit` | auth + profile | `{results: [{food_id, name, role, diet, cuisine, allergens, serving_g, per_100g, grams, nutrients, warnings, score, ...}]}` | yes |
| E16 | GET | `/foods/usda?q` | auth + profile, q ≥ 2 chars | `{results: [{fdc_id, name, data_type, ...}]}` (503 if USDA down) | yes |
| E17 | GET | `/foods/{food_id}` | auth + profile | food detail | no |
| E18 | GET | `/logs?date` | auth + profile | `{date, entries[], totals{kcal,protein,carbs,fat,fibre,sugar,sodium}, targets{kcal,protein,carbs,fat,fibre,sodium,sugar}}` | yes |
| E19 | POST | `/logs` | `{date?, meal: breakfast\|lunch\|snack\|dinner, grams 0-3000, food_id? \| fdc_id?, source}` | log entry `{id, date, meal, food_id, name, grams, source, kcal, protein, ...}` | yes |
| E20 | DELETE | `/logs/{log_id}` | auth + profile | `{ok: true}` | yes |
| E21 | POST | `/logs/photo` | multipart `file` (JPG/PNG/WEBP/HEIC, ≤ 8 MB) | `{items: [{detected, confidence, estimated_grams, description, matches[]}], model}` (503 if Gemini down) | yes |
| E22 | POST | `/weights` | `{date?, weight_kg 30-250}` | `{ok, recalculated \| null, target_kcal}` | yes |
| E23 | DELETE | `/weights/{weight_id}` | auth + profile | `{ok: true}` | yes |
| E24 | POST | `/progress/recalculate` | auth + profile | recalc result `{..., as_of, old_target_kcal, new_target_kcal}`; 400 if not enough data | yes |
| E25 | GET | `/progress?days=7-180` | auth + profile | `{weights[], intake[{date,kcal,protein,carbs,fat,target}], adherence{score,days_logged,window_days}, target_history[], current_target, trend_kg_week, goal_rate_kg_week}` | yes |

**Gaps found:** none blocking. Optional addition (see Decision D1): a read-only endpoint for evaluation numbers, because the kit's landing `StatsStrip` expects live metrics.

---

## 2. Existing features (from README, `docs/PLAN.md`, and the current `frontend/src`)

| ID | Feature | Where it lives today | Endpoints | Status |
|---|---|---|---|---|
| F01 | Landing page with "Get started" and "Try the sample account" | `pages/Landing.jsx` | E03 (sample login) | [x] |
| F02 | Register (name, email, password) | `pages/AuthPage.jsx` | E02 | [x] |
| F03 | Log in | `pages/AuthPage.jsx` | E03 | [x] |
| F04 | Log out | `components/Layout.jsx` | - | [x] |
| F05 | Profile wizard: body, activity, diet, cuisine, allergies, health conditions, goal | `pages/ProfileWizard.jsx` | E05, E06, E07 | [x] |
| F06 | Edit profile later (same page, pre-filled) | `pages/ProfileWizard.jsx` | E06, E07 | [x] |
| F07 | Daily targets: BMI, BMR, TDEE, kcal, macros, fibre, sodium, sugar, GL, notes, disclaimer | `pages/Dashboard.jsx` | E08 | [x] |
| F08 | Dashboard: targets, today's logged entries, today's plan, 7-day intake vs target | `pages/Dashboard.jsx` | E08, E10, E18, E25 | [x] |
| F09 | Generate 7-day meal plan | `pages/PlanPage.jsx` | E09 | [x] |
| F10 | View weekly plan: day × meal slots, per-dish macros, day totals vs targets | `pages/PlanPage.jsx` | E10 | [x] |
| F11 | Smart swap: list alternatives (kcal diff, same cluster), choose one | `pages/PlanPage.jsx` | E12, E13 | [x] |
| F12 | Recipe for a dish: ingredients, steps, prep/cook time, health tips, warnings, cached flag | `pages/PlanPage.jsx` | E14 | [x] |
| F13 | Food log by day (date picker), totals vs targets | `pages/FoodLog.jsx` | E18 | [x] |
| F14 | Log a dish from the database search (grams, meal) | `pages/FoodLog.jsx` | E15, E19 | [x] |
| F15 | Log an ingredient from USDA FoodData Central search | `pages/FoodLog.jsx` | E16, E19 | [x] |
| F16 | Log from a photo: upload → detected dishes → matches → confirm and log | `pages/FoodLog.jsx` | E21, E19 | [x] |
| F17 | Delete a food-log entry | `pages/FoodLog.jsx` | E20 | [x] |
| F18 | Log weight for a date (add or update same day) | `pages/Progress.jsx` | E22 | [x] |
| F19 | Delete a weight entry | `pages/Progress.jsx` | E23 | [x] |
| F20 | Charts: weight over time, intake vs target; range selector (14 / 30 / 90 days) | `pages/Progress.jsx`, `components/Charts.jsx` | E25 | [x] |
| F21 | Adherence score (7 days) | `pages/Progress.jsx` | E25 | [x] |
| F22 | Target history (why the target changed) | `pages/Progress.jsx` | E25 | [x] |
| F23 | Trend (kg/week) vs goal rate | `pages/Progress.jsx` | E25 | [x] |
| F24 | Recalculate target now | `pages/Progress.jsx` | E24 | [x] |
| F25 | Automatic weekly recalculation (result shown to the user after logging weight) | `pages/Progress.jsx` | E22 | [x] |
| F26 | Sample account shown on login and landing (clearly labelled as sample data) | `pages/AuthPage.jsx`, `pages/Landing.jsx` | E03 | [x] |
| F27 | Disclaimer shown with targets and plan (general guidance, not medical advice) | `pages/Dashboard.jsx`, `pages/PlanPage.jsx` | E08 | [x] |
| F28 | Route guard: logged-out → `/login`, no profile → `/profile` | `App.jsx` | E04 (local) | [x] |
| F29 | Unknown route → `/` | `App.jsx` | - | [x] |
| F30 | Session expiry: 401 clears session and returns to login | `api.js` | any | [x] |

**New per the frontend prompt (not existing today, must be built):** dark mode toggle in topbar (persisted), reduced-motion, 360px drawer nav, visible focus rings, Escape closes overlays, skeleton / empty / error / success states on every screen, landing page in Aurora Glass character.

---

## 3. Screen map (routes kept identical to today)

| ID | Route | Access | Built from | Covers features | Notes |
|---|---|---|---|---|---|
| S01 | `/` | public (redirects to `/dashboard` if logged in) | kit `landing/*`, `motion/*`, `AppShell` background | F01, F26 | Hero, how-it-works, example, stats strip, CTA buttons |
| S02 | `/login` | public | kit `ui/Field`, `ui/Button`, `ui/Card` | F03, F26 | Sample-account button |
| S03 | `/register` | public | same as S02 | F02 | Field validation messages from API |
| S04 | `/profile` | logged in, profile not required | kit `ui/Tabs`/`Stepper` pattern, `Select`, `Segmented`, `Switch` | F05, F06 | Stepper: body → lifestyle → diet & health → goal; saves → targets |
| S05 | `/dashboard` | logged in + profile | kit `ui/Display` StatCard, `charts/Chart`, `Table` | F07, F08, F27 | Skeletons while loading |
| S06 | `/plan` | logged in + profile | kit `Table`, `Modal`/`Drawer` (swap sheet, recipe drawer), `Tabs` (days), `EmptyState` | F09–F12, F27 | Swap sheet and recipe drawer open over the page; Escape closes |
| S07 | `/log` | logged in + profile | kit `Tabs` (Database / USDA / Photo), `FileDrop`, `Table`, `Modal` (confirm delete) | F13–F17 | Photo flow: drop → detect → confirm |
| S08 | `/progress` | logged in + profile | kit `charts/Chart`, `StatCard`, `Table`, `Select` | F18–F25 | Range selector, weight form, history table |
| S09 | app shell | all private routes | kit `ui/AppShell`, `Navigation`, `Toggles` (theme) | F04, F28 | Sidebar → drawer under 768px; topbar theme toggle; logout |
| S10 | unknown | - | redirect | F29 | Same as today |

---

## 4. Kit gaps and decisions (found while inventorying the kit)

These are problems in the kit itself. Per the prompt, all fixes go into **this project's copy**, never the kit.

| # | Finding | Impact | Planned fix |
|---|---|---|---|
| K1 | Kit imports 5 files it does not ship: `components/reactbits/AuroraBackground`, `lib/gsap`, `lib/api`, `lib/queries`, `lib/auth` | Build fails until written | Write them in `frontend/src` (`lib/api.ts` on the existing axios client, `lib/auth.tsx` on the existing auth context, `lib/queries.ts` for React Query keys, `lib/gsap.ts` re-exporting gsap + ScrollTrigger, AuroraBackground from the tokens in `index.css`) |
| K2 | Kit is **not** product-neutral: "PolicyLens" brand (`Logo`, `AppShell`, `Feedback`, theme storage key), policy copy (Ask your policy, Claim Copilot, Policy Card, sample policy example), policy-eval stats (`StatsStrip`) | Wrong brand and copy on screen | Rename to NutriSense, rewrite copy to meal planning, replace `ExampleAnswer` with a sample meal plan, remove Claim Copilot nav |
| K3 | Kit uses `@/` path alias everywhere | Nothing resolves without it | Add `tsconfig.json` paths and `vite.config.js` `resolve.alias` for `@` → `src` |
| K4 | Prompt says `styles/tokens.css`; kit ships `src/index.css` (tokens, Tailwind, tw-animate) | Import path in the prompt does not exist | Keep `src/index.css` as the kit does; import it once in `main.jsx` |
| K5 | Kit imports `react-router` (v7) and `@tanstack/react-query`; current project uses `react-router-dom` v6 and no query client | Route and data layer change | Switch imports to `react-router`; keep axios in `lib/api`, wrap with React Query where useful |
| K6 | Prompt's install line uses unpinned `react react-dom` | Would jump React 18.3 → 19 | Pin React to the current 18.3.x unless the kit needs 19 (check on Step 2 build) |
| K7 | Manifest says 37 files; folder has 38 (MANIFEST.md itself) | None | Ignore |
| K8 | Existing `index.css` has `.card`, `.btn-primary`, `.input` classes used by current pages | Pages are replaced, so classes go | Delete with the old pages |

**Decision D1 (taken: option a):** the kit's landing `StatsStrip` shows live evaluation numbers. The backend does not serve them. Options:
- **(a) Taken:** add one read-only `GET /api/evaluation` that returns `experiments/eval/metrics.json` (additive; no existing contract touched). Stats come from real results.
- (b) Drop `StatsStrip` from the landing page.

**Decision D2:** the photo flow needs Gemini. `gemini_configured` is `true` here, so the photo and recipe screens can be walked end-to-end.

---

## 5. Step 4 checks (carried forward)

- `npm run build` must pass in `frontend/`.
- `scripts/smoke_test.py` exists → run it against the live API.
- Walk every feature F01–F30; tick the boxes above.
- Commit scope: `git add -A .` in this folder would also stage `FRONTEND_PROMPT.md` (untracked), and `MASTER_PROMPT.md`, `MASTER_PROMPT_FAST.md`, `.env.example` are already staged. These are **not** product changes and must be excluded from the commit. `.env` is gitignored and safe.
- The prompt asks for "no co-author lines"; that rule overrides the default attribution line.
- Push: this session has no git credentials, so the user will have to run the push themselves.

---

## 6. Step 4 results

| Check | Result |
|---|---|
| `npm run build` (type check + Vite) | Passes; route chunks lazy-loaded |
| `scripts/smoke_test.py` | 19 pass, 2 fail: recipe and photo steps, both Gemini upstream (503 "high demand" on the primary model; fallback model names retired, 404) |
| Screen walk (Playwright, production build) | 55 / 55 checks: every F-feature exercised, 360 / 768 / 1440 px, light and dark, sign-up through wizard, log-out |
| Console on production build | No errors, no warnings; the only HTTP errors are the expected upstream 503s and the recalc 400 when fewer than 3 weights exist |
| Horizontal overflow | None at 360 or 768 px on landing, dashboard, plan, log, progress |

Feature ticks are the `[x]` marks in sections 2 and 3 above.

Known issues outside this rebuild (backend, not changed per the hard boundary):
- `GET /api/recipes/{id}` caches whatever Gemini returns, including a reply with no ingredients or steps. The frontend now shows "the recipe came back empty" instead of a blank recipe, but the empty result stays cached until its row is deleted.
- `GEMINI_FALLBACK_MODELS` in `.env` lists retired models (`gemini-2.5-flash`, `gemini-2.0-flash`), so the fallback path fails with 404.
