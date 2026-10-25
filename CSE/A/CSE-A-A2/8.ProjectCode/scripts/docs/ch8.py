"""Chapter 8: Results and output screens (ResQAI). Every number is read from facts.py (experiments/resqai_eval/*.json)."""

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, PAIR, TAB
from .refs import CITE as R

SH = F.shot


def c(*keys):
    return "[" + ", ".join(str(R[k]) for k in keys) + "]"


def S(name, caption, base=5.6, max_h=3.9):
    """Screenshot figure with a width that keeps the picture on one page."""
    return FIG(SH(name), caption, F.shot_w(SH(name), base, max_h))


def _cap(name, text):
    return (SH(name), text)


CAPTIONS = {
    "01_landing_light.png": "Landing page, light theme: the pitch 'Detect. Rate. Dispatch.', the live status tiles (API online, model trained ML, countdown 15 s) and the entry buttons.",
    "02_landing_dark.png": "Landing page, dark theme (the theme switch at the top right is remembered in the browser).",
    "03_landing_how_it_works.png": "'How it works' section of the landing page (Detect, Rate, Confirm, Dispatch). The tiles at the bottom (4 severity levels, 11 sensor features, 15 seconds to cancel, 10 hospitals listed) are captured after their count-up animation has finished.",
    "04_login_light.png": "Sign-in form. The monitor, manual override and response screens are reachable only after signing in.",
    "05_login_error_dark.png": "Sign-in with a wrong password (dark theme): the form reports 'Incorrect email or password.' without saying which of the two was wrong.",
    "06_register_dark.png": "Create-account form (name, e-mail, password and confirmation).",
    "07_monitor_empty.png": "Live monitor before any reading: the five scenario buttons, the live-monitoring switch, and empty result and trace panels.",
    "08_monitor_live.png": "Live monitor after normal driving: 'No accident', severity None, accident probability 0 %, with the sensor trace of acceleration and rotation magnitude.",
    "09_alert_countdown.png": "Confirmation dialog 'Possible accident detected' after a Severe crash: 100 % probability, 11 seconds left, the buttons 'I'm fine, cancel' and 'Send alert now', and the note that Escape cancels.",
    "10_alert_dispatched.png": "Dialog 'Emergency alert dispatched': alert id, severity, device location, the drafted message with its map link and nearest hospital, and the statement that the message is not sent to real responders.",
    "11_response_dispatched.png": "Emergency response screen after the dispatch: map with the accident and hospital markers, dispatch summary (id, severity, location source, nearest hospital) and the call button.",
    "12_manual_result.png": "Manual override with acc_x 32, acc_y 18 m/s2, speed change -45 km/h and jerk 40: derived magnitude 38.00 m/s2, result Moderate; the event log below records the earlier alerts.",
    "13_monitor_dark.png": "Live monitor in the dark theme after a normal reading.",
    "14_response_directory_dark.png": "Response map before any alert (dark theme): the ten-hospital directory around the default location and the emergency numbers 108, 112 and 103.",
    "15_manual_form.png": "Top of the manual override screen: the input fields for the accelerometer, gyroscope, speed and jerk, with the magnitude derived from them.",
    "16_monitor_minor_logged.png": "A Minor crash on the live monitor: 'Accident detected', severity Minor, 100 % probability; it is written to the event log and does not open the countdown.",
    "17_monitor_moderate_cancelled.png": "A Moderate crash after the occupant pressed 'I'm fine, cancel': the event log reads 'User confirmed they are OK. Alert cancelled.'",
    "18_not_found.png": "The 404 page shown for an unknown route.",
}
MAIN_SCREENS = ["01_landing_light.png", "04_login_light.png", "07_monitor_empty.png", "08_monitor_live.png", "09_alert_countdown.png", "10_alert_dispatched.png",
                "11_response_dispatched.png", "12_manual_result.png", "16_monitor_minor_logged.png", "17_monitor_moderate_cancelled.png"]
# screens placed in Appendix C in the full report (every screenshot appears exactly once in the report)
APPENDIX_C = [n for n in CAPTIONS if n not in MAIN_SCREENS]


def _pairs(names, width=2.8):
    return [PAIR([_cap(n, CAPTIONS[n]) for n in names[i:i + 2]], width) for i in range(0, len(names), 2)]


def screens():
    intro = ("The screens below were captured from the running application with a Playwright script (Chrome, 1440 by 900 pixels, Flask backend on port 8302, React front end on port 5302, demo account). "
             "Every result on them was produced by the real models: the readings come from the built-in simulator, which stands in for the phone, and the position is supplied by the browser (set to a point in Banjara Hills, Hyderabad, for the capture). "
             "Nothing was edited after capture.")
    if F.REPORT:
        return [H2("8.2 Output Screens"),
                P(intro + " The principal screens are shown here; the other captures (dark-theme landing and monitor, the landing page's how-it-works section, the wrong-password message, registration, the manual form, the response map before an alert, and the 404 page) are in Appendix C."),
                *_pairs(["01_landing_light.png", "04_login_light.png"]),
                *_pairs(["07_monitor_empty.png", "08_monitor_live.png"]),
                *_pairs(["09_alert_countdown.png", "10_alert_dispatched.png"]),
                *_pairs(["11_response_dispatched.png", "12_manual_result.png"]),
                *_pairs(["16_monitor_minor_logged.png", "17_monitor_moderate_cancelled.png"]),
                P("The sequence 08, 09, 10, 11 is the main flow of the system: a normal reading raises nothing; a Severe crash opens the countdown; pressing Send alert now (or letting the 15 seconds run out) composes the message; and the response screen shows where the accident is and which hospitals are nearest. "
                  "Screens 16 and 17 show the two outcomes that do not dispatch anything: a Minor crash, which is only logged, and a Moderate crash that the occupant cancels.")]
    out = [H2("8.2 Output Screens"), P(intro)]
    groups = [("Landing and sign-in", ["01_landing_light.png", "02_landing_dark.png", "03_landing_how_it_works.png", "04_login_light.png", "05_login_error_dark.png", "06_register_dark.png"]),
              ("Live monitor and confirmation", ["07_monitor_empty.png", "08_monitor_live.png", "16_monitor_minor_logged.png", "17_monitor_moderate_cancelled.png", "13_monitor_dark.png", "09_alert_countdown.png"]),
              ("Dispatch, response map and manual override", ["10_alert_dispatched.png", "11_response_dispatched.png", "14_response_directory_dark.png", "15_manual_form.png", "12_manual_result.png", "18_not_found.png"])]
    for title, names in groups:
        out.append(H3(title))
        for n in names:
            out.append(S(n, CAPTIONS[n], 5.0, 3.3))
    return out


# -------------------------------------------------------------------------------------------------- numbers
def _setup():
    e = F.M["environment"]
    kc = F.DS["kind_counts_test"]
    return [
        H2("8.1 Experimental Set-up"),
        P(f"All model results in this chapter are measured on {F.N_TEST:,} held-out events: the 20 % split of {F.N_TOTAL:,} synthetic sensor events that train_models.py generates with seed 42 and splits with a stratified random split. "
          f"The test part holds {kc['normal']:,} normal-driving, {kc['harsh_brake']} harsh-braking, {kc['minor_crash']} minor-crash, {kc['moderate_crash']} moderate-crash and {kc['severe_crash']} severe-crash events, that is {F.DET['confusion'][1][1]} accidents "
          f"({F.pct(F.DET['confusion'][1][1] / F.N_TEST)}) and {F.DET['confusion'][0][0]:,} non-accidents. The shipped models in models/*.pkl are evaluated, and a fresh retraining with the same seed is compared with them. "
          f"The measurements ran with Python {e['python']}, scikit-learn {e['sklearn']}, numpy {e['numpy']} and pandas {e['pandas']}, on one Intel Core i5-12500 with 15.7 GB of RAM and no GPU. "
          f"The pickles were written by scikit-learn 1.9.0 and loaded by {e['sklearn']}; the retrained models agree with them on {F.pct(F.RETRAIN['agreement_with_shipped_detector'], 2)} of the detector decisions and {F.pct(F.RETRAIN['agreement_with_shipped_severity'], 2)} of the severity decisions, so the version difference does not change a single answer."),
        P("The word 'real' in this chapter means that the number was measured by running the code; it does not mean that the data are real. There is no dataset of smartphone recordings of crashes in this project. "
          "The events are drawn from hand-written distributions that imitate normal driving, harsh braking and three grades of impact (Chapter 6), and the test events come from the same distributions as the training events. "
          "The scores that follow therefore measure how well the forests learn the generator, and they are an upper bound on what any real recording could achieve."),
    ]


def _detector():
    d = F.DET
    pk = F.SHIP["per_event_kind"]
    rows = [[k.replace("_", " "), v["n"], F.pct(v["predicted_accident_rate"]), f"{v['mean_accident_probability']:.4f}"] for k, v in pk.items()]
    sw = [[f"{r['threshold']:.2f}", f"{r['precision']:.4f}", f"{r['recall']:.4f}", f"{r['f1']:.4f}", r["false_positives"], r["false_negatives"]] for r in F.SWEEP]
    tn, fp = d["confusion"][0]
    fn, tp = d["confusion"][1]
    return [
        H2("8.3 Accident Detector"),
        P(f"On the {F.N_TEST:,} held-out events the detector makes no error: accuracy, precision, recall, F1 and ROC-AUC are all {d['accuracy']:.4f}, the confusion matrix is [[{tn}, {fp}], [{fn}, {tp}]], "
          f"and both the false-alarm rate and the miss rate are {F.pct(d['false_alarm_rate'])}. Its accuracy on the {F.N_TRAIN:,} training events is also {F.SHIP['detector_train_accuracy']:.4f}, so there is no gap between training and test. "
          "A perfect score on a test set is normally a warning sign, and here it is one: it comes from the way the data are built, not from a skilful model."),
        FIG(F.fig("f01_feature_separation.png"), "Why the detector cannot fail on this data: normal driving and harsh braking stay below 13.2 m/s2 of acceleration magnitude, every crash is above 15.3 m/s2.", 5.6),
        P(f"The left panel of the figure above shows the reason. The largest acceleration magnitude of any harsh-braking event in the 12,000 generated is {F.DS['class_overlap']['acc_magnitude']['harsh_brake'][1]} m/s2, the smallest of any crash is {F.DS['class_overlap']['acc_magnitude']['minor_crash'][0]} m/s2, "
          "and a gap lies between them. A single threshold at 15 m/s2 separates the two classes without an error, and Section 8.5 confirms that a rule with that threshold scores exactly as well as the random forest. "
          "The detector in this project is therefore easy by construction; its value in this chapter is that the full pipeline from reading to alert is exercised, not that 100 % tells us something about roads."),
        FIG(F.fig("f02_confusion_matrices.png"), "Confusion matrices of the shipped detector (left) and of the severity model after the detector gate (right), 2,400 test events.", 5.6),
        TAB("Detector behaviour by kind of event (shipped model, held-out events)", ["Event kind", "Events", "Flagged as accident", "Mean accident probability"], rows, widths=[1.7, 0.9, 1.6, 1.8], align=["l", "r", "r", "r"], size=10),
        P(f"The row that matters for the first objective is harsh braking: none of the {pk['harsh_brake']['n']} held-out braking events is flagged, and their mean accident probability is {pk['harsh_brake']['mean_accident_probability']:.4f}. "
          f"The weakest accident in the test set still receives an accident probability of {F.M['probability_separation']['min_proba_true_accident']:.2f}, and the strongest non-accident receives {F.M['probability_separation']['max_proba_true_non_accident']:.2f}, so the probabilities are well separated."),
        H3("8.3.1 Decision threshold"),
        P("The application uses the forest's own decision (equivalent to a probability threshold of 0.5). The table and figure below vary that threshold. Between 0.20 and 0.90 there is no error at all; at 0.10 and 0.05 a few false alarms appear (2 and 5), and at 0.95 two true accidents are missed. "
          "The operating point is not sensitive to the threshold on this data, which is again a sign of well-separated classes. On real recordings the choice would trade missed crashes against false alarms and would have to be set with a cost in mind: a missed crash can cost a life, a false alarm costs the occupant a few seconds, which is what the confirmation window is for."),
        TAB("Detector threshold sweep (shipped model)", ["Threshold", "Precision", "Recall", "F1", "False positives", "False negatives"], sw, widths=[0.9, 1.0, 1.0, 1.0, 1.2, 1.2], align=["c"] * 6, size=9.5),
        FIG(F.fig("f06_threshold_sweep.png"), "Precision and recall of the detector against the accident-probability threshold, with the number of errors.", 4.8),
    ]


def _severity():
    s = F.SEVM
    a = F.ALERT
    pc = s["per_class"]
    rows = [[k, f"{v['precision']:.4f}", f"{v['recall']:.4f}", f"{v['f1']:.4f}", v["support"]] for k, v in pc.items()]
    sd = F.SEEDS
    srows = [[r["seed"], f"{r['sev_accuracy']:.5f}", f"{r['sev_macro_f1']:.5f}", f"{r['alert_precision']:.4f}", f"{r['alert_recall']:.4f}", F.pct(r["alert_false_alarm"], 3)] for r in sd["rows"]]
    srows.append(["mean", f"{sd['mean']['sev_accuracy']:.5f}", f"{sd['mean']['sev_macro_f1']:.5f}", f"{sd['mean']['alert_precision']:.4f}", f"{sd['mean']['alert_recall']:.4f}", F.pct(sd["mean"]["alert_false_alarm"], 3)])
    srows.append(["SD", f"{sd['std']['sev_accuracy']:.5f}", f"{sd['std']['sev_macro_f1']:.5f}", f"{sd['std']['alert_precision']:.4f}", f"{sd['std']['alert_recall']:.4f}", F.pct(sd["std"]["alert_false_alarm"], 3)])
    ab = [[k, v["n_features"], f"{v['det_accuracy']:.4f}", f"{v['sev_accuracy']:.4f}", f"{v['sev_macro_f1']:.4f}"] for k, v in F.ABL.items()]
    imp = F.IMP
    top = lambda d, n=4: ", ".join(f"{k} ({v:.3f})" for k, v in sorted(d.items(), key=lambda kv: -kv[1])[:n])
    return [
        H2("8.4 Severity Predictor"),
        P(f"After the detector gate, as the application runs it, the severity model reaches accuracy {s['accuracy']:.5f} and macro-F1 {s['macro_f1']:.5f} on the {F.N_TEST:,} test events. "
          f"There is exactly one error ({s['errors']} of {F.N_TEST:,}): a Minor crash graded Moderate. It is a neighbouring class (Minor and Moderate are adjacent grades). "
          f"Per class, precision and recall are at least {min(min(v['precision'], v['recall']) for v in pc.values()):.4f}."),
        TAB("Severity per-class results (shipped model, after the gate)", ["Class", "Precision", "Recall", "F1", "Support"], rows, widths=[1.3, 1.2, 1.2, 1.2, 1.1], align=["l", "r", "r", "r", "r"], size=10),
        P(f"The decision that actually starts a countdown is whether the grade is Moderate or Severe. Treated as a two-class problem this decision has precision {a['precision']:.4f}, recall {a['recall']:.4f} and a false-alarm rate of {F.pct(a['false_alarm_rate'], 3)} "
          f"({a['confusion'][0][1]} false trigger in {a['confusion'][0][0] + a['confusion'][0][1]:,} events that should not trigger one). No Moderate or Severe event was missed. "
          "The one false trigger is the Minor crash that was graded Moderate: in the application it would have opened the countdown, and the occupant could have cancelled it."),
        H3("8.4.1 Repeatability over five seeds"),
        P("A single split can flatter a model, so the whole experiment was repeated five times, each time with a new dataset, a new split and newly trained forests (seeds 11, 22, 33, 44 and 55). "
          f"The detector scored accuracy 1.0000 in all five runs. The severity results varied only in the third decimal: accuracy {sd['mean']['sev_accuracy']:.5f} on average (SD {sd['std']['sev_accuracy']:.5f}, worst run {sd['min']['sev_accuracy']:.5f}) and macro-F1 {sd['mean']['sev_macro_f1']:.5f} (SD {sd['std']['sev_macro_f1']:.5f}, worst {sd['min']['sev_macro_f1']:.5f}). "
          f"The shipped model's single-split figures therefore sit within the spread of the five repeats, slightly above their mean."),
        TAB("Five-seed repeat (2,400 test events each)", ["Seed", "Severity accuracy", "Severity macro-F1", "Alert precision", "Alert recall", "Alert false-alarm"], srows, widths=[0.7, 1.2, 1.2, 1.1, 1.0, 1.2], align=["c", "r", "r", "r", "r", "r"], size=9.5),
        FIG(F.fig("f09_five_seeds.png"), "Severity accuracy, macro-F1 and alert-trigger recall in the five repeats.", 4.6),
        H3("8.4.2 Which features matter"),
        P(f"The detector relies on few features: by Gini importance the leaders are {top(imp['detector_gini'], 3)}; by permutation, shuffling acc_magnitude alone lowers the detector's F1 by {imp['detector_permutation_f1_drop']['acc_magnitude']:.3f} while shuffling any other single feature changes nothing, "
          "because the others carry the same information (jerk, gyroscope magnitude and speed change all rise with the impact). "
          f"The severity model uses more of the inputs: {top(imp['severity_gini'], 4)}; its permutation drops are largest for acc_magnitude ({imp['severity_permutation_macro_f1_drop']['acc_magnitude']:.3f}), speed_change ({imp['severity_permutation_macro_f1_drop']['speed_change']:.3f}) and speed_before ({imp['severity_permutation_macro_f1_drop']['speed_before']:.3f})."),
        FIG(F.fig("f04_feature_importance.png"), "Gini and permutation importance of the 11 features for the detector and the severity model.", 5.6),
        P("Retraining on feature subsets (table below) shows what can be removed. The gyroscope can be dropped without any change on this data, and speed and jerk each add a little to severity; acceleration alone detects every crash but grades severity less well "
          f"(accuracy {F.ABL['accelerometer only (x, y, z, magnitude)']['sev_accuracy']:.4f}, macro-F1 {F.ABL['accelerometer only (x, y, z, magnitude)']['sev_macro_f1']:.4f}), and the single feature acc_magnitude gives severity accuracy {F.ABL['acc_magnitude only']['sev_accuracy']:.4f}. "
          "That the gyroscope adds nothing is a property of the generator, in which rotation grows with impact exactly as acceleration does; on a real phone, rotation would help to separate a roll-over from a frontal impact."),
        TAB("Feature-group ablation (models retrained on each subset)", ["Features used", "N", "Detector accuracy", "Severity accuracy", "Severity macro-F1"], ab, widths=[2.6, 0.4, 1.1, 1.1, 1.1], align=["l", "c", "r", "r", "r"], size=9),
        FIG(F.fig("f10_ablation.png"), "Severity accuracy and macro-F1 for each feature group.", 5.0),
    ]


def _baselines():
    b = F.BASE
    keys = list(b)
    names = ["Rule-based fallback (acc_magnitude < 15 / 28 / 45)", "Logistic regression", "Decision tree (depth 10)", "HistGradientBoosting", "Random forest (ResQAI, retrained)"]
    rows = [[n, f"{b[k]['det_accuracy']:.4f}", f"{b[k]['det_f1']:.4f}", F.pct(b[k]["det_false_alarm"]), f"{b[k]['sev_accuracy']:.4f}", f"{b[k]['sev_macro_f1']:.4f}"] for n, k in zip(names, keys)]
    r0, rf = b[keys[0]], b[keys[-1]]
    return [
        H2("8.5 Comparison with Simpler Models"),
        P(f"To see what the random forests add, four other models were trained on the same split, with the same scaling and the same detector gate for severity. "
          f"All five detect crashes perfectly. The random forest and gradient boosting are the best on severity (accuracy {rf['sev_accuracy']:.4f} and {b[keys[3]]['sev_accuracy']:.4f}); the decision tree and logistic regression are close ({b[keys[2]]['sev_accuracy']:.4f} and {b[keys[1]]['sev_accuracy']:.4f}); "
          f"and the three-threshold rule on acceleration magnitude, which the application itself uses as a fallback, is clearly worse ({r0['sev_accuracy']:.4f} accuracy, {r0['sev_macro_f1']:.4f} macro-F1)."),
        TAB("Models on the same split (2,400 test events)", ["Model", "Detector accuracy", "Detector F1", "False-alarm", "Severity accuracy", "Severity macro-F1"], rows, widths=[2.3, 0.8, 0.8, 0.8, 0.9, 0.9], align=["l", "r", "r", "r", "r", "r"], size=9),
        FIG(F.fig("f03_baselines.png"), "Severity accuracy and macro-F1 of the random forest and four simpler models.", 5.2),
        P(f"The honest reading is twofold. For detection, the machine-learning model is not needed on this data: a single threshold does as well. For severity, the forest gains {F.pct(rf['sev_accuracy'] - r0['sev_accuracy'])} points of accuracy and {F.pct(rf['sev_macro_f1'] - r0['sev_macro_f1'])} points of macro-F1 over the rule, "
          "because the three severity bands overlap at their edges and the extra inputs (jerk, speed change, speed) resolve many of those cases. Gradient boosting would have been an equally good choice. "
          f"The random forest {c('breiman')} was kept because it is robust, needs no tuning, runs both models in about {F.INF['mean']:.0f} ms and was already in the shipped application."),
    ]


def _robust():
    nz = F.NOISE
    rows = [[f"{r['noise_sd_fraction_of_feature_sd']:.2f}", f"{r['det_accuracy']:.4f}", f"{r['det_f1']:.4f}", F.pct(r["det_false_alarm"]), F.pct(r["det_recall"]), f"{r['sev_accuracy']:.4f}", f"{r['sev_macro_f1']:.4f}"] for r in nz]
    po, sb = F.OOD["pothole"], F.OOD["speed_breaker"]
    return [
        H2("8.6 Robustness and Road-Surface Events"),
        P("Two tests go beyond the clean test split. The first adds Gaussian noise to the nine raw sensor channels of the test events; the standard deviation of the noise is a fraction of each feature's own standard deviation across the test set, and the magnitudes are recomputed afterwards. "
          "The shipped models were never trained on noisy readings."),
        TAB("Shipped models under added sensor noise", ["Noise (fraction of SD)", "Detector accuracy", "Detector F1", "False-alarm rate", "Detector recall", "Severity accuracy", "Severity macro-F1"], rows,
            widths=[1.0, 0.85, 0.8, 0.85, 0.8, 0.85, 0.85], align=["c", "r", "r", "r", "r", "r", "r"], size=9),
        FIG(F.fig("f05_noise_robustness.png"), "Detector F1, severity macro-F1 and false-alarm rate as noise grows from 0 to 100 % of each feature's SD.", 4.8),
        P(f"The models tolerate noise up to about one tenth of the natural spread: at 0.10 the detector is still perfect and severity macro-F1 is {nz[2]['sev_macro_f1']:.4f}. At 0.25 false alarms reach {F.pct(nz[3]['det_false_alarm'])} and at 0.50 they reach {F.pct(nz[4]['det_false_alarm'])}, "
          f"so a quarter of non-accident events would be flagged. At 1.00 the detector's accuracy ({F.pct(nz[5]['det_accuracy'])}) is below 50 %. Detector recall stays above {min(r['det_recall'] for r in nz):.3f} throughout: noise makes the system cry wolf, it does not make it miss crashes. "
          "A real phone is noisy (vibration, orientation, a loose mount), so a noise-aware retraining and a filter before the model would be necessary."),
        P(f"The second test asks the question that the second objective raises: what does the detector do with events that are neither crashes nor the harsh braking it was trained on? Two sets of 1,000 events each were constructed for this report, a pothole-like set (a vertical spike of 6 to 18 m/s2, almost no change of speed) and a speed-breaker-like set (a vertical rise of 3 to 9 m/s2 and a small slowing). "
          "They are our own construction and not recordings, and the parameters are in scripts/measure_metrics.py."),
        FIG(F.fig("f07_ood_probes.png"), "Share of events flagged as accident and share that start the 15-second alert, for trained and unseen kinds of event.", 5.0),
        P(f"The detector flags {F.pct(po['predicted_accident_rate'])} of the pothole-like events (mean accident probability {po['mean_accident_probability']:.2f}) and {F.pct(sb['predicted_accident_rate'])} of the speed-breaker-like events (mean probability {sb['mean_accident_probability']:.2f}): it behaves like a coin toss, because it has never seen a vertical-only spike. "
          f"None of them is graded Moderate or Severe ({F.pct(po['alert_trigger_rate'])} and {F.pct(sb['alert_trigger_rate'])} reach the countdown), so no alert would be raised, but the logged 'Accident detected' entries would be false. "
          "The objective of telling accidents from potholes and speed breakers is therefore met for hard braking and not demonstrated for the road-surface events. The fix is data, not tuning: such events must be recorded on real roads and added to training as their own class."),
    ]


SAMPLES = [
    # name, payload summary, derived acc magnitude, gyro magnitude, accident, severity, probability  (real calls to /api/predict, 2026-10-25)
    ["Calm driving", "acc (0.1, -0.2, 9.8), speed 40, change +0.5, jerk 0.3", "9.80", "0.11", "No", "None", "0.00"],
    ["Hard braking", "acc_x -4.5, speed 60, change -25, jerk 6", "10.79", "0.37", "No", "None", "0.00"],
    ["Minor-like impact", "acc (17, 8, 9.8), gyro about 1.1 each, change -22, jerk 20", "21.19", "1.91", "Yes", "Minor", "1.00"],
    ["Moderate impact (screen 12)", "acc (32, 18, 9.81), change -45, jerk 40", "38.00", "0.10", "Yes", "Moderate", "0.975"],
    ["Severe impact", "acc (55, 25, 10.5), gyro about 3 each, speed 90, change -70, jerk 62", "61.32", "5.24", "Yes", "Severe", "1.00"],
    ["Boundary case", "acc (22, 14, 9.8), gyro 2 each, change -30, jerk 28", "27.86", "3.46", "Yes", "Minor", "1.00"],
    ["Pothole-like (our probe)", "acc_z 21.8 (a 12 m/s2 vertical spike), change +1, jerk 12", "21.82", "0.67", "Yes", "Minor", "0.80"],
]


def _samples():
    me = F.SHIP["misclassified_examples"]
    ex = me[0]
    return [
        H2("8.7 Sample Inputs and Outputs"),
        P("The table below lists seven readings typed into /api/predict (the same payload the Manual override screen builds) and the answers returned by the shipped models on 2026-10-25. "
          "They are hand-picked to show each outcome, not a random sample, and the pothole-like reading is one of our constructed probes."),
        TAB("Sample readings and the response of /api/predict", ["Reading", "Input (m/s2, rad/s, km/h)", "Acc. magnitude", "Gyro magnitude", "Accident", "Severity", "Probability"], SAMPLES,
            widths=[1.1, 2.0, 0.65, 0.6, 0.6, 0.7, 0.65], align=["l", "l", "r", "r", "c", "c", "r"], size=8.5),
        P("For a Moderate or Severe answer the browser then calls /api/emergency. For the Banjara Hills position used in the screenshots (latitude 17.4126, longitude 78.4471) the server returned alert id RQ-1792896858 and this message:"),
        CODE("ResQAI EMERGENCY ALERT\nSeverity: Severe (confidence 100%)\nLocation: 17.41260, 78.44710\nGoogle Maps: https://www.google.com/maps?q=17.41260,78.44710\n"
             "Nearest hospital: Care Hospitals, Banjara Hills (0.0 km away, 040-30418888)\nNo response received from occupant. Please dispatch assistance.", 8.5),
        P("The three nearest hospitals returned with it were Care Hospitals (0.00 km), Rainbow Children's Hospital (0.27 km) and Yashoda Hospitals, Somajiguda (1.34 km). The second is a paediatric hospital: the directory holds no information about specialty or capacity, "
          "so the nearest hospital is not always the most suitable one (Section 8.10)."),
        P(f"The single severity error of the test split is a {ex['kind'].replace('_', ' ')} (true severity {ex['true_severity']}) with acceleration magnitude {ex['acc_magnitude']} m/s2, gyroscope magnitude {ex['gyro_magnitude']}, speed change {ex['speed_change']} km/h and jerk {ex['jerk']}, which the model graded {ex['pred_severity']} with accident probability {ex['accident_probability']}. "
          "Its magnitude lies in the stretch where the minor and moderate generators overlap (24.9 to 32.8 m/s2), so the error is a boundary case and not a surprise."),
    ]


def _comparison():
    return [
        H2("8.8 Comparison with the Base Paper and Related Work"),
        P(f"The base paper {c('base')} predicts the severity of a crash from the police record written after it happened: 30,442 crash records from Dongguan, China, 2019 to 2023, split 19,483 / 4,871 / 6,088, with driver, vehicle, road and weather attributes, and three tasks (injury severity with five classes, fatal severity with five classes and property loss with six classes). "
          "Its multi-task FT-Transformer reports accuracy 70.31 % for injury severity (F1 64.48 %), 90.38 % for fatal severity (F1 86.71 %) and 80.79 % for property loss (F1 79.18 %), and beats eight baseline models and an earlier multi-task CNN."),
        P("The two works cannot be compared by their numbers, and the table below is a comparison of what each does, not of scores."),
        TAB("ResQAI against the base paper and the two companion papers", ["Aspect", "Base paper [1]", "GreenBox [6]", "CIRS [7]", "ResQAI"], [
            ["Input", "Police crash records (tabular, after the event)", "Push-button impact sensors, MPU-6050, water sensors, GPS (Arduino)", "Camera frames", "11 motion features of a (simulated) phone reading"],
            ["Data", "30,442 real records, one Chinese city", "None reported", "5,200 accident and 4,800 non-accident frames", "12,000 synthetic events; none real"],
            ["Task", "Severity of injury, fatality and property loss", "Impact and roll-over detection, alert by SMS", "Accident detection, scene description, dispatch", "Crash detection, 4-level severity, confirmation, hospital and message"],
            ["Reported result", "Accuracy 70.31 / 90.38 / 80.79 %", "Qualitative: SMS 'in a matter of seconds'", "Accuracy 86.5 %, precision 0.866, recall 0.856, F1 0.861", "Detector 1.0000, severity 0.99958 on synthetic data (Section 8.3-8.4)"],
            ["Alert path", "None", "SMS with GPS position to preset contacts; cancel by SMS", "Multi-agent dispatch (reported)", "Message drafted and displayed; not sent"],
            ["False-alarm handling", "Not applicable", "Owner can cancel by SMS", "128 of 1,044 non-accident frames falsely flagged", "15-second cancel window; measured 0 % on held-out braking"],
        ], widths=[0.9, 1.3, 1.3, 1.2, 1.5], align=["l", "l", "l", "l", "l"], size=8),
        P("ResQAI's scores are higher than the base paper's, but that is not a finding. The base paper works on real, noisy, human-recorded data with overlapping classes and an inherently uncertain target (how many people were injured); ResQAI works on synthetic classes that are separable by construction. "
          "A fair comparison would need ResQAI evaluated on real sensor recordings of crashes, which do not exist in this project. What ResQAI does take from the base paper is the framing: severity is worth predicting, not only occurrence, and per-class accuracy, precision, recall and F1 are the right way to report it. "
          "It does not use the FT-Transformer, the multi-task loss, SMOTE or SHAP."),
        P(f"Against GreenBox {c('greenbox')}, ResQAI replaces fixed hardware thresholds with a learned severity grade and adds the hospital ranking, but GreenBox sends a real SMS and has been tested on a vehicle on the road, which ResQAI has not. "
          f"Against CIRS {c('cirs')}, ResQAI uses motion sensors that every phone carries instead of fixed cameras, so it can follow a vehicle anywhere, but CIRS was evaluated on real images and reports a false-alarm count, while ResQAI's figures describe generated data. "
          f"Neither companion paper reports an end-to-end alert time, so ResQAI's alert-path compute time ({F.ALERT_PATH['mean']:.0f} ms) has nothing to be compared with."),
    ]


def _analysis():
    return [
        H2("8.9 Success and Failure Analysis"),
        H3("8.9.1 What worked"),
        B(f"**The pipeline runs end to end.** A reading becomes a detection, a grade, an optional countdown, a location, three ranked hospitals and a dispatch message; {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} smoke checks and {F.TESTS['by_group']['unit']['passed']} of {F.TESTS['by_group']['unit']['total']} unit checks pass.",
          f"**Hard braking is not mistaken for a crash.** None of {F.SHIP['per_event_kind']['harsh_brake']['n']} held-out braking events is flagged, and the 15-second window gives the occupant a way to correct any other false alarm.",
          f"**Severity grading is accurate on its own distribution.** Accuracy {F.SEVM['accuracy']:.5f} (five-seed mean {F.SEEDS['mean']['sev_accuracy']:.5f}); every error is to a neighbouring class.",
          f"**It is quick.** {F.ALERT_PATH['mean']:.1f} ms of compute for the three calls of an alert, {F.INF['mean']:.1f} ms for the two models.",
          f"**Access control behaves as coded.** All {F.TESTS['by_group']['security']['total']} security checks pass, including the lock-out after five wrong passwords."),
        H3("8.9.2 What failed or is unproven"),
        B(f"**One severity error.** A Minor crash at 31.9 m/s2 was graded Moderate (Section 8.7); the application would have opened a countdown for it.",
          f"**Road-surface events.** About half of pothole-like ({F.pct(F.OOD['pothole']['predicted_accident_rate'])}) and speed-breaker-like ({F.pct(F.OOD['speed_breaker']['predicted_accident_rate'])}) events are flagged as accidents because the models have never seen them.",
          f"**Noise.** Above a quarter of the natural spread the detector's false-alarm rate climbs ({F.pct(F.NOISE[3]['det_false_alarm'])} at 0.25, {F.pct(F.NOISE[4]['det_false_alarm'])} at 0.50).",
          "**Input validation.** Eight edge cases are mishandled: four return HTTP 500, three accept nonsense input and one reuses an alert id (Chapter 7).",
          "**Alert delivery.** No message is sent, so the time to reach a human, which is what the system is for, is unmeasured."),
        H3("8.9.3 Why the near-perfect scores should not be trusted as a forecast"),
        P("Three features of the experiment make the scores optimistic. The training and test events come from one generator, so there is no distribution shift; the crash classes are far from the non-crash classes, so detection is trivial; and the sensors are noiseless apart from the Gaussian spread written into the generator. "
          "The repeat over five seeds and the fact that a retrained model agrees with the shipped one show that the numbers are stable and reproducible; they do not show that they transfer. "
          "The right claim is that the software and the models are consistent with each other and with the design, and that the next step is real data."),
    ]


def _limits():
    return [
        H2("8.10 Limitations"),
        B("**No real data.** All 12,000 events are generated; no smartphone recording, crash test or road trial was used.",
          "**Single sensor location and orientation.** The generator has no notion of how the phone is mounted, which axis points forward, or whether the phone is in a pocket; a real deployment needs orientation normalisation.",
          "**Pothole, speed-breaker, drop and bump events are not modelled** (Section 8.6).",
          "**Hospital directory.** Ten hospitals in Hyderabad, ranked by straight-line distance; no road network, traffic, specialty (the second-nearest hospital in the sample is a children's hospital), bed capacity or opening hours. Outside Hyderabad the 'nearest' hospital would be hundreds of kilometres away.",
          "**No transmission.** The dispatch message is displayed; there is no SMS, voice call or e-mail gateway, no contact list and no acknowledgement from a responder.",
          "**Confirmation window.** 15 seconds is taken from the project brief; an incapacitated occupant cannot cancel, which is intended, but a conscious occupant who is slow also triggers an alert.",
          "**Server.** Flask development server, in-process lock-out counter, JSON-file accounts, 12-hour tokens without revocation, no HTTPS, no rate limiting beyond the login lock-out.",
          "**Alerts are not stored** and carry no user id, so there is no audit trail and no history of alerts.",
          "**No user study** and no usability or accessibility evaluation beyond the keyboard (Escape) and screen-reader labels visible in the code."),
    ]


def _objectives():
    return [
        H2("8.11 Objectives Against Outcomes"),
        P("The project brief lists six objectives (6.OBJECTIVES&PROBLEM STATEMENT.docx). The table states, for each, what was built and what was measured, in plain terms."),
        TAB("Objectives and outcomes", ["No.", "Objective", "Outcome", "Evidence"], [
            ["1", "Collect and preprocess smartphone accelerometer, gyroscope, speed and GPS data for normal driving and collision events",
             "**Partly.** An 11-feature pipeline and a generator of 12,000 synthetic events; no real smartphone recordings were collected.", "train_models.py; Sections 8.1, 8.3"],
            ["2", "Train a classifier that separates genuine accidents from potholes, speed breakers and hard braking",
             f"**Partly.** Hard braking: 0 of {F.SHIP['per_event_kind']['harsh_brake']['n']} held-out events flagged. Potholes and speed breakers are not in the training data; a constructed probe flags {F.pct(F.OOD['pothole']['predicted_accident_rate'], 0)} and {F.pct(F.OOD['speed_breaker']['predicted_accident_rate'], 0)} of them, never as Moderate or Severe.", "Sections 8.3, 8.6"],
            ["3", "Build a severity model that grades an impact as minor, moderate or severe",
             f"**Achieved on synthetic data.** Accuracy {F.SEVM['accuracy']:.5f}, macro-F1 {F.SEVM['macro_f1']:.5f}; five-seed mean {F.SEEDS['mean']['sev_accuracy']:.5f} / {F.SEEDS['mean']['sev_macro_f1']:.5f}.", "Section 8.4"],
            ["4", "Use GPS to locate the crash and identify a suitable nearby hospital",
             "**Achieved at demo level.** Browser geolocation (fallback: default area), haversine ranking over a ten-hospital Hyderabad directory; no live hospital service, no specialty or capacity.", "Sections 8.2, 8.7"],
            ["5", "Dispatch an automated alert carrying location and severity to emergency contacts and medical services",
             "**Partly.** The alert id, message, map link and hospital are generated and displayed, with tap-to-call for 108, 112 and 103; **nothing is transmitted**.", "Screens 10, 11"],
            ["6", "Evaluate detection accuracy, false-alarm rate and end-to-end alert latency",
             f"**Done.** Accuracy and false-alarm rate reported with five-seed repeat, baselines, noise and threshold analyses; alert path {F.ALERT_PATH['mean']:.1f} ms mean on loopback plus the 15 s confirmation window; real delivery latency not measurable.", "Sections 8.3-8.6; Chapter 7"],
        ], widths=[0.35, 1.9, 3.1, 1.0], align=["c", "l", "l", "l"], size=9),
        P("Two items of the project definition beyond the six objectives were also met: a confirmation mechanism that reduces false alerts (the 15-second countdown, cancellable by button or Escape) and an emergency dashboard showing the accident and the hospitals on a map. "
          "The evaluation metrics named in the brief (accuracy, precision, recall and F1) are all reported, per class for severity."),
    ]


def blocks():
    return [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS")] + _setup() + screens() + _detector() + _severity() + _baselines() + _robust() + _samples() + _comparison() + _analysis() + _limits() + _objectives()
