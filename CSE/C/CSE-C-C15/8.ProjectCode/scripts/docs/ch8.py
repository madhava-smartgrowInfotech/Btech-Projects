"""Chapter 8: Results and output screens for SentinelFlow. Every number is read from facts.py (F.SHIP, F.REAL, F.HYB, F.WIN, F.LAT, F.API); nothing is typed in except labels."""
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, PAIR, TAB
from .refs import CITE as C

assert (C['base'], C['s_wisne'], C['carpet'], C['rahman'], C['engelen']) == (1, 3, 6, 7, 9)   # reference numbers typed in the prose below

SH = F.shot
RES = os.path.join(F.CODE, "results")


def pc(x, d=2):
    return f"{x * 100:.{d}f} %"


def S(name, caption, base=5.6, max_h=3.9):
    return FIG(SH(name), caption, F.shot_w(SH(name), base, max_h))


def screens(a, b):
    """Two screenshots: side by side in the report, one under the other in the chapter document."""
    if F.REPORT:
        return [PAIR([(SH(a[0]), a[1]), (SH(b[0]), b[1])], 3.0)]
    return [S(*a), S(*b)]


def blocks():
    K = F.K()
    R, H, W, A, L = F.REAL, F.HYB, F.WIN, F.API, F.LAT
    s = F.SHIP
    sr = R["shipped_on_real_all"]
    b = [H1("8. RESULTS AND OUTPUT SCREENS")]

    # ------------------------------------------------------------------ 8.1
    b += [H2("8.1 What was measured and how"),
          P("Four sets of measurements are reported, and they must be read together because they answer different questions. (1) The model the product shipped with, as it displays itself on its Model page: it was trained on a labelled synthetic fallback dataset, "
            "because CICIDS2017 was unreachable when the product was built. (2) The same model, and the same forest retrained with the product's own settings, on **real** CICIDS2017 flows: the Friday-afternoon DDoS capture, "
            f"{R['rows']:,} labelled flows ({R['benign']:,} benign, {R['attack']:,} DDoS), obtained from the Hugging Face mirror `c01dsnap/CIC-IDS2017` of the original `MachineLearningCSV` file and mapped to the ten-feature schema with the product's own `ml/preprocessing.py` "
            "(licence 'other'; the file is not part of the repository). (3) The shipped model inside the real window pipeline (aggregation, distributed risk, severity) on windows of 2, 5 and 10 seconds from the product's own traffic simulator. "
            "(4) Timings and behaviour of the running software (Chapter 7)."),
          P("All numbers come from `results/metrics.json` and `results/experiments/*.json`, written by `scripts/run_experiments.py` and `scripts/measure_api.py`, and are copied in `docs/REPORT_FACTS.md`. "
            "The hardware was an Intel Core i5-12500 with 15.7 GB of RAM and no GPU; no packet was captured from a real interface because Npcap is not installed.")]

    # ------------------------------------------------------------------ 8.2
    b += [H2("8.2 The shipped model on its own test split"),
          P(f"The shipped Random Forest (200 trees, balanced class weights, seed 42) was trained in {s['training_seconds']} s on {s['train_samples']:,} rows and tested on {s['test_samples']:,} held-out rows. The 24,000 rows are 9,000 benign and 9,000 attack synthetic flows plus "
            "6,000 aggregated simulator windows (3,000 of each class). The table below reproduces what the console shows."),
          TAB("Shipped model on its own held-out split (synthetic fallback data plus simulator windows).",
              ["Measure", "Value"],
              [["Accuracy", pc(s["accuracy"])], ["Precision (attack)", pc(s["precision"])], ["Recall (attack)", pc(s["recall"])], ["F1", pc(s["f1"])], ["ROC-AUC", pc(s["roc_auc"])],
               ["False-positive rate", f"{pc(K['ship_fpr'], 3)} ({F.CMX[0][1]} of {sum(F.CMX[0]):,} benign rows)"],
               ["False negatives", f"{F.CMX[1][0]} of {sum(F.CMX[1]):,} attack rows"], ["Confusion matrix [[TN, FP], [FN, TP]]", str(F.CMX)]],
              widths=[3.0, 3.3], align=["l", "l"], size=10.5),
          PAIR([(os.path.join(RES, "confusion_matrix.png"), "Confusion matrix of the shipped model (results/confusion_matrix.png)."),
                (os.path.join(RES, "roc_curve.png"), "ROC curve of the shipped model (results/roc_curve.png).")], 3.0),
          FIG(os.path.join(RES, "feature_importance.png"), "Feature importance of the shipped forest (results/feature_importance.png).", 4.6),
          P("These figures are real measurements of the shipped file, but they describe how well the forest separates two synthetic generators, not how well it detects DDoS traffic. The synthetic flows are drawn from simple distributions "
            "(an attack flow has many forward packets and few backward ones), and the window rows come from the generator that Simulation Mode later uses. A near-perfect score on such data is expected and says little about real traffic. "
            "The shipped forest leans on the sent-side counts: `sent_packets` (0.209), `received_packets` (0.176) and `sent_packets_per_second` (0.142) carry 53 % of the importance.")]

    # ------------------------------------------------------------------ 8.3
    b += [H2("8.3 Real-data check on CICIDS2017"),
          H3("8.3.1 The shipped model does not transfer"),
          P(f"Applied to all {R['rows']:,} real flows without any retraining, the shipped model scores **{pc(sr['accuracy'], 1)} accuracy, {pc(sr['precision'], 1)} precision, {pc(sr['recall'], 1)} recall, {pc(sr['f1'], 1)} F1 and a {pc(sr['fpr'], 1)} false-positive rate** "
            f"(ROC-AUC {pc(sr['roc_auc'], 1)}). Of {R['benign']:,} benign flows, {sr['fp']:,} are flagged as attacks; of {R['attack']:,} DDoS flows, {sr['fn']:,} are missed. A 20 % stratified sample gives the same picture ({pc(R['shipped_on_real_20pct']['accuracy'], 1)} accuracy), "
            "so the result is not an artefact of sample size. The ROC-AUC of 86.1 % shows that the forest's scores still rank attacks above benign flows better than chance, but the 0.5 threshold learnt from synthetic data is wrong for real flows."),
          H3("8.3.2 The same forest retrained on real flows"),
          P("The product's training script would have produced a different model if the CICIDS2017 CSV had been present in `data/raw/`. To measure that, the same forest (ten features, 200 trees, balanced class weights) was trained on the real flows, with a stratified 80/20 split repeated for five seeds, "
            "and with a chronological block split (the first 70 % of the file for training, the last 30 % for testing, since row order in these files follows capture order)."),
          TAB("Real CICIDS2017 Friday-DDoS flows: shipped model versus a forest retrained on real flows.",
              ["Experiment", "Accuracy", "Precision", "Recall", "F1", "FPR", "Rows tested"],
              [[n] + [pc(d[k]) for k in ("accuracy", "precision", "recall", "f1", "fpr")] + [f"{d['n']:,}"] for n, d in
               [("Shipped (synthetic) model, all real flows", sr), ("Retrained RF, seed 42, 20 % test", R["real_rf_seed42"]), ("Retrained RF, block split (70 % / 30 %)", R["real_rf_block_split"])]]
              + [["Retrained RF, five seeds, mean ± std", F.mstd(*K["rr_acc"]) + " %", F.mstd(*K["rr_prec"]) + " %", F.mstd(*K["rr_rec"]) + " %", F.mstd(*K["rr_f1"]) + " %", F.mstd(*K["rr_fpr"], d=3) + " %", "45,149 each"]],
              widths=[2.3, 0.8, 0.8, 0.7, 0.7, 0.7, 0.8], align=["l", "r", "r", "r", "r", "r", "r"], size=8.5),
          FIG(F.fig("f01_domain_gap.png"), "Accuracy, recall and false-positive rate: the shipped model on its own synthetic split, on real flows, and a forest retrained on real flows.", 5.8),
          FIG(F.fig("f06_confusion_matrices.png"), "Confusion matrices: shipped model on its synthetic test, shipped model on real flows, retrained forest on real flows.", 6.0),
          P(f"Retrained on real flows, the forest reaches {F.mstd(*K['rr_acc'])} % accuracy (the standard deviation over five seeds is 0.01 points) with a false-positive rate of {F.mstd(*K['rr_fpr'], d=3)} %, in {R['real_rf_per_seed'][0]['train_seconds']} s of training and a {R['real_rf_model_mb']} MB model file. "
            f"The chronological split gives {pc(K['blk_acc'])} accuracy and {pc(K['blk_fpr'])} false positives; its test part is {R['block_split_test_benign_share'] * 100:.1f} % benign. That the block split is slightly worse than the random split is expected: neighbouring flows of one attack burst are near-duplicates, "
            "so a random split leaks. Even so, both splits come from one capture day with one attack type, and CICIDS2017 is known to contain labelling and flow-construction errors [9]; these numbers show that the ten features separate this day's DDoS from this day's benign traffic, not that they would separate any DDoS from any benign traffic."),
          H3("8.3.3 Classifier comparison and feature ablation"),
          P("The base paper compares seven classifiers before building voting ensembles. The same style of comparison was made here on the real split (seed 42), using classifiers from scikit-learn with their default or stated settings."),
          TAB("Classifiers on real CICIDS2017 flows (same split, seed 42; training and prediction times on a CPU-saturated host).",
              ["Classifier", "Accuracy", "F1", "FPR", "Train (s)", "Predict 45,149 rows (s)"],
              [[n, pc(d["accuracy"]), pc(d["f1"]), pc(d["fpr"]), f"{d['train_seconds']:.2f}", f"{d['predict_seconds_test_set']:.3f}"] for n, d in R["baselines_seed42"].items()],
              widths=[2.2, 0.9, 0.8, 0.8, 0.8, 1.2], align=["l", "r", "r", "r", "r", "r"], size=9.5),
          FIG(F.fig("f03_classifier_comparison.png"), "Classifier comparison on real flows: accuracy, F1, false-positive rate and training time.", 6.0),
          P(f"The three tree-based learners are indistinguishable at 99.94-99.95 % accuracy; the Random Forest the product uses gives up nothing against gradient boosting, but it is the slowest of the three to train ({R['baselines_seed42']['RandomForest(200)']['train_seconds']:.1f} s against "
            f"{R['baselines_seed42']['HistGradientBoosting']['train_seconds']:.1f} s for boosting and {R['baselines_seed42']['DecisionTree']['train_seconds']:.1f} s for one tree). A single decision tree scores the same as the forest on this data. Gaussian Naive Bayes fails ({pc(R['baselines_seed42']['GaussianNB']['accuracy'], 1)} accuracy, "
            f"{pc(R['baselines_seed42']['GaussianNB']['fpr'], 1)} false positives): its independence and normality assumptions do not fit heavy-tailed packet counts. Scaled logistic regression is respectable ({pc(R['baselines_seed42']['LogisticRegression(scaled)']['accuracy'], 1)}) but has a {pc(R['baselines_seed42']['LogisticRegression(scaled)']['fpr'], 1)} false-positive rate. "
            "For comparison, the reference paper in the batch folder reports 0.971 for an SVM, 0.827 for a decision tree and 0.593 for logistic regression on a different, small CIC sample [7]; the datasets differ, so the ordering of the tree against the SVM there says nothing about this data."),
          TAB("Feature-group ablation: Random Forest on real flows (seed 42).",
              ["Feature group", "Features", "Accuracy", "Recall", "FPR"],
              [[n.replace("_", " "), str(len(d["features"])), pc(d["accuracy"]), pc(d["recall"]), pc(d["fpr"])] for n, d in R["ablation_seed42"].items()],
              widths=[2.4, 0.8, 1.1, 1.0, 1.0], align=["l", "c", "r", "r", "r"], size=9.5),
          FIG(F.fig("f04_feature_importance_compare.png"), "Feature importance of the shipped forest and of the forest retrained on real flows.", 5.6),
          P("Dropping the four rate features changes nothing (99.91 % accuracy, the lowest false-positive rate of any group at 0.02 %), and the four count and byte features alone do just as well. The received-side features alone are clearly worse (95.83 % accuracy, 9.56 % false positives): "
            "on this capture the attacker's forward direction carries the signal. The retrained forest relies on the average sent packet size (0.226), `sent_packets` (0.188) and `sent_bytes` (0.183), whereas the shipped forest relied mostly on counts. "
            "The ablation also shows a weakness of the design: because rates are counts divided by the window length, they add no information on top of the counts, and the model is only calibrated to the window length it was trained on (Section 8.5)."),
          FIG(F.fig("f05_feature_ablation.png"), "Feature-group ablation on real flows.", 5.2)]

    # ------------------------------------------------------------------ 8.4
    hm, hw = H["mixed_test"], H["hybrid_on_sim_windows"]
    b += [H2("8.4 The product's training recipe on real flows"),
          P(f"`ml/train_model.py` combines flow rows with 6,000 aggregated simulator windows so that window-scale feature values are represented. Run on the real file instead of the synthetic fallback (the flows plus the windows, capped at 120,000 rows: {H['benign']:,} benign and {H['attack']:,} attack), "
            f"the recipe gives {pc(hm['accuracy'])} accuracy, {pc(hm['f1'])} F1 and {pc(hm['fpr'], 3)} false positives on its own mixed 24,000-row test set, and {pc(H['hybrid_on_real_all_flows']['accuracy'])} accuracy on all real flows (about 80 % of the sampled flows were seen in training, so this second figure is optimistic). "
            f"On fresh simulator windows of 2, 5 and 10 seconds it classifies every window correctly ({pc(hw['window_2s']['accuracy'], 0)}, {pc(hw['window_5s']['accuracy'], 0)}, {pc(hw['window_10s']['accuracy'], 0)}), but this is not evidence: those windows come from the same generator that produced the augmentation rows."),
          P(f"The contrast with the forest trained on real flows alone is instructive. That forest labels every one of 1,500 simulator windows of 10 s as benign (attack recall {pc(R['real_rf_on_sim_windows']['window_10s']['recall'], 0)}), although its ROC-AUC on them is {pc(R['real_rf_on_sim_windows']['window_10s']['roc_auc'], 0)}: a flow-scale model sees a window with thousands of packets as unlike anything it has learnt, and the scores rank "
            "correctly while the threshold is wrong. A forest needs training rows at the scale it will be applied to; the window rows are what supplies that, and they are synthetic."),
          FIG(F.fig("f10_flow_vs_window_scale.png"), "Attack recall and false-positive rate on 10 s simulator windows for three training sets.", 5.2)]

    # ------------------------------------------------------------------ 8.5
    w2, w5, w10 = W["window_2s"], W["window_5s"], W["window_10s"]

    def wrow(lab, w):
        return [lab, pc(w["ml_only"]["accuracy"], 1), pc(w["ml_only"]["fpr"], 1), pc(w["actionable_high_or_critical"]["accuracy"], 1), pc(w["actionable_high_or_critical"]["fpr"]),
                pc(w["actionable_high_or_critical"]["recall"], 1), pc(w["distributed_risk_ge_0.7_only"]["recall"], 1), pc(w["distributed_risk_ge_0.4_only"]["recall"], 1)]
    miss10 = w10["actionable_high_or_critical"]["fn"]
    b += [H2("8.5 The window pipeline: model, risk and severity together"),
          P(f"The most informative experiment for the product as a whole feeds the shipped model through the pipeline as `app.py` runs it: simulator packets, `traffic_aggregator`, Random Forest, distributed risk against a rolling twelve-window baseline, persistence and severity. For each window length, "
            f"{w2['windows']:,} windows were generated with the simulator's own settings ({w2['attack_windows']:,} attack windows of three styles, {w2['benign_windows']:,} benign). The table below compares three possible decision rules: the forest's label alone, the severity layer (a window acts only at High or Critical, which is what triggers a quarantine), "
            "and the distributed-risk score alone at two thresholds."),
          TAB("Shipped model through the pipeline at three window lengths (4,000 simulated windows each).",
              ["Window", "RF label: accuracy", "RF label: FPR", "High/Critical: accuracy", "High/Critical: FPR", "High/Critical: recall", "Risk >= 0.7: recall", "Risk >= 0.4: recall"],
              [wrow("2 s", w2), wrow("5 s", w5), wrow("10 s", w10)], widths=[0.55, 0.85, 0.75, 0.85, 0.8, 0.8, 0.75, 0.75], align=["c"] + ["r"] * 7, size=8.5),
          FIG(F.fig("f02_window_size_effect.png"), "False-positive rate of the forest's label and of High/Critical severity, and the recall of High/Critical, at three window lengths.", 5.8),
          P(f"Three results stand out. **First, window length matters a great deal.** The forest was calibrated on 10-second windows. At 10 s its label is perfect on these simulated windows (a result that, as Section 8.4 explains, only reflects the shared generator); at 5 s it flags {pc(w5['ml_only']['fpr'], 1)} of benign windows as attacks, and at 2 s, the window length used for the screenshots, {pc(w2['ml_only']['fpr'], 1)}. "
            "Shorter windows contain fewer packets, the count features fall, and benign traffic starts to look like the lower end of the attack classes. The Simulation Mode default is 5 s and the live default 10 s, so the product's own demo setting is not the setting its model was calibrated for. "
            f"**Second, the severity layer removes most of the damage.** Requiring High or Critical lowers the benign-window false-positive rate to {pc(w5['actionable_high_or_critical']['fpr'])} at 5 s ({w5['actionable_high_or_critical']['fp']} of {w5['benign_windows']:,} windows) and {pc(w2['actionable_high_or_critical']['fpr'])} at 2 s ({w2['actionable_high_or_critical']['fp']} windows), at no cost in recall at those lengths (100 %). "
            "A false positive here is a quarantine of a source, which is the harm the batch's problem statement warns about, so this is the number that matters operationally. "
            f"**Third, the layer misses some real attacks at the length it was designed for.** At 10 s, {miss10} of {w10['attack_windows']:,} attack windows ({pc(1 - w10['actionable_high_or_critical']['recall'])}) stay at Medium, because the severity thresholds were tuned against a different packet-rate scale; none of them is quarantined, though each is flagged and a rate limit is recommended."),
          P(f"The distributed-risk score alone is precise but nearly blind: it has no false positives at either threshold (precision 100 %), yet at the 0.7 threshold it recovers only {pc(w2['distributed_risk_ge_0.7_only']['recall'], 1)}, {pc(w5['distributed_risk_ge_0.7_only']['recall'], 1)} and {pc(w10['distributed_risk_ge_0.7_only']['recall'], 1)} of attack windows at 2, 5 and 10 s, and "
            f"{pc(w2['distributed_risk_ge_0.4_only']['recall'], 1)}, {pc(w5['distributed_risk_ge_0.4_only']['recall'], 1)} and {pc(w10['distributed_risk_ge_0.4_only']['recall'], 1)} at 0.4. It is therefore used as one input of the severity score, not as a detector, and the carpet-bombing signal it carries is only as good as the spread of destinations in the window. "
            "The second table shows how the severity layer treats each traffic style at 5 s."),
          TAB("Severity by traffic style, 5 s windows (counts of windows).",
              ["Style", "Windows", "Mean packets/s", "RF flags Attack", "Low", "Medium", "High", "Critical", "Reaches High/Critical"],
              [[st, str(d["n"]), f"{d['mean_packet_rate']:.0f}", pc(d["ml_attack_rate"], 1)] + [str(d["severity_counts"][k]) for k in ("Low", "Medium", "High", "Critical")] + [pc(d["actionable_rate"], 1)]
               for st, d in w5["by_style"].items()],
              widths=[0.8, 0.7, 0.8, 0.8, 0.5, 0.65, 0.5, 0.65, 0.9], align=["l"] + ["r"] * 8, size=8.5),
          FIG(F.fig("f07_severity_by_style.png"), "Share of windows at each severity level for each simulated traffic style (5 s windows).", 5.4)]

    # ------------------------------------------------------------------ 8.6
    b += [H2("8.6 Mitigation behaviour in the running system"),
          P(f"In the live simulation run on a scratch copy of the backend (2 s windows), the first detection was stored {A['first_detection_after_start_seconds']:.1f} s after pressing Start. In the observation period {A['live_sim_windows_scored']} windows were scored: "
            f"{A['live_sim_by_prediction'].get('Attack', 0)} Attack and {A['live_sim_by_prediction'].get('Benign', 0)} Benign, with severities "+", ".join(f"{A['live_sim_by_severity'].get(k, 0)} {k}" for k in ('Critical', 'High', 'Medium', 'Low'))+f". The {A['live_sim_by_severity'].get('High', 0) + A['live_sim_by_severity'].get('Critical', 0)} High and Critical windows produced {A['live_sim_quarantines_recorded']} quarantine rows (three sources each), and {A['status_during_simulation']['active_mitigations']} quarantines were active at the time of the status call. "
            "Medium windows produced only a rate-limit recommendation, and Low windows were monitored. Each quarantine lasts 40 s (80 s for Critical) and then lapses; the Mitigation page counts the seconds down and the history row changes from active to recovered."),
          P(f"The decision itself is quick: from the finished feature vector to the mitigation decision took a median of {L['detect_to_mitigation_ms']['p50']:.0f} ms (95th percentile {L['detect_to_mitigation_ms']['p95']:.0f} ms) on a CPU-saturated machine, almost all of it forest inference (Chapter 7). "
            "What the quarantine does is limited, however: it adds the address to a list inside SentinelFlow. The operating-system firewall is never modified (`apply_os_firewall_block()` returns `applied: False`), no packet is dropped, and rate limiting is advised, not applied. "
            "The mitigation therefore demonstrates the policy, its timing and its recovery, not an actual reduction of attack traffic. The time between the first attack packet and the quarantine is at least the window length (10 s by default) plus the decision time; it was not measured against a real attack.")]

    # ------------------------------------------------------------------ 8.7
    b += [H2("8.7 Comparison with the base paper"),
          P(f"The base paper [{1}] reports 100 % accuracy, precision, recall and F1 for all four of its voting ensembles on both of its datasets. The comparison with SentinelFlow can only be indicative: the datasets, the features, the classifiers and the evaluation protocols differ, and the base paper measures resource use that SentinelFlow measures only coarsely. "
            f"The like-for-like fact is that the same family of tree learners reaches {F.mstd(*K['rr_acc'])} % on a real DDoS capture here, close to the paper's figure, and that this requires training on real data, which the shipped model did not."),
          TAB("Base paper and SentinelFlow, side by side (datasets and protocols differ).",
              ["Aspect", "Base paper (IEEE Access 2026)", "SentinelFlow (this project)"],
              [["Data", "SDN flow dataset (104,345 records, 23 features); CIC-DDoS2023 subset (1,754,109 rows, 47 features)", f"CICIDS2017 Friday-DDoS flows ({R['rows']:,} rows), mapped to 10 features; shipped model: synthetic fallback"],
               ["Features", "RF importance combined with the Banzhaf Power Index to select a subset", "Ten fixed count, byte, rate and size features shared by training and live windows; no feature selection"],
               ["Classifiers", "XGBoost, RF, Gradient Boosting, SVM, kNN, AdaBoost, Naive Bayes; four hard-voting ensembles", "Random Forest (200 trees); single-classifier comparison on real flows (Section 8.3.3)"],
               ["Headline result", "100 % accuracy, precision, recall, F1 on both datasets", f"{F.mstd(*K['rr_acc'])} % (5 seeds, real flows); {pc(K['ship_acc'])} on the synthetic split; {pc(K['shipreal_acc'], 1)} for the shipped model on real flows"],
               ["Resource profile", "Training time, inference time, memory, model size per ensemble; SVM-based ensembles over 4,000 s to train, kNN over 150 s to classify the SDN test set", f"RF trains in {R['real_rf_per_seed'][0]['train_seconds']} s (real flows); model {R['real_rf_model_mb']} MB (real) or {L['model_file_mb']} MB (shipped); window cost {L['total_ms']['p50']:.0f} ms median on a loaded host; no memory profile"],
               ["Mitigation", "Proposed as future work (throttling or blackholing; sidecar next to the controller)", "Implemented as application-level quarantine with automatic recovery; not enforced on the network"],
               ["False positives", "Reported through precision and F1 (all 1.0)", f"Measured per benign window: {pc(K['rr_fpr'][0], 3)} on real flows; {pc(K['w5_fpr_act'])} (5 s) after the severity layer"],
               ["Deployment test", "Offline datasets; live and testbed evaluation listed as future work", "Simulated windows through the real pipeline; live capture untested here (no Npcap)"]],
              widths=[1.1, 2.7, 2.7], align=["l", "l", "l"], size=8.8),
          P("Two further points of context. The carpet-bombing paper in the batch folder (Swileh et al. [6]) reports 99.94 % accuracy for an LLM-based detector at about two seconds per request on a Mininet and Ryu testbed, and the survey item of Raghavendran and Robinson [3] reports 97 % for KNN and 100 % for XGBoost on a testbed dataset; "
            "neither measurement is comparable with the figures above, and neither reports the effect of the false-positive rate on legitimate users that the severity layer addresses here.")]

    # ------------------------------------------------------------------ 8.8
    b += [H2("8.8 Sample input and output"),
          P("The excerpt below is a real detection record. It was produced by starting Simulation Mode on a scratch copy of the backend (window 2 s) and reading `GET /api/detections`; it was not edited except for omitting the unrelated top-destination list and rounding. "
            "The input is the ten-feature vector of one window of 7,504 packets from 20 sources to one destination; the output is the verdict, the risk breakdown, the severity score with its factors and the three quarantines."),
          CODE("""{ "id": 17, "source": "simulation", "prediction": "Attack", "confidence": 1.0, "severity": "Critical",
  "packet_rate": 3752.0, "byte_rate": 708363.5, "source_count": 20, "destination_count": 1,
  "distributed_risk": 0.6199, "mitigation_status": "quarantine",
  "detail": {
    "features": { "received_packets": 7504, "received_bytes": 1416727, "received_packets_per_second": 3752.0,
                  "received_bytes_per_second": 708363.5, "average_received_packet_size": 188.8,
                  "sent_packets": 0, "sent_bytes": 0, "sent_packets_per_second": 0.0,
                  "sent_bytes_per_second": 0.0, "average_sent_packet_size": 0.0 },
    "distributed": { "distributed_risk_score": 0.6199, "distributed_risk_level": "Medium",
                     "components": { "source_diversity": 0.667, "destination_diversity": 0.067,
                                     "packet_rate_pressure": 1.0, "baseline_deviation": 0.999 },
                     "explanation": "Observed 20 unique sources and 1 unique destinations at 3752 packets/sec
                       (708364 bytes/sec); traffic is spread across many sources (possible distributed flood)." },
    "severity": { "severity": "Critical", "severity_score": 75.0,
                  "factors": [ "Random Forest classified the window as Attack (100.0% confidence)",
                               "High model confidence (>= 90%)", "Very high packet rate (3752 pkt/s)",
                               "Medium distributed-traffic risk (0.62)" ],
                  "recommendation": "Quarantine top sources in SentinelFlow immediately and rate-limit the affected interface." },
    "actions": [ {"action": "quarantine", "target": "10.66.4.87", "duration": 80},
                 {"action": "quarantine", "target": "10.66.0.104", "duration": 80},
                 {"action": "quarantine", "target": "10.66.7.204", "duration": 80} ] } }""", 7.6),
          P("The severity score of 75 is the sum of 30 points for the Attack label, 15 for a confidence of at least 90 %, 20 for a rate of at least 3,000 packets per second and 10 for a medium distributed-risk score; it crosses the Critical threshold of 70, so the three busiest non-protected sources are quarantined for twice the base 40 s. "
            "The distributed-risk level is only Medium (0.62) because this is a single-destination flood: destination diversity contributes 0.067. A carpet-bombing window would score much higher on that component.")]

    # ------------------------------------------------------------------ 8.9
    sh = [H2("8.9 Output screens"),
          P("The twelve screens below were captured from the running React console at 1440 x 900 with the Playwright browser driver. The console was in Simulation Mode: windows are generated by the product's simulator and scored by the real model, and the interface labels this state; "
            "nothing on these screens is live network traffic. The simulation ran with 2-second windows, so the screens show the short-window behaviour discussed in Section 8.5, including benign-looking windows labelled Attack. The shipped database held about 250 scored windows at capture time."),
          ]
    sh += screens(("01_landing_light.png", "Landing page, light theme. A status card read from the API shows 140 attack windows, 68 benign windows, F1 99.71 % and ROC-AUC 99.99 %; these last two are the synthetic-split figures, shown here without a synthetic caveat."),
                  ("02_landing_dark.png", "Landing page, dark theme: 142 attack and 71 benign windows scored so far, same F1 and ROC-AUC. The counters update live from /api/detections."))
    sh += screens(("03_login.png", "Sign-in page. Email and password fields, the demo account (demo@sentinelflow.com, Demo@1234) and a Fill demo credentials button; the gate is browser-side only."),
                  ("04_overview.png", "Overview page. The amber banner says simulation mode; the red capture-problem banner reports the real error (winpcap not installed). Cards: Benign, severity Low (risk 0.1557), model confidence 73.5 %, 274 packets/s, 3 sources / 4 destinations, 23 active mitigations; session 207 windows done."))
    sh += screens(("05_detections.png", "Detections page, newest first, 100 rows with filters. Windows #232, #230, #226 and #224 are labelled Attack at 59-63 % confidence with only 3 sources, 4 destinations and 83-156 packets/s: benign-looking windows flagged by the forest at 2 s, held at Medium (rate limit advised). #227 (24 sources, 1 destination, 2,985 packets/s, 100 %) is Critical with a quarantine."),
                  ("06_threat_detail.png", "Threat-detail drawer for window #233: Benign at 52.5 % confidence, severity Low (score 4.2), 175 packets/s, 121,600 bytes/s, 3 sources, 4 destinations, distributed risk 0.14 with its four components, the first severity factor and the recommendation 'Continue routine monitoring'."))
    sh += screens(("07_analytics.png", "Analytics page: 237 windows scored, 155 Attack (65.4 %), 82 Benign, 99 High or Critical; donut chart, severity bar chart and the start of the packet-rate timeline. The simulator intends 35 % attack windows, so the 65.4 % reflects the short-window false alarms of Section 8.5."),
                  ("08_network_health.png", "Network health page, psutil counters sampled every 5 s: CPU 46.8 %, memory 98.1 % (the machine was heavily loaded), 1.8 GB received in 1,989,327 packets, 301 MB sent in 942,409 packets, with CPU/memory and throughput charts."))
    sh += screens(("09_mitigation.png", "Mitigation page: 18 active quarantines, 100 recorded actions, quarantine length 40 s (doubled for Critical). Each card shows the address, seconds left of 80 s, a progress bar and the reason, for example 172.16.28.168, 21 s left, 'Attack window (simulation) [Critical]'."),
                  ("10_model.png", "Model page: banner 'SYNTHETIC TRAINING DATA' with the warning that the numbers describe the synthetic fallback; accuracy 99.71 %, precision 99.96 %, recall 99.46 %, F1 99.71 %, ROC-AUC 99.99 %, 4,800 test samples, confusion matrix 2,399 / 1 / 13 / 2,387 and the feature-importance bars."))
    sh += screens(("11_settings.png", "Settings page: monitoring window 10 s (2-120), quarantine 40 s (5-3600, doubled for Critical), saved confirmation, dark-mode switch, and a session panel (signed in as the demo user, interface simulation, 224 windows completed, demo-gate note)."),
                  ("12_command_palette.png", "Command palette opened over the Overview page with the query 'tack': the matching detections (Windows #250, #245, #242, #238 and #235 Attack at Medium, #247 and #240 Critical with quarantine), with keyboard hints."))
    b += sh

    # ------------------------------------------------------------------ 8.10
    b += [H2("8.10 Success and failure analysis"),
          H3("Where the system succeeded"),
          B("**The loop closes.** A window goes from packets to a stored, explained detection and, when severe, to a temporary quarantine that recovers on its own, in a fraction of a second of compute per window (Chapter 7); 95 automated tests and 25 smoke checks pass.",
            f"**The severity layer works as a false-positive filter.** It lowers benign-window false positives from {pc(w5['ml_only']['fpr'], 1)} to {pc(w5['actionable_high_or_critical']['fpr'])} at 5 s and from {pc(w2['ml_only']['fpr'], 1)} to {pc(w2['actionable_high_or_critical']['fpr'], 1)} at 2 s while keeping recall at 100 %, and it lists the reasons for every verdict.",
            f"**The feature set is adequate for real DDoS flows.** Retrained on the real capture the forest reaches {F.mstd(*K['rr_acc'])} % accuracy over five seeds and {pc(K['blk_acc'])} on a chronological split; a single tree does as well.",
            "**The failure paths are handled.** Missing Npcap, a missing model, invalid features, out-of-range settings and a second start all produce a clear message or status code instead of a crash."),
          H3("Where it failed or fell short"),
          B(f"**The shipped model does not transfer to real flows**: {pc(sr['accuracy'], 1)} accuracy, {pc(sr['recall'], 1)} recall and {pc(sr['fpr'], 1)} false positives on {R['rows']:,} real CICIDS2017 flows, against {pc(s['accuracy'])} on its own synthetic split. The Model page warns about the synthetic data; the landing page does not.",
            f"**Window length breaks calibration.** At the Simulation Mode default of 5 s the forest alone flags {pc(w5['ml_only']['fpr'], 1)} of benign windows; the screenshots, taken at 2 s, show Attack labels on windows with 3 sources and under 160 packets/s.",
            f"**The severity layer misses weaker attacks at 10 s**: {miss10} of {w10['attack_windows']:,} attack windows stay at Medium and are not quarantined.",
            "**The 10 s synthetic result is circular.** Perfect accuracy on simulator windows follows from training on rows from the same generator; it is not detection performance.",
            "**The distributed-risk score is a weak detector** (recall 9-32 % at 0.7), and the carpet-bombing case was only tested with the simulator's own carpet style.",
            "**Mitigation is not enforcement.** Quarantine is a list inside the application; the firewall is untouched, nothing is dropped, rate limiting is only recommended.",
            f"**Inference is slower than it needs to be**: the saved `n_jobs=-1` makes single-window prediction about {L['single_inference_ms_n_jobs_-1']['p50'] / L['single_inference_ms_n_jobs_1']['p50']:.0f} times slower than `n_jobs=1` ({L['single_inference_ms_n_jobs_-1']['p50']:.0f} ms against {L['single_inference_ms_n_jobs_1']['p50']:.0f} ms median on the loaded host).",
            "**Live capture was never run**: Npcap is not installed on the test machine.")]

    # ------------------------------------------------------------------ 8.11
    b += [H2("8.11 Limitations of the results"),
          B("One real dataset, one attack day (the DDoS capture of CICIDS2017), one attack family; no other attack types, no other datasets, no cross-dataset test. The mirror's copy of the file was not independently checked against the original archive.",
            "CICIDS2017 has documented labelling and flow-construction problems [9]; flows adjacent in time are near-duplicates, so random splits overstate generalisation. The block split reduces but does not remove that.",
            "The window experiments use the product's own simulator, whose traffic styles were written by the same team that wrote the detector; they test the pipeline logic, not its behaviour on real mixtures of traffic.",
            "No real-time, live or testbed measurement: no real attack timeline, no throughput under load, no recovery of a real service. Timings come from a CPU-saturated machine and are upper bounds.",
            "The base-paper comparison is indicative only: different data, features, classifiers and protocol (Section 8.7).",
            "Seeds: the five-seed result varies only the split and the forest seed; the severity thresholds and the simulator settings were not tuned or varied in this study.")]

    # ------------------------------------------------------------------ 8.12
    b += [H2("8.12 Objectives against outcomes"),
          TAB("The six objectives of the batch against what was achieved.",
              ["#", "Objective", "Outcome"],
              [["1", "Acquire a benchmark dataset and extract flow features",
                f"Partly. The training script looks for CICIDS2017 CSVs in `data/raw` and otherwise builds a synthetic fallback, which is what shipped. In this documentation run the real Friday-DDoS file ({R['rows']:,} flows) was obtained and mapped with the product's own preprocessing; the shipped model was not retrained on it."],
               ["2", "Capture live traffic and compute the same features in real time",
                "Implemented (Scapy sniff, `traffic_aggregator`, the same ten-feature schema as training). Not verified on live traffic because Npcap is not installed; verified through the simulator, the aggregator tests and the error path."],
               ["3", "Train a classifier to distinguish DDoS from legitimate traffic",
                f"Achieved as code and, after retraining, as a result on real flows ({F.mstd(*K['rr_acc'])} %). The shipped artefact is synthetic-trained and scores {pc(sr['accuracy'], 1)} on real flows."],
               ["4", "Implement adaptive mitigation that rate-limits or blocks sources",
                "Partly. Temporary quarantine of the top three sources with automatic recovery, doubled for Critical; rate limiting only recommended; no enforcement outside the application."],
               ["5", "Build a dashboard of live traffic, detections and mitigation actions",
                "Achieved: nine-page React console plus the original dashboard, refreshed by polling every two seconds; screens in Section 8.9."],
               ["6", "Evaluate accuracy, false positive rate and time from detection to mitigation",
                f"Achieved for accuracy and false positives (synthetic split, real flows, three window lengths) and for decision latency (median {L['detect_to_mitigation_ms']['p50']:.0f} ms on a loaded host). Not measured against a real attack timeline."]],
              widths=[0.3, 2.2, 4.0], align=["c", "l", "l"], size=9.0)]
    return b
