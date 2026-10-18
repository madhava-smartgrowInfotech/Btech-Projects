# API reference

Base URL `http://localhost:8313`. Interactive docs at `/docs` (FastAPI).

## REST

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Service status, LLM configured?, pandapower version |
| GET | `/api/grid/state` | Latest power-flow snapshot (buses, lines, transformer, nodes, totals) |
| GET | `/api/grid/topology` | Graph layout: nodes, edges, devices |
| POST | `/api/simulation/start?resume=false` | Start a live run (body: `RunConfig`, optional) |
| POST | `/api/simulation/stop` | Stop the running simulation |
| POST | `/api/simulation/reset` | New engine at step 0 (body: `RunConfig`, optional) |
| POST | `/api/simulation/step` | Advance exactly one step |
| GET | `/api/simulation/status` | Status, step, provider, live summary |
| GET | `/api/scenarios` | The seven scenario definitions |
| POST | `/api/scenarios/{id}/run` | Run a scenario to completion, return its summary |
| GET | `/api/agents` | Agents with latest decision |
| GET | `/api/agents/{agent_id}` | History and latest decision |
| POST | `/api/agents/{agent_id}/decision` | **Dry run**: get the agent's proposal (no body) or validate an operator-crafted `action`; nothing is applied |
| GET | `/api/events?type=&run_id=&limit=` | Event log |
| GET | `/api/safety/events?status=&run_id=` | Hash-chained safety events, `chain_valid` |
| GET | `/api/safety/constraints` | Active constraint configuration |
| GET | `/api/metrics` | Summary metrics and per-step series |
| GET | `/api/runs`, `/api/runs/{id}`, `/api/runs/{id}/steps` | Stored runs |
| POST | `/api/experiments/run` | Start a baseline-vs-proposed experiment (background) |
| GET | `/api/experiments`, `/api/experiments/{id}` | Experiment jobs and stored results |

### `RunConfig`
`scenario_id`, `seed`, `steps`, `time_step_minutes`, `provider` (`mock|api|failing|baseline`), `unsafe_rate`, `step_delay_s`, `constraint_overrides`, `initial_soc`, `agents`, `inject_faults`, `shield_enabled` (leave `true` except for the ablation arm of experiments).

### `EnergyAction`
```json
{"agent_id": "prosumer_01", "action_type": "charge_battery", "power_kw": 3.2, "duration_minutes": 15,
 "target_node": null, "reason_codes": ["SOLAR_SURPLUS"], "confidence": 0.86}
```
Unknown fields are rejected (HTTP 422).

## WebSocket `/ws/simulation`

The server pushes JSON frames `{"type", "run_id", "timestamp", "data"}`. Clients only listen (any text sent is a keep-alive).

`connected`, `simulation_started`, `agent_action`, `safety_intervention`, `conflict_detected`, `grid_update`, `simulation_complete`, `simulation_stopped`, `simulation_error`.

## Limits of this API

Single process, one active run at a time, no authentication. Do not expose it to untrusted networks as is.
