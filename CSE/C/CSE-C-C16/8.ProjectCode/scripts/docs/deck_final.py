"""16.Final_PPT.pptx: 28 slides. Built from D:\\abstracts\\Templates\\Final_PPT.pptx (letterhead banner, rule, title and footer chrome inherited).

    python -m scripts.docs.deck_final          # from 8.ProjectCode
"""

import os

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE

from . import facts as F
from . import pptkit as K
from .lit import GAP, OBJECTIVES, PROBLEM_POINTS, PROBLEM_STATEMENT
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


def cap(slide, x, y, w, text, size=12):
    return ftext(slide, x, y, w, 0.5, text, size=size, color=K.FNAVY, align="c")


def bl(items, sa=8):
    return [(t, {"bullet": True, "space_after": sa}) for t in items]


def build(out_path):
    prs = Presentation(TEMPLATE)
    S = list(prs.slides)
    assert len(S) == 28, len(S)
    cp = prs.core_properties
    cp.title = f"{F.TITLE} - Final Review"
    cp.author = f"Batch {F.BATCH_NO}, Dept. of CSE"
    cp.comments = ""
    cp.subject = F.PRODUCT
    cp.keywords = "crop disease detection; leaf images; PlantDoc; treatment advice"
    cp.last_modified_by = ""
    notes = {}
    HC, HG, H0, C, CS, CT, MB, BL = F.HC, F.HG, F.H0, F.C, F.CS, F.CT, F.MB, F.BL
    RF, LR = BL["random_forest"], BL["logistic_regression"]
    LAT = F.LAT
    DC = LAT["detect_client_ms"]
    E = F.EDGE

    def p1(x):
        return f"{x * 100:.1f} %"

    for sl in S:
        for sh in sl.shapes:
            if sh.top == TOP_FOOT and sh.has_text_frame and "Final Review" in sh.text_frame.text:
                K.replace_text(sh, f"Dept. of CSE  |  Batch {F.BATCH_NO}  |  Final Review")

    # ---- 1 title
    for sh in S[0].shapes:
        if sh.name == "Text 1":
            K.replace_text(sh, F.TITLE, 28)
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
    notes[1] = "Introduce the team and the project: AgriVision, a leaf-photograph diagnosis and treatment-advice web application, and a measured study of how well it recognises disease on field photographs."

    # ---- 2 table of contents
    s = S[1]
    set_title(s, "Table of Contents")
    for sh in s.shapes:
        if sh.name == "Text 4":
            K.replace_text(sh, "Abstract\nBase Paper & Literature Survey\nResearch Gap, Problem Statement & Objectives\nProposed System & Architecture\nMethodology, Dataset & Models\nDecision Logic, Interaction & Database Design\nImplementation Highlights\nResults, Confusion Matrix & Parameter Analysis\nPerformance, Testing & Defects\nComparison with Base Paper\nOutput Screens\nConclusion, Future Scope & References", 17)
    notes[2] = "The agenda follows the report: problem, design, method, results, comparison, screens, conclusion."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.9, bl([
        "Crop disease costs farmers a large share of their harvest and the expert who could name it is rarely at the field in time.",
        "AgriVision lets a farmer upload a leaf photo, pick the crop and read the most likely disease, its severity and chemical, organic and cultural treatment advice for 38 classes, in an interface available in English, Hindi and Marathi (React + FastAPI + SQLite).",
        f"Measured on PlantDoc field photos ({F.NTRAIN:,} train, {F.NTEST} test): the engine shipped in the app is a colour/texture heuristic and is right on **{F.pm(HC)}** of photos with the crop chosen and fails on {F.pct(HC['failed_share']['mean'])} (a crop-option defect); the compact CNN of the training script reaches {F.pm(C)}; a reference MobileNetV2 reaches **{F.pm(MB)}** (not yet in the app).",
        f"{F.N_SMOKE} API checks pass; further tests record five defects. Fertiliser, yield and weather advice from the original proposal are not implemented.",
    ], 14), size=19.5)
    notes[3] = "State the system, then the honest measurement: the shipped heuristic is close to chance, a transfer-learning model reaches about 50 percent on this hard dataset."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base Paper")
    wipe(s)
    ftext(s, 0.55, 1.85, 12.2, 0.75, F.BASE_PAPER, size=13, color=K.FNAVY)
    rows = [["Aspect", "Foliagen (Pakka et al., IEEE Access, 2026)"],
            ["Aim", "Generate large, annotated crop foliage image sets from single-leaf photos, because annotated in-field foliage datasets are scarce"],
            ["Method", "Background removal (rembg), phyllotactic leaf placement per crop, a chosen disease rate gamma (1 to 20 %); no generative AI"],
            ["Data", "ASDID (10,722 soybean leaves, 7 diseases), a Kaggle soybean set, PlantVillage tomato; real foliage set MH-SoyaHealthVision"],
            ["Evaluation", "VGG19, ResNet50, DenseNet121, Swin Transformer, CBAM-ConvNeXt on 2 x RTX 6000 Ada GPUs; Adam 1e-4, batch 8"],
            ["Result", "Up to 98 % accuracy on natural foliage when 5 % of it is added to generated data; pre-training on generated data helps fine-tuning"],
            ["Use here", "Motivates the gap (field photos, scarce data); the project does not implement Foliagen: it builds the diagnosis + advice application"]]
    ftable(s, 0.55, 2.7, [1.7, 10.5], rows, size=12.5, row_h=0.56)
    notes[4] = "The base paper is about data generation for foliage classifiers. We take its motivation, not its method, and say so."

    # ---- 5 literature survey
    s = S[4]
    set_title(s, "Literature Survey")
    wipe(s)
    rows = [["Author / Year", "Methodology", "Dataset", "Key results", "Limitations"],
            ["Sherifi et al. 2026 [2]", "PD36-C compact CNN, 1.25 M parameters, desktop app", "87 k images, 38 classes (lab style)", "99.53 % test accuracy", "Clean backgrounds; no advice"],
            ["Kanakala, Ningappa 2025 [3]", "CNN and LSTM, Adam 1e-4", "70,295 train / 17,572 val, 38 classes", "CNN 96.4 % val; LSTM 93.43 %", "Random split of lab-style set"],
            ["Singh et al. 2020 [4]", "PlantDoc benchmark: VGG16, InceptionV3, InceptionResNetV2", "2,598 field photos, 27 classes", "44.5-70.5 % (cropped), 13.7-29.7 % (raw)", "Small, hard, noisy"],
            ["Mohanty et al. 2016 [6]", "AlexNet / GoogLeNet on PlantVillage", "54,306 images, 14 crops", "99.35 % held-out", "Lab backgrounds; weak on other sources"],
            ["Ferentinos 2018 [7]", "Five CNNs, lab and field backgrounds", "87,848 images, 58 classes", "99.53 % best", "Mostly lab; no advice"],
            ["Barbedo 2018 [8]", "Factors that limit deep learning on leaves", "Review and experiments", "Accuracy drops with condition variety", "Describes, does not build"]]
    ftable(s, 0.55, 1.85, [2.1, 3.1, 2.4, 2.4, 2.2], rows, size=11.5, row_h=0.66)
    ftext(s, 0.55, 6.5, 12.2, 0.4, "Four further survey papers named in the project proposal could not be verified; they are listed in the report as such and not quoted.", size=11, color=K.FNAVY, italic=True)
    notes[5] = "Lab-style datasets give 96 to 99 percent; the PlantDoc authors show that field photos give 14 to 70 percent."

    # ---- 6 research gap
    s = S[5]
    set_title(s, "Research Gap")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.8, bl([
        f"**Stated gap:** {GAP}",
        "**Lab versus field:** classifiers with 96 to 99 % accuracy are trained and tested on laboratory images; on field photographs the same models fall far lower [4], [8].",
        "**Label without advice:** the surveyed classifiers stop at the disease name [2], [3]; the base paper [1] produces training data, not guidance for the farmer.",
        "**Language:** advice is given in English only, which is unusable for many farmers.",
        "**Honest evaluation:** few applications report accuracy on field photos or document the defects of their own engine.",
    ], 12), size=18)
    notes[6] = "Five gaps. We build for the second to fourth and measure the first and fifth."

    # ---- 7 problem statement
    s = S[6]
    set_title(s, "Problem Statement")
    wipe(s)
    fbox(s, 0.55, 1.95, 12.2, 2.2)
    ftext(s, 0.85, 2.0, 11.6, 2.1, PROBLEM_STATEMENT, size=16.5, anchor="m")
    for i, (t, b_) in enumerate([("Input", "One leaf photo (JPG, PNG, WEBP, up to 10 MB) and the crop chosen by the farmer"), ("Output", "Top-3 classes, severity, three treatments, prevention, saved to a history"), ("Evidence", "PlantDoc test split, three seeds, defects and gaps stated")]):
        x = 0.55 + i * 4.1
        fbox(s, x, 4.4, 3.9, 1.6, fill=K.FZEBRA)
        ftext(s, x + 0.2, 4.48, 3.5, 0.4, t, size=17, color=K.FNAVY, bold=True)
        ftext(s, x + 0.2, 4.95, 3.5, 1.0, b_, size=14)
    ftext(s, 0.55, 6.2, 12.2, 0.6, "Need: " + NEED_TEXT, size=13, color=K.FNAVY, italic=True)
    notes[7] = "The statement has three parts: diagnose from a photo, return advice in the farmer's language, and report the accuracy honestly."

    # ---- 8 objectives
    s = S[7]
    set_title(s, "Objectives")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.9, [(f"{i}.  {o}", {"space_after": 12}) for i, o in enumerate(OBJECTIVES, 1)], size=20)
    notes[8] = "The six objectives of the proposal. The conclusion states which were met."

    # ---- 9 proposed system
    s = S[8]
    set_title(s, "Proposed System")
    wipe(s)
    K.flow(s, 0.55, 2.0, 12.2, 1.1, [("Leaf photo + crop", K.FNAVY), ("Validate, resize 256 px", K.FBLUE), ("Colour / texture features", K.GREEN), ("Score + rank classes", K.ORANGE), ("Knowledge card + advice", K.PURPLE)], size=14, gap=0.35, font=FONT)
    ftext(s, 0.55, 3.5, 12.2, 3.3, bl([
        "React web app: sign-in, Detect, Result, History, Analytics, Dashboard, Disease guide, Profile; English, Hindi, Marathi interface; light and dark theme.",
        "FastAPI service (16 routes, bearer-token login) over the original Flask product: same detection engine, same knowledge base, same SQLite file.",
        "Engine as shipped: a colour/texture heuristic. A trained Keras or ONNX model placed in models/ would be loaded instead; the training script and the PlantDoc label map exist.",
        "Knowledge base: 38 classes, 14 crops; each disease has symptoms, severity, chemical, organic and cultural treatments and prevention.",
    ], 10), size=17)
    notes[9] = "The pipeline as a row of boxes, then four properties. Say plainly that the shipped engine is a heuristic."

    # ---- 10 architecture
    s = S[9]
    set_title(s, "System Architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.55, 1.85, 6.4, 5.0)
    ftext(s, 7.2, 2.0, 5.6, 4.7, bl([
        "Presentation: React 18 + Vite + TypeScript + Tailwind, 12 page components, port 5416",
        "Application: FastAPI, 16 routes under /api, HMAC bearer token, one JSON error shape, port 8416",
        "Domain: agrivision/ inference engine and 38-class knowledge base, imported unchanged",
        "Storage: SQLite (users, results) and an uploads folder; models/ is empty",
        "Launch: run.bat builds the environment and starts both servers",
    ], 9), size=16)
    notes[10] = "Three tiers plus storage; the API layer imports the original Flask modules rather than reimplementing them."

    # ---- 11 methodology
    s = S[10]
    set_title(s, "Methodology")
    wipe(s)
    K.picture(s, F.diag("02_high_level_workflow.png"), 0.55, 1.85, 7.8, 5.0)
    ftext(s, 8.6, 2.0, 4.2, 4.8, bl([
        "Diagnosis path: upload checks, 256 px resize, six colour/texture features, candidate classes of the chosen crop, scored top-3, knowledge card.",
        "Learning path (offline): PlantDoc folders, 224 px cache, 10 % validation split, compact CNN or MobileNetV2, 3 seeds, test on 236 photos.",
        "The trained network is not copied into models/, so the app keeps the heuristic.",
    ], 10), size=15)
    notes[11] = "Two paths. The offline path is how every accuracy figure in this deck was measured."

    # ---- 12 dataset and models
    s = S[11]
    set_title(s, "Dataset, Preprocessing & Models")
    wipe(s)
    ftext(s, 0.55, 1.9, 7.0, 5.0, bl([
        f"**PlantDoc** (Singh et al.), CC-BY-4.0, web-scraped field photos: {F.NTRAIN:,} train + {F.NTEST} test, 28 train folders, 27 test folders (spider mites has 2 train photos, no test photo); 13 crops; 2 to 180 images per class.",
        "**Preprocessing:** resize to 224 x 224, 10 % stratified validation split; in-model flip, rotation 0.08, zoom 0.1, contrast 0.1. The app's heuristic resizes to 256.",
        f"**Compact CNN** (train.py): 5 separable-convolution blocks, batch norm, GAP, dense 256; {C['params']['mean']:,.0f} parameters (the docstring says about 1.1 M); Adam 1e-3, batch 32.",
        f"**MobileNetV2** reference: ImageNet weights, 2.29 M parameters; head trained, then top 30 layers fine-tuned at 1e-4.",
        "**Baselines:** random forest and logistic regression on colour histograms and edge statistics.",
    ], 8), size=14)
    K.picture(s, F.fig("f09_class_distribution.png"), 7.8, 1.85, 5.0, 5.0)
    notes[12] = "Small, imbalanced field data. Note the parameter count of the compact CNN differs from its docstring."

    # ---- 13 decision workflow
    s = S[12]
    set_title(s, "Decision Logic of the Shipped Engine")
    wipe(s)
    K.picture(s, F.diag("10_core_algorithm_flowchart.png"), 0.55, 1.8, 5.6, 5.1)
    ftext(s, 6.5, 1.95, 6.3, 4.9, bl([
        "Features from a 256 px copy: green, brown, yellow, dark and white pixel shares and the global standard deviation.",
        "Candidates: the classes of the chosen crop, or all 38 on 'general'.",
        "Healthy score rewards green and penalises brown/yellow; disease scores reward brown, yellow, dark and white plus name cues (rust, blight, mildew, mosaic, mite).",
        "Confidence is clamp(0.62 + 0.22 x score, 0.62, 0.99): it never reports low confidence.",
        "With fewer than 3 candidate classes (10 of 19 crop keys; 9 of the 18 in the web form) the code raises IndexError and the API returns HTTP 400 (defect D1).",
    ], 9), size=15)
    notes[13] = "The heart of the shipped engine. The confidence formula explains why almost every photo shows about 97 percent."

    # ---- 14 interaction
    s = S[13]
    set_title(s, "User–System Interaction")
    wipe(s)
    K.picture(s, F.diag("07_sequence_diagram.png"), 0.55, 1.8, 5.7, 4.65)
    K.picture(s, F.diag("08_use_case_diagram.png"), 6.5, 1.8, 6.3, 4.65)
    cap(s, 0.55, 6.5, 12.2, "Left: one diagnosis from upload to result screen. Right: use cases of the farmer, the visitor and the offline model owner.", 12.5)
    notes[14] = "Sequence of a scan through React, FastAPI, the engine, the knowledge base and SQLite; then the use cases."

    # ---- 15 database design
    s = S[14]
    set_title(s, "Database Design")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.55, 1.85, 7.4, 4.75)
    ftext(s, 8.2, 2.0, 4.6, 4.7, bl([
        "SQLite file shared by the Flask and FastAPI front ends; created by init_db(); a demo farmer is seeded.",
        "users: 11 columns; passwords stored as scrypt salted hashes.",
        "results: 12 columns, one row per scan, top-3 as JSON text; user_id is a foreign key.",
        "The 38-class knowledge base is code (disease_db.py), not a table; images are files named by random UUID.",
    ], 9), size=15)
    notes[15] = "Two tables. Deleting a scan removes the row and the image file."

    # ---- 16 implementation highlights
    s = S[15]
    set_title(s, "Implementation Highlights")
    wipe(s)
    rows = [["Component", "What was built"],
            ["Front end", "React 18, Vite 8, TypeScript 5.9, Tailwind 4; 12 page components, 5,647 lines; axios + TanStack Query; EN / HI / MR interface strings; light and dark theme; phone layout"],
            ["API layer", "FastAPI, 437 lines, 16 routes; HMAC-signed bearer token (7 days); upload checks (type, 10 MB, empty); owner checks on every scan; CSV and PDF export"],
            ["Engine", "inference.py: heuristic, or Keras / ONNX model if models/ holds one; PlantDoc-to-38-class label map"],
            ["Knowledge base", "disease_db.py: 38 classes, 26 curated cards, 3 treatments each with cost text, severity, prevention, lifecycle"],
            ["Data", "SQLite users + results, uploads folder; run.bat one-click start; own scripts: smoke, edge, UI checks, experiments (1,448 lines)"]]
    ftable(s, 0.55, 1.95, [2.2, 10.0], rows, size=14, row_h=0.8)
    notes[16] = "What exists in the repository. The engine row is the important one."

    # ---- 17 results: model performance
    s = S[16]
    set_title(s, "Results – Accuracy of Every Engine")
    wipe(s)
    rows = [["Engine (236 test photos)", "Accuracy", "Macro-F1", "Top-3"],
            ["Shipped heuristic, crop chosen", F.pm(HC), f"{HC['macro_f1']['mean']:.3f}", F.mean_pct(HC, "top3_accuracy")],
            ["Shipped heuristic, crop 'general'", F.pm(HG), f"{HG['macro_f1']['mean']:.3f}", F.mean_pct(HG, "top3_accuracy")],
            ["Logistic regression (colour/texture)", p1(LR["accuracy"]), f"{LR['macro_f1']:.3f}", p1(LR["top3_accuracy"])],
            ["Compact CNN of train.py (3 seeds)", F.pm(C), f"{C['macro_f1']['mean']:.3f}", F.mean_pct(C, "top3_accuracy")],
            ["Random forest (colour/texture)", p1(RF["accuracy"]), f"{RF['macro_f1']:.3f}", p1(RF["top3_accuracy"])],
            ["MobileNetV2 fine-tuned (3 seeds)", F.pm(MB), f"{MB['macro_f1']['mean']:.3f}", F.mean_pct(MB, "top3_accuracy")]]
    ftable(s, 0.55, 1.9, [3.3, 1.35, 1.0, 0.9], rows, size=12, row_h=0.46, align=["l", "c", "c", "c"])
    K.picture(s, F.fig("f01_model_comparison.png"), 7.3, 1.85, 5.5, 2.4)
    ftext(s, 0.55, 5.3, 12.2, 1.5, bl([
        f"Chance is {p1(F.H['chance_with_crop_hint'])} with the crop known and {p1(F.H['chance_general'])} on 38 classes; always answering the most frequent class gives {p1(F.H['majority_class_test'])}.",
        f"With hash seed 0 (what run.bat uses) the heuristic scores {p1(H0['accuracy'])} top-1; {F.pct(HC['failed_share']['mean'])} of photos get no answer (defect D1).",
        "Only the transfer-learning reference is clearly above chance, and it is not part of the shipped app.",
    ], 5), size=13.5)
    notes[17] = "The central result slide. Read the heuristic row first and then the MobileNetV2 row; the compact CNN of the training script does not learn the task."

    # ---- 18 confusion matrix
    s = S[17]
    set_title(s, "Confusion Matrix & Per-class F1")
    wipe(s)
    K.picture(s, F.fig("f02_confusion_matrix_mobilenet.png"), 0.45, 1.85, 4.9, 4.5)
    K.picture(s, F.fig("f03_per_class_f1.png"), 5.4, 1.85, 4.7, 4.5)
    ftext(s, 10.25, 1.95, 2.7, 4.6, bl([
        f"MobileNetV2: healthy recall {F.pm(MB, 'healthy_recall')}, diseased recall {F.pm(MB, 'diseased_recall')}.",
        "Best: Strawberry 1.00, grape black rot 0.93, grape 0.92, corn rust 0.89.",
        "Zero F1: bell pepper leaf spot, tomato bacterial spot, tomato mosaic virus.",
        "Spots on leaves look alike in photos.",
    ], 6), size=12.5)
    cap(s, 0.45, 6.4, 9.7, "Seed 42, 236 test photos; the compact CNN's F1 is near zero on most classes.", 12)
    notes[18] = "Confusions concentrate among similar spot diseases of tomato and pepper; the compact CNN only separates a few classes."

    # ---- 19 parameter analysis
    s = S[18]
    set_title(s, "Parameter Analysis: Protocol, Fine-tuning, Crop Choice")
    wipe(s)
    rows = [["Setting", "Accuracy", "Macro-F1"],
            ["Compact CNN, held-out validation (3 seeds)", F.pm(C), f"{C['macro_f1']['mean']:.3f}"],
            ["  shipped protocol: test folder as validation", p1(CS["accuracy"]["mean"]), f"{CS['macro_f1']['mean']:.3f}"],
            ["  no LR decay, up to 100 epochs (seed 42)", p1(CT["accuracy"]["mean"]), f"{CT['macro_f1']['mean']:.3f}"],
            ["MobileNetV2, head only (3 seeds)", F.pm(MB, "head_only_accuracy"), f"{MB['head_only_macro_f1']['mean']:.3f}"],
            ["MobileNetV2, + top-30-layer fine-tune", F.pm(MB), f"{MB['macro_f1']['mean']:.3f}"],
            ["Heuristic: crop chosen / 'general'", f"{F.pm(HC)} / {F.pm(HG)}", f"{HC['macro_f1']['mean']:.3f} / {HG['macro_f1']['mean']:.3f}"]]
    ftable(s, 0.55, 1.9, [4.6, 2.6, 1.3], rows, size=12, row_h=0.5, align=["l", "c", "c"], first_bold=False)
    K.picture(s, F.fig("f04_cnn_training_curves.png"), 9.2, 1.9, 3.7, 1.7)
    ftext(s, 0.55, 5.6, 12.2, 1.3, bl([
        "Selecting the checkpoint on the test folder (the shipped script) inflates the CNN by 1.6 points on the seed measured; it did not change the conclusion.",
        f"The CNN under-fits (training accuracy {F.pm(C, 'train_accuracy')}), so longer training or no LR decay did not help; transfer learning adds about 38 points.",
        "Fine-tuning adds only 1.6 points over the trained head; choosing the crop helps the heuristic but triggers defect D1.",
    ], 4), size=13)
    notes[19] = "Protocol effects. The big lever is the pre-trained backbone, not the training schedule."

    # ---- 20 performance & testing
    s = S[19]
    set_title(s, "Performance, Testing & Defects")
    wipe(s)
    rows = [["Check", "Result"],
            ["API smoke test", f"{F.N_SMOKE} / {F.N_SMOKE} pass"],
            ["Unit, API edge and security tests", f"{E['total']} checks: {E['PASS']} pass, {E['FAIL']} fail, {E['DEFECT']} defects"],
            ["Browser UI checks", f"{F.N_UI} passed (frontend session; not re-run here)"],
            ["Detect, 100 real photos", f"median {DC['median']:.0f} ms, p95 {DC['p95']:.0f} ms (client, 127.0.0.1)"],
            ["Other API calls", f"median {LAT['get_health_ms']['median']:.0f}-{LAT['get_diseases_ms']['median']:.0f} ms"],
            ["CPU inference per photo", f"CNN {C['latency_ms_median']['mean']:.0f} ms, MobileNetV2 {MB['latency_ms_median']['mean']:.0f} ms"]]
    ftable(s, 0.55, 1.9, [2.7, 4.6], rows, size=12, row_h=0.55, first_bold=True)
    fbox(s, 8.1, 1.9, 4.7, 4.85, fill=K.FZEBRA)
    ftext(s, 8.3, 2.0, 4.35, 4.7, [("Defects recorded", {"bold": True, "color": K.FNAVY, "size": 15, "space_after": 5})] + [(t, {"space_after": 6}) for t in [
        "D1 10 of 19 crop keys crash the engine (HTTP 400)",
        "D2 top-3 scores sum to up to 112 %",
        "D3 default token secret is public",
        "D4 no login rate limit",
        "D5 train.py validates on test, shifts grape labels",
        "D6 docstring says 1.1 M parameters, model has 189,655",
        "D7 reported latency padded by 40 ms"]], size=14)
    ftext(s, 0.55, 5.9, 7.3, 0.9, "Not measured: concurrent load, many users, a field trial, a user study. Security checks passed: hashed passwords, forged / expired tokens refused, owner checks, 10 MB limit, path traversal blocked.", size=12, color=K.FNAVY, italic=True)
    notes[20] = "Tests pass for the plumbing; the defects are about the engine and defaults. Do not hide them."

    # ---- 21 comparison with base paper
    s = S[20]
    set_title(s, "Comparison with Base Paper (context only)")
    wipe(s)
    rows = [["Work", "Task", "Data", "Hardware", "Reported", "Comparable?"],
            ["Foliagen [1] (base)", "Generate foliage images; train classifiers", "Soybean, tomato; generated + UAV set", "2 x RTX 6000 Ada", "Up to 98 % (5 % real added)", "No"],
            ["PD36-C [2]", "38-class CNN, 1.25 M parameters", "87 k lab-style images", "Not stated here", "99.53 % test", "No"],
            ["Kanakala [3]", "CNN / LSTM, 38 classes", "70,295 / 17,572 lab-style", "Not stated here", "CNN 96.4 % val", "No"],
            ["PlantDoc paper [4]", "VGG16, Inception on field photos", "2,598 photos, 27 classes", "V100 GPU", "44.5-70.5 % cropped", "Closest data"],
            ["This project", "Diagnosis + advice web app; measured engines", f"PlantDoc, {F.NTRAIN:,} / {F.NTEST}", "CPU only", f"{F.pm(MB)} (MobileNetV2); app {F.pm(HC)}", "-"]]
    ftable(s, 0.55, 1.9, [2.0, 2.8, 2.6, 1.6, 2.0, 1.2], rows, size=11.5, row_h=0.62)
    ftext(s, 0.55, 5.95, 12.2, 0.9, "Numbers are not comparable: the base paper generates training data for foliage classification, the lab-style sets are far easier than field photos, and hardware differs. The honest reading is that on real field photographs the achievable accuracy without cropping or more data is about 50 %, in line with the PlantDoc authors' own results.", size=12.5, color=K.FNAVY, italic=True)
    notes[21] = "Do not claim to beat any of these. The closest comparison is the PlantDoc paper, and our reference MobileNetV2 lies in its range."

    # ---- 22-24 output screens
    s = S[21]
    set_title(s, "Output – Detect and a Correct Diagnosis")
    wipe(s)
    K.picture(s, F.shot("07_detect_ready.png"), 0.55, 1.85, 6.0, 3.75, border=True)
    K.picture(s, F.shot("15_result_correct.png"), 6.8, 1.85, 6.0, 3.75, border=True)
    ftext(s, 0.55, 5.75, 6.0, 1.1, "Detect: a tomato late-blight photo from the PlantDoc test set is chosen with crop = Tomato; the 10 MB limit and the accepted formats are stated on the drop zone.", size=12.5, color=K.FNAVY)
    ftext(s, 6.8, 5.75, 6.0, 1.1, "Result: Potato early blight (high severity, urgent), top-3 list, treatments. Correct here; the score 97.2 % is a heuristic score, not a probability, as the amber note says.", size=12.5, color=K.FNAVY)
    notes[22] = "A correct case. Only 25 of the 160 photos the heuristic can answer are right, so this is the exception."
    s = S[22]
    set_title(s, "Output – Failure Cases")
    wipe(s)
    K.picture(s, F.shot("08_result.png"), 0.55, 1.85, 6.0, 3.75, border=True)
    K.picture(s, F.shot("16_error_blueberry.png"), 6.8, 1.85, 6.0, 3.75, border=True)
    ftext(s, 0.55, 5.75, 6.0, 1.1, "A tomato leaf with a large brown lesion is called Tomato healthy, 97.2 %. Five of the demo scans are lesioned leaves called healthy.", size=12.5, color=K.FNAVY)
    ftext(s, 6.8, 5.75, 6.0, 1.1, "Crop = Blueberry on a valid photo: 'The diagnosis failed. That file could not be read as an image' (defect D1, API status 400).", size=12.5, color=K.FNAVY)
    notes[23] = "Two real failures captured from the running application."
    s = S[23]
    set_title(s, "Output – Dashboard and Languages")
    wipe(s)
    K.picture(s, F.shot("09_dashboard.png"), 0.55, 1.85, 6.0, 3.75, border=True)
    K.picture(s, F.shot("17_dashboard_hindi.png"), 6.8, 1.85, 6.0, 3.75, border=True)
    ftext(s, 0.55, 5.75, 6.0, 1.1, "Dashboard with real scans: totals, healthy count, high-severity count, disease rate, quick actions and recent detections.", size=12.5, color=K.FNAVY)
    ftext(s, 6.8, 5.75, 6.0, 1.1, "Hindi interface: menus, headings and statistics are translated; sentences and the disease text stay in English (partial multilingual support).", size=12.5, color=K.FNAVY)
    notes[24] = "The application chrome works in three languages; the knowledge base text does not yet."

    # ---- 25 conclusion
    s = S[24]
    set_title(s, "Conclusion")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.9, bl([
        "**Delivered:** a working web application: sign-in, leaf upload, top-3 diagnosis with severity, three treatment types and prevention for 38 classes, history, CSV / PDF export, dashboard, analytics and a three-language interface; FastAPI layer over the original Flask product.",
        f"**Measured:** the shipped heuristic reaches {F.pm(HC)} on PlantDoc test photos and fails on {F.pct(HC['failed_share']['mean'])}; the shipped CNN recipe {F.pm(C)}; MobileNetV2 {F.pm(MB)}. {F.N_SMOKE} + {E['PASS']} checks pass; {E['DEFECT']} defects found.",
        "**Objectives:** 1 met, 2 partly, 3 trained but not accurate and not shipped, 4 treatment mapping met (no fertiliser dose), 5 met for the web interface and partly for language, 6 per-class accuracy measured, advice not validated.",
        "**Limits:** PlantDoc only, one small dataset, no field trial; advice not checked by an agronomist; not a substitute for an expert.",
    ], 12), size=19)
    notes[25] = "Be explicit: the application works, the engine in it does not diagnose reliably yet."

    # ---- 26 future scope
    s = S[25]
    set_title(s, "Future Scope")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.9, bl([
        "Install a transfer-learning model (MobileNetV2 class, about 50 % here) in models/ and show its probabilities honestly; add Grad-CAM to show what the model looked at.",
        "Fix D1 to D7: fewer than three candidates, score normalisation, secret from the environment, login throttling, train.py labels and validation.",
        "More and better data: own field photographs, cropped leaves, more images for rare classes, Foliagen-style generated foliage for augmentation.",
        "Add the proposed fertiliser, yield and weather modules; translate the disease and treatment text into Hindi and Marathi.",
        "Agronomist review of every treatment and dose; a pilot with farmers; offline use on a phone.",
    ], 14), size=19)
    notes[26] = "The first two follow directly from the findings."

    # ---- 27 references
    s = S[26]
    set_title(s, "References")
    wipe(s)
    ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 13, 19, 20]
    ftext(s, 0.55, 1.85, 6.0, 5.0, [(f"[{n}] {REFS[n - 1]}", {"space_after": 3}) for n in ids[:7]], size=12)
    ftext(s, 6.8, 1.85, 6.0, 5.0, [(f"[{n}] {REFS[n - 1]}", {"space_after": 3}) for n in ids[7:]], size=12)
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
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


NEED_TEXT = "a system that identifies crop disease from a leaf photograph and returns treatment advice in the farmer's own language."

if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "16.Final_PPT.pptx")))
