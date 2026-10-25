"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis)."""

from . import facts as F
from .blocks import B, H1, H2, N, P, TAB
from .refs import CITE as R


def c(*keys):
    return ", ".join(f"[{R[k]}]" for k in keys)


def blocks():
    return chapter3() + chapter4()


def report3():
    return chapter3()


def report4():
    return chapter4()


def chapter3():
    e = F.ENDPOINTS
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P("A feasibility study asks whether the system can be built with the available technology, at an acceptable cost, in a form people can operate, and within the time available. "
          "This chapter answers the four questions for ResQAI and then lists the advantages the study found and the constraints that remain. Where the answer rests on a measurement, the measurement is quoted from Chapter 8."),

        H2("3.1 Technical Feasibility"),
        P("The system needs a way to obtain sensor readings, two classifiers, a small web back end, a browser interface, a map and a hospital lookup. Each of these exists as mature, freely available software, and the project uses only that."),
        TAB("Technical building blocks and the evidence that each works",
            ["Need", "Technology used", "Evidence from the project"],
            [["Motion-feature classifiers", f"scikit-learn random forests {c('sklearn', 'breiman')}", f"Detector and severity models trained on {F.N_TRAIN:,} events; the two pickles total about 2.9 MB; one prediction takes {F.INF['mean']:.1f} ms in process"],
             ["Back end and API", "Flask 3.1 on Python 3.11, joblib model loading", f"POST /api/predict averages {e['POST /api/predict']['mean']:.1f} ms over HTTP on loopback (95th percentile {e['POST /api/predict']['p95']:.1f} ms)"],
             ["Accounts and security", f"werkzeug scrypt hashes {c('scrypt')}, itsdangerous signed tokens", f"{F.TESTS['by_group']['security']['passed']} of {F.TESTS['by_group']['security']['total']} security checks pass"],
             ["Console", f"React 19 and Vite 8 {c('react')}, Leaflet map, Recharts trace", "Production build succeeds in about 3.6 s; the smoke test serves the app shell"],
             ["Location", "Browser Geolocation API and haversine distance " + c("haversine"), "Nearest-k ranking matches brute force on 500 random points (0 mismatches)"],
             ["Sensor input", "Simulated by /api/simulate; a phone would send the same 11 fields", "Real phone sensing was not built (Chapter 10)"]],
            widths=[1.3, 2.3, 2.9], align=["l", "l", "l"], size=9.5),
        P("The one technical element that is not demonstrated is real sensing. A phone browser can read the accelerometer and gyroscope through standard web APIs, and a native application can do it continuously, "
          "but neither was built. The classifiers therefore rest on a generator, and the question that is open is whether their features, which are the physical quantities a phone reports, separate crashes from road-surface events on real data. "
          "The technology to find out is available; the data are not yet."),
        P(f"The development machine, a Windows 11 PC with an Intel Core i5-12500 processor and 15.7 GB of memory and no graphics card, was enough for training, evaluation and the full console. The complete evaluation script, which retrains the models many times for the five-seed repeat, the baselines and the feature ablation, ran in "
          f"{F.M['elapsed_s']:.0f} seconds. Technical feasibility is therefore established for the processing pipeline and not yet for the sensing front end."),

        H2("3.2 Economic Feasibility"),
        P("All software used is open source and free of licence charge. Development needed only a personal computer and a web browser. The cost of the delivered prototype to its builders is therefore the time of the team, and its running cost on a laptop is negligible."),
        TAB("Cost view of the prototype and of a real deployment (qualitative; no price figures were gathered)",
            ["Item", "Prototype (this project)", "Real deployment would need"],
            [["Software licences", "None (open-source stack)", "None for the stack; map-tile terms of use to be checked"],
             ["Compute", "One PC; 14 ms per prediction", "A small server or serverless function; the model is small"],
             ["Alert delivery", "Not implemented (message is displayed)", "An SMS or voice gateway with a per-message charge, and a contract with it"],
             ["Hospital data", "Ten entries in a JSON file", "A maintained directory or a mapping and routing service"],
             ["Mobile client", "Browser console", "A mobile application and its store distribution"],
             ["Validation", "Synthetic data", "Recording and labelling real driving and crash-like data, and safety review"]],
            widths=[1.5, 2.3, 2.7], align=["l", "l", "l"], size=9.5),
        P("The economic argument for the idea, as stated in the problem statement, is that a smartphone is already in the vehicle, whereas dedicated crash hardware is costly and is missing from most two-wheelers and older cars. "
          "The project did not carry out a cost-benefit calculation, and no cost or lives-saved figure is claimed. The largest real costs would be alert delivery and the work of collecting real validation data."),

        H2("3.3 Operational Feasibility"),
        P("The system is operated by a vehicle occupant, and the design keeps the interaction minimal. Detection is automatic. The only action asked of the occupant is to cancel within 15 seconds if the alarm is false, "
          "and cancelling needs a single button press or the Escape key. If the occupant cannot respond, the alert proceeds on its own, which is the intended behaviour for an incapacitated user."),
        B("**Usability.** The console has three working screens (live monitor, manual override, emergency response) and a landing, login and registration flow; the confirmation dialog is a modal with keyboard support.",
          "**Accessibility.** Dialogs carry role and name attributes (the test scripts locate them by role), light and dark themes are available, and call buttons are plain tel: links.",
          "**Training need.** A user needs no training beyond granting location permission and mounting the phone; the demonstration console is self-explanatory.",
          "**Maintenance.** The models are two small files and can be retrained with one script; hospitals and users are plain JSON.",
          f"**Reliability.** The 33 smoke checks pass and the security suite passes {F.TESTS['by_group']['security']['passed']} of {F.TESTS['by_group']['security']['total']}; the edge-case suite found {F.TESTS['by_group']['edge']['total'] - F.TESTS['by_group']['edge']['passed']} validation gaps (Chapter 7), which are operational risks if the API were exposed to untrusted callers."),
        P("The main operational question is the false-alarm burden. On the synthetic test data there were no detector false alarms (0 of 1,923 non-accident events) and one false Moderate or Severe trigger in 2,156 events that should not trigger. "
          "With real, noisy readings the rate would be higher: in the noise sweep, a noise level of a quarter of each feature's own spread raised the detector false-alarm rate to 1.2%, and half of it to 24.2%. "
          "The confirmation window is the design's answer to this risk, and its value in practice has to be measured with real users."),

        H2("3.4 Schedule Feasibility"),
        P("The project's history, recorded in the repository, shows the stages in which it was built. The dates are those of the commits."),
        TAB("Project schedule as recorded in the repository",
            ["Date (2026)", "Stage", "Output"],
            [["21 September", "Initial project", "Flask API, synthetic data generator, two trained models, original dashboard, hospital directory"],
             ["17 October", "Console and accounts", "React/Vite console (live monitor, manual override, response map), simulator aligned with the training generator, login and registration"],
             ["25 October", "Measurement and documentation", "Evaluation scripts, latency and test runs, diagrams, figures, screenshots and the submission documents"]],
            widths=[1.2, 1.8, 3.5], align=["l", "l", "l"], size=10),
        P("The pipeline is small enough that each stage fitted in a short period, so the schedule was feasible for the scope delivered. The stages that were not scheduled, real data collection and a phone client, "
          "would each take considerably longer, because they depend on recording and labelling real events, and they are the main items of future work."),

        H2("3.5 Advantages and Constraints"),
        B("**Advantages.** Hardware-free sensing in principle; open-source stack; small, fast models; a confirmation window that handles false alarms; a severity grade that lets alerts be prioritised; a single readable pipeline that a student team can test end to end.",
          "**Constraints.** Synthetic training data; no real-sensor input; no message delivery; a ten-hospital directory for one city; unpinned library versions (the shipped pickles were written by scikit-learn 1.9.0 and load with a warning under 1.5.0); input validation gaps in the API; the development server only."),
        TAB("Feasibility risks and how the design treats them",
            ["Risk", "Likelihood and effect", "Treatment in the project"],
            [["Synthetic data does not represent real crashes", "Certain; real-world accuracy unknown", "Stated in every document; feature definitions kept physical so real data can replace the generator; real-data collection listed as first future work"],
             ["False alarms from road-surface shocks", "Likely on real roads; detector flags about half of probe events", "Moderate / Severe gate and the 15 s cancel window; future work: train on labelled pothole and speed-breaker data"],
             ["Alert never reaches responders", "Certain in this build", "Message is shown, 108 / 112 tap-to-call provided; messaging gateway listed as future work"],
             ["Library versions drift", "Possible: requirements are unpinned", "Retraining script supplied; same-seed retrain agreed with the shipped models on 100% of test events"],
             ["Invalid input crashes an endpoint", "Seen in tests (HTTP 500 on non-numeric fields)", "Findings reported; input validation listed as the first code change"],
             ["Phone cannot sense continuously", "Likely in a browser", "A native client is listed as future work; the API accepts the same eleven fields"]],
            widths=[1.9, 2.0, 2.6], align=["l", "l", "l"], size=9.5),
        P("The study's overall finding is that the project is feasible as a research and teaching prototype and that the path to a field system is clear but long, because it needs real data, a phone client and an alert gateway."),
    ]


def chapter4():
    pk = F.SHIP["per_event_kind"]
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        P("This chapter describes what exists today, what ResQAI proposes in its place, and the requirements the proposed system must meet. It lists the functional and non-functional requirements, the hardware and software used, the user roles and the constraints. "
          "Requirements are numbered so that Chapters 5 and 7 can refer to them."),

        H2("4.1 Existing System and its Limitations"),
        P("Today an accident reaches the emergency services in one of three ways: the victim or a passer-by calls, an in-vehicle crash notification system sends a signal, or a purpose-built IoT device sends a message. "
          f"The first depends on someone being present and able to act. The second is dedicated hardware that is costly and absent from most two-wheelers and older cars. The third is represented in the literature by GreenBox {c('greenbox')} and similar Arduino and GSM designs {c('dashora', 'karthik', 'sharma')}."),
        TAB("Limitations of the existing approaches",
            ["Limitation", "Consequence"],
            [["Reporting depends on a person being present and able to call", "Accidents on quiet roads can go unreported for a long time"],
             ["Detection reports only that an impact occurred", "No severity, so responders cannot prioritise a minor scrape against a critical collision"],
             ["Fixed-threshold sensor prototypes", "Hard braking and road shocks can be mistaken for crashes; no learned separation"],
             ["Dedicated crash hardware", "Cost; not fitted to most two-wheelers and older cars"],
             ["Severity models on recorded datasets", "Useful for analysis and planning, but not connected to sensing or dispatch"]],
            widths=[3.0, 3.5], align=["l", "l"], size=10),

        H2("4.2 Proposed System and its Advantages"),
        P("ResQAI proposes a software chain that a smartphone could feed. A reading of eleven motion features is scaled and passed to a detector, a random forest that returns accident or not with a probability. "
          "A second random forest grades the severity as None, Minor, Moderate or Severe, and the detector gates it so that a non-accident is always graded None. A Moderate or Severe result opens a 15-second confirmation; "
          "the occupant may cancel, and if no one does the browser location is read, the nearest hospitals are ranked, and an alert message is composed and shown. The console also offers a manual override form so that any reading can be tried."),
        TAB("Advantages of the proposed system over the existing approaches",
            ["Advantage", "How it is achieved", "Evidence"],
            [["Severity as well as detection", "Second random forest on the same scaled features", f"Severity accuracy {F.f5(F.SEVM['accuracy'])} on synthetic test data; {F.pct(F.BASE['rule_based_fallback (acc_magnitude < 15 / 28 / 45)']['sev_accuracy'])} for a threshold rule"],
             ["Learned rather than fixed separation", "Forest on 11 features, with hard braking as a training class", f"0 of {pk['harsh_brake']['n']} braking test events flagged as accidents"],
             ["False-alarm control", "15-second confirmation; only Moderate and Severe start it", "Minor events are logged, not escalated"],
             ["Prioritised, located alert", "Severity, confidence, map link and nearest hospital in the message", f"Alert path {F.ALERT_PATH['mean']:.0f} ms mean on loopback, excluding the 15 s window"],
             ["No special hardware", "Phone-style sensors and a browser", "Console runs on a laptop; real sensing not yet built"]],
            widths=[1.7, 2.4, 2.4], align=["l", "l", "l"], size=9.5),

        P("**Main scenario.** The occupant signs in and opens the live monitor. A reading arrives, either from the stream or from a scenario button, and is shown with its probability and severity. "
          "If the severity is Moderate or Severe, a dialog titled Possible accident detected opens and counts down from 15; the occupant presses I'm fine, cancel (or Escape), and the event log records that the user confirmed they are OK. "
          "If instead the countdown ends, the console sends the alert, the dispatch dialog opens with the alert id, and the Response screen shows the accident marker, the hospital markers, the dispatch summary and the message. "
          "**Alternative flows.** If the location is denied, the server substitutes a point near the default area. If the API is unreachable, the console shows an error banner and live monitoring stops. If the models are missing, the rule-based fallback answers and the result is labelled as such."),
        P("The proposed system is deliberately modest in two respects. It does not try to predict crashes before they happen, which is the subject of driver-assistance systems, and it does not replace the emergency services; "
          "it only shortens the time between an impact and a located message, and adds the severity that helps the first responder decide how many resources to send."),

        H2("4.3 Functional Requirements"),
        TAB("Functional requirements and where they are met",
            ["ID", "Requirement", "Implemented in"],
            [["FR1", "Accept an 11-feature sensor reading as JSON and fill missing fields with safe defaults", "POST /api/predict, build_feature_vector"],
             ["FR2", "Decide whether the event is an accident and return its probability", "Detector forest, predict_proba"],
             ["FR3", "Grade severity None, Minor, Moderate or Severe; force None when no accident", "Severity forest and gate"],
             ["FR4", "Provide five simulated scenarios (normal, brake, minor, moderate, severe) and a random live stream every 1.5 s", "GET /api/simulate, MonitorContext"],
             ["FR5", "Start a 15-second confirmation on Moderate or Severe; allow cancel by button or Escape; pause live monitoring", "MonitorContext, AlertOverlays"],
             ["FR6", "On confirmation or timeout, obtain the device location (3 s timeout) or fall back to a default area", "Browser Geolocation, POST /api/emergency"],
             ["FR7", "Rank the three nearest hospitals by great-circle distance and list the five nearest on the map screen", "haversine_km, nearest_hospitals"],
             ["FR8", "Compose a dispatch message with severity, confidence, coordinates, map link, nearest hospital and phone, and an alert id", "POST /api/emergency"],
             ["FR9", "Show 108 and 112 (and 103) as tap-to-call numbers", "ContactsCard"],
             ["FR10", "Let the user type manual sensor values and run detection", "Manual override page"],
             ["FR11", "Register, sign in, sign out; lock the console behind a login; lock an account after 5 failed attempts for 5 minutes", "auth.py, AuthProvider"],
             ["FR12", "Keep an event log (last 25 entries) and a sensor trace (last 40 points)", "MonitorContext, EventLog, SensorChart"],
             ["FR13", "Report model status (loaded or fallback)", "GET /api/health, model_source"]],
            widths=[0.5, 4.0, 2.0], align=["c", "l", "l"], size=9.5),

        H2("4.4 Non-Functional Requirements"),
        TAB("Non-functional requirements and measured values",
            ["Quality", "Requirement", "Measured"],
            [["Performance", "A reading should be classified well within the countdown and without perceptible delay", f"/api/predict mean {F.ENDPOINTS['POST /api/predict']['mean']:.1f} ms; alert path {F.ALERT_PATH['mean']:.0f} ms mean (loopback, development server)"],
             ["Accuracy", "Detect crashes and grade severity on held-out events", f"Detector F1 {F.f4(F.DET['f1'])}; severity macro-F1 {F.f5(F.SEVM['macro_f1'])} (synthetic)"],
             ["Robustness", "Degrade gracefully with sensor noise", "Detector F1 stays 1.000 up to noise of 10% of each feature's spread and falls to 0.976 at 25%"],
             ["Security", "Hashed passwords, signed expiring tokens, lockout, guard on the API when enabled", f"Scrypt hashes; 12 h tokens; {F.TESTS['by_group']['security']['passed']} of {F.TESTS['by_group']['security']['total']} security checks pass"],
             ["Reliability", "Fall back to a rule-based answer if the model files are missing", "Fallback implemented; tested at unit level"],
             ["Portability", "Run on a standard Windows PC with Python 3.10+ and Node.js 18+", "setup.bat and run.bat provided"],
             ["Maintainability", "Small modules, scripted tests", "app.py 296 lines, auth.py 181 lines, train_models.py 195 lines"],
             ["Privacy", "No tracking; accounts stored locally", "Alerts are not stored on the server; accounts in data/users.json (git-ignored)"]],
            widths=[1.1, 2.7, 2.7], align=["l", "l", "l"], size=9.5),

        H2("4.5 Hardware Requirements"),
        TAB("Hardware used and a practical minimum",
            ["Component", "Used in this project", "Practical minimum"],
            [["Processor", "Intel Core i5-12500 (CPU only)", "Any recent dual-core processor"],
             ["Memory", "15.7 GB", "4 GB (the API process held about 115 MB when idle)"],
             ["Storage", "Under 1 GB including node_modules", "1 GB"],
             ["Graphics card", "None", "None"],
             ["Sensors", "None attached (simulated)", "A phone with accelerometer, gyroscope and GPS for real use"],
             ["Network", "Loopback; internet only for map tiles", "A data connection at the moment of dispatch"]],
            widths=[1.3, 2.7, 2.5], align=["l", "l", "l"], size=10),
        P("The practical minimum is an estimate and was not tested on other machines. During the measurements the PC was short of memory because of other programs, and one API server was lost to an out-of-memory error and restarted; the timings are therefore conservative."),

        H2("4.6 Software Requirements"),
        TAB("Software used",
            ["Layer", "Software and version"],
            [["Operating system", "Windows 11 Pro"],
             ["Language and runtime", f"Python {F.M['environment']['python']}; Node.js 18 or later"],
             ["Back end", "Flask 3.1.0, werkzeug, itsdangerous, joblib"],
             ["Machine learning", f"scikit-learn {F.M['environment']['sklearn']} in this environment (shipped pickles written by 1.9.0), numpy {F.M['environment']['numpy']}, pandas {F.M['environment']['pandas']}"],
             ["Front end", "React 19, Vite 8, react-router 7, Leaflet 1.9, Recharts 3, framer-motion, GSAP, lucide-react"],
             ["Testing and capture", "Playwright (Chrome) for screenshots; the scripts smoke_test.py, run_tests.py, measure_metrics.py, measure_api.py"],
             ["Browser", "A current Chrome, Edge or Firefox with location permission"]],
            widths=[1.8, 4.7], align=["l", "l"], size=10),
        P("requirements.txt lists Flask, scikit-learn, joblib, numpy and pandas without version numbers. This keeps installation simple but lets a new installation pick a scikit-learn version different from the one that wrote the shipped pickles; Chapter 6 gives the consequence and the advice."),

        H2("4.7 User Roles"),
        TAB("User roles",
            ["Role", "Description", "Access"],
            [["Visitor", "Not signed in", "Landing page only; the console redirects to the login screen"],
             ["Occupant (signed-in user)", "Driver or rider using the console", "Live monitor, manual override, emergency response; confirm or cancel alerts"],
             ["Developer or administrator", "Maintains the system from the command line", "Retrains the models, sets REQUIRE_AUTH and SECRET_KEY, edits the hospital directory, runs the test scripts"],
             ["Responder (external)", "Would receive the alert", "Not a user of the console; in this build the alert is shown to the occupant, not sent"]],
            widths=[1.7, 2.3, 2.5], align=["l", "l", "l"], size=10),

        H2("4.8 Constraints and Dependencies"),
        B("**Data and sensing.** The synthetic generator is the only source of training events, and the console cannot read real sensors; input is simulated or typed by hand.",
          "**Delivery.** No messaging gateway exists, so no alert leaves the application.",
          "**Location.** The hospital list covers one city; location depends on browser permission and falls back to a default point near Hyderabad when it is denied or times out.",
          "**Server.** Flask runs in debug mode on the development server; a production deployment would need a proper WSGI server.",
          "**Dependencies and authentication.** The map needs internet for tiles; Python packages are unpinned; REQUIRE_AUTH is off by default, so the API endpoints are open."),
    ]
