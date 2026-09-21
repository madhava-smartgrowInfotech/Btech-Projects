# Engine evaluation

SeatWise has no trained model: its core is an OR-Tools CP-SAT optimisation engine. This folder benchmarks that engine on seeded synthetic exam sessions and compares it with the ways seating is usually done by hand.

| File | Purpose |
|---|---|
| `scenarios.py` | The scenario matrix (150 to 2,000 candidates, 8- and 4-neighbour adjacency, roll gaps 0 / 5 / 10) and a seeded builder for each scenario. `python -m ml.scenarios` lists them. |
| `baselines.py` | Sequential (roll order), round-robin (papers interleaved) and random-shuffle seating. |
| `predictability.py` | Roll-to-seat rank correlation, repeated neighbour pairs across seeds, and front-row bias per department. |
| `benchmark.py` | Runs every method on every scenario and seed, validates each plan, tunes the per-hall time budget, and writes the experiment folder and `models/engine_profile.json`. |
| `plots.py` | The PNG charts saved with each run. |

## Running

From the product root, with the virtual environment active:

```bat
python -m ml.benchmark           :: full run (about 5-10 minutes)
python -m ml.benchmark --quick   :: smoke run (under a minute)
```

Each run creates `experiments/engine-benchmark-<date>/` containing `metrics.json`, `results.csv`, `benchmark.log` and the plots. A full run also rewrites `models/engine_profile.json`, and the product's **Analytics > Engine performance** view reads the run that profile points to.

## Engine interface used here

The scripts call the product engine directly (`backend/app/services/engine`), so the benchmark measures exactly what the product runs:

- `solve(candidates, halls, rules, seed=..., budget=None) -> EngineResult` (`ok`, `placements`, `reasons`, `solve_ms`, `stats`)
- `validate(candidates, halls, placements, rules) -> Scorecard` (`to_dict()` with `hard_ok`, `same_paper_pairs`, `roll_gap_violations`, `accessible_violations`, `capacity_violations`, `same_department_pairs`, `neighbour_pairs`, `halls_used`, `utilisation`, `per_hall`)
- `graph.seat_neighbours(hall, adjacency) -> {seat: [neighbour seats]}`
- Data classes `EngineCandidate`, `EngineHall`, `Placement` and `Rules`, plus `ENGINE_VERSION`.
