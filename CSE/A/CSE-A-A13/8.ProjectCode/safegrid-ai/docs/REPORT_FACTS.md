# REPORT FACTS - SafeGrid-AI

Single source of truth for every submission document. All numbers below were produced on **2026-10-18** by running this repository
(experiment: `backend/app/simulation/run_experiment.py`; tests: `pytest`; latency: live HTTP calls against `uvicorn`). Nothing is copied from a paper.
Raw experiment output: `docs/results/experiment_3seeds_24steps.json` (63 simulation runs, 1,512 agent proposals per arm).

## 1. Identity

| Item | Value |
|---|---|
| Project | SafeGrid-AI: An Explainable Multi-Agent System for Dynamic Power Routing |
| Batch | CSE-A, Batch 13 (A13) |
| College | TKR College of Engineering & Technology (Autonomous) - from `Documentary/Batch_13_...docx` |
| Students | DISHA KAUSHAL 23K91A0563; BOLLAM RAKESH 23K91A0542; CHINNOLLA RAVINDHAR 23K91A0554; AFFAN MOHAMMED RAMY 23K91A0505 |
| Guide | CHANDRASHEKAR (designation not stated in the source files) |
| Unknown, left as placeholder | principal, HOD, academic year, city, e-mail addresses, guide designation |
| Base paper (as recorded in `3.BASE PAPER.docx`) | S. E. Eyimaya and N. Altin, "Design of Multi-Agent-Based Energy Management System for DC Microgrids," IEEE Access, vol. 14, pp. 39120-39133, 2026, doi 10.1109/ACCESS.2026.3672618 |
| Supporting references (files in batch folder) | Y. Zhang et al., "Grid-Agent: An LLM-Powered Multi-Agent System for Power Grid Control," arXiv:2508.05702, 2025; J. Picault and C. Goubet, "Orchestrating Power Grid Studies with Multi-Agent AI and MCP Servers," arXiv:2607.14158, 2026 |

Base paper facts (read from the PDF): DC microgrid with PV, wind, synchronous generator, battery ESS, grid and critical/non-critical loads; four rule-based agents (DER, ESS, load, grid);
MATLAB/Simulink, 20 microsecond sampling, 800 V DC bus, eight operating scenarios; result: bus voltage regulated at 800 V in all scenarios and critical loads continuously supplied;
stated limitations: scalability, software integration, cybersecurity, no experimental validation. No LLM, no formal safety layer, no explanation interface.
Grid-Agent facts: planning agent + validation agent with sandboxed execution and rollback, IEEE 69-bus / CIGRE MV / IEEE 30-bus, top LLM configurations reported 100 % success rate; some weaker ones 63 % and 44 %.

## 2. What the system is (and is not)

- Software-only simulation of a 3-node low-voltage feeder (pandapower 3.5.6, AC power flow). Three agents: `prosumer_01` (node_1, residential, 6 kWp PV, 10 kWh battery),
  `ev_01` (node_2, 40 kWh EV, charge only, 7.4 kW), `renewable_01` (node_3, 20 kWp PV, 30 kWh battery).
- Each step: seeded profiles (PV, load, price) -> no-action power flow -> agents perceive structured context -> propose one `EnergyAction` -> coordinator detects conflicts and orders proposals ->
  **Symbolic Safety Shield** validates sequentially against cumulative grid state (APPROVED / PROJECTED by bisection / REJECTED) -> only validated setpoints are committed -> hash-chained safety log.
- **The "LLM" used in every measured result is a deterministic, seeded mock provider** (`MockLLMProvider`, built on a transparent cost-aware heuristic with seeded over-sizing).
  A real-LLM provider (`APILLMProvider`, Anthropic or OpenAI wire format, tool-call output schema-validated) exists but was **not exercised against a live model** (no API key configured; `llm_configured=false`).
  Consequence: results measure the shield and coordination, not language-model reasoning quality.
- Explanations are structured (inputs, decision factors, action, safety result). **No chain-of-thought is requested or stored** (tested). The batch abstract speaks of "chain-of-thought reasoning"; the implementation deliberately does not.
- The shield guarantee is narrower than the abstract's wording: executed actions never create or worsen a violation of the configured limits under the simulated model. It does **not** guarantee a violation-free grid
  (pre-existing stress is reported separately) and is not a formal proof.

## 3. Architecture summary

Layers: React 18 dashboard (Vite, kit V3 "Depth Studio", three.js landing hero) <-> FastAPI REST + WebSocket `/ws/simulation` <-> `SimulationService` <-> `SimulationEngine` (per run) <->
{agents, coordinator, shield, pandapower `GridSimulator`} <-> SQLite (`runs`, `events`, `safety_events`, `steps`, `experiments`).
Trust boundaries: LLM/mock = untrusted proposer; agent = partly trusted; coordinator, shield, simulator = trusted. The shield imports nothing from `llm`, `agents`, `simulation`, `grid` (enforced by test `test_shield_does_not_import_llm_or_agents`).

Shield checks, in order: STRUCTURE, POWER_LIMITS, BATTERY, NODE_LIMITS, POWER_BALANCE, POWER_FLOW, VOLTAGE (0.95-1.05 pu), LINE_LOADING (100 %), TRANSFORMER (100 %), GRID_LIMITS (200 kW import/export).
25 violation codes. Projection: bisection for the largest scale factor lam in [0,1] (40 iterations local limits, 14 iterations power-flow limits), then up to 4 re-verifications of the exact rounded action; results below 0.05 kW are rejected.
Attribution: only violations that are new or worse than the no-action grid state are blamed on an action. Audit log: SHA-256 chain over (prev_hash, [event_id, run_id, step, sim_time], payload).
Coordinator conflict types: PEER_MISMATCH, TARGET_CONTENTION, SHARED_FEEDER. Order: relief actions (idle, curtail, shift) first, then rotating order.
Action types (7): charge_battery, discharge_battery, import_power, export_power, curtail_generation, shift_load, idle. `EnergyAction` schema is `extra="forbid"`, power 0..1,000,000 kW finite, duration 1..1440 min, reason codes `[A-Z0-9_]{1,48}`.
Providers: `mock`, `api`, `failing`, `baseline`; any provider failure/timeout/invalid output becomes a labelled deterministic `fallback` decision (still shielded).
Network: HV 20 kV -- T0 (0.25 MVA 20/0.4 kV) -- B0 -- L0_1 (0.30 km) -- B1 -- L1_3 (0.45 km) -- B3; B0 -- L0_2 (0.25 km) -- B2; line type NAYY 4x50 SE; load power factor 0.95; 15-minute time step.
Scenarios (7): normal (32 steps), high_solar (24), peak_demand (24), battery_stress (16), line_congestion (16), voltage_violation (16), unsafe_ai_action (12).
Code size: backend 3,117 lines (`app/`), tests 624 lines, frontend 6,989 lines (JS/JSX/CSS, `src/`).

## 4. Dataset facts

There is **no external dataset and no trained model**. Inputs are synthetic and generated at run time from a seed: solar profile `sin^1.2` between 06:00 and 18:00 scaled by a seeded cloud factor (0.45-1.0);
household load shape = 0.55 + morning bump + evening bump with 5 % seeded noise; time-of-use tariff 3.8 / 5.2 / 4.6 / 9.0 / 5.0 INR per kWh (illustrative); export credited at 60 % of the import price.
No train/validation/test split, no accuracy, F1 or confusion matrix exist for this project. Licence: not applicable (generated data). Never write such metrics.

## 5. Measured results

Experiment: 7 scenarios x 3 arms x 3 seeds (0, 1, 2) x 24 steps, 15-min step, mock provider. Arms: `baseline_rule` (non-LLM time-of-use rules, no shield, no fault injection),
`agents_unshielded` (agents + scenario faults, proposals applied as requested), `safegrid_shielded` (agents + faults + shield). Wall time for the 63 runs about 10 minutes on the machine in section 7.

### Overall (mean over 7 scenarios x 3 seeds = 21 runs per arm, 24 steps each)

| Metric | Rule baseline | Agents, no shield | SafeGrid-AI |
|---|---|---|---|
| Steps with violations caused by actions | 2.19 | 4.71 | 0.00 |
| Violations caused by actions | 2.19 | 6.86 | 0.00 |
| Violations the raw proposals would cause | 6.05 | 8.52 | 9.14 |
| Steps with pre-existing stress (all idle) | 6.33 | 6.33 | 6.33 |
| Steps with any violation after execution | 6.05 | 6.38 | 2.48 |
| Voltage violation steps | 4.33 | 4.43 | 3.14 |
| Line overload events | 1.71 | 1.86 | 0.71 |
| Transformer overload events | 0.00 | 0.14 | 0.00 |
| Energy cost, INR (illustrative tariff) | 216.4 | 380.8 | 225.0 |
| Renewable utilisation | 1.000 | 0.884 | 0.860 |
| Battery utilisation (throughput / capacity) | 0.520 | 3.392 | 0.508 |
| Shield intervention rate | 0.000 | 0.000 | 0.232 |
| Fallback rate | 0.0000 | 0.0020 | 0.0020 |
| Mean decision latency, ms | 0.103 | 0.160 | 0.168 |
| Mean step time, ms | 107.9 | 106.2 | 347.8 |

### Steps with violations caused by actions, per scenario (mean of 3 seeds; 24 steps)

| Scenario | Rule baseline | Agents, no shield | SafeGrid-AI |
|---|---|---|---|
| normal | 0.00 | 1.67 | 0.00 |
| high_solar | 0.00 | 0.67 | 0.00 |
| peak_demand | 3.33 | 4.00 | 0.00 |
| battery_stress | 0.00 | 4.67 | 0.00 |
| line_congestion | 12.00 | 11.33 | 0.00 |
| voltage_violation | 0.00 | 6.33 | 0.00 |
| unsafe_ai_action | 0.00 | 4.33 | 0.00 |

### Shield decisions per scenario, SafeGrid-AI arm (mean of 3 seeds)

| Scenario | Proposals | Approved | Projected | Rejected | Raw-proposal violations | Pre-existing stress steps | Cost INR |
|---|---|---|---|---|---|---|---|
| normal | 72 | 59.7 | 8.7 | 3.7 | 1.7 | 0.3 | -16.7 |
| high_solar | 72 | 55.7 | 12.0 | 4.3 | 2.3 | 20.0 | -97.6 |
| peak_demand | 72 | 61.0 | 9.0 | 2.0 | 14.0 | 12.0 | 1126.4 |
| battery_stress | 72 | 52.0 | 12.0 | 8.0 | 5.3 | 3.0 | -57.0 |
| line_congestion | 72 | 45.7 | 23.0 | 3.3 | 16.0 | 0.0 | 580.8 |
| voltage_violation | 72 | 57.3 | 6.3 | 8.3 | 12.7 | 6.7 | 61.5 |
| unsafe_ai_action | 72 | 56.0 | 8.0 | 8.0 | 12.0 | 2.3 | -22.7 |

Headline numbers (all from the files above):
- Across 21 shielded runs: 1,512 proposals -> **1,162 approved (76.9 %), 237 projected (15.7 %), 113 rejected (7.5 %)**; 354 safety-log events; hash chain valid in 21/21 runs; 241 coordinator conflicts.
- **Violations caused by executed actions: 0 in all 504 shielded steps**, versus 144 violations over 99 steps without the shield (agents, no shield) and 46 over 46 steps for the rule baseline (from the congestion and peak-demand scenarios).
- Raw shielded-arm proposals would have caused 192 violations in 145 steps; the shield removed all of them.
- Pre-existing stress (violations present even with every agent idle) is not removed by design: 6.33 steps per run on average (e.g. high_solar 20 of 24 steps). Steps with any violation after execution:
  6.05 baseline, 6.38 unshielded, **2.48 shielded** (relief-first ordering and projection also reduce some pre-existing stress, but zero is not guaranteed).
- Cost of safety (illustrative tariff): mean cost 225.0 INR (shielded) vs 380.8 (unshielded) vs 216.4 (rule baseline); renewable utilisation 0.860 (shielded) vs 0.884 (unshielded) vs 1.000 (baseline);
  the shield limits some PV in high_solar (0.607) and voltage_violation (0.787).
- Compute cost: mean step time **347.8 ms shielded vs about 107 ms without the shield** (trial power flows during validation); decision latency of the mock provider 0.17 ms (not representative of a real LLM).
- Fallback rate 0.2 % (the injected malformed-output fault in `unsafe_ai_action`).

### Live API latency (uvicorn on localhost, scenario unsafe_ai_action, seed 42)

| Call | n | median ms | p95 ms |
|---|---|---|---|
| GET /api/health | 50 | 1.7 | 15.4 |
| GET /api/grid/state | 50 | 2.5 | 25.5 |
| GET /api/scenarios | 50 | 2.7 | 23.2 |
| GET /api/agents | 30 | 2.7 | 16.2 |
| POST /api/agents/{id}/decision (agent proposal dry run) | 30 | 62.8 | 84.5 |
| POST dry run, unsafe 1000 kW export (rejected) | 30 | 36.6 | 80.5 |
| POST dry run, 9 kW charge (projected by bisection) | 30 | 230.0 | 262.6 |
| POST /api/simulation/step | 12 | 440.7 | 522.2 |

Full scenario to completion through `POST /api/scenarios/{id}/run`: `normal` 32 steps in 10.68 s (96 proposals, 10 interventions); `unsafe_ai_action` 12 steps in 2.12 s (36 proposals, 12 interventions).
Strategy comparison through the dashboard (21 simulations per seed, 8 steps): about one minute.

### Tests (`backend/`, Python 3.11.9, pytest 9.1.1, 2026-10-18)

55 test functions: test_safety 22, test_agents 12, test_simulation 11, test_grid 6, test_api 4.
Result: **52 passed, 2 failed, 1 hangs (excluded)** in 55 s (`--deselect tests/test_api.py::test_websocket_receives_events`).
- Failing: `test_grid.py::test_power_flow_converges_and_balances` (external-grid power 10.995 kW vs expected 10.0 +/- 0.5 kW) and `test_grid.py::test_trial_does_not_change_committed_state`
  (-3.12314 vs -3.123 +/- 1e-6): numeric tolerances chosen for an older pandapower; the power flow itself converges. Not fixed (backend untouched by the documentation task).
- Hanging: `test_websocket_receives_events` blocks under the installed Starlette test client. The WebSocket endpoint works live (the dashboard uses it).
- Smoke test `scripts/smoke_test.py`: 20/20 checks pass against the live API.
- Frontend: `npm run build` passes; browser walk (Playwright/Chromium) of every screen at 360/768/1440 px, light and dark: no console errors, no horizontal overflow (frontend rebuild commit `710115c2`).
- Package versions in `backend/.venv`: pandapower 3.5.6, FastAPI 0.143.3, pydantic 2.14.1, numpy 2.4.6, pandas 2.3.3, scipy 1.17.1, uvicorn 0.54.0, httpx 0.28.1.

## 6. Endpoints

GET `/api/health`; GET `/api/grid/state`, `/api/grid/topology`; POST `/api/simulation/start?resume=`, `/stop`, `/reset`, `/step`; GET `/api/simulation/status`; GET `/api/scenarios`; POST `/api/scenarios/{id}/run`;
GET `/api/agents`, `/api/agents/{id}`; POST `/api/agents/{id}/decision` (dry run, nothing applied); GET `/api/events`; GET `/api/safety/events`, `/api/safety/constraints`; GET `/api/metrics`;
GET `/api/runs`, `/api/runs/{id}`, `/api/runs/{id}/steps`; POST `/api/experiments/run`; GET `/api/experiments`, `/api/experiments/{id}`; WebSocket `/ws/simulation`
(frames: connected, simulation_started, agent_action, safety_intervention, conflict_detected, grid_update, simulation_complete, simulation_stopped, simulation_error).
Database tables: runs, events, safety_events, steps, experiments (SQLite, standard library).
Security posture: no authentication on the API (single-user research prototype); the dashboard demo sign-in (`operator@safegrid.ai`) is a browser-side gate only; model output is never executed as code/SQL/shell; CORS origin list configurable; `.env` never committed.

## 7. Measurement machine (for "System Hardware")

Intel Core i5-12500 (6 cores / 12 threads), 15.7 GB RAM, Windows 11 Pro, no GPU used; Python 3.11.9, Node.js v24.19.0, Chromium via Playwright 1.44.0.

## 8. Screenshot inventory (`docs/screenshots/`, 1440x900, real run: scenario `unsafe_ai_action`, mock provider, seed 42, instant playback, 12 of 12 steps)

01_landing_dark, 01_landing_light (three.js hero), 02_landing_how_it_works, 03_login, 04_dashboard (8 KPI cards, 12 interventions of 36 proposals, 0 violations caused),
05_grid_view (single-line diagram), 06_agent_monitor, 07_safety_shield (events table, dry-run rejection of a 1000 kW export, active constraints),
08_power_flow, 09_scenarios (strategy comparison results), 10_explainability. Captured by `scripts/capture_screens.py`.

## 9. Honest gaps (to be stated plainly in every document)

1. No evaluation with a real LLM; every agent result is the deterministic mock provider.
2. Objective 6 asks for "violation resolution rate": the project measures violations *prevented* (caused-by-actions = 0) and steps with any violation, not a resolution rate for pre-existing violations.
3. "Decision latency" is 0.1-0.2 ms for the mock provider; real LLM latency was not measured.
4. Three seeds only; 3-node synthetic feeder; no real network or measurement data; illustrative tariff; no protection, dynamics, or three-phase unbalance.
5. The shield gives a model-relative guarantee (no new or worse violations), not a proof; the abstract's "mathematically guaranteeing zero physical constraint violations" is stronger than what was built or tested.
6. Comparison with the base paper is qualitative only (different system: DC microgrid in MATLAB/Simulink, rule-based agents, no LLM, no safety layer, no dataset); no like-for-like numeric comparison exists.
7. Two numeric-tolerance unit tests fail on pandapower 3.5.6 and one WebSocket test hangs.
8. No user study; "user acceptance" was not conducted.

## 10. Single-run traces (seed 42, scenario's native length, mock provider; `docs/results/timeseries_seed42.json`, figure `docs/figures/fig_timeseries.png`)

| Scenario | Quantity | Agents, no shield | SafeGrid-AI | Limit |
|---|---|---|---|---|
| line_congestion (16 steps) | worst line loading over the run | 137.7 % | 100.0 % (projected exactly to the limit) | 100 % |
| voltage_violation (16 steps) | highest bus voltage | 1.117 pu | 1.056 pu (pre-existing stress remains slightly above the limit) | 1.05 pu |
| peak_demand (24 steps) | lowest bus voltage | 0.861 pu | 0.932 pu (below 0.95 even with every agent idle: pre-existing stress) | 0.95 pu |

Steps with violations caused by actions in these three single runs (shield on / off): line_congestion 0 / 8, voltage_violation 0 / 6, peak_demand 0 / 4.
Interpretation: the shield removes what the agents add and keeps the worst case at or near the limit; it does not repair a grid that is already outside its limits.
