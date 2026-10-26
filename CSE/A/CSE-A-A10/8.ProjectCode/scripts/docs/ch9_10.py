"""Chapters 9 (Conclusion) and 10 (Future scope), plus the shared helper block lists used by documents 9, 10, 12 and 15."""
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def src(rel, a, b):
    """Lines a..b (1-based, inclusive) of a repository file, exactly as they stand in 8.ProjectCode."""
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        lines = f.read().split("\n")
    return "\n".join(lines[a - 1:b])


def _d(grid="2x2"):
    return F.derived(grid)


# ---------------------------------------------------------------------------- novelty / contributions
def novelty_blocks():
    d2, d3 = _d("2x2"), _d("3x3")
    return [
        H2("What the base paper contributes"),
        P(f"The base paper [{R['base']}] adds a supervisory emergency-priority layer to an already optimised traffic controller. A single-class YOLO26m detector trained on 3,130 annotated images finds the roof light-bar of an emergency vehicle "
          "(precision 0.73, recall 0.69, mAP50 0.73, 11-14 ms per frame on a GPU); a confidence threshold of 0.5 and three consecutive detections trigger a priority arbitrator that ends the current phase after a yellow interval, forces green on the ambulance approach and restores the optimised plan afterwards; "
          "the whole is validated in SUMO on one modelled roundabout in Rabat, where the ambulance travel time falls from 70 s (GA-SGD) and 64 s (fixed-time) to 56 s and the total waiting time to 19,887 s. "
          "The paper treats detection and priority at a single junction and leaves multi-junction coordination, congestion forecasting and violation handling out of scope."),
        H2("What is new in FlowSense"),
        B("**One working pipeline.** The batch objective is a single chain - detect, forecast, adapt, prioritise, coordinate, enforce - and FlowSense implements every link in one product with a console, an API and a built-in validation harness, where the base paper reports a detector and a simulation study.",
          "**A coordinated advanced controller.** The pressure of each phase combines passenger-car-equivalent queues, a 30-second machine-learning forecast of the build-up, vehicles arriving from the upstream junction within 8 s, a fairness term for the head-of-queue wait, and a spill-back damping factor when the downstream approach is nearly full; an ambulance is looked for 15 s upstream so that the junctions along its route turn green before it arrives (a green wave) instead of pre-empting one junction at a time.",
          "**Like-for-like benchmarking.** The four controllers share the same random demand and the same ambulances, so differences are attributable to control; the benchmark, a demand sweep, an emergency-heavy test and an ablation are all reproducible from `scripts/run_experiments.py`.",
          "**Honest validation beyond the simulator.** The vision layer was tested on 293 real dashcam frames and 600 real ambulance and non-ambulance photographs, and the forecaster by leaving whole simulation runs out; both exposed weaknesses that the product's own screens do not show."),
        H2("What is standard"),
        P(f"Several parts are established techniques used as they are: YOLOv8n with COCO weights [{R['ultralytics']}], [{R['yolo']}], passenger-car-equivalent weights [{R['hcm']}], queue-based actuated control in the tradition of [{R['webster']}] and [{R['varaiya']}], "
          f"gradient-boosted regression [{R['gbm']}] and random forests [{R['rf']}] through scikit-learn [{R['sklearn']}], and the idea of pre-empting a signal for an emergency vehicle [{R['sasikala']}], [{R['zlatkovic']}]. "
          "The simulator, the advanced pressure rule and the integration are the project's own work; none of the learning components was invented here."),
        H2("What is weaker than the base paper"),
        B("**No trained emergency detector.** The base paper trains a dedicated light-bar detector; FlowSense uses an HSV colour rule on top of a stock detector, which recalled 1.3 % of 300 real ambulance photographs (Chapter 8).",
          "**No SUMO.** The base paper validates in SUMO against a real intersection; FlowSense validates in a purpose-built simulator whose parameters are assumptions, so absolute numbers are not comparable.",
          "**Ground-truth emergency knowledge.** In the simulation the controllers know where the ambulances are; the vision layer is not closed-loop with the controllers, so the base paper's temporal-confirmation arbitrator (three consecutive detections) is not implemented.",
          "**A small gain over plain adaptive control.** The advanced controller improves on plain queue-actuated control by "
          f"{d2['delay_cut_advanced_vs_adaptive_pct']:.1f} % (2x2) and {d3['delay_cut_advanced_vs_adaptive_pct']:.1f} % (3x3), within about one standard deviation, so its novelty is better supported for ambulances than for general traffic."),
    ]


def contribution_blocks():
    d2, d3 = _d("2x2"), _d("3x3")
    return [
        P("The contributions of the project, stated at the strength the evidence supports, are:"),
        N(f"**An integrated smart-traffic pipeline**, FlowSense, that combines YOLOv8n vehicle detection with passenger-car-equivalent density, an HSV light-bar emergency rule, a 30-second queue forecaster, four signal controllers, a violation log and a FastAPI + React console on ports 8310 and 5310.",
          "**A like-for-like simulation harness** (the FlowSense simulator) for 2x2 and 3x3 junction grids in which four controllers - fixed-time, adaptive, a base-paper-style emergency-aware controller and the advanced controller - face identical seeded demand and identical ambulances.",
          f"**An advanced coordinated controller** whose pressure rule adds forecast, inbound-platoon, fairness and spill-back terms and an upstream emergency green wave. It reduces average delay by {d2['delay_cut_advanced_vs_fixed_pct']:.1f} % (2x2) and {d3['delay_cut_advanced_vs_fixed_pct']:.1f} % (3x3) against fixed-time and ambulance delay by {d2['emergency_cut_advanced_vs_fixed_pct']:.1f} % and {d3['emergency_cut_advanced_vs_fixed_pct']:.1f} %.",
          "**A 30-second queue forecaster** (gradient boosting on 11 features, 26,988 simulated samples) that beats persistence by about a third on a random split (MAE 1.64 against 2.57) and whose limits - failure on an unseen congested run, about 3 s of closed-loop benefit - were measured rather than assumed.",
          "**An honest evaluation**: five-seed means with standard deviations, a demand sweep, an emergency-heavy test, an ablation, leave-one-simulation-out validation, and tests of the vision layer on 293 real frames and 600 real photographs, which show that the synthetic vision results do not transfer.",
          "**A reproducible, tested software artefact**: 38 passing unit and API tests, a 33-check end-to-end smoke test, a one-click `run.bat`, and scripts that regenerate every number in the report from JSON."),
    ]


# ---------------------------------------------------------------------------- scope and limitations
def scope_blocks():
    return [
        H2("In scope"),
        B("**Signal control in a simulated grid** of 2x2 or 3x3 two-phase junctions with four approaches each, four controllers, a demand multiplier from 0.4 to 2.0 and a time-of-day profile with morning and evening peaks.",
          "**Vehicle detection and density estimation** on camera frames: YOLOv8n on photographs and uploads, a contour detector on rendered overhead scenes, passenger-car-equivalent density and a recommended green time.",
          "**Emergency-vehicle handling**: a red-plus-blue light-bar rule on detected vehicles in the vision layer, and pre-emption with an upstream green wave in the simulator.",
          "**Congestion forecasting**: queue 30 s ahead per approach from simulated junction data.",
          "**Inter-junction coordination** as look-ahead on vehicles in transit between junctions and spill-back avoidance.",
          "**A violation log** for red-light jumping and wrong-way driving with plate, vehicle class and confidence.",
          "**The console and API**: sign-in with a demo operator account, live control, benchmark, vision, prediction and violations screens, 20 HTTP endpoints, tests and a launcher."),
        H2("Out of scope"),
        B("Real camera streams (RTSP), video decoding, multi-object tracking and number-plate recognition.",
          "Training a light-bar or emergency-vehicle detector, or fine-tuning YOLO on local traffic.",
          "SUMO, CARLA or other microscopic simulators, and calibration of the simulator against field counts.",
          "Hardware: signal controllers, controller-area networks, V2I radios, edge devices.",
          "Pedestrian phases, turning-lane phases, left-turn protection, bus priority and signal plans with more than two phases.",
          "Persistent storage, user management with roles, multi-tenant operation and cloud deployment.",
          "Safety evaluation (conflicts, collisions) and any legal or regulatory assessment of automatic enforcement."),
        H2("Boundaries of the product"),
        TAB("Dimensions of the delivered system", ["Dimension", "Delivered"],
            [["Network sizes", "2x2 (4 junctions) and 3x3 (9 junctions), two-phase signals, 12 s links"],
             ["Controllers", "Fixed-time, queue-actuated adaptive, emergency-aware (base-paper style), advanced"],
             ["Vehicle classes", "Car, bike, bus, truck, ambulance (PCU 1, 0.5, 3, 2, 1)"],
             ["Vision modes", "Synthetic scene, YOLOv8n on the sample photo, YOLOv8n on an uploaded image (up to 12 MB)"],
             ["Forecast", "Queue per approach, 30 s ahead, gradient boosting, trained at API start-up in about 6 s"],
             ["Interface", "React console (8 pages), FastAPI backend, demo login, light and dark themes"],
             ["Hardware used", "Intel Core i5-12500, 15.7 GB RAM, no GPU"]],
            widths=[1.6, 4.6], align=["l", "l"], size=10),
    ]


def assumption_blocks():
    return [
        P("The results depend on the following assumptions, all of which are choices of the project rather than findings."),
        B("**Traffic model.** Arrivals are Poisson at the entry roads with base rates of 0.15 veh/s on the north and south entries and 0.10 veh/s on the east and west entries, scaled by the demand slider and a rush-hour profile peaking at 08:30 and 17:30; the vehicle mix is 68 % cars, 13 % bikes, 6 % buses and 13 % trucks.",
          "**Discharge and timing.** Saturation discharge is 0.5 vehicles per second per approach, with 2 s of start-up lost time and 3 s of yellow and all-red clearance; a link takes 12 s; an approach holds 30 vehicles before spill-back blocks upstream release.",
          "**Signals.** Each junction has two phases (north-south and east-west) and no turn-specific phases; vehicles turn right or left with fixed probabilities and leave the network at its edge.",
          "**Emergency vehicles.** Ambulances are known to the simulated controllers by ground truth within a look-ahead (5 s for the base-paper style, 15 s for the advanced controller); the vision layer is evaluated separately.",
          "**Violations.** 5 % of cars are red-light runners that pass after 25 s on red, and a wrong-way driver appears with probability 0.0003 per entry second.",
          "**Fuel and CO2.** An idling vehicle burns 0.6 L/h and 1 L of fuel gives 2.31 kg CO2.",
          "**Evaluation.** Five seeds (three for the demand sweep) at demand x1.2, 1800 s, start 08:00 unless stated; the predictor is trained on six simulated runs under the adaptive controller.",
          "**Operation.** One demo operator, one shared live simulation, the API and the console on one machine."),
    ]


def limitation_blocks():
    d2 = _d("2x2")
    return [
        P("The limitations below are properties of the delivered system and of the evidence, ordered by how much they affect the conclusions."),
        TAB("Limitations of FlowSense and their effect", ["Limitation", "Evidence", "Effect on the conclusions"],
            [["No trained emergency detector", "Light-bar rule recalls 4 of 300 real ambulance photos (0.013); 100 % on synthetic scenes", "The camera-to-signal link for ambulances is demonstrated only in simulation with ground-truth knowledge"],
             ["Stock COCO detector on mixed traffic", "Real frames: 4-wheeler recall 0.586, 2-wheeler 0.083, 3-wheeler 0.000", "Density estimates would undercount two- and three-wheelers; objective 1 only partly met"],
             ["Brittle classical detector", "No detections under Gaussian noise sigma 10; light bar lost at brightness x0.6", "Synthetic-scene success is not evidence of robustness"],
             ["Simulator, not SUMO", "Parameters are the authors' assumptions; no calibration with field data", "Absolute delays are not comparable with the base paper or with real roads"],
             ["Small gain over plain adaptive control", f"-{d2['delay_cut_advanced_vs_adaptive_pct']:.1f} % (2x2), within one standard deviation; worse at demand x0.6 and x0.9", "Most of the improvement over fixed-time comes from adaptivity itself"],
             ["Forecaster outside its range", "Leave-one-run-out R2 0.04; MAE 14.66 against 5.49 on the congested run", "The random-split R2 of 0.96 overstates real performance; closed-loop benefit about 3 s"],
             ["Pre-emption has a cost", "Base-paper style is 6.5 % (2x2) and 2.2 % (3x3) slower than adaptive; no pre-emption gives ambulance delay 27.3 s", "A deployment must choose the trade-off explicitly"],
             ["Violations are simulated", "Events come from ground-truth runners; confidence is a random draw in 0.86-0.99", "The Violations screen demonstrates logging, not detection"],
             ["No persistence, one operator", "State lives in the API process; demo login only", "Not a multi-user or production system"],
             ["Small statistical base", "Five seeds, standard deviations 2.8-11.0 s on the 2x2 grid", "Differences below one standard deviation are not established"]],
            widths=[1.6, 2.6, 2.4], align=["l", "l", "l"], size=9),
    ]


def not_measured_blocks():
    return [
        P("The following were not measured, and nothing in the documents should be read as a result for them:"),
        B("Detection accuracy of a trained light-bar or emergency-vehicle model, and any temporal-confirmation logic (the base paper's three-frame rule).",
          "Violation-detection accuracy: there is no detector and no labelled violation data.",
          "Behaviour with a live camera stream, tracking, night-time, rain or glare conditions.",
          "Accuracy of the simulator against field counts, and any comparison with SUMO or CARLA.",
          "Safety outcomes such as conflicts or collisions, and effects on pedestrians or cyclists.",
          "Performance with many simultaneous users, long-running stability, and failure behaviour of the API.",
          "Security of the demo authentication (no penetration test); the signing key is a development default unless `.env` supplies one.",
          "Energy use and hardware cost of an edge deployment; the base paper's 11-14 ms detector latency was measured on a GPU and ours (about 32-51 ms) on a CPU, so they are not comparable."),
    ]


# ---------------------------------------------------------------------------- design walk-throughs and decisions
def walkthrough_blocks():
    return [
        H2("The advanced controller's decision rule (`sim.py`)"),
        P("`_decide` is called once per second for each junction that is not in its clearance interval. Emergency pre-emption comes first; otherwise the pressure of the current phase and of the other phase are compared, subject to the minimum and maximum green times."),
        CODE(src("smart_traffic/sim.py", 230, 266), 8),
        P("If an ambulance is waiting at the junction or arriving within the look-ahead (`_emergency_target`), its phase is forced after at least 2 s of the current green (the clearance interval of 3 s follows automatically). "
          "Otherwise the junction stays in its phase until the minimum green (13 s for the advanced controller, 15 s for the others), and switches when the current phase is empty and the other has demand, when the other pressure exceeds twice the current pressure plus four, or at the 60 s maximum."),
        H2("Pressure, forecast and spill-back (`_pressure`)"),
        CODE(src("smart_traffic/sim.py", 268, 284), 8),
        P("For the advanced controller the pressure of each approach is the PCU-weighted queue plus 0.7 times the forecast build-up (forecast queue minus queue now, never negative), plus the passenger-car units due within 8 s from the upstream junction, plus the head-of-queue waiting time divided by 12 s as a fairness term; "
          "the whole is multiplied by 0.3 when the straight-ahead downstream approach is within four vehicles of its capacity, which is the spill-back avoidance. The adaptive controllers use the PCU queue alone. The constants 0.7, 8, 12 and 0.3 were chosen by hand, not fitted."),
        H2("The forecaster (`predictor.py`)"),
        CODE(src("smart_traffic/predictor.py", 14, 29) + "\n...\n" + src("smart_traffic/predictor.py", 32, 56), 8),
        P("Training data is generated by running the simulator under the adaptive controller and storing the 11-feature matrix every 10 s from t = 40 s, labelled with the queue 30 s later. A gradient-boosting regressor (160 trees, depth 4, learning rate 0.08, subsample 0.9) is fitted on a random 75 % of the rows and compared with a random forest and with persistence on the other 25 %. "
          "The random split is the weakness identified in Chapter 8: rows from one simulation are near-duplicates, so the reported R2 is optimistic."),
        H2("The light-bar rule and density report (`vision.py`)"),
        CODE(src("smart_traffic/vision.py", 51, 68) + "\n...\n" + src("smart_traffic/vision.py", 127, 136), 8),
        P("Red and blue masks are taken in HSV, dilated and intersected so that only red and blue blobs that touch survive; each cluster gets a score from the balance and amount of red and blue pixels. A detected vehicle box becomes an *ambulance* when a cluster lies on its upper part with score above 0.25. "
          "`density_report` sums PCU, divides by an assumed capacity of 14 PCU, names the level and recommends a green time of 12 s if an ambulance is present and otherwise 12 + 3.2 times the PCU, clamped to 15-60 s."),
        H2("Serving a benchmark (`service.py`)"),
        CODE(src("backend/service.py", 266, 292), 8),
        P("The benchmark endpoint validates the request, checks the cache, then runs every controller for every seed with the same seeds (40 + i), so controllers see identical traffic. The advanced controller receives the shared trained predictor, and results are averaged over seeds before the key performance indicators are computed. "
          "Errors are raised as `ApiError` objects and rendered by one exception handler as `{detail: {message, hint}}`."),
        H2("Token authentication (`auth.py`)"),
        CODE(src("backend/auth.py", 27, 42), 8),
        P("The sign-in token is a three-part HS256 token built with the standard library (`hmac`, `hashlib`, `base64`); verification compares signatures in constant time and rejects expired tokens. The signing key is read from `.env` and falls back to a development key if it is missing or a placeholder."),
    ]


def decision_blocks():
    return [
        P("The table lists the main implementation decisions with the reason for each and the consequence that was observed."),
        TAB("Implementation decisions and their reasons", ["Decision", "Reason", "Consequence observed"],
            [["Build a pure-Python simulator instead of using SUMO", "Runs on any laptop with no installation, is seeded and deterministic, and lets four controllers run on identical demand in seconds (1800 s in 0.17-0.52 s)", "Fast iteration and a like-for-like benchmark; absolute numbers cannot be compared with SUMO studies"],
             ["Run all controllers on the same random demand", "A fair comparison needs the same vehicles and ambulances; demand uses its own random stream independent of control", "Differences between controllers are due to control; verified by a unit test"],
             ["Two-phase signals", "Keeps the state small and the pressure rule readable", "No turn-specific phases; limits realism"],
             ["PCU-weighted queues", "A bus occupies more road than a motorbike; PCU weights 1, 0.5, 3, 2 follow common practice", "Density and pressure account for vehicle mix"],
             ["Gradient boosting for the forecaster", "Strong on tabular features, small, trains in about 6 s at start-up, no GPU", "Random forest was equally good (MAE 1.609 against 1.642); neither extrapolates beyond training queues"],
             ["Train the forecaster on the adaptive controller's data", "Avoids feedback from the advanced controller's own decisions", "Used inside a different controller at run time, a small distribution shift"],
             ["Clip forecasts to 0-40 vehicles", "Prevents absurd values reaching the controller", "Hides large errors on congested runs"],
             ["Stock YOLOv8n with COCO weights", "No labelled light-bar data in the batch; the model downloads automatically and runs on a CPU at about 32 ms per frame", "Poor on two- and three-wheelers; no emergency class"],
             ["HSV red-plus-blue light-bar rule", "Simple, explainable, needs no training data; mirrors the base paper's cue", "Perfect on synthetic scenes, 1.3 % recall on real photographs"],
             ["Classical contour detector for synthetic scenes", "YOLOv8n cannot see rendered rectangles; gives a demo path without a dataset", "Brittle under noise; synthetic scores are in-domain only"],
             ["Violations generated by the simulator", "No labelled violation video available; shows the logging and evidence flow", "Must be described as simulated, not detected"],
             ["FastAPI with one shared live simulation", "One operator console needs one shared state; state kept in process memory", "No persistence; a restart creates a fresh simulation"],
             ["Standard-library HS256 token and a demo account", "No user database needed for a demonstration; keeps the install small", "Not suitable for production"],
             ["Predictor trains in a background thread at start-up", "The API starts immediately; routes that need the model return 503 with a hint until it is ready", "First use after start-up waits about 6-10 s"],
             ["Cache benchmark results by request key", "Repeat requests are free and the page feels instant", "First run of four controllers by three seeds takes about 4.8 s"],
             ["Measure on 127.0.0.1", "`localhost` adds about 2 s per call through an IPv6 fall-back on this machine", "Latency figures reflect the application, not the resolver"]],
            widths=[1.7, 2.7, 2.2], align=["l", "l", "l"], size=9),
    ]


# ---------------------------------------------------------------------------- chapter 9
def _lessons():
    full = ["**Compare against the right baseline.** Against fixed-time signals every adaptive idea looks good; the informative comparison is against plain queue-actuated control, and that is where the advanced controller's advantage shrinks to about 4-5 %. A project that reports only the first comparison overstates its contribution.",
        "**Validate the way the system will be used.** A random train and test split gave a forecaster R2 of 0.96; holding out whole simulation runs gave 0.04. The first number is what the product screen shows; the second is closer to what an operator would meet on a new, more congested day.",
        "**Do not trust one's own test data.** The synthetic scenes were drawn by the same code that detects the vehicles in them, and the detector scored 0.976 recall and 1.000 ambulance recall; on real photographs the same rule scored 0.013. Real images, however few, changed the conclusion about emergency detection.",
        "**Say what is simulated.** Violations, plates, confidences and the knowledge of where an ambulance is are all generated inside the simulator. Labelling them as such in the interface, the tests and the documents prevents the demonstration from being read as detection.",
        "**Seeds matter.** Five seeds already show that the ordering of fixed-time, adaptive and advanced control is stable, and that the distance between adaptive and advanced is not; three seeds produced the -38 % on the benchmark screen, five give -34.8 %.",
        "**Measure the cost of safety features.** Pre-emption was assumed to be nearly free; the base-paper-style controller is slower than plain adaptive control for everyone else, and the ablation shows the network is fastest with no pre-emption at all."]
    if F.REPORT:
        return [full[0], full[1], full[2], full[3]]
    return full


def _greenwave():
    if F.REPORT:
        return []
    return ["**The route-wide green wave helps ambulances most on larger grids.** On the 3x3 grid the advanced controller's ambulance delay is 24.9 % below the one-junction pre-emption (5.6 against 7.5 s); on the 2x2 grid the gain is 4.2 %."]


def conclusion_blocks():
    d2, d3 = _d("2x2"), _d("3x3")
    return [
        H2("9.1 Summary of the work"),
        P(f"FlowSense was built to show, in one working product, the chain that the batch abstract describes: detect vehicles, forecast congestion, adapt signal timing, give emergency vehicles priority, coordinate neighbouring junctions and log violations. "
          f"The product consists of a seeded traffic-network simulator with four signal controllers, a YOLOv8n vision layer with a light-bar rule and a density estimate, a gradient-boosting queue forecaster, a violation log, and a FastAPI and React console. "
          f"It is grounded in the base paper [{R['base']}], whose emergency-aware supervisory layer it emulates and extends with forecasting and route-wide coordination."),
        P("The work was evaluated, not just demonstrated. Four controllers were compared on identical seeded traffic for five seeds, with a demand sweep, an emergency-heavy test and an ablation; the forecaster was validated by leaving whole simulation runs out; and the vision layer was measured on rendered scenes, on 293 real dashcam frames and on 600 real ambulance and non-ambulance photographs."),
        H2("9.2 Objectives achieved"),
        TAB("The eight objectives and their status", ["Objective", "Status", "Headline evidence"],
            [["Vehicle detection and classification with YOLOv8", "Partly achieved", "32 ms per frame on a CPU; real-frame recall 0.586 (4-wheelers), 0.083 (2-wheelers), 0 (3-wheelers)"],
             ["Dynamic signal timing from density", "Achieved in simulation", f"Delay -{d2['delay_cut_advanced_vs_fixed_pct']:.1f} % (2x2), -{d3['delay_cut_advanced_vs_fixed_pct']:.1f} % (3x3) against fixed-time"],
             ["Emergency-vehicle priority", "Achieved in simulation; detection not", f"Ambulance delay -{d2['emergency_cut_advanced_vs_fixed_pct']:.1f} % and -{d3['emergency_cut_advanced_vs_fixed_pct']:.1f} % against fixed-time; light-bar recall 0.013 on real photos"],
             ["Congestion prediction", "Partly achieved", "MAE 1.64, R2 0.96 (random split); R2 0.04 across held-out runs"],
             ["Inter-junction coordination", "Partly achieved", "Implemented in simulation; measured effect small"],
             ["Violation detection", "Partly achieved", "Simulated events logged; no detector"],
             ["Reduce waiting, congestion and fuel", "Achieved in simulation", "Queue 96.3 to 61.3 veh; idle fuel 28.9 to 18.4 L per run (2x2)"],
             ["Road safety and efficiency", "Not measured", "No safety metric exists"]],
            widths=[2.2, 1.5, 2.9], align=["l", "l", "l"], size=9.5),
        H2("9.3 Key findings"),
        N(f"**Adaptivity is what matters for general traffic.** Queue-actuated control already removes about a third of the delay of fixed-time signals; the advanced controller adds only {d2['delay_cut_advanced_vs_adaptive_pct']:.1f} % (2x2) and {d3['delay_cut_advanced_vs_adaptive_pct']:.1f} % (3x3), within one standard deviation, and is worse at low demand.",
          "**Pre-emption saves ambulance time and costs everyone else a little.** Ambulance delay falls by about 70-87 % against fixed-time; the base-paper-style controller is slower than plain adaptive control for general traffic, and without any pre-emption the network is fastest (42.4 s) but ambulances wait 27.3 s.",
          *_greenwave(),
          "**The forecaster looks better than it is.** The random-split R2 of 0.96 collapses to 0.04 when whole runs are held out, because trees cannot extrapolate to unseen congestion; its closed-loop value is about 3 s of delay.",
          "**Synthetic vision success does not transfer.** The light-bar rule found every ambulance in rendered scenes and 4 of 300 in real photographs; the stock detector misses most two-wheelers and all three-wheelers in real mixed traffic. On inspection, the four ambulance photographs the rule flagged were flagged on red and blue livery, a flag graphic and a star-of-life, not on roof lights, so even 4 of 300 overstates it.",
          "**Evaluation design changes conclusions.** The three-seed benchmark screen shows -38 % against fixed-time; five seeds give -34.8 %; the demand sweep shows where the advanced controller is worse; the real-image tests overturn the synthetic ones."),
        H2("9.4 Practical applications"),
        B("A teaching and planning tool for comparing signal strategies on identical traffic before touching a real junction, including how much delay an ambulance green wave costs other traffic.",
          "A demonstrator of an end-to-end camera-to-signal architecture and a baseline for the next stage: fine-tuned detection, calibrated simulation and hardware-in-the-loop trials."),
        H2("9.5 Known limitations"),
        P("The simulator is not SUMO and is uncalibrated; the emergency detector is not trained and fails on real photographs (its few hits were livery colours, not lights); vehicle detection is a stock COCO model that misses two- and three-wheelers; violations are simulated; the advanced controller's benefit over plain adaptive control is small; the forecaster does not generalise to unseen congestion; and nothing was tested with real cameras, signal hardware or many users. "
          "These limitations are listed with their evidence in Chapters 8 and 10, and they define the future work below."),
        H2("9.6 Lessons learned"),
        B(*_lessons()),
        H2("9.7 Concluding remarks"),
        P("FlowSense demonstrates that a complete, inspectable smart-traffic pipeline can be built, run on an ordinary computer and evaluated on identical traffic: adaptive control removes about a third of the delay of fixed-time signals, ambulance delay can be cut by about three quarters or more when the signals look ahead for them, and a forecast and a coordinated look-ahead add a smaller, measurable benefit. "
          "It also shows, with numbers, where such a project is weak: the perception components were not trained for the task and do not hold up on real photographs, the simulator is not calibrated, and the violation module is a simulation of enforcement. "
          "The honest reading of the work is therefore a validated control framework with a working console and a clear list of what must be replaced by real data, a trained emergency detector and field calibration before any claim about real roads could be made."),
    ]


def _concl_trim(bl):
    """Compact variant for the full report: no 'practical applications' list, six findings kept as five, shorter closing remark."""
    out, skip = [], False
    for b in bl:
        if b[0] == "h2":
            skip = b[1].startswith("9.4")
        if skip and not (b[0] == "h2" and not b[1].startswith("9.4")):
            continue
        if b[0] == "n":
            b = ("n", [x for x in b[1] if not x.startswith("**Evaluation design changes")])
        elif b[0] == "p" and b[1].startswith("FlowSense demonstrates that a complete"):
            b = ("p", b[1].split(" It also shows")[0] + " It also shows, with numbers, where the project is weak: the perception components were not trained for the task and do not hold up on real photographs, the simulator is not calibrated, and the violation module simulates enforcement. "
                 "The honest reading is a validated control framework with a working console and a clear list of what real data, a trained emergency detector and field calibration must still supply.")
        out.append(b)
    return out


def chapter9_blocks():
    from .blocks import renum
    return [H1("CHAPTER 9: CONCLUSION")] + renum(_concl_trim(conclusion_blocks()), "9")


# ---------------------------------------------------------------------------- chapter 10
def future_blocks():
    return [
        H2("10.1 Improvements to the existing system"),
        N("**Train a dedicated emergency detector.** Fine-tune YOLO on a light-bar or emergency-vehicle data set (the base paper's 3,130-image approach, or public siren and ambulance data), evaluate precision, recall and mAP, and replace the HSV rule. The target is the base paper's precision 0.73, recall 0.69 and mAP50 0.73, measured on real photographs rather than rendered scenes.",
          "**Fine-tune vehicle detection on local traffic.** Fine-tune on mixed-traffic data with a 3-wheeler class (such as the 293-frame set used in Chapter 8, extended) and measure the gain over the stock model's recall of 0.083 for two-wheelers and 0 for three-wheelers.",
          "**Close the loop.** Feed the detector's confirmed detections (a confidence threshold with a short temporal confirmation window, as in the base paper) and the PCU density into the controller instead of ground-truth knowledge in the simulator.",
          "**Make the forecaster robust.** Train on a wider range of demand including heavily congested runs, use models that extrapolate (linear trend terms, sequence models), report leave-one-run-out validation by default, and choose the forecast weight by demand level so that the advanced controller does not lose to adaptive control at low demand.",
          "**Tune and justify the controller constants** (0.7, 8 s, 12 s, 0.3, minimum and maximum green) by systematic search on one set of seeds and testing on another, and compare against max-pressure control and learned policies [%d], [%d]." % (R["varaiya"], R["intellilight"])),
        H2("10.2 Additional features"),
        B("**Multi-phase signals** with protected turns, pedestrian phases and bus priority, and a signal-timing output that respects local standards.",
          "**Real violation detection**: red-light and wrong-way detection from video with tracking and number-plate recognition, evaluated on labelled clips, replacing the simulated log.",
          "**Persistence and roles**: a database for events and configurations, operator and administrator roles, audit logging.",
          "**Alerting and reports**: scheduled benchmark reports, exportable evidence packs, notifications when a junction is pre-empted.",
          "**More emergency cues**: siren audio and flashing-state analysis to complement the light-bar, as suggested by the base paper's own limitations."),
        H2("10.3 Scalability and deployment"),
        B("**SUMO and TraCI port.** Re-implement the controllers against SUMO, calibrate against counts from a real corridor, and compare directly with the base paper's roundabout study [%d]." % R["base"],
          "**Camera ingestion.** RTSP or file ingestion with frame sampling, batching and a bounded queue; one detector process per camera or a shared GPU worker.",
          "**Edge deployment.** Export the detector (ONNX or TensorRT), measure latency on an embedded GPU, and keep the forecaster and controller on a small controller box; the base paper's 11-14 ms was on a GPU, ours is about 32-51 ms on a CPU.",
          "**Distributed coordination.** Replace look-ahead on a shared simulation state with messages between junction controllers (V2I or a publish-subscribe link), and test with delayed and lost messages.",
          "**Operations.** Containerise the API and console, add health probes and metrics, run load tests with many operators, and replace the demo token with a standard identity provider."),
        H2("10.4 Further research"),
        B("Compare the advanced pressure rule with reinforcement-learning controllers [%d] and with graph-neural-network traffic models such as the archived second candidate base paper [%d] on the same benchmark." % (R["intellilight"], R["necdm"]),
          "Study the efficiency-safety trade-off of pre-emption formally: how many seconds of general delay is an ambulance second worth, as a function of demand and grid size.",
          "Evaluate the accuracy of detectors trained on synthetic scenes when transferred to real cameras, and whether realistic rendering closes the gap measured here.",
          "Quantify fuel and emissions with a proper emissions model instead of an idling-rate assumption, and add safety surrogate measures such as time-to-collision."),
        H2("10.5 Proposed roadmap"),
        P("The improvements above are ordered below so that each stage removes a limitation measured in Chapter 8 and has a success measure that can be checked with the scripts already in the repository."),
        TAB("Roadmap from the present system to a field-ready study", ["Stage", "Work", "Limitation removed", "Success measure"],
            [["1. Perception", "Fine-tune YOLO on a local mixed-traffic set with a 3-wheeler class; train a light-bar or emergency-vehicle detector on real photographs", "Stock detector (2-wheeler recall 0.083, 3-wheeler 0.000); light-bar rule recall 0.013", "Precision, recall and mAP50 on a held-out real set at or above the base paper's 0.73 / 0.69 / 0.73 for the emergency class; vehicle recall for 2- and 3-wheelers above 0.5"],
             ["2. Closed loop", "Feed detections and PCU density into the controllers with a temporal-confirmation rule; remove ground-truth knowledge of ambulances", "Ground-truth emergency knowledge", "Ambulance delay with detected (not known) ambulances within 20 % of the ground-truth case in the benchmark"],
             ["3. Robust forecasting", "Wider training demand, extrapolating models, leave-one-run-out reporting, demand-dependent forecast weight", "Held-out R2 0.04; worse than adaptive at low demand", "Held-out MAE below persistence on every fold; advanced controller no worse than adaptive at x0.6"],
             ["4. Calibrated simulation", "Port to SUMO/TraCI, calibrate with counts from a real corridor, add pedestrian and turn phases", "Uncalibrated, two-phase simulator", "Simulated flows within an agreed tolerance of counted flows; results repeated in SUMO"],
             ["5. Real data pipeline", "RTSP ingestion, tracking, number-plate recognition on labelled clips, persistence and roles", "Simulated violations; demo login; in-memory state", "Violation detector precision and recall on labelled clips; audit log of every event"],
             ["6. Pilot", "Edge deployment and hardware-in-the-loop on a single junction with the authority's approval", "No hardware tests", "Detector latency and signal-command latency measured on the device; safe fall-back to fixed-time verified"]],
            widths=[0.9, 2.1, 1.6, 2.0], align=["l", "l", "l", "l"], size=9),
        P("Stages 1 to 3 can be completed on the existing code base and a workstation; stages 4 to 6 need field data, traffic-authority cooperation and hardware, and should not be started before the first three show that the perception and forecasting components hold up on real data."),
    ]


def _future_trim(bl):
    """Compact variant for the full report (the chapter document 15 keeps everything)."""
    if not F.REPORT:
        return bl
    out = []
    for b in bl:
        if b[0] == "n" and b[1][0].startswith("**Train a dedicated emergency detector"):
            b = ("n", b[1][:4])
        elif b[0] == "b" and b[1][0].startswith("**Multi-phase"):
            b = ("b", b[1][:3])
        elif b[0] == "b" and b[1][0].startswith("**SUMO and TraCI"):
            b = ("b", b[1][:3])
        elif b[0] == "b" and b[1][0].startswith("Compare the advanced pressure"):
            b = ("b", b[1][:2])
        elif b[0] == "tab" and b[1].startswith("Roadmap"):
            rows = b[3][:3] + [["4-6. Field readiness", "Port to SUMO/TraCI and calibrate; RTSP ingestion, tracking, plate recognition, persistence; edge deployment and hardware-in-the-loop pilot at one junction",
                               "Uncalibrated simulator; simulated violations; in-memory state; no hardware tests",
                               "Results repeated in SUMO within an agreed tolerance of counted flows; detector and signal-command latency measured on the device; safe fall-back to fixed-time verified"]]
            b = ("tab", b[1], b[2], rows) + tuple(b[4:])
        out.append(b)
    return out


def chapter10_blocks():
    return [H1("CHAPTER 10: FUTURE SCOPE")] + _future_trim(future_blocks())
