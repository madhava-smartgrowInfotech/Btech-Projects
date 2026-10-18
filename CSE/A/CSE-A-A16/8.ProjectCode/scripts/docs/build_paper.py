"""Builds 19.IEEE_Paper.docx (two-column, 6 pages) for SignSpeak from facts.py (metrics.json), the diagrams and the screenshots.

    python -m scripts.docs.build_paper            # from 8.ProjectCode, system python
"""

import os

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from PIL import Image

from . import facts as F
from .kit import add_runs, set_font
from .paper import FONT, Paper

pct, f3 = F.pct, F.f3


def make_figures():
    """Compact figures for the paper, written to docs/figures/paper_*.png."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 13})
    out = {}
    # Fig. 3: per-class F1 (sorted) and confidence-threshold trade-off
    fig, (a, b) = plt.subplots(2, 1, figsize=(6.8, 6.6), gridspec_kw={"height_ratios": [1, 1], "hspace": 0.55})
    items = sorted(F.T["per_class_f1"].items(), key=lambda kv: kv[1])
    names = [k for k, _ in items]
    vals = [v for _, v in items]
    cols = ["#D9772F" if v < 0.75 else "#2B6CB0" for v in vals]
    a.bar(range(len(vals)), vals, color=cols)
    a.set_xticks(range(len(vals)))
    a.set_xticklabels(names, rotation=90, fontsize=11)
    a.set_ylim(0.5, 1.02)
    a.axhline(F.T["macro_f1"], color="#14907F", ls="--", lw=1.4)
    a.text(0.2, F.T["macro_f1"] + 0.012, f"macro F1 {F.T['macro_f1']:.3f}", color="#14907F", fontsize=12)
    a.set_ylabel("F1 on test split")
    a.set_title("(a) Per-class F1 (orange: below 0.75)", fontsize=13)
    a.spines[["top", "right"]].set_visible(False)
    th = [r["threshold"] for r in F.THR]
    b.plot(th, [r["coverage"] for r in F.THR], "o-", color="#2B6CB0", lw=2, label="share of frames accepted")
    b.plot(th, [r["accuracy_on_accepted"] for r in F.THR], "s-", color="#14907F", lw=2, label="accuracy on accepted frames")
    b.axvline(0.75, color="#D9772F", ls="--", lw=1.5)
    b.text(0.765, 0.36, "deployed\nthreshold 0.75", color="#D9772F", fontsize=12)
    b.set_xlabel("confidence threshold")
    b.set_ylabel("fraction")
    b.set_ylim(0.25, 1.05)
    b.legend(loc="lower left", fontsize=11, frameon=False)
    b.set_title("(b) Confidence threshold trade-off", fontsize=13)
    b.spines[["top", "right"]].set_visible(False)
    p = os.path.join(F.FIGS, "paper_results.png")
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    out["results"] = p
    # Fig. 4 / 5: real screenshots cropped to the application area
    for name, src, box in (("recognize", "04_recognize.png", (288, 85, 1410, 790)), ("curves", "07c_model_curves.png", (288, 85, 1410, 830))):
        p = os.path.join(F.FIGS, f"paper_{name}.png")
        Image.open(F.shot(src)).convert("RGB").crop(box).save(p)
        out[name] = p
    return out


def build(path):
    figs = make_figures()
    env = F.ENV
    L = F.LAT
    T = F.T
    U = F.UNSEEN
    R = F.ROB
    t75 = F.thr_row(0.75)
    t90 = F.thr_row(0.9)
    wf = F.sorted_f1()

    P = Paper()
    authors = [[n.title(), "Dept. of Computer Science and Engineering", "TKR College of Engineering & Technology", "Hyderabad, India", "[email address]"] for n, _ in F.STUDENTS]
    authors.append([F.GUIDE.title() if False else "V. Pallavi", f"{F.GUIDE_DESIGNATION}, Dept. of Computer Science and Engineering", "TKR College of Engineering & Technology", "Hyderabad, India", "[email address]"])
    P.title_block("SignSpeak: Real-Time American Sign Language Fingerspelling Recognition from a Webcam with a Convolutional Neural Network, Converted to Text and Speech", authors)
    P.begin_two_columns()

    P.abstract(
        "Sign language is the main medium of communication for many people with hearing and speech impairments, yet few hearing people understand it. "
        "This paper presents SignSpeak, a webcam-based system that recognises American Sign Language fingerspelling with a convolutional neural network, "
        "builds the letters into a sentence and speaks it aloud. Each frame is cropped to a hand region, segmented with Otsu thresholding, reduced to "
        f"64 x 64 pixels and classified by a {F.MODEL['parameters'] / 1e6:.1f}-million-parameter network into 26 letters plus space, delete and nothing; a confidence threshold and a "
        "majority vote over recent frames decide when a letter is typed. Trained on 7,250 images of a public dataset on a desktop CPU, the network reaches "
        f"{pct(T['accuracy'], 2)} accuracy on a held-out split of {T['n']:,} images, and the server pipeline needs about {L['server_side_total_per_frame']['median_ms']:.0f} ms per frame. "
        "Accuracy falls sharply when the hand is rotated by ten degrees and unseen signers were not tested, so real-world accuracy is expected to be lower. "
        "Words and motion signs are not covered.",
        ["American Sign Language", "assistive technology", "convolutional neural network", "fingerspelling", "hand gesture recognition", "image segmentation", "real-time systems"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Sign languages are the primary medium of communication for many deaf and hard-of-hearing people, but few hearing people can sign, and interpreters are "
           "scarce, costly and rarely present in spontaneous everyday exchanges {r:2,3}. Automatic sign language recognition aims to close this gap by turning "
           "camera images into text or speech. Early systems used special sensors or restricted vocabularies {r:4,5}; deep learning now classifies hand "
           "images directly {r:6,7}, and the most recent work targets video recognition of whole signs on small edge devices {r:1}.")
    P.para("Today, a deaf person who needs to talk to a hearing person who does not sign relies on a human interpreter, on writing or typing, or on a phone "
           "application; each costs time or money, and none supports a quick exchange at a counter or in a classroom. Gloves and depth cameras read hand shape "
           "well but are expensive and rarely owned, whereas a plain webcam is built into almost every laptop. Fingerspelling, which spells a word letter by letter "
           "with the 26 hand shapes of the manual alphabet, is used for names and terms that have no sign of their own {r:6}; it is a bounded task with a small "
           "number of static classes, and therefore a sensible first target for a low-cost recogniser.")
    P.para("Two practical problems remain. Many published systems stop at a trained classifier evaluated on stored images; they are not packaged as a live "
           "application that a non-expert can run, and their accuracy is reported without the conditions that matter, such as background, lighting, hand rotation "
           "and signer. Second, recognition that is accurate on a benchmark often degrades with background clutter, changing light and unseen signers, "
           "which is the situation of every real use. This paper addresses the first problem and measures part of the second.")
    P.para("The contributions are: (1) a complete, tested system that runs a live webcam loop and turns recognised letters into an on-screen sentence and "
           "synthesised speech; (2) one shared preprocessing function (region of interest, Otsu segmentation, 64 x 64 normalisation) used for data "
           "collection, training and recognition; (3) a decision rule combining a confidence threshold, majority vote and stability count that turns noisy "
           "per-frame predictions into typed letters; and (4) a measured evaluation with accuracy, per-class results, a confidence-threshold analysis, "
           "robustness to rotation, brightness and noise, and latency, stated together with what was not tested. Section II reviews related work, Section III "
           "describes the method, Section IV reports results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para(f"All training and every measurement used one desktop computer: {env['cpu'].replace('12th Gen ', '')} ({env['ram_gb']} GB RAM), no graphics card, "
           "Windows 11. A standard webcam supplies the live video; the browser captures it.")
    P.sub("B", "Software Requirements")
    P.para(f"Python {env['python']}, TensorFlow/Keras {env['tensorflow']} {{r:23}}, OpenCV {env['opencv']} {{r:24}}, NumPy {env['numpy']}, a FastAPI service for the "
           "back end, a React 18 and Vite interface for the browser, pyttsx3 for offline speech, and pytest for the automated tests.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para("**Base paper.** Vo et al. {r:1} study sign recognition on edge devices. Their input is not an image but a skeleton: a sequence of 27 upper-body and "
           "hand keypoints per frame, extracted by a pose estimator such as MediaPipe {r:13}, processed by a spatio-temporal graph convolutional network "
           "{r:11}. Their method, MAG-KD, distils three large teacher networks into a small student (0.48 M parameters): a hard correctness mask removes "
           "teacher outputs that disagree with the ground truth, and a small gating network weights the remaining teachers, following the knowledge-"
           "distillation idea of Hinton et al. {r:12}. On the AUTSL Turkish Sign Language benchmark {r:14} (38,336 videos, 43 signers, 226 signs) the student reaches "
           "94.25 +/- 0.19 % top-1 accuracy over three seeds, and 66.33 +/- 0.54 % on WLASL-100 {r:15}. Exported through ONNX and TensorRT in half precision it runs "
           "at 33.13 frames per second at 6.23 W on a Jetson Nano. The authors note two limits: the mask needs ground-truth labels, and the whole system is "
           "bounded by the speed and accuracy of the pose estimator.")
    P.para("**Related work.** Starner et al. {r:4} recognised sentence-level ASL from desk-mounted and wearable cameras with hidden Markov models; Pugeault and "
           "Bowden {r:5} classified fingerspelled letters in real time from colour and depth images of a Kinect sensor. Bheda and Radpour {r:6} applied deep "
           "convolutional networks to static images of letters and digits, building on the line of CNNs started by LeCun et al. {r:7}. Surveys {r:2,3} "
           "separate static, isolated-word and continuous recognition and list background, lighting and signer variation as open problems.")
    P.para("**From video to skeletons.** Video methods began with 3D convolutional networks {r:9}, which model motion directly but are expensive. Skeleton methods "
           "such as ST-GCN {r:11} pass only joint coordinates through a graph network, which is cheaper and less affected by background, but depends on pose estimates "
           "that jitter or drop joints in fast motion, the failure that the base paper's mask is designed to contain {r:1}. Both families take video sequences "
           "and are built for signs that move; a fingerspelled letter is nearly a static hand shape and can be classified from a single frame.")
    P.para("**Datasets.** AUTSL {r:14} and WLASL {r:15}, the benchmarks of the base paper, contain word-level signs and do not apply to fingerspelling. For letters, the "
           "Kaggle ASL Alphabet dataset {r:25} offers 29 classes of 3,000 images each. Its images are frames from video, so neighbouring images are near-duplicates "
           "and no signer identifier is given; a split by image therefore says little about unseen signers, a caveat that shapes how the results below are reported.")
    P.para("**Gap.** The base paper and most recent work address word-level recognition from video, where a pose estimator and heavy training infrastructure "
           "are assumed. What is less often delivered is the simple end-to-end path for fingerspelling: an inexpensive camera, a small image classifier, and a "
           "live application that outputs text and speech, evaluated with its conditions stated. This work targets that path and does not attempt to match "
           "video methods.")
    P.table("Representative work compared", ["Work", "Approach", "Data", "Reported result", "Limitation"], [
        ["{r:1}", "Skeleton GCN student, multi-teacher distillation", "AUTSL, WLASL-100 (video)", "94.25 % AUTSL; 66.33 % WLASL-100; 33.13 FPS", "Needs pose estimator; words, not letters"],
        ["{r:4}", "Hidden Markov models on video", "ASL sentences, small vocabulary", "Early real-time ASL", "Restricted vocabulary"],
        ["{r:5}", "Colour + depth, letter classifier", "ASL letters, Kinect", "Real-time letters", "Depth sensor needed"],
        ["{r:6}", "Deep CNN on images", "ASL letters, digits (static)", "CNN works on static letters", "No live application"],
        ["{r:14}", "Dataset and baselines", "38,336 videos, 226 signs", "Benchmark for {r:1}", "Turkish signs"],
        ["{r:3}", "Survey of deep methods", "Many datasets", "Maps the field", "No system"],
    ], widths=[0.28, 0.82, 0.72, 0.85, 0.73], size=7, align=["c", "l", "l", "l", "l"])

    P.para("Reading Table I: the closest work in method is the base paper, and the closest in task is the line from Pugeault and Bowden to Bheda and Radpour, "
           "which classifies static fingerspelled letters. The reported results come from different datasets and metrics and are not ranked here; they show the range "
           "of what has been tried, not a leaderboard. The contrast that matters for this project is the input: skeleton sequences with distillation and "
           "half-precision deployment in {r:1}, against a single segmented image and a small, unoptimised CNN here.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.para("**Architecture.** Fig. 1 shows the system. The browser owns the webcam: each frame is cover-cropped to 16:9, mirrored and drawn to a 960 x 540 canvas, "
           f"compressed to JPEG (quality 0.8, about {L['jpeg_payload_kb_mean']:.0f} KB) and posted to a FastAPI service, one request at a time and at least 60 ms apart. "
           "The service runs the same Python modules as the original desktop application: preprocessing, the network, the recogniser, speech and the "
           "training loop. Training images and the saved model are plain files; sessions are held in memory.")
    P.figure(F.diag("01_system_architecture.png"), "System architecture: browser, FastAPI service, shared recognition modules and file storage.")
    P.para("**Preprocessing.** A 300 x 300 region of interest (x 620-920, y 90-390 of the 960 x 540 frame) is cropped, converted to grayscale and smoothed with a "
           "7 x 7 Gaussian filter. Otsu's method {r:17} then picks the threshold t* that maximises the between-class variance of the grey-level histogram,")
    P.eq("t* = arg max  ω₀(t) ω₁(t) [μ₀(t) − μ₁(t)]²")
    P.para(indent=0, text="where ω₀, ω₁ are the fractions and μ₀, μ₁ the mean grey levels of the two classes. If the mean of the resulting mask exceeds 127 it is inverted so "
           "that the hand is always white; one opening and two closings with a 3 x 3 kernel remove speckle and fill holes; the mask is resized to 64 x 64 and divided "
           "by 255. The same function serves data collection, training and recognition, so training and use cannot drift apart.")
    P.para(f"**Data.** The Kaggle ASL Alphabet dataset {{r:25}} has 87,000 training images (200 x 200 pixels, 29 classes of 3,000: letters A-Z, space, delete and nothing). "
           f"Because neighbouring images are frames from video, an evenly spaced subset of 250 per class ({F.DS['images_in_data_folder']:,} images) was used, split "
           f"70/15/15 with a stratified random split (seed 42) into {F.DS['train']:,} training, {F.DS['validation']:,} validation and {F.DS['test']:,} test images. "
           "No signer identifiers are provided, so the split is by image, not by person.")
    P.para(f"**Model.** The classifier ({F.MODEL['parameters']:,} parameters, {F.MODEL['file_size_mb']} MB) has three convolution blocks of 3 x 3 kernels with 32, 64 and "
           "128 filters, each with batch normalisation {r:19}, ReLU and 2 x 2 max pooling; dropout 0.25 follows blocks two and three. The 8,192-value "
           "feature vector feeds a dense layer of 256 units (batch normalisation, dropout 0.4) and a 29-way softmax,")
    P.eq("p_k = exp(z_k) / Σ_j exp(z_j),")
    P.eq("L = −(1/N) Σ_i Σ_k y_ik log p_ik")
    P.para(indent=0, text="trained with categorical cross-entropy and the Adam optimiser {r:21} (learning rate 10⁻³, batch 32). Augmentation randomly rotates (12 degrees), shifts "
           "(10 %), zooms (12 %) and shears (8 %) the training images only; dropout {r:20} and early stopping on validation accuracy (patience 6) limit over-fitting. "
           f"A small network was chosen because it trains on a CPU, at about {F.TRAIN_SPEED['seconds_per_epoch']:.0f} s per epoch, and classifies a frame in tens of milliseconds. "
           f"The saved run used all {F.RUN['epochs']} epochs.")
    P.para("**Decision logic.** A raw per-frame prediction is not a typed letter. As Fig. 2 shows, a prediction below 0.75 confidence is replaced by nothing; the "
           "last 15 accepted labels vote; and a letter is typed only after the winning label has been stable for 18 consecutive frames, differs from the last "
           "typed letter, and is not nothing. Showing nothing resets the repeat guard, so a double letter needs the hand to be lowered between letters. Space "
           "and delete are acted on as commands. The typed sentence can be edited and read aloud by an offline speech engine, with a browser voice as fallback.")
    P.figure(F.diag("10_core_algorithm_flowchart.png"), "Per-frame flow: image pipeline (left) and decision logic (right).", width=3.0)
    P.para("**Service and implementation.** The FastAPI service exposes 16 endpoints under one prefix: health, configuration and about; dataset listing and image "
           "access; a preview of the segmentation mask; capture of training images; recognition sessions and frames; model reload; speech; training start, stop and "
           "status; and the model report. Inputs are validated (epochs 1-500, batch 1-1,024, learning rate between 10⁻⁶ and 1, at least two classes with images, "
           "image-name patterns, speech text up to 2,000 characters) and errors return clear codes. A recognition session holds one recogniser object, up to 20 "
           "at a time, and a lock serialises calls to the single TensorFlow model; training runs in a background thread with a stop flag and progress that the "
           "browser polls. The React interface offers a live recognition page with the mask preview and sentence editor, a collection page that adds labelled "
           "images, a training page with live charts, and a model-performance page with per-class scores, the confusion matrix and training curves.")
    P.para("**Evaluation protocol.** Precision (P), recall (R) and F1 are computed per class on the test split, and the macro F1 is their mean over the 29 classes,")
    P.eq("F1 = 2PR / (P + R),    macro F1 = (1/29) Σ_k F1_k.")
    P.para(indent=0, text="Top-3 accuracy counts a hit when the true class is among the three highest probabilities. For the confidence threshold, coverage is the fraction of "
           "frames whose top probability reaches the threshold and accuracy on accepted frames is measured on those frames only. Six evaluations are reported: "
           "the held-out split; 2,900 other archive photos (100 per class) that were never copied into the training folder; the 28 official Kaggle test photos; "
           "the threshold sweep; a robustness check on 580 photos (20 per class) under rotation, brightness, noise and blur; and per-stage latency over 300 frames.")
    P.para("**Design rationale.** Otsu's threshold needs no training and costs under a millisecond, but it assumes that hand and background fall into two grey-level "
           "classes; it was chosen for speed and simplicity, and its failure on cluttered scenes is measured below. A 64 x 64 input keeps the first dense layer "
           "(8,192 x 256 weights, about 2.1 million of the parameters) small enough to train on a CPU while leaving finger shapes visible. The 18-frame stability rule "
           "equals about one second at the measured 17.6 frames per second, long enough to ignore the transition between two signs and short enough to type at a "
           "natural pace. Majority voting over 15 frames, rather than averaging probabilities, stops a single confident wrong frame from changing the output.")
    P.para("**Reproducibility.** Everything uses seed 42. One script measures every figure in Section IV from the saved model and writes it to a JSON file, and "
           "re-evaluating the saved model on the regenerated split reproduced the stored test accuracy (0.8281) and loss (0.5569). The collection page of the "
           "application adds labelled images from the webcam, so the system can be retrained on a new signer or background without code changes.")
    P.para(f"**Verification.** {F.PYTEST_TOTAL} pytest tests pass: {F.PYTEST_API} on the API (validation, errors, sessions, training control), {F.PYTEST_PRE} on preprocessing, "
           f"{F.PYTEST_REC} on the recogniser's voting and commit logic with a stub model, and {F.PYTEST_DS} on dataset handling and the network. A {F.SMOKE_TOTAL}-check live smoke test "
           "against a running server (input validation, collection of 80 images, a long run stopped at epoch two, a three-epoch training run, the model report, recognition "
           "and an unknown-session error) also passes, and every screen was walked through in a browser with an emulated camera fed real dataset photos.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.para(f"**Test conditions.** The headline figure is accuracy on the {T['n']:,} test-split images, which were never used for training or model selection. Because "
           "the dataset consists of video frames from a few recordings, this is a split by image, not by signer, and it is not a test on unseen people. "
           f"Table II lists the results. Accuracy is {pct(T['accuracy'], 2)}, macro F1 {f3(T['macro_f1'])} and top-3 accuracy {pct(T['top3_accuracy'])}; training reached "
           f"{pct(F.RUN['final_train_accuracy'])} and validation {pct(F.RUN['best_val_accuracy'])} at epoch {F.RUN['best_epoch']} (the cap), so more training would probably help.")
    se = (T["accuracy"] * (1 - T["accuracy"]) / T["n"]) ** 0.5
    P.para(f"With {T['n']:,} test images the 95 % binomial interval around {pct(T['accuracy'])} is about +/-{1.96 * se * 100:.1f} points ({pct(T['accuracy'] - 1.96 * se)} to "
           f"{pct(T['accuracy'] + 1.96 * se)}); this covers sampling noise only, not the choice of split or signer. Validation accuracy exceeds training accuracy "
           "because dropout and augmentation act only on the training pass, and the validation loss, which spiked in the first epochs while batch normalisation "
           "statistics settled, was stable from epoch six.")
    P.table("Measured accuracy by protocol (one trained model)", ["Protocol", "n", "Accuracy", "Macro F1", "Top-3"], [
        ["Held-out test split (headline)", f"{T['n']:,}", pct(T["accuracy"], 2), f3(T["macro_f1"]), pct(T["top3_accuracy"])],
        ["Other archive photos (optimistic)", f"{U['n']:,}", pct(U["accuracy"], 2), f3(U["macro_f1"]), pct(U["top3_accuracy"])],
        ["Official Kaggle test photos", str(F.OFFICIAL["n"]), f"{pct(F.OFFICIAL['correct'] / F.OFFICIAL['n'])} ({F.OFFICIAL['correct']}/{F.OFFICIAL['n']})", "-", "-"],
        ["Robustness subset: clean", "580", pct(R["clean"]), "-", "-"],
        ["Rotated +10 degrees", "580", pct(R["rotate +10 deg"]), "-", "-"],
        ["Rotated -10 degrees", "580", pct(R["rotate -10 deg"]), "-", "-"],
        ["Brightness x 1.5", "580", pct(R["brightness x1.5"]), "-", "-"],
        ["Gaussian noise (s = 25)", "580", pct(R["gaussian noise s=25"]), "-", "-"],
    ], widths=[1.4, 0.35, 0.65, 0.5, 0.5], size=7, align=["l", "c", "c", "c", "c"])
    P.para(f"The 2,900 other archive photos were not copied into the training folder, but they come from the same recordings as the training images and neighbouring "
           f"frames are near-duplicates, so their {pct(U['accuracy'])} overstates generalisation and is not used as the headline. Of the 28 official Kaggle test photos, "
           f"{F.OFFICIAL['correct']} are correct (A read as S at 0.675 confidence, I as D at 0.734).")
    P.figure(figs["results"], "Per-class F1 on the test split (a) and the effect of the confidence threshold (b).")
    wk = ", ".join(f"{k} {v:.2f}" for k, v in wf[:4])
    P.para(f"**Per-class results and failures.** The easiest classes are nothing (F1 0.99), C and Q (0.96); the weakest are {wk}. The most frequent confusions are "
           f"E read as B ({F.CONFUSIONS[1]['count']} images), V as W (7), V as U (6) and S as Y (6): signs that differ by finger position or are partly occluded. "
           "J and Z are motion letters but are read from one frame here. The segmentation masks still contain background structure in cluttered scenes, so part "
           "of what the network learns may be the scene rather than the hand.")
    fc = F.FAILS
    P.para(f"**Confident errors.** A wrong letter can be shown with high confidence. In a sample of {fc['sampled']:,} archive photos, {fc['wrong']} were misread, and the "
           f"most confident errors reached {fc['examples'][0]['confidence'] * 100:.1f} % (B read as W) and {fc['examples'][1]['confidence'] * 100:.1f} % (W read as Z). "
           "Confidence therefore reduces errors but does not remove them, which is why the stability rule and an editable sentence are part of the design.")
    P.para(f"**Class difficulty.** The weakest classes are the same under two protocols: on the {U['n']:,} other photos the lowest per-class accuracies are E "
           f"({U['per_class_accuracy']['E'] * 100:.0f} %) and X ({U['per_class_accuracy']['X'] * 100:.0f} %), then U ({U['per_class_accuracy']['U'] * 100:.0f} %), which suggests that these are genuinely "
           f"hard shapes for the model and not an artefact of one split. Top-3 accuracy of {pct(T['top3_accuracy'])} against {pct(T['accuracy'])} at top-1 means the correct letter "
           "is often the runner-up, which an interface could exploit by offering the second-best letter as a one-touch correction.")
    P.para(f"**Threshold.** Requiring 0.75 confidence keeps {pct(t75['coverage'])} of test frames at {pct(t75['accuracy_on_accepted'])} accuracy (all frames: {pct(T['accuracy'])}); "
           f"0.90 keeps {pct(t90['coverage'])} at {pct(t90['accuracy_on_accepted'])}. Together with the 18-frame stability rule this suppresses most wrong letters at the cost of "
           "holding a sign for about a second.")
    P.para("**Practical reading.** With the deployed settings, about three frames in ten are discarded as uncertain and the rest are right about 97 times in 100, "
           "so a signer who holds a clear sign steady for about a second should see the correct letter typed; a hand held at an angle, a cluttered wall or a hard pair such as V "
           "and U or E and B will more often produce a wrong or missing letter, which the sentence editor lets the user correct.")
    P.para(f"**Robustness and speed.** Rotating the hand by +/-10 degrees lowers accuracy from {pct(R['clean'])} to about 68 %, and brighter light to {pct(R['brightness x1.5'])}, while "
           "blur and moderate noise change little. Per frame (median of 300): JPEG decoding "
           f"{L['jpeg_decode_960x540']['median_ms']:.2f} ms, segmentation {L['roi_crop_and_segmentation_and_normalisation']['median_ms']:.2f} ms, network {L['cnn_forward_batch1']['median_ms']:.1f} ms; "
           f"server total {L['server_side_total_per_frame']['median_ms']:.1f} ms (95th percentile {L['server_side_total_per_frame']['p95_ms']:.1f} ms) and a localhost HTTP round trip "
           f"{L['http_recognize_frame_round_trip']['median_ms']:.1f} ms, i.e. about {L['http_round_trip_fps_sequential']} frames per second, with no model optimisation.")
    P.para(f"At about {L['http_round_trip_fps_sequential']} frames per second a letter needs 18 stable frames, a little over one second, so the loop speed bounds typing to under about 60 "
           "letters per minute even when every frame is read correctly.")
    P.para("**What the tests do not show.** The browser path was exercised with an emulated camera fed real dataset photos, not a physical webcam, and no user study was "
           "run. Conditions outside the dataset's recordings, such as other cameras, lighting, hand distances and left-handed signers, were not evaluated. J and Z involve "
           f"motion in ASL but are read from one frame here, so their scores (F1 {T['per_class_f1']['J']:.2f} and {T['per_class_f1']['Z']:.2f}) describe still approximations of those signs.")
    P.figure(figs["recognize"], "Output screen: live recognition of the letter H at 87 % confidence, with the segmentation mask and the sentence being built.")
    P.figure(figs["curves"], "Output screen: model performance page with 82.8 % test accuracy and the 30-epoch training curves.")
    P.figure(F.fig("f10_preprocessing_stages.png"), "Preprocessing stages for four letters: raw region of interest, grayscale, blur, Otsu mask with morphology, and the 64 x 64 model input. "
             "Background structure (ceiling edge, wall) survives in the masks.")
    P.para(f"**Cost of training and what the masks show.** Training on the CPU took about {F.TRAIN_SPEED['seconds_per_epoch']:.1f} s per epoch in a two-epoch benchmark "
           f"(loading and preprocessing the 7,250 images took {F.DS['load_and_preprocess_seconds']:.0f} s); the wall-clock time of the saved 30-epoch run was not recorded. "
           f"The network call is {L['cnn_forward_batch1']['median_ms'] / L['server_side_total_per_frame']['median_ms'] * 100:.0f} % of the server time, so faster inference needs a lighter or exported "
           "model, not faster image code. Fig. 6 shows why the model is sensitive to the scene: Otsu's global threshold separates the hand only where it contrasts with a "
           "plain background, and in a cluttered room the mask also contains walls and edges.")
    P.para("**Threats to validity.** Every number comes from one trained model and one split with one seed; repeated splits and seeds, which would show run-to-run variation, were not run. "
           "Only 250 of the 3,000 available images per class were used, hyper-parameters were not searched, and no ablation of the preprocessing choices (for example with and "
           "without segmentation) was made, so the contribution of each step is argued, not measured. The confidence interval above reflects sampling noise on the test split only.")
    P.para(f"**Comparison with the base paper.** The comparison is context only. The base paper {{r:1}} recognises word signs from video skeletons (AUTSL: 226 signs, 94.25 %); "
           f"SignSpeak recognises 29 static classes from single images ({pct(T['accuracy'])}), with 2.2 M parameters (about 4.6 times the 0.48 M student) on a desktop CPU "
           "rather than a TensorRT-optimised Jetson Nano. Datasets, tasks, hardware and protocols differ, so no claim of superiority or inferiority is made.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para(f"SignSpeak recognises ASL fingerspelling letters from a webcam and turns them into text and speech. The network reaches {pct(T['accuracy'], 2)} on a held-out "
           "split, and a 0.75 confidence threshold with a stability rule trades speed for reliability. Against the six project objectives: (1) the dataset covers the alphabet and three control "
           "classes but not common words; (2) preprocessing with segmentation, resizing and augmentation was done; (3) the CNN was designed and trained; (4) real-time operation was only "
           f"partly met, at about {L['http_round_trip_fps_sequential']} frames per second without model optimisation; (5) text and speech output work; and (6) accuracy, per-class results and latency were "
           "measured, but not on unseen signers. Limits: images come from a few recordings, so real-world accuracy "
           "will be lower; the model is sensitive to hand rotation; only letters are covered; and the live webcam path was verified with an emulated camera only.")
    P.para("Key findings: a 2.2-million-parameter CNN on thresholded hand masks learns the alphabet well enough for a first working system; the dominant weaknesses are "
           "hand rotation and cluttered backgrounds, not speed; and a confidence threshold with a stability rule raises the accuracy of accepted letters from about 83 % to about 97 %. "
           "The evidence supports the claim of a working prototype, not of everyday-use accuracy.")
    P.para("Intended use: SignSpeak is a communication aid and a research prototype, not a certified interpreter. A wrong letter can change a message, so the sentence is shown "
           "and can be edited before it is spoken.")
    P.para("Future work: test on unseen signers and varied backgrounds; train on all 3,000 images per class with stronger augmentation (rotation, brightness); "
           "use hand-landmark detection such as MediaPipe {r:13} instead of Otsu thresholding; add words and motion signs with a sequence model; and export "
           "the network to an optimised runtime for faster inference.")

    P.references()
    P.save(path)
    return path, P.order


if __name__ == "__main__":
    out = os.path.join(F.BATCH, "19.IEEE_Paper.docx")
    path, order = build(out)
    print(path, "refs:", len(order), order)
