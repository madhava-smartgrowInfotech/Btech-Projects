"""Chapter 8: Results and output screens. Every number is read from experiments/*/metrics.json at build time."""

import os
import sqlite3
import sys

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F

FRAME_KEY = "POST frame (real face JPEG 640x480, monitoring on)"


def _shot(name, caption, width=5.6):
    p = F.shot_view(name)
    return FIG(p, caption, F.shot_w(p, width))


def _latency_row(fps, closure):
    for r in (F.RULES or {}).get("closure_latency", []):
        if r["fps"] == fps and r["closure_s"] == closure:
            return r
    return {}


def analysis():
    """Derived statements used in prose, the decks and the paper (computed, never typed)."""
    out = {}
    cew, geo, rules = F.CEW, F.GEO, F.RULES
    if geo:
        d = geo["default_threshold_0.21"]
        b = geo["best_threshold_in_sample_youden"]
        out.update(
            geo_default=d, geo_best=b, geo_auc=geo["auc_ear_closed_vs_open"],
            default_false_closed_rate=d["fp"] / (d["fp"] + d["tn"]),
            default_missed_closed_rate=d["fn"] / (d["fn"] + d["tp"]),
        )
        out["weak"] = (f"the default threshold of 0.21 labels {d['fp']} of {d['fp'] + d['tn']:,} open eyes ({F.pct(d['fp'] / (d['fp'] + d['tn']))}) as closed, "
                       f"while a threshold of {b['threshold']:.2f} would have mislabelled {b['fp']} ({F.pct(b['fp'] / (b['fp'] + b['tn']))})")
    if cew:
        out.update(gated=cew["default_threshold_0.21"], coverage=cew["coverage"], gated_auc=cew["auc_ear_closed_vs_open"],
                   e2e_accuracy=cew["end_to_end_accuracy_unassessed_counted_wrong"])
    if rules:
        warned = [r["closure_s"] for r in rules["closure_latency"] if r["warned"] == r["runs"]]
        never = [r["closure_s"] for r in rules["closure_latency"] if r["warned"] == 0]
        out.update(min_closure_that_warns=min(warned) if warned else None, longest_closure_never_warns=max(never) if never else None,
                   warn_latency_15fps=_latency_row(15, 3.0).get("latency_mean_s"))
        out["false_alarm_cases"] = rules["false_alarm_on_blink_streams"]
    return out


def _scenario_rows():
    """Run the four scripted scenarios through the real rule engine (core.py) and report the final decision at t = 12 s."""
    if F.CODE not in sys.path:
        sys.path.insert(0, F.CODE)
    from core import RiskEngine, simulate, WARNING
    rows = []
    for sc in ("Normal", "Prolonged eye closure", "Missing face", "Poor lighting"):
        e = RiskEngine()
        first = None
        for i in range(121):
            t = i * 0.1
            d = e.update(simulate(sc, t, t))
            if d.state == WARNING and first is None:
                first = t
        rows.append([sc, d.state, d.reason, f"{d.ear:.2f}", f"{d.closure:.1f}", "-" if first is None else f"{first:.1f} s"])
    return rows


def _event_rows():
    """Real rows from data/events.sqlite3 (live-camera diagnostic of 23 Sep 2026), one per distinct state/reason."""
    path = os.path.join(F.CODE, "data", "events.sqlite3")
    if not os.path.exists(path):
        return []
    try:
        db = sqlite3.connect("file:" + path.replace("\\", "/") + "?mode=ro", uri=True)
        rows = db.execute("SELECT MIN(id), timestamp, source, state, quality, reason, ear, closure, roll FROM events "
                          "GROUP BY state, quality, reason ORDER BY MIN(id) LIMIT 4").fetchall()
        db.close()
    except sqlite3.Error:
        return []
    return [[str(r[0]), r[1][:19].replace("T", " "), r[2], r[3], r[4], r[5], f"{r[6]:.3f}", f"{r[7]:.1f}", f"{r[8]:.1f}"] for r in rows]


def blocks():
    cew, geo, rob, rules = F.CEW or {}, F.GEO or {}, F.ROB or {}, F.RULES or {}
    A = analysis()
    gd = cew.get("default_threshold_0.21", {})
    gb = cew.get("best_threshold_in_sample_youden", {})
    d = geo.get("default_threshold_0.21", {})
    b = geo.get("best_threshold_in_sample_youden", {})
    bc = cew.get("by_class", {})
    vl = cew.get("latency_ms_vision_process_640x480", {})
    api = F.API_LAT or {}
    fr = api.get(FRAME_KEY, {})
    fa = rules.get("false_alarm_on_blink_streams", [])
    sweep = rules.get("parameter_sweep", [])
    oth = rules.get("other_rules", {})

    out = [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS")]

    # ------------------------------------------------------------------ 8.1 screens
    out += [
        H2("8.1 Output screens"),
        P("The screens below are captures of the running web application at 1440 x 900 pixels (phone-width captures are in Appendix C), made by `scripts/capture_screens.py` with the demo account. "
          "Screen numbers in the text (for example \"screen 06\") are the file numbers in `docs/screenshots/`. Simulation screens show scripted measurements and are labelled SIMULATION on the "
          "page; the live-camera screens use Chromium's fake webcam, which plays a looping video of one public-domain portrait, because no rider was available to the capture script. The history screen "
          "therefore holds both simulated and camera events, and the research screen holds a synthetic file, as its banner says."),
        _shot("03_login.png", "Screen 03: sign-in page with the demo account shown"),
        _shot("07_monitor_idle.png", "Screen 07: monitor before any source is chosen; the disclaimer is always visible in the sidebar"),
        _shot("04_monitor_simulation_warning.png", "Screen 04: scripted \"Prolonged eye closure\" scenario; the warning *Possible impairment or drowsiness* is shown with its reason (continuous closure 4.9 s), "
                                                   "and the SIMULATION label marks the data as scripted"),
        _shot("05_monitor_calibrating.png", "Screen 05: personal calibration in progress on the camera path (19 usable of 19 frames, 4 s of the 8-15 s window); monitoring is stopped meanwhile and the "
                                            "state is *Unable to assess*"),
        _shot("06_monitor_camera_normal.png", "Screen 06: live camera path after calibration; green dots mark the six points of each eye, the verdict is *Normal*, EAR 0.254, calibrated threshold 0.183, head roll 2.5 degrees"),
        _shot("15_monitor_light.png", "Screen 15: the monitor in the light theme"),
        _shot("08_history.png", "Screen 08: event history with the EAR chart (live camera against simulation), counts, filters, search and CSV export; 34 events at the time of capture"),
        _shot("10_thresholds.png", "Screen 10: the six rule thresholds with their bounds; the badge shows that the threshold came from calibration"),
        _shot("09_thresholds_validation.png", "Screen 09: an out-of-range closure value (9 s) is refused with the message \"Must be between 0.5 and 5\"; the toast reports an earlier CSV export"),
        _shot("11_research_empty.png", "Screen 11: the research screen before any data is supplied; the status is *Model not trained*"),
        _shot("12_research_report.png", "Screen 12: offline evaluation of the **synthetic** demonstration file. The 100 % precision and recall come from a generated file in which the two classes are "
                                        "separable by construction; they show that the pipeline runs and are not a performance result"),
        _shot("13_about.png", "Screen 13: pipeline overview and limitations on the \"How it works\" page"),
        _shot("14_about_formulas.png", "Screen 14: formulas, warning rules and default values on the \"How it works\" page"),
    ]

    # ------------------------------------------------------------------ 8.2 rule engine
    cl = [(r["closure_s"], r) for r in rules.get("closure_latency", []) if r["fps"] == 15]
    cl_rows = [[f"{c:.1f} s", f"{r['warned']} / {r['runs']}", "-" if r["latency_mean_s"] is None else f"{r['latency_mean_s']:.2f} s"] for c, r in cl]
    fa_rows = [[r["case"], f"{r['sessions_with_warning']} / {r['sessions']}", f"{r['alerts_per_hour']:.2f}"] for r in fa]
    sw_rows = [[f"{r['closure_seconds']:.1f}", f"{r['persistence_seconds']:.1f}", F.pct(r["detect_3s_closure_rate"], 0), f"{r['alerts_per_hour_with_10pct_slow_blinks']:.2f}"] for r in sweep]
    out += [
        H2("8.2 Behaviour of the rule engine on scripted streams"),
        P("The decision logic was characterised with `scripts/measure_rules.py`, which generates seeded measurement streams (open-eye EAR about 0.30, closed about 0.12) and feeds them to the real "
          "`RiskEngine`. These streams are scripted, not recordings of people, so they show how the rules behave, not how riders behave. All results below use the default settings unless a sweep is stated."),
        H3("Closure length against warning"),
        P(f"Each closure was inserted into a quiet stream 6 s after the start and repeated 30 times at 10, 15 and 30 frames per second. At 15 frames per second the outcome is the same for every run "
          f"(table below): closures of up to {A.get('longest_closure_never_warns', 0):.1f} s never produce a warning, and closures of {A.get('min_closure_that_warns', 0):.1f} s or longer always do. "
          f"The warning appears {A.get('warn_latency_15fps', 0):.2f} s after the eyes close ({_latency_row(30, 3.0).get('latency_mean_s', 0):.2f} s at 30 frames per second): the 1.5 s closure rule plus 1.0 s of persistence plus the lag of the three-sample median. "
          "**A rider whose eyes close for two seconds and then reopen is never warned**; this is a design consequence of persistence, and it is the main sensitivity limit of the default rules."),
        TAB("Closure duration against warning (15 frames/s, 30 runs each)", ["Closure", "Runs that warned", "Mean latency from closure onset"], cl_rows,
            widths=[1.6, 1.8, 2.4], size=10, align=["c", "c", "c"]),
        FIG(F.fig("closure_vs_warning.png"), "Share of runs that warned against closure duration at 10, 15 and 30 frames per second", 5.2),
        H3("False warnings on blink streams"),
        P("Normal-looking streams (180 s each, 15 frames per second, 300 sessions per case) were generated with blinks of 0.1 to 0.4 s and counted for warnings. Blinks never warned, even at 35 per minute or with noisy EAR. "
          "Warnings appeared only when 20 % of the blinks were made unnaturally slow (0.8 to 1.3 s)."),
        TAB("Warnings on generated blink streams (defaults)", ["Stream", "Sessions with a warning", "Alerts per hour"], fa_rows, widths=[3.6, 1.6, 1.1], size=10, align=["l", "c", "c"]),
        H3("Parameter trade-off"),
        P("Closure time and persistence were varied together. The sweep shows that sensitivity and false alerts pull in opposite directions, and that the sum of closure and persistence is what matters: "
          "any setting whose sum exceeds the 3 s test closure misses it entirely. The defaults (1.5 s and 1.0 s) detect the 3 s closure and, on streams with 10 % slow blinks, produce no alerts, while a "
          "faster setting (1.0 s and 0.5 s) detects it too but raises 3.0 alerts per hour."),
        TAB("Closure and persistence against detection and false alerts", ["Closure (s)", "Persistence (s)", "3 s closure detected", "Alerts per hour (10 % slow blinks)"], sw_rows,
            widths=[1.2, 1.3, 1.6, 2.2], size=9.5, align=["c", "c", "c", "c"]),
        FIG(F.fig("parameter_tradeoff.png"), "Alerts per hour against the closure setting for three persistence values", 5.0),
        H3("Other rules"),
        B(f"**Closed-fraction rule.** Closures of 0.9 s every 1.5 s (60 % closed, no single long closure) produce a warning {oth.get('closed_fraction_rule', {}).get('first_warning_after_onset_s', 0):.1f} s after onset "
          f"with the reason \"{oth.get('closed_fraction_rule', {}).get('reason_at_warning', '')}\"; it needs at least 8 s of history, so it reacts slowly.",
          f"**Head-tilt rule.** A 30 degree roll with an EAR of 0.19 warns after {oth.get('tilt_rule', {}).get('first_warning_after_onset_s', 0):.2f} s; the same roll with open eyes never warns "
          f"({'confirmed' if oth.get('tilt_alone_warns') is False else 'not confirmed'}).",
          f"**Warm-up and recovery.** The first *Normal* appears {oth.get('warmup_first_normal_s', 0):.1f} s after the start, and {oth.get('recovery_after_signal_loss_first_normal_s', 0):.2f} s after a signal loss."),
    ]

    # ------------------------------------------------------------------ 8.3 setup for vision
    out += [
        H2("8.3 Experimental setup for the eye-state measurement"),
        P(f"The only component that can be measured on public data is the one that turns a face image into an EAR and decides whether the eye is closed. It was evaluated on the Closed Eyes in the Wild (CEW) "
          f"dataset {n(12)}: {cew.get('closed_images', 1192):,} faces with both eyes closed (collected from the Internet) and {cew.get('open_images', 1231):,} faces with open eyes (from LFW {n(13)}), supplied "
          "as 100 x 100 pixel warped crops. Each crop was enlarged to 480 x 480 pixels and centred on a 640 x 480 canvas, the size of the application's camera frames, and passed through the shipped "
          "`Vision.process` (MediaPipe Face Landmarker, quality gates, six-point EAR). The dataset is not part of the repository."),
        TAB("Protocol of the eye-state measurement", ["Item", "Value"], [
            ["Data", f"CEW, {cew.get('images_total', 2423):,} still images: {cew.get('closed_images', 1192):,} closed, {cew.get('open_images', 1231):,} open"],
            ["Pipeline A (as shipped)", "`Vision.process` with all quality gates; only assessed (*Good*) images are classified"],
            ["Pipeline B (geometry only)", "Same landmarks and `eye_aspect_ratio`, first detected face, no gates: separates \"is EAR informative\" from \"did the gates let the image through\""],
            ["Decision rule", "Closed if EAR is below the threshold (default 0.21); positive class = closed"],
            ["Training", "None: there is no learned model; the threshold is a fixed engineering default"],
            ["Hardware", f"{F.HW['cpu']}, {F.HW['ram']}, CPU only, Python {F.HW['python']}, MediaPipe {F.HW['mediapipe']}"],
        ], widths=[1.6, 4.7], size=10),
    ]

    # ------------------------------------------------------------------ 8.4 results
    sw = [s for s in geo.get("threshold_sweep", []) if s["threshold"] in (0.15, 0.17, 0.19, 0.21, 0.23, 0.25, 0.28)]
    sw_rows2 = [[f"{s['threshold']:.2f}", F.pct(s["accuracy"]), F.pct(s["recall"]), F.pct(s["specificity"])] for s in sw]
    out += [
        H2("8.4 Eye-state results on public data"),
        P(f"**Pipeline A (as shipped).** Only {cew.get('assessed_good', 0):,} of {cew.get('images_total', 0):,} images ({F.pct(cew.get('coverage', 0))}) pass the quality gates "
          f"(closed {F.pct(bc.get('closed', {}).get('coverage', 0))}, open {F.pct(bc.get('open', {}).get('coverage', 0))}). The main reason is the sharpness gate: a 100-pixel crop enlarged 4.8 times is soft, and "
          f"{bc.get('closed', {}).get('quality_breakdown', {}).get('Blurred or hidden eyes', 0) + bc.get('open', {}).get('quality_breakdown', {}).get('Blurred or hidden eyes', 0):,} images were refused as "
          "\"Blurred or hidden eyes\"; a further "
          f"{bc.get('closed', {}).get('quality_breakdown', {}).get('Multiple faces', 0) + bc.get('open', {}).get('quality_breakdown', {}).get('Multiple faces', 0)} were refused because a second face was detected. "
          f"If every refused image is counted as an error, end-to-end accuracy is only {F.pct(cew.get('end_to_end_accuracy_unassessed_counted_wrong', 0))}. This says more about the low-resolution test images than about webcam frames, but it "
          "also shows how strict the gates are. Among the assessed images the default threshold gives:"),
        TAB("Pipeline A: assessed images, threshold 0.21", ["Measure", "Value"], [
            ["True closed / false open (FN)", f"{gd.get('tp', 0)} / {gd.get('fn', 0)}"], ["True open / false closed (FP)", f"{gd.get('tn', 0)} / {gd.get('fp', 0)}"],
            ["Accuracy", F.pct(gd.get("accuracy", 0), 2)], ["Precision (closed)", F.pct(gd.get("precision", 0), 2)], ["Recall (closed)", F.pct(gd.get("recall", 0), 2)],
            ["Specificity (open)", F.pct(gd.get("specificity", 0), 2)], ["F1", F.pct(gd.get("f1", 0), 2)], ["ROC AUC of EAR", f"{cew.get('auc_ear_closed_vs_open', 0):.3f}"],
            ["Mean EAR, closed / open", f"{bc.get('closed', {}).get('ear_mean', 0):.3f} / {bc.get('open', {}).get('ear_mean', 0):.3f}"],
        ], widths=[3.6, 2.0], size=10.5),
        P(f"**Pipeline B (geometry only).** Without the gates a face is found in {geo.get('face_found', 0):,} of {geo.get('images_total', 0):,} images (closed {geo.get('closed_found', 0):,}, open {geo.get('open_found', 0):,}). "
          f"At the default threshold the result is accuracy {F.pct(d.get('accuracy', 0))}, recall of closed eyes {F.pct(d.get('recall', 0))}, specificity {F.pct(d.get('specificity', 0))}, precision {F.pct(d.get('precision', 0))} "
          f"and F1 {F.pct(d.get('f1', 0))}, with an AUC of {geo.get('auc_ear_closed_vs_open', 0):.3f}. The mean EAR is {geo.get('ear_mean_closed', 0):.3f} for closed and {geo.get('ear_mean_open', 0):.3f} for open eyes, "
          "so EAR separates the two states well; the errors come from where the threshold is set."),
        FIG(F.fig("ear_histogram.png"), "Distribution of EAR for closed and open eyes among the assessed CEW images, with the default threshold", 5.2),
        FIG(F.fig("landmark_examples.png"), "Six-point eye landmarks (green dots) and the resulting EAR on open (top) and closed (bottom) CEW faces that passed the quality gates", 5.2),
        FIG(F.fig("roc.png"), "ROC curve of EAR as a closed-eye score on the assessed CEW images", 4.6),
        H3("Threshold analysis"),
        P(f"The sweep below (pipeline B) shows the cost of the conservative default. Raising the threshold only adds closed-eye recall, but specificity falls quickly: at 0.21 about {F.pct(A.get('default_false_closed_rate', 0))} of open eyes "
          f"are called closed. The in-sample best threshold, {b.get('threshold', 0):.2f}, reaches accuracy {F.pct(b.get('accuracy', 0))} (recall {F.pct(b.get('recall', 0))}, specificity {F.pct(b.get('specificity', 0))}); "
          f"the same threshold is also best for pipeline A ({F.pct(gb.get('accuracy', 0))}). It was chosen on the test images themselves, so it is an indication and not a validated setting. In the application, "
          "calibration replaces the fixed 0.21 by 0.72 times the rider's own median open-eye EAR, which is the intended remedy: the calibrated value in screen 06 is 0.183. Whether calibration is better than a fixed 0.17 "
          "could not be measured, because the CEW images do not contain several images of the same person."),
        TAB("Threshold sweep, pipeline B", ["Threshold", "Accuracy", "Closed recall", "Open specificity"], sw_rows2, widths=[1.2, 1.3, 1.4, 1.5], size=10, align=["c", "c", "c", "c"]),
        FIG(F.fig("threshold_sweep.png"), "Accuracy, closed-eye recall and open-eye specificity against the EAR threshold (pipeline B)", 5.2),
    ]

    # ------------------------------------------------------------------ 8.5 robustness
    conds = {c["condition"]: c for c in rob.get("conditions", [])}

    def g(name):
        c = conds.get(name, {})
        return F.pct(c.get("good_rate", 0), 1)

    out += [
        H2("8.5 Behaviour under degraded conditions"),
        P(f"Objective 6 asks for performance under low light and partial occlusion. The measurement in Section 7.6 degraded {rob.get('n_images', 272)} open-eye faces in software. The gates refuse when the picture "
          f"is dark (brightness x0.25 and below: {g('brightness x0.25')} assessed), blurred ({g('Gaussian blur sigma 2 px')}), hidden behind opaque sunglasses ({g('opaque sunglasses over both eyes')}) or when one eye is covered "
          f"({g('one eye covered')}); that is the intended safe failure. They pass most images with noise ({g('Gaussian noise sd 20')}), a lower-face mask ({g('lower face masked')}) or tinted lenses "
          f"({g('tinted lenses (55% dark)')}). Two findings are unfavourable. Halving the brightness (x0.50) already blocks assessment ({g('brightness x0.50')} assessed, almost all refused by the sharpness gate, because "
          "scaling intensity scales the Laplacian variance by the square of the factor), so the system is unavailable in dim but still visible light. And two images in the sunglasses test slipped through the gates, "
          "one of them with a false closed reading, which confirms the README's warning that the gates are heuristics and not a proof of occlusion detection."),
    ]

    # ------------------------------------------------------------------ 8.6 speed
    out += [
        H2("8.6 Speed"),
        P(f"`Vision.process` takes {vl.get('mean', 0):.1f} ms on average on a 640 x 480 frame (median {vl.get('p50', 0):.1f} ms, 95th percentile {vl.get('p95', 0):.1f} ms) on the CPU. Through the HTTP API a camera frame "
          f"takes {fr.get('p50_ms', 0):.1f} ms at the median and {fr.get('p95_ms', 0):.1f} ms at the 95th percentile (Section 7.7), about {1000 / fr.get('p50_ms', 31):.0f} frames per second for one session, so the "
          "prototype is not limited by computation on this laptop."),
    ]

    # ------------------------------------------------------------------ 8.7 base paper
    out += [
        H2("8.7 Comparison with the base paper"),
        P(f"The base paper {n(1)} and this project differ in target, method, data and hardware, so the table is context and not a ranking. The paper's figures are taken from its own text; those for this project are "
          "from Sections 8.2 to 8.6."),
        TAB("Base paper and this project", ["Aspect", "Base paper (Feng and Li)", "This project"], [
            ["Target state", "Drowsiness, fatigue and distraction", "A drowsiness-type impairment indicator; **not** alcohol detection"],
            ["Eye feature", "EAR-4 (four upper-lid points) compared with six-point EAR", "Conventional six-point EAR"],
            ["Decision", "Fuzzy belief rule-based inference fusing EAR, head pose and voice", "Transparent if-then duration rules on EAR, closed fraction and roll"],
            ["Voice interface", "Whisper-tiny wake words and commands", "None"],
            ["Calibration", "Personalised adaptive threshold from more than 300 frames", "8-15 s, threshold = 0.72 x median EAR"],
            ["Data", "NTHU-DDD: 4 subjects, 65,834 frames (29,804 open, 36,030 closed), 80/20 split; Random Forest and XGBoost", f"CEW: {cew.get('images_total', 2423):,} still faces for the EAR component only; no rider data; no training"],
            ["Reported eye-state metric", "EAR-4 recall 0.894, F1 0.845 (Subject 2, Random Forest); six-point EAR 0.856 and 0.813", f"Six-point EAR at 0.21: recall {F.f3(d.get('recall', 0))}, specificity {F.f3(d.get('specificity', 0))}, F1 {F.f3(d.get('f1', 0))} (CEW, pipeline B)"],
            ["Hardware and speed", "NVIDIA Jetson Orin Nano 8 GB, 25 frames per second", f"Laptop CPU (i5-12500), about {1000 / fr.get('p50_ms', 31):.0f} frames per second through the API"],
            ["Deliverable", "Embedded driver monitoring and assistance system", "Stationary web and desktop demonstration prototype"],
        ], widths=[1.3, 2.6, 2.4], size=9),
        P("Three points should be stated plainly. First, the metrics are not comparable: the base paper classifies frames of four drivers from a video dataset with trained models, whereas this project applies a "
          "fixed threshold to still faces of different people. Second, the base paper's six-point recall of 0.856 is lower than the 0.992 measured here, but the datasets, the class mix and the protocol differ, so "
          "no conclusion about which method is better can be drawn. Third, the project does not reproduce the base paper's EAR-4, voice interface or fuzzy belief engine."),
    ]

    # ------------------------------------------------------------------ 8.8 samples
    ev = _event_rows()
    out += [
        H2("8.8 Sample inputs and outputs"),
        P("**Scripted scenarios through the real rule engine.** The table gives the decision of `RiskEngine` after 12 s of each scenario in `core.simulate`, together with the time of the first warning. "
          "These are deterministic demonstrations, not predictions."),
        TAB("Decisions for the four simulation scenarios", ["Scenario", "Verdict after 12 s", "Reason", "EAR", "Closure", "First warning"], _scenario_rows(),
            widths=[1.2, 1.3, 1.9, 0.4, 0.6, 0.8], size=8.5, align=["l", "l", "l", "c", "c", "c"]),
        P(f"**Camera frames through the API.** A real face frame ({api.get('frame_jpeg_bytes', 0):,} bytes) was posted {fr.get('n', 0)} times in a row with monitoring on. All frames were assessed as quality *Good*; "
          f"{api.get('frame_states', {}).get('Unable to assess', 0)} of the verdicts were *Unable to assess* (the two-second warm-up at about 30 frames per second) and {api.get('frame_states', {}).get('Normal', 0)} were *Normal*, "
          "with no warning, as expected for an open-eyed face."),
    ]
    if ev:
        out += [
            P("**Logged events.** The events table of the repository holds a short live-camera diagnostic recorded on 23 September 2026. One row per distinct outcome is shown; the camera was pointed at a "
              "real scene and the labels are those the quality gates produced, including *Multiple faces*."),
            TAB("Rows from `data/events.sqlite3`", ["id", "UTC time", "Source", "State", "Quality", "Reason", "EAR", "Closure", "Roll"], ev,
                widths=[0.3, 1.0, 0.7, 0.8, 0.7, 1.2, 0.4, 0.5, 0.4], size=7.5, align=["c", "l", "l", "l", "l", "l", "c", "c", "c"]),
        ]

    # ------------------------------------------------------------------ 8.9 success / failure
    out += [
        H2("8.9 Success and failure analysis"),
        P(f"**Where it works.** Closed eyes are found reliably: recall is {F.pct(d.get('recall', 0))} at the default threshold, and the EAR distributions of closed and open eyes barely overlap (AUC {geo.get('auc_ear_closed_vs_open', 0):.3f}). "
          "The rule engine ignores normal blinks entirely, warns on sustained closure with a stated reason, and the gates refuse to guess in darkness, blur and with covered eyes. The application runs at about 30 frames per second "
          "on a laptop CPU, and all 54 automated checks pass."),
        P("**Where it fails.**"),
        B(f"*False closed readings.* {A.get('weak', '')}. People with narrow eyes, or looking down, have a low open-eye EAR; this is why calibration exists.",
          f"*Availability.* Only {F.pct(cew.get('coverage', 0))} of the low-resolution test images pass the gates, and dim light (half brightness) already blocks assessment.",
          f"*Slow onset.* Closures shorter than {A.get('min_closure_that_warns', 0):.1f} s never warn, so a rider who nods off for two seconds is not warned.",
          "*Spurious second face.* About one in ten test images was refused because a second face was detected, even though each crop shows one face.",
          "*Occlusion gaps.* A few sunglasses images passed the gates, one of them with a false closed reading.",
          "*Not alcohol.* Closed eyes and low EAR have many causes; open eyes do not prove alertness. No result in this report relates to intoxication."),
        H2("8.10 Limitations of the results"),
        B("One public still-image dataset, with closed and open classes taken from different sources; separation may be optimistic.",
          "No video, no blink dynamics and no head motion in the eye-state measurement; the rule engine was exercised only with scripted streams.",
          "The best threshold is chosen in-sample; there is no held-out validation of a tuned setting.",
          "Tracking state in MediaPipe's video mode makes unrelated stills depend on the previous image: coverage figures carry about two percentage points of noise.",
          "No intoxicated person, no rider, helmet, visor, vibration or night condition, and no demographic analysis.",
          "All results come from one machine and one run per measurement."),
        H2("8.11 Objectives against outcomes"),
    ]
    status = [
        ["1. Capture driver facial video with a webcam and detect the face and landmarks in real time", "**Achieved**", "MediaPipe landmarks with six-point eye geometry; 31 ms median per frame (Sections 7.7, 8.6)"],
        ["2. Extract impairment cues: eye closure ratio, blink frequency, gaze deviation, head movement", "**Partly achieved**", "EAR, closure time, closed fraction, blink rate (display only) and image-plane head roll are measured; **gaze deviation is not**"],
        ["3. Train a deep-learning classifier to separate a sober driver from an intoxicated one", "**Not achieved**", "No intoxication dataset was available; live decisions use explainable rules; the offline nearest-centroid pipeline has only been run on a synthetic file"],
        ["4. Run inference continuously and alert when the impairment score crosses a threshold", "**Achieved**", "Rule engine with three outputs, on-screen warning and optional bell with cooldown (Section 8.2); the score is a drowsiness-type indicator, not an alcohol score"],
        ["5. Integrate a prevention action (ignition warning, notification to a registered contact)", "**Not achieved**", "The application only shows a warning and plays a bell; it never controls ignition and sends no notification"],
        ["6. Evaluate accuracy, false-positive rate, low light and partial occlusion", "**Partly achieved**", f"Eye-state accuracy and false-closed rate on CEW and gate behaviour under degradation (Sections 8.4, 8.5); no intoxication accuracy and no rider study"],
    ]
    out += [TAB("Objectives of the batch and their outcome", ["Objective", "Outcome", "Evidence"], status, widths=[2.6, 0.9, 2.8], size=9.5)]
    return out
