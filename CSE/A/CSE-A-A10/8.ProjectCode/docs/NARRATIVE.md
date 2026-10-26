# NARRATIVE - the story every FlowSense document tells (CSE-A-A10)

Read `docs/REPORT_FACTS.md` (numbers) and this file (story, names, contracts) before writing anything. Numbers come from
`scripts/docs/facts.py` (`F.C2`, `F.C3`, `F.SW`, `F.EM`, `F.AB`, `F.PR`, `F.VS`, `F.VY`, `F.VR`, `F.TH`, `F.API`, helpers `F.gm`, `F.derived`) or are typed
exactly as in REPORT_FACTS.md. Never round a number differently in two places. Never write a number that is not in those files.

## 1. One-paragraph story

Cities run fixed-time signals that cannot see queues or ambulances. The base paper (Lamrabet et al., IEEE Access 2026) adds a trained YOLO26m roof-light-bar
detector as a supervisory emergency-priority layer on a GA-SGD optimised controller and validates it in SUMO on one Rabat roundabout. FlowSense, built by the
batch, puts the whole chain in one working web product: a seeded traffic-network simulator (2x2 or 3x3 junctions) with four controllers run on identical demand
(fixed-time, queue-actuated adaptive, a base-paper-style emergency-aware controller, and the project's "advanced" controller that adds PCU-weighted pressure, a
30-second ML queue forecast, inter-junction look-ahead with spill-back avoidance and an emergency green wave), a YOLOv8n vision layer with an HSV light-bar rule
and PCU density estimate, a gradient-boosting queue forecaster, a violation log, and a FastAPI + React console (ports 8310 / 5310). It was measured honestly:
the adaptive family beats fixed-time by about a third, the advanced controller beats plain adaptive control only slightly, pre-emption cuts ambulance delay by
~70-85 % at a small cost to other traffic, the forecaster looks excellent on a random split but fails on an unseen heavily congested run, and the vision layer
works on synthetic scenes but not on real ambulance photos.

## 2. Names and wording (use exactly)

- Product **FlowSense**; project title **AI-Based Smart Traffic Management**; college TKR College of Engineering & Technology (An Autonomous Institution), Department of CSE, batch A10 (CSE-A).
- Controllers (code keys -> display): `fixed` Fixed-time; `adaptive` Adaptive (queue-actuated); `emergency` Emergency-aware adaptive ("base-paper style" - an emulation of the base paper's idea, NOT a re-implementation: no GA-SGD, no trained detector, ground-truth emergency knowledge, one-junction pre-emption with 5 s look-ahead); `advanced` Advanced coordinated AI (FlowSense).
- The simulator is called "the FlowSense simulator"; it is **not SUMO** and **not comparable in absolute terms** with the base paper's SUMO roundabout. Say so wherever the base paper is compared.
- Vision modes: "synthetic scene" (classical contour detector), "YOLOv8n sample photo / upload". The light-bar rule is HSV red+blue cluster. There is no trained light-bar model.
- Violations are "simulated violation events logged with a plate and a confidence drawn from 0.86-0.99" - never "detected by a model".
- Demo login `operator@flowsense.app` / `Flow@1234` (shown on the sign-in page). Backend http://127.0.0.1:8310, frontend http://localhost:5310, started with `run.bat`.
- Student/guide names, roll numbers: see `facts.py`. College principal, HOD, academic year, place, date, guide designation stay as `[PLACEHOLDER]` text.

## 3. Findings that MUST be stated plainly (each at least once in the report, and in the paper / final deck / results doc where relevant)

1. Fixed-time -> adaptive/advanced: average delay -34.8 % (2x2) and -30.5 % (3x3) for the advanced controller; most of that gain comes from adaptivity itself.
2. Advanced vs plain adaptive is only -4.3 % (2x2) / -5.3 % (3x3), within about one standard deviation of the adaptive controller over 5 seeds; at low demand (x0.6) advanced is worse than adaptive (26.4 vs 20.6 s).
3. The base-paper-style emergency controller has a *higher* mean delay than plain adaptive (+6.5 % on 2x2, +2.2 % on 3x3): pre-emption has a price.
4. Ambulance delay: advanced 5.7 s vs fixed 20.1 s (2x2, -71.5 %) and 5.6 s vs 42.4 s (3x3, -86.7 %); vs the base-paper style -4.2 % (2x2) and -24.9 % (3x3). In the emergency-heavy test (one ambulance per ~60 s) pre-emption controllers cut ambulance delay by ~75 % vs fixed/adaptive.
5. Ablation: no ML forecast +3.2 s delay (47.4 vs 44.2 s); no platoon look-ahead +0.7 s; no emergency green wave: ambulance delay 5.7 -> 9.0 s; no pre-emption at all: network delay lowest (42.4 s) but ambulance delay 27.3 s - a real efficiency/safety trade-off.
6. Forecaster: random 75/25 split MAE 1.64 / R2 0.959 (GB) vs persistence 2.57 / 0.896 - but leave-one-simulation-out R2 ~0.04 (mean), GB beats persistence in 5 of 6 held-out runs and fails on the one heavily congested run (14.66 vs 5.49 MAE) because queues beyond the training range cannot be extrapolated by trees (predict also clips to 40). Random Forest is as good as the used Gradient Boosting (MAE 1.609 vs 1.642).
7. Vision: synthetic scenes recall 97.6 %, precision 100 %, ambulance recall 100 % / false alarms 0.6 % - in-domain, optimistic; Gaussian noise sigma 10 -> zero detections; brightness x0.6 -> light-bar recall 0; blur -> 50.8 %. Real photos: YOLOv8n on 293 real dashcam frames: 4-wheeler recall 58.6 % / precision 60.9 %, 2-wheeler recall 8.3 %, 3-wheeler 0 %, all vehicles recall 23.7 % / precision 64.6 %; light-bar rule on 600 real photos: recall 1.3 % (any cluster) and 0.7 % (YOLO box + light bar), false-alarm 0.3 % / 0 %. The base paper's trained detector (P 0.73 / R 0.69 / mAP50 0.73) is the standard that was not reached.
8. Violations are simulated events; emergency vehicles are known to the controllers by ground truth in the simulator; the vision module is not closed-loop with the controllers; inter-junction "communication" is simulated look-ahead on the transit queue, not a network protocol.
9. No database; no real camera stream; no hardware; no SUMO/CARLA; single demo operator; CPU-only (i5-12500, 15.7 GB).
10. Tests: 38 pytest tests passed (24 engine, 14 API), 33 smoke checks passed; not tested: concurrency/load, security penetration, real hardware.
11. (Added after viewing the images) The 4 real ambulance photos the light-bar rule flagged were flagged on red/blue livery stripes, a flag graphic and a star-of-life - not on roof lights - and the single non-ambulance flag was a blue car. So even the 1.3 % / 0.7 % recall overstates what the rule does: it responds to red+blue colour clusters, not to emergency lights. (Endpoints: the API has 20 routes, 4 public + 16 token-guarded, not 18.)

## 4. Fixed diagram files (`docs/diagrams/`, produced by `scripts/docs/make_diagrams.py`; index with captions in `scripts/docs/diagram_index.py`)

01_system_architecture.png - 02_high_level_workflow.png - 03_dfd_level0.png - 04_dfd_level1.png - 05_dfd_level2.png - 06_uml_class.png -
07_sequence_flow.png - 08_use_case.png - 09_er_diagram.png (logical: no database; in-memory entities) - 10_flowchart_control.png (the advanced controller's per-junction
decision) - 11_flowchart_vision.png (frame -> YOLOv8n -> light-bar rule -> PCU density -> green-time recommendation) - 12_model_architecture.png (queue forecaster: 11 features,
GB regressor, RF and persistence baselines, closed-loop use inside `_pressure`).

## 5. Fixed figure files (`docs/figures/`, produced by `scripts/docs/make_figures.py` from the metrics JSON, 150 dpi)

f01_delay_by_controller.png (avg delay, 4 controllers x 2x2/3x3, error bars) - f02_emergency_delay.png (ambulance delay by controller, 2x2/3x3) -
f03_demand_sweep.png (delay vs demand) - f04_ablation.png (delay and ambulance delay per ablation) - f05_forecaster_validation.png (MAE: random split vs leave-one-simulation-out, all models, plus per-fold GB vs persistence) -
f06_forecast_scatter_importance.png (predicted vs actual 30 s queue for the shipped model + feature importance) - f07_vision_synthetic_robustness.png (recall and ambulance recall under noise/dark/blur) -
f08_ambulance_real_confusion.png (real ambulance photos, confusion matrix of the shipped light-bar rule) - f09_base_paper_comparison.png (relative reductions: base paper SUMO vs FlowSense simulator; different testbeds, indicative only) -
f10_api_latency.png - f11_queue_timeseries.png (total queued vehicles over time, 4 controllers, seed 40, 2x2) - f12_real_vision_per_class.png (YOLOv8n precision/recall per class on the 293 real frames) -
f13_real_examples.png (four real photos: traffic frame with detections, a miss, a light-bar hit, a light-bar miss; CC BY 4.0 datasets).

## 6. Screenshots (`docs/screenshots/`, real, 1440x900)

01_landing_dark 02_landing_features_dark 03_landing_light 04_login 05_live_control 06_live_map_and_status 07_benchmark 08_benchmark_charts 09_benchmark_sweep 10_vision_synthetic 11_vision_density 12_vision_yolo 13_prediction 14_prediction_forecast 15_violations 16_violations_log 17_about 18_about_pipeline 19_live_control_light (all `.png`, see REPORT_FACTS section 12 for what each shows).
The benchmark screens (07-09) use the UI defaults (30 min, demand x1.2, 3 seeds, 08:00): fixed 73.0, adaptive 48.5, emergency-aware 51.2, advanced 45.4 s; -38 % vs fixed-time, -11 % vs emergency-aware, emergency delay -73 % (5.1 vs 18.7 s), fuel saved 12.4 L / CO2 28.6 kg. State that the report tables use 5 seeds (mean ± std) and so differ slightly from the 3-seed screen.

## 7. Module contract for the report build (`scripts/docs/`; copied from the A5 kit - the kit modules `kit.py`, `blocks.py`, `pptkit.py`, `word_finalize.py`, `comlock.py` need only small edits)

`build_docs.py` calls these functions; each returns a list of blocks from `blocks.py` (H1/H2/H3/P/B/N/FIG/TAB/PAIR/EQ/CODE) and uses `F.REPORT` to emit a compact version for the full report:
`ch1.blocks()`, `ch2.blocks()`, `ch3_4.blocks()`, `ch5.blocks()`, `ch6.blocks()`, `ch6.methodology_blocks()`, `ch6.application_blocks()`, `ch7.blocks()`, `ch8.blocks()`,
`ch9_10.{chapter9_blocks, chapter10_blocks, novelty_blocks, contribution_blocks, scope_blocks, assumption_blocks, limitation_blocks, not_measured_blocks, walkthrough_blocks, decision_blocks, conclusion_blocks, future_blocks}`,
`appendix.{code_blocks, guide_blocks, screens_blocks}`, `front.{cover, certificate, declaration, acknowledgement, abstract, abbreviations}`, `diagram_index.DIAGRAMS`, `refs.REFS/CITE`.
Chapter headings in the report (H1 text exactly, as in the A5 kit and Project_Report.pdf): `CHAPTER 1: INTRODUCTION`, `CHAPTER 2: LITERATURE SURVEY`, `CHAPTER 3: FEASIBILITY STUDY`, `CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS`, `CHAPTER 5: SYSTEM DESIGN`, `CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION`, `CHAPTER 7: SYSTEM TESTING`, `CHAPTER 8: RESULTS AND OUTPUT SCREENS`, `CHAPTER 9: CONCLUSION`, `CHAPTER 10: FUTURE SCOPE`; then `REFERENCES`, `APPENDIX A: IMPORTANT CODE`, `APPENDIX B: INSTALLATION AND USER GUIDE`, `APPENDIX C: ADDITIONAL SCREENS`.
Target: the full report ~80-95 Word pages (A5 landed at 88 with ~30k words); chapter documents each >= 40 KB (embed at least one figure).

## 8. Project facts for the Methodology / Design text (read the code to confirm before writing)

Files: `smart_traffic/sim.py` (Sim, Vehicle, controllers, `_pressure`, `_decide`, `_emergency_target`, `_scan_upstream`, `feature_matrix`, `summary`, `run_benchmark`), `predictor.py` (QueuePredictor, build_dataset),
`vision.py` (detect_yolo, detect_classical, detect_lightbars, density_report, annotate, render_scene), `backend/{main,service,auth,config}.py`, `frontend/src/pages/*.jsx`, `scripts/{run_experiments,eval_real_vision,measure_api,smoke_test,capture_screens}.py`, `tests/`.
Constants: LINK_TIME 12, CAP 30, SAT 0.5, STARTUP 2, CLEAR 3, FIXED_GREEN 30, MIN_GREEN 15, MAX_GREEN 60 (advanced min 13); PCU car 1 / bike 0.5 / bus 3 / truck 2 / ambulance 1.
Advanced pressure per approach: `w = Σ PCU(queue) + 0.7·max(forecast − queue, 0) + inbound PCU within 8 s + head_wait/12`, times 0.3 if the straight-ahead downstream queue ≥ CAP−4; switch when the current phase has no pressure and the other has some, when `other > 2·current + 4`, or at max green; emergency override: nearest ambulance (in queue, or inbound within 15 s) forces its phase green after ≥ 2 s of the current green.
Density: `PCU / 14` -> LOW <0.35, MEDIUM <0.7, HIGH <1.0, JAMMED; recommended green 12 s with an emergency vehicle else clamp(12 + 3.2·PCU, 15, 60).
Fuel/CO2: idle queue-seconds × 0.6 L/h; 2.31 kg CO2 per litre (assumptions of the simulator).
