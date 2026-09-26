# Code structure

```
.
├─ backend/                 FastAPI application and its tests
├─ frontend/                React + Vite web app
├─ ml/                      Engine benchmark (evaluation) code
├─ notebooks/               Benchmark walkthrough notebook
├─ experiments/             One folder per benchmark run (metrics, results, plots, log)
├─ models/                  Settings the product loads (tuned engine profile)
├─ data/                    Sample data, import templates, the database (app.db, not committed)
├─ scripts/                 Setup, sample data, checks and demo utilities
├─ docs/                    Documentation
├─ setup.bat  run.bat  stop.bat
├─ .env.example             Every setting, documented (copied to .env by setup.bat)
└─ pyrightconfig.json       Editor settings so Python imports resolve
```

## backend/

| Path | Contents |
|---|---|
| `app/main.py` | App factory: settings, logging, CORS, error handlers, request logging, database creation and demo accounts at start-up. |
| `app/core/` | `config.py` (settings from `.env`, paths), `db.py` (engine, session, base), `security.py` (bcrypt, JWT), `deps.py` (current user, admin guard), `errors.py` (readable error responses), `logging.py` (key=value logs to console and `logs/`). |
| `app/models/` | SQLAlchemy tables: `user.py`, `exam.py` (departments, courses, candidates, registrations, halls, sittings, papers), `plan.py` (plans, seats, invigilators), `attendance.py`, `system.py` (imports, audit, settings). |
| `app/schemas/` | Pydantic request and response models. |
| `app/api/` | Routers: `auth`, `users`, `settings`, `imports`, `data`, `plans` (generation, publish, verify, maps, swaps, invigilators), `exports`, `attendance`, `analytics`, `audit`, `public` (lookup, slips, QR, benchmark summary), `health`. |
| `app/services/engine/` | **The seating engine**: `types.py`, `rolls.py` (roll-number rules), `graph.py` (seat graph, colour classes, labels), `prechecks.py`, `stage_a.py` (hall and colour-class allocation), `stage_b.py` (seat layout per hall), `engine.py` (orchestration, seeds, retries), `validator.py` (independent checks), `baselines.py` (manual methods). Pure Python + OR-Tools, no database. |
| `app/services/importer/` | `spec.py` (column definitions used by importer, templates and docs), `parse.py` (CSV/XLSX reading, header aliases), `validate.py` (row and cross-file checks), `commit.py` (batches, applying), `templates.py` (Excel/CSV templates). |
| `app/services/exports/` | `data.py` (export data), `seating_chart_pdf.py`, `invigilator_pdf.py`, `slips_pdf.py`, `excel.py`, `pdf_common.py` (fonts, logo, QR drawing). |
| `app/services/` | `plans.py` (generate, publish, verify, delete), `swap.py` (move checks), `hallmap.py`, `attendance.py`, `analytics.py`, `sessions.py`, `halls.py`, `audit.py`, `seed.py` (demo accounts), `settings_service.py`, `ratelimit.py`. |
| `app/ml/profile.py` | Loads `models/engine_profile.json` and the benchmark run it points to. |
| `app/assets/fonts/` | DejaVu fonts (open licence, `LICENSE_DEJAVU`) so PDFs print any name. |
| `tests/` | pytest suite (58 tests) and helpers. |
| `requirements.txt` | Pinned Python packages. |

## frontend/

| Path | Contents |
|---|---|
| `vite.config.ts` | Fixed port 5113 (`strictPort`), `/api` proxy to 8113, LAN access, pre-bundled dependencies, chunking. |
| `tailwind.config.ts`, `src/index.css` | Design tokens (light and dark), paper colours, fonts, reduced-motion rules. |
| `src/main.tsx`, `src/App.tsx` | Providers (theme, TanStack Query, auth, Motion, tooltips, toasts) and routes (every page lazy-loaded). |
| `src/lib/` | `api.ts` (Axios with token, readable errors, downloads), `auth.tsx`, `theme.tsx`, `types.ts` (API types), `format.ts`, `papers.ts`, `storage.ts`, `useDebounced.ts`, `utils.ts`. |
| `src/components/ui/` | shadcn/ui components (Radix based): button, card, dialog, sheet, alert dialog, dropdown, select, tabs, table, tooltip, switch, checkbox, radio group, progress, badge, skeleton, popover, scroll area, toaster. |
| `src/components/layout/` | `AppLayout` (sidebar, mobile menu, page transition), `nav.ts` (menu by role), `PublicShell` (public header and footer). |
| `src/components/common/` | Page header, empty/error/loading states, file drop, theme toggle, route guard. |
| `src/components/seatmap/SeatGrid.tsx` | Hall grid layout used by the seat map and attendance. |
| `src/components/charts/ChartKit.tsx` | Chart styling, tooltip, legend, chart card with table view, stat tile. |
| `src/components/reactbits/` | React Bits components (DotGrid, BlurText, RotatingText, CountUp, SpotlightCard) with their licence. |
| `src/components/landing/`, `plans/`, `rules/`, `halls/`, `attendance/`, `brand/` | Landing illustrations, plan widgets, rules form, hall preview, camera scanner, logo. |
| `src/pages/public/` | Landing page, seat lookup. |
| `src/pages/auth/` | Sign in, request account. |
| `src/pages/app/` | Dashboard, Import, Data, Sittings, Plan page, Hall map, Exports, Attendance (list and hall), Analytics, Audit, Team, Settings. |
| `public/favicon.svg` | Logo mark. |

## ml/

| Path | Contents |
|---|---|
| `scenarios.py` | Seeded benchmark scenarios (150-2,000 candidates). |
| `baselines.py` | Re-exports the manual methods from the engine. |
| `predictability.py` | Roll-to-seat correlation, repeated neighbours, front-row bias. |
| `benchmark.py` | Runs everything, tunes the budget, writes `experiments/...` and `models/engine_profile.json`. |
| `plots.py` | Benchmark charts. |
| `requirements-notebooks.txt` | Optional packages to run the notebook. |

## scripts/

| Script | Purpose |
|---|---|
| `check_env.py` | Checks Python, Node, ports, `.env` (standard library only). |
| `ensure_env.py` | Creates `.env` and a random secret (used by `setup.bat`). |
| `init_db.py` | Creates (or `--reset`s) the database and demo accounts. |
| `generate_sample_data.py` | Seeded sample data and import templates. |
| `demo_scenario.py` | Runs the demo scenario against a running installation. |

## Where to change things

| Change | Place |
|---|---|
| A seating rule or the solver | `backend/app/services/engine/` - then run `pytest tests/test_engine.py` and `python -m ml.benchmark --quick` |
| An import column | `backend/app/services/importer/spec.py` (templates follow), validation in `validate.py`, saving in `commit.py` |
| A PDF or Excel layout | `backend/app/services/exports/` |
| A screen | `frontend/src/pages/...` (API types in `src/lib/types.ts`) |
| Colours and fonts | `frontend/src/index.css`, `tailwind.config.ts` |
