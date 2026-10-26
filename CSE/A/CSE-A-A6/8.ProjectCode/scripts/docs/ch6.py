"""Chapter 6: Methodology and software implementation."""

from .appendix import source
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F


def _c():
    """Numbers used in the text, read from the measurement files."""
    cew, geo = F.CEW, F.GEO
    return cew, geo


def methodology_blocks():
    cew, geo = _c()
    return [
        H2("6.1 Overall methodology"),
        P("The work has two parts that share the same measurement code. In the **runtime pipeline**, a frame from the webcam (or a scripted simulation sample) is checked for image "
          "quality, a pre-trained face landmark model locates the eyes, the eye aspect ratio and head roll are computed, and a transparent rule engine turns the last few seconds of "
          "measurements into one of three answers: Normal, Possible impairment or drowsiness, or Unable to assess. In the **evaluation part**, the components of that pipeline are "
          "measured separately on the data that exist: the eye-state decision on a public dataset of open and closed eyes, the image-quality checks on deliberately degraded images, "
          "the rule engine on scripted measurement streams, and the speed of the whole path. An offline research pipeline for a consented, labelled study is also provided, "
          "but no real study data exist yet."),
        FIG(F.diag("02_high_level_workflow.png"), "Overall workflow of the runtime pipeline", 5.8),
        P("This is a deliberate narrowing of the batch's original aim. The abstract speaks of classifying a driver as Safe or Intoxicated with a deep-learning model and of a "
          "prevention action such as an ignition warning. We found no dataset of intoxicated and sober people that could be used (Section 6.2), a camera cannot establish alcohol "
          "consumption, and a classifier trained without such data would have produced numbers with no meaning. We therefore built an explainable drowsiness and impairment warning "
          "from observable eye and head cues, kept the objectives that could be met honestly and recorded those that could not (Chapter 9)."),
        H2("6.2 Data used and not used"),
        P("**No dataset of intoxicated people was used, and no intoxication accuracy is claimed anywhere in this report.** The public dataset DIF of perceived intoxicated faces "
          f"{n(4)} lost many of its source videos, as the authors of the base-paper companion study note {n(2)}, who built their own set of 202 people and 3,542 video segments; it is not "
          "available to us. The table lists every data source that was used and what each one can and cannot show."),
        TAB("Data sources", ["Source", "What it is", "Used for", "Cannot show"], [
            ["Closed Eyes in the Wild (CEW)", f"{cew['images_total']:,} face images at 100 x 100 pixels: {cew['closed_images']:,} with both eyes closed (collected from the Internet) and {cew['open_images']:,} with eyes open (from LFW) {n(12, 13)}",
             "Measuring how well the six-point EAR separates closed from open eyes in the shipped pipeline; the threshold sweep; the ROC curve", "Anything about alcohol, blink dynamics, video, riders, helmets, or sources other than these two"],
            ["Degraded copies of CEW open-eye faces", f"{F.ROB['n_images']} faces, each darkened, over-exposed, blurred, noised, covered by an opaque patch over both eyes (sunglasses), a semi-transparent patch (tinted lenses), a patch over one eye, or masked below the nose",
             "Checking that the quality gates fail safe", "Real-world lighting, real eyewear or real occlusion; the 100-pixel source images are softer than a webcam frame"],
            ["Scripted simulation streams", "Four scenarios inside `core.simulate`, and seeded generators in `scripts/measure_rules.py`",
             "Showing how the rules behave (how long a closure must last, what blink patterns could false-alarm)", "Performance on people: the streams are generated, not recorded"],
            ["Synthetic research CSV", "`backend/synthetic.py`: seeded generator, 6 subjects x 2 labels x 30 s at 10 Hz (3,600 rows)",
             "Demonstrating the offline pipeline end to end (48 training and 24 held-out windows)", "Anything: its 100 % scores only prove the code runs, and the interface flags them as Synthetic data"],
            ["Public-domain portrait", "One public-domain face photograph played as the browser's fake webcam",
             "Capturing real screenshots of the camera path and testing the camera API", "Detection accuracy: it is one face"],
        ], widths=[1.3, 2.0, 1.7, 1.3], size=8.5),
        P("The CEW images are used only to measure the pipeline and are not copied into the project folder. Closed-eye pictures come from the Internet while open-eye pictures come from a "
          "different, face-recognition collection, so the two classes differ in source and image conditions as well as in eye state; the separation measured on them may therefore be "
          "better than within a single source. The images are still pictures: they cannot test blink timing or the persistence rules."),
        FIG(F.fig("landmark_examples.png"), "The shipped pipeline on real CEW faces: the six landmark points per eye (green) and the resulting EAR, for open eyes (top row) and closed eyes (bottom row)", 5.6),
        H2("6.3 Preprocessing: image-quality checks and landmark geometry"),
        P("Every frame passes through the same steps, in this order (the pixel checks and the landmark steps are in `vision.py`). The first checks work on the pixels alone, so a frame that is too dark or too blurred is "
          "rejected before any landmark model is run:"),
        N("Resize the frame to 640 x 480 (the camera worker or the session does this before calling `Vision.process`; the browser already sends frames of this size).",
          "Compute the mean grey level of the frame; below 40 or above 225 (on a 0 to 255 scale) the quality label is Poor lighting.",
          "Compute the Laplacian variance of the grey image as a sharpness measure; below 25 the label is Blurred or hidden eyes.",
          "Compute the mean absolute difference from the previous frame reduced to 96 x 72 pixels; above 35 the label is Unstable video.",
          f"Run the MediaPipe Face Landmarker {n(10, 11, 24)} in video mode (detection, presence and tracking confidence 0.7, up to two faces). No face gives No face; more than one gives Multiple faces.",
          "For each eye take the six perimeter points (left eye landmarks 33, 160, 158, 133, 153, 144; right eye 362, 385, 387, 263, 373, 380). If an eye is narrower than 14 pixels or its "
          "patch (with a 6-pixel margin) leaves the image the label is Eyes out of view or too small. If the eye patch has a mean grey level below 35 or above 230, or a standard deviation below 8, the label is Hidden eyes or poor eye lighting.",
          "Compute the EAR of both eyes. If they differ by more than 0.12, or either exceeds 0.65, the label is Unreliable eye geometry; otherwise the observation's EAR is their mean.",
          "Compute the head roll from the outer eye corners (landmarks 33 and 263) and draw the eye points on the frame for the preview."),
        P("These checks are heuristics, not a proof that the eyes are visible: dark or blank visors usually fail them, but patterned occlusions or landmarks inferred for hidden eyes "
          "can pass. Chapter 8 measures how they behave under degradation. Two further timing checks are made by the rule engine itself: an observation whose time does not increase, "
          "or that arrives more than 0.5 s after the previous one, invalidates the accumulated evidence."),
        TAB("Quality labels produced before a verdict", ["Label", "Condition"], [
            ["Poor lighting", "Frame mean grey level < 40 or > 225"],
            ["Blurred or hidden eyes", "Laplacian variance < 25"],
            ["Unstable video", "Mean difference from the previous reduced frame > 35"],
            ["No face / Multiple faces", "Landmarker returned no face / more than one face"],
            ["Eyes out of view or too small", "Eye width < 14 px, or eye patch outside the frame"],
            ["Hidden eyes or poor eye lighting", "Eye patch mean < 35 or > 230, or standard deviation < 8"],
            ["Unreliable eye geometry", "Left and right EAR differ by > 0.12, or EAR > 0.65"],
        ], widths=[2.4, 3.9], size=9.5),
        H2("6.4 Algorithm choice and justification"),
        TAB("Choices and reasons", ["Decision", "Choice", "Reason"], [
            ["Landmarks", f"MediaPipe Face Landmarker (pre-trained, not trained by us) {n(10, 11, 24)}", f"Runs on a laptop CPU at {F.CEW['latency_ms_vision_process_640x480']['p50']:.0f} ms per frame (median) in our measurement; needs no training data; gives the eye contour points directly"],
            ["Eye openness", f"Six-point eye aspect ratio {n(9)}", "Dimensionless, so independent of image scale; simple to compute and to explain; the same feature family as the base paper"],
            ["Noise suppression", "Median of the last 3 EAR values", "Removes a single outlier frame without the lag of a long average"],
            ["Decision", "Transparent duration rules, not a trained classifier", "No labelled intoxication data exist for this project; every warning can be explained by a sentence (closure of 4.9 s, closed fraction 63 % over 10 s); thresholds can be reviewed by the user; unclassified signal is not forced into a class"],
            ["What is being detected", "Sustained eye closure, closed-eye fraction, head tilt with low EAR", f"These are established drowsiness indicators {n(15, 16, 28)}; they are not specific to alcohol, so the output is named Possible impairment or drowsiness"],
            ["Personalisation", "Calibration: threshold = 0.72 x median open-eye EAR", f"People differ in natural eye openness; the base paper also personalises its threshold {n(1)}"],
            ["Safety behaviour", "Quality failure always gives Unable to assess and clears the evidence", "A wrong Normal is worse than no answer"],
            ["Offline study tool", "Standardised nearest-centroid classifier on 5-second windows, subject-disjoint split", "Deliberately simple and auditable; ready for a real consented dataset; never loaded into the live engine"],
        ], widths=[1.3, 2.1, 2.9], size=9),
        P(f"Learned alternatives exist. A recent study on facial video reports 95.82 % accuracy for intoxication with a graph attention network and a 3D ResNet {n(2)}, and a smartwatch "
          f"study reports an AUROC of 0.88 on a test track {n(3)}. Both rely on data collected from people who had drunk alcohol under controlled conditions. We could not reproduce such a "
          "study within a student project and did not want to present an unvalidated network as if it had been."),
        H2("6.5 Mathematical formulation"),
        P("**Eye aspect ratio.** For one eye with perimeter points p1 (outer corner), p2 and p3 (upper lid), p4 (inner corner), p5 and p6 (lower lid):"),
        EQ("EAR = ( ‖p2 − p6‖ + ‖p3 − p5‖ ) / ( 2 · ‖p1 − p4‖ )"),
        P("The observation's EAR is the mean of the left and right values, each computed from landmark coordinates in pixels (so the image aspect ratio is respected). The engine then "
          "smooths it with a median over the last three observations:"),
        EQ("EARs(t) = median( EAR(t), EAR(t − 1), EAR(t − 2) )"),
        P("**Closed eye, closure time and blink.** An eye is closed when EARs is below the threshold θ (0.21 by default). With t0 the time at which the current uninterrupted closure began:"),
        EQ("closed(t) = [ EARs(t) < θ ],     closure(t) = t − t0   while closed"),
        P("A completed closure lasting between 0.08 s and 0.8 s counts as a blink. The blink rate is the number of blinks in the last 60 s divided by the observed good-signal "
          "time (capped at 60 s), times 60; it is displayed but never triggers a warning by itself."),
        P("**Closed fraction.** Over the last 10 seconds the fraction is time-weighted, so an irregular frame rate cannot multiply the votes of a closed eye. For consecutive "
          "observations i and i + 1 at times ti:"),
        EQ("fraction = Σ ( ti+1 − ti ) · closedi  /  ( tlast − tfirst )"),
        P("**Head roll.** From the outer eye corners (xL, yL) and (xR, yR) in image coordinates, in degrees:"),
        EQ("roll = atan2( yR − yL , | xR − xL | ) · 180 / π"),
        P("This is the tilt of the face in the image plane. It is not a full head pose: it ignores yaw and pitch and depends on how the camera is mounted."),
        P("**Warning rule.** Let R1 = closure ≥ 1.5 s, R2 = (fraction ≥ 0.55 and at least 8 s of history) and R3 = (|roll| ≥ 25° and the eye is closed). An evidence timer starts "
          "at the first time any of them is true and is cleared when none is. With at least 2 s of reliable history the answer is a warning when the evidence has lasted the persistence time (1.0 s):"),
        EQ("warning(t) = ( R1 ∨ R2 ∨ R3 )  and  ( t − tevidence ≥ 1.0 s )  and  ( history ≥ 2 s )"),
        P("**Calibration.** During an 8 to 15 second stationary recording only frames of Good quality, EAR between 0.15 and 0.50 and |roll| below 15° are accepted. If at least 40 "
          "frames and at least 70 % of all frames were accepted, and the spread is small, the new threshold is:"),
        EQ("θ = clip( 0.72 · median(EAR accepted), 0.12, 0.32 ),   required:  std(EAR) / median(EAR) ≤ 0.15"),
        P("**Offline metrics.** For the research pipeline and for our measurements, with TP, FP, FN and TN counted for the closed (or impaired) class:"),
        EQ("precision = TP / (TP + FP),   recall = TP / (TP + FN),   specificity = TN / (TN + FP)"),
        EQ("F1 = 2TP / (2TP + FP + FN),   accuracy = (TP + TN) / (TP + TN + FP + FN),   false-alarm rate = FP / (FP + TN)"),
        P(f"ROC analysis {n(25)} and the area under the curve (AUC) summarise how well EAR alone ranks closed eyes below open eyes over all thresholds, and the metric definitions follow {n(26)}. "
          "The false-alarm rate of the research tool is per test window, not per hour of riding."),
        H2("6.6 Model architecture and what 'training' means here"),
        P("**There is no trained model in the decision path.** The only learned component is Google's pre-trained Face Landmarker, which we use as a geometry tool: it returns 478 "
          "facial landmark coordinates and was neither trained nor fine-tuned by us. It does not know about drowsiness or alcohol. Everything after it is a rule engine."),
        P("The rule engine is a small state machine with three outputs. It starts in Unable to assess (warm-up) and needs 2 seconds of continuous good observations before it may say "
          "Normal. From Normal, the first time a rule is satisfied starts the evidence timer; the answer changes to the warning only after the persistence time, and returns to Normal "
          "when the rules clear. Any quality failure, timing gap or invalid value resets the machine to Unable to assess."),
        TAB("States and transitions", ["From", "Event", "To"], [
            ["Any state", "Quality label other than Good, timing gap > 0.5 s, non-finite value, EAR outside 0 to 0.65", "Unable to assess (evidence cleared)"],
            ["Unable to assess", "Less than 2 s of reliable history", "Unable to assess (reason: gathering observations)"],
            ["Unable to assess", "2 s of reliable history and no rule satisfied", "Normal"],
            ["Normal", "A rule satisfied (timer starts)", "Normal, reason marked 'persistence pending'"],
            ["Normal", "A rule satisfied for the persistence time (1.0 s)", "Possible impairment or drowsiness (alert if the cooldown of 15 s has passed)"],
            ["Possible impairment or drowsiness", "No rule satisfied", "Normal"],
        ], widths=[1.6, 3.1, 1.6], size=9.5),
        P("What is learned or fitted, and on what, is therefore limited to the following, and each item is stated with its data:"),
        TAB("Fitted or evaluated elements", ["Element", "Fitted or evaluated on", "Status"], [
            ["Per-rider EAR threshold", "8 to 15 s of the rider's own open-eye frames (calibration)", "Implemented and exercised with a real face; the stored value 0.183 appears in the screenshots"],
            ["Default rule constants (0.21, 1.5 s, 1.0 s, 0.55, 25°, 15 s)", "Engineering choices, not tuned on data", "Left unchanged; the threshold sweep in Chapter 8 was run afterwards and suggests a lower EAR threshold (about 0.17) separates CEW images better, but it was chosen on those same images"],
            ["Nearest-centroid classifier", "Subject-disjoint 5-second windows of a consented CSV", f"Pipeline tested only on the seeded synthetic CSV ({F.TESTS['unittest']['passed']} unit tests include it); status Model not trained for real data"],
            ["EAR eye-state check", f"{cew['images_total']:,} CEW images, evaluation only", f"AUC {cew['auc_ear_closed_vs_open']:.3f} with the gates and {geo['auc_ear_closed_vs_open']:.3f} without them (Chapter 8)"],
        ], widths=[1.9, 2.3, 2.1], size=9),
        H2("6.7 Relation to the base paper's method"),
        P(f"The base paper {n(1)} builds an adaptive driver monitoring system that fuses an eye feature, head pose and voice intent with a Fuzzy Belief Rule-Based engine {n(30)} and "
          f"runs on a Jetson Orin Nano. Our work takes its general idea (an eye-aspect-ratio signal, a personalised threshold and a rule-based decision) and differs in these ways."),
        TAB("Comparison of methods", ["Aspect", "Base paper", "This project"], [
            ["Eye feature", "EAR-4 from four upper-lid points, compared with the six-point EAR", "The conventional six-point EAR only"],
            ["Decision", "Fuzzy Belief Rule-Based inference over EAR, head pose and voice", "If-then duration rules over EAR, closed fraction and image-plane roll"],
            ["Voice", "Whisper-tiny wake words and commands " + n(29), "None"],
            ["Personal threshold", "Initialisation phase on more than 300 frames", "8 to 15 s, threshold = 0.72 x median EAR"],
            ["Target", "Drowsiness, fatigue and distraction", "Possible drowsiness or impairment; not alcohol"],
            ["Hardware", "Jetson Orin Nano (8 GB), 25 frames per second", "Laptop CPU; about 30 frames per second sustained by the API in our measurement"],
        ], widths=[1.3, 2.5, 2.5], size=9.5),
        P("We did not reproduce EAR-4, the fuzzy belief engine or the voice interface, and no figure of the base paper is attributed to this project."),
    ]


def application_blocks():
    lat = F.API_LAT
    frame = lat["POST frame (real face JPEG 640x480, monitoring on)"]
    return [
        H2("6.8 Application architecture"),
        P("`backend/main.py` creates a FastAPI application whose routes hold no decision logic. Each browser tab gets a `RiderSession` (`backend/session.py`) that mirrors the desktop "
          "`Application.consume` and `tick` methods: it owns the source (none, camera or simulation), the monitoring flag, the calibration, a `Vision` instance for the camera and a "
          "`RiskEngine`, and it writes events through `Store`. Sessions live in a dictionary guarded by a lock and idle sessions are dropped after 15 minutes. A fresh `Store` (a new "
          "SQLite connection) is opened for each call because SQLite connections are bound to the thread that created them. Demo credentials, ports and the token secret are read from `.env`."),
        P("The front end is a React single-page application. `useRiderSession.ts` is the heart of the monitor screen: with the camera as source it grabs a frame from the video "
          "element, cover-crops it to 4:3, encodes it as JPEG at quality 0.8 and posts it, then waits so that frames are at least 110 ms apart and only one request is in flight; "
          "with a simulation it calls the tick route every 200 ms. Three failed posts in a row show an error message. The browser sends about nine frames per second, which is "
          f"well within what the server can do (median {frame['p50_ms']:.0f} ms per frame in our measurement) and keeps the gap between frames far below the 0.5 s limit that "
          "invalidates evidence. Queries to the history and settings routes use TanStack Query, charts use Recharts, and a 401 response from any call signs the user out."),
        H2("6.9 API design"),
        P("Section 5.7 lists the 22 routes. The route that matters most is the frame route. It reads the uploaded JPEG, passes it to the session and returns the session snapshot "
          "together with the annotated preview as a data URL. The session decodes the bytes, resizes to 640 x 480, calls `Vision.process` and hands the observation to `consume`:"),
        CODE(source("backend/main.py", "@app.post('/api/session/{session_id}/frame'", "@app.post('/api/session/{session_id}/tick'")),
        P("Calibration, thresholds and monitoring go through the same session object, so the web interface behaves exactly like the desktop one: saving thresholds stops monitoring "
          "and clears the calibrated flag, calibration is refused in simulation, and monitoring cannot start while calibration is running. These rules return 409 with a message the "
          "interface shows to the user."),
        H2("6.10 Security and error handling"),
        TAB("Controls", ["Threat or fault", "Control in the code"], [
            ["Unauthenticated access", "Every route except health, config, about, login and the demo hint depends on `current_user`, which reads the `Authorization: Bearer` header and answers 401"],
            ["Token forgery or tampering", "Token = base64 payload (`sub`, `exp`) + HMAC-SHA256 signature computed with `AUTH_SECRET` and checked with `hmac.compare_digest`; expiry 12 h"],
            ["Timing attack on the password", "Email and password are compared with `hmac.compare_digest`"],
            ["Invalid thresholds", "`Settings.validate` checks every value is finite and inside its bounds; the API answers 422 and the file is not written"],
            ["Corrupt settings file", "Invalid JSON or out-of-range values fall back to safe defaults with a visible note; saves go through a temporary file and an atomic replace"],
            ["Hostile frames", "Undecodable bytes give 422; every frame is resized to 640 x 480; frames are never written to disk"],
            ["SQL injection", "All SQL uses bound parameters; the table name is fixed"],
            ["Concurrency", "A lock per session; one SQLite connection per call; a research evaluation lock that answers 409 if one is already running"],
            ["Bad research data", "Row-by-row CSV validation (consent, labels, ranges, duplicate timestamps, subject split) with a plain error and no model produced"],
            ["Unexpected server error", "A catch-all handler returns JSON with status 500; the front end shows the message instead of failing silently"],
            ["Missing landmark model", "Camera start answers 503 with the instruction to run `setup_model.py`; simulation keeps working"],
            ["Privacy", "No image or video is stored or uploaded to a third party; the monitor screen states this"],
        ], widths=[1.8, 4.5], size=9.5),
        P("The weaknesses listed in Section 5.9 apply here: a shared demo account, plain HTTP on the local machine, open CORS, no rate limiting and in-memory sessions."),
        H2("6.11 Installation and execution"),
        P("`run.bat` is the one-click start. Its six steps are: find Python (it prefers 3.14, the version the pinned packages were tested on; 3.12 or newer is required) and rebuild the "
          "virtual environment if it was copied from another computer; install `requirements.txt` and `backend/requirements.txt`; download Google's `face_landmarker.task` (about 3.7 MB) "
          "once if it is missing; check Node.js; install the front-end packages on first use; then start the API in one window and the web application in another and open the "
          "browser. The ports come from `.env` (API 8306, web 5306). Sign in with the demo account `demo@smartrider.app` / `Demo@1234`. The original desktop application still runs "
          "with `app.py`, optionally `--simulation`. Appendix B gives the complete guide, the manual commands and a troubleshooting table."),
    ]


def blocks():
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
