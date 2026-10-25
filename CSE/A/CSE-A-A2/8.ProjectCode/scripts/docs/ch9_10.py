"""Novelty, contributions, scope, limitations, walkthroughs, decisions, conclusion (Chapter 9) and future scope (Chapter 10) for ResQAI."""

import ast
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R


# ------------------------------------------------------------------------------------------------ helpers
def _text(rel):
    return open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n")


def src_fn(rel, name):
    """Source of one top-level function of a Python file of 8.ProjectCode, found with ast so line numbers never go stale."""
    text = _text(rel)
    lines = text.split("\n")
    node = next(n for n in ast.parse(text).body if getattr(n, "name", None) == name)
    first = node.decorator_list[0].lineno if node.decorator_list else node.lineno
    return "\n".join(lines[first - 1:node.end_lineno])


def between(rel, start, end, include_end=True):
    """Lines of a file from the first line containing `start` to the next line containing `end`."""
    lines = _text(rel).split("\n")
    i = next(k for k, ln in enumerate(lines) if start in ln)
    j = next(k for k in range(i, len(lines)) if end in lines[k])
    return "\n".join(lines[i:j + (1 if include_end else 0)])


def c(*keys):
    """Citation string such as [1], [6] from CITE keys."""
    return "[" + ", ".join(str(R[k]) for k in keys) + "]"


def _bp():
    return c("base")


RULE = F.BASE[next(k for k in F.BASE if k.startswith('rule_based'))]


# ------------------------------------------------------------------------------------------------ document 9
def novelty_blocks():
    b = _bp()
    return [
        P(f"The base paper named in the batch file is the multi-task FT-Transformer of Wang, Liang and He {b}. It is a model of what happened after a crash: from the police record of 30,442 crashes in one Chinese city, "
          "it predicts three severity outcomes (injury, fatality and property loss) with a feature-token transformer, an uncertainty-weighted multi-task loss and SHAP explanations. "
          f"The survey in the batch file ends with the observation that this whole family of work predicts severity from recorded datasets after the event, and that none of it closes the loop from live sensing through severity grading to automated dispatch {c('hamdan', 'pei')}. "
          "ResQAI is built on that observation, so its novelty lies in the system, not in a new learning algorithm."),
        TAB("What is adopted, adapted and new", ["Element", "Base paper", "ResQAI", "Status"], [
            ["Idea that severity, not only occurrence, should be predicted", "Central", "Four grades (None, Minor, Moderate, Severe) decide whether anyone is contacted", "Adopted"],
            ["Evaluation by accuracy, precision, recall and F1", "Per task, on 6,088 real test records", "Per class on 2,400 synthetic test events, plus five-seed repeat", "Adopted"],
            ["Classifier family", "FT-Transformer, multi-task, uncertainty-weighted loss", "Two random forests (detector and severity) behind one scaler", "Different, standard"],
            ["Input", "Police-recorded driver, vehicle, road and weather attributes", "Eleven accelerometer, gyroscope, speed and jerk features of one event", "New for this project"],
            ["Time of use", "After the crash, for planning and policy", "At the moment of the crash, to trigger a response", "New"],
            ["False-alarm control", "Not applicable", "15-second occupant confirmation; only Moderate or Severe starts it", "New"],
            ["Action taken", "None (analysis)", "Location, three nearest hospitals ranked by distance, drafted dispatch message", "New"],
            ["Interpretability", "SHAP at sub-class level", "Gini and permutation importance, feature-group ablation", "Simpler"],
            ["Multi-task learning, SMOTE, SHAP", "Used", "Not used (class weights instead of SMOTE)", "Not adopted"],
        ], widths=[1.9, 1.7, 2.0, 0.9], align=["l", "l", "l", "l"], size=9),
        H2("Where the contribution lies"),
        P("Three things are new relative to the base paper and to the five surveyed works, and each is a matter of design rather than of algorithm. The first is the end-to-end chain: one application takes a motion-sensor reading to a detection, a severity grade, an occupant confirmation, a location, a ranked list of hospitals and a drafted alert, "
          "and exposes every step on screen. The second is the confirmation mechanism: the system does not treat its own classification as final, and the choice of which grades start the countdown (Moderate and Severe, not Minor) is explicit and testable. "
          "The third is the evaluation, which goes further than the project brief asked: it repeats the experiment over five seeds, compares the forests with simpler models, shows that the detector adds nothing over a threshold on this data while the severity model does, "
          "measures the effect of sensor noise, and probes events outside the training distribution. The evaluation exposed limits (the potholes, the noise, the validation gaps) that a single accuracy figure would have hidden."),
        H2("What is standard"),
        P(f"The classifier is a random forest {c('breiman')} from scikit-learn {c('sklearn')}, the distance is the haversine formula {c('haversine')}, the passwords are hashed with scrypt {c('scrypt')}, and the interface is React {c('react')} with a Flask back end. "
          "None of these is claimed as new. The labelled data are synthetic and were produced by the project team, so no result of the project is a contribution to the knowledge of how real crashes look in a phone's sensors."),
        P(f"Against GreenBox {c('greenbox')}, which also detects an accident and alerts by SMS, ResQAI differs in learning the severity from data instead of fixing hardware thresholds, in keeping a human in the loop through the countdown, and in naming the hospital; "
          f"GreenBox, in return, runs on real hardware in a moving vehicle and really sends the message. Against CIRS {c('cirs')}, which detects accidents in camera images, ResQAI uses a sensor that every phone carries; CIRS was trained and tested on real frames."),
    ]


def contribution_blocks():
    return [
        P("The work makes the following contributions. The first five concern the system, the last three the evaluation. Each statement is limited to what the code and the measurements in this report support."),
        N("An end-to-end, working prototype that turns an 11-feature motion-sensor reading into a crash decision, a four-level severity grade, a 15-second occupant confirmation, a location, three ranked hospitals and a dispatch message, with a React console and a Flask API.",
          "A two-model design in which an accident detector gates a severity predictor: when the detector says 'no accident' the severity is forced to None, so a mislabelled severity can never contradict the detection.",
          "A confirmation mechanism that starts only for Moderate and Severe results and can be answered by a button or by Escape; cancelling is logged, and live monitoring is paused while a decision is pending.",
          "A hospital recommendation step that ranks a directory by great-circle distance from the device position (browser geolocation with a fallback), verified against a brute-force ranking on 500 random positions.",
          "A simulator that generates readings from the same parameters as the training data, which lets the whole pipeline be demonstrated and tested without a phone; its consistency with the models is tested (60 of 60 readings per scenario rated correctly).",
          f"A measured evaluation of the two classifiers on {F.N_TEST:,} held-out events: detector accuracy {F.DET['accuracy']:.4f}, severity accuracy {F.SEVM['accuracy']:.5f} and macro-F1 {F.SEVM['macro_f1']:.5f}, repeated over five seeds (severity accuracy {F.SEEDS['mean']['sev_accuracy']:.5f} on average).",
          "A comparison with four simpler models, a feature-group ablation and a threshold sweep, which show that a single threshold detects crashes as well as the forest on this data, while the forest grades severity clearly better than the three-threshold rule.",
          "A robustness and limits analysis: tolerance to sensor noise up to a tenth of the natural spread, a probe of pothole-like and speed-breaker-like events that the detector flags about half the time, and an input-validation test that found eight gaps in the API."),
        P("The code, the generated diagrams, the figures and every measurement script are part of the project folder, so each number in this report can be regenerated with scripts/measure_metrics.py, scripts/measure_api.py and scripts/run_tests.py."),
    ]


# ------------------------------------------------------------------------------------------------ document 10
def scope_blocks():
    return [
        H2("In scope"),
        B("**Crash detection from motion features.** Eleven features (three acceleration axes and their magnitude, three rotation axes and their magnitude, speed before the event, speed change, jerk) classified as accident or not.",
          "**Severity grading** into None, Minor, Moderate and Severe, evaluated per class.",
          "**Occupant confirmation** with a 15-second countdown, cancel by button or Escape, and automatic dispatch when the time runs out.",
          "**Location and hospital recommendation** from the browser's position, with a ten-hospital directory around Hyderabad, ranked by great-circle distance.",
          "**Dispatch message and emergency dashboard:** alert id, severity, confidence, map link, nearest hospital and phone, three nearest hospitals on a Leaflet map, call buttons for 108, 112 and 103.",
          "**A web console and API:** landing page, registration and sign-in, live monitor, manual override, response map, light and dark themes, optional token guard for the API.",
          "**Evaluation** by accuracy, precision, recall and F1, five-seed repeat, baselines, ablation, noise and threshold analysis, API latency, and tests."),
        H2("Out of scope"),
        B("**A phone application.** There is no Android or iOS code and no streaming of real sensor data; a built-in simulator stands in for the phone.",
          "**Real crash or road data.** No smartphone recordings, crash-test data or public benchmark were used or collected.",
          "**Delivery of the alert.** No SMS, voice call, e-mail or push notification is sent, no contact list is stored and no responder acknowledges.",
          "**Road-surface events.** Potholes, speed breakers, phone drops and similar events are not part of the training data.",
          "**Routing and hospital capability.** No road network, traffic, ambulance dispatch, specialty or bed information; the nearest hospital is the nearest by straight line.",
          "**Post-crash analytics** of the kind done by the base paper (injury counts, property loss, SHAP at class level).",
          "**Vehicle integration** (airbag, OBD-II, in-vehicle crash sensors) and multi-vehicle or roll-over modelling.",
          "**Production operation:** HTTPS, load balancing, monitoring, data-protection compliance and regulatory approval of an automatic emergency call."),
        H2("Target users"),
        P("The system is aimed at the occupant of a car or two-wheeler who carries a smartphone, and at a responder who would receive the message. In this build only the occupant's console exists; the responder's side is represented by the drafted message and the map."),
    ]


def assumption_blocks():
    return [
        P("The design and the measurements rest on the following assumptions. Where one fails in practice, the corresponding result in Chapter 8 should be read with care."),
        B("**The phone is rigidly attached and its orientation is known.** The generator draws an acceleration vector in a random direction in the horizontal plane and keeps gravity on the z axis; a phone in a pocket or a loose mount would blur this.",
          "**Crash events look like the generator.** A crash is a large, brief spike of acceleration and rotation together with a drop in speed and a high jerk; real crashes include low-speed scrapes, rear-end hits and roll-overs that this description does not capture.",
          "**Non-crash events are normal driving or hard braking.** Potholes, speed breakers, kerb strikes and drops of the phone are assumed absent, which is untrue on real roads.",
          "**The sensor is noiseless apart from the generator's own spread.** Real accelerometers add bias, drift and vibration (Section 8.6 of the report shows the effect of noise).",
          "**A smartphone can compute the eleven features and send them as JSON** (speed from GPS or the vehicle, jerk from the derivative of acceleration) in time to act.",
          "**The occupant sees and hears the prompt.** The 15-second countdown assumes a screen or sound that a conscious occupant can notice and answer; an incapacitated occupant is meant not to answer.",
          "**The browser position is usable.** Geolocation permission is granted; if not, a point near the default location in Hyderabad is used instead, which is only a demonstration fallback.",
          "**The ten hospitals are all suitable.** The directory carries no specialty, capacity or availability.",
          f"**One user, one machine.** The measurements were taken on one Windows 11 computer with a single client; the pickles written by scikit-learn 1.9.0 are assumed to load identically under the installed version (verified here for {F.N_TEST:,} events)."),
    ]


def limitation_blocks():
    po, sb = F.OOD["pothole"], F.OOD["speed_breaker"]
    n = F.NOISE
    return [
        H2("Data"),
        P(f"The single largest limitation is the data. All {F.N_TOTAL:,} events are synthetic; the test events come from the generator that produced the training events, and the crash classes are separated from normal driving by a gap in acceleration magnitude (harsh braking reaches at most {F.DS['class_overlap']['acc_magnitude']['harsh_brake'][1]} m/s2, the weakest crash starts at {F.DS['class_overlap']['acc_magnitude']['minor_crash'][0]} m/s2). "
          "Scores of 1.0000 for the detector follow from this and say nothing about roads. The class sizes are also small for the rare grades: the test split has 156 Moderate and 88 Severe events, so one more or fewer error moves the per-class recall by about one percentage point."),
        H2("Models"),
        B(f"**Potholes and speed breakers.** The detector flags {F.pct(po['predicted_accident_rate'], 0)} of pothole-like and {F.pct(sb['predicted_accident_rate'], 0)} of speed-breaker-like probe events as accidents; none reaches the countdown, but the 'Accident detected' log entry is false.",
          f"**Sensor noise.** The false-alarm rate rises to {F.pct(n[3]['det_false_alarm'])} at a quarter and {F.pct(n[4]['det_false_alarm'])} at a half of the natural spread; the models were not trained on noise.",
          "**No uncertainty beyond the forest's own probability,** which saturates at 0 or 1 for almost every event, so the confidence value shown to the user carries little information.",
          "**No calibration, no sequence model.** Each reading is classified alone; there is no window of readings and no use of the temporal shape of a crash.",
          "**Large values are not recognised as absurd.** A reading of 1e9 m/s2 is graded Minor instead of being rejected."),
        H2("Application"),
        B("**Nothing is sent.** The alert is a message on the screen; the ambulance and emergency numbers are tel: links.",
          "**Eight input-validation gaps** (four HTTP 500 responses, three accepted nonsense inputs, one repeated alert id) found by scripts/run_tests.py and left unfixed.",
          "**Alerts are not stored** and carry no user id, so there is no audit trail and no alert history.",
          "**Development server and file storage.** Flask's debug server, accounts in a JSON file, a lock-out counter in the memory of one process, 12-hour tokens without revocation, no HTTPS.",
          "**Hospital directory** of ten entries in one city; outside it, the nearest hospital is far away, and inside it, the nearest may be unsuitable (a children's hospital is the second nearest to the demonstration position).",
          "**The pickles come from a newer scikit-learn (1.9.0) than the one installed here (1.5.0);** requirements.txt is not pinned. Predictions were verified identical to a fresh retraining, but a pinned environment would be safer."),
        H2("Hardware and environment"),
        P("The work was done on one Intel Core i5-12500 computer without a GPU, with 15.7 GB of RAM that other programs were also using. No phone, no sensor board and no vehicle was used, so battery use, sampling rate, background execution limits of a mobile operating system and real GPS error are all unknown."),
    ]


def not_measured_blocks():
    return [
        P("The following were not measured, and no figure in this report should be read as covering them."),
        B("The detection rate and the false-alarm rate on **real** crashes and on real everyday driving.",
          "Behaviour with **real phone sensors**: mounting, orientation, sampling rate, bias, vibration.",
          "**Pothole, speed-breaker, drop and kerb events** from real roads (only a constructed probe was run).",
          "**GPS accuracy** and the time to obtain a fix; the position in the screenshots was supplied by the browser.",
          f"**Delivery latency** of a real SMS, call or e-mail, and the time until a human responds; the {F.ALERT_PATH['mean']:.0f} ms alert-path figure covers computing only and excludes the 15-second confirmation window.",
          "**Concurrency, endurance and load** (more than one client, hours of live monitoring).",
          "**Battery, CPU and memory use on a phone.**",
          "**User behaviour:** how quickly and reliably occupants cancel, how often they press the button by mistake, whether 15 seconds is the right window; no user study was carried out.",
          "**Accessibility and usability** beyond the labels and keyboard handling visible in the code.",
          "**Security under attack:** no penetration test, no rate limiting beyond the login lock-out, no analysis of token theft.",
          "**Other platforms:** all runs were on Windows 11 with Python 3.11."),
    ]


def walkthrough_blocks():
    js_countdown = between("frontend/src/state/MonitorContext.jsx", "// Countdown ticks while an alert is pending", "}, [pending, countdown, sendAlert])")
    js_gate = between("frontend/src/state/MonitorContext.jsx", "if ((r.severity_label === 'Moderate'", "setLive(false)", True)
    emergency_msg = between("app.py", "message = (", 'message += "No response received', True)
    login = src_fn("auth.py", "login")
    make_sev = between("train_models.py", "else:  # severe_crash", "severity = 3")
    train = between("train_models.py", "accident_clf = RandomForestClassifier(", "severity_clf.fit(", True)
    return [
        P("This part reads the code that carries the main flow, quoting short excerpts from the project files exactly as they stand."),
        H2("Building the feature vector (app.py)"),
        P("A payload from the browser may omit fields, so the function gives each input a default, derives the two magnitudes if they were not supplied, takes the absolute value of the jerk, and returns the values in the order in which the models were trained."),
        CODE(src_fn("app.py", "build_feature_vector"), 7.5),
        P("Two details matter. The default for acc_z is 9.81 m/s2 (one g), so an empty payload describes a stationary phone; and the vector is built from a dictionary indexed by FEATURE_NAMES, which are loaded from the same pickle as the models, so a change of feature order in training cannot silently misalign the columns."),
        H2("Detection, severity and the gate (app.py)"),
        P("This is the core of the system. When the models are loaded the vector is scaled, the detector gives the class and the probability of an accident, and the severity model gives the grade; if the detector says no accident the grade is forced to 0. Without the models the three thresholds of the fallback decide."),
        CODE(src_fn("app.py", "predict_from_features"), 7.5),
        CODE(src_fn("app.py", "rule_based_fallback"), 7.5),
        P("The comment in the source calls the gate 'trust the stronger signal'; what it does is to let the detector override the severity model. The reverse override is absent: a detector 'yes' with a severity of None is possible in principle (the severity forest could say None for an event the detector accepts) and would be returned as an accident of severity None, which the interface would show as an accident of severity None. "
          "On the 2,400 test events it never happens, but the code does not prevent it."),
        H2("Distance and the nearest hospitals (app.py)"),
        CODE(src_fn("app.py", "haversine_km"), 7.5),
        CODE(src_fn("app.py", "nearest_hospitals"), 7.5),
        P(f"The haversine formula {c('haversine')} gives the great-circle distance on a sphere of radius 6,371 km; for the few kilometres involved in a city the error against a road route is far larger than the error of the formula. "
          "The function ranks all ten hospitals on the distance rounded to two decimals and returns the first k; the rounding is why two hospitals a few metres apart can swap places, and why the unit test compares distances and not names. "
          "The route does not validate k, which is why k = -1 returns nine hospitals (Chapter 7)."),
        H2("Composing the dispatch message (app.py)"),
        CODE(emergency_msg, 7.5),
        P("The message is built with an f-string from the severity label and the confidence supplied by the client, the coordinates and the nearest hospital. The label is not validated, which is one of the eight findings; the alert id is the Unix time in seconds, which is the reason two alerts in one second collide."),
        H2("The client-side confirmation rule (MonitorContext.jsx)"),
        P("The browser, not the server, decides when to ask the occupant. After each prediction the context checks the grade; for Moderate and Severe it stores the result as pending, resets the countdown to 15 and stops live monitoring so that new readings do not pile up under an open question."),
        CODE(js_gate, 7.5),
        P("A one-second timer then decrements the countdown, and when it reaches zero the alert is sent exactly as if the occupant had pressed the button."),
        CODE(js_countdown, 7.5),
        P("Cancelling (button, cross or Escape) clears the pending result and writes 'User confirmed they are OK. Alert cancelled.' to the event log. Because the timer lives in the browser, closing the tab during the countdown sends nothing; in a phone application the same state machine would have to survive the app being backgrounded."),
        H2("Account lock-out (auth.py)"),
        CODE(login, 7.5),
        P("The login route keeps, for each e-mail, the times of failed attempts in the last five minutes. After five the route answers 429 and does not even check the password, so a correct guess after the fifth failure is also refused, as the security test confirms. "
          "On success the failure list is cleared and a signed token valid for 12 hours is returned. The counter lives in a Python dictionary, so it is reset when the server restarts and is not shared between processes."),
        H2("Training the two forests (train_models.py)"),
        CODE(make_sev, 7.5),
        CODE(train, 7.5),
        P(f"The severe-crash generator draws the magnitude of the acceleration spike between 45 and 80 m/s2 in a random direction, with rotation, deceleration and jerk drawn from wider distributions than for the lesser grades. Both forests use balanced class weights because the rare grades make up only a few percent of the events (447 severe events of 12,000), and both see the same scaled features. "
          f"The script prints accuracy and a classification report on the held-out events; this project's measurement script reproduces that split exactly ({F.N_TRAIN:,} / {F.N_TEST:,}) and adds the analyses of Chapter 8."),
    ]


def decision_blocks():
    return [
        P("The table lists the main implementation decisions, the reason recorded for each, and what was given up. Several of them follow from the aim of a demonstrable prototype that runs on one laptop without a phone, a cloud or a database."),
        TAB("Implementation decisions", ["Decision", "Reason", "Alternative not taken"], [
            ["Two random forests (detector, severity), not one 4-class model", "The first answer ('is it a crash?') is the safety-critical one and can be inspected on its own; the second refines it. The gate prevents an inconsistent pair of answers.", "A single 4-class model; a multi-task network as in the base paper"],
            ["Random forest", "Handles mixed-scale features, needs little tuning, trains in seconds on a CPU, gives a probability, and performed as well as gradient boosting (Chapter 8).", "Gradient boosting, neural network, FT-Transformer"],
            ["Class weight 'balanced', no oversampling", "Crash grades are 20 % of the events; weights keep the training set unchanged and the pipeline simple.", "SMOTE as in the base paper"],
            ["Synthetic training data from hand-written distributions", "No public dataset of phone recordings of crashes was available within the project; a generator made the whole pipeline testable and reproducible (seed 42).", "Collecting real data; using a public benchmark"],
            ["Eleven features including derived magnitudes and jerk", "Magnitudes remove dependence on axis direction; jerk and speed change describe the suddenness of the event; all can be computed on a phone.", "Raw time series with a 1-D CNN or LSTM"],
            ["StandardScaler in front of tree models", "Trees do not need it; it is kept so that the same scaled vector can feed any other model (the baselines) and so the pickles stay compatible with the shipped app.", "No scaling"],
            ["Rule-based fallback on acc_magnitude", "The API must answer even if the pickles are missing; the thresholds 15, 28 and 45 m/s2 mirror the generator.", "Return an error"],
            ["15-second countdown, cancel by button or Escape; only Moderate and Severe", "False alarms are the main cost of an automatic system, and a conscious occupant can stop one cheaply; Minor events should not wake an emergency service.", "Immediate alert; a confirmation for every accident"],
            ["Live monitoring pauses while a decision is pending", "Avoids a second alert and a second dialog for the same event.", "Keep streaming and queue alerts"],
            ["Haversine distance over a 10-hospital JSON file", "Needs no external service or key, deterministic, testable against brute force.", "A maps or places API with road routing, capacity and specialty"],
            ["Browser Geolocation with a 3-second timeout and a default fallback", "The demo must work on a laptop and with permission denied.", "Server-side location lookup; mandatory permission"],
            ["Simulator inside the server, mirroring training", "Lets the screens and the tests run anywhere; the scenarios are named after the generator's kinds.", "A separate test client; replaying recorded data"],
            ["JSON files for users and hospitals, no database", "Two small, rarely-written collections; one file each is enough for a prototype and is easy to inspect.", "SQLite or PostgreSQL"],
            ["Optional token guard (REQUIRE_AUTH)", "The original Flask page had no login and had to keep working; the React console adds one.", "Always require authentication"],
            ["scrypt hash, signed expiring token, five-failure lock-out", "Standard, library-provided protections that cost little code.", "OAuth / external identity provider"],
            ["React + Vite console, Leaflet, Recharts", "A responsive single-page interface with a live trace and map; component state keeps the confirmation logic in one place (MonitorContext).", "Server-rendered pages only"],
            ["Reproducible measurement scripts committed with the project", "Every reported figure is regenerated by a script from the code that ships; no number is typed into a document.", "Reporting the training script's console output only"],
        ], widths=[1.8, 2.8, 1.6], align=["l", "l", "l"], size=8.5),
        P("Most of these decisions are reasonable for a demonstrator and would change for a deployed system: real data would replace the generator, a window of readings would replace the single reading, a mobile client would replace the simulator, and a messaging gateway would replace the drafted message."),
    ]


# ------------------------------------------------------------------------------------------------ conclusion / future (shared bodies)
def _summary_ps():
    d, s = F.DET, F.SEVM
    return [
        P("ResQAI set out to shorten the time between a road accident and the arrival of help by detecting the accident automatically from the sensors that a smartphone already carries, judging how serious it is, asking the occupant to confirm, and then composing a located alert that names the nearest hospital. "
          f"The base paper and the surveyed work {c('base')} predict severity from records after the event, and none of it connects sensing to dispatch; this project built that connection as a working prototype and measured it."),
        P(f"The prototype is a Flask service with two random forests behind one scaler and a React console. A reading of eleven features is classified as accident or not, graded None, Minor, Moderate or Severe, and, for Moderate and Severe grades, held for a 15-second confirmation before the location, the three nearest hospitals and the dispatch message are produced. "
          f"On {F.N_TEST:,} held-out events the detector scored accuracy {d['accuracy']:.4f} and the severity model accuracy {s['accuracy']:.5f} with macro-F1 {s['macro_f1']:.5f}; over five repeats severity accuracy averaged {F.SEEDS['mean']['sev_accuracy']:.5f}. "
          f"The whole alert path took {F.ALERT_PATH['mean']:.0f} ms of computing on loopback, before the deliberate 15-second window."),
    ]


def conclusion_blocks():
    po, sb = F.OOD["pothole"], F.OOD["speed_breaker"]
    return [
        H2("Summary of the work"),
        *_summary_ps(),
        H2("Key findings"),
        N(f"**The pipeline works end to end.** {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} smoke checks and {F.TEST_PASSED} of {F.TEST_TOTAL} further checks pass; the eight that fail are input-validation gaps that the React screens cannot trigger.",
          f"**On this data detection is easy and severity is where learning helps.** A single threshold on acceleration magnitude detects crashes as perfectly as the forest; for severity the forest is clearly better than the threshold rule (accuracy {F.SEVM['accuracy']:.5f} against {RULE['sev_accuracy']:.4f}, macro-F1 {F.SEVM['macro_f1']:.5f} against {RULE['sev_macro_f1']:.4f}).",
          f"**Hard braking is not mistaken for a crash,** but potholes and speed breakers are untested territory: constructed probes of both are flagged about half the time ({F.pct(po['predicted_accident_rate'], 0)} and {F.pct(sb['predicted_accident_rate'], 0)}), though never graded high enough to start a countdown.",
          f"**The models tolerate light sensor noise and fail beyond it.** Up to a tenth of the natural spread the detector is unchanged; at a quarter false alarms reach {F.pct(F.NOISE[3]['det_false_alarm'])}, at a half {F.pct(F.NOISE[4]['det_false_alarm'])}.",
          "**The human-in-the-loop design is what keeps false alarms cheap.** The 15-second window and the restriction to Moderate and Severe results put the decision about contacting anyone in the occupant's hands."),
        H2("Objectives achieved"),
        P("Of the six objectives of the brief, one (severity grading) is achieved on synthetic data, one (hospital recommendation from location) at demonstration level, and one (evaluation) in full. Three are only partly met: data collection, because no real recordings exist; the separation of accidents from potholes and speed breakers, because only hard braking is handled; "
          "and the automated alert, because the message is composed and displayed but not transmitted. Chapter 8 gives the evidence for each."),
        H2("Practical applications"),
        B("A teaching and demonstration platform for the structure of an automatic crash-response service: sensing, classification, confirmation, location, dispatch.",
          "A test bench for new detectors: any model that accepts the 11 features can be swapped into predict_from_features and evaluated with the same scripts.",
          "A starting point for a phone application and an insurer or fleet service that would receive the alert, once real data and a messaging channel are added."),
        H2("Known limitations"),
        P("The data are synthetic and the scores are upper bounds; road-surface events are unmodelled; nothing is transmitted; the input validation of the API has eight known gaps; and no user study was done. These limits are the agenda of the future work below."),
    ]


def future_blocks():
    return [
        H2("Data and models"),
        B("**Collect real data.** Record accelerometer, gyroscope, speed and GPS from phones in ordinary driving, on rough roads, over speed breakers and kerbs, in low-speed bumps and, under a safe protocol (instrumented crash tests, staged low-speed impacts, public crash-reconstruction data), in impacts; retrain and re-measure.",
          "**Make potholes, speed breakers and drops their own classes** and add the cases of phone drops, door slams and rough parking.",
          "**Use a window of readings.** Replace the single-reading classifier with a model over 1 to 3 seconds of samples (1-D CNN, gradient boosting on window features) and compare it with the forests of this work.",
          "**Train for noise and orientation.** Add noise and random phone orientation during training, normalise the axes with the gravity vector, and calibrate the probabilities.",
          "**Consider multi-task learning** of the kind in the base paper (one network for detection and severity) and explain predictions with SHAP, once real data make the extra capacity worthwhile."),
        H2("Alerting and location"),
        B("**Send the alert.** Add an SMS, voice-call or push gateway, a list of emergency contacts per user and an acknowledgement from the receiver; measure the delivery time.",
          "**Use a real hospital source and road routing.** Replace the ten-entry file with a maps or health-registry service giving road distance, traffic, specialty (trauma centre, paediatric) and capacity, and let the recommendation depend on the grade.",
          "**Store alerts** with a unique id, user, time and outcome, so that an audit trail and statistics are possible.",
          "**Send location updates** after the first alert (the vehicle may be moving or the first fix poor)."),
        H2("Application quality and security"),
        B("Fix the eight validation gaps: reject non-numeric and out-of-range input with 400, bound k, accept only the four severity labels, reject physically impossible readings, and generate unique alert ids.",
          "Move to a production WSGI server behind HTTPS, store accounts in a database, share the lock-out counter between processes, revoke tokens, and require authentication by default.",
          "Add automated tests to the repository (pytest, front-end tests), a continuous-integration run, and a pinned requirements file so that the models always load under the version that wrote them.",
          "Improve accessibility: sound and vibration for the countdown, larger controls, screen-reader announcements already in place to be tested with users."),
        H2("Deployment and scale"),
        B("**A phone client** (Android first) that samples the sensors in the background within the operating system's limits, computes the features on the device or streams compressed windows, and keeps the confirmation state machine alive when the app is not in the foreground.",
          "**Edge inference.** Export the forests (or a smaller model) to run on the phone so that detection works without coverage and only the alert needs the network.",
          "**Scale the back end** with several workers, a queue for alerts and monitoring of latency and error rates."),
        H2("Further research"),
        B("How early, within a crash, can severity be estimated from phone sensors, and how well does it correlate with injury? This needs linkage with medical outcomes, as the base paper itself notes for its own data.",
          "What confirmation window and what interface minimise both missed alerts and nuisance alerts under real stress? This needs a user study and, for a regulated service, agreement with emergency authorities.",
          "Can the false-alarm behaviour on road-surface events be learned from crowd-sourced, privacy-preserving phone data?",
          "Can a post-event severity model such as the base paper's be fed with the facts available at the scene (vehicle type, road class from the map, time of day) to refine the first grade measured from motion alone?"),
    ]


def chapter9_blocks():
    po, sb = F.OOD["pothole"], F.OOD["speed_breaker"]
    return [
        H1("CHAPTER 9: CONCLUSION"),
        H2("9.1 Summary"),
        *_summary_ps(),
        H2("9.2 Objectives Achieved"),
        P("The brief set six objectives. They are repeated here with the verdict that Chapter 8 supports; the evidence for each is in Section 8.11."),
        TAB("Objectives and verdicts", ["No.", "Objective (short)", "Verdict"], [
            ["1", "Collect and preprocess smartphone sensor data", "Partly: 11-feature pipeline and 12,000 synthetic events; no real recordings"],
            ["2", "Separate accidents from potholes, speed breakers and hard braking", f"Partly: hard braking yes (0 of {F.SHIP['per_event_kind']['harsh_brake']['n']} flagged); potholes and speed breakers not demonstrated"],
            ["3", "Severity model (minor, moderate, severe)", f"Achieved on synthetic data: accuracy {F.SEVM['accuracy']:.5f}, macro-F1 {F.SEVM['macro_f1']:.5f}"],
            ["4", "Locate the crash and suggest a nearby hospital", "Achieved at demonstration level (ten hospitals, straight-line distance)"],
            ["5", "Dispatch an automated alert with location and severity", "Partly: message composed and displayed, not transmitted"],
            ["6", "Evaluate accuracy, false-alarm rate and alert latency", f"Done: see Chapter 8; alert path {F.ALERT_PATH['mean']:.0f} ms plus the 15 s window"],
        ], widths=[0.4, 3.0, 3.0], align=["c", "l", "l"], size=9.5),
        H2("9.3 Key Findings"),
        N(f"The complete chain from reading to dispatch message works, and its tests pass ({F.SMOKE_PASSED} of {F.SMOKE_TOTAL} smoke checks; {F.TEST_PASSED} of {F.TEST_TOTAL} further checks, the eight failures being input-validation gaps).",
          f"On the synthetic data a single acceleration threshold detects crashes as well as the forest; the forest's contribution is the severity grade, where it raises accuracy from {RULE['sev_accuracy']:.4f} to {F.SEVM['accuracy']:.5f}.",
          f"Detector accuracy was {F.DET['accuracy']:.4f} in every one of five repeats; severity accuracy was {F.SEEDS['mean']['sev_accuracy']:.5f} on average (SD {F.SEEDS['std']['sev_accuracy']:.5f}). These figures are upper bounds because the data are generated.",
          f"Hard braking is not mistaken for a crash, but about half of constructed pothole-like ({F.pct(po['predicted_accident_rate'], 0)}) and speed-breaker-like ({F.pct(sb['predicted_accident_rate'], 0)}) events are flagged; none starts the countdown.",
          "Light noise is tolerated; beyond a quarter of the natural spread the false-alarm rate climbs quickly (Section 8.6).",
          "The 15-second confirmation, limited to Moderate and Severe results, is the design element that keeps false alarms cheap; its length was not validated with users."),
        H2("9.4 Practical Applications"),
        B("A demonstration and teaching platform for automatic crash response.",
          "A test bench into which other detectors can be plugged with the same features, scripts and screens.",
          "A basis for a phone-based crash-notification service once real data, a messaging channel and a real hospital directory are added."),
        H2("9.5 Known Limitations"),
        P("The data are synthetic; the scores measure separability by construction and cannot be taken as real-world accuracy. Potholes, speed breakers and sensor noise degrade the detector. Nothing is transmitted, so the time to reach a human is unmeasured. "
          "The hospital directory has ten entries and no specialty information. The API has eight known input-validation gaps, the server is a development server, and no user study was carried out. "
          "The conclusion is therefore that the architecture is sound and demonstrable, that the severity model beats a threshold rule, and that the project's claims about real roads remain to be earned by data and field trials."),
    ]


def chapter10_blocks():
    return [
        H1("CHAPTER 10: FUTURE SCOPE"),
        P("The limits found in Chapters 7 and 8 define the future work. It is grouped by what it would change: the data and models, the alert and its location, the quality of the application, the deployment, and open research questions."),
        *[blk for blk in _numbered_future()],
    ]


def _numbered_future():
    out = []
    for i, blk in enumerate(future_blocks()):
        if blk[0] == "h2":
            idx = sum(1 for x in out if x[0] == "h2") + 1
            out.append(("h2", f"10.{idx} {blk[1]}"))
        else:
            out.append(blk)
    return out
