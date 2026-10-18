# Frontend rebuild plan - SafeGrid-AI (kit V3, Depth Studio)

Ports: backend **8313**, frontend **5313**. Code root: `8.ProjectCode/safegrid-ai/`.

## 1. Backend endpoints (unchanged)

| Method | Path | Request | Response (shape) |
|---|---|---|---|
| GET | `/api/health` | - | `{status, app_env, llm_provider, llm_configured, pandapower, ws_clients}` |
| GET | `/api/grid/state` | - | `{run_id, step, time, buses[], lines[], trafos[], nodes[], totals{generation_kw, load_kw, ext_grid_kw, import_kw, export_kw, losses_kw, min/max_voltage_pu, max_line_loading_pct}, converged}` |
| GET | `/api/grid/topology` | - | `{nodes[{id,type,x,y}], edges[{id,source,target,kind}], devices[{bus,label,devices[]}]}` |
| POST | `/api/simulation/start?resume=` | `RunConfig` (optional) | status object (409 if already running) |
| POST | `/api/simulation/stop` | - | status |
| POST | `/api/simulation/reset` | `RunConfig` (optional) | status |
| POST | `/api/simulation/step` | - | `{status, step}` (409 when finished) |
| GET | `/api/simulation/status` | - | `{status, step, total_steps, time, provider{name}, ...}` |
| GET | `/api/scenarios` | - | 7 scenario definitions `{id, name, description, n_steps, start_time, faults[]}` |
| POST | `/api/scenarios/{id}/run` | `RunConfig` (optional) | `{summary, ...}` - runs to completion |
| GET | `/api/agents` | - | `[{agent_id, node_id, role, label, soc, voltage_pu, exchange_kw, provider, latest}]` |
| GET | `/api/agents/{id}` | `?limit=` | `{agent_id, node_id, role, provider, history[], latest}` |
| POST | `/api/agents/{id}/decision` | `{action?: EnergyAction}` | dry-run record `{proposal, shield, explanation, ...}` - nothing applied |
| GET | `/api/events` | `?type=&run_id=&limit=` | `{run_id, events[]}` |
| GET | `/api/safety/events` | `?status=&run_id=&limit=` | `{run_id, chain_valid, total, events[]}` (hash-chained) |
| GET | `/api/safety/constraints` | - | active constraint config |
| GET | `/api/metrics` | - | `{run_id, status, summary{...}, series[]}` |
| GET | `/api/runs`, `/api/runs/{id}`, `/api/runs/{id}/steps` | - | stored runs |
| POST | `/api/experiments/run` | `{scenarios?, seeds[], steps?, arms?, time_step_minutes}` | job `{exp_id, status}` |
| GET | `/api/experiments`, `/api/experiments/{id}` | - | jobs, stored results, arm labels |
| WS | `/ws/simulation` | (listen only) | frames `{type, run_id, timestamp, data}`: `connected, simulation_started, agent_action, safety_intervention, conflict_detected, grid_update, simulation_complete, simulation_stopped, simulation_error` |

`EnergyAction`: `{agent_id, action_type, power_kw, duration_minutes, target_node, reason_codes[], confidence}`.
`RunConfig`: `scenario_id, seed, steps, time_step_minutes, provider(mock|api|failing|baseline), unsafe_rate, step_delay_s, constraint_overrides, initial_soc, agents, inject_faults, shield_enabled`.

No backend change is planned. No new endpoint is needed.

## 2. Existing features / screens (old React UI, 7 pages + shell)

| # | Feature | Old screen | Endpoints used | Done |
|---|---|---|---|---|
| F1 | Run controls: scenario, agent brain (provider), seed, Start / Resume / Step / Stop / Reset, progress | topbar (all pages) | start, stop, reset, step, status, scenarios | [x] |
| F2 | Live stream indicator (WebSocket connection state) + provider name | sidebar footer | `/ws/simulation` | [x] |
| F3 | Light / dark theme toggle (persisted) | sidebar footer | - | [x] |
| F4 | Backend-unreachable / action error banner | all pages | - | [x] |
| F5 | Dashboard: 7 KPI tiles (generation, load, grid exchange, voltage range, worst line, shield interventions, violations caused) | Dashboard | grid/state, metrics | [x] |
| F6 | Dashboard charts: generation/load/exchange, battery SOC, shield outcome per step | Dashboard | metrics | [x] |
| F7 | Latest shield intervention (proposal -> shield -> executed lane) | Dashboard | agents | [x] |
| F8 | Event timeline (live WS events + stored) + safety event count and chain validity | Dashboard | events, safety/events, WS | [x] |
| F9 | Grid view: single-line diagram, bus voltage colouring, line loading colouring, device cards | Grid view | grid/topology, grid/state | [x] |
| F10 | Line and transformer loading table | Grid view | grid/state | [x] |
| F11 | Agent cards (role, node, SOC, voltage, exchange, latest proposal, shield result, source) | Agent monitor | agents | [x] |
| F12 | Selected agent: latest decision lane, recent-decisions table, "context the agent saw" | Agent monitor | agents/{id} | [x] |
| F13 | Safety shield: counters (proposals, approved, projected, rejected, violations avoided / caused, audit chain) | Safety shield | metrics, safety/events | [x] |
| F14 | Safety events table with filter (all / projected / rejected), expandable checks, violations, hash and prev-hash | Safety shield | safety/events | [x] |
| F15 | Dry-run: craft an action and validate it against the shield (nothing applied) | Safety shield | agents/{id}/decision | [x] |
| F16 | Power flow: 8 charts (bus voltage + limits, line loading + 100% limit, node exchange, battery power, generation/consumption, import/export, price, losses) and non-convergence banner | Power flow | metrics, grid/state | [x] |
| F17 | Scenario runner: 7 scenario cards, Run to completion, summary table per scenario | Scenario runner | scenarios, scenarios/{id}/run | [x] |
| F18 | Experiment: seeds + steps, run baseline-vs-proposed, poll job, results table + notes | Scenario runner | experiments/run, experiments/{id} | [x] |
| F19 | Explainability: agent picker, decision lane, decision factors, reason codes, source, context, safety result + violations, raw JSON | Explainability | agents | [x] |
| F20 | Constraint configuration view (`/api/safety/constraints` wrapper exists in api.js but no old screen shows it) | new, in Safety shield | safety/constraints | [x] |

## 3. Screen map to build

Public: **Landing** `/` (three.js hero, scroll story, CTA to console) - new.
Console (AppShell: sidebar -> drawer under 900px, topbar with run controls, theme toggle, WS dot):

| Route | Screen | Covers |
|---|---|---|
| `/app` | Dashboard | F5-F8 |
| `/app/grid` | Grid view | F9, F10 |
| `/app/agents` | Agent monitor | F11, F12 |
| `/app/shield` | Safety shield (+ constraints panel, dry-run) | F13-F15, F20 |
| `/app/power-flow` | Power flow | F16 |
| `/app/scenarios` | Scenario runner + experiment | F17, F18 |
| `/app/explain` | Explainability | F19 |
| shell | run controls, WS status, theme, error banner | F1-F4 |

State: keep the existing `SimulationProvider` (REST + WebSocket) and `services/api.js` / `ws.js` as is; only the UI layer is replaced.

## 4. Run / ports plan

- No `run.bat`, root `.env` or `docs/03_HOW_TO_RUN.md` exist yet. Add `run.bat` (creates `backend/.venv`, installs, starts uvicorn on 8313 and vite on 5313), root `.env` + `.env.example` with `BACKEND_PORT=8313`, `FRONTEND_PORT=5313`, update `CORS_ORIGINS` to 5313, `vite.config.js` proxy to 8313, and write `docs/03_HOW_TO_RUN.md`.
- Backend deps are installed into `backend/.venv` (gitignored).

## 5. Verification (done)

- [x] `npm run build` passes (Vite 5, code-split: landing, login and each console page are lazy chunks; three.js loads only on the landing page).
- [x] `python scripts/smoke_test.py` - 20 checks pass against the running backend (health, scenarios, topology, reset/step, grid state, agents + history, dry run, metrics, hash-chain valid, constraints, scenario run, events, runs, 404, frontend proxy).
- [x] Walked every screen in Chromium through the real API: login (wrong password error, demo sign-in), run controls (reset, step, start, instant playback), dashboard, grid view, agent monitor, safety shield (dry run, event detail modal, filter), power flow, scenarios (run + strategy comparison), explainability, sign out and route guard.
- [x] Console clean in dark and light at 360, 768 and 1440 px (no errors, no failed requests, no 4xx/5xx, no unhandled rejections).
- [x] No horizontal overflow on any screen at 360 and 768 px; sidebar becomes a drawer; Escape closes drawer and dialogs; skip link gets first focus.
- [x] Theme toggle persists across reloads; `prefers-reduced-motion` swaps the 3D hero for a static image.
- [x] Screenshots at 1440x900 in `docs/screenshots/` (landing in dark and light) via `scripts/capture_screens.py`.
- [x] `docs/03_HOW_TO_RUN.md` and `run.bat` added; README run section updated for ports 8313 / 5313.

Notes
- Added a demo sign-in (`operator@safegrid.ai` / `SafeGrid@2026`). The API has no accounts, so it is a browser-side gate for demos, not a security boundary.
- Backend tests: `tests/test_api.py::test_websocket_receives_events` hangs under the installed Starlette test client, and two grid tests (`test_power_flow_converges_and_balances`, `test_trial_does_not_change_committed_state`) fail on numeric tolerances against pandapower 3.5.6. These are in the backend as delivered and were not touched.
- The strategy comparison runs 21 simulations per seed and takes roughly a minute at 8 steps; the screen shows elapsed time while it runs.
