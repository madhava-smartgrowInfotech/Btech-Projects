# SafeGrid-AI

Explainable multi-agent power routing for a small smart grid, with a deterministic **Symbolic Safety Shield** between AI proposals and the grid.

LLM-driven agents (a residential prosumer, an EV / storage node and a renewable prosumer) propose energy actions. A rule-based shield checks every proposal against battery, node and network limits using a pandapower power flow, and approves it, scales it down (projection) or rejects it. Only validated actions ever reach the simulated grid. A React dashboard shows what the AI proposed, what the shield decided and what was actually executed.

> Research prototype. Everything runs on a simulated 3-node low-voltage feeder. It is not connected to, and must not be used to control, real equipment.

## Contents
1. [Research motivation](#research-motivation)
2. [Architecture](#architecture)
3. [Tech stack](#tech-stack)
4. [Folder structure](#folder-structure)
5. [Installation](#installation)
6. [Environment variables](#environment-variables)
7. [Running the backend](#running-the-backend)
8. [Running the frontend](#running-the-frontend)
9. [Running the tests](#running-the-tests)
10. [Running scenarios and experiments](#running-scenarios-and-experiments)
11. [Understanding the Safety Shield](#understanding-the-safety-shield)
12. [Understanding the multi-agent system](#understanding-the-multi-agent-system)
13. [Evaluation methodology](#evaluation-methodology)
14. [Limitations and verification status](#limitations-and-verification-status)
15. [Future work](#future-work)

## Research motivation

LLM agents are attractive for energy management because they can weigh messy context and explain themselves, but their output is unreliable and can be wrong, oversized or malformed. Physical systems need hard guarantees that a language model cannot give. SafeGrid-AI separates the two: the AI is free to propose, and a small deterministic layer decides what is allowed. The project investigates how much unsafe behaviour such a shield removes, and what it costs in dispatch quality.

Four objectives: (1) decentralised agents that propose actions, (2) a deterministic shield that enforces constraints, (3) a power-flow simulation to check network effects, (4) an explainable dashboard.

## Architecture

```
LLM / mock agent --proposal--> Coordinator --> Symbolic Safety Shield --validated action--> pandapower grid
      ^                                              (approve | project | reject)                  |
      +-------------------------- observations (voltages, loading, prices, SOC) <-------------------+
                                                     |
                                      SQLite + hash-chained safety log --> FastAPI (REST + WebSocket) --> React
```

Details: [`docs/architecture.md`](docs/architecture.md), [`docs/safety-shield.md`](docs/safety-shield.md), [`docs/api.md`](docs/api.md), [`docs/experiments.md`](docs/experiments.md).

## Tech stack

Backend: Python 3.10+, FastAPI, Pydantic v2, pandapower, NumPy, pandas, SciPy, SQLite (standard library), httpx. Frontend: React 18, Vite, React Router, Recharts, Framer Motion and three.js (Depth Studio design kit). Communication: REST and WebSocket.

## Folder structure

```
safegrid-ai/
  backend/
    app/
      main.py                 FastAPI entrypoint
      config.py               environment-based settings
      api/                    routers: grid, simulation, agents, safety, metrics
      agents/                 base agent, 3 role agents, policy, manager, explanations
      safety/                 shield, constraints, validator, projector, models, events   <- core contribution
      grid/                   pandapower network, power flow, state, simulator
      simulation/             timestep/profiles, scenarios, coordinator, engine, experiment runner, CLIs
      llm/                    provider interface, mock, fault injector, real API provider
      models/                 EnergyAction and API schemas
      services/               SimulationService, WebSocket hub
      database/               SQLite store
    tests/                    test_safety, test_agents, test_grid, test_simulation, test_api
    requirements.txt  .env.example  pytest.ini
  frontend/
    src/{components,pages,hooks,services,charts}
    package.json  vite.config.js
  docs/
```

## Installation

Requirements: Python 3.10 or newer, Node.js 18 or newer.

```bash
# backend
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                 # Windows: copy .env.example .env

# frontend
cd ../frontend
npm install
```

## Environment variables

Set in `backend/.env` (see `.env.example`).

| Variable | Default | Meaning |
|---|---|---|
| `LLM_PROVIDER` | `mock` | `mock`, `api`, `failing` (always fails, tests fallback), `baseline` |
| `LLM_API_KEY`, `LLM_MODEL` | empty | needed for `api`; without them agents use the labelled fallback policy |
| `LLM_API_STYLE` | `anthropic` | wire format: `anthropic` or `openai` |
| `LLM_BASE_URL` | provider default | override endpoint (for compatible servers) |
| `LLM_TIMEOUT_SECONDS` | `20` | per-decision timeout, then fallback |
| `DATABASE_URL` | `sqlite:///./safegrid.db` | SQLite file |
| `VOLTAGE_MIN`, `VOLTAGE_MAX` | `0.95`, `1.05` | pu limits |
| `LINE_MAX_LOADING_PCT`, `TRAFO_MAX_LOADING_PCT` | `100` | loading limits |
| `DEFAULT_TIME_STEP_MINUTES`, `DEFAULT_SEED` | `15`, `42` | simulation defaults |
| `CORS_ORIGINS` | `http://localhost:5313,...` | allowed browser origins |

Never commit `.env`. The real-LLM provider sends the agent's structured context to the configured API; do not put sensitive data in it.

## Running the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8313
```
Open http://localhost:8313/docs for the interactive API docs and http://localhost:8313/api/health for a health check. On Windows, `run.bat` in this folder does the whole setup and starts both servers (see `docs/03_HOW_TO_RUN.md`).

## Running the frontend

```bash
cd frontend
npm run dev
```
Open http://localhost:5313 and sign in with the demo account (`operator@safegrid.ai` / `SafeGrid@2026`). The dev server proxies `/api` and `/ws` to port 8313. Pick a scenario in the run controls and press **Start** (live playback) or **Step**. For a production build: `npm run build`.

## Running the tests

```bash
cd backend
pytest
```
`test_safety.py` and `test_agents.py` need only Pydantic. `test_grid.py`, `test_simulation.py` and `test_api.py` need pandapower (and FastAPI for the API tests) and skip themselves if they are missing.

## Running scenarios and experiments

```bash
cd backend
python -m app.simulation.run_scenario unsafe_ai_action --seed 42          # shows every proposal and what the shield did
python -m app.simulation.run_scenario line_congestion --no-shield         # ablation: same run without the shield
python -m app.simulation.run_experiment --seeds 0 1 2 --steps 24 --out results/experiment.json
```

Scenarios: `normal`, `high_solar`, `peak_demand`, `battery_stress`, `line_congestion`, `voltage_violation`, `unsafe_ai_action`. The last four inject intentionally unsafe or malformed proposals at fixed steps so the shield's behaviour is reproducible without a real LLM.

## Understanding the Safety Shield

Each proposal is an `EnergyAction` (agent, action type, power, duration, reason codes, confidence). The shield runs structural checks, battery and node-limit checks, and then a trial power flow (voltage, line and transformer loading, grid limits, power balance). It returns **APPROVED**, **PROJECTED** (power reduced to the largest verified safe value, original request kept) or **REJECTED**. Violations are attributed only to actions that make the grid state new-or-worse, so an action that relieves an existing overload is not blocked. Every intervention is written to a hash-chained log. See [`docs/safety-shield.md`](docs/safety-shield.md).

The shield never imports LLM, agent, simulation or grid code (enforced by a test), so it cannot be influenced by model text.

## Understanding the multi-agent system

Three agents each own one node: a residential prosumer (load, PV, battery), an EV / storage node (charge-only EV with an optional target state of charge), and a renewable prosumer (large PV and battery). Every step an agent perceives a structured context (own load, solar, SOC, price, weather, neighbours' exchange and voltage, grid limits, its previous action) and asks its provider for one action.

Providers: `mock` (deterministic, seeded, occasionally over-eager), `api` (real LLM via tool calling; its output is treated as untrusted and schema-validated, and the agent id is never taken from the model), `failing`, and `baseline` (non-LLM rules). If a provider fails, times out or returns invalid output, a deterministic fallback policy is used and the decision is labelled `fallback` with the reason. Agents do not negotiate directly. The coordinator detects peer mismatch, target contention and shared-feeder conflicts, and the shield validates proposals in sequence against the cumulative grid state. Explanations contain inputs, decision factors, the action and the safety outcome; no chain-of-thought is requested or stored.

The decision policy is a transparent heuristic (price bands, SOC headroom, voltage awareness). It is not claimed to be optimal.

## Evaluation methodology

Three arms are compared on identical scenarios and seeds: a non-LLM rule baseline, the agents without the shield (ablation), and the full system. Metrics include violations the raw proposals would cause, violations caused by executed actions, voltage and line overload events, energy cost, renewable utilisation, battery use, decision latency and fallback rate. See [`docs/experiments.md`](docs/experiments.md). No result numbers are included in this repository: run the experiment yourself.

## Limitations and verification status

**Verification status (please read).** This project was written in a sandbox without network access, so `pandapower`, `FastAPI`, `pytest` and the frontend dependencies could not be installed there. What was actually run:

- The shield, agents, providers, coordinator, engine, experiment runner, SQLite store and service layer were executed and tested (51 tests passing) using small local stand-ins for Pydantic and pytest, and a simple linearised radial solver standing in for pandapower.
- **Not run:** the code against the real pandapower (`network.py`, `power_flow.py`, `simulator.py` are written to the pandapower API and compile, but real numerical behaviour is unverified), the FastAPI server and WebSocket endpoint (`test_api.py` was skipped), and the frontend build (`npm install` / `vite`; the JSX files were only syntax-checked).
- So expect to fix small integration issues on first run, for example a pandapower version difference or a standard-type name. Run `pytest` first: `test_grid.py` and `test_simulation.py` exercise the pandapower path. Scenario thresholds (for example the reduced ampacity of `L0_2` and the weak-feeder settings) were chosen from typical cable data and should be re-tuned against real power-flow results if a scenario does not trigger as described.

**Modelling limits.**
- Small illustrative 3-node feeder, balanced single-phase-equivalent AC power flow, no protection, dynamics or unbalance.
- Time-of-use tariff and export credit are illustrative.
- The shield guarantees only that executed actions do not create or worsen violations of the configured limits under the simulated model. It does not guarantee a violation-free grid, and it is not a formal proof of safety.
- Projection assumes that reducing an action's power does not make it less safe; the final action is re-verified, and rejected if the check fails.
- The hash chain is tamper-evident, not tamper-proof.
- Single process, one active run, no authentication.
- Mock-LLM results say little about real LLM behaviour.

## Future work

Real network and measurement data; unbalanced three-phase models; more agents and multi-feeder topologies; agent-to-agent negotiation with shield-validated contracts; a learned or optimisation-based policy compared with the heuristic; formal verification of the projection step; PostgreSQL storage; authentication and multi-user runs; evaluation with several real LLMs and adversarial prompt testing.
