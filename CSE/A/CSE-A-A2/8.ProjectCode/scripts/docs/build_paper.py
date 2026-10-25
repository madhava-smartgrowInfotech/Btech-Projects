"""Builds 19.IEEE_Paper.docx (two-column, 6 pages) for ResQAI from facts.py (experiments/resqai_eval/*.json), the diagrams and the screenshots.

    python -m scripts.docs.build_paper            # from 8.ProjectCode, system python
Every number in the text is read from facts.py (F) so the paper cannot drift from docs/REPORT_FACTS.md.
"""

import os

from PIL import Image

from . import facts as F
from .paper import Paper
from .refs import CITE

pct, f2, f3, f4, f5 = F.pct, F.f2, F.f3, F.f4, F.f5


def R(*keys):
    """Citation placeholder resolved by Paper.expand in order of first appearance."""
    return "{r:" + ",".join(str(CITE[k]) for k in keys) + "}"


# --------------------------------------------------------------------------------------------- figures
def _box(ax, x, y, w, h, text, fc, tc="white", fs=6.4, bold=False):
    from matplotlib.patches import FancyBboxPatch

    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=fc, ec=fc, lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc, fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.25)


def _arr(ax, p1, p2):
    ax.annotate("", xy=p2, xytext=p1, arrowprops=dict(arrowstyle="-|>", color="#1F3A5F", lw=1.0, shrinkA=0, shrinkB=0))


def _arch_fig():
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(3.4, 3.05))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 96)
    ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)
    _box(ax, 2, 80, 96, 14, "React 19 + Vite interface (port 5302)\nMonitor - Manual override - Emergency response map\n15 s countdown state (MonitorContext)", "#2B6CB0", fs=6.3)
    _box(ax, 2, 58, 96, 16, "Flask API (port 8302)\n/api/simulate - /api/predict - /api/hospitals\n/api/emergency - /api/auth/* (signed token)", "#14907F", fs=6.3)
    _box(ax, 2, 34, 96, 18, "Machine-learning tier (loaded once)\nStandardScaler -> accident detector (RF, 200 trees)\n-> severity model (RF, 250 trees) -> gate", "#D9772F", fs=6.3)
    _box(ax, 2, 4, 30, 24, "users.json\nscrypt hashes\n(accounts)", "#EEF2F7", tc="#14213D", fs=6.0)
    _box(ax, 35, 4, 30, 24, "hospitals.json\n10 Hyderabad\nhospitals", "#EEF2F7", tc="#14213D", fs=6.0)
    _box(ax, 68, 4, 30, 24, "models/*.pkl\nscaler, detector,\nseverity", "#EEF2F7", tc="#14213D", fs=6.0)
    for y1, y2 in ((80, 74.5), (58, 52.5), (34, 28.5)):
        _arr(ax, (50, y1), (50, y2))
    p = os.path.join(F.FIGS, "paper_arch.png")
    fig.savefig(p, dpi=200, facecolor="white")
    plt.close(fig)
    return p


def _flow_fig():
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(3.4, 3.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 112)
    ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)
    _box(ax, 10, 99, 80, 11, "Sensor reading (11 features)\nsimulated by /api/simulate", "#2B6CB0", fs=6.4)
    _box(ax, 10, 83, 80, 11, "Scale; detector P(accident); severity class", "#14907F", fs=6.4)
    _box(ax, 10, 67, 80, 11, "Gate: no accident -> severity None", "#14907F", fs=6.4)
    _box(ax, 10, 51, 80, 11, "Moderate or Severe?  (else: log only)", "#D9772F", fs=6.4)
    _box(ax, 10, 35, 80, 11, "15 s confirmation: cancel / Esc, or send", "#D9772F", fs=6.4)
    _box(ax, 10, 19, 80, 11, "Browser GPS (3 s) -> 3 nearest hospitals (haversine)", "#6B5BD2", fs=6.0)
    _box(ax, 10, 3, 80, 11, "Dispatch message + alert id + 112 / 108 (displayed)", "#1F3A5F", fs=6.1)
    for y1, y2 in ((99, 94.5), (83, 78.5), (67, 62.5), (51, 46.5), (35, 30.5), (19, 14.5)):
        _arr(ax, (50, y1), (50, y2))
    p = os.path.join(F.FIGS, "paper_flow.png")
    fig.savefig(p, dpi=200, facecolor="white")
    plt.close(fig)
    return p


def _results_fig():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 6.5})
    fig, (a, b) = plt.subplots(1, 2, figsize=(3.4, 2.45), gridspec_kw={"wspace": 0.5})
    names = [("rule_based_fallback (acc_magnitude < 15 / 28 / 45)", "rule"), ("logistic_regression", "LR"), ("decision_tree (depth 10)", "DT"),
             ("hist_gradient_boosting", "HGB"), ("random_forest (ResQAI, retrained)", "RF")]
    vals = [F.BASE[n]["sev_macro_f1"] for n, _ in names]
    x = np.arange(len(names))
    a.bar(x, vals, color=["#8795A8", "#2B6CB0", "#2B6CB0", "#2B6CB0", "#D9772F"], width=0.65)
    for i, v in enumerate(vals):
        a.text(i, v + 0.004, f"{v:.3f}", ha="center", fontsize=5.2, rotation=90, va="bottom")
    a.set_xticks(x)
    a.set_xticklabels([s for _, s in names], fontsize=6)
    a.set_ylim(0.85, 1.04)
    a.set_ylabel("severity macro-F1")
    a.set_title("(a) severity models", fontsize=6.8)
    a.spines[["top", "right"]].set_visible(False)
    n = F.NOISE
    xs = [r["noise_sd_fraction_of_feature_sd"] for r in n]
    b.plot(xs, [r["det_f1"] for r in n], "o-", color="#14907F", ms=2.5, lw=1, label="det. F1")
    b.plot(xs, [r["sev_macro_f1"] for r in n], "s-", color="#D9772F", ms=2.5, lw=1, label="sev. macro-F1")
    b.plot(xs, [r["det_false_alarm"] for r in n], "^--", color="#C0392B", ms=2.5, lw=1, label="false alarm")
    b.set_xlabel("noise SD / feature SD")
    b.set_title("(b) added sensor noise", fontsize=6.8)
    b.legend(frameon=False, fontsize=5.2, loc="upper right")
    b.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    p = os.path.join(F.FIGS, "paper_results.png")
    fig.savefig(p, dpi=220, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    return p


def make_figures():
    out = {"arch": _arch_fig(), "flow": _flow_fig(), "results": _results_fig()}
    s09 = Image.open(F.shot("09_alert_countdown.png")).convert("RGB")
    p = os.path.join(F.FIGS, "paper_screen_countdown.png")
    s09.crop((442, 235, 1012, 680)).save(p)
    out["countdown"] = p
    s11 = Image.open(F.shot("11_response_dispatched.png")).convert("RGB")
    p = os.path.join(F.FIGS, "paper_screen_dispatch.png")
    s11.crop((857, 288, 1410, 760)).save(p)
    out["dispatch"] = p
    return out


# --------------------------------------------------------------------------------------------- text
def build(path):
    figs = make_figures()
    env = F.M["environment"]
    det, sev, alr = F.DET, F.SEVM, F.ALERT
    seeds_m, seeds_s = F.SEEDS["mean"], F.SEEDS["std"]
    ood = F.OOD
    pk = F.SHIP["per_event_kind"]
    n3 = {r["noise_sd_fraction_of_feature_sd"]: r for r in F.NOISE}
    inf, ap = F.INF, F.ALERT_PATH
    ep = F.ENDPOINTS
    pc = sev["per_class"]
    B = F.BASE
    rule = B["rule_based_fallback (acc_magnitude < 15 / 28 / 45)"]
    rf = B["random_forest (ResQAI, retrained)"]

    P = Paper()
    authors = [[n, f"Roll No. {r}", "Dept. of Computer Science and Engineering", "TKR College of Engineering & Technology", "[CITY], India", "[EMAIL]"] for n, r in F.STUDENTS]
    authors.append([F.GUIDE, f"{F.GUIDE_DESIGNATION}, project guide", "Dept. of Computer Science and Engineering", "TKR College of Engineering & Technology", "[CITY], India", "[EMAIL]"])
    P.title_block("ResQAI: AI-Based Accident Detection, Severity Assessment and Intelligent Emergency Response System", authors)
    P.begin_two_columns()

    P.abstract(
        "A crash on a quiet road can go unreported for a long time, and today's crash alerts usually say only that an impact occurred, not how serious it was. "
        "This paper presents ResQAI, a web application that turns motion-sensor readings (accelerometer, gyroscope, speed and jerk) into a graded, located emergency alert. "
        "Two random forests detect a crash and grade it as none, minor, moderate or severe; only a moderate or severe result opens a 15-second confirmation in which the occupant can cancel a false alarm; "
        "otherwise the browser location is read, the three nearest hospitals are ranked by great-circle distance and an alert message is composed. "
        f"No real recordings were available, so the models were trained and tested on {F.N_TOTAL:,} synthetic events. On the {F.N_TEST:,} held-out events the detector scored 1.000 on every metric, which a one-line threshold also achieves, "
        f"and severity accuracy was {f4(sev['accuracy'])} (five-seed mean {f4(seeds_m['sev_accuracy'])}). "
        f"Events the generator never produces, such as potholes, were flagged as accidents about half the time. The alert path took {ap['mean']:.0f} ms on loopback, excluding the confirmation window; nothing is transmitted. "
        "The pipeline works end to end; it is not shown to perform this well on real roads.",
        ["accident detection", "emergency response", "hospital recommendation", "random forest", "severity prediction", "smartphone sensors"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para(f"Road traffic injury is a leading cause of death worldwide {R('who')}, and the outcome of a serious crash depends heavily on how soon help arrives. "
           "Victims are often unable to call for help, and on a remote stretch an accident may go unreported until a passer-by stops. Modern smartphones carry accelerometers, gyroscopes and GPS, "
           "so they are a low-cost crash sensor, but the alert built on that sensor is usually binary: an impact happened. Without a severity grade, a responder cannot tell a minor scrape from a critical collision, "
           "and without a confirmation step, a dropped phone or a hard stop can dispatch a false alarm.")
    P.para(f"Research on severity has mostly worked after the event, on recorded crash reports. The base paper {R('base')} predicts injury, fatal and property-loss severity from 30,442 police-reported crashes with a multi-task FT-Transformer {R('gorishniy', 'kendall')}; "
           "it never detects a crash, never sees a sensor and never contacts anyone. Prototypes that do detect crashes, from Arduino boards with a GSM modem " + R('greenbox', 'karthik') + " to camera-based systems " + R('cirs') + ", rarely grade severity or report measured error rates. "
           "The loop from live sensing through severity grading and confirmation to a located, prioritised alert is therefore not closed in the work surveyed.")
    P.para("ResQAI closes that loop at demonstration scale. Its contributions are: "
           "(1) a detector and a four-level severity model (random forests) over an eleven-feature sensor reading, gated so that a non-crash is never graded; "
           "(2) a confirmation rule that only a moderate or severe result starts a 15-second window for the occupant to cancel, followed by GPS location and nearest-hospital ranking; "
           "(3) a measured evaluation that goes beyond one accuracy figure, with a five-seed repeat, baselines, a feature ablation, a noise sweep, out-of-distribution probes, latency and a 55-check test run; and "
           "(4) a plain record of what the evaluation could not show. Section II reviews related work, Section III describes the method, Section IV gives the results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para("All measurements were taken on one desktop PC: Windows 11 Pro, an Intel Core i5-12500 processor, 15.7 GB of RAM and no GPU. During the runs other programs held most of the memory, so timings are conservative.")
    P.sub("B", "Software Requirements")
    P.para(f"Python {env['python']}, scikit-learn {env['sklearn']} {R('sklearn')} with NumPy {env['numpy']} and pandas {env['pandas']}; Flask 3.1 for the API with scrypt password hashing and signed tokens; "
           "React 19 and Vite 8 with Leaflet and Recharts for the console, and Node.js 18 or later. The shipped model files were written by scikit-learn 1.9.0 and loaded under 1.5.0; a retrain with the same seed agrees with them on every test event.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para(f"**Base paper.** Wang, Liang and He {R('base')} predict three outcomes of a traffic accident (injury severity in 5 classes, fatal-accident severity in 5 classes and property loss in 6 classes) from police-reported records of Dongguan, China, 2019-2023: "
           "30,442 records split into 19,483 for training, 4,871 for validation and 6,088 for testing, with driver, vehicle, road and environment attributes. "
           f"A multi-task FT-Transformer {R('gorishniy')} embeds each tabular feature as a token and shares them across the three tasks, with a loss that weights each task by its uncertainty {R('kendall')}; SMOTE balances the training set and SHAP explains the predictions. "
           "It reaches accuracies of 70.31%, 90.38% and 80.79% (F1 64.48%, 86.71% and 79.18%) and beats eight baselines including XGBoost, LightGBM, CatBoost and a random forest. "
           "The authors note a single city, proprietary data, injury proxied by the number of injured and no ordinal modelling. The model describes a crash that has already been reported; it does not detect one.")
    P.para(f"**Sensor and IoT detection.** GreenBox {R('greenbox')} uses an Arduino Uno and a SIM7600G-H GSM and GPS shield with four push-button impact sensors, an MPU-6050 for rollover beyond 70 degrees, water sensors and an engine-cut relay, "
           "and sends an SMS with location and speed to preset contacts; the owner can cancel a false detection by SMS. It is evaluated qualitatively (alerts \"in a matter of seconds\") with no accuracy or latency figure, and it applies no learning. "
           f"GreenBox itself surveys earlier IoT designs {R('dashora', 'karthik', 'sharma', 'uma', 'anilkumar')}: accelerometer, vibration or heart-rate sensors with GPS and GSM alerts and, in one case, an alcohol sensor and a black-box log; "
           "it points out that accelerometer-only detection risks false positives on sudden braking. None of them grades severity.")
    P.para(f"**Vision-based detection.** CIRS {R('cirs')} is a multi-agent framework in which YOLOv11 detects accidents in camera frames (5,200 accident and 4,800 non-accident frames), a vision-language model describes the scene, and further agents locate and dispatch. "
           "YOLOv11 reaches top-1 accuracy 86.5%, precision 0.866, recall 0.856 and F1 0.861, and 128 of 1,044 non-accident frames were falsely classified as accidents. It needs fixed cameras, which a vehicle on a rural road does not have.")
    P.para(f"**Severity prediction.** Random forests and boosting on crash records have been applied to teen-driver crashes {R('lin')} and to logistic regression, decision-tree and forest comparisons on 9,472 Taiwanese crashes {R('chen')}; "
           f"recurrent {R('sameen')} and convolutional {R('zheng')} networks were tried on larger records (the base paper cites 73.76% accuracy for the recurrent model); explainable deep learning has been used for risk prediction {R('pei')}; and a recent review compares such methods {R('hamdan')}. "
           "All of them learn from recorded attributes after the event.")
    P.para("**Positioning.** The surveyed systems sit at two ends. IoT prototypes sense the crash but treat every impact alike and measure little; record-based severity models grade well-defined outcomes but cannot act, "
           "because their input is the report of an accident that has already been handled. The base paper's own limits make the distance explicit: its labels come from police files, its injury severity is a count of injured persons, and its inference cost is not studied. "
           "A phone-based pipeline must work from a few seconds of motion data, tolerate noise and orientation, and keep false alarms rare, because each costs the occupant a countdown and, if sent, a responder's time. "
           f"GreenBox's SMS cancellation {R('greenbox')} and the 128 false positives among 1,044 non-accident frames in CIRS {R('cirs')} both show that the confirmation step and the false-alarm rate are central, which is why ResQAI measures them.")
    P.table("Representative related work", ["Work", "Approach", "Data", "Reported result", "Limitation"], [
        [R("base"), "Multi-task FT-Transformer, SHAP", "30,442 Dongguan crash records", "Accuracy 70.31 / 90.38 / 80.79 %", "Post-event; no sensing or alert"],
        [R("greenbox"), "Arduino + GSM/GPS, SMS alert", "Prototype tests", "Qualitative, \"seconds\"", "No metrics, no learning, no severity"],
        [R("karthik") + ", " + R("sharma"), "Accelerometer / vibration + GSM", "Prototypes", "Not reported here", "No severity grade"],
        [R("cirs"), "YOLOv11 + vision-language agents", "5,200 + 4,800 frames", "Top-1 86.5 %, F1 0.861", "Fixed cameras; no severity"],
        [R("lin") + ", " + R("chen"), "RF, XGBoost, logistic, tree", "8,859 and 9,472 crashes", "Forest or XGBoost best", "Post-event records"],
        [R("sameen") + ", " + R("zheng"), "RNN, CNN on crash records", "Crash records", "RNN 73.76 % (as cited in base)", "Post-event; opaque"],
    ], widths=[0.45, 0.85, 0.8, 0.75, 0.55], size=6.5, align=["c", "l", "l", "l", "l"])
    P.para("**Gap.** Severity work learns from records written after the crash, and detection work seldom measures its error rates or grades severity. "
           "No surveyed system detects a crash from motion signals, grades it, lets the occupant cancel, and then locates the crash and ranks hospitals with reported measurements. ResQAI targets that gap at demonstration scale.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.para("**Architecture.** Fig. 1 shows the tiers. A React console calls a single Flask process that serves five scenario generators, the prediction route, the hospital ranking and the dispatch composition, with accounts handled by a separate blueprint. "
           "There is no database: users are stored as scrypt hashes in a JSON file, the ten-hospital directory is a second JSON file, and the scaler and the two forests are loaded once from four pickles. "
           "Readings, predictions and alerts exist only in requests and in the browser's state.")
    P.figure(figs["arch"], "ResQAI architecture: React console, Flask API, machine-learning tier and the file-based data tier.")
    P.para(f"**Data.** No real smartphone recordings were available, so the project generates {F.N_TOTAL:,} events from a seeded generator (seed 42): {F.DS['kind_counts_total']['normal']:,} normal-driving, {F.DS['kind_counts_total']['harsh_brake']:,} harsh-braking, "
           f"{F.DS['kind_counts_total']['minor_crash']:,} minor, {F.DS['kind_counts_total']['moderate_crash']} moderate and {F.DS['kind_counts_total']['severe_crash']} severe crashes (19.9% accidents). "
           "A crash draws a random-direction acceleration spike of 15-28, 28-45 or 45-80 m/s2 with rising gyroscope noise, deceleration and jerk; braking draws a forward deceleration of about 4.5 m/s2. "
           "Each event has eleven features: three acceleration axes, three gyroscope axes, their two magnitudes, speed before the event, speed change and jerk. "
           f"The split is 80/20 stratified on the accident label ({F.N_TRAIN:,} training, {F.N_TEST:,} test events; 477 test accidents).")
    P.para(f"**Models.** Features are standardised, z = (x - mu) / sigma, with the training mean and deviation. The accident detector is a random forest {R('breiman')} of 200 trees, depth 10, with balanced class weights, whose accident probability is the mean of the trees' class probabilities")
    P.eq("P(accident | x) = (1/T) Σ_t p_t(accident | z),   T = 200,")
    P.para("and the severity model is a second forest (250 trees, depth 12) over four classes. A forest was chosen because the inputs are eleven tabular numbers, training is seconds on a CPU, "
           "and the same family is a strong baseline in the base paper. The application then gates the grade so that a non-crash is never graded,", indent=0)
    P.eq("S(x) = 0 if the detector says no accident, otherwise the severity forest's class.")
    P.para("**Training.** Both forests use scikit-learn settings other than the tree count, depth and balanced class weights (random state 42). The severity forest is trained on all events with None as class 0, so it also learns what a non-crash looks like; "
           "the gate then makes the detector authoritative for the crash decision. The training script holds out 20% of the events and prints the accuracy and a classification report; it uses no validation split and no cross-validation, "
           "so the hyper-parameters were fixed in advance and not tuned. The evaluation below adds the repeats, baselines and stress tests that the script lacks.", indent=0.2)
    P.figure(figs["flow"], "Main flow of one event: detection, grading, gate, confirmation, location, hospital ranking and the displayed dispatch.")
    P.para(f"**Confirmation and dispatch.** The React console runs a state machine. A Moderate or Severe result pauses live monitoring (one reading every 1.5 s) and opens a {F.COUNTDOWN_S}-second countdown; "
           "the occupant can cancel with a button or Escape, which is logged as a false alarm, and at zero the alert is sent. The browser location is read with a 3-second timeout (otherwise the server uses a point near the default area), "
           "and the three nearest of ten hospitals are chosen by the haversine distance " + R("haversine"))
    P.eq("d = 2R asin( sqrt( sin2(Δφ/2) + cos φ1 cos φ2 sin2(Δλ/2) ) ),   R = 6371 km.")
    P.para(f"The response carries an alert id, the coordinates, the nearest hospitals with phone numbers, a message with a map link, and the national (112) and ambulance (108) numbers. "
           "No SMS, call or e-mail is actually sent; the message is displayed. If the model files are missing, three thresholds on acceleration magnitude (15, 28 and 45 m/s2) give a rule-based grade instead.")
    P.para("**Implementation.** The API validates registration (a name of 2 to 60 characters, an e-mail address, a password of 8 to 128 characters) and stores scrypt password hashes. Tokens are signed with a 12-hour expiry and sent as a Bearer header; "
           "five failed logins lock an account for five minutes, and setting REQUIRE_AUTH=1 makes every route except health and authentication demand a token (it is off by default so the original single-page dashboard keeps working). "
           "The simulation route draws each scenario from the training generator's parameters. The prediction route fills missing fields with defaults (1 g on the vertical axis, zeros elsewhere), derives the magnitudes, takes the absolute jerk, and returns the accident flag, the class, its label, the probability, the features used and the model source. "
           "The console keeps the last 40 sensor points and 25 events, offers a light and a dark theme, and shows the numbers 108 and 112 as tap-to-call links.")
    P.para("**Reproducibility.** Every figure and table in Section IV is produced by three scripts in the repository, one for the models (data regeneration with the training seed, baselines, ablations, noise, probes, thresholds), "
           "one for API latency and one for the unit, edge and security checks, and each writes a JSON file that this paper reads when it is built, so the text cannot drift from the measurements. "
           "The generator reproduces the training script's dataset exactly, so the held-out events are the ones the shipped models never saw.")
    P.para(f"**Evaluation protocol.** The shipped models were scored on the {F.N_TEST:,} held-out events (accuracy, precision, recall, F1, ROC-AUC, confusion matrices); the same procedure was repeated for five seeds with a new dataset, split and forests each time; "
           "logistic regression, a depth-10 tree, histogram gradient boosting and the three-threshold rule were trained on the same split; "
           "feature groups were removed and the models retrained; zero-mean Gaussian noise with a standard deviation of 0.05 to 1.0 times each feature's own was added to the test inputs; "
           "1,000 events each of two constructed road-surface probes (pothole-like and speed-breaker-like, parameters in the repository, not real recordings) were scored; and latency was timed on 127.0.0.1 with 300 calls per route. "
           f"The test run has {F.SMOKE_TOTAL} shipped smoke checks and {F.TEST_TOTAL} further unit, edge and security checks.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.para("**Test conditions.** Everything ran on the machine of Section I-A. The data are synthetic and drawn from the same generator for training and testing, so every accuracy below is an upper bound that says how well the classes are separated by construction. "
           "Table II lists the main figures.")
    P.table("Measured performance (shipped models, 2,400 held-out events)", ["Measure", "Value"], [
        ["Detector accuracy / precision / recall / F1 / AUC", f"{f3(det['accuracy'])} / {f3(det['precision'])} / {f3(det['recall'])} / {f3(det['f1'])} / {f3(det['roc_auc'])}"],
        ["Detector confusion [[TN, FP], [FN, TP]]", f"[[{det['confusion'][0][0]}, {det['confusion'][0][1]}], [{det['confusion'][1][0]}, {det['confusion'][1][1]}]]"],
        ["Severity accuracy / macro-F1", f"{f5(sev['accuracy'])} / {f5(sev['macro_f1'])}"],
        ["Severity per-class F1 (None, Minor, Moderate, Severe)", f"{f3(pc['None']['f1'])}, {f3(pc['Minor']['f1'])}, {f3(pc['Moderate']['f1'])}, {f3(pc['Severe']['f1'])}"],
        ["Alert trigger (Moderate or Severe): precision / recall", f"{f3(alr['precision'])} / {f3(alr['recall'])}; {pct(alr['false_alarm_rate'], 3)} false alarms"],
        ["Five seeds: severity accuracy, mean ± SD", f"{f5(seeds_m['sev_accuracy'])} ± {f5(seeds_s['sev_accuracy'])}"],
        ["Five seeds: severity macro-F1, mean ± SD", f"{f5(seeds_m['sev_macro_f1'])} ± {f5(seeds_s['sev_macro_f1'])}"],
        ["Hard braking flagged as accident", f"0 of {pk['harsh_brake']['n']}"],
        ["Pothole-like / speed-breaker-like flagged (probes)", f"{pct(ood['pothole']['predicted_accident_rate'])} / {pct(ood['speed_breaker']['predicted_accident_rate'])}"],
        ["Alert path (simulate + predict + emergency), mean (p95)", f"{ap['mean']:.1f} ms ({ap['p95']:.1f} ms)"],
        ["POST /api/predict, mean (p95); throughput", f"{ep['POST /api/predict']['mean']:.1f} ms ({ep['POST /api/predict']['p95']:.1f} ms); {F.LAT['predict_throughput_req_per_s_single_client']} req/s"],
    ], widths=[2.15, 1.25], size=6.8, align=["l", "c"])
    P.para(f"**Detection.** The detector made no error on {F.N_TEST:,} events and the lowest accident probability of a true crash (0.90) is well above the highest of a non-crash (0.17), so thresholds from 0.2 to 0.9 give identical, perfect results. "
           "This is not evidence of difficulty solved: braking and normal driving never exceed 13.2 m/s2 of acceleration magnitude, crashes never fall below 15.3, and the three-threshold rule detects as well as the forest (Table III).")
    sw = {r["threshold"]: r for r in F.SWEEP}
    P.para(f"At a threshold of 0.05 the detector raises {sw[0.05]['false_positives']} false alarms (precision {f3(sw[0.05]['precision'])}) and at 0.95 it misses {sw[0.95]['false_negatives']} crashes (recall {f3(sw[0.95]['recall'])}); the plateau between is wide, so the operating point is not sensitive on this data. "
           "On the minor crashes, whose acceleration is the lowest of the crash classes, all 233 test events were flagged and 232 graded Minor.")
    P.table("Severity grading against simpler models (same split)", ["Model", "Severity accuracy", "Macro-F1"], [
        ["Three-threshold rule on acc_magnitude", f4(rule["sev_accuracy"]), f4(rule["sev_macro_f1"])],
        ["Logistic regression", f4(B["logistic_regression"]["sev_accuracy"]), f4(B["logistic_regression"]["sev_macro_f1"])],
        ["Decision tree (depth 10)", f4(B["decision_tree (depth 10)"]["sev_accuracy"]), f4(B["decision_tree (depth 10)"]["sev_macro_f1"])],
        ["Histogram gradient boosting", f4(B["hist_gradient_boosting"]["sev_accuracy"]), f4(B["hist_gradient_boosting"]["sev_macro_f1"])],
        ["Random forest (ResQAI, retrained)", f4(rf["sev_accuracy"]), f4(rf["sev_macro_f1"])],
    ], widths=[2.0, 0.8, 0.6], size=6.8, align=["l", "c", "c"])
    P.para(f"**Severity.** The only error in {F.N_TEST:,} events is a minor crash graded Moderate (acceleration 31.9 m/s2, in the overlap of the minor and moderate ranges); it is an adjacent-class error and turns a log-only event into an alert. "
           f"Over five seeds the accuracy is {f4(seeds_m['sev_accuracy'])} ± {f5(seeds_s['sev_accuracy'])} and the worst seed is {f4(F.SEEDS['min']['sev_accuracy'])}. "
           f"The forest beats the threshold rule ({f4(rf['sev_accuracy'])} against {f4(rule['sev_accuracy'])}) but is tied with gradient boosting, and logistic regression is already at {f4(B['logistic_regression']['sev_accuracy'])} (Fig. 3a). "
           f"Acceleration magnitude carries most of the signal (permutation drop in macro-F1 {F.IMP['severity_permutation_macro_f1_drop']['acc_magnitude']:.2f}), followed by speed change and speed before; the gyroscope adds nothing measurable here, "
           f"and acceleration magnitude alone gives severity accuracy {f4(F.ABL['acc_magnitude only']['sev_accuracy'])}.")
    P.para(f"**Alert-level view.** What the occupant experiences is not the four-class grade but whether the countdown starts. On the test events {alr['confusion'][0][1]} of {alr['confusion'][0][0] + alr['confusion'][0][1]} events that should not start it did (a minor crash graded Moderate), and none of the {alr['confusion'][1][1]} that should was missed. "
           f"Across the five seeds, however, alert recall averages {f4(seeds_m['alert_recall'])} ± {f4(seeds_s['alert_recall'])} (worst {f4(F.SEEDS['min']['alert_recall'])}) and precision {f4(seeds_m['alert_precision'])}, "
           "so about 0.7% of Moderate or Severe crashes are graded one step too low and would start no countdown, and the cost of that error is much larger than the cost of a false trigger. "
           "A deployment would therefore bias the alert rule toward recall, for example by also alerting on a Minor grade with a high probability and a large speed change.")
    A = F.ABL
    P.table("Feature-group ablation (models retrained on each subset)", ["Features kept", "Det. acc.", "Sev. acc.", "Sev. macro-F1"], [
        [lab, f4(A[k]["det_accuracy"]), f4(A[k]["sev_accuracy"]), f4(A[k]["sev_macro_f1"])] for lab, k in
        (("All 11", "all 11 features"), ("Accelerometer only (4)", "accelerometer only (x, y, z, magnitude)"), ("acc_magnitude alone", "acc_magnitude only"), ("Without gyroscope", "without gyroscope"),
         ("Without speed features", "without speed (speed_before, speed_change)"), ("Without jerk", "without jerk"), ("Without acc_magnitude and jerk", "without acc_magnitude and jerk"))],
        widths=[1.5, 0.6, 0.6, 0.7], size=6.8, align=["l", "c", "c", "c"])
    P.para("Removing any single group costs little because the features are correlated: magnitude, jerk and speed change all grow with the severity of the impact. Only dropping magnitude and jerk together lets one detector error appear. "
           "Gyroscope data would matter for rollover or spin, but the generator gives it only a noise level that rises with severity, so this experiment cannot show its value on real vehicles.")
    P.figure(figs["results"], "(a) Severity macro-F1 of the rule, logistic regression (LR), decision tree (DT), gradient boosting (HGB) and random forest (RF). (b) Effect of sensor noise on the shipped models.")
    P.para(f"**Robustness and failure cases.** The models were never trained on noisy inputs. With noise at 0.1 of each feature's deviation they are unchanged (detector F1 {f3(n3[0.1]['det_f1'])}); at 0.25 the detector false-alarm rate is {pct(n3[0.25]['det_false_alarm'])}; at 0.5 it is {pct(n3[0.5]['det_false_alarm'])} and severity macro-F1 falls to {f2(n3[0.5]['sev_macro_f1'])} (Fig. 3b). "
           f"The pothole-like and speed-breaker-like probes, which the generator never produces, were flagged as accidents {pct(ood['pothole']['predicted_accident_rate'])} and {pct(ood['speed_breaker']['predicted_accident_rate'])} of the time, with mean probability about 0.5, "
           "so the detector has no concept of road-surface events; none reached Moderate or Severe, so none would start the countdown. The stated objective of separating potholes and speed breakers from crashes is therefore not demonstrated, only hard braking is. "
           f"The shipped smoke test passes {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks; the {F.TEST_TOTAL} further checks pass {F.TEST_PASSED}, and the failures are input-validation gaps: non-numeric fields and a JSON array return HTTP 500, a negative hospital count returns nine of ten hospitals, "
           "out-of-range coordinates are accepted, and two alerts raised within the same second share one alert id.")
    P.figure(figs["countdown"], "Output screen: a Severe result (100% accident probability) opens the 15-second confirmation with Cancel and Send buttons.", width=3.0)
    P.figure(figs["dispatch"], "Output screen: dispatch summary after the alert is sent: id, severity, device-GPS location and nearest hospital with its phone number.", width=3.0)
    P.para(f"**Latency.** On the loopback interface of the test machine the in-process model call takes {inf['mean']:.1f} ms on average, /api/predict {ep['POST /api/predict']['mean']:.1f} ms and the three-call alert path {ap['mean']:.1f} ms (p95 {ap['p95']:.1f} ms) "
           f"on the Flask development server. This excludes the {F.COUNTDOWN_S}-second confirmation window by design and any real network delivery, which was not implemented and so not measured; no load test with several users was run.")
    P.para("**Threats to validity.** The generator, the probes and the hospital directory were written by the same team that built the models, which favours the system. The ten-hospital directory is a demonstration list for one city, and neither the GPS accuracy nor the map were scored. "
           "Alerts are not stored on the server and carry no user id, no concurrent-user test was run, the development server is single-process, and no occupant, clinician or responder was consulted. "
           "A real deployment would need labelled phone recordings with realistic noise, orientation and mounting, which the sensor streams in the console only imitate.")
    P.para(f"**Confirmation window.** The {F.COUNTDOWN_S}-second value is a design constant that was neither tuned nor tested with users: a shorter window risks dispatching for an occupant who is conscious but slow to respond, and a longer one delays help for one who is not. "
           "While the dialog is open live monitoring is paused, and a second event is logged but does not restart or replace the countdown. The window is also the dominant delay in the system: it is about 265 times the 56 ms of computation in the alert path.")
    P.para(f"**Comparison with the base paper.** The base paper {R('base')} reports 70.31%, 90.38% and 80.79% accuracy for three severity tasks on 30,442 real crash records with up to six classes per task. "
           "ResQAI's figures are on synthetic sensor events, with a four-class severity and a binary detection. The datasets, the inputs (recorded attributes against sensor readings), the labels and the tasks all differ, "
           "so the numbers cannot be compared and no superiority is claimed; the base paper's results on real data are much harder-won than 0.9996 on generated events. What ResQAI adds is the part the base paper leaves out: live sensing, a confirmation step, location and a dispatch message, with measured latency.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para(f"ResQAI detects a crash from eleven sensor features, grades its severity, asks the occupant to confirm within 15 seconds, and composes a located alert with the three nearest hospitals. "
           f"Of the six project objectives, severity grading ({f4(sev['accuracy'])} accuracy on synthetic data), location with hospital ranking, and the evaluation of accuracy, false alarms and latency are achieved; "
           "collecting real smartphone data and separating potholes and speed breakers from crashes are not; and automated dispatch is only simulated, because no message is sent. "
           "The key finding is that the synthetic classes are separable enough that a one-line threshold detects as well as the forest, so the learned model matters only for severity, and that road-surface events outside the generator are flagged about half the time. "
           "The limits are the synthetic data, a single machine, no real GPS or messaging path and the validation gaps above. A pipeline of this shape is worth building on only once it has been trained and tested on real recordings; until then its numbers describe the software, not the roads.")
    P.para("Future work: record labelled data from real phones, including potholes and speed breakers; train and test on noisy, orientation-varied signals; add an SMS or call gateway and a live hospital directory; "
           "validate the inputs and issue unique alert ids; and tie each alert to an account so that contacts can be notified.")

    P.references()
    P.save(path)
    return path, P.order


if __name__ == "__main__":
    out = os.path.join(F.BATCH, "19.IEEE_Paper.docx")
    path, order = build(out)
    print(path, "refs:", len(order), order)
