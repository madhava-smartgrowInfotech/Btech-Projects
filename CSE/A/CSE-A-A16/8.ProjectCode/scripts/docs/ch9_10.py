"""Novelty, contributions, scope, limitations, walkthroughs, decisions, conclusion (Chapter 9) and future scope (Chapter 10)."""

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB


def src(rel, start=None, end=None):
    """Lines start..end (1-based, inclusive) of a source file of 8.ProjectCode, for code listings."""
    import os

    lines = open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    return "\n".join(lines[(start or 1) - 1:end or len(lines)]).rstrip("\n")


# ------------------------------------------------------------------ document 9
def novelty_blocks():
    return [
        P("SignSpeak does not propose a new learning algorithm, and we do not claim one. Its building blocks (convolution, batch normalisation, dropout, Adam, Otsu thresholding, majority voting) are standard. "
          "What is new is the combination, the way it is delivered and the care with which it is measured. This section states the difference from the base paper first and then lists what is, and is not, new."),
        H2("2.1 Difference from the base paper"),
        TAB("SignSpeak and the base paper compared", ["Dimension", "Base paper (MAG-KD) [1]", "SignSpeak", "What differs"],
            [["Problem", "Compress a skeleton-based sign recogniser for edge devices", "Read fingerspelling letters live and turn them into text and speech", "Different task: SignSpeak is an end-to-end assistive tool for letters"],
             ["Input", "2D skeleton sequences from a pose estimator", "Binary hand mask of a fixed region of a single frame", "No pose estimator, no temporal model; classical segmentation"],
             ["Core technique", "Multi-teacher knowledge distillation with a hard correctness mask and an adaptive gate", "A small CNN trained directly", "No distillation; the base paper's central idea is not used"],
             ["Evaluation", "AUTSL and WLASL-100, three seeds, Jetson Nano profiling", "Held-out split of 7,250 images, one seed, CPU latency", "Much weaker statistics; no unseen-signer test"],
             ["Deliverable", "A training method and an edge-deployment study", "A running application with collection, training, recognition and speech", "SignSpeak adds the usable system around the model"]],
            widths=[1.0, 1.9, 1.9, 1.8], align=["l", "l", "l", "l"], size=9),
        P("The batch documents describe the project as reusing the base paper's technique. In fairness to the paper, we state what was actually taken from it: its *motivation* (real-time sign recognition on modest hardware, as a "
          "communication aid) and its attention to measured speed. Its *method* was not reproduced, because it addresses a different input (skeleton sequences) and a different problem (word signs in video)."),
        H2("2.2 What is standard and what is new"),
        TAB("Standard components and project-specific elements", ["Element", "Standard or new", "Comment"],
            [["Convolution + batch norm + dropout + Adam", "Standard", "Textbook components [7], [19], [20], [21]"],
             ["Otsu threshold, morphology", "Standard", "Classical segmentation [17], [18]"],
             ["Shared preprocessing for collection, training and live use", "Design choice", "Removes train/serve mismatch"],
             ["Confidence gate + 15-frame vote + 18-frame stability + repeat guard", "Project-specific", "Turns noisy frame labels into typed letters; its trade-off is measured (Chapter 8)"],
             ["Browser-owned camera with a cover-crop/mirror/JPEG protocol and a one-request-at-a-time loop", "Project-specific", "Gives the server a frame whose ROI matches the box drawn on screen; bounds the load"],
             ["Web and desktop front ends over one set of modules", "Project-specific", "The API contains no model logic; both interfaces use the same code"],
             ["In-application collect, train and report loop", "Project-specific", "A user can build a personal model without leaving the browser"],
             ["Honest evaluation: near-duplicate analysis, threshold curve, robustness, latency, test suite", "Project-specific", "States which numbers are optimistic and which are headline"]],
            widths=[2.8, 1.2, 2.6], align=["l", "c", "l"], size=9.5),
    ]


def contribution_blocks():
    t = F.T
    return [
        P("The key contributions, in the order in which the evidence supports them, are:"),
        N("**An end-to-end ASL fingerspelling system** - camera, segmentation, CNN, temporal decision logic, sentence builder and speech - delivered as a desktop and a web application that share one code path.",
          f"**A measured baseline.** A 2.20-million-parameter CNN reaches {F.pct(t['accuracy'], 2)} accuracy, macro F1 {F.f3(t['macro_f1'])} and top-3 accuracy {F.pct(t['top3_accuracy'])} on a held-out split of {t['n']:,} images, with per-class results and the most frequent confusions.",
          f"**A quantified decision rule.** At the 0.75 confidence threshold, {F.pct(F.thr_row(0.75)['coverage'])} of frames are accepted and {F.pct(F.thr_row(0.75)['accuracy_on_accepted'])} of them are correct; the full curve is reported.",
          f"**Real-time evidence on a CPU.** {F.LAT['server_side_total_per_frame']['median_ms']:.1f} ms per frame on the server and {F.LAT['http_recognize_frame_round_trip']['median_ms']:.1f} ms over HTTP (about {F.LAT['http_round_trip_fps_sequential']} frames per second), with the stage-by-stage breakdown.",
          "**A frank evaluation.** Robustness to brightness, noise, blur and rotation; an explanation of why the dataset's near-duplicate frames inflate some numbers; objectives reported as met, partly met or not met.",
          f"**Engineering quality.** {F.PYTEST_TOTAL} automated tests, a {F.SMOKE_TOTAL}-check end-to-end smoke test, a measurement script that regenerates every reported number, and a verifier for the documentation."),
    ]


# ------------------------------------------------------------------ document 10
def scope_blocks():
    return [
        P("The scope is what the delivered system does and was tested to do. Each in-scope item exists in the code base and is covered by the evidence named in the last column."),
        TAB("In scope", ["Capability", "Detail", "Evidence"],
            [["Alphabet recognition", "26 letters + `space`, `del`, `nothing` (29 classes) from a live camera", "Chapter 8: 82.81 % held-out accuracy"],
             ["Preprocessing", "ROI crop, grayscale, blur, Otsu, morphology, 64x64 normalisation", "10 unit tests; figure in Chapter 6"],
             ["Training", "In-application training with augmentation, early stopping and reports", "Smoke test; saved 30-epoch run"],
             ["Live decisions", "Confidence 0.75, vote of 15, 18 stable frames, repeat guard", "7 unit tests; threshold curve"],
             ["Sentence and speech", "Space, delete, clear, speak; offline voice with a browser fallback", "Screens; API tests"],
             ["Data collection", "Single and burst capture of 200x200 images per class", "Smoke test (80 images); screen capture"],
             ["Interfaces", "React web application (landing + 6 screens) and the original desktop application", "Browser walk at 360-1440 px"],
             ["Measurement", "Accuracy, per-class scores, confusion, threshold, robustness, latency", "`scripts/measure_metrics.py`"]],
            widths=[1.5, 3.3, 1.8], align=["l", "l", "l"], size=9.5),
        H2("1.1 Out of scope"),
        B("**Words and sentences in sign language.** Only the manual alphabet is recognised; there is no vocabulary of word signs and no sentence-level or grammatical modelling.",
          "**Motion.** J and Z are traced in the air; the system reads one frame, so it does not model their motion.",
          "**Two hands, two-way translation and other sign languages.** One hand in one box; text-to-sign translation is not provided; only ASL letters are covered.",
          "**Mobile and embedded deployment.** The system runs on a personal computer; no phone, Jetson or browser-only inference was built.",
          "**Accounts, multi-user operation and cloud hosting.** The application is single-user and local; the API has no authentication.",
          "**Clinical or educational validation.** No field trial with deaf users or interpreters, no usability study, no certification as an assistive device."),
    ]


def assumption_blocks():
    return [
        P("The results hold under these assumptions; where one fails, accuracy is expected to fall."),
        B("**One hand in the box.** The signer places one hand inside the 300x300 box drawn on the camera view; anything outside it is ignored.",
          "**Reasonable light and a plain background.** The segmentation assumes the hand is the main bright or dark region of the box; cluttered backgrounds put extra shapes in the mask.",
          "**Upright hand.** The training data show hands in the poses of the dataset; a tilt of 10 degrees already costs about 17 accuracy points.",
          "**A steady sign.** A letter is typed only after about 18 stable frames, so signs must be held for around a second.",
          "**Same kind of data as training.** The reported accuracy applies to images like those of the recorded dataset; a new signer, camera or room is outside the evidence.",
          "**Modern PC.** Windows, Python 3.10/3.11, Node.js 18 or newer, Chrome or Edge on `localhost`, a webcam and speakers. Speed figures are for the measured i5-12500 machine."),
    ]


def limitation_blocks():
    return [
        P("The limitations below are real and affect how the system should be used. Each is listed with its effect and with what could reduce it."),
        TAB("Limitations", ["No.", "Limitation", "Effect", "What would help"],
            [["L1", "Dataset: frames from video of a few recordings, near-duplicate neighbours, no signer ids", "Test accuracy (82.81 %) is for held-out frames of the same recordings; accuracy on new people is unknown and expected lower", "A signer-disjoint dataset or new recordings of several people"],
             ["L2", "Only 250 of 3,000 images per class used (7,250 of 87,000)", "Possible under-fitting; the 30-epoch run was still improving", "Train on more or all images; longer runs"],
             ["L3", "Otsu segmentation keeps background structure", "The CNN partly learns the scene; clutter hurts", "Skin-colour or landmark-based hand isolation"],
             ["L4", "Orientation sensitivity (85.0 % to about 68 % at +/-10 degrees)", "Tilted hands are misread", "Rotation-aware augmentation; hand alignment"],
             ["L5", "Static letters only; J and Z read from one frame", "No words; the two motion letters are not truly recognised", "A sequence model on hand landmarks"],
             ["L6", "Hardware: CPU only; `model.predict` costs 50 ms", "About 17.6 frames per second end to end", "Direct model call, export, quantisation, browser-side inference"],
             ["L7", "One training run, one seed, no ablation", "No confidence interval; design choices (Otsu, 64x64, dropout rates) not compared", "Repeated runs and ablations"],
             ["L8", "Live webcam not exercised; fake camera only", "Camera hook untested against real hardware variety", "Tests on several physical webcams"],
             ["L9", "No authentication, open CORS", "Safe only on one machine; not for a network", "Add authentication and restrict origins before sharing"],
             ["L10", "No user study", "Usability and acceptance for deaf and hearing users unknown", "A small study with signers"]],
            widths=[0.4, 2.1, 2.2, 1.9], align=["c", "l", "l", "l"], size=9),
    ]


def not_measured_blocks():
    return [
        P("Honesty about gaps matters more than a longer list of numbers. The following were **not measured**, and nothing in these documents should be read as a claim about them:"),
        B("accuracy on signers who are not in the dataset, and on new backgrounds or lighting;",
          "accuracy of typed *words* (letter error rate of whole sentences) with real signers;",
          "behaviour on a physical webcam (only Chromium's fake camera, fed with real photographs, was used);",
          "the wall-clock time of the saved 30-epoch training run (a separate 2-epoch benchmark gave about 9.9 s per epoch);",
          "power use, memory use under load, and behaviour under many simultaneous users;",
          "alternative architectures, hyper-parameter settings, skin-colour segmentation or landmark input;",
          "usability, accessibility with assistive technologies, and acceptance by the deaf community."),
        P("The 87.24 % accuracy on other photos of the archive was measured, but it is optimistic for the reason given in Chapter 8 and is not used as the headline."),
    ]


# ------------------------------------------------------------------ document 12
def walkthrough_blocks():
    return [
        P("This section walks through the code that carries the design. The listings are copied from the repository."),
        H2("3.1 Segmentation: from a colour crop to a hand mask"),
        CODE(src("sign_language_app/preprocessing.py", 47, 60), 8.5),
        P("`segment_threshold` applies Otsu's method to the blurred grey crop. Otsu picks the threshold that best separates the two modes of the histogram, so it adapts to the exposure of each frame. If more than half of "
          "the result is white, the polarity is wrong (a bright background was labelled foreground) and the mask is inverted so that the hand is always the minority white region. An opening removes isolated specks and two "
          "closings fill small gaps in the silhouette. The unit test `test_segmentation_marks_hand_as_foreground` checks both polarities."),
        H2("3.2 The network"),
        CODE(src("sign_language_app/model.py", 18, 50), 8.5),
        P("Three convolution blocks (32, 64, 128 filters) each end in 2x2 max pooling, so a 64x64 mask becomes an 8x8x128 map. Batch normalisation follows every convolution and the first dense layer. Dropout of 0.25 after blocks 2 and 3 and "
          "0.4 before the output fights over-fitting of the large dense layer. The model compiles with Adam and categorical cross-entropy, as the formulation of Chapter 6 requires."),
        H2("3.3 Training with augmentation and early stopping"),
        CODE(src("sign_language_app/train.py", 55, 83), 8.5),
        P("The augmenter perturbs the training images only; validation and test images are untouched. `restore_best_weights` returns the best validation epoch when early stopping fires, and the checkpoint keeps the best "
          "model on disk. In the saved run the cap of 30 epochs was reached first, so the final weights are those of epoch 30."),
        H2("3.4 Frame in, decision out"),
        CODE(src("backend/main.py", 249, 267), 8.5),
        P("The endpoint checks that a model is loaded (409) and that the session exists (404), decodes and resizes the frame, crops the ROI and calls the session's recogniser under the model lock. The response carries "
          "everything the interface needs: the raw label and confidence, the smoothed label, the committed letter and the mask."),
        H2("3.5 The browser capture loop"),
        CODE(src("frontend/src/pages/Recognize.tsx", 63, 100), 8.5),
        P("The loop runs while the camera is on and a session exists. It grabs a frame, awaits the answer, and waits for the remainder of 60 ms, so there is only ever one request in flight and never more than "
          "about 16 per second. A 404 (the server forgot the session after a restart) opens a new session automatically."),
    ]


def decision_blocks():
    return [
        P("Each decision below is stated with the alternative that was available and the reason for the choice."),
        TAB("Implementation decisions", ["Decision", "Alternative", "Reason"],
            [["Wrap the original desktop modules in FastAPI instead of rewriting them", "Port the logic into the API", "One code path; the web app cannot drift from the tested desktop logic; less code"],
             ["Camera in the browser (`getUserMedia`)", "Server-side OpenCV camera streamed to the page", "No native camera code; works with any browser camera; the user sees a normal permission prompt"],
             ["Send 960x540 JPEG frames (quality 0.8, about 27 KB)", "Raw frames or smaller crops", "Matches the desktop geometry so the same ROI box applies; small enough for localhost"],
             ["One request in flight, at least 60 ms apart", "Fire-and-forget at a fixed rate", "Bounded load; no queue of stale frames; latency never grows"],
             ["64x64 binary mask input", "Colour crop at 128x128 or more", "Small network, 10 s per epoch on a CPU; the mask removes skin tone and lighting differences"],
             ["Otsu threshold with polarity check", "Skin-colour (YCrCb) mask; hand landmarks", "No extra model; adaptive per frame. Known weakness: clutter. Skin mode exists in code but was not evaluated"],
             ["Three conv blocks, dense 256", "Deeper or pretrained network", "Fast enough for live use on a CPU; adequate accuracy; keeps the model small enough to retrain on a laptop"],
             ["Stratified 70/15/15 split, seed 42", "Signer-wise split", "The dataset has no signer ids; the split is reproducible and class-balanced"],
             ["Confidence 0.75 + vote of 15 + 18 stable frames", "Take the single-frame argmax", "Filters noise and transition frames; costs about a second of hold time"],
             ["File-system storage, no SQL database", "SQLite", "The data are image files and a model; no queries to answer; one fewer dependency"],
             ["Server voice (pyttsx3) with a browser-voice fallback", "Browser voice only", "Offline and consistent where available; the fallback keeps Speak working"],
             ["Keep the desktop application", "Delete it", "It is the original deliverable and the reference implementation for the web version"]],
            widths=[2.2, 1.8, 2.6], align=["l", "l", "l"], size=9.5),
    ]


# ------------------------------------------------------------------ chapters 9 and 10
def conclusion_blocks():
    t = F.T
    thr = F.thr_row(0.75)
    return [
        H2("9.1 Summary"),
        P("SignSpeak is a working sign language recognition system for the ASL manual alphabet. A browser camera feeds frames to a FastAPI service that crops a hand region, segments it with Otsu's method, "
          "resizes it to 64x64 and classifies it with a three-block CNN of 2,199,453 parameters. A temporal rule (confidence 0.75, majority of 15, 18 stable frames) decides when a letter is typed; the letters form a sentence "
          "that can be spoken. The application also collects images, trains models and shows their performance. It runs on one CPU-only PC."),
        H2("9.2 Objectives achieved"),
        P("Of the six objectives, three were met (preprocessing with segmentation and augmentation, a trained CNN, text and speech output) and three were met in part: the dataset covers the alphabet and control signs "
          "but not common words; real-time operation is achieved at about 17.6 frames per second on a CPU without model optimisation; and evaluation covers accuracy, per-class performance and latency but not unseen signers. "
          "Chapter 8 gives the table."),
        H2("9.3 Key findings"),
        N(f"A compact CNN on a 64x64 Otsu mask reads held-out frames of the dataset with {F.pct(t['accuracy'], 2)} accuracy (macro F1 {F.f3(t['macro_f1'])}, top-3 {F.pct(t['top3_accuracy'])}).",
          f"Confidence is informative: at the 0.75 threshold the system accepts {F.pct(thr['coverage'])} of frames and is right on {F.pct(thr['accuracy_on_accepted'])} of them, so rejecting low-confidence frames is an effective filter.",
          "Errors concentrate in look-alike signs (V with W and U, E with B and A, S with Y) and in rotated or brighter images (accuracy 85.0 % falls to about 68 % at +/-10 degrees of rotation).",
          f"The system is fast enough to be used live on a CPU: {F.LAT['server_side_total_per_frame']['median_ms']:.1f} ms per frame on the server, {F.LAT['http_round_trip_fps_sequential']} frames per second end to end; the CNN call is 95 % of the server time.",
          "Numbers measured on a random split of video frames are optimistic: other photos of the same archive score 87.24 %, but near-duplicate frames explain part of that, so the held-out 82.81 % is the figure we report.",
          "A single code path for desktop and web, backed by 52 tests, made it possible to rebuild the interface without touching the recognition logic."),
        H2("9.4 Practical applications"),
        B("A fingerspelling aid for a signer to spell a name or a technical term to a hearing person, with the sentence shown and spoken.",
          "A teaching tool for learners of the ASL alphabet, who can check whether a hand shape is read as intended.",
          "A platform for building personal or local-variant models: the Collect and Train screens let a user capture their own hands and retrain.",
          "A base for classroom exercises on the whole machine-learning cycle: data, preprocessing, training, evaluation and deployment."),
        H2("9.5 Known limitations"),
        P("The system recognises letters only, was evaluated on held-out frames of the same recordings as the training set and not on unseen signers, is sensitive to rotation and cluttered backgrounds, was tested end to end with a fake camera, "
          "has no authentication, and has had no user study. It is a research and teaching prototype, not a certified assistive device. Section 8.8 and the limitation table of the scope document give the full list."),
    ]


def future_blocks():
    return [
        H2("10.1 Improvements to the recogniser"),
        B("**Unseen-signer evaluation first.** Record several signers in several rooms (or use a dataset with signer identifiers), split by signer, and report that accuracy as the headline; this is the most important missing measurement.",
          "**More data and a proper search.** Use more than 250 images per class, longer runs and a small hyper-parameter search; add ablations of the preprocessing (Otsu against skin mask against none) and of the dropout rates.",
          "**Better hand isolation.** Replace Otsu by a hand-landmark detector such as MediaPipe [13] and classify the landmarks (or crop around them), which would remove most background structure and bring SignSpeak closer to the skeleton idea of the base paper [1].",
          "**Orientation robustness.** Rotation-aware augmentation beyond 12 degrees, or normalising the hand's orientation, to address the drop to about 68 % at 10 degrees of tilt.",
          "**Calibrated confidence.** Temperature scaling so that a confidence of 0.8 means about 80 % right, and a per-user threshold."),
        H2("10.2 Additional features"),
        B("**Words and phrases.** A sequence model over landmarks or frames (for example a small temporal CNN or a graph network) trained on a word-level dataset such as WLASL [15] or AUTSL [14], with a vocabulary beyond the alphabet.",
          "**Motion letters.** Recognise J and Z from a short window of frames instead of one frame.",
          "**Two-way communication.** Add speech-to-text so that a hearing person's reply is shown to the signer.",
          "**Personalisation.** A short calibration that fine-tunes the model on a new user's hand in a minute.",
          "**Languages and voices.** Other sign alphabets and text-to-speech voices."),
        H2("10.3 Scalability and deployment"),
        B("**Faster inference.** Call the model directly instead of `model.predict`, export to a lighter runtime and quantise; the 50 ms CNN call is the main cost. Running the model in the browser (for example with TensorFlow.js) would remove the server round trip.",
          "**Edge devices.** Port to a phone or a Jetson-class board; the base paper's ONNX and TensorRT workflow [1] is a template, and its power and speed profiling would give a fair comparison of hardware cost.",
          "**Packaging and sharing.** Container image, authentication and restricted origins before any network use; a persistent session store if several users are to share one server.",
          "**Continuous evaluation.** Run the measurement script and the 52 tests in a CI pipeline so that every model change is evaluated automatically."),
        H2("10.4 Further research"),
        B("Apply knowledge distillation, the base paper's technique [12], [1], to compress a stronger teacher into the small student used here, and measure the accuracy-latency trade-off on the same held-out and unseen-signer data.",
          "Study how much of the accuracy comes from the hand and how much from the scene by training on masks with the background removed.",
          "Run a user study with deaf and hearing participants to measure typing speed, error rate and acceptance."),
    ]


def chapter9_blocks():
    return [H1("CHAPTER 9: CONCLUSION")] + conclusion_blocks()


def chapter10_blocks():
    return [H1("CHAPTER 10: FUTURE SCOPE")] + future_blocks()
