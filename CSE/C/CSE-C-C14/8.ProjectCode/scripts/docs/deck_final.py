"""16.Final_PPT.pptx: 28 slides for VeriVision AI. Built from D:\\abstracts\\Templates\\Final_PPT.pptx (banner, rule, title and footer chrome inherited).

    python -m scripts.docs.deck_final            # from 8.ProjectCode
"""

import os

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE

from . import facts as F
from . import pptkit as K
from .lit import (BASE_PAPER_POINTS, EXPECTED_OUTCOMES, GAPS, LIT_TABLE, OBJECTIVES, PROBLEM_STATEMENT, PROPOSED_APPROACH, SUPPORT_EVIDENCE)
from .refs import REFS

TEMPLATE = r"D:\abstracts\Templates\Final_PPT.pptx"
FONT = "Calibri"
TOP_BANNER, TOP_RULE, TOP_TITLE, TOP_FOOT = 73152, 979985, 1098857, 6446520


def chrome(sh):
    return sh.top in (TOP_BANNER, TOP_RULE, TOP_TITLE, TOP_FOOT)


def set_title(slide, text, size=None):
    for sh in slide.shapes:
        if sh.top == TOP_TITLE:
            K.replace_text(sh, text, size)
            return


def wipe(slide):
    K.clear(slide, chrome)


def fbox(slide, x, y, w, h, fill=K.FHEAD, line=None):
    return K.box(slide, x, y, w, h, fill=fill, line=line, radius=0.04)


def ftable(slide, x, y, widths, rows, size=13, row_h=0.45, align=None, first_bold=True):
    return K.table(slide, x, y, widths, rows, font_size=size, row_h=row_h, header_fill=K.FHEAD, header_color=K.FNAVY, zebra=K.FZEBRA,
                   body_color=K.DARK, first_bold=first_bold, font=FONT, align=align, border=K.RGBColor(0xBF, 0xBF, 0xBF))


def ftext(slide, x, y, w, h, paras, size=16, color=K.DARK, **kw):
    return K.text(slide, x, y, w, h, paras, size=size, color=color, font=FONT, **kw)


def ftile(slide, x, y, w, h, value, label, color=K.FBLUE, vsize=26):
    K.box(slide, x, y, w, h, fill=K.FHEAD, line=None, radius=0.05)
    K.box(slide, x, y, 0.08, h, fill=color, line=None, shape=MSO_SHAPE.RECTANGLE)
    K.text(slide, x + 0.2, y + 0.06, w - 0.3, h * 0.55, value, size=vsize, color=K.FNAVY, bold=True, anchor="m", font=FONT)
    K.text(slide, x + 0.2, y + h * 0.58, w - 0.3, h * 0.4, label, size=12, color=K.DARK, font=FONT)


def plain(ref):
    return ref.replace("*", "")


def build(out_path):
    prs = Presentation(TEMPLATE)
    S = list(prs.slides)
    assert len(S) == 28, len(S)
    cp = prs.core_properties
    cp.title = f"{F.TITLE} - Final Review"
    cp.author = ", ".join(n for n, _ in F.STUDENTS)
    cp.comments = ""
    cp.subject = F.PRODUCT
    cp.keywords = "AI-generated image detection, CNN ensemble, Grad-CAM, explainable AI, image forensics"
    cp.last_modified_by = ""
    notes = {}

    E, BR, CI, SW = F.ENS, F.BR, F.CI, F.SWEEP
    V = F.VARIANTS
    n_test = F.N_TEST
    thr = {round(r["threshold"], 1): r for r in SW}
    rob = F.ROB
    xd = F.XD["ensemble"]
    lat = F.LATENCY
    
    def acc(d):
        return F.pct(d["accuracy"], 2)

    # footers on every slide
    for sl in S:
        for sh in sl.shapes:
            if sh.top == TOP_FOOT and sh.has_text_frame and "Final Review" in sh.text_frame.text:
                K.replace_text(sh, f"Dept. of CSE  |  Batch {F.BATCH_NO}  |  Final Review")

    # ---- 1 title
    s = S[0]
    for sh in s.shapes:
        if sh.name == "Text 1":
            K.replace_text(sh, "Detecting AI Generated Images with CNN\nand Interpretation Using Explainable AI", 26)
        elif sh.name == "Text 2":
            K.replace_text(sh, f"Final Review  ·  {F.PRODUCT}")
        elif sh.name == "Text 3":
            K.replace_text(sh, f"Team Details : Batch {F.BATCH_NO}")
        elif sh.name == "Text 4":
            K.replace_text(sh, "\n".join(f"{r_}   {n_}" for n_, r_ in F.STUDENTS))
        elif sh.name == "Text 5":
            K.replace_text(sh, f"Under the Esteemed Guidance of\n{F.GUIDE}\n{F.GUIDE_DESIGNATION}, Department of CSE")
        elif sh.name == "Text 6":
            K.replace_text(sh, f"DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING  ·  {F.COLLEGE_SHORT}  ·  Academic Year {F.YEAR}")
    notes[1] = "Introduce the team and the project: VeriVision AI, a local application that tells whether an image is real or AI-generated and shows why."

    # ---- 2 table of contents
    s = S[1]
    set_title(s, "Table of Contents")
    for sh in s.shapes:
        if sh.name == "Text 4":
            K.replace_text(sh, "Abstract\nBase Paper & Literature Survey\nResearch Gap, Problem Statement & Objectives\nProposed System & Architecture\nMethodology, Dataset & Models\nDecision Logic, Interaction & Data Model\nImplementation Highlights\nResults: Held-out, Threshold, Robustness\nPerformance & Testing\nComparison with Base Paper\nOutput Screens\nConclusion, Future Scope & References", 17)
    notes[2] = "The agenda follows the report: problem, design, method, results, comparison, screens, conclusion."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract")
    wipe(s)
    ftext(s, 0.55, 1.85, 12.2, 5.0, [
        ("AI image generators now produce pictures that people cannot reliably tell from photographs, and a bare real/fake score gives an analyst nothing to defend in a dispute.", {"bullet": True, "space_after": 9}),
        ("VeriVision AI runs four ImageNet-pretrained CNN routes (EfficientNet-B0 x2, ResNet50, MobileNetV3-Large), fuses their logits with two gating rules, explains the verdict with Grad-CAM and re-tests the image under JPEG, resize and blur.", {"bullet": True, "space_after": 9}),
        (f"On a held-out CIFAKE test subset (n = {n_test:,}, 32 px) the ensemble scores {acc(E)} accuracy, F1 {F.f4(E['f1'])} and ROC-AUC {F.f4(E['roc_auc'])}; its advantage over the best single route is not statistically distinguishable.", {"bullet": True, "space_after": 9}),
        (f"Resize and blur drop accuracy to {F.pct(rob['resize']['ensemble']['accuracy'])} and {F.pct(rob['blur']['ensemble']['accuracy'])}; on 600 full-resolution images from other sources the ensemble is at chance ({F.pct(xd['accuracy'])}). Cross-generator generalisation was measured and not achieved.", {"bullet": True, "space_after": 9}),
        (f"A full analysis takes about {lat['analyze_cifake_32px']['median']:.1f} s on a CPU; {F.PYTEST_PASSED} of {F.PYTEST_TOTAL} tests and {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} smoke checks pass.", {"bullet": True, "space_after": 9}),
        ("Not done: several generators, full-resolution training data, GPU runs, a user study.", {"bullet": True}),
    ], size=16)
    notes[3] = "Give the problem, the system in one breath, the headline number with its protocol, and end on the honest limits."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base Paper")
    wipe(s)
    ftext(s, 0.55, 1.85, 12.2, 0.8, F.BASE_PAPER, size=13, color=K.FNAVY)
    rows = [["Aspect", "Base paper: Learning the manifold of authenticity (CTrue)"],
            ["Method", "One-class representation learning: only authentic data is used for training, pseudo-fakes are synthesised, a hybrid-curvature representation separates authentic from deepfake faces"],
            ["Data and cost", "720 pristine FaceForensics++ videos; EfficientNet-B4 (19.3 M parameters); 200 epochs on two V100 GPUs (about 16 h); 74 fps on an RTX 3060"],
            ["Reported results", "AUC 98.9% on FF++ (in-domain) and 77.0% on DFDC in the lambda = 1 ablation; the cross-dataset table is an image in the paper and is not quoted"],
            ["Scope", "Face deepfakes in video frames; metric is AUC; no per-image explanation of the verdict"],
            ["What we take", "The goal of generalisable detection and the cross-dataset test idea. We do not implement CTrue: our models are supervised CNNs on general images"]]
    ftable(s, 0.55, 2.75, [2.0, 10.2], rows, size=13, row_h=0.62)
    notes[4] = "Larue et al., IEEE Access 2026. The base paper is a one-class face-deepfake detector. We state clearly that this project does not implement it; HEDGE is our design reference for fusion and gating."

    # ---- 5 literature survey
    s = S[4]
    set_title(s, "Literature Survey")
    wipe(s)
    rows = [["Work", "Year", "Approach", "Finding / limitation"]]
    for r in LIT_TABLE:
        rows.append([r[0].replace(" (base paper)", " (base)"), r[1], r[2], r[3]])
    ftable(s, 0.55, 1.75, [2.4, 0.65, 4.6, 4.55], rows, size=11, row_h=0.5, align=["l", "c", "l", "l"])
    notes[5] = "Representative work on face deepfakes, diffusion-image detection, foundation-model features, frequency cues and explanation. Batch survey items that could not be verified are marked in the report's reference list and no number from them is used."

    # ---- 6 research gap
    s = S[5]
    set_title(s, "Research Gap")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.9, [(g, {"bullet": True, "space_after": 20}) for g in GAPS], size=22)
    notes[6] = "Six gaps from the survey. The project addresses the second, fifth and sixth directly; the third is measured and the result is negative."

    # ---- 7 problem statement
    s = S[6]
    set_title(s, "Problem Statement")
    wipe(s)
    fbox(s, 0.55, 1.9, 12.2, 2.3)
    ftext(s, 0.85, 1.95, 11.6, 2.2, PROBLEM_STATEMENT, size=17, anchor="m", bullets=True)
    for i, (t, b_) in enumerate([("Input", "One image (png, jpg, jpeg or webp, up to 10 MB)"), ("Output", "Verdict, confidence, four route votes, Grad-CAM heat maps, robustness consistency"), ("Constraint", "Runs locally on a CPU; the image never leaves the machine")]):
        x = 0.55 + i * 4.1
        fbox(s, x, 4.5, 3.9, 1.7, fill=K.FZEBRA)
        ftext(s, x + 0.2, 4.6, 3.5, 0.4, t, size=17, color=K.FNAVY, bold=True)
        ftext(s, x + 0.2, 5.1, 3.5, 1.0, b_, size=15)
    notes[7] = "The statement has three parts: classify, explain, and stay deployable on ordinary hardware."

    # ---- 8 objectives
    s = S[7]
    set_title(s, "Objectives")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.9, [(f"{i}.  {o}", {"space_after": 18}) for i, o in enumerate(OBJECTIVES, 1)], size=22)
    notes[8] = "The six objectives of the proposal. The conclusion states the real status of each: 1 partly met, 4 measured and not achieved."

    # ---- 9 proposed system
    s = S[8]
    set_title(s, "Proposed System")
    wipe(s)
    K.flow(s, 0.55, 1.95, 12.2, 1.1, [("Image upload", K.FNAVY), ("Validate + resize", K.FBLUE), ("Four CNN routes", K.GREEN), ("Fusion + gates", K.ORANGE), ("Grad-CAM + robustness", K.PURPLE)], size=15, gap=0.35, font=FONT)
    ftext(s, 0.55, 3.35, 12.2, 3.5, [(p, {"bullet": True, "space_after": 14}) for p in PROPOSED_APPROACH] + [
        ("The verdict is decision support: every result screen says the heat map is an explanation aid, not proof of authenticity.", {"bullet": True})], size=19)
    notes[9] = "The proposed system as one line of boxes and the design rules behind it."

    # ---- 10 architecture
    s = S[9]
    set_title(s, "System Architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.55, 1.8, 5.6, 5.1)
    ftext(s, 6.6, 2.0, 6.2, 4.8, [
        (f"Web app: React + Vite on port {F.WEB_PORT}", {"bullet": True, "space_after": 12}),
        (f"API: Flask on port {F.API_PORT}, token sign-in", {"bullet": True, "space_after": 12}),
        ("Inference: four PyTorch models loaded once, fusion, Grad-CAM, robustness", {"bullet": True, "space_after": 12}),
        ("Storage: checkpoints, metadata and metric files only; no database", {"bullet": True, "space_after": 12}),
        ("Local first: no external service is called", {"bullet": True}),
    ], size=18)
    notes[10] = "Four tiers; all analysis runs on the local machine."

    # ---- 11 methodology
    s = S[10]
    set_title(s, "Methodology")
    wipe(s)
    K.flow(s, 0.55, 1.9, 12.2, 1.2, [("Validate image", K.FNAVY), ("Resize + normalise", K.FBLUE), ("Four routes", K.GREEN), ("Weighted logits", K.ORANGE), ("Two gates", K.PURPLE), ("Softmax + confidence", K.FBLUE), ("Grad-CAM + re-test", K.FNAVY)], size=13, gap=0.2, font=FONT)
    ftext(s, 0.55, 3.4, 12.2, 3.4, [
        ("Training: ImageNet weights, upper blocks fine-tuned; AdamW (weight decay 1e-4), cosine decay, lr 3e-4 (B 2e-4), batch 32 (B 16), early stopping on validation F1, patience 3; seeds 42-45.", {"bullet": True, "space_after": 9}),
        ("Losses and augmentation differ per route: cross-entropy for A1, A2 and B, focal loss (gamma 2) for C; A2 uses distortion-hardened augmentation; B adds horizontal-flip test-time augmentation.", {"bullet": True, "space_after": 9}),
        (f"Evaluation on the official CIFAKE test split ({n_test:,} images), bootstrap 95% intervals (2,000 resamples), 15-bin calibration, threshold sweep, fusion ablation on the same logits.", {"bullet": True, "space_after": 9}),
        ("Robustness on 1,000 test images under JPEG q60, 2x resize round trip, Gaussian blur and noise; cross-domain probe on 600 images from another source.", {"bullet": True, "space_after": 9}),
        ("Every number is written by scripts/run_cifake_experiments.py to experiments/cifake/metrics.json.", {"bullet": True}),
    ], size=15)
    notes[11] = "The workflow and the measurements added on top of plain accuracy: intervals, calibration, ablation, robustness and a cross-domain probe."

    # ---- 12 dataset and models
    s = S[11]
    set_title(s, "Dataset & Models")
    wipe(s)
    ftile(s, 0.55, 1.9, 2.9, 1.05, "6,000", "train images (3,000 real + 3,000 AI)", K.FBLUE, 26)
    ftile(s, 0.55, 3.1, 2.9, 1.05, "1,200", "validation images (600 + 600)", K.GREEN, 26)
    ftile(s, 0.55, 4.3, 2.9, 1.05, "2,000", "held-out test images (1,000 + 1,000)", K.ORANGE, 26)
    K.picture(s, F.fig("f01_dataset_split.png"), 3.7, 1.85, 4.6, 2.5)
    rows = [["Route", "Backbone", "Trainable params"],
            ["A1", "EfficientNet-B0 224", "1,131,954"], ["A2", "EfficientNet-B0 224", "3,158,302"],
            ["B", "ResNet50 320", "14,968,834"], ["C", "MobileNetV3-L 224", "2,185,522"]]
    ftable(s, 8.55, 1.9, [0.8, 2.0, 1.45], rows, size=11, row_h=0.5, first_bold=True)
    ftext(s, 3.7, 4.45, 9.0, 2.4, [
        ("CIFAKE [8]: 60,000 real CIFAR-10 images and 60,000 Stable Diffusion v1.4 images, 32 x 32 px; official split 100,000 train / 20,000 test.", {"bullet": True}),
        ("Class-balanced subset (seed 42): only 6% of the training pool, because training was CPU-only. One generator, tiny images.", {"bullet": True}),
        ("Cross-domain probe: 300 real + 300 AI images from another source (Hugging Face AI-vs-Real, MIT), about 640 to 1024 px.", {"bullet": True}),
    ], size=14)
    ftext(s, 0.55, 5.55, 3.0, 1.3, "Labels: 0 REAL, 1 AI_GENERATED. Subsets are drawn without overlap.", size=12, color=K.FNAVY, italic=True)
    notes[12] = "Be frank about the data: CIFAKE is 32 px and has one generator, and only 6,000 of 100,000 training images were used."

    # ---- 13 decision logic
    s = S[12]
    set_title(s, "Decision Logic: Fusion and Gates")
    wipe(s)
    K.picture(s, F.diag("10_flowchart_ensemble.png"), 0.55, 1.8, 5.6, 5.1)
    ftext(s, 6.4, 1.95, 6.4, 4.9, [
        ("Weighted sum of raw logits: A1 0.35, A2 0.15, B 0.25, C 0.25, then softmax.", {"bullet": True, "space_after": 10}),
        ("Gate 1: drop route B if its margin is at least 2.5 and the other three all disagree; weights renormalised.", {"bullet": True, "space_after": 10}),
        ("Gate 2: nudge the fused logits by 0.75 toward the B + C class when both agree with margins of at least 2.5.", {"bullet": True, "space_after": 10}),
        ("Confidence word: High at 0.85 or more, Moderate at 0.60 or more, otherwise Low.", {"bullet": True, "space_after": 10}),
        (f"Measured effect of the gates: Gate 1 fired on {E['gate1_fired']} of {n_test:,} images, Gate 2 on {E['gate2_fired']}; removing them gave {F.pct(V['no_gates']['accuracy'], 2)} against {F.pct(V['full']['accuracy'], 2)}.", {"bullet": True, "bold": True}),
    ], size=16)
    notes[13] = "The core algorithm in app/ensemble.py. The gate thresholds are engineering defaults, not tuned, and the ablation shows they did not help on this data."

    # ---- 14 user-system interaction
    s = S[13]
    set_title(s, "User – System Interaction")
    wipe(s)
    K.picture(s, F.diag("07_sequence_analyze.png"), 0.55, 1.8, 7.2, 5.1)
    K.picture(s, F.diag("08_use_case.png"), 7.9, 1.8, 4.9, 5.1)
    notes[14] = "Sequence of one analysis request and the use cases of the user and the developer."

    # ---- 15 data model
    s = S[14]
    set_title(s, "Data Model and Storage")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.55, 1.8, 7.0, 4.5)
    rows = [["Persisted item", "Content"], ["models/*.pt (4 files)", "route checkpoints"], ["model_metadata.json", "per-route settings and paths"],
            ["artifacts/metrics/", "evaluation JSON and PNG"], ["data/ folders", "train, val, test images"], ["Session token", "signed, 12 h, not stored"], ["Upload", "decoded in memory, discarded"]]
    ftable(s, 7.8, 1.9, [2.4, 2.6], rows, size=11, row_h=0.52)
    ftext(s, 0.55, 6.4, 12.2, 0.5, "There is no relational database: a request leaves no record, so nothing about an uploaded image is retained.", size=13, color=K.FNAVY, italic=True)
    notes[15] = "A file-based data model. The no-retention design is deliberate for privacy; it also means there is no analysis history."

    # ---- 16 implementation highlights
    s = S[15]
    set_title(s, "Implementation Highlights")
    wipe(s)
    for i, (v, l, c) in enumerate([("4", "CNN routes fused", K.FBLUE), (f"{F.PYTEST_TOTAL} + {F.SMOKE_TOTAL}", "pytest tests + smoke checks", K.GREEN), ("3", "routes with Grad-CAM", K.ORANGE), (f"{lat['analyze_cifake_32px']['median']:.1f} s", "median full analysis (CPU)", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.9, 2.9, 1.1, v, l, c, 28)
    ftext(s, 0.55, 3.3, 12.2, 3.5, [
        ("Upload validation: png / jpg / jpeg / webp, up to 10 MB, must decode as RGB and be at least 8 x 8; JSON errors 400, 401, 413, 500, 503.", {"bullet": True, "space_after": 9}),
        ("API: /health, /api/config, /api/insights, /api/auth/login, /api/auth/me, /api/analyze (token), /api/predict (JSON verdict); original Jinja pages kept.", {"bullet": True, "space_after": 9}),
        ("Models load once at start; a missing checkpoint gives 503 and the Status page names the missing files.", {"bullet": True, "space_after": 9}),
        ("React + Vite interface with verdict card, vote table, heat-map tabs, robustness table, insights and a dark theme; one command (run.bat) starts both servers.", {"bullet": True}),
    ], size=16)
    notes[16] = "Highlights: validation, API surface, load-once models and the interface."

    # ---- 17 results: held-out performance
    s = S[16]
    set_title(s, "Results – Held-out Performance")
    wipe(s)
    for i, (v, l, c) in enumerate([(acc(E), f"ensemble accuracy, n = {n_test:,}", K.FBLUE), (F.f4(E["f1"]), "ensemble F1", K.GREEN), (F.f4(E["roc_auc"]), "ensemble ROC-AUC", K.ORANGE), (F.pct(E["fpr"]), "false-positive rate (real called AI)", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.85, 2.9, 1.1, v, l, c, 26)
    K.picture(s, F.fig("f02_branch_metrics.png"), 0.55, 3.1, 5.9, 3.1)
    rows = [["Model", "Acc.", "F1", "AUC", "95% CI (acc.)"]]
    for k in F.BRANCHES:
        b = BR[k]
        rows.append([F.BRANCH_NAME[k], f"{b['accuracy']:.4f}", f"{b['f1']:.4f}", f"{b['roc_auc']:.4f}", f"{CI[k][0]:.3f}-{CI[k][1]:.3f}"])
    rows.append(["Ensemble (deployed)", f"{E['accuracy']:.4f}", f"{E['f1']:.4f}", f"{E['roc_auc']:.4f}", f"{CI['ensemble'][0]:.3f}-{CI['ensemble'][1]:.3f}"])
    ftable(s, 6.7, 3.15, [2.3, 0.85, 0.85, 0.85, 1.25], rows, size=11, row_h=0.4, align=["l", "c", "c", "c", "c"])
    ftext(s, 6.7, 5.7, 6.1, 1.2, "Single run per route (seeds 42-45). The ensemble's accuracy edge over A1 (0.55 points) is inside the overlap of the two intervals, so it is not statistically distinguishable; its AUC is higher. The model leans toward AI-generated (false positives 13.1%, false negatives 2.2%).", size=12, color=K.FNAVY, italic=True)
    ftext(s, 0.55, 6.3, 5.9, 0.6, "Route B is the most biased toward fake (recall 0.991, precision 0.793).", size=12, color=K.FNAVY, italic=True)
    notes[17] = "Headline numbers with their protocol. Be explicit that the ensemble is not significantly better than EfficientNet A1 on accuracy, and that errors are mostly real images called AI-generated."

    # ---- 18 confusion matrix & threshold
    s = S[17]
    set_title(s, "Confusion Matrix & Threshold Analysis")
    wipe(s)
    K.picture(s, F.fig("f03_confusion_matrix.png"), 0.55, 1.85, 5.2, 3.2)
    K.picture(s, F.fig("f07_threshold_sweep.png"), 6.0, 1.85, 6.8, 3.4)
    t7, t8 = thr[0.7], thr[0.8]
    ftext(s, 0.55, 5.2, 5.2, 1.7, [
        (f"Of {n_test:,} test images {E['confusion_matrix'][0][1]} real ones were called AI-generated and {E['confusion_matrix'][1][0]} AI images were called real.", {"bullet": True}),
        (f"Mean |margin|: correct {F.f2(F.ERR['mean_abs_margin_correct'])}, wrong {F.f2(F.ERR['mean_abs_margin_wrong'])}: errors sit near the boundary.", {"bullet": True}),
    ], size=13)
    ftext(s, 6.0, 5.4, 6.8, 1.5, [
        (f"Threshold 0.5 (deployed): accuracy {F.pct(thr[0.5]['accuracy'], 2)}, FPR {F.pct(thr[0.5]['fpr'])}. At 0.7: {F.pct(t7['accuracy'])} accuracy, FPR {F.pct(t7['fpr'])}; at 0.8: {F.pct(t8['accuracy'])}, FPR {F.pct(t8['fpr'])}, recall {F.pct(t8['recall'])}.", {"bullet": True}),
        ("The threshold was swept on the test subset, so the gain is optimistic; a separate validation set would be needed to adopt 0.7.", {"bullet": True, "italic": True}),
    ], size=13)
    notes[18] = "Counts and rates of the ensemble, and the effect of the decision threshold. Raising it lowers false positives at some cost in recall, but the choice was made on the test set."

    # ---- 19 ablation, robustness, cross-domain
    s = S[18]
    set_title(s, "Ablation, Robustness and Cross-Domain")
    wipe(s)
    K.picture(s, F.fig("f06_fusion_ablation.png"), 0.45, 1.8, 4.1, 3.0)
    K.picture(s, F.fig("f08_robustness.png"), 4.6, 1.8, 4.3, 3.0)
    K.picture(s, F.fig("f09_cross_domain.png"), 8.95, 1.8, 4.0, 3.0)
    ftext(s, 0.45, 4.6, 4.0, 2.2, [
        (f"Same logits, seven fusion rules: all within {F.pct(V['equal_weights']['accuracy'], 2)} to {F.pct(V['prob_avg']['accuracy'], 2)} accuracy.", {"bullet": True}),
        (f"No-gate fusion {F.pct(V['no_gates']['accuracy'], 2)}; the gates did not help.", {"bullet": True}),
        (f"Majority vote has a far lower AUC ({F.f3(V['majority']['roc_auc'])}).", {"bullet": True}),
    ], size=13)
    ftext(s, 4.6, 4.6, 4.3, 2.2, [
        (f"Clean {F.pct(rob['clean_subset']['ensemble']['accuracy'])}, JPEG q60 {F.pct(rob['jpeg']['ensemble']['accuracy'])}, noise {F.pct(rob['noise']['ensemble']['accuracy'])}.", {"bullet": True}),
        (f"Resize round trip {F.pct(rob['resize']['ensemble']['accuracy'])}, blur {F.pct(rob['blur']['ensemble']['accuracy'])}: the cue is lost on 32 px images.", {"bullet": True}),
        ("Distortion-hardened A2 was not more robust than A1.", {"bullet": True}),
    ], size=13)
    ftext(s, 8.95, 4.6, 4.0, 2.2, [
        (f"600 full-resolution images: ensemble {F.pct(xd['accuracy'])}, AUC {F.f3(xd['roc_auc'])}: chance level.", {"bullet": True, "bold": True}),
        ("A2, B and C call almost everything AI-generated.", {"bullet": True}),
        ("Objective 4 measured and not achieved.", {"bullet": True, "bold": True}),
    ], size=13)
    notes[19] = "Three honest findings: the gating rules are neutral, resizing and blur destroy the cue, and the CIFAKE-trained models do not transfer to full-resolution images from other sources."

    # ---- 20 performance & testing
    s = S[19]
    set_title(s, "Performance & Testing")
    wipe(s)
    bt = F.M.get("inference_seconds_per_image_batched")
    for i, (v, l, c) in enumerate([(f"{lat['health']['median'] * 1000:.0f} ms", "GET /health", K.FBLUE), (f"{lat['predict_cifake_32px']['median']:.2f} s", "/api/predict, four routes + fusion", K.GREEN),
                                   (f"{lat['analyze_cifake_32px']['median']:.2f} s", "/api/analyze (32 px image)", K.ORANGE), (f"{lat['analyze_photo_1024px']['median']:.2f} s", "/api/analyze (1024 px image)", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.85, 2.9, 1.15, v, l, c, 26)
    rows = [["Test layer", "What it covers", "Result"],
            ["Unit and API (pytest)", "preprocessing, weights, fusion, both gates, response structure, health, bad upload, login, config, insights, oversize", f"{F.PYTEST_PASSED} of {F.PYTEST_TOTAL} passed in {F.PYTEST_SECONDS:.0f} s"],
            ["Smoke test", "running API and web proxy: login, fake and real analysis, votes, Grad-CAM, robustness, error cases, classic pages", f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks"],
            ["Browser walk", "every screen captured in Chrome (capture_screens.py)", "no console errors, no failed requests"],
            ["Latency", "8 runs each, API on 127.0.0.1, idle machine", "medians as above"],
            ["Not done", "explainability / robustness unit tests, load, GPU, adversarial attacks, user study", "stated gap"]]
    ftable(s, 0.55, 3.2, [2.4, 6.6, 3.2], rows, size=12, row_h=0.52)
    ftext(s, 0.55, 6.4, 12.2, 0.55, f"{F.LATENCY['machine']['cpu']}, 15.7 GB RAM, no GPU. Offline batched inference: {bt * 1000:.0f} ms per image for all four routes.", size=12, color=K.FNAVY, italic=True)
    notes[20] = "A full analysis, including three Grad-CAM overlays and three robustness variants, takes under two seconds on this CPU. Tests pass; the untested areas are listed."

    # ---- 21 comparison with the base paper
    s = S[20]
    set_title(s, "Comparison with Base Paper (context only)")
    wipe(s)
    rows = [["Aspect", "Base paper: CTrue [1]", "This project: VeriVision AI"],
            ["Task and data", "Face deepfakes, FaceForensics++ and DFDC video frames", "General real-vs-AI images, CIFAKE 32 px subset (one generator)"],
            ["Training", "One-class, 720 pristine videos plus pseudo-fakes, 200 epochs", "Supervised, 6,000 images, 3-5 epochs per route"],
            ["Model", "EfficientNet-B4, 19.3 M parameters", "Four CNN routes (EfficientNet-B0 x2, ResNet50, MobileNetV3-L) fused"],
            ["Compute", "Two V100 GPUs, about 16 h", "Intel i5-12500 CPU, 13-53 min per route (upper bounds)"],
            ["In-domain AUC", "98.9% (FF++)", f"{F.pct(E['roc_auc'], 2)} (CIFAKE test)"],
            ["Cross-dataset AUC", "77.0% (DFDC, lambda = 1 ablation)", f"{F.pct(xd['roc_auc'], 1)} (600 full-resolution images, another source)"],
            ["Output", "Detection score", "Verdict, votes, Grad-CAM heat maps, robustness consistency"]]
    ftable(s, 0.55, 1.8, [2.0, 4.9, 5.3], rows, size=12, row_h=0.52)
    ftext(s, 0.55, 6.15, 12.2, 0.8, f"Task, data, training and metric emphasis all differ; only AUC is like-for-like, so the numbers are context, not a ranking, and no superiority is claimed. HEDGE [2], our design reference, reports 98.3% balanced accuracy on five benchmarks with 8 H800 GPUs.", size=13, color=K.FNAVY)
    notes[21] = "State plainly that 98.65% AUC on 32 px CIFAKE cannot be set against 98.9% on FF++ faces. Cross-dataset, the paper reports 77.0% on DFDC and our cross-domain probe is at chance."

    # ---- 22-24 output screens
    def shot(slide, name, x, y, w=6.0, h=3.75):
        K.picture(slide, F.shot(name), x, y, w, h, border=True)

    s = S[21]
    set_title(s, "Output – Verdict Screens")
    wipe(s)
    shot(s, "07_result_verdict.png", 0.55, 1.85)
    shot(s, "17_result_real.png", 6.8, 1.85)
    ftext(s, 0.55, 5.75, 6.0, 1.1, "A 32 px AI-generated test image: 'Likely AI-generated', 99.25% (High confidence), 4 of 4 routes agree.", size=14, color=K.FNAVY)
    ftext(s, 6.8, 5.75, 6.0, 1.1, "A real CIFAR-10 test image: 'Likely a real image', 97.17% (High confidence), 4 of 4 routes agree.", size=14, color=K.FNAVY)
    notes[22] = "Real screenshots from the running application with the CIFAKE-trained models."

    s = S[22]
    set_title(s, "Output – Votes, Robustness and a Failure Case")
    wipe(s)
    shot(s, "08_result_votes_robustness.png", 0.55, 1.85)
    shot(s, "19_result_hires_real.png", 6.8, 1.85)
    ftext(s, 0.55, 5.75, 6.0, 1.1, "Per-route votes with fusion weights, and the robustness table: the resize variant flips to Real, so consistency is 3/4 and the UI advises caution.", size=14, color=K.FNAVY)
    ftext(s, 6.8, 5.75, 6.0, 1.1, "Failure case: a real full-resolution photograph (food on a plate) is called AI-generated with 100% confidence. This image comes from the cross-domain probe measured on slide 19.", size=14, color=K.FNAVY)
    notes[23] = "The right-hand screen is deliberately included: the CIFAKE-trained models mislabel real full-resolution photographs, so a High-confidence label is not evidence outside the training domain."

    s = S[23]
    set_title(s, "Output – Grad-CAM Explanations")
    wipe(s)
    shot(s, "09_result_gradcam.png", 0.55, 1.85)
    shot(s, "10_result_gradcam_resnet.png", 6.8, 1.85)
    ftext(s, 0.55, 5.75, 6.0, 1.1, "EfficientNet tab: original image and Grad-CAM heat map for the predicted class; the strongest response is on the right edge of the frog.", size=14, color=K.FNAVY)
    ftext(s, 6.8, 5.75, 6.0, 1.1, "ResNet50 tab for the same image: a broader response over the lower body. Heat maps were judged by eye only; no faithfulness test was run.", size=14, color=K.FNAVY)
    notes[24] = "Different routes attend to different regions of the same image. The explanation is an aid, and the screen says so."

    # ---- 25 conclusion
    s = S[24]
    set_title(s, "Conclusion")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 5.0, [
        (f"**Delivered:** a working local application from image upload to verdict, per-route votes, Grad-CAM heat maps and a robustness check; {F.PYTEST_PASSED} of {F.PYTEST_TOTAL} tests and {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} smoke checks pass.", {"bullet": True, "space_after": 9}),
        (f"**Measured:** ensemble {acc(E)} accuracy, F1 {F.f4(E['f1'])}, AUC {F.f4(E['roc_auc'])} on {n_test:,} held-out CIFAKE images; resize and blur cut it to about 58-61%; cross-domain {F.pct(xd['accuracy'])}.", {"bullet": True, "space_after": 9}),
        ("**Objectives:** 2, 3, 5 and 6 met (5 judged qualitatively); 1 partly met (one generator, 32 px subset); 4 measured and not achieved.", {"bullet": True, "space_after": 9}),
        ("**Findings:** the ensemble is not significantly better than its best route; the gates did not help; the models lean toward AI-generated.", {"bullet": True, "space_after": 9}),
        ("**Limits:** single seed, 6% of the training data, 3-5 epochs, no GPU run, no user study. The verdict is decision support, not proof.", {"bullet": True}),
    ], size=20)
    notes[25] = "Be explicit about which objectives were met and which were not, and what was never measured."

    # ---- 26 future scope
    s = S[25]
    set_title(s, "Future Scope")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 5.0, [
        ("Train on the full 100,000 CIFAKE images and on a mix of generators and resolutions; repeat with several seeds to put intervals on the ranking of routes.", {"bullet": True, "space_after": 10}),
        ("Test cross-generator transfer properly with per-generator breakdowns, including newer diffusion models and GAN images.", {"bullet": True, "space_after": 10}),
        ("Add foundation-model or frequency features, as in HEDGE, and tune the gates and the decision threshold on a validation set.", {"bullet": True, "space_after": 10}),
        ("Add a quantitative faithfulness test for Grad-CAM (deletion and insertion curves) and a user study of the explanations.", {"bullet": True, "space_after": 10}),
        ("Add GPU timing, load and adversarial tests, and a hosted deployment with real authentication.", {"bullet": True}),
    ], size=22)
    notes[26] = "Concrete next steps, ordered by value."

    # ---- 27 references
    s = S[26]
    set_title(s, "References")
    wipe(s)
    ids = [1, 2, 3, 8, 10, 12, 13, 19, 20, 21, 22, 26]
    ftext(s, 0.55, 1.8, 6.0, 5.1, [(f"[{n}] {plain(REFS[n - 1])}", {"space_after": 5}) for n in ids[:6]], size=12)
    ftext(s, 6.8, 1.8, 6.0, 5.1, [(f"[{n}] {plain(REFS[n - 1])}", {"space_after": 5}) for n in ids[6:]], size=12)
    notes[27] = "Selected references; the complete numbered list is in the report."

    # ---- 28 thank you
    for sh in S[27].shapes:
        if sh.name == "Text 2":
            K.replace_text(sh, "Questions & Suggestions")
    notes[28] = "Invite questions."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes.get(i, ""))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, "VeriVision")
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "16.Final_PPT.pptx")))
