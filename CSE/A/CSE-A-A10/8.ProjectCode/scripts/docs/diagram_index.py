"""Index of the FlowSense design diagrams: (key, title, file, caption, explanatory paragraph).

The files are written by scripts/docs/make_diagrams.py and diagrams_more.py into docs/diagrams/.
Used by the block-diagram document (11), the full report, the decks and the paper.
"""

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "Four-tier architecture of FlowSense: React console, FastAPI application with 20 routes, service layer and traffic engine, and in-memory state plus files.",
     "The presentation tier is the React console on port 5310, calling the API through an axios client; the original Streamlit page remains as a separate process. "
     "The FastAPI tier on port 8310 exposes 20 routes: four public ones (health, login, demo account, landing preview) and sixteen guarded by a signed token. Below it, backend/service.py holds the shared live simulation, "
     "the landing-page preview, the background-trained forecaster and the benchmark and vision functions, all driving smart_traffic/sim.py, predictor.py and vision.py in one Python process. "
     "There is no database: state lives in memory, and only the model weights, the sample photo and the .env settings are files."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "Two lanes: the closed simulated control loop (sense, forecast, decide, act, coordinate, report) and the vision layer for one camera frame.",
     "Lane A is repeated every simulated second. Arrivals fill the approach queues, the gradient-boosting model forecasts each queue 30 seconds ahead every tenth second, the controller scores the two phases and either holds or switches, "
     "and released vehicles travel a 12-second link to the next junction, which lets a junction look ahead at an approaching platoon. Results feed the KPIs, the benchmark and the violation log. "
     "Lane B treats one camera frame: detect vehicles, find red-and-blue light bars, compute a PCU density and a green-time hint, and return the annotated frame. Lane B is a demonstration and is not wired into the controllers of Lane A."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Context diagram (DFD level 0): one process, the operator, the image source, the evaluator or developer, and the simulated demand.",
     "At level 0 the whole product is a single process. The operator sends a login, network settings, step commands, ambulance requests and benchmark requests, and receives live KPIs, the road map, queues, forecasts and the violation log. "
     "The image source supplies a JPG or PNG frame of up to 12 MB with a confidence value and receives detections, the PCU density and the light-bar flag. The evaluator or developer supplies experiment scripts, tests and .env settings "
     "and receives metric files, test results and screenshots. Vehicle arrivals and ambulance events come from a seeded Poisson generator; it is drawn as an external entity because a deployment would replace it with real cameras."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "DFD level 1: seven processes (authenticate, simulate, control, forecast, vision, benchmark, report) and five data stores.",
     "Level 1 splits the platform into seven processes. Process 1.0 authenticates and validates every request. Process 2.0 simulates traffic and writes queues, phases and in-flight vehicles to the live state (D1). "
     "Process 3.0 reads that state and the forecast from 4.0, which reads its model from D2, and decides the phases; its events go to the violation and emergency logs (D4). Process 5.0 analyses an image with the YOLOv8n weights (D5). "
     "Process 6.0 runs the four controllers on identical demand and fills the benchmark cache (D3). Process 7.0 turns the state and logs into the KPIs, map and violation log that the operator sees."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "DFD level 2: the control process 3.0 expanded into six sub-processes for one junction and one second.",
     "Level 2 follows one junction through one second of the advanced controller. Process 3.1 scans the transit queue for inbound traffic within 8 seconds and ambulances within 15 seconds. Process 3.2 refreshes the queue forecast every ten seconds. "
     "Process 3.3 finds the phase of the nearest ambulance, queued or inbound. Process 3.4 scores the current and the other phase from queue PCU, forecast excess, inbound platoon, head-of-queue wait and the spill-back damping. "
     "Process 3.5 applies the minimum-green, maximum-green and switching rules, and process 3.6 runs the three-second clearance and the discharge at 0.5 vehicles per second, updating the queues and logging events."),
    ("uml", "UML class diagram", "06_uml_class.png",
     "UML class diagram: the FastAPI application, the service classes (Live, Preview, Predictor), the engine classes (Sim, Vehicle, QueuePredictor) and the vision module.",
     "The FastAPI application delegates to three service classes in backend/service.py. Live owns the shared Sim and exposes configure, reset, step, ambulance and snapshot; Preview owns a second Sim for the landing page; "
     "Predictor trains a QueuePredictor in a background thread. Sim holds the queues of Vehicle objects, the signal state, the transit queue, the violation and emergency logs and the controller code (_decide, _pressure, _emergency_target); "
     "only the advanced controller uses the forecaster. The vision module is a set of functions rather than a class. The authentication and configuration modules and the benchmark cache sit beside the application."),
    ("seq", "Sequence diagram of the main flow", "07_sequence_flow.png",
     "Sequence diagram: skipping five minutes on the Live page (token check, simulation loop, forecast calls, snapshot), then sending an ambulance.",
     "Part A follows one click on Skip 5 min. The console posts the step request with the bearer token; FastAPI verifies the HS256 signature and expiry, calls Live.step under a lock, and Live attaches the predictor if the ML toggle is on "
     "and runs Sim.run(300). Each simulated second performs arrivals, signals and discharge; the advanced controller asks the QueuePredictor for a forecast every ten seconds. Live then builds the snapshot of KPIs, map, queue series and junction table, "
     "which FastAPI returns and the console redraws. Part B sends an ambulance: it joins an entry queue, the snapshot carries the pre-emption banner, and the next step forces its phase green."),
    ("uc", "Use-case diagram", "08_use_case.png",
     "Use-case diagram with the operator, the visitor, and the evaluator or developer.",
     "The operator signs in with the demo account and can configure the network (grid, controller, demand, ML toggle), run the live simulation or skip five minutes, send an ambulance, run the controller benchmark and the demand sweep, "
     "analyse an image (synthetic scene, bundled photo or upload), view the queue forecast and review the violation log. Configuring includes signing in, running includes configuring, and sending an ambulance extends running. "
     "The visitor can only watch the live preview on the landing page, which is public. The evaluator or developer runs the experiments, tests and screenshot scripts, which import the same engine; this use case sits at the system edge."),
    ("er", "Entity-relationship diagram (logical)", "09_er_diagram.png",
     "Logical entity-relationship diagram: FlowSense has no database, so the entities are in-memory structures, a token and a cache.",
     "A network (one Sim) contains n junctions, each with four approaches, and each approach holds a queue of vehicles. A vehicle may raise one simulated violation (red-light jumping or wrong-way driving with a plate and a confidence) "
     "or finish as one emergency run recording its delay and travel time. A network may use one trained forecaster; the benchmark cache stores the summaries of benchmark runs, and the session token is a signed string kept by the browser. "
     "No foreign keys exist; the relations are Python references inside one process, and all of it is lost when the server restarts. The diagram is logical for that reason."),
    ("flow_ctrl", "Controller decision flowchart", "10_flowchart_control.png",
     "Flowchart of the advanced controller's decision for one junction in one second.",
     "During a clearance interval the junction only counts down. Otherwise the green timer advances and, if an ambulance is queued at the junction or inbound within 15 seconds, its phase becomes the target: the controller switches to it after at least two seconds of the current green. "
     "Without an ambulance, the pressure of each phase is computed from PCU queue, forecast excess, inbound platoon and head wait, damped when the downstream queue is nearly full. The phase holds before 13 seconds, switches after 60 seconds "
     "if the other side has demand, switches if the current phase is empty and the other is not, switches if the other pressure exceeds twice the current plus four, and otherwise holds."),
    ("flow_vision", "Vision pipeline flowchart", "11_flowchart_vision.png",
     "Flowchart of the vision layer: detection, light-bar rule, density report and annotated response.",
     "A frame is either a synthetic overhead scene, handled by a contour-based detector, or a real photograph, handled by YOLOv8n at confidence 0.3 for cars, motorcycles, buses and trucks. "
     "Both paths then run the light-bar rule: red and blue masks in HSV space are cleaned, dilated and intersected, and a cluster with enough pixels of both colours counts as a light bar. A vehicle box whose upper part contains a light bar with a high enough score is relabelled ambulance. "
     "The density report adds passenger-car units, divides by a capacity of 14 to give LOW, MEDIUM, HIGH or JAMMED, and recommends a green time."),
    ("model", "Queue forecaster architecture", "12_model_architecture.png",
     "Architecture of the queue forecaster: eleven features, gradient boosting with two baselines, a 30-second forecast, and its use in the controller.",
     "For every approach the simulator state at second t is turned into eleven features: the current and PCU-weighted queue, the queue ten and thirty seconds ago, the inflow over thirty seconds, the inbound vehicles over fifteen seconds, "
     "whether the approach is green and for how long, whether it is an entry road, and the sine and cosine of the time of day. A gradient-boosting regressor of 160 trees predicts the queue thirty seconds ahead, clipped to the range 0 to 40; "
     "a random forest and a persistence rule are the baselines. It is trained on 26,988 snapshots from six simulated runs and, for the advanced controller, adds 0.7 times the forecast growth to each approach's pressure."),
]
