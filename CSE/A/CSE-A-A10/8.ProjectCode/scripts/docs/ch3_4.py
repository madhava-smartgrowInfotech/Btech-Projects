"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis) for FlowSense."""

from . import facts as F
from . import lit
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def lat(prefix):
    """Mean API latency (ms) of the endpoint whose label starts with prefix."""
    for r in F.API["results"]:
        if r["endpoint"].startswith(prefix):
            return r["mean_ms"]
    raise KeyError(prefix)


def _speed(key):
    return F.TH[key]["speedup"]


def blocks():
    return chapter3() + chapter4()


# =====================================================================================================================
def chapter3():
    yolo = F.VY["sample_photo"]
    d2 = F.derived("2x2")
    slowest = min(_speed(k) for k in ("2x2/fixed", "2x2/advanced", "3x3/fixed", "3x3/advanced"))
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        H2("3.1 Introduction"),
        P("This chapter asks whether FlowSense can be built, run and maintained with the resources at hand, partly by argument and partly by building the system and measuring it on a six-core desktop with no graphics card."),
        H2("3.2 Technical Feasibility"),
        P("**Hardware.** Every measurement in this report was taken on an Intel Core i5-12500 (6 cores, 12 threads) with 15.7 GB of memory and integrated graphics, running Windows 11. "
          "No CUDA graphics card was used, so the project demonstrates that the whole pipeline runs on an ordinary office PC. Lower-specification machines were not tested."),
        P("**Software.** All components are mature open-source packages: Python 3.11, NumPy, pandas, scikit-learn, OpenCV, PyTorch and Ultralytics for the engine and vision layer, FastAPI and "
          "Uvicorn for the API, and React with Vite, Tailwind and Recharts for the console. Every package installs from the public package indexes; `run.bat` creates the environment and starts both servers."),
        P("**Data.** The control layer needs no external dataset, because the simulator generates demand from a seed; the only datasets are the two public image sets used to test the vision layer. "
       "This removes the usual feasibility risk of a data-driven project (not enough labelled data) but moves the risk to validity: the generated demand is only as realistic as its assumptions."),
     P("**Evidence from measurement.** The feasibility of each technical risk was tested directly:"),
        TAB("Technical risks and the measurements that retired them", ["Risk", "Measurement", "Verdict"],
            [["Simulation too slow for interactive use", f"A 1,800 s run takes 0.17-0.52 s of wall time; slowest case {slowest:,.0f} times real time", "Feasible"],
             ["Machine-learning forecast too slow inside the control loop", f"Forecaster fit {F.PR['shipped_fit']['fit_seconds']:.1f} s at start-up; prediction of 16 rows {F.TH['predictor_batch16_ms']:.2f} ms", "Feasible"],
             ["YOLOv8 too slow without a GPU", f"{yolo['latency_ms_mean']:.1f} ms mean per 1080x810 photo on CPU ({F.VR['mixed_traffic']['latency_ms_mean']:.1f} ms per 640x480 frame)", "Feasible for stills; live video untested"],
             ["API too slow for a live console", f"Advance 2 s: {lat('live step 2 s'):.1f} ms; advance 300 s: {lat('live step 300 s'):.0f} ms; first four-controller benchmark {lat('POST /api/benchmark (4 ctrl')/1000:.1f} s", "Feasible"],
             ["Vision accurate enough on real frames", f"YOLOv8n recall {F.VR['mixed_traffic']['per_class']['4-wheeler']['recall'] * 100:.0f} % (four-wheelers) and {F.VR['mixed_traffic']['per_class']['2-wheeler']['recall'] * 100:.0f} % (two-wheelers) on real dashcam frames", "Not feasible as shipped; needs fine-tuning"],
             ["Light-bar rule works on real photos", f"{F.VR['ambulance_classification']['ambulance_flag_yolo_plus_lightbar']['tp']} of {F.VR['ambulance_classification']['ambulance_images']} real ambulance photos flagged", "Not feasible as a colour rule; needs a trained detector"]],
            widths=[2.0, 3.2, 1.3], align=["l", "l", "l"], size=9.5),
        P("**Environment risks that did occur.** On Windows, PyTorch's native libraries fail to initialise (`WinError 1114`) if scikit-learn or OpenCV are imported first, so `backend/main.py` imports `torch` first; and installing the YOLO package upgraded PyTorch to 2.14.1, so the launcher installs the engine and YOLO packages in two steps and keeps every other page working if the second fails."),
        H2("3.3 Economic Feasibility"),
        P("No prices are quoted because none were invented for this project. All software is open source with no licence fee (Python, PyTorch, Ultralytics, OpenCV, scikit-learn, FastAPI, React); "
          "development and testing used one existing desktop PC; the two image sets are free under CC BY 4.0; and the simulator was written in-house, so no SUMO or CARLA set-up was needed. "
          "Cameras and a signal-controller interface are not part of this project and are not costed."),
        P(f"**Benefit.** Over a 30-minute run on a 2x2 grid the advanced controller wastes {d2['fuel_saved_L_advanced_vs_fixed_per_run']:.1f} litres less fuel idling than fixed-time signals, an assumption-driven figure "
          "(queued vehicles are assumed to burn 0.6 litres per hour) that describes the model, not a measured saving on a road. The cost of reproducing and extending this work is low; "
          "the cost of real junctions would be dominated by cameras, controller integration and safety approval."),
        H2("3.4 Operational Feasibility"),
        B("**Operators.** A single-role console shows the map, queue, forecast, alert log and benchmark without command-line use.",
          "**Installation.** `run.bat` creates a virtual environment, installs packages and starts the API (port 8310) and the console (port 5310).",
          "**Maintenance.** The engine is about 700 lines in three modules and every reported number is written by a script, so a controller change can be re-measured with one command.",
          "**Acceptance.** The project has not been trialled with traffic police or a signal authority; operational acceptance by real operators is not claimed."),
        H2("3.5 Schedule Feasibility"),
        P("The work ran in seven overlapping phases; the original calendar dates were not recorded, so the table gives relative weeks."),
        TAB("Work packages in the order they were carried out", ["Phase", "Work", "Weeks"],
            [["1", "Problem study, base-paper reading, literature survey", "1-3"],
             ["2", "Architecture and data-flow design; simulator rules", "3-5"],
             ["3", "Simulator and four controllers; benchmark runner", "5-8"],
             ["4", "Vision layer (YOLOv8, light-bar rule, density) and queue forecaster", "7-10"],
             ["5", "FastAPI service, React console, authentication", "9-12"],
             ["6", "Experiments, unit and API tests, real-image evaluation", "12-14"],
             ["7", "Diagrams, screenshots, report, decks and paper", "13-15"]],
            widths=[0.7, 4.6, 1.2], align=["c", "l", "c"], size=10.5),
        H2("3.6 Legal, Ethical and Safety Feasibility"),
        B("**Privacy and licensing.** The project never handles private footage: demand is generated, plate strings are random, and the two public image sets (CC BY 4.0) are anonymised by their publishers. Ultralytics and the YOLOv8 weights are AGPL-3.0, fine for academic use but needing a licensing review before commercial deployment.",
          f"**Safety.** Overriding signals on a public road needs authorisation and safety clearance, as the base paper [{R['base']}] also notes. FlowSense stays in simulation; a pilot would need a fail-safe that returns the junction to a fixed plan when sensing fails, which the current build does not implement."),
        H2("3.7 Risk Assessment"),
        TAB("Principal risks and how they were handled", ["Risk", "Likelihood", "Impact", "Handling"],
            [["Controller looks good only on one random seed", "Medium", "High", "Five seeds, mean and standard deviation; per-seed values stored"],
             ["Synthetic vision accuracy overstates real accuracy", "High", "High", "Real-image evaluation on two public sets; failures reported"],
             ["Forecaster fails outside its training range", "High", "Medium", "Leave-one-simulation-out test; forecast used as one term among several, clipped to 40"],
             ["Pre-emption harms ordinary traffic", "Medium", "Medium", "Ablation and emergency-heavy test measure the network cost"],
             ["Misreading simulation as field evidence", "Medium", "High", "Every chapter states that the simulator is not SUMO and not a road trial"]],
            widths=[2.4, 0.9, 0.8, 2.4], align=["l", "c", "c", "l"], size=9.5),
        H2("3.8 Advantages and Constraints"),
        H3("3.8.1 Advantages"),
        B("The system runs on one PC and every result is reproducible from a seed.",
          f"Adaptive timing lowers delay by about a third against fixed-time signals ({d2['delay_cut_advanced_vs_fixed_pct']:.1f} % on a 2x2 grid); four controllers on identical demand and an ablation isolate each idea.",
          "A web console makes the behaviour visible to non-programmers."),
        H3("3.8.2 Constraints"),
        B("Simulation is not the road: its demand, saturation flow and link times are assumptions, and it is not SUMO.",
          "The vision layer is stock YOLOv8n without fine-tuning and a colour rule for light-bars; both fail on real data to a degree measured in Chapter 8.",
          "Emergency vehicles and violations are known to the simulator; no real camera feed drives the control loop.",
          "No database, one demo user, no hardware integration."),
    ]


def chapter4():
    a2 = F.gm("2x2", "advanced", "Avg delay / vehicle (s)")
    f2 = F.gm("2x2", "fixed", "Avg delay / vehicle (s)")
    base = R["base"]
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Existing System"),
        P("Most junctions today are controlled by a fixed-time plan, or by a plan with local vehicle actuation, that does not know about the neighbouring junction or about emergency vehicles. "
          "The existing practice and research systems fall into the groups below."),
        B(*lit.EXISTING_SYSTEM),
        H2("4.2 Limitations of the Existing System"),
        B(*lit.LIMITATIONS_OF_EXISTING),
        H2("4.3 Proposed System"),
        P(f"FlowSense is one pipeline in which the stages feed each other. A vision layer detects vehicles (YOLOv8n) and flags emergency vehicles by a roof light-bar rule, and converts the detections into a "
          "density level and a recommended green time in passenger-car units. A forecaster predicts each approach's queue 30 seconds ahead from eleven features. A controller combines "
          "queue pressure, the forecast, vehicles already on the road to the junction and the waiting time of the head of the queue into one score per phase, damps it when the downstream link "
          "is nearly full, and overrides it for an approaching ambulance, extending the override along the route as a green wave. Violations are logged with a plate and a time. "
          "A FastAPI service exposes all of it and a React console presents it."),
        P(f"On identical seeded traffic on a 2x2 grid, the proposed controller averages {a2[0]:.1f} s of delay per vehicle against {f2[0]:.1f} s for fixed-time signals (five seeds)."),
     H2("4.4 Advantages of the Proposed System"),
        B("One product covers detection, forecasting, priority, coordination and violation logging, with four controllers benchmarked on identical demand so the gain of each idea is isolated.",
          "Emergency vehicles are served in a few seconds in the simulator; every number is script-generated and guarded by tests; failure modes are measured and reported."),
        H2("4.5 Functional Requirements"),
        TAB("Functional requirements and where they are implemented", ["ID", "Requirement", "Implementation"],
            [["FR1", "Sign in with a demo operator account; reject bad credentials with a readable message", "POST /api/auth/login, GET /api/auth/demo"],
             ["FR2", "Run a live simulation of a 2x2 or 3x3 junction grid; choose controller, demand, emergencies and ML on/off", "GET /api/live, PUT /api/live/config"],
             ["FR3", "Advance the simulation by 1 to 900 seconds, reset it, and inject an ambulance", "POST /api/live/step, /reset, /ambulance"],
             ["FR4", "Show the road map with signal states and queues, junction table and queue chart", "Live control page"],
             ["FR5", "Compare four controllers on identical demand over 1 to 5 seeds, with mean and spread", "POST /api/benchmark"],
             ["FR6", "Show delay against demand for all controllers", "POST /api/benchmark/sweep"],
             ["FR7", "Detect vehicles in a synthetic scene, a bundled photo or an uploaded image (JPG or PNG up to 12 MB) and report density, PCU and recommended green time", "GET /api/vision/synthetic, /sample; POST /api/vision/analyze"],
             ["FR8", "Flag an emergency vehicle by its red-blue light-bar", "smart_traffic/vision.py (detect_lightbars)"],
             ["FR9", "Forecast the queue of every approach 30 s ahead and report model quality", "GET /api/prediction, /api/prediction/live"],
             ["FR10", "Pre-empt signals for an emergency vehicle and coordinate neighbouring junctions", "Advanced and emergency controllers"],
             ["FR11", "Log red-light and wrong-way violations with plate, junction, time and confidence", "GET /api/violations"],
             ["FR12", "Report idling fuel and CO2 for each controller", "Benchmark summary"]],
            widths=[0.5, 3.7, 2.3], align=["c", "l", "l"], size=9.5),
        P("All twelve are met in the delivered build with the qualifications of Chapter 1: FR7 and FR8 run on stills, FR8 fails on real ambulance photographs, FR10 relies on ground-truth emergency knowledge and FR11 logs simulated events."),
     H2("4.6 Non-Functional Requirements"),
        TAB("Non-functional requirements, targets and measurements", ["Quality", "Requirement", "Measured"],
            [["Performance", "Live step of 2 s answered well under a second; benchmark in seconds", f"{lat('live step 2 s'):.1f} ms (2 s step); {lat('POST /api/benchmark (4 ctrl') / 1000:.1f} s first benchmark; {lat('POST /api/benchmark (cached') :.1f} ms when cached"],
             ["Throughput", "Simulation faster than real time by a large margin", f"At least {min(_speed(k) for k in ('2x2/fixed', '2x2/advanced', '3x3/fixed', '3x3/advanced')):,.0f}x real time"],
             ["Vision speed", "A frame in well under a second on CPU", f"{F.VY['sample_photo']['latency_ms_mean']:.1f} ms mean (YOLOv8n, sample photo)"],
             ["Reliability", "Engine and API behave as specified", f"{F.PYTEST_PASSED} of {F.PYTEST_TOTAL} tests and {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} smoke checks pass"],
             ["Security", "Protected routes need a token; inputs validated; uploads limited", "HS256 token expiring after 12 h; 401 without token; 422 on invalid input; 12 MB upload cap"],
             ["Usability", "Demo account shown on the sign-in page; light and dark themes", "Shown on /login; theme toggle"],
             ["Portability", "One launcher on Windows", "run.bat (tested on Windows 11)"],
             ["Maintainability", "Business logic separated from the API", "smart_traffic/ (engine) and backend/ (API) packages"],
             ["Not measured", "Concurrent users, long-run stability, availability", "Not tested"]],
            widths=[1.2, 2.7, 2.6], align=["l", "l", "l"], size=9.5),
        P("Even the slowest simulator configuration runs thousands of times faster than real time; the first YOLO call and the first benchmark are slower (weights loading; four controllers x seeds) and the benchmark is then cached. Availability, concurrency and long-run stability were not measured."),
        H2("4.7 Interface Requirements"),
        P("The console talks to the API through JSON over HTTP with the token in an `Authorization: Bearer` header. Protected routes answer 401 without a valid token, invalid input 422, an image over 12 MB 413, a non-image 415, "
          "a request while the predictor trains 503 and a YOLO failure 502, all as `{detail: {message, hint}}` so the console shows one kind of error banner."),
        H2("4.8 Hardware Requirements"),
        TAB("Hardware used and recommended", ["Item", "Used for all measurements", "Remark"],
            [["Processor", "Intel Core i5-12500, 6 cores / 12 threads", "A comparable modern multi-core CPU is recommended"],
             ["Memory", "15.7 GB", "YOLOv8 and PyTorch need several GB when loaded"],
             ["Graphics", "Integrated Intel UHD 770; no CUDA GPU", "A GPU would speed up YOLOv8; it was not needed"],
             ["Disk", "A few GB", "PyTorch and Ultralytics are the largest packages"],
             ["Camera, signal controller", "Not used", "Required only for a pilot, not for this project"]],
            widths=[1.4, 2.7, 2.4], align=["l", "l", "l"], size=10),
        H2("4.9 Software Requirements"),
        TAB("Software stack and versions used", ["Layer", "Package", "Version"],
            [["Operating system", "Windows 11 Pro", "10.0 (build 26300)"],
             ["Language", "Python", "3.11.9"],
             ["Engine", "NumPy / pandas / scikit-learn", "1.26.4 / 2.2.1 / 1.5.0"],
             ["Vision", "OpenCV / Ultralytics / PyTorch (CPU)", "4.11.0 / 8.4.186 / 2.14.1"],
             ["API", "FastAPI with Uvicorn", "0.143.3 / 0.54.0"],
             ["Console", "React / Vite / Tailwind / Recharts", "19 / 8 / 4 / 3"],
             ["Runtime for the console", "Node.js", "24.19.0"],
             ["Testing", "pytest / FastAPI TestClient", "8.2.0"]],
            widths=[1.6, 3.2, 1.7], align=["l", "l", "l"], size=10.5),
        H2("4.10 User Roles and Usage Scenarios"),
        P("FlowSense has one role, the **operator**. The operator signs in with the demo account (`operator@flowsense.app`; the password is shown on the sign-in page), controls the live simulation, runs benchmarks, "
          "uses the vision page, reads forecasts and reviews the violation log. There is no administrator role, no user registration and no per-user data; all sessions share one simulation. "
          "A production system would need role separation between operators and administrators, which is listed as future scope."),
        H3("4.10.1 Usage scenarios"),
        B("**Morning peak and ambulance.** The operator picks the 3x3 network, raises demand to 1.6 and presses Run live; queues build on the busiest approaches and the junction table shows the 30-second forecast beside the current queue. Send ambulance makes the banner report pre-emption with the advanced or emergency controller and \"ignored\" with fixed or adaptive.",
          "**Choosing a controller.** The Benchmark page compares the four controllers on delay, ambulance delay, fuel and CO2, with spread over seeds.",
          "**Camera frame and violations.** The Vision page returns detections, PCU density and a recommended green time for an uploaded frame; the Violations page lists logged events by junction and minute."),
        H2("4.11 Constraints and Assumptions"),
        B("The sign-in is a demonstration, not an identity system; state lives in memory and is lost on restart.",
          "Traffic is simulated, with Poisson arrivals shaped by two daily peaks and a fixed vehicle mix; real arrivals are burstier and platoons are shaped by upstream signals.",
          "Signals have two phases (north-south, east-west) with 3 s clearance; real junctions often have protected turn phases.",
          f"Emergency vehicles are visible to the simulated controllers by ground truth; with the real detector the base paper reports precision 0.73 and recall 0.69 [{base}], and FlowSense's own rule is weaker.",
          "Datasets used for the real-image evaluation are public, CC BY 4.0, and anonymised by their publishers; plate strings in the violation log are random and refer to no real vehicle."),
        P("The next chapter turns these requirements into a design."),
    ]
