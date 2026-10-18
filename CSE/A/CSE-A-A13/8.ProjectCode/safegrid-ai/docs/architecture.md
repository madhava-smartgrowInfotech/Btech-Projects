# Architecture

```
 React dashboard  <--REST + WebSocket-->  FastAPI  -->  SimulationService
                                                            |
                                                      SimulationEngine (per run)
                                                            |
  Profiles (seeded solar/load/price)                        |
        |                                                   v
        v                                     +--------------------------+
  GridSimulator (pandapower) --state--> Agents (perceive, propose)  <--- LLM provider
        ^                                     |  (mock | real API | fallback)
        |                                     v
        |                              Coordinator (conflict detection, ordering)
        |                                     |
        |                                     v
        |                          Symbolic Safety Shield (deterministic)
        |                            APPROVE | PROJECT | REJECT
        |                                     |
        +------ only validated setpoints -----+
                                              |
                                  SQLite (runs, steps, events, hash-chained safety log)
```

## Trust boundaries

| Component | Trusted? | Role |
|---|---|---|
| LLM / mock LLM | No | Produces a *proposal* (`EnergyAction`) only |
| Agent | Partly | Builds context, calls the provider, falls back on failure; cannot touch the grid |
| Coordinator | Yes | Detects conflicts, fixes validation order; never edits an action |
| Safety Shield | Yes | Pure, deterministic rule checks + power-flow checks; imports nothing from `llm`, `agents`, `simulation` or `grid` |
| GridSimulator | Yes | The only code that mutates the pandapower network |

Model output is never executed as code, SQL or shell. The only thing a model can produce is a tool call that must
validate against the `EnergyAction` schema (`extra="forbid"`); the `agent_id` is set by the system, never by the model.

## Step lifecycle (`backend/app/simulation/engine.py`)

1. Seeded exogenous inputs for the step (PV, load, price, EV availability) are applied to the grid.
2. A no-action power flow gives the "current" state; each agent builds a structured context from it.
3. All agents propose concurrently. Provider failures, timeouts or invalid output become a labelled fallback decision.
4. The coordinator reports conflicts (`PEER_MISMATCH`, `TARGET_CONTENTION`, `SHARED_FEEDER`) and orders proposals: relief actions first, then a rotating order for fairness.
5. The shield validates the proposals **sequentially against the cumulative grid state**, so a later proposal sees the effect of earlier approved ones. This is how conflicts between agents are resolved safely.
6. Only validated setpoints are committed; a power flow is run, battery energy is integrated, and metrics/events are stored.

## Modules

- `app/safety/` - the shield (`shield.py`), constraint definitions, pure validators, projection by bisection, hash-chained events.
- `app/agents/` - `BaseAgent` and the three role agents, decision policy, structured explanations.
- `app/llm/` - provider interface, mock provider, fault injector, real API provider (Anthropic or OpenAI wire format), factory.
- `app/grid/` - pandapower network, power-flow wrappers, node state, simulator.
- `app/simulation/` - timeline/profiles, seven scenarios, coordinator, engine, experiment runner.
- `app/services/` - `SimulationService` (background runs, experiments) and the WebSocket hub.
- `app/api/` - FastAPI routers. `app/main.py` wires everything.
- `app/database/store.py` - SQLite behind a `Store` interface (replaceable with PostgreSQL).

## The test network

```
HV 20 kV --T0-- B0 (0.4 kV) --L0_1-- B1 [node_1 residential prosumer: load, PV 6 kWp, 10 kWh battery] --L1_3-- B3 [node_3 renewable prosumer: load, PV 20 kWp, 30 kWh battery]
                     \--L0_2-- B2 [node_2 EV / storage: load, 40 kWh EV, charge only]
```
