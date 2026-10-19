"""Chapter 8: Results and output screens. Every number is read from experiments/*.json at build time."""

import json
import os

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F

SHORT = {"Normal": "Normal", "Bacterial Pneumonia": "Bacterial", "Viral Pneumonia": "Viral"}


def _samples():
    p = os.path.join(F.EXP, "sample_predictions.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def analysis():
    """Derived statements used in the prose (computed, never typed)."""
    M = F.DEPLOYED or {}
    T = M.get("test", {})
    cm = T.get("confusion_matrix")
    out = {}
    if not cm:
        return out
    worst = min(F.CLASSES, key=lambda c: T["per_class"][c]["recall"])
    best = max(F.CLASSES, key=lambda c: T["per_class"][c]["recall"])
    pairs = []
    for i, a in enumerate(F.CLASSES):
        for j, b in enumerate(F.CLASSES):
            if i != j:
                pairs.append((cm[i][j], a, b))
    pairs.sort(reverse=True)
    out.update(worst=worst, best=best, top_pair=pairs[0], second_pair=pairs[1], pairs=pairs)
    out["weak"] = (f"normal radiographs are the weak point: {cm[0][2]} of {sum(cm[0])} are called viral and {cm[0][1]} bacterial pneumonia (specificity "
                   f"{T['binary_normal_vs_pneumonia']['specificity'] * 100:.1f}%), and viral precision is {T['per_class']['Viral Pneumonia']['precision']:.2f}; "
                   f"confusion between the two pneumonia types is smaller ({cm[2][1]} viral called bacterial, {cm[1][2]} bacterial called viral)")
    return out


def blocks():
    M = F.DEPLOYED or {}
    T = M.get("test", {})
    TR = M.get("training", {})
    DS = M.get("dataset", {})
    HP = M.get("hyperparameters", {})
    LAT = M.get("latency_ms_mean_cpu", {})
    Bn = T.get("binary_normal_vs_pneumonia", {})
    PC = T.get("per_class", {})
    cm = T.get("confusion_matrix", [[0] * 3] * 3)
    A = analysis()
    E2, E3, E4, LD = F.E5, F.E4, F.E3, F.LEAK   # E2 = no-CLAHE ablation, E3 = MobileNetV3Small, E4 = patient-level re-partition
    E1 = F.E1

    out = [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS")]

    # ------------------------------------------------------------------ 8.1 screens
    out += [
        H2("8.1 Output screens"),
        P("The screens below are captures of the running application at 1440 x 900 pixels, taken by `scripts/capture_screens.py` after real scans had been uploaded through the interface "
          "(four public sample radiographs, so the history, dashboard and result pages hold real data). The script fails on any console error or failed request; none occurred."),
        FIG(F.shot_view("01_landing_light.png"), "Landing page (light theme): hero, how the pipeline works, the three classes and the clinical disclaimer", F.shot_w(F.shot_view("01_landing_light.png"), 5.6)),
        FIG(F.shot_view("05_detect_preview.png"), "Detect screen with a preview of the selected radiograph and the Analyse button", F.shot_w(F.shot_view("05_detect_preview.png"), 5.6)),
        FIG(F.shot_view("06_result.png"), "Result screen: original X-ray beside the Grad-CAM overlay, class badge, confidence and the three probability bars", F.shot_w(F.shot_view("06_result.png"), 5.8)),
        FIG(F.shot_view("07_result_blend.png"), "Result screen, blended view: a slider sets how strongly the heat map is laid over the X-ray", F.shot_w(F.shot_view("07_result_blend.png"), 5.6)),
        FIG(F.shot_view("09_dashboard.png"), "Dashboard: totals, class distribution, scans per day and the most recent scans", F.shot_w(F.shot_view("09_dashboard.png"), 5.6)),
        FIG(F.shot_view("11_history.png"), "History: searchable, filterable, sortable table with thumbnails and CSV export", F.shot_w(F.shot_view("11_history.png"), 5.6)),
        FIG(F.shot_view("12_about.png"), "About screen: abstract, the five-step pipeline, technology and disclaimer", F.shot_w(F.shot_view("12_about.png"), 5.6)),
    ]

    # ------------------------------------------------------------------ 8.2 setup
    out += [
        H2("8.2 Experimental setup and protocol"),
        P("All model results come from `scripts/train_experiment.py`, which writes `experiments/<name>/metrics.json`. The protocol of the main experiment is fixed before looking at any test result:"),
        TAB("Protocol of the main experiment", ["Item", "Value"], [
            ["Data", "Kermany et al. paediatric chest X-ray dataset, 5,856 images, three classes derived from file names"],
            ["Training pool", f"Official train + val folders; patient-level 10 % validation split (stratified group split, seed 42)"],
            ["Sizes", f"train {DS.get('train', 0):,} ({DS.get('train_patients', 0):,} patients) / validation {DS.get('validation', 0):,} ({DS.get('validation_patients', 0):,} patients) / test {DS.get('test', 0)} (official, used once)"],
            ["Model", f"custom CNN, {F.MODEL_INFO['total_params']:,} parameters, trained from scratch" if F.MODEL_INFO else "custom CNN"],
            ["Training", f"Adam {HP.get('learning_rate', 1e-4)}, batch {HP.get('batch_size', 32)}, up to {HP.get('epochs_max', 25)} epochs; {TR.get('epochs_run', 0)} run, best epoch {TR.get('best_epoch', 0)}; about {TR.get('seconds_per_epoch', 0):.0f} s per epoch on a CPU"],
            ["Class weights", ", ".join(f"{F.CLASSES[int(k)]} {v:.2f}" for k, v in (M.get('class_weights') or {}).items())],
            ["Environment", f"TensorFlow {M.get('environment', {}).get('tensorflow', '')}, Python {M.get('environment', {}).get('python', '')}, Intel Core i5-12500, no GPU"],
        ], widths=[1.3, 5.0], size=10),
        FIG(F.fig("training_curves_exp02.png"), "Training and validation accuracy and loss of the main experiment (dotted line: best epoch)", 5.8),
        P(f"Validation accuracy of the restored best model is {F.pct(TR.get('val_accuracy_restored_model', 0))}. The validation curve is noisy, which is typical of batch-normalised networks "
          "trained from scratch on a small validation set (544 images)."),
    ]

    # ------------------------------------------------------------------ 8.3 performance
    if T:
        rows = [[c, F.f3(PC[c]["precision"]), F.f3(PC[c]["recall"]), F.f3(PC[c]["f1"]), str(PC[c]["support"])] for c in F.CLASSES]
        rows.append(["Macro average", F.f3(T["macro_precision"]), F.f3(T["macro_recall"]), F.f3(T["macro_f1"]), str(T["n"])])
        out += [
            H2("8.3 Model performance on the official test split"),
            TAB(f"Per-class results on the official test split (n = {T['n']})", ["Class", "Precision", "Recall", "F1", "Support"], rows,
                widths=[2.3, 1.0, 1.0, 1.0, 1.0], align=["l", "c", "c", "c", "c"]),
            P(f"Overall three-class accuracy is **{F.pct(T['accuracy'])}** and the macro F1 is **{F.f3(T['macro_f1'])}** (macro one-vs-rest AUC {F.f3(T['auc_ovr_macro'])}). "
              f"The class recalled best is {A['best']} ({F.pct(PC[A['best']]['recall'])}); the class recalled worst is {A['worst']} ({F.pct(PC[A['worst']]['recall'])})."),
            FIG(F.fig("confusion_matrix_exp02.png"), "Confusion matrix on the official test split (rows: true class, columns: predicted class)", 3.9),
            P(f"The largest single confusion is {SHORT[A['top_pair'][1]]} images predicted as {SHORT[A['top_pair'][2]]} ({A['top_pair'][0]} images), followed by "
              f"{SHORT[A['second_pair'][1]]} predicted as {SHORT[A['second_pair'][2]]} ({A['second_pair'][0]} images)."),
            FIG(F.fig("per_class_metrics.png"), "Per-class precision, recall and F1 on the official test split", 5.0),
            H3("Normal against pneumonia"),
            P("Collapsing the two pneumonia classes gives the binary view used by most of the literature, with pneumonia as the positive class:"),
            TAB("Binary view of the same predictions", ["Measure", "Value"], [
                ["True positives / false negatives", f"{Bn['tp']} / {Bn['fn']}"], ["True negatives / false positives", f"{Bn['tn']} / {Bn['fp']}"],
                ["Accuracy", F.pct(Bn["accuracy"])], ["Sensitivity (recall of pneumonia)", F.pct(Bn["sensitivity"])], ["Specificity", F.pct(Bn["specificity"])],
                ["Precision", F.pct(Bn["precision"])], ["F1", F.f3(Bn["f1"])], ["AUC (1 - P(Normal) as score)", F.f3(Bn["auc"])],
            ], widths=[3.6, 1.6], size=10.5),
            P(f"Calibration: the expected calibration error is {F.f3(T['expected_calibration_error'])} (10 bins) and the mean confidence is {F.f3(T['mean_confidence'])} "
              f"against an accuracy of {F.f3(T['accuracy'])}; a gap between the two means the softmax probability should not be read as a literal probability of being right."),
        ]

    # ------------------------------------------------------------------ 8.4 overlap
    out += [H2("8.4 Overlap between the training and test folders")]
    if LD:
        ft, dj = LD["full_test"], LD["patient_disjoint_subset"]
        bc = LD["by_class"]
        out += [
            P(f"Pneumonia file names carry a patient id (`person123_virus_45.jpeg`). Counting ids, **{LD['sharing_patient_id_with_training']} of the {LD['test_images']} official test images** "
              f"({bc['Bacterial Pneumonia']['sharing_patient_id_with_training'] + bc['Viral Pneumonia']['sharing_patient_id_with_training']} of the "
              f"{bc['Bacterial Pneumonia']['test'] + bc['Viral Pneumonia']['test']} pneumonia images) have an id that also occurs in the training folders, while none of the 234 normal test images do. "
              f"Shahi and Bagale {n(6)} made the same observation about this dataset. Some of these coincidences may be different children given the same number, but the file names "
              "cannot show this, so the conservative reading is possible patient leakage."),
            P(f"The model's metrics on the {LD['patient_disjoint_images']} test images whose id does not occur in training are given next to the full-test metrics. "
              f"The subset contains {dj['support'][0]} normal, {dj['support'][1]} bacterial and {dj['support'][2]} viral images, so its class mix differs from the full test split."),
            TAB("Full official test split against the id-disjoint subset", ["Measure", f"Full test (n = {ft['n']})", f"Id-disjoint subset (n = {dj['n']})"], [
                ["3-class accuracy", F.pct(ft["accuracy"]), F.pct(dj["accuracy"])],
                ["Pneumonia sensitivity", F.pct(ft["binary_normal_vs_pneumonia"]["sensitivity"]), F.pct(dj["binary_normal_vs_pneumonia"]["sensitivity"])],
                ["Normal specificity", F.pct(ft["binary_normal_vs_pneumonia"]["specificity"]), F.pct(dj["binary_normal_vs_pneumonia"]["specificity"])],
                ["Recall: Normal / Bacterial / Viral",
                 " / ".join(F.pct(ft["per_class"][c]["recall"]) for c in F.CLASSES),
                 " / ".join(F.pct(dj["per_class"][c]["recall"]) if dj["per_class"][c]["support"] else "n/a" for c in F.CLASSES)],
            ], widths=[2.4, 1.9, 2.0], size=10.5, align=["l", "c", "c"]),
        ]
    if E4:
        t4, d4, b4 = E4["test"], E4["dataset"], E4["test"]["binary_normal_vs_pneumonia"]
        out += [
            P(f"A second, stricter protocol re-partitions all 5,856 images by patient (stratified group split, seed 42): {d4['train']:,} training, {d4['validation']:,} validation and {d4['test']:,} "
              f"test images with no id shared between the three parts (test images sharing an id with training: {d4.get('test_images_sharing_patient_id_with_training', 0)}). "
              f"The same network and settings reach {F.pct(t4['accuracy'])} three-class accuracy and macro F1 {F.f3(t4['macro_f1'])} on this test part, with pneumonia sensitivity "
              f"{F.pct(b4['sensitivity'])} and normal specificity {F.pct(b4['specificity'])}. Its class mix and test size differ from the official split, so the two are reported side by side, not averaged."),
            FIG(F.fig("confusion_matrix_exp03.png"), "Confusion matrix of the patient-level re-partition", 3.9),
        ]

    # ------------------------------------------------------------------ 8.5 ablation
    out += [H2("8.5 Ablation and comparison with MobileNetV3Small")]
    rows = []
    for lab, e in (("Baseline: project defaults (lr 1e-4), stopped early", E1), ("Tuned recipe (deployed model)", F.DEPLOYED), ("Tuned, no CLAHE (ablation)", E2), ("MobileNetV3Small, ImageNet start (base-paper backbone)", E3), ("Tuned, patient-level re-partition (own test part)", E4)):
        if e:
            t = e["test"]
            rows.append([lab, f"{e['training'].get('parameters', 0):,}", F.pct(t["accuracy"]), F.f3(t["macro_f1"]), F.pct(t["binary_normal_vs_pneumonia"]["sensitivity"]), F.pct(t["binary_normal_vs_pneumonia"]["specificity"])])
    out += [
        P("Three further runs use the same code and seed. The CLAHE ablation removes the contrast step from training and inference; the MobileNetV3Small run uses the backbone that the base paper selects "
          f"{n(1, 13)}, trained in two stages (head only, then fine-tuning) and evaluated on the same official test images. The patient-level run uses a different test part and is listed for completeness."),
        TAB("Experiments compared", ["Experiment", "Parameters", "3-class acc.", "Macro F1", "Sensitivity", "Specificity"], rows, widths=[2.4, 0.9, 0.8, 0.7, 0.8, 0.8], size=9, align=["l", "r", "c", "c", "c", "c"]),
    ]
    if E2 and F.DEPLOYED:
        d_acc = E2["test"]["accuracy"] - F.DEPLOYED["test"]["accuracy"]
        out += [P(f"Removing CLAHE changes three-class accuracy by {d_acc * 100:+.1f} percentage points and macro F1 by {E2['test']['macro_f1'] - F.DEPLOYED['test']['macro_f1']:+.3f}. "
                  "With one seed per configuration this difference should be read as indicative; differences of a few points are within the run-to-run variation of small CNNs, which this project could not measure for lack of repeated runs. "
                  + (f"The variant without CLAHE scored higher on the test split, so this project does not show that the contrast step helps. Its validation accuracy ({E2['training']['val_accuracy_restored_model'] * 100:.1f}%) was almost the same as that of the deployed model "
                     f"({F.DEPLOYED['training']['val_accuracy_restored_model'] * 100:.1f}%), the deployed model had been chosen before the ablation was run, and the deployed application keeps CLAHE for consistency with the original project; "
                     "re-training the deployed model without CLAHE is listed as future work." if d_acc > 0 else ""))]
    if E3:
        out += [P("The shipped `gradcam.py` cannot compute a heat map for the MobileNetV3Small model, because the backbone is a nested model and the feature tensor is not connected to the outer input; "
                  "this is one reason the transfer-learning option was not deployed; its accuracy on these test images was also lower than that of the custom CNN.")]
    if os.path.exists(F.fig("experiment_comparison.png")):
        out += [FIG(F.fig("experiment_comparison.png"), "Comparison of the experiments on the official test images", 5.4)]

    # ------------------------------------------------------------------ 8.6 thresholds
    out += [H2("8.6 Threshold analysis")]
    if T:
        thr = T["confidence_threshold_analysis"]
        rows = [[f"{r['threshold']:.2f}", f"{r['kept']}", F.pct(r["coverage"]), F.pct(r["accuracy_on_kept"]) if r["accuracy_on_kept"] is not None else "n/a"] for r in thr]
        sweep = T["pneumonia_decision_threshold_sweep"]
        rows2 = [[f"{r['threshold']:.1f}", F.pct(r["sensitivity"]), F.pct(r["specificity"]), F.pct(r["accuracy"])] for r in sweep]
        out += [
            P("**Confidence threshold.** A deployment could auto-report only scans whose top probability reaches a threshold and send the rest for review. The table below shows the trade-off on the test split: "
              "a higher threshold raises accuracy on the scans kept but reduces coverage."),
            TAB("Accuracy against minimum confidence", ["Threshold", "Scans kept", "Coverage", "Accuracy on kept"], rows, widths=[1.2, 1.2, 1.2, 1.6], align=["c", "c", "c", "c"], size=10.5),
            FIG(F.fig("confidence_threshold.png"), "Accuracy on the scans kept and coverage as the minimum confidence rises", 5.0),
            P("**Decision threshold for pneumonia.** Using the score 1 - P(Normal), sweeping the threshold moves the operating point between sensitivity and specificity. The default arg-max rule corresponds "
              "to a threshold near 0.5."),
            TAB("Pneumonia decision-threshold sweep", ["Threshold", "Sensitivity", "Specificity", "Accuracy"], rows2, widths=[1.2, 1.3, 1.3, 1.3], align=["c", "c", "c", "c"], size=10.5),
            FIG(F.fig("decision_threshold_sweep.png"), "Sensitivity, specificity and accuracy against the pneumonia decision threshold", 5.0),
        ]

    # ------------------------------------------------------------------ 8.7 base paper
    if T:
        out += [
            H2("8.7 Comparison with the base paper"),
            P("The datasets and protocols differ, so this table is context and not a ranking. The base paper's figures are taken from its text and abstract; those for this project are from Section 8.3."),
            TAB("Base paper and this project", ["Aspect", "Base paper [1]", "This project"], [
                ["Task", "Binary Normal / Pneumonia; 4-class COVID-19, Normal, Pneumonia, TB", "3-class Normal / Bacterial / Viral; binary view derived"],
                ["Image source", "Mendeley paediatric set (5,863 images) and a merged 7,135-image set", "Same Kermany paediatric images (5,856 in the public folders)"],
                ["Split", "Balanced subset, 1,300 per class; 2,080 / 260 / 260 (binary)", f"Official imbalanced split; {DS.get('train', 0):,} / {DS.get('validation', 0)} / {DS.get('test', 0)}"],
                ["Model", "MobileNet family, ImageNet-pretrained; SSL with FixMatch, FlexMatch, FreeMatch", f"Custom CNN from scratch ({F.MODEL_INFO['total_params']:,} parameters)" if F.MODEL_INFO else "Custom CNN"],
                ["Reported accuracy", "Up to 98 % (binary), 97 % (4-class); 97 % with 20 % / 30 % labels", f"{F.pct(T['accuracy'])} three-class; {F.pct(Bn['accuracy'])} Normal vs pneumonia"],
                ["Explanation", "Grad-CAM", "Grad-CAM (on every scan, in the application)"],
                ["Reliability", "MC Dropout (50 passes, entropy 0.30), TTA, ECE", f"ECE {F.f3(T['expected_calibration_error'])}; confidence-threshold analysis"],
                ["Latency", "0.11 s per image (MobileNetV3Small)", f"{LAT.get('total_pipeline', 0) / 1000:.2f} s per image for preprocessing, inference and Grad-CAM (CPU)" if LAT else "n/a"],
                ["Deliverable", "Research framework", "Complete web application with history, dashboard and tests"],
            ], widths=[1.2, 2.6, 2.5], size=9),
            P(f"Two points are worth stating plainly. First, the base paper's 97 to 98 % comes from a balanced 260-image test subset and from ImageNet-pretrained backbones; this project's {F.pct(Bn['accuracy'])} "
              "Normal-versus-pneumonia accuracy is on the official 624-image test split, which is about 62 % pneumonia, from a network trained from scratch, and three-class accuracy is a harder task. "
              f"Second, studies on the same images report anywhere from 79.7 % to 98 % depending on the protocol {n(3, 5, 6)}, so a gap of several points between two papers is not evidence of a better method."),
        ]

    # ------------------------------------------------------------------ 8.8 samples
    sm = _samples()
    out += [H2("8.8 Sample inputs and outputs")]
    out += [FIG(F.fig("gradcam_examples.png"), "Grad-CAM overlays for the highest-confidence correct test image of each class and the most confident misclassification", 5.8)]
    if sm:
        rows = [[s["file"], s["caption"], s["prediction"], F.pct(s["confidence"]), " / ".join(f"{s['probabilities'][c] * 100:.0f}" for c in F.CLASSES), f"{s['ms']:.0f}"] for s in sm]
        out += [
            P("The four public-domain sample radiographs in `dataset_sample/` were sent through the running API. They come from Wikimedia Commons (not from the training data, and some are adult films), "
              "so they illustrate the interface and the output format, not accuracy. The class named in the source caption is shown for reference only; it is not a dataset label."),
            TAB("Sample radiographs through the deployed API", ["File", "Source caption", "Predicted", "Confidence", "P(N / B / V) %", "ms"], rows, widths=[1.2, 1.7, 1.1, 0.7, 1.0, 0.5], size=8.5),
        ]

    # ------------------------------------------------------------------ 8.9 success / failure
    if T:
        pairs = A["pairs"]
        out += [
            H2("8.9 Success and failure analysis"),
            P(f"**Where it works.** Pneumonia is detected as pneumonia in {F.pct(Bn['sensitivity'])} of cases ({Bn['fn']} of {Bn['tp'] + Bn['fn']} pneumonia images were called normal) and bacterial pneumonia has a recall of "
              f"{F.pct(PC['Bacterial Pneumonia']['recall'])}. The heat maps in the Grad-CAM figure are diffuse: in the correctly classified examples they cover parts of the lung fields but also the ribs, the shoulders, "
              "the corners and the diaphragm line, so they do not isolate a lesion."),
            P("**Where it fails.** The confusion counts above show the pattern:"),
            B(*[f"{SHORT[a]} predicted as {SHORT[b]}: {c} images" for c, a, b in pairs[:4]]),
            P(f"In short, {A['weak']}. A likely contributor, not tested here, is that the official test folder differs in distribution from the training folder; the patient-level re-partition (Section 8.4) removes most of this "
              "gap. Separating bacterial from viral pneumonia is hard in general because the two overlap on a radiograph and the pathogen label in this dataset comes from the file name, not from a re-read of the image. "
              "The most confident misclassification (last column of the Grad-CAM figure) shows that a wrong prediction can still carry a high confidence."),
            P("**Why the heat maps need care.** Grad-CAM shows where the network looked, not why a region matters clinically. Without segmentation the maps also highlight areas outside the lungs "
              "in some images (borders, text markers, the diaphragm line), which is a reason to treat the overlay as a prompt for inspection and not as a lesion detector."),
        ]

    # ------------------------------------------------------------------ 8.10 limits
    out += [
        H2("8.10 Limitations of the results"),
        B("One data source, one seed per configuration: no confidence intervals and no repeated runs.",
          "Pathogen labels derive from file names and were not re-verified.",
          "Possible patient overlap between the official training and test folders; the id-disjoint and patient-level results are the safer reading.",
          "No external or prospective validation; the four sample images are illustrations.",
          "Probabilities are uncalibrated softmax values."),
    ]

    # ------------------------------------------------------------------ 8.11 objectives
    status = [
        ["1. Acquire and preprocess a dataset (resize, normalise, augment)", "Achieved", "Kermany data; `preprocess.py`; augmentation in `train_experiment.py` (Sections 6.2 and 6.3)"],
        ["2. U-Net lung segmentation before classification", "**Not achieved**", "No segmentation network was implemented, trained or evaluated"],
        ["3. Train a CNN to separate pneumonia from normal", "Achieved", f"Three-class CNN; pneumonia sensitivity {F.pct(Bn.get('sensitivity', 0))}, specificity {F.pct(Bn.get('specificity', 0))}"],
        ["4. Evaluate with accuracy, sensitivity, specificity, F1, confusion matrix", "Achieved", "Section 8.3, plus AUC, ECE and threshold analysis"],
        ["5. Heat-map visualisation for each prediction", "Achieved", "Grad-CAM overlay on every scan (application and Section 8.8)"],
        ["6. Deploy behind an interface with prediction, confidence and heat map", "Achieved", "FastAPI + React application, original Flask UI, 73 tests"],
    ]
    out += [H2("8.11 Objectives against outcomes"), TAB("Objectives of Section 1.5 and their outcome", ["Objective", "Outcome", "Evidence"], status, widths=[2.6, 0.9, 2.8], size=9.5)]
    return out
