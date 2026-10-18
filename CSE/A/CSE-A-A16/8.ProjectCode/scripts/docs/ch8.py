"""Chapter 8: Results and Output Screens (also document 14)."""

import os
import re

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB
from .lit import OBJECTIVES

_ROW = re.compile(r"^\s*(\S+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s*$")


def report_rows():
    rows = {}
    for line in open(os.path.join(F.MODELS, "classification_report.txt"), encoding="utf-8"):
        m = _ROW.match(line)
        if m and m.group(1) in F.CLASSES:
            rows[m.group(1)] = (float(m.group(2)), float(m.group(3)), float(m.group(4)), int(m.group(5)))
    return rows


def screen(name, caption, base=5.0, max_h=3.2):
    p = F.shot(name)
    return FIG(p, caption, F.shot_w(p, base, max_h))


def screens_blocks():
    """Every working screen with real data (the light-theme and phone captures are in Appendix C)."""
    return [
        H2("8.2 Output screens"),
        P("All screens below are real captures (1440x900) of the application running on the development PC with the trained model loaded and the 7,250-image working dataset in `data/`. "
          "The Recognize capture was made with Chromium's fake camera fed with a clip assembled from real held-out ASL photos, because the build machine has no webcam; for each letter the clip uses the first of 12 photos "
          "that the live model reads correctly with at least 0.8 confidence, so that the demonstration is legible. The Model screen shows the true held-out accuracy."),
        H3("8.2.1 Landing page"),
        screen("01_landing_dark.png", "Landing page (dark theme): tagline, pipeline illustration (ROI crop, segmentation, CNN, sentence) and the statistics strip."),
        P("The landing page introduces SignSpeak (\"Sign it. See it. Hear it.\"), says that it reads American Sign Language letters from a webcam with a convolutional neural network, types them into a sentence and speaks it, and shows the pipeline as three small panels. "
          "Below the fold a strip shows the live figures of this installation (29 classes, 7,250 images, 29 of 29 classes with data, 82.8 % test accuracy)."),
        screen("01b_landing_features_dark.png", "Landing page: the four features (collect, train, recognize, speak) and the reference to the base paper."),
        H3("8.2.2 Dashboard"),
        screen("03_dashboard.png", "Dashboard: model ready, 7,250 images, 29 of 29 classes, 82.8 % test accuracy, images per class and the last training run."),
        P("The dashboard summarises the state of the system in one view: whether a model is loaded, the number of stored images (7,250, the same as the training set), the classes covered (29 of 29), the model's held-out "
          "accuracy (82.8 %), a bar chart of images per class and the last training run."),
        H3("8.2.3 Live recognition"),
        screen("04_recognize.png", "Recognize screen: letter H recognised at 87 %, the segmentation mask the network sees, and the sentence built so far."),
        P("The large letter and the confidence bar update with every frame; the mask panel shows the 300x300 region after segmentation, which is exactly what the network classifies (after resizing). The sentence "
          "(\"HELLOH\" in this capture) is built by committed letters; space, back, clear and speak are the controls beneath it. The trailing H is the fake-camera clip starting over."),
        H3("8.2.4 Data collection"),
        screen("05_collect.png", "Collect screen: ROI box on the camera view, class L selected, \"Captured 5 images for L\", mask preview and recent captures."),
        P("The user picks a class, aligns the hand in the box and captures one image or a burst; each capture is saved as a 200x200 PNG in `data/<class>/` and the thumbnail list and counts update at once."),
        H3("8.2.5 Training"),
        screen("06_train.png", "Train screen: dataset coverage of 7,250 images, hyper-parameter fields and the finished run (82.8 % test accuracy)."),
        screen("06b_train_charts.png", "Train screen: live accuracy and loss charts of the run."),
        P("The screen refuses to start with fewer than two classes, validates the hyper-parameters, shows data-loading and per-epoch progress, plots training and validation accuracy and loss while the run proceeds, "
          "and ends with the test accuracy. The charts are those of the saved run."),
        H3("8.2.6 Model performance"),
        screen("07_model_per_class.png", "Model screen: test accuracy and the per-class precision, recall and F1 table."),
        screen("07b_model_confusion.png", "Model screen: confusion matrix of the 1,088 test images."),
        screen("07c_model_curves.png", "Model screen: training curves."),
        P("The Model screen reads the saved reports, so it always shows the numbers of the model that is loaded. It is the in-application counterpart of Sections 8.3 and 8.4."),
        H3("8.2.7 About"),
        screen("08_about.png", "About screen: abstract, the eight pipeline steps and the base paper."),
    ]


def blocks():
    T, R = F.T, report_rows()
    b = [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS")]
    b += [H2("8.1 Experimental setup and protocol"),
          P(f"All figures in this chapter come from `docs/metrics/metrics.json`, written by `scripts/measure_metrics.py` from the saved model and the saved training files, on {F.ENV['cpu']} with {F.ENV['ram_gb']} GB RAM and no GPU "
            f"(Python {F.ENV['python']}, TensorFlow {F.ENV['tensorflow']}). The headline protocol is the **held-out test split**: of the 7,250 working images, 15 % (**{F.DS['test']:,} images, 37-38 per class**) were set aside by a stratified split "
            "with seed 42 and were never used for training or for choosing the model. We reproduced the saved test result independently from the model and the same seed: accuracy 0.8281 and loss 0.5569, identical to "
            "the training run's own report."),
          P("**What this protocol does and does not show.** The images are frames from video, so a random split puts neighbouring, almost identical frames in training and test. The result therefore measures how well "
            "the model reads held-out frames of the recorded signers and scenes. It is not a test on unseen signers (the archive has no signer identifiers), and the real-world accuracy of the system for a new "
            "person in a new room is expected to be lower. Every number below is stated with its protocol.")]
    b += screens_blocks()
    b += [H2("8.3 Model performance"),
          P("The first table gives the summary and the second the per-class scores of the held-out test split."),
          TAB("Held-out test split (n = 1,088)", ["Metric", "Value"],
              [["Accuracy", f"**{F.pct(T['accuracy'], 2)}** ({T['accuracy']:.4f})"], ["Loss (cross-entropy)", f"{T['loss']:.4f}"], ["Macro F1", f"{T['macro_f1']:.4f}"], ["Weighted F1", f"{T['weighted_f1']:.4f}"],
               ["Top-3 accuracy", F.pct(T["top3_accuracy"], 2)], ["Best classes (F1)", "nothing 0.99, C 0.96, Q 0.96, G 0.93, K 0.93"],
               ["Weakest classes (F1)", "Y 0.62, V 0.69, X 0.69, U 0.70, W 0.70, E 0.70"]],
              widths=[2.4, 4.0], align=["l", "l"], size=10.5),
          FIG(F.fig("f02_per_class.png"), "F1 of each of the 29 classes on the test split, beside accuracy on other archive photos (optimistic).", 5.8)]
    rows = []
    for c in F.CLASSES:
        p, r, f1, n = R[c]
        rows.append([c, f"{p:.2f}", f"{r:.2f}", f"{f1:.2f}", str(n)])
    # two-column layout of the per-class table to save space
    half = (len(rows) + 1) // 2
    merged = []
    for i in range(half):
        left = rows[i]
        right = rows[i + half] if i + half < len(rows) else ["", "", "", "", ""]
        merged.append(left + right)
    b += [TAB("Per-class precision, recall, F1 and support (test split)", ["Class", "P", "R", "F1", "n", "Class", "P", "R", "F1", "n"], merged,
              widths=[0.75, 0.5, 0.5, 0.5, 0.45, 0.75, 0.5, 0.5, 0.5, 0.45], align=["l", "c", "c", "c", "c", "l", "c", "c", "c", "c"], size=9.5),
          P("The classes that the network finds hardest are letters whose hand shapes are close to others in a binary mask: Y (F1 0.62), V, X, U, W and E. The control class `nothing` (an empty box) is "
            "almost perfect (0.99), which matters because it is what keeps the system silent when no hand is shown."),
          H3("8.3.1 Confusion matrix and the most frequent confusions"),
          FIG(F.fig("f03_confusion_matrix.png"), "Confusion matrix of the 1,088 test images (rows true, columns predicted).", 4.6),
          FIG(F.fig("f04_top_confusions.png"), "The most frequent confusions: V read as W (7), E as B (7), V as U (6), S as Y (6).", 4.6),
          P("The matrix is concentrated on the diagonal. The off-diagonal mass is made of visually similar signs: V with W and U (extended fingers differing in spread), E with B and A (closed fingers versus a flat hand), "
            "S with Y. A human reader would expect these pairs to be the ones that are confused; the net does not make random errors.")]

    thr = F.thr_row(0.75)
    b += [H2("8.4 Confidence threshold analysis"),
          P("The recogniser accepts a prediction only if its confidence is at least 0.75; otherwise the frame counts as `nothing`. The test split shows what this buys. If every frame were accepted, 82.81 % would be correct. "
            f"With the threshold at 0.75, {F.pct(thr['coverage'])} of the frames are accepted and **{F.pct(thr['accuracy_on_accepted'])}** of those are correct; the rest are ignored and the user simply holds the sign a little longer. "
            "The trade-off is shown in the figure and the table."),
          FIG(F.fig("f05_threshold.png"), "Share of frames accepted and accuracy on the accepted frames for confidence thresholds from 0 to 0.99.", 5.0),
          TAB("Confidence threshold trade-off (test split)", ["Threshold", "Frames accepted", "Accuracy on accepted frames"],
              [[f"{r['threshold']:.2f}" + (" (used)" if abs(r["threshold"] - 0.75) < 1e-9 else ""), F.pct(r["coverage"]), F.pct(r["accuracy_on_accepted"])] for r in F.THR],
              widths=[1.6, 1.8, 2.4], align=["c", "c", "c"], size=10.5),
          P("A higher threshold gives cleaner letters but makes the signer wait; at 0.95 only 48.9 % of frames pass. The threshold of 0.75 was chosen by design before these measurements and sits in the middle of the curve. "
            "Together with the 15-frame vote and the 18-frame stability rule (about a second at 17-19 frames per second), it is what turns a 82.8 % frame-level classifier into a keyboard that makes few wrong letters. "
            "We did not measure the letter error rate of whole typed words with real signers; that would need a user study.")]

    b += [H2("8.5 Other evidence"),
          P(f"**Other archive photos.** {F.UNSEEN['n']:,} further photos of the same archive (100 per class) that were never copied into `data/` give {F.pct(F.UNSEEN['accuracy'], 2)} accuracy "
            f"(macro F1 {F.UNSEEN['macro_f1']:.4f}, top-3 {F.pct(F.UNSEEN['top3_accuracy'], 2)}). This number is **optimistic and is not used as the headline**: the photos come from the same recordings, and the training set took "
            "every 12th frame, so many of these photos are near neighbours of trained frames."),
          P(f"**Official Kaggle test photos.** The archive's own 28-image test set is read correctly in **{F.OFFICIAL['correct']} of {F.OFFICIAL['n']}** cases. The two errors are A read as S (confidence 0.675) and I read as D (0.734). "
            "Twenty-eight images is far too few to estimate accuracy; the result is a sanity check.")]

    b += [H2("8.6 Comparison with the base paper"),
          P("The base paper [1] (MAG-KD) and SignSpeak solve different problems, so the comparison below is context, not a ranking, and **no claim of superiority is made**. MAG-KD recognises isolated *word* signs from *video* by "
            "classifying sequences of 2D skeletons with a graph network distilled from three teachers, and is evaluated on large benchmarks with several random seeds. SignSpeak recognises *static fingerspelling letters* "
            "from single frames with a plain CNN on a CPU and is evaluated once on a held-out split of a single dataset."),
          TAB("SignSpeak against the base paper (different tasks, data and hardware)", ["Aspect", "Base paper [1]", "SignSpeak (this work)"],
              [["Task", "Isolated sign (word) recognition from video", "Static fingerspelling letters (A-Z) and three control signs from single frames"],
               ["Input representation", "2D skeleton sequences from a pose estimator (27 joints)", "Binary hand mask, 64x64, from classical segmentation"],
               ["Model", "STA-GCN student distilled from SL-GCN, CTR-GCN and TD-GCN teachers (MAG-KD)", "3-block CNN, 2.20 M parameters, no distillation"],
               ["Data", "AUTSL: 38,336 videos, 43 signers, 226 signs; WLASL-100", "Kaggle ASL Alphabet subset: 7,250 images, 29 classes, no signer labels"],
               ["Reported accuracy", "94.25 +/- 0.19 % Top-1 (AUTSL, 0.48 M parameters); 66.33 +/- 0.54 % (WLASL-100)", "82.81 % on a random held-out split (1,088 images); no unseen-signer test"],
               ["Statistical care", "Three seeds, mean and standard deviation", "One seed, one run"],
               ["Hardware and speed", "NVIDIA Jetson Nano, TensorRT FP16: 33.13 FPS at 6.23 W", f"Intel i5-12500 CPU, TensorFlow: {F.LAT['http_round_trip_fps_sequential']} FPS end to end ({F.LAT['http_recognize_frame_round_trip']['median_ms']:.0f} ms per frame); power not measured"],
               ["Deliverable", "Training method and edge deployment study", "Working application: camera, recognition, sentence, speech, collection, training"]],
              widths=[1.3, 2.6, 2.7], align=["l", "l", "l"], size=9.5),
          P("What can be said fairly: both works are motivated by real-time sign recognition on modest hardware, and both report speed on the hardware they used. What cannot be said: that either accuracy is better, "
            "because one is a 226-way word problem on video and the other a 29-way letter problem on stills. The base paper's decisive ideas (distilling several teachers with a correctness mask, skeleton input) are not used in SignSpeak; "
            "Chapter 9 states what SignSpeak does contribute.")]

    fc = F.FAILS
    b += [H2("8.7 Success and failure analysis"),
          H3("8.7.1 Where it works"),
          P("The network is strongest on shapes that are distinct in the mask: C, Q, G and K, and the empty-box class `nothing` (F1 0.99). With a clean mask, a steady hand and the box well filled, the live screen reads "
            "a letter at confidences of 0.85 or more (the Recognize capture shows H at 87 %), and the vote-and-hold logic then types it once."),
          H3("8.7.2 Where it fails"),
          FIG(F.fig("f11_failure_cases.png"), "Confident mistakes on other archive photos: the raw crop, the mask and the wrong reading.", 5.8),
          P(f"Of {fc['sampled']:,} other archive photos examined for failures, {fc['wrong']} ({fc['wrong'] / fc['sampled'] * 100:.1f} %) were read wrongly. The most confident mistakes include "
            + "; ".join(f"{e['true']} read as {e['predicted']} at {e['confidence']:.3f}" for e in fc["examples"][:4])
            + ". A wrong reading can therefore carry a high confidence, so the threshold reduces but cannot remove wrong letters."),
          B("**Look-alike signs.** V, U, W and R differ in finger spread; E, S and A are closed fists differing in thumb position. The mask has little to separate them.",
            "**Background structure in the mask.** Otsu does not isolate the hand on a cluttered background, and the network partly learns the scenes it was trained on (Chapter 6).",
            "**Rotation.** Tilting the hand by 10 degrees lowers accuracy from 85.0 % to about 68 % (Chapter 7).",
            "**Motion letters.** J and Z are drawn in the air; a single frame cannot show the motion, so they are read from their start pose only (their F1 here is 0.89, so the dataset's J and Z images can be told apart from single frames, but the real motion is not captured).",
            "**Brightness.** A 1.5 times brighter image drops accuracy to 73.3 %; darker and noisier images matter little.")]

    b += [H2("8.8 Limitations of the results"),
          B("No evaluation on unseen signers, new backgrounds or a physical webcam; the held-out split shares recordings with the training set.",
            "A single run with one seed; no confidence interval and no comparison of alternative architectures, preprocessing choices or hyper-parameters.",
            "Training used 250 of the 3,000 available images per class; more data was not tried.",
            "The 87.24 % figure on other archive photos is inflated by near-duplicate frames and should not be quoted as the accuracy.",
            "Latency was measured on one CPU with one client; power use was not measured."),
          ]

    ach = [
        ["1", OBJECTIVES[0], "**Partly.** Alphabet plus three control classes: 7,250 working images from the public archive, and the in-app collection tool. Common words: not done (static letters only)."],
        ["2", OBJECTIVES[1], "**Done.** ROI crop, Otsu segmentation, 64x64 normalisation, training-time augmentation. Weakness: segmentation does not isolate the hand on cluttered backgrounds."],
        ["3", OBJECTIVES[2], "**Done.** 3-block CNN, 2.20 M parameters, 82.81 % held-out accuracy."],
        ["4", OBJECTIVES[3], f"**Partly.** {F.LAT['http_round_trip_fps_sequential']} frames per second end to end on a CPU with no model optimisation; the CNN call dominates ({F.LAT['cnn_forward_batch1']['median_ms']:.0f} ms). No quantisation or export was tried."],
        ["5", OBJECTIVES[4], "**Done.** Sentence builder with space, back and clear; offline speech (pyttsx3) with a browser-voice fallback."],
        ["6", OBJECTIVES[5], "**Partly.** Accuracy, per-class precision/recall/F1, confusion matrix, robustness and latency are measured. **Unseen signers: not done**; the archive has no signer identifiers."],
    ]
    b += [H2("8.9 Objectives against outcomes"),
          TAB("Objectives (from the project's objectives document) against outcomes", ["No.", "Objective", "Outcome"], ach, widths=[0.4, 2.5, 3.7], align=["c", "l", "l"], size=9.5),
          P("Objectives 2, 3 and 5 are met, and objectives 1, 4 and 6 are met in part. The gaps are stated so that they can be closed: words need a video or sequence model and a new dataset; "
            "unseen-signer evaluation needs a dataset with signer identifiers or new recordings of several people; inference speed can be raised with a lighter inference path.")]
    return b
