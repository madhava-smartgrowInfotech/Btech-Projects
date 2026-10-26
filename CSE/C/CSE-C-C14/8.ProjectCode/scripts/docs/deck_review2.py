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
    out = os.path.join(tempfile.gettempdir(), f"c14_deck_{tag}.png")
    with Image.open(F.shot(name)) as im:
        im.crop(box).save(out)
    return out


def best(h):
    """Best validation (accuracy, F1) over the epochs actually run."""
    i = max(range(len(h["val_f1"])), key=lambda k: h["val_f1"][k])
    return h["val_acc"][i], h["val_f1"][i]


def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}
    E, L, D = F.ENS, F.LATENCY, F.DATA
    ci = F.CI["ensemble"]
    C = [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE]

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: four CNN routes, logit fusion and Grad-CAM explanations",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = "This review shows how VeriVision AI is designed and built: the data and models, what is implemented, the first measured results and the open items."

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and dataset"), ("03", "Preprocessing and models"), ("04", "Training and decision logic"),
               ("05", "Data flow, database and UML"), ("06", "Technology stack"), ("07", "Implementation progress and results"),
               ("08", "Output screens and testing"), ("09", "Challenges and next steps")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "AI-generated images are realistic enough to fool people. Detectors trained on one generator often fail on another, resizing and compression remove the cues, and a bare verdict is not credible without an explanation.", K.ORANGE, "!"),
        ("Proposed system", "VeriVision AI runs four CNN routes on every uploaded image, fuses their logits with two gating rules, shows Grad-CAM heat maps, and re-tests the image after JPEG, resize and blur. All on a CPU, all local.", K.BLUE, "i"),
        ("Base paper link", "Larue et al. (CTrue) detect face deepfakes one-class. We share the aim of generalisable detection but work on general images, supervised, with explanations; HEDGE is the design reference for fusion and gating. Results are not comparable.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, 4.9, t, b_, col, gl, body_size=17)
    notes[3] = "One-minute recap of Review 1: the problem, our heterogeneous-ensemble approach, and how the base paper relates (shared aim, different scope and data)."

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.6, 1.3, 7.1, 5.6)
    K.text(s, 8.0, 1.5, 4.7, 5.3, [
        ("**Four tiers**", {"space_after": 8}),
        (f"Presentation: React and Vite web app (port {F.WEB_PORT}), six pages: landing, login, analyze, insights, models, status.", {"bullet": True}),
        (f"Application: Flask (port {F.API_PORT}); /api/analyze, /api/predict, /api/insights, demo sign-in with a signed token; PNG, JPG, JPEG, WEBP up to {F.UPLOAD_LIMIT_MB} MB.", {"bullet": True}),
        ("Inference: four PyTorch models loaded once, logit fusion, Grad-CAM, robustness variants.", {"bullet": True}),
        ("Data: checkpoints, metadata and metric JSON as files. No database.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[4] = "Routes live in app/routes.py and app/api.py; inference, fusion, explanation and robustness are separate modules so each can be tested alone. Storage is local files."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: end-to-end workflow")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.2, [("Image upload", K.NAVY), ("Validate + RGB", K.PURPLE), ("Resize + normalise", K.PURPLE), ("Four CNN routes", K.GREEN),
                                      ("Fuse + gates", K.ORANGE), ("Grad-CAM", K.BLUE), ("Robustness check", K.NAVY)], size=13, gap=0.22)
    for i, (t, b_) in enumerate([("One analysis path", "POST /api/analyze validates the image, runs the four routes and the fusion, adds three Grad-CAM overlays and the three robustness variants, and returns one JSON result."),
                                 ("Deterministic fusion", "Weighted logits plus two transparent gates; every response lists the per-route votes, active weights and gate notes, so the verdict can be audited."),
                                 ("Measured, not typed", "scripts/run_cifake_experiments.py writes every reported number to experiments/cifake/metrics.json; the Insights page and the figures read from artifacts, not from typed text.")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 3.1, 3.85, 3.6)
        K.text(s, x + 0.25, 3.25, 3.4, 0.5, t, size=20, color=K.INK, bold=True)
        K.text(s, x + 0.25, 3.9, 3.4, 2.7, b_, size=16, color=K.TXT)
    notes[5] = "Three design principles: one analysis path, auditable fusion, and numbers that come from scripts. The same pipeline serves the live app and the measurements."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Dataset used")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{D['train_real'] * 2:,} train", f"plus {D['val_real'] * 2:,} validation and {D['test_real'] * 2:,} test images, class-balanced", K.BLUE), ("32 x 32 px", "CIFAKE image size (JPEG)", K.GREEN),
                                   ("1", "generator in training data: Stable Diffusion 1.4", K.ORANGE), (f"{D['xdomain_real'] * 2}", "cross-domain probe images (other sources)", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, c, vsize=24, lsize=12)
    K.picture(s, F.fig("f01_dataset_split.png"), 0.6, 2.95, 6.3, 3.2)
    K.text(s, 7.2, 2.95, 5.5, 4.0, [
        ("CIFAKE (Bird and Lotfi): 60,000 real CIFAR-10 images and 60,000 Stable Diffusion v1.4 images; official split 100,000 train / 20,000 test.", {"bullet": True}),
        ("We use a class-balanced subset (seed 42) because training is CPU-only: validation is drawn from the train split, test from the official test split.", {"bullet": True}),
        ("Cross-domain probe: 300 real photographs and 300 AI images from another Hugging Face dataset (MIT), larger and from other generators.", {"bullet": True}),
        ("The models that shipped first were trained on synthetic demo images (100% scores, no meaning) and were replaced.", {"bullet": True}),
    ], size=14, color=K.INK, space_after=8)
    K.text(s, 0.6, 6.25, 6.3, 0.6, "Images per class in each split of the subset.", size=12, color=K.TXT, align="c", italic=True)
    notes[6] = ("Be frank about the data: 32 px images from one generator, and only 6,000 of the 100,000 training images because of CPU-only training. "
                "The cross-domain probe exists precisely to test how far the result transfers.")

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Data preprocessing and augmentation")
    wipe(s)
    K.flow(s, 0.6, 1.4, 12.13, 0.95, [("Extension and size check", K.NAVY), ("Non-empty, decodes", K.NAVY), ("Convert to RGB, >= 8 px", K.PURPLE), ("Resize 224 / 320", K.PURPLE), ("ImageNet mean / std", K.GREEN)], size=13, gap=0.25)
    rows = [["Route", "Training augmentation"],
            ["A1", "Random-resized-crop (0.8-1), flip, colour jitter"],
            ["A2", "Stronger crop (0.6-1), rotation 12, jitter, blur, noise, JPEG 40-90, down-up resize"],
            ["B, C", "Crop (0.75-1), flip, rotation 8, jitter, blur, JPEG 50-95 with p = 0.35"]]
    K.table(s, 0.6, 2.75, [1.0, 6.2], rows, font_size=14, row_h=0.8, first_bold=True)
    K.text(s, 8.1, 2.75, 4.6, 4.1, [
        ("**At inference**", {"space_after": 6}),
        ("PNG, JPG, JPEG or WEBP only, at most 10 MB, at least 8 x 8 px.", {"bullet": True}),
        ("Routes A1, A2 and C see 224 px; route B sees 320 px and is averaged with its horizontal flip.", {"bullet": True}),
        ("Uploads are decoded in memory and discarded after the reply.", {"bullet": True}),
        ("Known effect: 32 px images are up-scaled 7-10x, so detail is interpolated, not real.", {"bullet": True, "italic": True}),
    ], size=14, color=K.INK, space_after=7)
    notes[7] = "Validation rejects bad uploads with a JSON error before any model runs. Augmentation differs per route on purpose: A2 is the distortion-hardened route, B and C are moderate."

    # ---- 8 models
    s = S[7]
    set_title(s, "Models used")
    wipe(s)
    rows = [["Route", "Architecture, input, loss", "Trainable / total params", "Fusion weight"],
            ["A1", "EfficientNet-B0, 224 px, cross-entropy, normal augmentation", "1,131,954 / 4,010,110", "0.35"],
            ["A2", "EfficientNet-B0, 224 px, cross-entropy, distortion-hardened augmentation", "3,158,302 / 4,010,110", "0.15"],
            ["B", "ResNet50, 320 px, cross-entropy, flip test-time averaging", "14,968,834 / 23,512,130", "0.25"],
            ["C", "MobileNetV3-Large, 224 px, focal loss (gamma 2)", "2,185,522 / 4,204,594", "0.25"]]
    K.table(s, 0.6, 1.5, [1.0, 6.0, 3.4, 1.73], rows, font_size=14, row_h=0.8, first_bold=True, align=["c", "l", "c", "c"])
    K.tile(s, 0.6, 5.6, 3.8, 1.2, "ImageNet", "pretrained weights, upper blocks fine-tuned", K.BLUE, vsize=26)
    K.tile(s, 4.7, 5.6, 3.8, 1.2, "2 classes", "REAL (0) and AI_GENERATED (1)", K.GREEN, vsize=26)
    K.tile(s, 8.8, 5.6, 3.93, 1.2, "No GPU", "everything trains and runs on a CPU", K.ORANGE, vsize=26)
    notes[8] = "Four heterogeneous routes: two EfficientNet variants with different augmentation, a larger ResNet at higher resolution, and a light MobileNet trained with focal loss. Weights are the product's configured values, not tuned."

    # ---- 9 training configuration
    s = S[8]
    set_title(s, "Training configuration")
    wipe(s)
    ba = {k: best(F.HIST[k]) for k in F.BRANCHES}
    rows = [["Setting", "Value"],
            ["Optimiser", "AdamW, weight decay 1e-4, cosine decay; lr 3e-4 (route B 2e-4); batch 32 (B 16)"],
            ["Epochs run", "A1, A2, C: 5; B: 3 (best validation F1 at epoch 2 kept); early stopping patience 3 on validation F1"],
            ["Seeds", "A1 42, A2 43, B 44, C 45 (single run per route)"],
            ["Best validation acc. / F1", " ; ".join(f"{F.BRANCH_SHORT[k]} {ba[k][0]:.4f} / {ba[k][1]:.4f}" for k in F.BRANCHES)],
            ["Hardware and time", "Intel Core i5-12500, 16 GB, CPU only; about A1 24, A2 22, B 53, C 13 min (upper bounds, shared PC)"]]
    K.table(s, 0.6, 1.35, [2.6, 9.53], rows, font_size=13, row_h=0.46, first_bold=True)
    K.picture(s, F.fig("f04_training_curves.png"), 0.6, 4.3, 7.8, 2.65)
    K.text(s, 8.7, 4.5, 4.0, 2.4,"Training and validation loss fall for every route; route B overfits after epoch 2 (validation loss rises) and route C trains to a very low loss with a higher validation loss. One run per route, no seed study.", size=13, color=K.TXT)
    notes[9] = "Settings from scripts/common.py and the train_* scripts. Validation F1 chose the checkpoint. Only one seed per route was run, so rankings between close routes carry run-to-run uncertainty."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: logit fusion with two gates")
    wipe(s)
    K.picture(s, F.diag("10_flowchart_ensemble.png"), 0.5, 1.2, 6.4, 5.8)
    K.text(s, 7.1, 1.5, 5.6, 5.3, [
        ("**Fusion.** Weighted sum of raw logits (0.35, 0.15, 0.25, 0.25), then softmax; the larger probability is the confidence.", {"bullet": True, "space_after": 8}),
        ("**Gate 1.** Drop route B when its margin is at least 2.5 and all three other routes disagree.", {"bullet": True, "space_after": 8}),
        ("**Gate 2.** Nudge the fused logits by 0.75 toward the B + C class when B and C agree with margins of at least 2.5 and the fused direction differs.", {"bullet": True, "space_after": 8}),
        ("**Wording.** At least 0.85 High, at least 0.60 Moderate, else Low confidence.", {"bullet": True, "space_after": 8}),
        (f"**Finding.** The gates fired on {E['gate1_fired']} of 2,000 test images (Gate 1) and {E['gate2_fired']} (Gate 2); without them accuracy is {F.pct(F.VARIANTS['no_gates']['accuracy'], 2)} against {F.pct(E['accuracy'], 2)}. They did not help here.", {"bullet": True}),
    ], size=17, color=K.INK)
    notes[10] = "Weights and gate thresholds live in app/config.py and are engineering defaults, not tuned. The ablation on the same logits shows the gates are neutral on this data."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, F.diag("04_dfd_level1.png"), 0.6, 1.3, 6.2, 5.6)
    rows = [["Module", "Role"], ["preprocessing", "upload checks, RGB decode"], ["models", "four architectures, checkpoints"], ["inference", "per-route logits, flip TTA"], ["ensemble", "fusion, Gate 1, Gate 2"],
            ["explainability", "Grad-CAM overlays"], ["robustness", "JPEG, resize, blur variants"], ["api / routes", "JSON API, classic pages"], ["config", "weights, gates, limits"], ["scripts/", "prepare, train, evaluate"]]
    K.table(s, 7.1, 1.4, [2.4, 3.23], rows, font_size=13, row_h=0.5)
    notes[11] = "Level-1 data flow: validation and sign-in, preprocessing and route logits, fusion, Grad-CAM, robustness, insights, and training and evaluation, with three data stores of local files."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Data model and UML")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.6, 1.35, 6.4, 4.2)
    K.picture(s, F.diag("06_uml_class.png"), 7.2, 1.3, 5.5, 5.65)
    K.text(s, 0.6, 5.75, 6.4, 1.2, "No relational database: persisted state is four checkpoints, model_metadata.json and the evaluation JSON and PNG. The session token is signed, not stored; uploads live in memory only.", size=13, color=K.TXT, italic=True)
    notes[12] = "Honest point: the service modules are plain Python files of functions, drawn as classes in the UML to show responsibilities. There is deliberately no database for this product."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    rows = [["Layer", "Technology"],
            ["Backend", "Python 3.11.9, Flask 3.1.3, signed demo token, JSON error handlers"],
            ["Deep learning", "PyTorch 2.14.1 (CPU build), torchvision 0.29.1 with ImageNet weights: EfficientNet-B0, ResNet50, MobileNetV3-Large"],
            ["Explainability", "pytorch-grad-cam 1.5.7 (Grad-CAM), OpenCV headless 5.0, Pillow 13.0"],
            ["Data and metrics", "NumPy 2.4.6, pandas 3.0.6, scikit-learn 1.9.1, matplotlib 3.11.2, reportlab 5.1"],
            ["Front end", "React 19, Vite 8, React Router 7, Recharts, Framer Motion, GSAP (port 5414)"],
            ["Testing", "pytest 9.1.1, API smoke script, Playwright browser walk of every screen"],
            ["Hardware", "Intel Core i5-12500 (6 cores, 12 threads), 16 GB RAM, no GPU, Windows 11"]]
    K.table(s, 0.6, 1.5, [2.8, 9.33], rows, font_size=15, row_h=0.62, first_bold=True)
    notes[13] = "Everything is open source. requirements.txt pins the versions that were tested; run.bat starts both servers."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Data preparation (CIFAKE subset, cross-domain probe)", "Done", "6,000 / 1,200 / 2,000 images; 600 probe images"],
            ["Four CNN routes trained and evaluated", "Done", f"ensemble accuracy {F.pct(E['accuracy'], 2)}, single run"],
            ["Logit fusion, Gate 1 and Gate 2", "Done", "gates fired 7 and 0 times: no gain"],
            ["Grad-CAM on three routes, robustness re-check", "Done", "qualitative only; consistency k/n shown"],
            ["Flask API and React web app (6 pages)", "Done", f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} smoke checks; 19 screenshots"],
            ["Automated tests", "Done, partial", f"{F.PYTEST_PASSED} of {F.PYTEST_TOTAL} pytest; no unit tests of Grad-CAM or robustness"],
            ["Cross-generator generalisation", "Not achieved", f"cross-domain accuracy {F.pct(F.XD['ensemble']['accuracy'])}, AUC {F.XD['ensemble']['roc_auc']:.3f}"],
            ["Seed study, Grad-CAM faithfulness, GPU run, user study", "Not done", "listed as future work"]]
    K.table(s, 0.6, 1.4, [5.2, 1.75, 5.18], rows, font_size=13, row_h=0.6)
    notes[14] = "State of the code base. The honest gaps: cross-generator generalisation was measured and not achieved, and the seed study, Grad-CAM faithfulness test and user study were not done."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results")
    wipe(s)
    for i, (v, l, c) in enumerate([(F.pct(E["accuracy"], 2), f"ensemble accuracy, held-out test (n = {E['n_samples']:,})", K.BLUE), (F.f4(E["f1"]), "ensemble F1 score", K.GREEN),
                                   (F.f4(E["roc_auc"]), "ensemble ROC-AUC", K.ORANGE), (F.pct(F.XD["ensemble"]["accuracy"]), "cross-domain accuracy: chance level", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    K.picture(s, F.fig("f02_branch_metrics.png"), 0.6, 2.9, 6.0, 3.3)
    K.picture(s, F.fig("f08_robustness.png"), 6.75, 2.9, 6.0, 3.3)
    K.text(s, 0.6, 6.25, 12.1, 0.75, f"Single run, seed 42, CIFAKE subset (32 px, one generator). 95% CI for accuracy {ci[0]:.3f} to {ci[1]:.3f}; the ensemble's edge over route A1 is not statistically distinguishable. It over-predicts AI-generated (false-positive rate {F.pct(E['fpr'])}). Resize and blur cut accuracy to about 58 to 61%.", size=12, color=K.TXT)
    notes[15] = ("Four headline numbers, each with its caveat. 92.35 percent accuracy and ROC-AUC 0.9865 on 2,000 CIFAKE test images; the same models score 51.0 percent, AUC 0.499, on full-resolution photographs "
                 "and AI images from other sources, so cross-generator generalisation, objective 4, was measured and not achieved.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    cw, ch_ = 5.6, 2.56
    x1, x2, y1, y2 = 0.6, 7.13, 1.25, 4.2
    K.picture(s, crop("07_result_verdict.png", (264, 290, 1412, 700), "s07"), x1, y1, cw, ch_, border=True)
    K.picture(s, crop("08_result_votes_robustness.png", (290, 77, 1412, 589), "s08"), x2, y1, cw, ch_, border=True)
    K.picture(s, crop("09_result_gradcam.png", (292, 160, 1412, 672), "s09"), x1, y2, cw, ch_, border=True)
    K.picture(s, crop("11_insights.png", (292, 100, 1412, 612), "s11"), x2, y2, cw, ch_, border=True)
    cap = dict(size=11, color=K.TXT, italic=True)
    K.text(s, x1, y1 + ch_ + 0.03, cw, 0.3, "Verdict card: label, confidence, 4/4 branches agree (CIFAKE test image).", **cap)
    K.text(s, x2, y1 + ch_ + 0.03, cw, 0.3, "Per-route votes and the robustness consistency check.", **cap)
    K.text(s, x1, y2 + ch_ + 0.03, cw, 0.3, "Grad-CAM: original image and heat map for the EfficientNet route.", **cap)
    K.text(s, x2, y2 + ch_ + 0.03, cw, 0.3, "Model insights: held-out metrics read from the evaluation artifacts.", **cap)
    notes[16] = "Real screenshots of the running application with the CIFAKE-trained models. They show the interface, not proof of correctness: the verdicts on single images are only as reliable as the measured test results."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.PYTEST_PASSED} / {F.PYTEST_TOTAL}", "pytest tests passed", K.GREEN), (f"{F.SMOKE_PASSED} / {F.SMOKE_TOTAL}", "smoke-test checks passed", K.BLUE),
                                   ("0", "console errors in the browser walk", K.ORANGE), (f"{L['predict_s']:.2f} s / {L['analyze_s']:.1f} s", "median /api/predict and /api/analyze on a CPU", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, c, vsize=24, lsize=12)
    rows = [["Observation", "Action"],
            [f"The ensemble leans toward AI-generated: false-positive rate {F.pct(E['fpr'])}, false-negative rate {F.pct(E['fnr'])}", "Reported; a higher threshold (0.7 to 0.8) lowers false positives but was picked on the test set"],
            ["Resize and blur drop ensemble accuracy to 61.0% and 58.3%; the hardened route A2 was no better", "Reported as a limit; hardening did not transfer to these distortions"],
            ["Not covered: Grad-CAM and robustness unit tests, load, GPU timing, adversarial attacks, user study", "Listed as future work"]]
    K.table(s, 0.6, 3.0, [6.3, 5.83], rows, font_size=14, row_h=0.88)
    notes[17] = "Tests cover preprocessing, fusion, both gates, response structure and the API routes; the smoke script and browser walk cover the running system. Latency was measured on 127.0.0.1 with the machine idle."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "Corrective action"],
            ["The shipped models were trained on synthetic demo images (100% scores, meaningless)", "Retrained all four routes on a real CIFAKE subset; the synthetic numbers are kept only as a footnote"],
            ["CPU-only training: route B alone took about 53 min", "Class-balanced subset of 6,000 training images, 3 to 5 epochs, early stopping"],
            ["The gates, as designed, never changed a result (fired 7 and 0 times)", "Ablation on the same logits; reported as no gain, defaults left unchanged"],
            ["Cues vanish under resize and blur; distortion-hardened A2 did not help", "Measured and reported; the robustness check shown to the user as a consistency score"],
            [f"Cross-domain probe at chance ({F.pct(F.XD['ensemble']['accuracy'])}, AUC {F.XD['ensemble']['roc_auc']:.3f})", "Objective 4 stated as not achieved; multi-generator, higher-resolution data planned"]]
    K.table(s, 0.6, 1.5, [5.6, 6.53], rows, font_size=15, row_h=0.9)
    notes[18] = "Each challenge was met by a concrete step or by measuring it and saying so plainly in the report."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("More and better data", "Train on the full 100,000 CIFAKE images and on several generators at higher resolution; evaluate per generator.", K.BLUE, "1"),
        ("Stronger evaluation", "Repeat with several seeds, tune weights, gates and the threshold on a validation set, and test on held-out generators.", K.GREEN, "2"),
        ("Explanation quality", "Test Grad-CAM quantitatively with deletion and insertion, and compare with other attribution methods.", K.ORANGE, "3"),
        ("Hardening", "Unit tests for explainability and robustness, a GPU run, load tests, and real user authentication.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.09, 1.6, 2.85, 4.6, t, b_, col, gl, body_size=17)
    notes[19] = "The first two items address the biggest honest gaps: a small single-generator training set and a cross-domain result at chance."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = ("Likely questions: why four routes (disagreement carries information, and HEDGE motivates heterogeneous routes); why the gates did not help (they rarely fire on 32 px CIFAKE); "
                 "whether Grad-CAM proves why the model decided (it is a qualitative aid).")

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, "VeriVision")
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
