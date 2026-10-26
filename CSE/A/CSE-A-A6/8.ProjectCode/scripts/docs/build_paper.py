"""Builds 19.IEEE_Paper.docx (two-column, ~6 pages) for Smart Rider. Run after the experiments, figures and screenshots exist.

    python -m scripts.docs.build_paper

Every number is read from experiments/*/metrics.json through facts.py (see docs/REPORT_FACTS.md); the paper is a
condensation of the report and must not disagree with it.
"""

import os

from PIL import Image

from . import facts as F
from .ch8 import analysis
from .paper import Paper


def crop_shot(name, out, box):
    p = os.path.join(F.FIGS, out)
    Image.open(F.shot(name)).convert("RGB").crop(box).save(p)
    return p


def cond(name):
    return next(c for c in F.ROB["conditions"] if c["condition"].startswith(name))


def build(path):
    geo, cew = F.GEO, F.CEW
    gd, gb = geo["default_threshold_0.21"], geo["best_threshold_in_sample_youden"]
    cd, cb = cew["default_threshold_0.21"], cew["best_threshold_in_sample_youden"]
    api = F.API_LAT["POST frame (real face JPEG 640x480, monitoring on)"]
    lat = cew["latency_ms_vision_process_640x480"]
    rules = F.RULES
    pct = F.pct
    A = analysis()
    hw = F.HW
    unit, smoke = F.TESTS["unittest"], F.TESTS["web_smoke"]
    fa = {r["case"]: r for r in rules["false_alarm_on_blink_streams"]}
    slow20 = fa["20% slow blinks (0.8-1.3 s), 17/min"]
    other = rules["other_rules"]
    dark50, dark25 = cond("brightness x0.50"), cond("brightness x0.25")
    glasses, tint, one_eye = cond("opaque sunglasses"), cond("tinted lenses"), cond("one eye covered")
    mask, noise, blur2 = cond("lower face masked"), cond("Gaussian noise"), cond("Gaussian blur sigma 2")
    base = cond("baseline")
    fpr = gd["fp"] / (gd["fp"] + gd["tn"])
    fpr_b = gb["fp"] / (gb["fp"] + gb["tn"])
    byc = cew["by_class"]

    P = Paper()
    dept, college, city = "Dept. of Computer Science and Engineering", "TKR College of Engineering and Technology", "Hyderabad, India"
    authors = [[n.title(), dept, college, city, "[email address]"] for n, _ in F.STUDENTS]
    authors.append(["N. Padmavathi", "[DESIGNATION], " + dept, college, city, "[email address]"])
    P.title_block("Smart Rider: A Webcam Impairment Warning from Eye Closure and Head Tilt", authors)
    P.begin_two_columns()

    P.abstract(
        "Drunk riding is a serious road-safety problem, but a camera cannot confirm that someone has drunk alcohol. This paper describes and measures Smart Rider, "
        "a webcam system that warns of possible drowsiness or impairment from visible eye and head cues. Face landmarks give an eye aspect ratio and the image-plane "
        "head roll, quality gates withhold a verdict when the signal is unreliable, and transparent duration rules with a per-rider calibration produce one of three "
        "outputs: Normal, Possible impairment or drowsiness, or Unable to assess. No deep-learning classifier was trained, no intoxication data were available and no "
        "prevention action such as an ignition lock is implemented. On "
        f"{geo['images_total']:,} public face images the eye-state signal reaches an AUC of {geo['auc_ear_closed_vs_open']:.3f} and {pct(gd['accuracy'])} accuracy at the "
        f"default threshold, which calls {pct(fpr)} of open eyes closed; the quality gates pass only {pct(cew['coverage'], 0)} of these low-resolution images and refuse "
        f"to assess when brightness is halved. On scripted streams a closure must last about {A['min_closure_that_warns']:.1f} s to warn. One camera frame takes "
        f"{api['p50_ms']:.0f} ms through the API on a laptop CPU. The system is a stationary demonstration prototype and not an alcohol test.",
        ["driver monitoring", "eye aspect ratio", "explainable rules", "facial landmarks", "impairment warning", "MediaPipe", "quality gating"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Road crashes kill about 1.19 million people a year, and riders of powered two- and three-wheelers account for 21 % of those deaths {r:17}. Impairment by alcohol or "
           "fatigue is among the preventable causes, yet it is checked mainly at the roadside and only occasionally. Trained officers already judge impairment partly from "
           "the eyes, for example through gaze nystagmus {r:18}, which suggests that eye behaviour carries a signal that a camera might also see.")
    P.para("Vision research on drivers has concentrated on drowsiness: the eye aspect ratio (EAR) of six eye landmarks {r:9}, the share of time the eyes are closed {r:15}, blink "
           "behaviour {r:16} and combined visual cues {r:28}. The base paper of this work, Feng and Li {r:1}, fuses EAR, head pose and voice commands with a fuzzy belief rule-based "
           "engine on an embedded board. Work aimed at alcohol uses facial video {r:2,4}, thermal images {r:5,8} or a smartwatch {r:3}. All of it needs labelled intoxicated data, "
           "which are hard to obtain: many source videos of the best-known face dataset are no longer online {r:2}, and testing detection systems requires giving participants alcohol "
           "under controlled conditions {r:6}.")
    P.para("The project title promises alcohol intoxication detection and prevention. What was built is narrower and is stated here plainly: a **rule-based drowsiness and impairment "
           "warning**. It is not an alcohol detector. It has no trained deep-learning classifier because no intoxication dataset was available, it implements no prevention action "
           "(it never touches ignition, brakes or power and notifies no contact), it does not measure gaze, and it has not been studied with riders. Of the six batch objectives, two "
           "were achieved, two partly and two not. The contributions are:")
    P.para("(1) an explainable, quality-gated and personally calibrated rule engine with three outputs, one of which is a refusal to guess; (2) a desktop and web implementation "
           f"verified by {unit['passed']} unit tests and {smoke['passed']} API checks; (3) measurements of its parts: eye-state separation on public data, behaviour under degraded "
           "images, rule behaviour on scripted streams and latency; and (4) an offline, subject-disjoint evaluation pipeline that has so far run only on a synthetic demonstration file.",
           indent=0)
    P.para("**Why a refusal matters.** A warning system for a rider can fail in two familiar ways: it can miss an impaired rider, or it can accuse a sober one. A third failure is "
           "quieter, namely reporting confidently when the eyes cannot be seen at all. Smart Rider treats the third as the most avoidable. When the picture is dark, blurred, off-centre "
           "or the eyes are hidden it answers *Unable to assess* and discards what it has accumulated instead of guessing. The price is availability, which Section IV measures. "
           "Normal never means fit to ride.")
    P.para("Section II reviews related work, Section III describes the method, Section IV reports measurements and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para(f"All measurements ran on one laptop: {hw['cpu']}, {hw['ram']} RAM, {hw['gpu']}, {hw['os']}. No GPU was used.")
    P.sub("B", "Software Requirements")
    P.para(f"Python {hw['python']} with MediaPipe {hw['mediapipe']} {{r:11}}, OpenCV 5.0, NumPy 2.5 and Matplotlib 3.11; FastAPI 0.162 {{r:22}} with SQLite for the server; "
           "React 18, Vite 8 and TypeScript for the web interface; the standard unittest library and a scripted API check for testing. Google's face-landmark model "
           "(about 3.7 MB) is downloaded once.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para("**Base paper.** Feng and Li {r:1} build an adaptive driver monitoring system for drowsiness, fatigue and distraction. MediaPipe landmarks give a six-point EAR and a "
           "four-point variant, EAR-4, that uses only the upper eyelid; head pose is estimated from six landmarks; a small speech model handles voice commands; and a fuzzy belief "
           "rule-based engine fuses the three sources and sounds a buzzer above a risk threshold. A personal EAR threshold is learned from more than 300 frames. On four subjects "
           "of the NTHU drowsy-driver data {r:14} (65,834 frames, 80/20 split) Random Forest and XGBoost reach an EAR-4 recall of 0.894 for one subject against 0.856 for six-point "
           "EAR, and the system runs at 25 frames per second on a Jetson Orin Nano. The authors list subject-independent validation as future work. The target is drowsiness, not alcohol.")
    P.para("**Eye measures and drowsiness.** EAR was introduced for blink detection {r:9}; closure over time (PERCLOS) was proposed as a real-time alertness measure {r:15} and blink "
           "rate was studied as a fatigue signal {r:16}. Ji et al. {r:28} combine eyelid movement, gaze, head movement and expression in a probabilistic model with infrared "
           "illumination. These works establish the cues Smart Rider uses, but in all of them the target state is fatigue.")
    P.para("**Intoxication from the face and body.** Baroutian et al. {r:2} fuse a graph attention network over facial landmarks with 3D ResNet features on 3,542 clips from 202 "
           "people (YouTube) and report 95.82 % accuracy. The DIF dataset {r:4} labels how intoxicated people look, not their measured alcohol level. Thermal images "
           "have been used with CNNs and classical classifiers {r:5,8}, and a smartwatch study with 54 participants on a test track reaches an AUROC of 0.88 {r:3}. A testing "
           "methodology for in-vehicle alcohol detection is still being piloted {r:6}.")
    P.para("**Datasets.** Public driver datasets cover drowsiness and yawning, for example NTHU-DDD {r:14} and YawDD {r:27}, but none of the intoxication studies cited here releases "
           "labelled video that could simply be reused: DIF depends on videos that have since been removed {r:2}, the study of Baroutian et al. {r:2} is curated from online clips, "
           "and the thermal studies used their own volunteers {r:5,8}. For the eye-state component alone, the Closed Eyes in the Wild data (CEW) {r:12} supply 1,192 "
           "closed-eye faces from the Internet and 1,231 open-eye faces taken from LFW {r:13}, so the signal can be checked even though intoxication cannot.")
    P.para("**Critical reading.** The cues reported for intoxicated faces, such as prolonged eye closure, downward gaze and head tilt {r:2}, overlap with those of drowsiness, and the same "
           "study found false negatives for intoxicated people with neutral expressions. A system that sees only eyes and head tilt can therefore report that something is wrong "
           "but not what. This is the reason the output of this work is a *possible impairment or drowsiness* warning and never an alcohol result.")
    P.para("**Evaluation practice.** The reported figures come from different protocols. The base paper {r:1} splits the frames of four subjects 80/20 at random and lists subject-independent "
           "validation as future work, which can let a person's appearance leak across the split; Baroutian et al. {r:2} split by subject over curated clips; the smartwatch study {r:3} "
           "uses leave-one-subject-out validation on a test track. This work therefore keeps its offline pipeline subject-disjoint and does not rank its own eye-state numbers against these results.")
    P.table("Representative related work", ["Ref.", "Approach", "Data", "Reported result", "Limitation"], [
        ["{r:1}", "EAR-4, head pose, voice, fuzzy rules", "NTHU-DDD, 4 subjects", "EAR-4 recall 0.894; 25 FPS", "Drowsiness; not alcohol"],
        ["{r:2}", "Landmark GAT + 3D ResNet", "202 people, 3,542 clips", "95.82 % accuracy", "Online videos"],
        ["{r:3}", "Smartwatch accelerometer + HRV, CNN", "54 participants, test track", "AUROC 0.88 / 0.86", "Preprint; wearable"],
        ["{r:5}", "Thermal camera, CNN", "50 volunteers", "85.10 % (4 levels)", "Abstract only read"],
        ["{r:8}", "Thermal faces, MLP and others", "Public + own images", "About 90 %", "Abstract only read"],
        ["{r:28}", "Eyelid, gaze, head cues; probabilistic", "Drivers, infrared", "Robust per abstract", "Fatigue; infrared"],
    ], widths=[0.38, 0.78, 0.68, 0.85, 0.71], size=7, align=["c", "l", "l", "l", "l"])
    P.para("**Gap.** Published intoxication detectors need labelled alcohol data and report results on data the team here did not have, while drowsiness work does not claim alcohol. "
           "What is missing in this setting is a camera system that is explicit about what it cannot know: one that gates its input, explains each verdict, calibrates to the person and "
           "has measured limits. Smart Rider addresses that narrower gap, not the detection of alcohol.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.para("**Pipeline.** A browser or desktop camera supplies 640 x 480 frames that live only in memory. MediaPipe Face Landmarker {r:11} returns 478 landmarks. Seven "
           "quality gates are applied first: mean brightness outside 40 to 225, Laplacian variance below 25, frame-to-frame change above 35, no face or more than one face, eye "
           "width below 14 px, eye-region contrast too low and a difference between the two eyes' EAR above 0.12. A frame that fails any gate gives *Unable to assess* and clears all "
           "evidence. Otherwise an observation (time, EAR, roll) enters the rule engine. Fig. 1 shows the architecture.")
    P.figure(F.diag("01_system_architecture.png"), "Architecture: React and Tk front ends, FastAPI service, shared Python modules and numeric-only data stores.")
    P.para("**Features.** For six eye points p1 to p6 the EAR is (|p2 - p6| + |p3 - p5|) / (2 |p1 - p4|), averaged over both eyes and smoothed by a median of three frames. Head roll is "
           "atan2(y_r - y_l, |x_r - x_l|) between the outer eye corners, in degrees; it is an image-plane tilt, not a full head pose. An eye is closed when the smoothed EAR is below a "
           "threshold, 0.21 by default. Blink rate is displayed but never warns on its own.")
    P.para("**Rules.** A closure of at least 1.5 s, or a closed-eye fraction of at least 0.55 over the last 10 s (with 8 s of history), or a roll of at least 25 degrees with a closed "
           "eye starts an evidence timer; the warning appears only when the evidence persists for another second with 2 s of reliable history. Alert sounds are rate limited to one "
           "per 15 s. Every verdict carries its reason. The constants are engineering choices; they were not tuned on data, and they are adjustable within validated bounds.")
    P.para("**Start-up and recovery.** After monitoring starts, 2 s of continuous good observations are required before *Normal* can appear. Any failed gate, a time gap above 0.5 s or a "
           "non-finite value clears the closure timers, the 10 s window and the evidence, so a warning can never be built from stale or unreliable data; only the alert-sound cool-down "
           "is kept across such gaps, which prevents a flickering signal from sounding the alert repeatedly.")
    P.para("**Calibration.** The rider looks forward with eyes open for 8 to 15 s. If at least 40 frames and 70 % of observations are usable and the EAR spread is small, the threshold "
           "becomes 0.72 times the median EAR, limited to 0.12 to 0.32. Calibration cannot tell whether the rider was already tired.")
    P.para("**Design principles.** Four choices follow from the missing data. Decisions are rules a reviewer can read, because there is no labelled intoxication set to train on and a "
           "black box could not be justified without one. Every verdict carries a reason, so a warning can be checked against the measurements. Unreliable input produces a refusal, "
           "not a guess. And no image is kept: frames exist in memory for the length of one request, and only numeric events are written, locally.")
    P.figure(F.diag("02_high_level_workflow.png"), "Main flow of a monitoring session, from sign-in to review.")
    P.para("**Implementation.** The original Tkinter application and a FastAPI service share the same vision, rule and storage modules. The service issues an HMAC-signed 12-hour "
           "demo token, validates every input and stores only numeric events (state, quality, reason, EAR, closure, roll) in SQLite; it never writes images. A React interface shows the "
           "live verdict, history, thresholds and an offline research page. The offline pipeline cuts labelled measurement files into 5 s windows, separates subjects between "
           "training and test, and fits a standardised nearest-centroid classifier; it never changes the live rules.")
    P.para("**Logging and export.** An event row is written when the state or the signal quality changes, every 5 s while monitoring and whenever an alert fires. Each row has a UTC "
           "timestamp, a source label (live camera, or the name of the simulated scenario so that scripted rows cannot be mistaken for live ones), the verdict, its reason and the "
           "measurements. The history screen shows the latest 500 rows with a chart, and the whole table can be exported as a CSV file.")
    P.para("**Offline pipeline.** For research use, a measurement file has the columns subject, session, time, EAR, roll, quality, label and consent. Windows of 5 s need at least 20 frames, "
           "4.5 s of coverage, gaps of at most 0.5 s, all-Good quality and one label. Six features (EAR mean, standard deviation and minimum, closed fraction, mean absolute roll, roll "
           "standard deviation) are standardised on training windows only, and each test window goes to the nearer class centroid. Subjects never appear on both sides, precision is "
           "TP/(TP+FP), recall TP/(TP+FN), F1 2TP/(2TP+FP+FN) and the false-alarm rate FP/(FP+TN), all per window and not per hour.")
    P.para(f"**Evaluation protocols.** (a) The eye-state signal was run through the shipped code on the Closed Eyes in the Wild data {{r:12}}: {cew['closed_images']:,} "
           f"closed-eye faces from the Internet and {cew['open_images']:,} open-eye faces from LFW {{r:13}}, as 100 x 100 images upscaled to 480 x 480. It was scored twice: with the quality gates "
           "(the shipped pipeline) and geometry only (same landmarks and EAR, no gates). (b) 272 open-eye faces were degraded by darkening, over-exposure, blur, noise, opaque or "
           "tinted lenses, a covered eye and a masked lower face, to see how the gates respond. (c) Seeded scripted EAR streams (open 0.30, closed 0.12) probe the rule engine. "
           "(d) Latency was timed on 127.0.0.1 with a real face image. ROC analysis follows Fawcett {r:25}.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.para(f"**Eye-state signal.** Table II gives the results on the CEW faces at the default threshold of 0.21 (closed eyes are the positive class). Without gates, {geo['face_found']:,} of "
           f"{geo['images_total']:,} faces gave a measurement; EAR averaged {geo['ear_mean_closed']:.3f} for closed and {geo['ear_mean_open']:.3f} for open eyes, an AUC of "
           f"{geo['auc_ear_closed_vs_open']:.3f}. At 0.21 the signal misses {pct(A['default_missed_closed_rate'])} of closed eyes but calls {pct(fpr)} of open eyes closed. "
           f"The sweep in Fig. 3 shows why: a threshold of {gb['threshold']:.2f} would give {pct(gb['accuracy'])} accuracy and a {pct(fpr_b)} false-closure rate. That value was found on the "
           "same images and is context, not a tuned setting; the default was left at 0.21, which the personal calibration is meant to correct.")
    rows = [
        ["Geometry only, 0.21", f"{geo['face_found']:,}", pct(gd["accuracy"]), pct(gd["precision"]), pct(gd["recall"]), pct(gd["specificity"]), pct(gd["f1"]), f"{geo['auc_ear_closed_vs_open']:.3f}"],
        [f"Geometry only, {gb['threshold']:.2f} (in-sample)", f"{geo['face_found']:,}", pct(gb["accuracy"]), pct(gb["precision"]), pct(gb["recall"]), pct(gb["specificity"]), pct(gb["f1"]), f"{geo['auc_ear_closed_vs_open']:.3f}"],
        ["Shipped, gated, 0.21", f"{cew['assessed_good']:,}", pct(cd["accuracy"]), pct(cd["precision"]), pct(cd["recall"]), pct(cd["specificity"]), pct(cd["f1"]), f"{cew['auc_ear_closed_vs_open']:.3f}"],
        [f"Shipped, gated, {cb['threshold']:.2f} (in-sample)", f"{cew['assessed_good']:,}", pct(cb["accuracy"]), pct(cb["precision"]), pct(cb["recall"]), pct(cb["specificity"]), pct(cb["f1"]), f"{cew['auc_ear_closed_vs_open']:.3f}"],
    ]
    P.table("Eye-state results on CEW faces (closed = positive)", ["Setting", "n", "Acc.", "Prec.", "Rec.", "Spec.", "F1", "AUC"], rows,
            widths=[1.02, 0.31, 0.37, 0.37, 0.37, 0.37, 0.37, 0.28], size=6.5, align=["l", "c", "c", "c", "c", "c", "c", "c"])
    P.figure(F.fig("threshold_sweep.png"), "Accuracy, closed-eye recall and open-eye specificity against the EAR threshold on the images that pass the gates; the dashed line is 0.21.", width=3.2)
    P.figure(F.fig("roc.png"), "ROC curve of the EAR for closed against open eyes on the assessed images.", width=2.4)
    cl, op = byc["closed"], byc["open"]
    P.para(f"**Overlap of the classes.** The ROC curve in Fig. 4 stays close to the top-left corner. On the assessed images the EAR of closed eyes lies between {cl['ear_p5_p95'][0]:.3f} and {cl['ear_p5_p95'][1]:.3f} (5th to 95th percentile) and that of open eyes "
           f"between {op['ear_p5_p95'][0]:.3f} and {op['ear_p5_p95'][1]:.3f}. The open-eye spread is wide because narrowed eyes, squints, eyeglasses and head pose all lower the ratio, and "
           "this tail is what a fixed threshold of 0.21 falsely calls closed. A per-rider threshold, which Smart Rider sets at 0.72 of the median open-eye EAR, moves with the person; "
           "the CEW images are of different people with no per-person calibration frames, so the effect of calibration could not be measured here.")
    P.para(f"**Quality gates.** The shipped pipeline assesses only {cew['assessed_good']:,} of {cew['images_total']:,} images ({pct(cew['coverage'])}); the main reason is the sharpness gate, "
           "because a 100-pixel face enlarged almost five times is soft. Among assessed images accuracy is higher, "
           f"{pct(cd['accuracy'])}, and AUC {cew['auc_ear_closed_vs_open']:.3f}. Counting every unassessed image as wrong gives {pct(cew['end_to_end_accuracy_unassessed_counted_wrong'])}. "
           f"Coverage is alike for both classes ({pct(cl['coverage'], 0)} closed, {pct(op['coverage'], 0)} open). The sharpness gate rejects {cl['quality_breakdown']['Blurred or hidden eyes']} closed and "
           f"{op['quality_breakdown']['Blurred or hidden eyes']} open images, and a spurious second face {cl['quality_breakdown']['Multiple faces']} and {op['quality_breakdown']['Multiple faces']}. "
           "These coverage figures are a property of the test images, not of webcam frames, and vary by about two points between runs because the landmark tracker keeps state "
           "between frames. Fig. 5 shows the live screen with landmarks on a real face, and Fig. 9 the landmarks on CEW faces.")
    P.figure(crop_shot("06_monitor_camera_normal.png", "paper_monitor.png", (270, 85, 1430, 900)),
             "Output screen, live camera path: landmarks on a real face, verdict Normal, EAR 0.254 against a calibrated threshold of 0.183.", width=3.0)
    P.para(f"**Degraded conditions.** Of {base['n']} open-eye faces, {pct(base['good_rate'])} are assessed unmodified. Halving the brightness leaves {dark50['good']} assessed and a quarter leaves "
           f"{dark25['good']}; Gaussian blur of 2 px leaves {blur2['good']}; opaque sunglasses leave {glasses['good']}, a covered eye {one_eye['good']}. The gates therefore fail safe (Fig. 8), with "
           f"*Unable to assess*, but they are strict, so availability in dim light is poor. Noise ({pct(noise['good_rate'], 0)}), tinted lenses ({pct(tint['good_rate'], 0)}) and a masked "
           f"lower face ({pct(mask['good_rate'], 0)}) are mostly still assessed, with false-closure rates of {pct(noise['false_closure_rate_among_good'])}, {pct(tint['false_closure_rate_among_good'])} and "
           f"{pct(mask['false_closure_rate_among_good'])}.")
    P.para(f"**Rule behaviour.** On scripted streams closures up to {A['longest_closure_never_warns']:.1f} s never warn and closures of {A['min_closure_that_warns']:.1f} s or more always do, "
           f"with a latency of {A['warn_latency_15fps']:.2f} s at 15 frames per second (the 1.5 s closure rule plus 1 s of persistence, plus median lag). No warning occurred in 300 "
           "sessions of 180 s each with normal blinks, frequent blinks, noisy EAR or 5 % slow blinks; with 20 % slow blinks "
           f"{slow20['sessions_with_warning']} of 300 sessions warned ({slow20['alerts_per_hour']:.1f} alerts per hour). A 60 %-closed pattern of 0.9 s closures warned after "
           f"{other['closed_fraction_rule']['first_warning_after_onset_s']:.1f} s, a 30-degree tilt with a low EAR after {other['tilt_rule']['first_warning_after_onset_s']:.1f} s, and tilt alone never warned. "
           "These streams are generated, so they show how the rules behave, not how real riders blink. Fig. 6 shows the warning screen for a scripted closure and Fig. 7 how often a closure of each length warns.")
    P.figure(crop_shot("04_monitor_simulation_warning.png", "paper_warning.png", (270, 85, 1430, 900)),
             "Output screen, simulation: a scripted prolonged closure raises the warning with its reason; the simulation is labelled on screen.", width=3.0)
    P.figure(F.fig("closure_vs_warning.png"), "Share of scripted runs that warn against the length of one closure, at three frame rates (default rules).", width=2.7)
    sw = {(r["closure_seconds"], r["persistence_seconds"]): r for r in rules["parameter_sweep"]}
    sel = [(1.0, 0.5), (1.0, 1.0), (1.5, 0.5), (1.5, 1.0), (1.5, 2.0), (2.0, 0.5), (2.0, 1.0), (3.0, 0.5)]
    P.table("Rule parameters on scripted streams (default in bold)", ["Closure (s)", "Persistence (s)", "Detects 3 s closure", "Alerts per hour*"],
            [[("**%.1f**" if k == (1.5, 1.0) else "%.1f") % k[0], ("**%.1f**" if k == (1.5, 1.0) else "%.1f") % k[1], pct(sw[k]["detect_3s_closure_rate"], 0),
              f"{sw[k]['alerts_per_hour_with_10pct_slow_blinks']:.2f}"] for k in sel],
            widths=[0.7, 0.85, 1.0, 0.85], size=7, align=["c", "c", "c", "c"])
    P.para("*Streams with 10 % slow blinks (0.8 to 1.3 s). Shortening the closure or persistence time detects the same 3 s closure but alerts more often on slow blinks; any pair whose "
           "sum exceeds 3 s misses it. The default, 1.5 s and 1.0 s, detects every scripted closure and raised no alert on these streams. This is a trade-off curve of a generator, "
           "not a measured rate for riders.", indent=0, size=8)
    P.figure(F.fig("robustness.png"), "Share of open-eye faces that are assessed under each degradation; the rest receive *Unable to assess*.", width=3.1)
    P.para(f"**Speed and tests.** A camera frame takes a median of {api['p50_ms']:.1f} ms (95th percentile {api['p95_ms']:.1f} ms) from HTTP request to annotated reply, and the landmark "
           f"step alone averages {lat['mean']:.1f} ms, about 30 frames per second on one laptop CPU. The rule engine costs {F.RULES['engine_cost']['microseconds_per_update']:.0f} microseconds "
           f"per observation. All {unit['passed']} unit tests and {smoke['passed']} API checks pass.")
    P.para("**Offline pipeline.** The subject-disjoint pipeline was exercised on a seeded synthetic file of six subjects, 12 held-out windows per class. It separated them perfectly, "
           "which says only that the code runs: the data are generated, the screen that shows the report carries a *Synthetic data* banner, and the pipeline has never seen a real "
           "labelled recording. It is therefore listed as untested on real data and not as a result.")
    P.figure(F.fig("landmark_examples.png"), "Six eye landmarks (green) on CEW faces that passed the gates, with the EAR obtained.", width=3.3)
    P.para("**Comparison with the base paper.** The two studies differ in target (drowsiness, not alcohol), data, method and hardware, so this is context and not a ranking. The base "
           "paper reports an EAR-4 recall of 0.894 for one NTHU subject with Random Forest, on frames of four drivers, and 25 frames per second on a Jetson Orin Nano. Here the six-point "
           f"EAR has a recall of {pct(gd['recall'])} and a specificity of {pct(gd['specificity'])} at one threshold on still faces from two image sources, with no learned model and "
           "no voice or fuzzy fusion.")
    P.para("**Objectives.** Real-time capture with landmarks (objective 1) and continuous inference with an alert above a threshold (objective 4) were achieved. Impairment cues (objective 2) "
           "were measured only in part: EAR, closure time, closed fraction, blink rate and head roll, but not gaze. The deep-learning classifier (objective 3) and the prevention action "
           "(objective 5) were not built. Evaluation (objective 6) covered the eye-state signal, low light and covering of the eyes, but not intoxication, false-positive rates on riders or "
           "road conditions, and is only partly done.")
    P.para("**Failure cases and limits.** Closed eyes are not intoxication, and open eyes do not prove alertness. The default threshold over-calls closed eyes; the gates are "
           "strict; a slow eye closure needs about " f"{A['min_closure_that_warns']:.1f} s to be reported; "
           " CEW classes come from different sources, so separation may be optimistic; the screens use a public-domain "
           "portrait and scripted scenarios, not riders; and the offline classifier's only report, from a synthetic file, is not evidence of performance.")
    P.para("**What this means for use.** Three consequences follow. First, the threshold must be set per rider: the shipped default errs towards calling eyes closed, and only calibration, "
           "not yet measured on people, addresses it. Second, availability matters as much as accuracy: a system that refuses in dim light is safe but not useful at dusk, so the sharpness "
           "and brightness gates need tuning on real webcam footage. Third, any prevention action such as an ignition interlock would act on this output, so its false-alarm rate on riders "
           "would have to be measured first; none of that has been done, and the prototype is for stationary demonstration only.")
    P.para("**Threats to validity.** Each measurement comes from one machine and one configuration. CEW images are small, from two sources, and show mostly frontal faces; the degradations "
           "are synthetic and applied to still images; the scripted streams assume the EAR values and blink statistics written into the generator; and the best thresholds were chosen "
           "on the same images they describe. None of these were checked on motorcyclists, helmets, visors, night riding, vibration, different skin tones or glasses, so the results bound "
           "the signal and the software, not a rider's safety.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para("Smart Rider turns a webcam into an explainable warning of possible drowsiness or impairment and is honest about what it cannot do. Against the six batch objectives, "
           "real-time face and landmark capture and continuous inference with an alert were achieved; impairment cues were measured only in part (no gaze); and the "
           "deep-learning classifier and the prevention action were not built. The key finding is that the eye signal separates open from closed eyes well (AUC "
           f"{geo['auc_ear_closed_vs_open']:.2f}) but that its default threshold and strict gates, not the rules, limit practical use. Limitations are the absence of intoxication data, of a rider "
           "study and of validation under helmets and visors, and a stationary-only prototype. Future work: collect a consented sober and intoxicated video dataset and train and test "
           "on held-out subjects; add gaze and temporal features; tune thresholds on separate validation subjects; run an in-vehicle trial with helmets, visors and vibration; and connect "
           "a prevention action such as an ignition interlock or a trusted-contact alert.")

    P.references()
    P.save(path)
    return path, len(P.order)


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "19.IEEE_Paper.docx")))
