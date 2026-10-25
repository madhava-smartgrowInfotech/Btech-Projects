"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx."""

import os
import tempfile

from PIL import Image
from pptx import Presentation

from . import facts as F
from . import pptkit as K
from .deck_review1 import agenda, prepare, set_title, thank_you, title_slide, wipe

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"


def crop(name, box, tag):
    """Crop a real screenshot to the part that matters on a slide (written to the temp folder, source untouched)."""
    out = os.path.join(tempfile.gettempdir(), f"a2_deck_{tag}.png")
    with Image.open(F.shot(name)) as im:
        im.crop(box).save(out)
    return out


MAIN = (248, 62, 1440, 700)   # screenshot area without the sidebar and top bar, upper part of the page


def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}
    C = [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE]
    DET, SEVM, ALERT, SEEDS = F.DET, F.SEVM, F.ALERT, F.SEEDS
    pk = F.SHIP["per_event_kind"]
    sev_acc, sev_f1 = f"{SEVM['accuracy']:.5f}", f"{SEVM['macro_f1']:.5f}"

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: from a simulated sensor reading to a confirmed, located emergency alert",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = "This review shows how ResQAI is designed and built: data, models, what is implemented, the first measured results and the open items."

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and dataset"), ("03", "Preprocessing and models"), ("04", "Configuration and decision logic"),
               ("05", "Data flow, database and UML"), ("06", "Technology stack"), ("07", "Implementation progress and results"),
               ("08", "Output screens and testing"), ("09", "Challenges and next steps")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Victims of road accidents often cannot call for help, and crash detection that reports only an impact gives responders no severity to prioritise by. Dedicated crash hardware is costly and rare on two-wheelers.", K.ORANGE, "!"),
        ("Proposed system", "Smartphone-style sensor readings go to a crash detector and a severity model. A Moderate or Severe result opens a 15-second confirmation; if it is not cancelled, the location, the three nearest hospitals and a dispatch message are produced.", K.BLUE, "i"),
        ("Base paper link", "Wang, Liang and He grade crash severity from 30,442 recorded crashes with a multi-task FT-Transformer. We borrow severity grading and per-class metrics, but our task, data and models differ, so the results are not comparable.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, 4.9, t, b_, col, gl, body_size=17)
    notes[3] = "One-minute recap of Review 1: the delay and severity problem, our two-model approach with a confirmation step, and how the base paper relates (a different task on recorded data)."

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.6, 1.3, 7.1, 5.6)
    K.text(s, 8.0, 1.5, 4.7, 5.3, [
        ("**Layers**", {"space_after": 8}),
        (f"Presentation: React 19 and Vite 8 console (port {F.WEB_PORT}), 6 screens.", {"bullet": True}),
        (f"Application: Flask 3 (port {F.API_PORT}): simulate, predict, hospitals, emergency, health and account routes.", {"bullet": True}),
        ("Machine learning: scaler and two random forests loaded once at start-up.", {"bullet": True}),
        ("Data: users.json, hospitals.json and four model pickles; no database.", {"bullet": True}),
    ], size=16, color=K.INK)
    notes[4] = "All routes are in app.py and auth.py. The model objects are loaded once. Storage is local JSON; readings, predictions and alerts are not stored."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: end-to-end workflow")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.2, [("Generate events", K.NAVY), ("11 features", K.PURPLE), ("Scale", K.PURPLE), ("Detect (RF)", K.GREEN),
                                      ("Grade (RF)", K.ORANGE), ("Confirm 15 s", K.BLUE), ("Locate + dispatch", K.NAVY)], size=13, gap=0.22)
    for i, (t, b_) in enumerate([("One decision path", "predict_from_features runs scaler, detector and severity model in one place, so the web console, the tests and the measurement script exercise the same code."),
                                 ("Honest fallbacks", "If the model files are missing, three acc_magnitude thresholds (15, 28, 45) answer instead and the response says rule_based_fallback."),
                                 ("Measured, not typed", "scripts/measure_metrics.py, measure_api.py and run_tests.py write every reported number to experiments/resqai_eval; figures are drawn from those files.")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 3.1, 3.85, 3.6)
        K.text(s, x + 0.25, 3.25, 3.4, 0.5, t, size=20, color=K.INK, bold=True)
        K.text(s, x + 0.25, 3.9, 3.4, 2.7, b_, size=16, color=K.TXT)
    notes[5] = "Three design principles: one decision path, honest fallbacks, and numbers that come from scripts."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Dataset and input sources")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.N_TOTAL:,}", "synthetic events, seed 42", K.BLUE), ("11", "sensor features per event", K.GREEN),
                                   (F.pct(F.DS["accident_rate_total"]), "of events are crashes (2,387)", K.ORANGE), (f"{F.N_TRAIN:,} / {F.N_TEST:,}", "train / held-out test, stratified", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    K.picture(s, F.fig("f01_feature_separation.png"), 0.6, 2.9, 6.8, 2.75)
    K.text(s, 7.6, 2.95, 5.1, 3.9, [
        ("No real crash recordings were available, so train_models.py generates events: normal driving 60 %, harsh braking 20 %, minor 10 %, moderate 6 %, severe crashes 4 %.", {"bullet": True}),
        ("Realised counts: 7,289 normal, 2,324 braking, 1,215 minor, 725 moderate, 447 severe.", {"bullet": True}),
        ("Crashes start above 15.3 m/s² and braking never exceeds 13.2: one gap separates the classes.", {"bullet": True}),
        ("Not in the data: potholes, speed breakers, phone drops, sensor orientation, real noise.", {"bullet": True}),
    ], size=14, color=K.INK, space_after=9)
    K.text(s, 0.6, 5.8, 6.8, 1.0, "Left: acceleration magnitude by event kind (log scale) and magnitude against jerk. The gap between 13.2 and 15.3 m/s² is why detection is easy on this data.", size=12, color=K.TXT, italic=True)
    notes[6] = ("Be frank: the data are synthetic, drawn from the same generator the live simulator uses. That makes detection easy (a single threshold separates the classes) and the metrics optimistic; "
                "it is also why potholes and speed breakers, which the generator never produces, are an open question.")

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Data preprocessing")
    wipe(s)
    K.picture(s, F.diag("05_dfd_level2.png"), 0.6, 1.35, 6.9, 5.45)
    K.text(s, 7.8, 1.5, 4.9, 5.2, [
        ("1  Complete the payload: missing fields default (acc_z = 9.81, others 0)", {}),
        ("2  Derive acc_magnitude = sqrt(x² + y² + z²) and gyro_magnitude when absent", {}),
        ("3  Store jerk as an absolute value", {}),
        ("4  Order the 11 values as the trained feature list", {}),
        ("5  Standardise with the training mean and standard deviation (StandardScaler fitted on 9,600 events)", {}),
        ("Finding: the detector's permutation importance is carried by acc_magnitude alone; the gyroscope adds nothing measurable on this data.", {"italic": True, "size": 14, "color": K.TXT}),
    ], size=15, color=K.INK, space_after=9)
    notes[7] = "Preprocessing is light: defaults, two derived magnitudes and scaling. The finding at the bottom comes from the ablation study."

    # ---- 8 models
    s = S[7]
    set_title(s, "Model architecture")
    wipe(s)
    rows = [["Component", "Configuration", "Role"],
            ["Scaler", "StandardScaler, 11 features, fitted on the training split", "puts features on one scale"],
            ["Accident detector", "RandomForest, 200 trees, max depth 10, class_weight balanced, seed 42", "crash or not, with probability"],
            ["Severity model", "RandomForest, 250 trees, max depth 12, balanced; trained on all events (None = class 0)", "None / Minor / Moderate / Severe"],
            ["Rule fallback", "acc_magnitude < 15 / 28 / 45 m/s² gives None / Minor / Moderate / Severe", "only if the model files are missing"]]
    K.table(s, 0.6, 1.4, [2.4, 6.0, 3.73], rows, font_size=14, row_h=0.74, first_bold=True)
    K.tile(s, 0.6, 5.65, 3.8, 1.2, "385 KB / 2.6 MB", "detector / severity pickle size", K.BLUE, vsize=24)
    K.tile(s, 4.7, 5.65, 3.8, 1.2, "14 ms", f"mean in-process prediction (p95 {F.INF['p95']:.1f} ms)", K.GREEN, vsize=26)
    K.tile(s, 8.8, 5.65, 3.93, 1.2, "No GPU", "scikit-learn on a CPU", K.ORANGE, vsize=26)
    notes[8] = ("Two forests of the same family, one for the binary decision and one for the grade. The gate in the application forces the grade to None whenever the detector says no accident. "
                "The pickles were written with scikit-learn 1.9.0 and load here under 1.5.0 with a warning; a fresh retrain agrees on 100 % of the 2,400 test events.")

    # ---- 9 configuration
    s = S[8]
    set_title(s, "Training configuration and parameter analysis")
    wipe(s)
    rows = [["Setting", "Value"],
            ["Split", "80 / 20, stratified on the accident label, random_state 42: 9,600 train, 2,400 test; no validation split"],
            ["Operating point", "detector predict() (threshold about 0.5); alert only for Moderate or Severe; 15 s countdown"],
            ["Repeat study", "five seeds (11, 22, 33, 44, 55): new dataset, split and forests each time"],
            ["Baselines", "rule thresholds, logistic regression, decision tree (depth 10), HistGradientBoosting"],
            ["Machine", "Intel Core i5-12500, 15.7 GB RAM, Windows 11, Python 3.11.9, scikit-learn 1.5.0; training takes seconds"]]
    K.table(s, 0.6, 1.4, [2.2, 9.93], rows, font_size=13, row_h=0.52, first_bold=True)
    K.picture(s, F.fig("f06_threshold_sweep.png"), 0.6, 4.7, 5.4, 2.3)
    K.text(s, 6.3, 4.8, 6.4, 2.2, "Parameter check: the detector probability threshold. Precision and recall are both 1.000 for every threshold from 0.2 to 0.9; at 0.05 there are 5 false alarms, at 0.95 two missed crashes. The operating point is not threshold-sensitive on this data (lowest crash probability 0.90, highest non-crash 0.17).", size=14, color=K.TXT)
    notes[9] = "Settings come straight from train_models.py. The threshold sweep shows a wide plateau: no tuning was needed, which again reflects how separable the synthetic classes are."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: gate, confirmation and dispatch")
    wipe(s)
    K.picture(s, F.diag("10_flowchart_core_algorithm.png"), 0.6, 1.25, 5.0, 5.75)
    K.text(s, 6.0, 1.5, 6.7, 5.3, [
        ("**Detect.** The detector's class and probability come from predict() and predict_proba().", {"bullet": True, "space_after": 9}),
        ("**Gate.** No accident forces severity to None, whatever the severity forest says.", {"bullet": True, "space_after": 9}),
        ("**Confirm.** Only Moderate or Severe opens the 15 s dialog; live monitoring pauses; Escape or the cancel button logs a false alarm.", {"bullet": True, "space_after": 9}),
        ("**Locate.** Browser GPS (3 s timeout); otherwise a point near the default Hyderabad location.", {"bullet": True, "space_after": 9}),
        ("**Dispatch.** Haversine ranking of 10 hospitals, nearest three, message with a map link, alert id RQ-<unix seconds>, numbers 112 and 108. Nothing is transmitted.", {"bullet": True}),
    ], size=16, color=K.INK)
    notes[10] = "The decision logic is a few lines of code. The confirmation step is the only protection against false alarms in the live app; its effect on real users was not measured."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, F.diag("04_dfd_level1.png"), 0.6, 1.3, 6.2, 5.6)
    rows = [["Module / function", "Role"], ["build_feature_vector", "defaults, magnitudes, order"], ["predict_from_features", "scale, detect, grade, gate"], ["rule_based_fallback", "thresholds if no models"],
            ["api_simulate", "five scenario generators"], ["nearest_hospitals, haversine_km", "rank the directory"], ["api_emergency", "message, alert id, 112 / 108"], ["auth.py", "accounts, token, lockout, guard"],
            ["MonitorContext.jsx", "countdown, cancel, dispatch"]]
    K.table(s, 7.1, 1.4, [3.1, 2.53], rows, font_size=12, row_h=0.52)
    notes[11] = "Level-1 data flow: reading, detection and grading, confirmation, location and hospital ranking, dispatch. The table maps each step to the function in the code."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database design and UML")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.6, 1.35, 6.4, 4.2)
    K.picture(s, F.diag("06_uml_class.png"), 7.2, 1.3, 5.5, 5.65)
    K.text(s, 0.6, 5.75, 6.4, 1.2, "No relational database: accounts and hospitals are JSON files. Readings, predictions and alerts are transient (JSON in requests and React state), and an alert carries no user id.", size=13, color=K.TXT, italic=True)
    notes[12] = "A deliberate simplification for a demonstration: two JSON files and four pickles. A real deployment would store alerts and tie them to accounts."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    rows = [["Layer", "Technology"],
            ["Backend", "Python 3.11, Flask 3.1, itsdangerous signed tokens, werkzeug scrypt password hashes, JSON files"],
            ["Machine learning", "scikit-learn (RandomForestClassifier, StandardScaler), joblib, NumPy, pandas"],
            ["Front end", "React 19, Vite 8, react-router 7, Leaflet map, Recharts, Framer Motion, GSAP"],
            ["Location and maps", "browser Geolocation API; OpenStreetMap tiles; haversine distance in app.py"],
            ["Testing", "scripts/smoke_test.py, scripts/run_tests.py (unit, edge, security), Playwright screenshot walk"],
            ["Measurement", "scripts/measure_metrics.py, measure_api.py; matplotlib figures"],
            ["Packaging", "setup.bat (venv, pip, npm) and run.bat (both servers); requirements.txt is not version-pinned"]]
    K.table(s, 0.6, 1.5, [3.2, 8.93], rows, font_size=15, row_h=0.62, first_bold=True)
    notes[13] = "Everything is open source and runs on a laptop. The requirements file is unpinned, which matters because the shipped pickles were written with a newer scikit-learn than the one used for these measurements."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Synthetic data generator and training script", "Done", "12,000 events, 4 pickles; generator reproduced exactly"],
            ["Detector and severity models", "Done", f"detector 1.000; severity accuracy {sev_acc} (n = 2,400)"],
            ["Flask API (10 routes) and accounts", "Done", f"smoke test {F.SMOKE_PASSED} of {F.SMOKE_TOTAL}; auth checks 18 of 18"],
            ["React console: monitor, manual, response map", "Done", "6 screens, dark mode, 18 screenshots"],
            ["15 s confirmation, location, hospitals, dispatch message", "Done (demo)", "alert path 56 ms mean; message displayed, not sent"],
            ["Real phone sensors, SMS / call delivery", "Not done", "feed is simulated; no gateway"],
            ["Potholes and speed breakers", "Not done", "not in the data; probe flags about half"],
            ["Input validation hardening", "Open", "8 of 55 edge and unit checks fail (HTTP 500 on bad input)"]]
    K.table(s, 0.6, 1.4, [4.9, 1.6, 5.63], rows, font_size=13, row_h=0.6)
    notes[14] = "State of the code base. The honest gaps: real sensing, real delivery, road-surface events and validation of malformed input."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results")
    wipe(s)
    for i, (v, l, c) in enumerate([("1.000", "detector accuracy and F1, 2,400 test events", K.BLUE), (sev_acc, "severity accuracy after the gate", K.GREEN),
                                   (sev_f1, "severity macro-F1 (5-seed mean 0.99501)", K.ORANGE), ("0 of 460", "harsh-braking events flagged as accidents", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, c, vsize=24, lsize=12)
    K.picture(s, F.fig("f02_confusion_matrices.png"), 0.6, 2.9, 6.6, 3.2)
    K.picture(s, F.fig("f03_baselines.png"), 7.4, 2.9, 5.3, 3.2)
    K.text(s, 0.6, 6.2, 12.1, 0.8, "Synthetic data from the training generator: the near-perfect scores show the classes are separable by construction. A single acc_magnitude threshold matches the detector (1.000) and scores 0.975 on severity; the forest gains 2.5 points there. Not comparable with the base paper.", size=12, color=K.TXT)
    notes[15] = ("Detector 1.000 on 2,400 events: 1,923 non-accidents and 477 accidents, no error. Severity: one error, a Minor crash graded Moderate. "
                 "Five-seed repeat: severity accuracy 0.99875 plus or minus 0.00066, macro-F1 0.99501 plus or minus 0.00293. These are pipeline checks on synthetic data, not road performance.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    K.picture(s, crop("08_monitor_live.png", MAIN, "a"), 0.6, 1.25, 6.0, 2.8, border=True)
    K.picture(s, crop("09_alert_countdown.png", MAIN, "b"), 6.75, 1.25, 6.0, 2.8, border=True)
    K.picture(s, crop("11_response_dispatched.png", MAIN, "c"), 0.6, 4.15, 6.0, 2.4, border=True)
    K.picture(s, crop("12_manual_result.png", MAIN, "d"), 6.75, 4.15, 6.0, 2.4, border=True)
    K.text(s, 0.6, 6.62, 12.1, 0.4, "Live monitor and the 15 s confirmation for a Severe crash; dispatched alert with map; manual override result. Captured from the running app.", size=12, color=K.TXT)
    notes[16] = "Real screenshots of the running console with simulated sensor data flowing through the real models. The dispatch is a displayed message; nothing is sent."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.SMOKE_PASSED} / {F.SMOKE_TOTAL}", "smoke-test checks passed", K.GREEN), (f"{F.TEST_PASSED} / {F.TEST_TOTAL}", "unit, edge and security checks passed", K.BLUE),
                                   ("18 / 18", "authentication and security checks", K.ORANGE), (f"{F.ENDPOINTS['POST /api/predict']['mean']:.0f} ms", "mean POST /api/predict on loopback", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Observation", "Action"],
            ["Non-numeric input to /api/predict, /api/hospitals and /api/emergency returns HTTP 500; k = -1 returns 9 of 10 hospitals", "Recorded as findings (8 failed checks); validation listed as next step"],
            ["Two alerts raised in the same second get the same id (RQ-<unix seconds>)", "Recorded; a UUID or counter is the fix"],
            ["Pothole-like and speed-breaker-like probes: about 49 % and 50 % flagged as accidents, none Moderate or Severe", "No alert is started, but road-surface events need their own classes"]]
    K.table(s, 0.6, 3.0, [6.8, 5.33], rows, font_size=14, row_h=0.9)
    notes[17] = "Tests ran against the real models. The failures are findings: the product code was left untouched and each is documented in the report."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "Corrective action"],
            ["No real crash recordings or public sensor dataset in the project", "Synthetic, labelled generator; every metric states it; a threshold baseline shows the ceiling effect"],
            ["Pickles written by scikit-learn 1.9.0; requirements unpinned", "Retrained with the same seed: 100 % agreement on 2,400 events; pinning is a next step"],
            ["Potholes and speed breakers are not in the training data", "Measured with constructed probes (about 50 % flagged); the Moderate / Severe gate keeps them from alerting"],
            ["Sensor noise was never part of training", "Noise sweep: stable to 10 % noise, 24 % false alarms at 50 %"],
            ["Test machine short of memory; first API run crashed", "Repeated; timings are conservative and stated as such"]]
    K.table(s, 0.6, 1.5, [5.4, 6.73], rows, font_size=15, row_h=0.9)
    notes[18] = "Each challenge was met by a concrete step or by measuring it and saying so in the report."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Real sensor data", "Record accelerometer and gyroscope traces on phones, including potholes, speed breakers and hard braking, and retrain on them.", K.BLUE, "1"),
        ("Road-surface classes", "Add pothole and speed-breaker classes and report false-alarm rate per event kind on real data.", K.GREEN, "2"),
        ("Real delivery", "Connect an SMS or call gateway and measure end-to-end latency including delivery, not only the 56 ms of compute.", K.ORANGE, "3"),
        ("Harden and pin", "Validate all inputs, use unique alert ids, store alerts per user and pin the library versions.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.09, 1.6, 2.85, 4.6, t, b_, col, gl, body_size=16)
    notes[19] = "Plan to the final review and beyond. The first two items address the biggest honest gap: synthetic data and untested road-surface events."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Likely questions: why a random forest; why detection is 100 percent (separable synthetic classes); what happens with potholes; whether alerts are really sent (no)."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
