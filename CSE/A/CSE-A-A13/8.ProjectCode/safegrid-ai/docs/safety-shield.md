# Symbolic Safety Shield

Location: `backend/app/safety/`. The shield is deterministic: the same action, node state and grid state always give the same decision (tested).

## Outcomes

- **APPROVED** - the action is safe as requested (its duration is aligned to the time step).
- **PROJECTED** - the action is unsafe as requested, so its power is scaled down to the largest value that passes every check. The original request is preserved next to the corrected one.
- **REJECTED** - the action is malformed, refers to unknown agents or nodes, is implausibly large, cannot be made safe, or would need a direction (import vs export) that cannot be reached safely. Nothing is executed.

## Checks (in order)

1. Structure: known agent, agent owns the node, known target node, finite non-negative power, plausible size.
2. Battery: availability (e.g. EV away), charge/discharge power limits, SOC bounds with charge/discharge efficiency over the step.
3. Node limits: import, export, generation (curtailment cannot exceed generation), load-shift fraction.
4. Power flow (trial run on the pandapower network): convergence, bus voltage 0.95 - 1.05 pu, line loading, transformer loading, grid import/export limits, power-balance residual.

All limits are configurable (`ConstraintConfig`, environment variables, or per-run `constraint_overrides`).

## Projection

If the request is unsafe, `projector.bisect_max` searches for the largest scale factor in [0, 1] that passes, first for the cheap local limits and then for power-flow limits. It assumes that reducing an action never makes it less safe (monotonicity), so the result is then **re-verified on the exact, rounded action** that would be executed (up to four times). If it cannot be verified it is rejected. Results below `min_action_kw` are rejected as pointless.

## Attribution of violations

Only violations that are **new or worse than the grid state without the action** are blamed on an action. Otherwise an action that *relieves* a pre-existing overload would be blocked by that overload. The flip side is important: the shield does not guarantee that the grid is violation-free, only that the executed actions do not create or worsen violations. Pre-existing stress (for example an evening peak that overloads the transformer with every agent idle) is reported separately as `violation_steps_no_action`.

## Import / export semantics

`import_power` and `export_power` are interpreted as **target net exchange at the node's connection point**. The shield back-calculates the storage setpoint needed to reach that exchange given the node's current load and PV.

## Audit log

Every non-approved decision (and every fallback/injected action) is written as a `SafetyEvent` with `prev_hash` and `hash` (SHA-256 over the previous hash, a canonical id/step/time tuple and the payload). Wall-clock time is excluded from the hash so reruns with the same seed give the same chain. `GET /api/safety/events` reports `chain_valid`. This is tamper-evident, not tamper-proof: someone who can rewrite the whole database can rewrite the chain.

## Event schema

```json
{
  "event_id": 3, "sim_time": "12:15", "step": 1, "timestamp": "2026-09-28T10:00:00.000+00:00",
  "event_type": "SAFETY_INTERVENTION", "status": "rejected",
  "agent_id": "renewable_01", "node_id": "node_3",
  "requested_action": {"action_type": "export_power", "power_kw": 1000.0},
  "validated_action": null,
  "violations": [{"code": "POWER_LIMIT_EXCEEDED", "component": "node_3", "requested": 1000.0, "allowed": 12.0, "unit": "kW"}],
  "corrections": [], "checks": [{"name": "STRUCTURE", "passed": false}],
  "decision_source": "injected", "prev_hash": "...", "hash": "..."
}
```

## What the shield does not claim

It checks the limits it was given on the model it was given. It does not prove global safety, does not model protection relays or dynamics, and its power-flow checks are only as good as the network model. See the README limitations.
