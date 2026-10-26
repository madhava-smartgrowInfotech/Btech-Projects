"""Chapter 1: Introduction (blocks are shared with the scope / limitations document)."""

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F

_FRAME = (F.API_LAT or {}).get("POST frame (real face JPEG 640x480, monitoring on)", {})
_P50 = f"{_FRAME.get('p50_ms', 0):.0f}"
_UT = (F.TESTS or {}).get("unittest", {})
_SM = (F.TESTS or {}).get("web_smoke", {})

# The six objectives exactly as the batch proposal states them (6.OBJECTIVES&PROBLEM STATEMENT.docx).
OBJECTIVES = [
    "Capture driver facial video using a webcam and detect the face and key landmarks in real time.",
    "Extract impairment cues such as eye closure ratio, blink frequency, gaze deviation and head movement.",
    "Train a deep learning classifier to distinguish a sober driver from an intoxicated one.",
    "Run inference continuously and raise an alert when the impairment score crosses a threshold.",
    "Integrate a prevention action such as an ignition warning or notification to a registered contact.",
    "Evaluate accuracy, false positive rate and performance under low light and partial occlusion.",
]

# Honest status of each objective: (status, what exists). Used here and again in Chapter 8 and the decks.
OBJECTIVE_STATUS = [
    ("Achieved", f"MediaPipe Face Landmarker on 640 x 480 frames; one frame through the web API takes about {_P50} ms (median) on the development laptop."),
    ("Partly achieved", "Eye aspect ratio, closure time, closed-eye fraction over 10 s, blink rate (shown, never used to warn) and image-plane head roll are measured. Gaze deviation is not measured."),
    ("Not achieved", "No dataset of intoxicated and sober people was available and no deep-learning model was trained. Live decisions use explainable rules. An offline nearest-centroid pipeline exists but has only run on a synthetic demonstration file."),
    ("Achieved (as rules)", "Three outputs (Normal, Possible impairment or drowsiness, Unable to assess), a reason for each, an on-screen warning and an optional bell with a 15 s cooldown. There is no learned impairment score."),
    ("Not achieved", "The system only shows a warning and sounds an optional bell. It never controls ignition, brakes or power and sends no notification to a contact."),
    ("Partly achieved", "Measured on public closed-eye data, under degraded images and on scripted streams. No accuracy for intoxication and no study with riders exists."),
]

SCOPE_IN = [
    "Real-time observation of one face from a webcam (browser or desktop), reduced to eye aspect ratio, closure time, closed-eye fraction, blink rate and head roll.",
    "Seven quality gates that refuse to assess when lighting, blur, motion, face count, eye size, eye-region contrast or eye geometry are unreliable, and a three-way output: Normal, Possible impairment or drowsiness, Unable to assess.",
    "A transparent rule engine with adjustable, validated thresholds, a per-rider calibration step and four scripted simulation scenarios for demonstrations without a camera.",
    "A numeric event history in SQLite with CSV export, an on-screen warning and an optional alert sound.",
    "A web application (React front end, FastAPI service, demo login) and the original Tkinter desktop application over the same Python modules.",
    "An offline research pipeline that validates a consented measurement CSV and trains a nearest-centroid classifier with held-out subjects, never used for live decisions.",
    "Measurements of the vision component on public data, of its behaviour under degraded images, of the rule engine on scripted streams, of speed, and an automated test suite.",
]

SCOPE_OUT = [
    "Detecting alcohol. A camera cannot confirm alcohol consumption; the system reports possible impairment or drowsiness from visible eye and head cues, and Normal never means fit to ride.",
    "A trained deep-learning classifier of sober versus intoxicated riders. No such dataset was available, so none was trained or evaluated.",
    "Gaze deviation, full three-dimensional head pose, yawning, voice and any physiological sensor.",
    f"A prevention action. The system never controls ignition, brakes or vehicle power and sends no message to a registered contact.",
    "Use on a moving vehicle, helmets with visors, dark or reflective eyewear, night riding and vibration; the prototype is for stationary demonstration.",
    "Clinical, legal or road-safety validation, regulatory approval, multi-user accounts and cloud deployment.",
]

ASSUMPTIONS = [
    "The rider's face is in front of the camera with both eyes visible, in diffuse front lighting, at 640 x 480 pixels.",
    "The default thresholds (EAR 0.21, closure 1.5 s, persistence 1.0 s, closed fraction 0.55, tilt 25 degrees) are engineering choices for a demonstration; per-rider calibration sets the EAR threshold.",
    "Closed eyes, low EAR and a tilted head are treated as possible signs of drowsiness or impairment; they have other explanations and do not prove alcohol use.",
    "A single trusted user population: the demo login is a convenience, not an identity system.",
    "The machine has Python 3.12 or newer (3.14.7 was used), Node.js 18 or newer and a webcam that the browser can open on localhost.",
]

LIMITATIONS = [
    "**No alcohol detection.** The batch title and abstract speak of intoxication, but the delivered system detects only visible eye-closure and head-tilt patterns that also arise from tiredness. It cannot tell the cause.",
    "**No trained classifier and no intoxication data.** Objective 3 was not met. The only offline model was exercised on a seeded synthetic file and says nothing about real riders.",
    "**No prevention action.** Objective 5 was not met; the system warns but does not act.",
    f"**Strict quality gates.** On 2,423 public CEW faces only {F.pct(F.CEW['coverage'])} passed the gates (the 100-pixel crops are soft), and halving the brightness of open-eye faces blocked assessment in almost every case. The gates fail safe, but availability in dim light or at low resolution is poor.",
    "**Conservative default threshold.** At EAR 0.21 about one open-eye face in seven is called closed on the public data; calibration per rider is needed, and the measurement is on still images only.",
    "**No study with people.** There is no rider, helmet, visor, glasses, vibration or demographic evaluation; the rule engine's behaviour is shown on scripted streams only.",
    "**Image-plane head roll only.** It is not full head pose and depends on camera tilt.",
    "**Security is demonstration-grade.** One shared demo account, an HMAC-signed token and open CORS for local use.",
    "**Not a medical device or a road-safety system.** The output must not be relied on to decide whether anyone may ride.",
]

CONTRIBUTIONS = [
    "A complete, runnable path from webcam frame to an explained, logged warning: landmark extraction, quality gating, calibration, a rule engine with a stated reason for every output, history and export.",
    "An honest design: three outputs including Unable to assess, quality gates that take precedence over every rule, and wording that never claims alcohol detection.",
    "A web application and API layer over the original desktop modules, with a demo login, live monitor, history, threshold editor and research screen, without changing the decision logic.",
    f"Measurements of what can be measured: eye open/closed separation of the six-point EAR on 2,423 public CEW faces (AUC {F.GEO['auc_ear_closed_vs_open']:.3f} without gates), behaviour of the quality gates under twelve degraded conditions, rule-engine behaviour on scripted streams and speed on a laptop CPU.",
    f"A reproducible verification set: {_UT.get('passed', 0)} unit tests, {_SM.get('passed', 0)} API checks, seeded measurement scripts and design documentation (ten diagrams).",
    "A candid comparison with the base paper and a list of what is missing for the batch objectives.",
]


def blocks():
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        H2("1.1 Domain overview"),
        P("Road traffic injuries remain a leading cause of death. The World Health Organization reports about 1.19 million road traffic deaths a year, a fall of 5 % since 2010, "
          f"and riders of powered two- and three-wheelers such as motorcycles account for 21 % of them {n(17)}. A rider is more exposed than a car occupant: there is no cabin, "
          "and a lapse of attention that lasts a second or two can be enough. Two conditions that degrade attention are of particular interest here: tiredness and alcohol. "
          f"Police assess impairment at the roadside with standardised field sobriety tests, which include the movement of the eyes {n(18)}, and breath testers confirm alcohol, but "
          "both are occasional checks by an officer, not continuous monitoring."),
        P("Computer vision offers a contactless way to watch the face continuously. Face landmark detectors locate dozens of points on the face in real time on an ordinary laptop "
          f"{n(10, 11, 24)}, and six points around each eye give the eye aspect ratio (EAR), a number that falls towards zero as the eye closes {n(9)}. Eye closure over time, blink "
          f"behaviour and head posture are the standard ingredients of driver-drowsiness monitors {n(1, 15, 16, 28)}. The domain of this project is therefore Artificial Intelligence and "
          "Computer Vision applied to rider and driver monitoring."),
        H2("1.2 Background and motivation"),
        P("The batch proposal is titled *Smart Alcohol Intoxication Detection and Prevention System Using AI* and asks for a software-only system that uses a webcam instead of a breath "
          f"sensor. Research on exactly this idea exists: intoxication has been classified from facial video with deep networks {n(2, 4)}, from thermal facial images {n(5, 8)} and "
          f"from a wrist-worn smartwatch in a controlled test-track study {n(3)}. Two things stand out in that literature. First, the video and thermal studies rely on purpose-collected "
          f"or scraped data; the authors of the most recent video study note that many source videos of the earlier DIF dataset {n(4)} can no longer be accessed {n(2)}. Second, "
          f"building and testing an intoxication detector needs participants who have been given alcohol, which raises safety and ethics questions {n(6)}. No such data were "
          "available to this team."),
        P(f"The base paper {n(1)} is not about alcohol. It combines the eye aspect ratio, head pose and voice commands in a fuzzy belief rule-based engine to warn about drowsiness, fatigue "
          "and distraction on an embedded board. Its eye and head cues overlap with those that the video study reports for intoxicated people, such as prolonged eye closure and head tilt "
          f"{n(2)}. That overlap is the technical basis of this project, and also its limit: the same cues have more than one cause. The project therefore builds what can honestly be "
          "built and tested with a webcam: a *Smart Rider Impairment Warning System for Two-Wheelers* that watches the eyes and head, refuses to guess when the picture is poor, and warns of "
          "possible impairment or drowsiness with the reason shown. It is a stationary demonstration prototype, not an alcohol test."),
        H2("1.3 Problem statement"),
        B("Roadside breath testing is occasional and cannot monitor a rider through an entire journey.",
          "Existing driver monitoring concentrates on drowsiness and does not target alcohol impairment specifically.",
          "Hardware alcohol sensors add cost and can be bypassed by asking another person to blow.",
          "Detection after a vehicle is already moving is too late to prevent an accident."),
        P("The problem addressed here is: *given a live camera view of a rider's face, decide continuously whether the visible eye and head behaviour shows a sustained pattern that may "
          "indicate impairment or drowsiness, say Unable to assess when the picture cannot be trusted, give the reason for every output and keep a numeric record, all through an interface "
          "that a non-expert can run.*"),
        H2("1.4 Need for the system"),
        P("The need identified by the batch is a contactless system that assesses a rider continuously and warns before harm. A camera-based monitor needs no sensor in the mouth or on the "
          "wrist, runs on hardware many riders already carry, and can react within seconds. Two further needs shaped the design. The first is explanation: a warning that says *continuous "
          "eye closure 2.6 s* can be checked by the rider and by a reviewer, whereas a bare score cannot. The second is honesty about uncertainty: a monitor that guesses in bad light would "
          "raise false alarms and be switched off, so the system returns Unable to assess instead."),
        H2("1.5 Objectives"),
        P("The batch proposal lists the following six objectives. The table after the list states plainly what was done about each; Chapter 8 gives the evidence."),
        N(*OBJECTIVES),
        TAB("Objectives and what was delivered", ["No.", "Status", "What exists"],
            [[str(i), s, t] for i, (s, t) in enumerate(OBJECTIVE_STATUS, 1)], widths=[0.5, 1.3, 4.5], size=9.5, align=["c", "l", "l"]),
        P("Two of the six objectives, the deep-learning classifier and the prevention action, were not met. The reason for the first is the absence of data, not of effort; the reason for the "
          "second is a deliberate design choice, since software that cuts the ignition of a moving two-wheeler on a rule-based guess would itself be a hazard."),
        H2("1.6 Scope"),
        P("**In scope.**"),
        B(*SCOPE_IN),
        P("**Out of scope.**"),
        B(*SCOPE_OUT),
        H2("1.7 Contributions"),
        N(*CONTRIBUTIONS),
        H2("1.8 Limitations and assumptions"),
        P("**Assumptions.**"),
        B(*ASSUMPTIONS),
        P("**Limitations.**"),
        B(*LIMITATIONS),
        H2("1.9 Organisation of the report"),
        TAB("Organisation of this report", ["Chapter", "Content"], [
            ["1  Introduction", "Domain, motivation, problem, objectives and their status, scope, contributions, limitations."],
            ["2  Literature Survey", "The base paper in depth, related work by theme, datasets and algorithms, research gap."],
            ["3  Feasibility Study", "Technical, economic, operational and schedule feasibility."],
            ["4  System Requirements and Analysis", "Existing and proposed system, functional and non-functional requirements, hardware, software, users."],
            ["5  System Design", "Architecture, workflow, data-flow diagrams, UML, database, modules and user interface."],
            ["6  Methodology and Software Implementation", "Data, preprocessing, algorithms, mathematics, calibration, application, API, security, installation."],
            ["7  System Testing", "Strategy and results of unit, integration, functional, security, performance and edge-case tests."],
            ["8  Results and Output Screens", "Measured results, comparison with the base paper, output screens, failure analysis, objectives versus outcomes."],
            ["9  Conclusion", "Summary, objectives achieved, key findings, applications, known limitations."],
            ["10 Future Scope", "Improvements, features, deployment and research directions."],
            ["Appendices", "A: important code; B: installation and user guide; C: additional screens."],
        ], widths=[2.3, 3.9]),
    ]
