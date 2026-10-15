# REPORT_FACTS - HubOptima (CSDS-A-A4)

Single source of truth for every submission document. All figures below were read from this project's own
artefacts on 2026-10-15 (`models/forecast_metrics.json`, `results/*.json`, `data/*.csv`, test runs, measured API calls).
Where `README.md` quotes slightly different numbers (it was written for an earlier training run - e.g. MAE 1,970, R2 0.978,
solve 3.5 s), **the JSON files win**.

## 1. Identity

| Item | Value |
|---|---|
| Project title | Advanced Optimization in E-Commerce Logistics: Combining Matheuristics With Random Forests for Hub Location Efficiency |
| Product name | HubOptima (Python package `hublocator`, v1.0.0) |
| Batch | CSDS-A, Batch A4 - B.Tech CSE (Data Science), Section A |
| Students | CH.ARCHANA 23K91A6745 - A.MEENAKSHI 23K91A6705 - B.ARUN 23K91A6734 - A.SAMPATH 23K91A6712 |
| Guide | name not recorded in the batch files ("GUIDE NAME") - keep placeholder `[GUIDE NAME]` |
| College / HOD / Principal / academic year | not recorded - keep square-bracket placeholders |
| Base paper | K. Danach, A. Rammal, I. Moukadem, H. Harb, A. Nasser, "Advanced Optimization in E-Commerce Logistics: Combining Matheuristics With Random Forests for Hub Location Efficiency," IEEE Access, vol. 13, pp. 55915-55926, 2025, DOI 10.1109/ACCESS.2025.3550560 |
| Ports | API 8104, web 5104 (Flask classic UI 5000) |

Objectives (from `6.OBJECTIVES&PROBLEM STATEMENT.docx`): O1 collect/preprocess data - O2 Random Forest regional demand - O3 hub location
as optimisation with cost/time/capacity - O4 matheuristic solver - O5 re-optimise as demand changes - O6 compare with traditional methods.

## 2. Architecture summary

Predict-then-optimise pipeline, pure Python:

```
regions.csv + demand_history.csv --(data.py: clean, dedupe, interpolate)--> features (forecast.py: 19 features)
 --> RandomForestRegressor (400 trees) --> next-month demand per region
 --> Instance (model.py: distances x1.25 road factor, time, unit cost, fixed cost by tier, capacity)
 --> matheuristic.py (construct -> MIP-priced local search -> kernel search)  |  exact CBC MIP (baseline)
 --> evaluate_solution() KPIs on realised demand --> JSON / UI
 rolling.py re-runs forecast+plan month by month; baselines.py compares methods.
```

| Layer | Technology |
|---|---|
| Core package `hublocator/` | pandas 2.2.1, numpy 1.26.4, scikit-learn 1.4.2 (RandomForestRegressor, KMeans), PuLP 3.3.2 with bundled CBC, joblib 1.3.2 |
| API `backend/main.py` (272 lines) | FastAPI 0.110.0, uvicorn 0.29.0, pydantic; CORS limited to localhost:5104 |
| Classic UI `hublocator/webapp.py` (349 lines) | Flask 3.1.0 (server-rendered, original) |
| Web app `frontend/` | React 18.3.1, Vite 5.4.11, react-router-dom 6.28.0, recharts 2.13.3, framer-motion 11.11.17, gsap 3.12.5, lucide-react 0.460.0 ("Soft Pastel Calm" design, light + dark) |
| Storage | **No database.** CSV (`data/`), joblib model (`models/rf_demand.joblib`, 38.5 MB), JSON results (`results/`). No user accounts / authentication (single local user). |
| Python source | hublocator 1,963 lines incl. run.py/tests.py/backend; frontend src 4,235 lines (jsx/js) |

Modules: `config.py` (31 lines) - `data.py` (177) - `forecast.py` (145) - `model.py` (203) - `matheuristic.py` (167) - `baselines.py` (121) -
`rolling.py` (140) - `viz.py` (139, SVG for Flask) - `webapp.py` (349).

### Hub-location model (as coded in `model.py`)
Capacitated single-allocation p-hub-style location MIP; every region is a candidate hub site (90 candidates).
min  sum_j f_j y_j + sum_ij (r*dist_ij + lambda*time_ij) * d_i * x_ij
s.t. sum_j x_ij = 1; x_ij <= y_j; sum_i d_i x_ij <= C y_j; sum_j y_j <= p; (optional hard SLA) time_ij x_ij <= SLA; binary x,y.
Parameters (`config.DEFAULTS`): p=6, capacity factor 1.25 (C = 1.25 * total demand / p), transport rate INR 0.04/order/km,
fixed hub cost INR 2,500,000/month x tier multiplier (tier 1 = 1.35, tier 2 = 1.0, tier 3 = 0.75), time penalty INR 1.5/order/hour,
truck speed 45 km/h, hub handling 6 h (local delivery 3 h), SLA 48 h (soft by default), MIP time limit 20 s.
Distances: haversine x 1.25 road factor. time_ij = dist/45 + 6 h.
Differences from the base paper's model: single allocation, one capacity level, no unmet-demand penalty variable (instead the soft SLA time penalty and an
evaluation-time fulfilment KPI), no robust/scenario optimisation, no routing.

### Matheuristic (as coded in `matheuristic.py`)
1. Construction: greedy weighted k-medoids (open the hub that most reduces cost, then medoid refinement).
2. Local search (swap / drop / add on the hub set); every candidate move is screened with a cheap capacity-aware greedy bound (tolerance 6 %), promising ones are priced by an exact assignment MIP for the fixed hub set (first improvement; stops at 70 % of the time limit).
3. Kernel search: a restricted full MIP over ~24 promising candidate hubs (kernel) to polish.
Not Variable Neighbourhood Search (the base paper names VNS); the project's local search is swap/drop/add with MIP pricing.

## 3. Dataset (synthetic - state this plainly everywhere)

| Fact | Value |
|---|---|
| Source | **Synthetic**, generated by `hublocator/data.py::generate_dataset(seed=42)`. No public region-level order dataset was available; no real company data. |
| Licence | Generated by the project itself - no third-party licence. City coordinates/populations are approximate public values (30 Indian cities). |
| Regions | 90 = 30 Indian cities + 60 satellite districts (3 per tier-1 city, 2 per tier-2, 1 per tier-3, 45-160 km away). Tier counts by region: tier 1: 8, tier 2: 14, tier 3: 68 (satellites are tier 3). |
| History | 36 months, 2023-01 to 2025-12; 90 x 36 = 3,240 rows |
| Total orders | 48,295,881 (dataset summary shows 48.3 M); per-region-month min 218, max 321,460 |
| Peak month | 2025-10: 2,383,534 orders (festival season); first month 1,002,122; last month 1,593,341 |
| Generating process | population x tier-specific e-commerce penetration / 12, monthly growth 1.0-2.2 %, festival multipliers (Oct 1.35, Nov 1.25, Jan 1.08, Aug 1.10; Feb/Jun x0.93), promotion flag (18 % random, forced Oct/Nov) giving +14 % lift (promo share 31.9 % of rows), Gaussian noise (sd 6 %) |
| Columns | demand_history: region_id, period, year, month, orders, promo, avg_order_value, avg_parcel_weight_kg, return_rate; regions: region_id, city, state, lat, lon, population, tier, parent, penetration |
| Preprocessing | de-duplicate (region, period); numeric coercion; sort; per-region interpolation of gaps; drop NaN; derive year/month. (No gaps/duplicates exist in the generated data - the steps are guards for user-supplied data.) |
| Features (19) | lag_1, lag_2, lag_3, lag_6, lag_12, roll_mean_3, roll_mean_6, roll_std_3, trend_3, month, quarter, festival, promo, promo_prev, population, tier, penetration, avg_order_value, return_rate |
| Split | time-based: train 2023-04 to 2025-06 (2,430 rows); test 2025-07 to 2025-12 (540 rows). No random split, no cross-validation, no hyper-parameter search. |

## 4. Demand forecast (models/forecast_metrics.json, trained_at 2026-09-26T09:43:16Z)

Random Forest: 400 trees, max_depth None, min_samples_leaf 2, max_features 0.6, random_state 42; fit time 0.8 s (12-thread i5-12500).

| Forecaster | MAE | RMSE | MAPE % | R2 |
|---|---|---|---|---|
| Random Forest (proposed) | 1,984.0 | 6,618.9 | 7.67 | 0.9766 |
| Last month's value | 4,151.1 | 12,604.1 | 19.71 | 0.9152 |
| 3-month moving average | 3,785.5 | 11,882.0 | 17.56 | 0.9246 |

Top feature importances: roll_mean_3 0.3788, lag_1 0.2417, population 0.1547, lag_2 0.0761, lag_12 0.0724, lag_3 0.0403, roll_mean_6 0.0219; every other feature <= 0.002 (promo 0.0019, festival 0.0017, month 0.0011).
Per-region error in the last test month (Dec 2025, 90 regions): median absolute error 7.0 %, mean 8.9 %, 8 regions above 20 %, worst 39.9 % (R007 Pune), R008 Ahmedabad 39.3 %, R005 Chennai 39.0 %.
Network-level forecast errors (rolling.json): Jul 3.06 %, Aug 3.48 %, Sep 5.96 %, **Oct 13.1 % (under-forecast of the festival peak)**, Nov 1.49 %, Dec 10.22 % (over-forecast).
Next-month forecast (Jan 2026): 1,788,825 orders.

## 5. Method comparison - planned for Oct 2025 (results/comparison.json), p = 6, scored on realised demand

Forecast demand 2,067,718 vs realised 2,383,534 (forecast 13.2 % low). SLA 48 h soft, capacity factor 1.25.

| Method | Hubs | Cost INR M | vs proposed | Avg delivery h | Max h | Fulfilment % | Overloaded hubs | Solve s |
|---|---|---|---|---|---|---|---|---|
| RF forecast + matheuristic (proposed) | Mumbai, Delhi, Kolkata, Hyderabad-W2, Bengaluru-SE, Ahmedabad-SE | 62.158 | 0.00 % | 8.56 | 37.71 | 92.28 | 3 | 4.89 |
| RF forecast + exact MIP (CBC, 30 s limit) | same six hubs | 62.158 | 0.00 % | 8.56 | 37.71 | 92.28 | 3 | 7.99 (Optimal) |
| RF forecast + greedy heuristic | ... Nagpur-N instead of Ahmedabad-SE | 69.310 | +11.51 % | 9.47 | 37.08 | 89.27 | 3 | 0.01 |
| RF forecast + k-means | Mumbai, Delhi, Warangal, Bengaluru-SE, Kolkata-W, Ahmedabad-SE | 64.407 | +3.62 % | 9.19 | 37.71 | 91.81 | 3 | 0.11 |
| Largest-markets rule | Hyderabad, Mumbai, Delhi, Bengaluru, Chennai, Kolkata | 72.151 | +16.08 % | 8.96 | 49.99 | 91.13 | 3 | 0.00 |
| Historical-average demand + matheuristic (no forecast) | Delhi, Hyderabad-W2, Mumbai-S, Bengaluru-SE, Kolkata-W, Ahmedabad-SE | 67.172 | +8.07 % | 9.91 | 34.05 | 66.04 | 5 | 3.60 |

Proposed cost split (INR): fixed 15,750,000 - transport 15,818,196 - time penalty 30,589,338; INR 26.08 per order; avg distance 165.9 km.
Utilisation on realised demand: Mumbai 110 %, Delhi 122 %, Kolkata 80 %, Hyderabad-W2 59 %, Bengaluru-SE 111 %, Ahmedabad-SE 71 % - three hubs overloaded because the forecast under-called the peak.
"Fulfilment" and "SLA reliability" are model KPIs: orders a hub can process within capacity (and, for reliability, assigned within 48 h) divided by realised demand. They are **simulated**, not observed deliveries.
Observation to state honestly: on this instance the matheuristic and the exact MIP found the **same** solution; the matheuristic's advantage shows only at larger sizes. (Reliability = fulfilment except for the largest-markets rule, 90.69 %.)

## 6. Rolling re-optimisation (results/rolling.json) - Jul-Dec 2025, p = 6

| Month | Forecast | Realised | Err % | Adaptive fulfil % | Static fulfil % | Adaptive cost M | Static cost M | Hub change |
|---|---|---|---|---|---|---|---|---|
| 2025-07 | 1,409,247 | 1,453,765 | 3.06 | 100.00 | 95.29 | 45.829 | 46.480 | - |
| 2025-08 | 1,569,092 | 1,625,632 | 3.48 | 99.44 | 88.46 | 48.647 | 50.165 | - |
| 2025-09 | 1,430,570 | 1,521,247 | 5.96 | 99.04 | 93.26 | 46.487 | 47.752 | - |
| 2025-10 | 2,071,229 | 2,383,534 | 13.10 | 92.43 | 64.91 | 62.155 | 67.438 | opened Kolkata, closed Kolkata-W |
| 2025-11 | 2,145,198 | 2,177,565 | 1.49 | 98.71 | 70.75 | 58.789 | 63.096 | - |
| 2025-12 | 1,756,241 | 1,593,341 | 10.22 | 100.00 | 89.53 | 46.492 | 49.343 | - |

Averages: adaptive fulfilment 98.27 % vs static 83.70 % (+14.6 pts); avg cost INR 51.40 M vs 54.05 M (-4.9 %); avg delivery 8.93 h vs 9.98 h; one hub opening across the horizon.
Static plan hubs: Delhi, Hyderabad-W2, Mumbai-S, Bengaluru-SE, Kolkata-W, Ahmedabad-SE. Matheuristic solve times per month 2.69-4.93 s.

## 7. Scalability (results/scalability.json) - exact MIP limited to 40-45 s

| Nodes | Binary vars | Matheuristic s | Exact MIP s | Exact status | Matheuristic gap vs exact |
|---|---|---|---|---|---|
| 90 | 8,190 | 3.13 | 12.74 | Optimal | 0.00 % |
| 180 | 32,580 | 8.31 | 42.94 | Optimal | -0.05 % (matheuristic slightly better - exact solved to CBC's default tolerance) |
| 270 | 73,170 | 30.53 | 67.14 | Not Solved (limit hit; best bound reported 53.43 M) | +3.67 % vs the exact incumbent |

At 270 nodes the matheuristic is **3.7 % worse** than the (not-proven-optimal) exact incumbent; that is an honest cost of the speed-up. Base paper claims 50-500 nodes; this project tested up to 270 nodes only.

## 8. Testing (measured 2026-10-15)

- `python tests.py`: 4 tests (data, forecast, optimisation, Flask web app + API) - **all passed**, 32.7 s wall.
- `python scripts/smoke_test.py` (FastAPI layer, in-process): **18 checks, all ok**, 20.9 s. Covers health, summary, regions, options, forecast, metrics, compare, scalability, rolling, optimise (matheuristic, allocation covers every region, next month, exact MIP, hard-SLA edge case, validation of n_hubs=0, unknown month), job status.
- Assertions worth quoting: matheuristic within 2 % of exact on a p=5 next-month instance; capacity respected on the plan (fulfilment >= 0.99, 0 overloaded hubs); hard SLA 30 h forces every assignment <= 30 h; forecast of Oct 2025 within 30 % on the peak.
- Hard-SLA edge case (1 hub, 5 h hard SLA, Dec 2025 - deliberately infeasible-ish) is answered cleanly by the API; the smoke test reported a plan with reliability 0.1957 (not an error).
- Browser walkthrough: Playwright (Chrome) opened all 7 routes + not-found, ran 3 planning runs through the UI, 22 screenshots captured (`scripts/capture_screens.py`).
- Not done: no JS/unit tests for the frontend, no load testing, no authentication/security testing beyond input validation, no user-acceptance study, no real-data validation.

## 9. Measured performance (this machine, localhost, median of n calls)

Machine: Intel Core i5-12500 (6 cores / 12 threads), 15.7 GB RAM, Windows 11 Pro, Python 3.11.9, Node v24.19.0, no GPU used.

| Call | Median | Range | n |
|---|---|---|---|
| GET /api/health | 10 ms | 2-27 | 20 |
| GET /api/summary | 30 ms | 4-37 | 20 |
| GET /api/regions | 16 ms | 2-32 | 20 |
| GET /api/forecast (next month, 90 regions) | 264 ms | 200-343 | 10 |
| GET /api/forecast/metrics | 4 ms | 2-24 | 10 |
| GET /api/compare | 11 ms | 8-35 | 10 |
| GET /api/rolling | 3 ms | 2-14 | 10 |
| GET /api/scalability | 2 ms | 1-30 | 10 |
| POST /api/optimize matheuristic, Oct 2025, p=6 | 12.2 s | 9.2-13.4 | 5 |
| POST /api/optimize exact MIP, Oct 2025, p=6 | 15.3 s | 13.4-15.7 | 3 |
| POST /api/optimize matheuristic, next month, p=6 | 10.7 s | 9.6-13.2 | 5 |
| POST /api/optimize matheuristic, Dec 2025, p=4 | 3.4 s | 3.2-4.1 | 5 |

End-to-end `/api/optimize` includes forecasting, instance build and evaluation, so it is slower than the solver-only seconds in comparison.json (4.89 s). Solver-only time in the UI was 9.23 s (matheuristic) and 9.29 s (exact) for the same Oct-2025 plan on a busy machine - **at 90 nodes the two are comparable**; run-to-run timing varies by several seconds (CBC, shared CPU).
Forecaster training: 0.8 s fit. Retrain endpoint included in the UI.

## 10. Endpoints (FastAPI, port 8104; Flask classic UI adds /, /forecast, /optimize, /compare, /rolling pages on port 5000)

| Method | Path | Purpose |
|---|---|---|
| GET | /api/health | status, version, solver, forecaster trained |
| GET | /api/summary | dataset + forecaster + comparison + rolling digest |
| GET | /api/regions | the 90 regions with average orders |
| GET | /api/options | planning months, defaults, solver availability |
| GET | /api/forecast | next-month forecast per region + metrics |
| GET | /api/forecast/metrics | full forecaster metrics, importance, last-month detail |
| GET | /api/compare | saved method comparison |
| GET | /api/scalability | saved scalability runs |
| GET | /api/rolling | saved rolling-horizon results |
| GET | /api/jobs | status of background jobs (compare, rolling, train) |
| POST | /api/train | retrain the Random Forest (synchronous) |
| POST | /api/optimize | plan hubs (matheuristic or exact) - validated body (p 1-20, capacity >= 1, SLA > 0, time limit 2-300 s, ...) |
| POST | /api/compare/run | background comparison or scalability benchmark |
| POST | /api/rolling/run | background rolling-horizon run (2-12 months) |

Error handling: pydantic validation (422), unknown month 400, job already running 409, infeasible plan returns `{"error": ...}`, numpy values cleaned (NaN/inf -> null). Background jobs use a lock + thread.

## 11. Screens (docs/screenshots/, 1440x900, real data, light theme unless noted)

01_landing, 02_landing_pipeline, 03_dashboard, 04_dashboard_full, 05_forecast, 06_forecast_full, 07_regions, 08_plan_parameters, 09_plan_kpis (Oct 2025, matheuristic, p=6: INR 62.2 M, 8.6 h, 92.3 %), 10_plan_full, 11_plan_map, 12_plan_searchlog (construction INR 61.5 M -> swap 59.1 M -> swap 57.7 M planned), 13_plan_next_month (Jan 2026 forecast), 14_plan_exact (exact MIP, Oct 2025, "Optimal"), 15_compare, 16_compare_full, 17_compare_scalability, 18_compare_scalability_full, 19_rolling, 20_rolling_full, 21_dashboard_dark, 22_not_found. 22 PNG files.
The compare, scalability and rolling screens display the saved JSON results above (long jobs were not re-run, so no numbers changed).

## 12. Honest gaps (to appear as stated gaps in the documents)

1. Dataset is synthetic; no real logistics data; absolute rupee figures, delivery hours and fulfilment are model outputs, not field measurements.
2. Base paper's real-data results (92.3 % delivery-time compliance, 97.6 % fulfilment, robustness 0.87, +7.8 % / +9.4 % / +16 %, 15-20 % cost reduction, networks to 500 nodes) are **not reproduced** - datasets and metric definitions differ; the comparison is qualitative.
3. Network robustness (base paper's third KPI) and scenario/robust optimisation were not implemented or measured.
4. No cross-validation or hyper-parameter tuning for the Random Forest; single time-based hold-out of 6 months.
5. Forecast under-called the Oct 2025 festival peak by 13 %, leaving 3 of 6 hubs overloaded (92.3 % fulfilment) - the plan was not robust to that error.
6. At 90 nodes matheuristic = exact solution and solve times are comparable; at 270 nodes the matheuristic is 3.67 % above the exact incumbent.
7. Single allocation, single capacity level, no routing, no multi-period capacity expansion, no hub-disruption model.
8. No database, authentication or multi-user support; no deployment beyond localhost; no frontend automated tests.
9. comparison.json and rolling.json came from separate runs; their October forecast totals differ by 0.17 % (2,067,718 vs 2,071,229).
10. Guide name, college, HOD, principal and academic year are not in the batch files -> placeholders.
