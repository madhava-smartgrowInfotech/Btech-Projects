"""Chapter 1: Introduction."""

from . import facts as F
from .blocks import B, H1, H2, N, P, TAB
from .refs import CITE as R

OBJECTIVES = [
    "Collect and preprocess smartphone accelerometer, gyroscope, speed and GPS data for normal driving and collision events.",
    "Train a classifier that distinguishes genuine accidents from potholes, speed breakers and hard braking.",
    "Build a severity model that grades an impact as minor, moderate or severe.",
    "Use GPS to locate the crash and identify a suitable nearby hospital.",
    "Dispatch an automated alert carrying location and severity to emergency contacts and medical services.",
    "Evaluate detection accuracy, false alarm rate and end-to-end alert latency.",
]


def c(*keys):
    return ", ".join(f"[{R[k]}]" for k in keys)


def blocks():
    pot, sb = F.OOD["pothole"], F.OOD["speed_breaker"]
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        P(f"This chapter introduces the domain of the project, the motivation for building {F.PRODUCT}, the problem it addresses, the objectives set for it, the scope that was actually delivered, "
          "the contributions, and the limitations and assumptions that govern every result reported later. It ends with a map of the rest of the report. Throughout the report, "
          "statements about what the system measured are separated from statements about what a real deployment would require."),

        H2("1.1 Domain and Background"),
        P("The project belongs to the domain of Artificial Intelligence and Machine Learning applied to road safety and emergency response. Road traffic injuries are a leading public-health "
          f"problem, and the World Health Organization publishes a global status report on road safety for exactly this reason [{R['who']}]. Where a serious crash happens matters as much as how serious it is: "
          "a collision on a quiet stretch may go unreported for a long time because the victims cannot call for help, and the first hour after a severe injury, often called the golden hour, "
          "is the period in which treatment is most effective."),
        P("Modern smartphones already carry the sensors that a crash detector needs: a three-axis accelerometer, a three-axis gyroscope, a GPS receiver from which speed is derived, and a mobile data connection. "
          "A crash shows up in these sensors as a large, brief spike of acceleration and rotation together with a sudden loss of speed. The difficulty is that other events resemble it in part: "
          "hard braking produces a large negative acceleration, and a pothole or a speed breaker produces a sharp vertical shock. A usable detector must therefore be able to tell these apart, "
          "and it must also say how serious the impact is, because a minor scrape and a critical collision call for different responses."),
        P(f"Machine learning is a natural tool for this separation. Tree ensembles such as the random forest [{R['breiman']}], available in scikit-learn [{R['sklearn']}], handle a small set of numeric features, "
          "train in seconds and return class probabilities. Published work on accident severity has mostly applied such models, and later deep models, to recorded crash reports after the event "
          f"[{R['lin']}], [{R['chen']}], [{R['sameen']}], [{R['zheng']}], [{R['hamdan']}]. The base paper assigned to this batch, Wang, Liang and He [{R['base']}], is in this line: it predicts injury, fatal and "
          "property-loss severity from police-reported crash records with a multi-task FT-Transformer. ResQAI takes the idea of grading severity, but moves it from the archive to the moment of impact: "
          "it works on a sensor reading, not on a finished report, and it connects the grade to an alert."),

        P("The eleven features that ResQAI uses are the quantities such a phone reports or can derive. They are the three acceleration components and their magnitude, the three rotation-rate components and their magnitude, "
          "the speed before the event, the change in speed over the event, and the jerk, which is the rate of change of acceleration. A normal reading sits near one standard gravity (9.81 m/s²) of acceleration magnitude, "
          "hard braking adds a sustained deceleration, and a crash adds a large, short burst in acceleration, rotation and jerk. The classifiers learn the boundaries between these patterns from examples."),
        P("An automatic alert raises a second question beyond detection: who confirms it. A system that sends an alert on every impact will, sooner or later, send one on a dropped phone or a violent pothole, "
          "and every wrong alert costs responders time and costs the system its credibility. The design used here therefore treats confirmation as a first-class step: the system proposes, the occupant disposes, and silence is read as an inability to respond."),

        H2("1.2 Motivation"),
        B("Victims are often unable to call for help, so an accident on a remote road can go unreported until a passer-by arrives.",
          "Existing automatic crash detection typically reports that an impact occurred, with no indication of how serious it was; without severity, responders cannot prioritise.",
          "Dedicated in-vehicle crash hardware is costly and absent from most two-wheelers and older cars, whereas a smartphone is already present.",
          "False alarms waste emergency resources and teach users to ignore the system, so any automatic alert needs a way for the occupant to say \"I am fine\".",
          "The published severity models of the literature survey work on recorded datasets; none closes the loop from live sensing through severity grading to a located, prioritised alert."),

        H2("1.3 Problem Statement"),
        P("Accidents on remote stretches often go unreported until a passer-by intervenes. Existing crash detection reports only that an impact occurred, with no indication of how serious it is, "
          "and without severity information responders cannot prioritise between a minor scrape and a critical collision. Dedicated in-vehicle crash hardware is costly and absent from most two-wheelers and older cars."),
        P(f"**Problem statement.** Design and build a smartphone-based system that detects a crash from motion-sensor readings, grades its severity, gives the occupant a short window to cancel a false alarm, "
          "and then produces a located, prioritised emergency alert that names the nearest hospital. The system must be evaluated for detection accuracy, false-alarm rate and the time the alert path takes."),

        H2("1.4 Need of the System"),
        P("The need is for a low-cost, hardware-free chain that runs end to end: sense, detect, grade, confirm, locate, alert. Each link exists separately in the literature. Sensor-based prototypes such as GreenBox "
          f"[{R['greenbox']}] detect an impact with push-buttons and an inertial sensor and send an SMS with the location, but use fixed thresholds and give no severity grade. Camera-based work such as CIRS "
          f"[{R['cirs']}] detects accidents in video frames and describes the scene, but needs fixed cameras. Severity-prediction papers grade crashes but only from recorded reports. "
          "ResQAI is built to join the links in one pipeline that a phone could feed, and to show clearly how the confirmation step prevents a mistaken alert from being sent."),

        H2("1.5 Objectives"),
        P("The six objectives set in the batch project definition are listed below. Their status at the end of the project is measured in Chapter 8 and summarised in the table that follows;"
          "the short version is that the pipeline works end to end on synthetic data, and that two objectives are only partly met."),
        N(*OBJECTIVES),
        TAB("Status of the six project objectives at the end of the project",
            ["No.", "Objective (short form)", "Status", "What was done"],
            [["1", "Collect and preprocess smartphone sensor data", "Partly",
              f"A generator of {F.N_TOTAL:,} synthetic events and an 11-feature pipeline; no real smartphone recordings were collected"],
             ["2", "Separate accidents from potholes, speed breakers, hard braking", "Partly",
              f"Hard braking handled (0 of {F.SHIP['per_event_kind']['harsh_brake']['n']} test braking events flagged); potholes and speed breakers are not in the training data and a probe flags about half of them"],
             ["3", "Severity model: minor, moderate, severe", "Achieved on synthetic data",
              f"Accuracy {F.f5(F.SEVM['accuracy'])}, macro-F1 {F.f5(F.SEVM['macro_f1'])} on {F.N_TEST:,} held-out events"],
             ["4", "Locate the crash and a nearby hospital", "Achieved at demo level",
              f"Browser geolocation and haversine ranking over a {F.N_HOSPITALS}-hospital Hyderabad directory"],
             ["5", "Automated alert to contacts and medical services", "Partly",
              "Alert message and id composed and shown, with tap-to-call 108 and 112; nothing is sent by SMS, call or e-mail"],
             ["6", "Evaluate accuracy, false-alarm rate, latency", "Done",
              f"Section 8; alert path {F.ALERT_PATH['mean']:.0f} ms on loopback plus the 15 s confirmation window"]],
            widths=[0.4, 2.1, 1.1, 2.9], align=["c", "l", "l", "l"], size=9.5),

        H2("1.6 Scope of the Project"),
        P("Within scope: a Flask API with simulated sensor input; two random-forest models (accident detector and severity predictor) trained on a synthetic dataset; the 15-second confirmation mechanism; "
          "GPS location from the browser; nearest-hospital ranking over a small directory; a drafted dispatch message; account registration and login; a React console with a live monitor, a manual override form and an emergency-response map; "
          "and the evaluation scripts that produced every number in this report."),
        P("Outside scope: a native mobile application, reading real sensors, continuous background sensing, real SMS, call or e-mail delivery, a live hospital or routing service, multi-user alert history stored on a server, "
          "and any clinical or regulatory validation. Chapter 10 of the report and the separate scope document set these boundaries out in detail."),

        P(f"The delivered system is a Flask back end on port {F.API_PORT} and a React console on port {F.WEB_PORT}. The back end exposes five application endpoints (health, simulate, predict, hospitals and emergency) and four account routes, "
          f"loads two scikit-learn models and a scaler once at start-up, and stores two JSON files. The console offers five scenario buttons, a live stream that sends a new reading every {F.LIVE_MS / 1000:.1f} seconds, "
          "a form for manual values, a confirmation dialog, a map with the accident and hospital markers, and an event log. Chapter 5 describes the design and Appendix B the installation."),

        H2("1.7 Contributions"),
        N("An end-to-end, runnable pipeline that connects a sensor-style reading to detection, severity grading, occupant confirmation, location, hospital ranking and a drafted alert.",
          "A two-model design in which a detector gates a four-level severity model, and a client-side rule that only Moderate and Severe results start the 15-second confirmation, so that Minor events are logged and not escalated.",
          f"An evaluation that goes beyond the single shipped test score: a five-seed repeat, baselines, feature ablation, noise sweep, threshold sweep and an out-of-distribution probe, which together show that on this synthetic data detection is trivially separable and that the severity model is the part that adds value over a threshold rule.",
          "A documented set of tested behaviours: 33 of 33 smoke checks pass, and a 55-check suite (unit, edge-case and security) passes 47, with the 8 failures reported as findings and not hidden.",
          "A full web console (React 19 and Vite 8) with theme switch, accessible dialogs, a live sensor trace and a response map."),
        P(f"The headline results, all on synthetic data, are these. The detector scores accuracy, precision and recall of {F.f4(F.DET['accuracy'])} on {F.N_TEST:,} held-out events. "
          f"The severity model scores accuracy {F.f5(F.SEVM['accuracy'])} with one error in {F.N_TEST:,} events, a Minor crash rated Moderate; over five seeds the mean accuracy is {F.f5(F.SEEDS['mean']['sev_accuracy'])}. "
          f"Of the events that should not start the countdown, {F.pct(F.ALERT['false_alarm_rate'], 3)} did. The alert path from reading to composed message averages {F.ALERT_PATH['mean']:.0f} ms on a local machine, and the confirmation window adds a fixed {F.COUNTDOWN_S} seconds. "
          "Chapter 8 qualifies each of these with the baselines and probes that put them in context."),

        H2("1.8 Limitations and Assumptions"),
        P(f"**Synthetic data.** The project ships no real crash recordings. The {F.N_TOTAL:,} training events are drawn from hand-written distributions in train_models.py, and the simulated readings used by the console come from the same distributions. "
          f"The detector scores accuracy {F.f4(F.DET['accuracy'])} on the {F.N_TEST:,} held-out events, but a one-line threshold on acceleration magnitude scores the same, because the generator leaves a gap between the largest braking event (13.2 m/s²) and the smallest crash (15.3 m/s²). "
          "These figures show that the pipeline is correct and the classes are separable by construction; they do not predict performance on real roads."),
        P(f"**Road-surface events.** Potholes and speed breakers are not in the training data. A probe of {pot['n']:,} constructed pothole-like and {sb['n']:,} speed-breaker-like events (our own construction, not recordings) was flagged as an accident "
          f"{F.pct(pot['predicted_accident_rate'])} and {F.pct(sb['predicted_accident_rate'])} of the time; none reached Moderate or Severe, so no alert would start, but the detector cannot be said to reject them."),
        P("**No transmission.** The dispatch message is composed and displayed; the application has no SMS, e-mail or telephony gateway. The hospital directory has ten entries for Hyderabad. "
          "The base paper's numbers cannot be compared with this project's, because its data, task and labels are different (Chapter 8)."),
        P("**Assumptions.** The phone is assumed to be rigidly mounted so that the axes are consistent; the user is assumed to carry a charged phone with location permission granted; "
          "the occupant is assumed able to respond to the countdown if conscious; and a data connection is assumed to exist at the moment of dispatch."),

        H2("1.9 Organisation of the Report"),
        TAB("Organisation of the report",
            ["Chapter", "Title", "Content"],
            [["1", "Introduction", "Domain, motivation, problem, objectives, scope, contributions, limitations"],
             ["2", "Literature Survey", "Base paper, related work by theme, datasets and algorithms, research gap"],
             ["3", "Feasibility Study", "Technical, economic, operational and schedule feasibility"],
             ["4", "System Requirements and Analysis", "Existing and proposed system, requirements, hardware, software, roles"],
             ["5", "System Design", "Architecture, workflow, DFDs, UML, database, modules, user interface"],
             ["6", "Methodology and Software Implementation", "Data, preprocessing, algorithms, training, API, security, installation"],
             ["7", "System Testing", "Strategy, unit, integration, functional, security, edge cases, performance"],
             ["8", "Results and Output Screens", "Model performance, output screens, comparison, failure analysis, objectives against outcomes"],
             ["9", "Conclusion", "Summary, objectives achieved, findings, applications, limitations"],
             ["10", "Future Scope", "Improvements, features, scalability, further research"]],
            widths=[0.7, 2.4, 3.4], align=["c", "l", "l"], size=10),
        P("The references and three appendices follow: important code (Appendix A), installation and user guide (Appendix B) and additional screens (Appendix C)."),
    ]
