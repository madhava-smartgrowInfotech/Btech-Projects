"""Chapter 5: System Design for FlowSense.

build_docs.doc12 renders blocks()[1:], so the first element must be the chapter H1.
"""

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB, PAIR
from .refs import CITE as R


def blocks():
    return _report() if F.REPORT else _full()


def _report():
    """Compact variant for the full report: every required diagram except the vision flowchart and the forecaster architecture
    (both are in the Block Diagrams document and described in Chapter 6), shorter prose, fewer tables."""
    a, c3 = F.API_PORT, F.WEB_PORT
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter describes the architecture and workflow, the data flow, the UML and data design, the core algorithms, the module and API design and the user interface of FlowSense. "
          "The diagrams were drawn from the code (`smart_traffic/` and `backend/`); the complete set, with explanations, is also in the Block Diagrams document."),

        H2("5.1 Design Goals and Architecture"),
        P("Five goals shaped the design: **like-for-like comparison** (every controller faces the same seeded vehicles, ambulances and red-light runners); **one pipeline rather than parts**, because the surveyed systems "
          "either detect vehicles or adapt timing but not both [" + str(R['s_signaliq']) + "], [" + str(R['s_cisct']) + "]; **measurable behaviour**, re-runnable from `scripts/run_experiments.py`; "
          "**no GPU or simulator licence**, hence a pure-Python simulator instead of SUMO [" + str(R['sumo']) + "]; and **a console an operator can read**."),
        FIG(F.diag("01_system_architecture.png"), "Four-tier architecture of FlowSense: presentation (React console, legacy Streamlit app), FastAPI application with 20 routes, service layer and traffic engine, and in-memory state and files (no database).", 5.4),
        P(f"The React 19 console on port {c3} calls the FastAPI application on 127.0.0.1:{a} through a Vite proxy. `backend/service.py` wraps the engine and holds the shared state: one live simulation, one background-trained queue forecaster, a benchmark cache and the landing-page preview. "
          "The engine in `smart_traffic/` has three modules (simulator with four controllers, forecaster, vision layer) and contains no web code. Nothing is stored except the YOLOv8 weights and the experiment outputs; there is no database."),

        H2("5.2 High-Level Workflow"),
        FIG(F.diag("02_high_level_workflow.png"), "High-level workflow: Lane A is the control loop repeated every simulated second; Lane B is the vision layer for one camera frame (a demo path, not wired into the controllers).", 5.4),
        P("**Lane A** runs once per simulated second: *sense* (Poisson arrivals fill the queues, measured in passenger-car units), *forecast* (eleven features per approach give the queue 30 s ahead, refreshed every 10 s), "
          "*decide* (pressure score and ambulance target per junction), *act* (keep or switch phase after a 3 s clearance), *coordinate* (vehicles ride a 12 s link and appear in the next junction's inbound scan; an ambulance within 15 s makes it switch early, a green wave) and *report* (KPIs, tables, log, map). "
          "**Lane B** passes one frame through YOLOv8n or the contour detector, the light-bar rule and the density step; it informs the operator but the controllers do not call it."),

        H2("5.3 Data Flow Diagrams"),
        H3("5.3.1 Level 0: context"),
        FIG(F.diag("03_dfd_level0.png"), "Data flow diagram, level 0: four external entities exchange data with the FlowSense platform.", 4.8),
        P("The platform is one process with four external entities: the **operator** (login, configuration, commands; receives KPIs, map, forecasts and the violation log), the **image source** (JPG or PNG up to 12 MB; receives detections, density and the light-bar flag), "
          "the **evaluator or developer** (runs the experiment, test and screenshot scripts) and **simulated demand** (seeded Poisson arrivals, drawn as external because a deployment would use real cameras)."),
        H3("5.3.2 Level 1: seven processes"),
        FIG(F.diag("04_dfd_level1.png"), "Data flow diagram, level 1: seven processes and five data stores.", 5.2),
        P("Level 1 has seven processes: **1.0** authenticate and validate, **2.0** simulate traffic (store D1), **3.0** control signals, **4.0** forecast queues (model store D2), **5.0** analyse a vision frame (YOLOv8n weights D5), "
          "**6.0** benchmark controllers (cache D3, with its own simulations) and **7.0** report KPIs, map and log. Events go to D4. All stores except the weights file are memory structures; the landing preview is a second simulation so it never disturbs an operator's session."),
        H3("5.3.3 Level 2: one simulated second"),
        FIG(F.diag("05_dfd_level2.png"), "Data flow diagram, level 2: process 3.0 (control signals) expanded into six sub-processes for one junction and one second.", 5.2),
        P("Process 3.0 expands into **3.1** scan upstream (inbound PCU within 8 s, ambulances within 15 s), **3.2** refresh forecast (advanced controller, every 10 s from t = 30), **3.3** find the ambulance target, **3.4** score pressure, "
          "**3.5** decide the phase (minimum and maximum green, pressure rule or ambulance target) and **3.6** switch and discharge, updating D1 and writing events to D4."),

        H2("5.4 UML Design"),
        H3("5.4.1 Class diagram"),
        FIG(F.diag("06_uml_class.png"), "UML class diagram: the FastAPI application, the service classes, the simulator, the forecaster and the vision functions.", 5.2),
        TAB("Principal classes and their roles.",
            ["Class", "File", "Role"],
            [["`Sim`, `Vehicle`", "smart_traffic/sim.py", "The network (queues, phases, transit, four controllers, KPIs, logs) and one vehicle"],
             ["`QueuePredictor`", "smart_traffic/predictor.py", "Gradient-boosted regressor with Random Forest and persistence baselines"],
             ["`Live`, `Preview`, `Predictor`", "backend/service.py", "Shared live simulation, landing-page simulation, background training wrapper"],
             ["`ApiError`", "backend/service.py", "Exception carrying status, message and hint, rendered as JSON"]],
            widths=[1.5, 1.8, 3.1], align=["l", "l", "l"], size=9.5),
        P("`Sim` is deliberately large because the four controllers differ only in `_signals` and `_decide`; arrivals, transit, discharge and recording are shared, which guarantees identical demand. The vision layer is a module of functions."),
        H3("5.4.2 Sequence diagram"),
        FIG(F.diag("07_sequence_flow.png"), "Sequence diagram of the main flow: (A) skip five minutes on the Live page; (B) send an ambulance and step again.", 4.6),
        P("In scenario A the console sends `POST /api/live/step {seconds: 300}` with the bearer token; `current_user` checks the HS256 signature and expiry, `Live.step` runs under the service lock and calls `Sim.run(300)`, "
          "and the service returns a snapshot (KPIs, map, queue series, junction table). In scenario B `Live.ambulance()` creates an ambulance at a random entry road; the next step switches the affected junctions, whereas fixed-time and adaptive controllers show an \"ignored\" banner."),
        H3("5.4.3 Use-case diagram"),
        FIG(F.diag("08_use_case.png"), "Use-case diagram with the operator, the visitor and the evaluator or developer.", 4.4),
        P("The **operator** signs in with the demo account, configures and runs the simulation, sends an ambulance, runs the benchmark and sweep, analyses images, views forecasts and reviews violations. The **visitor** only watches the public landing preview; "
          "the **evaluator or developer** runs the scripts. There is a single operator role: the demo sign-in is a gate, not a role system."),

        H2("5.5 Data Design"),
        FIG(F.diag("09_er_diagram.png"), "Logical entity-relationship diagram: FlowSense keeps its entities in memory; there is no database.", 4.8),
        P("FlowSense stores no tables, so the diagram is logical. One NETWORK has n = rows x columns JUNCTIONs (1 : n), each with four APPROACHes holding a queue of VEHICLEs; a vehicle may raise at most one VIOLATION or finish as an EMERGENCY_RUN; "
          "the FORECASTER is shared with the BENCHMARK_CACHE and the SESSION_TOKEN is stateless. There are no foreign keys; relations are Python references inside one process."),
        TAB("In-memory entities.",
            ["Entity", "Key attributes", "Lifetime"],
            [["Network (`Sim`)", "rows, columns, controller, demand multiplier, seed, start hour, clock", "Until reset or restart"],
             ["Junction / approach", "phase (0 or 1), timer, clearance counter; approach queue, forecast, entry-road flag", "Per simulation"],
             ["Vehicle", "id, type, arrival time, wait, emergency and red-runner flags, plate", "Until it leaves"],
             ["Violation / emergency record", "time, junction, approach, kind, plate, confidence 0.86-0.99; delay and travel time", "Per simulation"],
             ["Forecaster, benchmark result", "GB model, metrics, importance; per-controller summaries", "Until restart (retrained in about 6 s)"],
             ["Token", "subject, name, expiry (12 h), HS256 signature", "Client side"]],
            widths=[1.6, 3.5, 1.3], align=["l", "l", "l"], size=9.5),
        P("Keeping state in memory was a choice: runs are seeded and cheap to regenerate (0.17 to 0.52 s per 30 simulated minutes). The cost is that nothing survives a restart and one shared live simulation serves every browser, acceptable for a single-operator demonstration only."),

        H2("5.6 Core Algorithms"),
        FIG(F.diag("10_flowchart_control.png"), "Flowchart of the advanced controller's per-junction decision, evaluated every simulated second.", 4.4),
        P("While a clearance interval runs nothing is decided. Otherwise the controller checks for an emergency target (the nearest ambulance among queue heads and inbound vehicles within 15 s); if its phase is not green and the current green is at least 2 s old, it switches. "
          "Otherwise it compares pressures: the PCU-weighted queue, plus 0.7 times the forecast excess, plus the PCU arriving within 8 s, plus the head wait divided by 12, times 0.3 when the straight-ahead receiving queue is nearly full. "
          "A green lasts 13 to 60 s; the controller switches when the green phase has no pressure and the other has some, or when the other pressure exceeds twice the current plus 4."),
        P("The other controllers simplify this loop: *fixed* switches every 30 s; *adaptive* uses queue-only pressure and a 15 to 60 s green; *emergency* is adaptive plus pre-emption at the junction holding an ambulance or within 5 s of it. "
          "It emulates the base paper's idea [" + str(R['base']) + "] but is not a re-implementation, because the simulator knows which vehicles are ambulances and models no detector."),
        P("The vision pipeline runs YOLOv8n [" + str(R['ultralytics']) + "] on the COCO vehicle classes [" + str(R['coco']) + "], relabels a vehicle as `ambulance` when an HSV red-and-blue light-bar cluster lies in its upper box, converts counts to passenger-car units, "
          "divides by a capacity of 14 PCU for a LOW to JAMMED level and recommends a green time (Chapter 6). The forecaster is a scikit-learn GradientBoostingRegressor [" + str(R['gbm']) + "], [" + str(R['sklearn']) + f"] of 160 trees, depth 4, "
          f"trained on {F.PR['n_samples']:,} snapshots from six simulated runs, compared with a Random Forest [" + str(R['rf']) + "] and a persistence baseline; the controller calls it every 10 s and clips its output to 0 to 40 vehicles."),
        P(f"The simulator's cost is linear in junctions and vehicles: 1,800 simulated seconds take {F.TH['2x2/fixed']['wall_s']:.2f} s (2 x 2, fixed-time) to {F.TH['3x3/advanced']['wall_s']:.2f} s (3 x 3, advanced), "
          f"{F.TH['3x3/advanced']['speedup']:,.0f} to {F.TH['2x2/fixed']['speedup']:,.0f} times faster than real time. Each second runs five steps in order: arrivals, transit arrivals, signals, discharge and record (`Sim.step`)."),

        H2("5.7 Module Design"),
        TAB("Modules, responsibilities and size.",
            ["Module", "Lines", "Responsibility"],
            [["`smart_traffic/sim.py`", "415", "Simulator, demand profile, four controllers, features, KPIs, benchmark helper"],
             ["`smart_traffic/predictor.py`", "59", "Dataset builder and the gradient-boosted queue forecaster with baselines"],
             ["`smart_traffic/vision.py`", "201", "YOLOv8 wrapper, light-bar rule, classical detector, density report, synthetic scene"],
             ["`backend/main.py`, `service.py`", "210 + 437", "Routes, input models, error handlers, authentication; Live, Preview and Predictor classes, payloads"],
             ["`backend/auth.py`, `config.py`", "55 + 32", "Stdlib HS256 token, credential check, `.env` settings"],
             ["`frontend/src/pages/*.jsx`", "8 pages", "Landing, Login, Live, Benchmark, Vision, Prediction, Violations, About"],
             ["`tests/`, `scripts/`, `app.py`", "-", "38 pytest tests (24 engine, 14 API); experiment, test and screenshot scripts; original Streamlit app (546 lines, unchanged)"]],
            widths=[2.2, 0.8, 3.4], align=["l", "c", "l"], size=9.5),
        P("Dependencies point strictly downward: pages call `/api`, `main.py` calls `service.py`, `service.py` calls `smart_traffic`, and no engine module imports FastAPI, so the 24 engine tests run without a server."),

        H2("5.8 API Design"),
        P("The API has twenty endpoints: four public (health, login, demo account, landing pulse) and sixteen that need a bearer token. Bodies are JSON except the multipart image upload, and errors always have the shape `{detail: {message, hint}}`. Chapter 6 lists every endpoint."),

        H2("5.9 User Interface Design"),
        P("The console follows a control-room metaphor: dark theme with a light option, monospaced readings, keyboard navigation (G then C, B, V, P, R, A) and a command palette on `/`. The sign-in page shows the demo account. "
          "Eight screens (landing, sign-in, live control, benchmark, vision, prediction, violations, about) load real data; API errors are shown with their hint and a model still training is shown as a state. The layout works from 360 px to 1440 px and honours reduced motion."),
        PAIR([(F.shot("06_live_map_and_status.png"), "Live control: road map, queue chart and junction table."), (F.shot("07_benchmark.png"), "Benchmark screen with KPI tiles and charts.")], 2.9),

        H2("5.10 Traceability to the Project Objectives"),
        TAB("Objectives, design elements and what was delivered.",
            ["Objective", "Design element", "Delivered"],
            [["1. Detect and count vehicles with YOLO", "`detect_yolo`, `detect_classical`; Vision screen", "Single frames and uploads only; stock COCO weights; no live video"],
             ["2. Estimate density per approach", "`density_report` (PCU / 14); simulator queues", "Per image and per simulated approach; not wired from camera to simulator"],
             ["3. Adaptive timing in proportion to demand", "`_pressure`, `_decide`", "Yes, in simulation"],
             ["4. Emergency priority", "`_emergency_target`, upstream scan; light-bar rule", "Yes with ground-truth ambulances; image rule not closed-loop"],
             ["5. Coordination between junctions", "Transit look-ahead, spill-back damping, green wave", "Yes, as simulated look-ahead; not a network protocol"],
             ["6. Evaluate accuracy, waiting time, clearance", "`run_experiments.py`, `eval_real_vision.py`, benchmark screen", "Yes; see Chapter 8"]],
            widths=[2.1, 2.5, 1.8], align=["l", "l", "l"], size=9.5),

        H2("5.11 Design Trade-offs"),
        B("**Own simulator instead of SUMO:** portable, fast and reproducible, but its assumptions are the project's own, so absolute numbers cannot be compared with the base paper.",
          "**Ground-truth emergency knowledge:** isolates control from detection, at the price of not testing detection inside the loop.",
          "**Pretrained detector, no training:** no dataset was available, so real-image accuracy is modest (Chapter 8).",
          "**In-memory state:** enough for a demonstration; unsuitable for several operators or restarts.",
          "**Forecast as a pressure term:** a poor forecast can only bias the decision slightly, consistent with the ablation (removing it costs about 3 s of delay)."),
    ]


def _full():
    a, c3 = F.API_PORT, F.WEB_PORT
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter describes how FlowSense is built: the architecture and workflow, the data flow, the class and sequence design, the data design, the three core algorithms, "
          "the module and API design and the user interface. Every diagram was drawn from the code (`smart_traffic/sim.py`, `predictor.py`, `vision.py` and the `backend/` package) "
          "and is reproduced with an explanation; the full set is also collected in the Block Diagrams document."),

        H2("5.1 Design Goals and Architecture"),
        P("Five goals shaped the design. First, **like-for-like comparison**: every controller must face exactly the same vehicles, the same ambulances and the same red-light runners, "
          "otherwise a difference in delay could come from luck rather than from the controller. This is why the simulator draws demand from a seeded random generator that the controllers never touch. "
          "Second, **one pipeline rather than parts**: the literature survey found systems that either detect vehicles or adapt signal timing but not both [" + str(R['s_signaliq']) + "], [" + str(R['s_cisct']) + "], "
          "so FlowSense keeps vision, forecasting, control, emergency priority and violation logging in one code base. Third, **measurable behaviour**: every claim is checked by an experiment that can be re-run from `scripts/run_experiments.py`. "
          "Fourth, **runnable on a laptop without a GPU or a traffic simulator licence**, which led to a pure-Python simulator instead of SUMO [" + str(R['sumo']) + "]. "
          "Fifth, **a console that an operator can read**: live map, benchmark, vision, prediction and violation screens, each driven by the real engine."),
        FIG(F.diag("01_system_architecture.png"), "Four-tier architecture of FlowSense: presentation (React console, axios client, legacy Streamlit app), FastAPI application with 20 routes, service layer and traffic engine, and in-memory state and files (no database).", 5.4),
        P(f"The presentation tier is a React 19 and Vite console on port {c3} that calls the API through a Vite proxy. The application tier is FastAPI on 127.0.0.1:{a} with four route groups: public routes "
          "(health, login, demo account, landing-page pulse), the live-control routes, the benchmark and sweep routes, and the vision, prediction and violation routes. A service layer in `backend/service.py` "
          "wraps the engine and holds the shared state: one live simulation, one background-trained queue forecaster, a benchmark cache and the landing-page preview simulation. "
          "The engine itself, in `smart_traffic/`, has three modules: the simulator and its four controllers, the forecaster, and the vision layer. Nothing is stored on disk except model weights for YOLOv8 (`yolov8n.pt`) "
          "and the experiment outputs; there is no database, so everything held in memory is lost when the API restarts."),
        P("The original Streamlit application (`app.py`) was kept unchanged beside the new web console. Both call the same engine functions, which is why the engine contains no web code and the service layer contains no traffic logic."),

        H2("5.2 High-Level Workflow"),
        FIG(F.diag("02_high_level_workflow.png"), "High-level workflow: Lane A is the closed control loop repeated every simulated second; Lane B is the vision layer for one camera frame (a demo path, not wired into the controllers).", 5.6),
        P("The workflow has two lanes. **Lane A** is the control loop, run once per simulated second in six steps. *Sense*: Poisson arrivals fill the approach queues, measured in passenger-car units. *Forecast*: eleven features per approach go into the gradient-boosted model, "
          "which predicts the queue 30 seconds ahead and is refreshed every 10 seconds. *Decide*: each junction computes its pressure score (queue, forecast excess, inbound platoon, fairness) and looks for an ambulance target. "
          "*Act*: the junction keeps or switches its phase, with a 3-second clearance before the new green. *Coordinate*: vehicles released by one junction ride a 12-second link and appear in the next junction's inbound scan, "
          "and an ambulance within 15 seconds of a junction makes it switch ahead of time, which produces a green wave. *Report*: the KPIs, benchmark tables, violation log and map are served to the console. "
          "The new queues, phases and in-flight vehicles are the next second's input."),
        P("**Lane B** is the vision layer for one camera frame. The frame (an upload, the bundled photograph or a synthetic overhead scene) goes to a detector (YOLOv8n or the contour detector), the light-bar rule relabels a vehicle box as an ambulance, "
          "the density step turns counts into passenger-car units, a level and a green-time hint, and the annotated image and numbers are returned as JSON. This lane informs the operator on the Vision screen; the simulator's controllers do not call it, "
          "and that distinction matters when reading the results."),

        H2("5.3 Data Flow Diagrams"),
        H3("5.3.1 Level 0: context"),
        FIG(F.diag("03_dfd_level0.png"), "Data flow diagram, level 0: four external entities exchange data with the FlowSense platform.", 5.0),
        P("At level 0 the platform is a single process with four external entities. The **operator** sends the login, the network configuration (grid, controller, demand, emergency toggle, ML toggle) and commands (step, ambulance, benchmark) and receives live KPIs, the map, queues, forecasts and the violation log. "
          "The **image source** (a camera frame or an upload of up to 12 MB) sends a JPG or PNG with a confidence threshold and receives detections, the PCU density and the light-bar flag. "
          "The **evaluator or developer** supplies `.env` settings and runs the experiment, test and screenshot scripts, receiving `metrics.json` files, test results and screenshots. "
          "**Simulated demand** (seeded Poisson arrivals and ambulance events) is drawn as an external entity although it is generated inside the platform, because a deployment would replace it with real cameras."),
        H3("5.3.2 Level 1: seven processes"),
        FIG(F.diag("04_dfd_level1.png"), "Data flow diagram, level 1: seven processes and five data stores.", 5.6),
        P("Level 1 divides the platform into seven processes. **1.0 Authenticate and validate** checks credentials and tokens against the `.env` settings and validates the requests it passes on. **2.0 Simulate traffic** advances the network and writes its state to store D1 (live and preview simulation state: queues, phases, transit). "
          "**3.0 Control signals** reads the queues and the forecast and writes events (violations, emergencies) to D4. **4.0 Forecast queues** reads queues, lags and inflow from D1, fits and reads the model in D2 and returns a 30-second forecast to 3.0. "
          "**5.0 Analyse vision frame** loads the YOLOv8n weights (D5) and returns detections, density and the light-bar flag. **6.0 Benchmark controllers** builds its own simulations with the model from D2 and stores summaries in D3, the benchmark cache with the last benchmark's violation counts; it never touches D1. "
          "**7.0 Report KPIs, map and log** reads D1 and D4 and returns the display to the operator. The public landing preview is a second simulation held in the same store as D1 so that it never disturbs an operator's session. All five stores except the weights file are memory structures."),
        H3("5.3.3 Level 2: one simulated second"),
        FIG(F.diag("05_dfd_level2.png"), "Data flow diagram, level 2: process 3.0 (control signals) expanded into six sub-processes for one junction and one second.", 5.6),
        P("Level 2 expands the control process for one junction in one second. **3.1 Scan upstream** reads the transit queue and produces the inbound PCU within 8 seconds and the ambulances inbound within 15. **3.2 Refresh forecast** (advanced controller only, every 10 seconds from t = 30) obtains the model's prediction from D2. "
          "**3.3 Find ambulance target** combines the queued ambulances in D1 with the inbound ones to name the phase of the nearest ambulance. **3.4 Score pressure** combines queue PCU, forecast excess, inbound PCU and head wait for the current and the other phase. "
          "**3.5 Decide phase** applies the minimum-green, maximum-green and pressure rules, or the ambulance target, and outputs switch or hold. **3.6 Switch and discharge** updates queues, phase and transit in D1 and writes events to D4. "
          "The five steps of the whole simulated second are tabulated in Section 5.6.4."),

        H2("5.4 UML Design"),
        H3("5.4.1 Class diagram"),
        FIG(F.diag("06_uml_class.png"), "UML class diagram: the FastAPI application, the service classes, the simulator, the forecaster and the vision functions.", 5.6),
        TAB("Principal classes and their roles.",
            ["Class", "File", "Role"],
            [["`Sim`", "smart_traffic/sim.py", "The network: queues, phases, timers, transit list, controllers, KPIs, violation and emergency logs; `step`, `run`, `feature_matrix`, `summary`"],
             ["`Vehicle`", "smart_traffic/sim.py", "One vehicle: id, type, arrival time, accumulated wait, emergency flag, red-runner flag, route draws, plate"],
             ["`QueuePredictor`", "smart_traffic/predictor.py", "Gradient-boosted regressor with Random Forest and persistence baselines; `fit`, `predict`, metrics, importance"],
             ["`Live`", "backend/service.py", "The shared live simulation: configure, step, reset, ambulance, snapshot"],
             ["`Preview`", "backend/service.py", "The landing page's own real-time simulation and event lines"],
             ["`Predictor`", "backend/service.py", "Background training wrapper with ready and error state"],
             ["`ApiError`", "backend/service.py", "Exception carrying status, message and hint, rendered as JSON"]],
            widths=[1.2, 1.8, 3.4], align=["l", "l", "l"], size=9.5),
        P("`Sim` is deliberately large because the four controllers differ only in `_signals` and `_decide`; everything else (arrivals, transit, discharge, recording) is shared, which is what guarantees "
          "identical demand. The vision layer is a module of functions rather than classes because each call is a pure transformation of an image."),
        H3("5.4.2 Sequence diagram"),
        FIG(F.diag("07_sequence_flow.png"), "Sequence diagram of the main flow: (A) skip five minutes on the Live page; (B) send an ambulance and step again.", 5.3),
        P("Scenario A starts when the operator clicks *Skip 5 min*. The React console sends `POST /api/live/step {seconds: 300}` with the bearer token; the API's `current_user` dependency checks the HS256 signature and expiry; "
          "`Live.step` runs under the service lock, attaches the forecaster if the ML toggle is on and calls `Sim.run(300)`. Inside that call the simulator loops 300 times through arrivals, transit arrivals and signals, asks the forecaster for a prediction every 10 seconds (advanced controller) and finishes each second with discharge and record. "
          "The service then builds a snapshot (KPIs, map geometry, queue series, junction table) and the console redraws. In scenario B the operator sends an ambulance: `Live.ambulance()` creates an emergency vehicle at a random entry road and the snapshot carries the banner *signals pre-empting*; "
          "on the next step the simulator's decision step switches the affected junctions. The fixed-time and adaptive controllers instead give an \"ignored\" banner."),
        H3("5.4.3 Use-case diagram"),
        FIG(F.diag("08_use_case.png"), "Use-case diagram with the operator, the visitor and the evaluator or developer.", 4.6),
        P("The **operator** signs in with the demo account and can configure the network (grid, controller, demand, ML toggle), run the live simulation or skip five minutes, send an ambulance (an extension of running the simulation), "
          "run the controller benchmark and demand sweep, analyse an image (synthetic scene, sample photograph or upload), view the queue forecast and review the violation log. Every operator use case includes signing in. "
          "The **visitor** only watches the public live preview on the landing page, which needs no token. The **evaluator or developer** runs the experiment, test and screenshot scripts, which import the same engine. "
          "There is a single operator role in this build; the demo sign-in is a gate, not a role system."),

        H2("5.5 Data Design"),
        FIG(F.diag("09_er_diagram.png"), "Logical entity-relationship diagram: FlowSense keeps its entities in memory; there is no database.", 5.4),
        P("FlowSense stores no tables. The entity-relationship diagram is therefore logical: it shows which entities exist at run time and how they refer to one another. One NETWORK (the `Sim`) has n = rows x columns JUNCTIONs (1 : n); "
          "each junction has four APPROACHes (1 : 4); each approach holds a queue of zero or more VEHICLEs (1 : 0..*). A network uses at most one FORECASTER, which in turn is used by the BENCHMARK_CACHE; "
          "a vehicle may raise at most one VIOLATION or finish as an EMERGENCY_RUN if it is an ambulance; and the SESSION_TOKEN is stateless and kept by the browser. There are no foreign keys: the relations are Python references inside one process."),
        TAB("In-memory entities.",
            ["Entity", "Key attributes", "Lifetime"],
            [["Network (`Sim`)", "rows, columns, controller, demand multiplier, seed, start hour, clock, spawned ambulances, pre-emptions", "Until reset or API restart"],
             ["Junction", "index, phase (0 or 1), timer, clearance counter, next phase, pre-emption flag", "Per simulation"],
             ["Approach", "name (N, E, S, W), queue of vehicles in arrival order, forecast, discharge credit, entry-road flag", "Per simulation"],
             ["Vehicle", "id, type (car, bike, bus, truck, ambulance), arrival time, wait, emergency flag, red-runner flag, plate", "Until it leaves the network"],
             ["Violation event", "time, junction, approach, kind, plate, vehicle type, confidence 0.86-0.99", "Per simulation"],
             ["Emergency record", "id, delay, travel time", "Per simulation"],
             ["Forecaster", "GB model, metrics, importance, training row count", "Until API restart (retrained in about 6 s)"],
             ["Benchmark result", "per-controller summaries for a settings key", "Cached until restart"],
             ["Token", "subject, name, expiry (12 h), HS256 signature", "Client side"]],
            widths=[1.4, 3.7, 1.4], align=["l", "l", "l"], size=9.5),
        P("Keeping state in memory was a choice, not an omission: the simulation is seeded and cheap to regenerate (a 30-minute run takes 0.17 to 0.52 s), the benchmark is deterministic for a given seed and settings, "
          "and the landing page's pulse does not need history. The cost is that nothing survives a restart and that the API serves one shared live simulation to every signed-in browser, which is acceptable for a single-operator demonstration and would not be for a deployment."),

        H2("5.6 Core Algorithms"),
        H3("5.6.1 The advanced controller's decision"),
        FIG(F.diag("10_flowchart_control.png"), "Flowchart of the advanced controller's per-junction decision, evaluated every simulated second.", 5.0),
        P("Each junction has two phases (north-south and east-west). While a clearance interval is running nothing is decided. Otherwise the controller first checks for an emergency target: the nearest "
          "ambulance among queue heads and the inbound transit list within 15 seconds. If there is one and its phase is not green, the controller switches to it once the current green is at least 2 seconds old. "
          "If there is no emergency target, it compares the pressure of the green phase with that of the red phase. Pressure is the PCU-weighted queue, plus 0.7 times the forecast excess over the current queue, "
          "plus the PCU of vehicles arriving within 8 seconds, plus the head vehicle's wait divided by 12, and the result is multiplied by 0.3 for an approach whose straight-ahead receiving queue is nearly full. "
          "The green is kept for at least 13 seconds and at most 60; after the minimum the controller switches when the green phase has no pressure and the other has some, or when the other phase's pressure exceeds twice the current plus 4."),
        P("The other controllers are simplifications of the same loop: *fixed* switches every 30 seconds; *adaptive* uses the same switching rule with queue-only pressure and a 15 to 60 second green; "
          "*emergency* is adaptive plus pre-emption at the junction where the ambulance is queued or within 5 seconds. The emergency controller is an emulation of the base paper's idea [" + str(R['base']) + "], "
          "not a re-implementation, because the simulator knows which vehicles are ambulances and does not model a detector."),
        H3("5.6.2 The vision pipeline"),
        FIG(F.diag("11_flowchart_vision.png"), "Flowchart of the vision pipeline: frame, vehicle detection, light-bar rule, density estimate and green-time recommendation.", 5.0),
        P("For a real image the pipeline runs YOLOv8n [" + str(R['ultralytics']) + "] restricted to the COCO classes car, motorcycle, bus and truck [" + str(R['coco']) + "], then an HSV rule finds red and blue blobs "
          "that touch after dilation. A detected vehicle whose box contains a light-bar cluster in its upper region is relabelled `ambulance`. The density report converts counts to passenger-car units "
          "(car 1, bike 0.5, bus 3, truck 2), divides by a road capacity of 14 PCU, labels the ratio LOW, MEDIUM, HIGH or JAMMED, and recommends 12 seconds of green if an ambulance is present, otherwise "
          "12 + 3.2 per PCU clamped to 15 to 60 seconds. For the synthetic overhead scenes a contour-based classical detector replaces YOLO because the overhead renderer is outside COCO's training distribution."),
        H3("5.6.3 The queue forecaster"),
        FIG(F.diag("12_model_architecture.png"), "Architecture of the queue forecaster: 11 features per approach, gradient-boosted regressor, baselines and closed-loop use in the controller.", 5.2),
        P(f"The forecaster predicts the queue length of each approach 30 seconds ahead from eleven features: the current queue, its PCU weight, the queue 10 and 30 seconds ago, the arrivals in the last 30 seconds, "
          f"the vehicles inbound within 15 seconds, whether the approach is green, the green time so far, whether it is an entry road, and the sine and cosine of the time of day. It is a scikit-learn "
          f"GradientBoostingRegressor [" + str(R['gbm']) + "], [" + str(R['sklearn']) + f"] of 160 trees, depth 4, learning rate 0.08 and subsample 0.9, trained on {F.PR['n_samples']:,} snapshots from six simulated runs, with a Random Forest [" + str(R['rf']) + "] "
          "and a persistence baseline (\"the queue stays the same\") for comparison. The advanced controller calls it every 10 simulated seconds and clips the output to 0 to 40 vehicles."),

        H3("5.6.4 Cost of one simulated second"),
        P("The simulator's cost is linear in the number of junctions and vehicles. Arrivals touch only the entry roads; the transit step touches the vehicles landing in that second; the signal step evaluates two phase pressures per junction, each a sum over two queues; "
          "the discharge step releases at most a few vehicles per approach; the record step walks every queue once to add a second of waiting time. The advanced controller adds an upstream scan of the next 15 seconds of the transit list and, every tenth second, one forecaster call on a 16 x 11 or 36 x 11 matrix. "
          f"Measured on the test machine, 1,800 simulated seconds take {F.TH['2x2/fixed']['wall_s']:.2f} s (2 x 2, fixed-time) to {F.TH['3x3/advanced']['wall_s']:.2f} s (3 x 3, advanced), which is {F.TH['3x3/advanced']['speedup']:,.0f} to {F.TH['2x2/fixed']['speedup']:,.0f} times faster than real time; this is what makes five-seed benchmarks interactive."),
        TAB("Order of events inside one simulated second (`Sim.step`).",
            ["Step", "Method", "What happens"],
            [["1", "`_arrivals`", "Poisson arrivals at entry roads scaled by demand and time of day; wrong-way driver draw; possible ambulance at a random entry road"],
             ["2", "`_transit_arrivals`", "Vehicles whose 12 s link time ends join their next approach queue"],
             ["3", "`_signals`", "Advanced or emergency-aware controllers scan upstream; the advanced one refreshes forecasts every 10 s; each junction advances its clearance or evaluates `_decide`"],
             ["4", "`_discharge`", "Green approaches release vehicles at saturation flow (ambulance first); red-light runners may cross; spill-back blocks release"],
             ["5", "`_record`", "Queue and arrival histories, total queue and phase log are appended; every queued vehicle's wait grows by 1 s"]],
            widths=[0.5, 1.5, 4.4], align=["c", "l", "l"], size=9.5),

        H2("5.7 Module Design"),
        TAB("Modules, responsibilities and size.",
            ["Module", "Lines", "Responsibility"],
            [["`smart_traffic/sim.py`", "415", "Simulator, demand profile, four controllers, features, KPIs, benchmark helper"],
             ["`smart_traffic/predictor.py`", "59", "Dataset builder and the gradient-boosted queue forecaster with baselines"],
             ["`smart_traffic/vision.py`", "201", "YOLOv8 wrapper, light-bar rule, classical detector, density report, annotation, synthetic scene"],
             ["`backend/main.py`", "210", "FastAPI routes, input models, error handlers, authentication dependency"],
             ["`backend/service.py`", "437", "Live, Preview and Predictor classes, benchmark and sweep, vision payloads, prediction and violation payloads"],
             ["`backend/auth.py`, `config.py`", "55 + 32", "Stdlib HS256 token, credential check, `.env` settings"],
             ["`frontend/src/pages/*.jsx`", "8 pages", "Landing, Login, Live, Benchmark, Vision, Prediction, Violations, About"],
             ["`frontend/src/lib/*`", "-", "Authentication context, live-simulation provider, theme, activity log, request hook"],
             ["`scripts/`", "-", "`run_experiments`, `eval_real_vision`, `measure_api`, `smoke_test`, `capture_screens`, `check_ui`, docs builders"],
             ["`tests/`", "2 files", "38 pytest tests (24 engine, 14 API)"],
             ["`app.py`", "546", "Original Streamlit application, unchanged"]],
            widths=[2.2, 0.7, 3.5], align=["l", "c", "l"], size=9.5),
        P("The dependency direction is strictly downward: the React pages call `/api`, `main.py` calls `service.py`, `service.py` calls `smart_traffic`, and `smart_traffic` imports only NumPy, scikit-learn, OpenCV and, optionally, Ultralytics. "
          "No engine module imports FastAPI, so the engine can be tested without a server, as the 24 engine tests do."),

        H2("5.8 API Design"),
        P("The API has twenty endpoints in four groups. Four are public (health, login, the demo account for the sign-in page and the landing pulse); the other sixteen require a bearer token. "
          "Requests and responses are JSON, except the image upload, which is multipart. Errors always have the shape `{detail: {message, hint}}`, so the console can say what failed and what to do. "
          "Chapter 6 lists every endpoint with its request and response."),
        TAB("Route groups.",
            ["Group", "Routes", "Purpose"],
            [["Public", "GET /api/health; POST /api/auth/login; GET /api/auth/demo; GET /api/public/pulse", "Liveness and predictor state; sign-in; demo credentials; landing-page preview"],
             ["Live control", "GET /api/live; PUT /api/live/config; POST /api/live/step; /ambulance; /reset", "The shared simulation"],
             ["Benchmark", "POST /api/benchmark; POST /api/benchmark/sweep", "Four controllers on identical traffic; delay against demand"],
             ["Vision, forecast, violations", "GET /api/vision/synthetic, /sample; POST /api/vision/analyze; GET /api/prediction, /live; POST /api/prediction/simulate; GET /api/violations", "Detections and density; forecasts; evidence log"]],
            widths=[1.2, 3.4, 1.8], align=["l", "l", "l"], size=9.5),

        H2("5.9 User Interface Design"),
        P("The console follows a control-room metaphor: a dark theme with a light option, a monospaced typeface for readings, and a left navigation with keyboard shortcuts (G then C, B, V, P, R, A) and a "
          "command palette on `/`. The sign-in page shows the demo account so that a reviewer never has to look for credentials. Every screen loads real data from the API; an error from the API is shown with its hint, "
          "and a model that is still training is shown as a state, not a blank panel."),
        PAIR([(F.shot("04_login.png"), "Sign-in page with the demo account."), (F.shot("06_live_map_and_status.png"), "Live control: road map, queue chart and junction table.")], 2.9),
        TAB("Screens and what each shows.",
            ["Screen", "Route", "Main content"],
            [["Landing", "/", "Live preview map, headline numbers, event lines, feature overview"],
             ["Sign in", "/login", "Credentials and the demo account"],
             ["Live control", "/app", "Network settings, KPIs, road map with signals and vehicles, queue chart, junction status, ambulance button"],
             ["Benchmark", "/app/benchmark", "Duration, demand, seeds and start hour; four-controller KPIs, delay and ambulance-delay charts, demand sweep"],
             ["Vision", "/app/vision", "Synthetic scene, YOLOv8 sample photo and upload; detections, light-bar clusters, density report"],
             ["Prediction", "/app/prediction", "Forecaster KPIs, predicted-against-actual scatter, importance, model comparison, live forecast"],
             ["Violations", "/app/violations", "Counts, per-junction and per-minute charts, evidence log"],
             ["About", "/app/about", "The paper, the pipeline and the project team"]],
            widths=[1.2, 1.4, 3.8], align=["l", "l", "l"], size=9.5),
        PAIR([(F.shot("07_benchmark.png"), "Benchmark screen with KPI tiles and charts."), (F.shot("10_vision_synthetic.png"), "Vision screen on a synthetic scene.")], 2.9),
        P("The layout works from 360 px to 1440 px, honours reduced-motion settings, and keeps the state of the live simulation in a provider so that moving between screens does not reset it; "
          "`scripts/check_ui.py` exercises these cases in a real browser."),

        H2("5.10 Traceability to the Project Objectives"),
        P("The batch's six objectives (file 6, Objectives and Problem Statement) are each realised by a design element, and the table states plainly how far."),
        TAB("Objectives, design elements and what was delivered.",
            ["Objective", "Design element", "Delivered"],
            [["1. Detect and count vehicles from camera video with YOLO", "`detect_yolo` (YOLOv8n) and `detect_classical`; Vision screen", "Single frames and uploads only; no live video ingestion; stock COCO weights"],
             ["2. Estimate density per approach", "`density_report` (PCU / 14 capacity) for images; per-approach queue and PCU in the simulator", "Yes, per image and per simulated approach; not wired from camera to simulator"],
             ["3. Adaptive signal timing in proportion to demand", "`_pressure` and `_decide` of the adaptive and advanced controllers", "Yes, in simulation"],
             ["4. Emergency priority", "`_emergency_target`, upstream scan, lane clearing; light-bar rule for images", "Yes in simulation with ground-truth ambulances; the image rule is not closed-loop"],
             ["5. Coordination between adjacent junctions", "Transit look-ahead, spill-back damping, green wave", "Yes, as simulated look-ahead; not a network protocol"],
             ["6. Evaluate detection accuracy, waiting time and emergency clearance", "`run_experiments.py`, `eval_real_vision.py`, benchmark screen", "Yes; see Chapter 8"]],
            widths=[2.2, 2.4, 1.8], align=["l", "l", "l"], size=9.5),

        H2("5.11 Design Trade-offs"),
        B("**Own simulator instead of SUMO.** A pure-Python simulator is portable and fast (1,800 simulated seconds in 0.17 to 0.52 s) and keeps the experiment reproducible, but it is a model whose assumptions the project chose; absolute numbers cannot be compared with the base paper's SUMO study.",
          "**Ground-truth emergency knowledge.** The controllers know which vehicle is an ambulance; this isolates the control question from the detection question, at the price of not testing detection inside the loop.",
          "**Pretrained detector, no training.** YOLOv8n is used as shipped, which avoids a training pipeline and a dataset the batch did not have, and is the reason real-image accuracy is modest (Chapter 8).",
          "**In-memory state.** Simpler and enough for a demonstration; unsuitable for more than one operator or for restarts.",
          "**Forecast as a pressure term, not a controller.** The forecaster adds to the pressure score rather than replacing the rule, so a poor forecast can only bias the decision slightly, which is consistent with the ablation result that removing it costs about 3 s of delay."),
    ]
