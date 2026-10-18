# Experimental evaluation

Run from the dashboard (Scenario runner, "Run experiment"), with `POST /api/experiments/run`, or from the command line:

```bash
cd backend
python -m app.simulation.run_experiment --seeds 0 1 2 --steps 24 --out results/experiment.json
```

## Arms

| Arm | Controller | Shield | Fault injection |
|---|---|---|---|
| `baseline_rule` | Non-LLM time-of-use rules | off | no |
| `agents_unshielded` | Agents (mock LLM) | off | scenario faults |
| `safegrid_shielded` | Agents (mock LLM) | on | scenario faults |

Every arm runs on the same scenario and seed, so differences come from the controller and the shield. The unshielded ablation shows what the shield contributes; the baseline shows what a simple non-AI controller does.

## Metrics

Requested / approved / projected / rejected counts; violations the raw proposals would cause; **violations caused by executed actions** (new or worse than the all-idle grid state); pre-existing stress steps; voltage-violation steps; line and transformer overload events; energy cost (illustrative tariff, export credited at 60% of import price); renewable utilisation (1 - curtailed / available PV); battery throughput and utilisation; decision latency; step time; fallback rate.

## Reading the results honestly

- The network is a small 3-node illustrative feeder; the results are simulation results, not field results.
- The mock LLM is a deterministic rule-driven stand-in with seeded misbehaviour; a real LLM will behave differently. Use `LLM_PROVIDER=api` to test one.
- The decision policy is a transparent heuristic. Nothing here claims globally optimal dispatch.
- Cost numbers use an invented tariff; compare arms with each other, not with real bills.
- "Violations caused by executed actions = 0" is the property the shield is designed to give under its model and limits. It is not a proof of safety in general.
- Report means *and* spreads over several seeds; the runner returns min, max and standard deviation.
