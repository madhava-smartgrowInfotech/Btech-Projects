"""Chapters 9 and 10 and the sections reused by the scope, methodology, design and conclusion documents."""

import os

from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F


def _src(rel, start, end=None):
    """Text of a source file from the line containing `start` up to (not including) the line containing `end`."""
    path = os.path.join(F.CODE, rel)
    lines = open(path, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    a = next(i for i, l in enumerate(lines) if start in l)
    b = len(lines)
    if end:
        b = next(i for i in range(a + 1, len(lines)) if end in lines[i])
    chunk = lines[a:b]
    while chunk and not chunk[-1].strip():
        chunk.pop()
    return "\n".join(chunk)


def _m():
    """Frequently quoted measurements, read from the metrics files."""
    geo, cew, api = F.GEO or {}, F.CEW or {}, F.API_LAT or {}
    d = geo.get("default_threshold_0.21", {})
    b = geo.get("best_threshold_in_sample_youden", {})
    fr = api.get("POST frame (real face JPEG 640x480, monitoring on)", {})
    return dict(
        auc=geo.get("auc_ear_closed_vs_open", 0), recall=d.get("recall", 0), spec=d.get("specificity", 0), acc=d.get("accuracy", 0),
        fp=d.get("fp", 0), tn=d.get("tn", 0), best_thr=b.get("threshold", 0), best_acc=b.get("accuracy", 0),
        coverage=cew.get("coverage", 0), n=cew.get("images_total", 0), p50=fr.get("p50_ms", 0),
        unit=(F.TESTS or {}).get("unittest", {}).get("tests", 20), smoke=(F.TESTS or {}).get("web_smoke", {}).get("checks", 34),
    )


SCOPE_IN = [
    "A Windows laptop prototype that watches one person's face through a webcam and estimates possible drowsiness or impairment from visible eye and head cues (eye aspect ratio, closure time, closed-eye fraction, blink rate and image-plane head roll).",
    "Transparent, explainable rules with three outputs - *Normal*, *Possible impairment or drowsiness*, *Unable to assess* - and a stated reason for each verdict.",
    "Quality gating: no verdict when lighting, sharpness, motion, face count, eye size or eye geometry is unreliable.",
    "Personal calibration of the closed-eye threshold from 8-15 s of the rider's own open eyes, and six validated, editable thresholds.",
    "On-screen warning and an optional bell with a cooldown; four scripted simulation scenarios for demonstrations without a camera.",
    "Numeric event history in SQLite with CSV export; no video or face image is ever stored.",
    "Two front ends over the same Python modules: the original Tkinter desktop application and a FastAPI + React web application with a demo login.",
    "An offline, subject-disjoint evaluation pipeline for a consented, labelled measurement CSV (never used by the live rules).",
    "Measurements of the eye-state component on public data, of the rule engine on scripted streams and of speed, plus 20 unit tests and a 34-check API smoke test.",
]

SCOPE_OUT = [
    "**Alcohol detection.** A camera cannot confirm alcohol consumption; the system never reports alcohol.",
    "A trained deep-learning sober-versus-intoxicated classifier (no intoxication dataset was available).",
    "Gaze deviation, saccades, nystagmus, facial expression, voice or any non-visual signal.",
    "A prevention action: ignition lock, vehicle immobilisation or notification of a registered contact. The system never controls ignition, brakes or vehicle power.",
    "In-vehicle or on-motorcycle deployment, helmet and visor handling, vibration, night riding or an embedded device.",
    "Medical, legal or road-safety certification; use by the public; any claim of fitness to ride (*Normal* does not mean fit to ride).",
    "Multi-user accounts, a production identity system, cloud hosting or mobile applications.",
    "Full 3D head pose; only image-plane roll is computed.",
]

ASSUMPTIONS = [
    "The rider's face and both eyes are visible to the camera, with diffuse front lighting and no dark or reflective eyewear.",
    "One person is in front of the camera; the laptop is secured and the demonstration is stationary.",
    "Calibration is done while the rider is naturally alert with eyes open; the system cannot certify that the rider was alert.",
    "A webcam delivers roughly 15 to 30 frames per second at 640 x 480 pixels, and the browser (Chrome or Edge on `localhost`) allows camera access.",
    "The default thresholds are engineering choices for demonstration, not measured safety specifications.",
    "The Google Face Landmarker model is downloaded once and run locally; no internet access is needed during use.",
    "Anyone who loads research data holds the participants' consent; a `consent=yes` column cannot verify it.",
]

LIMITATIONS = [
    "**Not an alcohol detector.** Closed eyes, low EAR and head tilt have many causes (sleep loss, medication, illness, eye shape); open eyes do not establish alertness, and sober people can be flagged.",
    "**No intoxication data.** No labelled sober/intoxicated recordings exist in this project, so no accuracy for intoxication is claimed, and the deep-learning classifier requested in the objectives was not built.",
    "**No prevention action.** The system warns on screen and by bell only; it cannot stop a vehicle or notify a contact.",
    "**Conservative default threshold.** On public data the default EAR threshold of 0.21 labels about one open eye in seven as closed; calibration is the intended remedy but was not measured per person.",
    "**Strict quality gates.** Roughly 44 % of the 100-pixel test images pass; halving the image brightness already blocks assessment; a few sunglasses images passed the gates.",
    "**Slow reaction.** With the default rules a closure shorter than about 2.5 s never warns, and the closed-fraction rule needs 8-10 s of history.",
    "**Single data source and machine.** The eye-state measurement uses one public still-image dataset whose classes come from different sources; no helmet, visor, glasses-in-motion, vibration, night or demographic study was done; all timings come from one i5-12500 laptop without a GPU.",
    "**Image-plane roll only.** Head roll is tilt in the image, not yaw or pitch, and depends on camera placement.",
    "**Prototype security.** Demo credentials are displayed on the login page, CORS is open, and no penetration test was performed.",
    "**Research pipeline untested on real data.** The offline classifier has only been run on a generated synthetic file, which is flagged as such.",
]


# ------------------------------------------------------------------ methodology document extras
def novelty_blocks():
    m = _m()
    return [
        P(f"The base paper {n(1)} is an embedded driver-monitoring study that combines a new eye feature (EAR-4), head pose and a voice interface in a fuzzy belief rule-based engine. This project does not "
          "reproduce it and does not try to beat its numbers; its contribution is of a different, more modest kind. The table separates what is new in this work from what is standard practice that it reuses."),
        TAB("Novelty against the base paper", ["Aspect", "Base paper", "This project", "Novel here?"], [
            ["Target", "Drowsiness, fatigue, distraction", "Drowsiness-type impairment indicator for a two-wheeler rider; explicitly not alcohol", "Different framing; no new detection capability"],
            ["Decision logic", "Fuzzy belief rule base fusing EAR-4, head pose, voice", "Transparent duration rules with persistence, a reason string and quality precedence", "Simpler; the **explainability and the refusal to guess** are the point"],
            ["Signal quality", "Not the focus", "Seven quality gates; *Unable to assess* as a first-class output; gate behaviour measured under degradation", "**Yes** for this project"],
            ["Personalisation", "Adaptive threshold from over 300 frames", "Calibration with acceptance tests (>= 40 frames, >= 70 % accepted, low variance) and a clipped 0.72 x median rule", "Comparable idea, different recipe"],
            ["Delivery", "Jetson Orin Nano, buzzer", "Desktop app and a FastAPI + React web app sharing one core, demo login, history, CSV export, threshold editor", "**Yes**: a reusable software layer"],
            ["Evaluation honesty", "NTHU-DDD frame classification", "Eye-state component on CEW with and without gates; degraded-condition test; scripted-stream study of the rules; synthetic results flagged", "**Yes**: measured limits are reported"],
            ["Offline learning", "Random Forest and XGBoost on EAR features", "Subject-disjoint window evaluation with a nearest-centroid model, never used live", "Pipeline only; no real-data result"],
            ["Voice, EAR-4, fuzzy engine", "Core of the paper", "Not implemented", "Not reproduced"],
        ], widths=[1.1, 1.6, 2.2, 1.4], size=9),
        P(f"**What is not new.** Six-point EAR {n(9)}, MediaPipe landmarks {n(10, 11)}, closed-fraction ideas related to PERCLOS {n(15)}, blink-rate fatigue cues {n(16)} and subject-wise evaluation are established. "
          f"The project's value lies in assembling them into one inspectable, tested system and in stating its measured behaviour: an EAR ROC AUC of {m['auc']:.3f} on public data, a default threshold that is too conservative, gates that fail safe but strictly, "
          "and a warning that needs about 2.5 s of closure."),
    ]


def contribution_blocks():
    m = _m()
    return [
        P("The contributions of the project, in order of importance:"),
        N("An explainable, quality-gated rule engine for eye closure and head tilt with three outputs, a reason for every verdict, evidence persistence, a cooldown and personal calibration (`core.py`).",
          "A complete software layer around it: a MediaPipe vision module, a Tkinter desktop application, a FastAPI service and a React interface with demo login, history, thresholds and research screens, all sharing the same modules.",
          f"A measured characterisation of the eye-state component on {m['n']:,} public face images: ROC AUC {m['auc']:.3f}, and the finding that the default threshold of 0.21 is conservative while about {m['best_thr']:.2f} separates better.",
          "A measured characterisation of the quality gates under software-degraded conditions, showing that they fail safe for darkness, blur and covered eyes but are strict in dim light.",
          "A scripted-stream study of the rules (warning latency, false alerts, parameter trade-off) that makes the design consequences, such as the 2.5 s minimum closure, explicit.",
          "An offline evaluation pipeline that enforces consent, subject-disjoint splits and window-level metrics, and labels synthetic demonstrations as synthetic.",
          f"An automated check suite ({m['unit']} unit tests and {m['smoke']} API checks) plus reproducible measurement scripts for every number in this report.",
          "A plain statement of what was not achieved: no alcohol detection, no deep-learning classifier, no prevention action, no gaze features and no rider study."),
    ]


# ------------------------------------------------------------------ scope document
def scope_blocks():
    return [
        H2("1.1 In scope"),
        TAB("In scope", ["#", "Item"], [[str(i), s] for i, s in enumerate(SCOPE_IN, 1)], widths=[0.4, 5.9], align=["c", "l"], size=10.5),
        H2("1.2 Out of scope"),
        TAB("Out of scope", ["#", "Item"], [[str(i), s] for i, s in enumerate(SCOPE_OUT, 1)], widths=[0.4, 5.9], align=["c", "l"], size=10.5),
        P("The boundary is deliberate. The batch title speaks of alcohol intoxication detection and prevention; what could honestly be built and measured in the available time is a drowsiness-type "
          "impairment indicator with explainable rules. Everything that would turn it into an alcohol test or a road-safety device - labelled intoxication data, a trained classifier, vehicle integration, "
          "validation on riders and regulatory approval - lies outside the project and is listed as future work."),
    ]


def assumption_blocks():
    return [B(*ASSUMPTIONS)]


def limitation_blocks():
    m = _m()
    out = [B(*LIMITATIONS)]
    out += [
        P(f"**Evidence from the measurements.** On {m['n']:,} public face images the EAR separates closed from open eyes with an AUC of {m['auc']:.3f}, but at the default threshold {m['fp']} of {m['fp'] + m['tn']:,} open eyes "
          f"are called closed (specificity {F.pct(m['spec'])}); only {F.pct(m['coverage'])} of the images pass the shipped quality gates. These figures come from one dataset, one machine and one run per measurement and carry no confidence interval."),
        TAB("Risks and mitigations", ["Risk", "Mitigation in the project"], [
            ["Output mistaken for an alcohol test or a fitness-to-ride certificate", "Wording *Possible impairment or drowsiness*; disclaimer on every screen and in the README; *Normal* is accompanied by \"This does not certify safety\""],
            ["False warning from a naturally narrow eye", "Personal calibration; thresholds editable within bounds; persistence before any warning"],
            ["A guess made on a bad image", "Quality gates take precedence; *Unable to assess* clears the evidence and restarts warm-up"],
            ["Over-reading a synthetic result", "Synthetic report carries a **Synthetic data** banner; simulation events are labelled SIMULATION"],
            ["Privacy of faces", "Frames live in memory only; the database stores numbers; no telemetry or upload"],
            ["Unauthorised access", "HMAC-signed expiring token, 401 on protected routes; local demo account only, no real personal data should be loaded"],
        ], widths=[2.2, 4.1], size=10),
    ]
    return out


def not_measured_blocks():
    return [
        P("The following were not measured and are therefore stated as gaps, not estimated:"),
        B("Any accuracy, sensitivity or false-alarm rate for alcohol intoxication, or for sober versus intoxicated classification.",
          "Any deep-learning model: none was trained.",
          "Performance with real riders, helmets, visors, glasses, vibration, night riding or different skin tones and ages.",
          "Gaze deviation and any prevention action (ignition lock or contact notification), which were not implemented.",
          "A real labelled, consented dataset through `research.py`: the pipeline has only been run on a generated synthetic file.",
          "Long-duration false-alarm rate on real people (the 300 x 180 s streams are generated).",
          "Whether calibration beats a fixed lower threshold, because the test images contain no repeated subjects.",
          "Audible loudness of the alert bell, accuracy of variable-frame-rate video extraction, load and concurrency of the API, and browsers other than Chromium."),
    ]


# ------------------------------------------------------------------ design document extras
def walkthrough_blocks():
    return [
        H2("3.1 Eye aspect ratio and head roll"),
        P("`eye_aspect_ratio` takes the six perimeter points of one eye and returns the mean of the two vertical distances divided by the horizontal width; it rejects non-finite points and a degenerate width. "
          "`head_roll` returns the image-plane angle of the line through the two eye centres, with the horizontal distance taken in absolute value so that it stays near zero for an upright face."),
        CODE(_src("core.py", "def eye_aspect_ratio", "class RiskEngine")),
        H2("3.2 The decision step of the rule engine"),
        P("Each observation first passes the quality and timing test (shown earlier in `update`); only then are the three rules evaluated. A reason is collected for each rule that holds, the evidence timer "
          "starts on the first one, and a warning needs the timer to reach the persistence time with at least two seconds of reliable history. Alerts are rate-limited by the cooldown."),
        CODE(_src("core.py", "        reasons = []", "        return Decision(state, reason, 'Good'")),
        H2("3.3 Quality gates in the vision module"),
        P("Whole-frame gates (brightness, sharpness, motion) run before any landmarking, so a bad frame costs almost nothing. After landmarking, each eye is checked for size, position and contrast, "
          "and the two eyes must agree."),
        CODE(_src("vision.py", "        quality = 'Good'", "        o = Observation(now, quality=quality")),
        CODE(_src("vision.py", "        for eye in eyes:", "        ears = [eye_aspect_ratio")),
        H2("3.4 Personal calibration"),
        P("Calibration accepts only good, plausible, upright frames. After 8 s it needs 40 usable frames, at least 70 % acceptance and a steady EAR before it sets the threshold to 0.72 of the median; "
          "after 15 s it fails and the previous threshold is kept."),
        CODE(_src("core.py", "class Calibration", "def simulate")),
        H2("3.5 Session glue for the web application"),
        P("The web layer adds no decision logic. `RiderSession.consume` receives an observation from the vision module (or the simulator), drives calibration or the rule engine, and writes an event "
          "when the state changes, every five seconds, or when an alert fires. A fresh SQLite connection is opened per call because connections are bound to their thread."),
        CODE(_src("backend/session.py", "    def consume(self, o):", "    def _display")),
        H2("3.6 Signed demo token"),
        P("The demo login issues a token made of a base64 payload (e-mail and expiry) and its HMAC-SHA256 signature, verified with a constant-time comparison."),
        CODE(_src("backend/main.py", "def _sign", "class Login")),
    ]


def decision_blocks():
    return [
        TAB("Decisions and reasons", ["Decision", "Alternatives considered", "Reason", "Consequence"], [
            ["Explainable rules for the live verdict", "Train a CNN or sequence model on facial video", "No labelled intoxication data existed; rules can be read, tested and justified, and every verdict has a reason", "No learned accuracy; behaviour is only as good as the thresholds"],
            ["Six-point EAR with a 3-sample median", "EAR-4 of the base paper; deep eye-state classifier", "Standard, cheap, needs no training, and measurable (AUC 0.989 on CEW)", "Conservative default threshold; narrow eyes read as closed"],
            ["Quality gates before the rules; *Unable to assess* output", "Always produce Normal or Warning", "A wrong confident answer is worse than none for a safety indicator", "Low availability in dim light and on soft images"],
            ["Persistence of 1.0 s on top of 1.5 s closure", "Warn at the first closed frame; shorter rules", "Blinks (0.1-0.4 s) and slow blinks must not alarm; sweep shows 0 alerts per hour with 10 % slow blinks", "A closure under about 2.5 s never warns"],
            ["Personal calibration, threshold = 0.72 x median EAR", "Fixed 0.21 or 0.18", "Eye shape differs between people; calibration is clipped to 0.12-0.32 and refused on poor data", "Calibration assumes the rider is alert when calibrating"],
            ["MediaPipe Face Landmarker, video mode, local", "dlib, cloud face API", "Runs on a laptop CPU at about 30 frames per second without uploads", "Video-mode tracking makes unrelated stills depend on the previous one"],
            ["Frames kept in RAM; numeric SQLite events only", "Store clips for later review", "Privacy; nothing sensitive to leak or to delete", "No replay of what the camera saw"],
            ["FastAPI layer beside the unchanged Tkinter app", "Rewrite the core for the web", "`core`, `vision`, `storage` and `research` are reused as they are; one set of tests covers both", "Two front ends to maintain"],
            ["Browser camera, frames posted to the server", "Server opens the webcam", "Works in any browser on `localhost`; per-tab sessions", "Needs Chrome or Edge on `localhost` or https"],
            ["HMAC token for the demo login", "Session store, OAuth", "Stateless and simple for a local demonstration", "Demo credentials visible; not production authentication"],
            ["Offline research pipeline never used live", "Switch live decisions to the learned model", "Metrics from synthetic or tiny data must not drive warnings", "The learned path is inert until real data exist"],
            ["Synthetic sample flagged by file hash", "Hide the synthetic option", "Lets reviewers see the screen working without misleading them", "Extra code to detect and label the sample"],
        ], widths=[1.5, 1.4, 2.3, 1.1], size=8.5),
    ]


# ------------------------------------------------------------------ chapters 9 and 10
def conclusion_blocks():
    m = _m()
    return [
        H1("CHAPTER 9: CONCLUSION"),
        H2("9.1 Summary"),
        P(f"The project set out to build a {F.TITLE.lower()}. What it delivers is narrower and is stated here without softening: the **{F.PRODUCT}**, a stationary demonstration prototype that reads "
          "a person's eyes and head through a webcam and returns *Normal*, *Possible impairment or drowsiness* or *Unable to assess*, with the reason. A MediaPipe face-landmark module, a six-point eye aspect ratio, "
          "seven quality gates, personal calibration and explainable duration rules run on a laptop CPU at about 30 frames per second; a Tkinter application and a FastAPI + React application expose them, and a numeric "
          "event history, CSV export, a threshold editor and an offline evaluation pipeline complete the system. **It does not detect alcohol, it contains no deep-learning classifier, and it takes no prevention action.**"),
        H2("9.2 Objectives achieved"),
        P("Of the six objectives in the batch description, two were achieved (real-time face and landmark capture; continuous inference with an alert), two were achieved in part (impairment cues - without gaze deviation; "
          "evaluation - on eye state and degraded conditions, not on intoxication), and two were not achieved: training a deep-learning sober-versus-intoxicated classifier and integrating a prevention action. "
          "The reasons are plain. No labelled intoxication recordings were available to the team, and a classifier trained on synthetic data would have been meaningless; and a prevention action needs vehicle integration that a laptop "
          "demonstration cannot provide. Section 8.11 gives the objective-by-objective table."),
        H2("9.3 Key findings"),
        B(f"On {m['n']:,} public face images the six-point EAR computed by the shipped pipeline separates closed from open eyes with a ROC AUC of {m['auc']:.3f}; at the default threshold of 0.21 closed-eye recall is {F.pct(m['recall'])} but open-eye "
          f"specificity is only {F.pct(m['spec'])}. A threshold near {m['best_thr']:.2f} gives {F.pct(m['best_acc'])} accuracy in-sample, so the default is conservative and personal calibration matters.",
          f"The quality gates fail safe (no verdict) for darkness, blur, opaque sunglasses and a covered eye, but they are strict: only {F.pct(m['coverage'])} of the 100-pixel images pass, and halving brightness already blocks assessment.",
          "On scripted streams the default rules never fire on normal blinks and warn only after about 2.5 s of continuous closure; a closure of two seconds goes unwarned. Closure and persistence trade sensitivity against false alerts, and their sum is what counts.",
          f"A camera frame costs about {m['p50']:.0f} ms through the API on a laptop CPU, so the design is not computation-limited.",
          f"The software is verified by {m['unit']} unit tests and {m['smoke']} API checks, and every figure in this report can be regenerated by the measurement scripts.",
          "The offline research pipeline works mechanically, but its only report comes from a synthetic file; it is a pipeline check, not a result."),
        H2("9.4 Practical applications"),
        B("A teaching and demonstration tool for how eye-based fatigue cues, quality gating and explainable rules work, with scripted scenarios that need no camera.",
          "A reusable software scaffold - vision module, rule engine, API, web interface and evaluation pipeline - for a future study that does have labelled data.",
          "A drowsiness-type warning prototype that could, after validation on riders, support a fatigue-awareness feature; it should not be used to decide whether anyone is fit to ride."),
        H2("9.5 Known limitations"),
        B(*LIMITATIONS[:7]),
    ]


def chapter9_blocks():
    return conclusion_blocks()


def future_blocks():
    return [
        H1("CHAPTER 10: FUTURE SCOPE"),
        H2("10.1 Improvements to the model"),
        B("**Collect a consented, labelled sober/intoxicated video dataset** under a documented protocol with measured blood or breath alcohol, and evaluate with subject-disjoint splits through the existing `research.py`. "
          f"Companion work reports high accuracy on its own video data {n(2)}, but its source videos are not generally available, so new data would be needed.",
          "**Add gaze and eye-movement features** (saccade speed, nystagmus-like jitter, gaze deviation) that the objectives name and that standardised field tests use as cues " + n(18) + ".",
          "**Learn a temporal model** over windows of EAR, roll and gaze features, and compare it with the rules on the same held-out subjects before letting it influence live decisions.",
          "**Tune thresholds on held-out subjects**, replacing the in-sample 0.17 suggestion; compare personal calibration with a fixed lower threshold using several images per person.",
          "**Make the gates helmet-, visor- and low-light-aware**: replace the brightness-sensitive sharpness gate by a scale-free measure and test on night and helmet footage."),
        H2("10.2 Additional features"),
        B("A prevention action: a vehicle interface that inhibits ignition or notifies a registered contact, designed with a safety review and a fail-safe default.",
          "A voice or haptic channel and wearable sensing, in the spirit of the base paper's voice interface " + n(1) + " and of smartwatch-based drunk-driving detection " + n(3) + ".",
          "Real user accounts, per-rider calibration profiles and an audit log.",
          "A reviewer screen that lets a researcher label events, feeding the evaluation pipeline."),
        H2("10.3 Scalability and deployment"),
        B("Run the vision path on an embedded device with an infrared camera, as the base paper does on a Jetson Orin Nano, and measure frame rate, heat and power on the motorcycle.",
          "Package the API and the built front end in a container behind a reverse proxy with HTTPS, replace the demo token by a proper identity provider, and add rate limits.",
          "Add monitoring of latency, the share of *Unable to assess* and alert counts to detect drift in the field."),
        H2("10.4 Further research"),
        B("A formal user and rider study with ethics approval, including false-alarm tolerance, alert design and over-reliance on a *Normal* verdict.",
          "Fusion of camera cues with driving behaviour or wearable signals, since wrist-based detection has shown promise on a test track " + n(3) + ".",
          "Fairness testing across skin tones, ages, eye shapes and eyewear, which this project could not do.",
          "Comparison of EAR variants, such as the upper-lid EAR-4 of the base paper, against six-point EAR on the same data."),
    ]


def chapter10_blocks():
    return future_blocks()
