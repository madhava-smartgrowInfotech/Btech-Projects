"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx."""

import os

from pptx import Presentation

from . import facts as F
from . import pptkit as K
from .deck_review1 import agenda, prepare, set_title, thank_you, title_slide, wipe

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"


def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}
    hc, hg, c, mb, bl, lat = F.HC, F.HG, F.C, F.MB, F.BL, F.LAT
    rf = bl["random_forest"]

    # ---- 1 title
    title_slide(S[0], "A leaf-photograph diagnosis web application with knowledge-based treatment advice, and a measured study of what it recognises",
                "REVIEW 2  \u00b7  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = "This review shows how the system is designed and built, what is implemented, the first measured results on PlantDoc field photographs, and the open problems."

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and dataset"), ("03", "Preprocessing and models"), ("04", "Training and decision logic"),
               ("05", "Data flow, database and UML"), ("06", "Technology stack"), ("07", "Implementation progress and results"),
               ("08", "Output screens and testing"), ("09", "Challenges and next steps")],
           [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Farmers cannot identify crop disease early, expert help is not at hand, existing tools classify without advising, and advice in English alone is unusable for many.", K.ORANGE, "!"),
        ("Proposed system", "Photo + crop in; disease, severity, chemical, organic and cultural treatment out, from a 38-class knowledge base, through a web application in English, Hindi and Marathi.", K.BLUE, "i"),
        ("Base paper link", "Pakka et al. (2026) generate foliage images to train field classifiers. We do not implement their generator; we take the motivation (field images are scarce) and build the farmer-facing diagnosis and advice around a classifier.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, 4.9, t, b_, col, gl, body_size=17)
    notes[3] = "One-minute recap of Review 1. The base paper is about training data for in-field classification; our contribution is the application and an honest measurement."

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.6, 1.3, 7.2, 5.65)
    K.text(s, 8.0, 1.5, 4.75, 5.3, [
        ("**Three tiers**", {"space_after": 8}),
        ("Presentation: React 18 app, 12 page components, port 5416.", {"bullet": True}),
        ("Application: FastAPI, 16 routes under /api, HMAC bearer token, port 8416.", {"bullet": True}),
        ("Domain: the original Flask product (diagnosis, knowledge base, init_db), imported unchanged.", {"bullet": True}),
        ("Storage: SQLite (users, results) and an uploads folder.", {"bullet": True}),
        ("No trained network is installed: the engine is a colour/texture heuristic.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[4] = "The FastAPI layer imports the same detection and knowledge modules as the Flask app and shares its database file, so both front ends see the same accounts and scans."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: end-to-end workflow")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.2, [("Photo + crop", K.NAVY), ("Validate upload", K.PURPLE), ("Resize + features", K.PURPLE), ("Candidate classes", K.GREEN),
                                      ("Score, top-3", K.ORANGE), ("Knowledge card", K.BLUE), ("Save + show", K.NAVY)], size=13, gap=0.22)
    for i, (t, b_) in enumerate([("Two engines, one contract", "The heuristic ships; a Keras model from train.py is loaded instead if models/ holds one. Both return a top-3 list that the knowledge base turns into advice."),
                                 ("Measured offline", "scripts/run_experiments.py scores the heuristic, the compact CNN, MobileNetV2 and classical baselines on the same 236 test photos."),
                                 ("Reproducible", "Seeds 42, 43, 44; JSON output feeds every figure and number in the documents.")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 3.1, 3.85, 3.0)
        K.text(s, x + 0.25, 3.25, 3.4, 0.5, t, size=18, color=K.INK, bold=True)
        K.text(s, x + 0.25, 3.95, 3.4, 2.1, b_, size=17, color=K.TXT)
    notes[5] = "Top row is the runtime path of every scan (diagram 2 of the report); the boxes below explain how the engines relate and how they were measured."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Dataset: PlantDoc field photographs")
    wipe(s)
    for i, (v, l, col) in enumerate([(f"{F.NTRAIN:,}", "training photos, 28 folders", K.BLUE), (str(F.NTEST), "test photos, 27 folders", K.GREEN),
                                     ("13", "crops (14 in the 38-class label set)", K.ORANGE), ("2 to 180", "photos per training class", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, col, vsize=28, lsize=12)
    K.text(s, 0.6, 3.0, 7.3, 3.9, [
        ("Source: PlantDoc (Singh et al., 2020), CC-BY-4.0, web-scraped photographs with real backgrounds, lighting and blur [4].", {"bullet": True}),
        ("Released split kept intact: 2,342 train and 236 test. The spider-mite folder has 2 training photos and no test photo, so test scores cover 27 classes.", {"bullet": True}),
        ("All 28 folders map one-to-one to the product's 38 classes (PLANTDOC_MAP); 10 knowledge-base classes have no photos here.", {"bullet": True}),
        ("The test split has 90 healthy and 146 diseased photos; always answering the largest class (corn leaf blight) scores 5.1 %.", {"bullet": True}),
        (f"Scored on the 2,342 training photos too, the heuristic gets {F.pct(F.H['train_crop_hint']['accuracy']['mean'])}, so its weakness is not a small-test-set accident.", {"bullet": True}),
    ], size=14, color=K.INK, space_after=8)
    K.picture(s, F.fig("f09_class_distribution.png"), 8.1, 2.85, 4.63, 4.1)
    notes[6] = "PlantDoc is small and hard, which is the point: the literature numbers near 99 percent are for laboratory images. The original authors report 44.5 to 70.5 percent on cropped leaves."

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Data preprocessing")
    wipe(s)
    K.card(s, 0.6, 1.45, 5.95, 5.35, "In the application (inference.py)",
           [("Accept JPG, PNG, JPEG, WEBP up to 10 MB; reject empty or unreadable files.", {"bullet": True, "space_after": 6}),
            ("Convert to RGB, resize to 256 x 256, scale to [0, 1].", {"bullet": True, "space_after": 6}),
            ("Compute six numbers: green share (g > r + 0.03 and g > b + 0.01), brown, yellow, dark (mean < 0.25), white (min > 0.72) and the global standard deviation.", {"bullet": True, "space_after": 6}),
            ("Candidate classes come from the crop the farmer chose; 'general' keeps all 38.", {"bullet": True})], K.BLUE, "1", body_size=15, bullets=True)
    K.card(s, 6.78, 1.45, 5.95, 5.35, "For training (train.py and our experiments)",
           [("Resize every photo to 224 x 224 (bilinear, no cropping), keep as uint8.", {"bullet": True, "space_after": 6}),
            ("In-model augmentation, active only in training: horizontal flip, rotation 0.08, zoom 0.1, contrast 0.1.", {"bullet": True, "space_after": 6}),
            ("Rescale to [0, 1] inside the network; MobileNetV2 uses its own [-1, 1] scaling.", {"bullet": True, "space_after": 6}),
            ("10 % stratified validation split carved from the training folder for early stopping; the test folder is never touched.", {"bullet": True})], K.GREEN, "2", body_size=15, bullets=True)
    notes[7] = "No leaf cropping or segmentation is done; photos are used as scraped. This is a limit: PlantDoc's authors show cropping helps."

    # ---- 8 model
    s = S[7]
    set_title(s, "Model: three engines")
    wipe(s)
    rows = [["Engine", "What it is", "Size"],
            ["Heuristic (shipped)", "Hand-written score per class from six colour/texture numbers; confidence squeezed into 0.62 to 0.99", "no learned parameters"],
            ["Compact CNN (train.py)", "5 separable-conv blocks (32, 64, 128, 256, 256 filters) with batch norm, max-pool and dropout 0.15, global average pooling, dropout 0.3, dense 256, softmax over 28 classes", f"{c['params']['mean']:,.0f} parameters, 2.4 MB"],
            ["MobileNetV2 reference", "ImageNet weights, new softmax head; head trained first, then the top 30 layers fine-tuned at 1e-4", f"{mb['params']['mean']:,.0f} parameters"]]
    K.table(s, 0.6, 1.45, [2.7, 6.6, 2.83], rows, font_size=14, row_h=1.0, first_bold=True)
    K.text(s, 0.6, 5.65, 12.1, 1.3, "The docstring of train.py calls the compact CNN 'about 1.1M parameters' and 'PD36-C-style'; it has 189,655 parameters and is not the PD36-C of [2], which has 1,250,694. Neither CNN is part of the shipped application.", size=15, color=K.TXT, italic=True)
    notes[8] = "The shipped engine has no training. The compact CNN is the repository's own training recipe; MobileNetV2 is our reference to show what the data allows with transfer learning."

    # ---- 9 training configuration
    s = S[8]
    set_title(s, "Training configuration")
    wipe(s)
    rows = [["Setting", "Compact CNN", "MobileNetV2"],
            ["Optimiser, rate", "Adam 1e-3, halved on validation-loss plateau", "Adam 1e-3 (head), 1e-4 (fine-tune)"],
            ["Batch, input", "32, 224 x 224", "32, 224 x 224"],
            ["Epochs", "up to 60, early stop on validation accuracy (patience 8)", "head up to 20 (patience 4), fine-tune up to 12 (patience 3)"],
            ["Validation", "10 % stratified split of the training folder", "same split"],
            ["Seeds", "42, 43, 44 (mean ± std reported)", "42, 43, 44"],
            ["Time on CPU", f"{c['train_seconds']['mean']:.0f} s per run (mean {c['epochs_run']['mean']:.0f} epochs)", f"{mb['train_seconds']['mean']:.0f} s per run"],
            ["Machine", "Intel Core i5-12500, 15.7 GB RAM, no GPU; TensorFlow 2.21", "same"]]
    K.table(s, 0.6, 1.4, [2.4, 5.0, 4.73], rows, font_size=13, row_h=0.6, first_bold=True)
    K.text(s, 0.6, 6.35, 12.1, 0.6, "Also run once: the shipped protocol (test folder as validation) and a no-LR-decay variant; both stay at 12.7 to 13.6 %.", size=14, color=K.TXT, italic=True)
    notes[9] = "Training is cheap on this data (a few thousand photos). Other jobs shared the CPU, so times are indicative."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic")
    wipe(s)
    K.picture(s, F.diag("10_core_algorithm_flowchart.png"), 0.6, 1.3, 5.6, 5.65)
    K.text(s, 6.5, 1.5, 6.25, 5.4, [
        ("**Score.** Healthy classes reward green share and penalise brown, yellow and dark pixels; diseased classes reward brown, yellow, dark, white pixels and little green, plus small bonuses by disease name (rust, mildew, blight...).", {"bullet": True, "space_after": 8}),
        ("**Confidence.** The top score is mapped to 0.62 to 0.99; the second and third scores come from the image hash. The three values add up to more than 100 % on most photos.", {"bullet": True, "space_after": 8}),
        ("**Advice.** The top-1 class selects a knowledge card: severity, 3 treatments, prevention, 'urgent' for high severity.", {"bullet": True, "space_after": 8}),
        ("**Failure.** A crop with fewer than 3 candidate classes raises an error (defect D1).", {"bullet": True}),
    ], size=14, color=K.INK)
    notes[10] = "The flowchart is the real predict() path. When a trained Keras or ONNX model is present, the left branch replaces the scoring steps."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, F.diag("04_dfd_level1.png"), 0.6, 1.3, 7.0, 5.65)
    rows = [["Module", "Role"], ["inference.py", "predict(): heuristic or Keras / ONNX"], ["disease_db.py", "38 classes, treatment cards"], ["app.py, config.py", "init_db(), limits, Flask pages"],
            ["backend/main.py", "FastAPI routes, token, exports"], ["train.py", "offline CNN training"], ["frontend/src", "12 pages, API client, i18n"],
            ["scripts/", "tests, experiments, captures"]]
    K.table(s, 7.9, 1.5, [2.0, 2.83], rows, font_size=12, row_h=0.55)
    notes[11] = "Level-1 data flow: authenticate, manage profile, diagnose, browse the guide, history and exports, dashboard. The knowledge base is code, not a table."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database design and UML")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.6, 1.35, 5.9, 4.9)
    K.picture(s, F.diag("06_uml_class_diagram.png"), 6.7, 1.3, 6.0, 5.5)
    K.text(s, 0.6, 6.4, 5.9, 0.6, "Two SQLite tables, users 1 : N results; images are files.", size=13, color=K.TXT, align="c", italic=True)
    notes[12] = "Two tables created by init_db(). The class diagram shows modules and the two entities because the code has no ORM classes."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    rows = [["Layer", "Technology"],
            ["Diagnosis", "Python 3.11, NumPy, Pillow; TensorFlow 2.21 / Keras 3 for the offline CNNs; scikit-learn and OpenCV for the baselines"],
            ["API", "FastAPI, uvicorn, python-multipart; HMAC-signed bearer token; werkzeug password hashes; reportlab for PDF"],
            ["Original product", "Flask 3.1 templates (still runnable on port 5000), SQLite"],
            ["Front end", "React 18, TypeScript 5.9, Vite 8, Tailwind 4, TanStack Query, Recharts, GSAP; EN / HI / MR strings"],
            ["Testing and capture", "Python check scripts (smoke, edge), Playwright with Chrome for screenshots and UI checks"],
            ["Hardware", "Windows 11, Intel Core i5-12500, 15.7 GB RAM, no GPU"]]
    K.table(s, 0.6, 1.45, [2.7, 9.43], rows, font_size=15, row_h=0.74, first_bold=True)
    notes[13] = "Everything is open source and starts with run.bat; no GPU or cloud service is needed."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["React interface (12 pages, light and dark)", "Done", "18 screenshots, build passes, 55 UI checks earlier"],
            ["FastAPI service (16 routes)", "Done", f"{F.N_SMOKE}/{F.N_SMOKE} smoke checks pass"],
            ["Knowledge base, 38 classes", "Done", "26 curated cards, 3 treatments each"],
            ["Heuristic diagnosis engine", "Done, weak", "9.1 % top-1; fails for 10 of 19 crop keys"],
            ["CNN training script", "Done, defects", "label shift and test-set selection (D5, D6)"],
            ["Trained network inside the app", "Not done", "MobileNetV2 50.3 % is offline only"],
            ["Hindi / Marathi", "Partial", "interface strings only; advice text in English"],
            ["Fertiliser, yield, weather advice", "Not done", "proposed in the abstract"]]
    K.table(s, 0.6, 1.4, [4.7, 1.9, 5.53], rows, font_size=13, row_h=0.6)
    notes[14] = "State of the code base. The honest gaps are the missing trained model in the application, fertiliser, yield and weather advice, and translated advice text."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results: PlantDoc test split")
    wipe(s)
    for i, (v, l, col) in enumerate([(F.mean_pct(hc), "shipped heuristic, top-1 (crop chosen)", K.TXT),
                                     (F.mean_pct(c), "compact CNN of train.py (3 seeds)", K.ORANGE), (F.pct(rf["accuracy"]), "random forest on colour/texture", K.GREEN),
                                     (F.mean_pct(mb), "MobileNetV2 transfer (3 seeds)", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, col, vsize=28, lsize=11)
    K.picture(s, F.fig("f01_model_comparison.png"), 0.6, 2.9, 7.9, 4.05)
    K.card(s, 8.7, 2.95, 4.03, 3.95, "Reading",
           f"Chance is 2.6 % on 38 classes. MobileNetV2: macro-F1 {mb['macro_f1']['mean']:.2f}, top-3 {F.mean_pct(mb, 'top3_accuracy')}, healthy-vs-diseased {F.mean_pct(mb, 'healthy_vs_diseased_accuracy')}. "
           f"The shipped heuristic does not beat chance on healthy-vs-diseased ({F.mean_pct(hc, 'healthy_vs_diseased_accuracy')} against 61.9 % for always saying diseased). Test set: {F.NTEST} photos.", K.BLUE, "i", body_size=13)
    notes[15] = ("All figures are on the 236 PlantDoc test photos, mean of 3 seeds except the heuristic (5 hash seeds) and the random forest. "
                 "Foliagen's 98 percent and PD36-C's 99.53 percent are on other data and cannot be compared. PlantDoc's authors report 44.5 to 70.5 percent for cropped leaves.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    K.picture(s, F.shot("08_result.png"), 0.6, 1.3, 7.0, 4.4, border=True)
    K.picture(s, F.shot("15_result_correct.png"), 7.85, 1.3, 4.88, 2.75, border=True)
    K.picture(s, F.shot("16_error_blueberry.png"), 7.85, 4.2, 4.88, 2.75, border=True)
    K.text(s, 0.6, 5.85, 7.0, 1.3, "Left: a tomato late-blight leaf scored 'healthy 97.2 %' by the heuristic engine (failure). Right: a correct potato early-blight diagnosis with severity and treatments, and the error shown for crop = Blueberry on a valid photo (defect D1).", size=12, color=K.TXT)
    notes[16] = "Real screenshots of the running application with PlantDoc test photos. The successes and the failures are shown on purpose."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, col) in enumerate([(f"{F.N_SMOKE}/{F.N_SMOKE}", "API smoke checks pass", K.GREEN), (f"{F.N_EDGE_PASS} + {F.N_EDGE_DEFECT}", "edge checks: passes + defects found", K.ORANGE),
                                     (f"{lat['detect_client_ms']['median']:.0f} ms", "median detect round trip, 127.0.0.1", K.BLUE), ("55", "UI checks (earlier session)", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, col, vsize=26, lsize=12)
    rows = [["Observation", "Where it shows"],
            ["10 of the engine's 19 crop keys (9 of the 18 offered in the web form) make the heuristic fail: 32.2 % of test photos get no answer", "D1, screenshot 16"],
            ["Three displayed scores add up to more than 100 % on 82 % of answerable photos", "D2, Chapter 7"],
            ["A token signed with the public default secret is accepted; login has no rate limit", "D3, D4"],
            ["Passwords hashed, forged tokens, bad uploads, path tricks and foreign origins all refused", "46 edge checks pass"]]
    K.table(s, 0.6, 3.05, [8.4, 3.73], rows, font_size=14, row_h=0.72)
    notes[17] = f"{F.N_SMOKE} smoke checks and {F.N_EDGE} edge checks ({F.N_EDGE_PASS} pass, {F.N_EDGE_DEFECT} reproduce defects). The UI checks were run in the earlier frontend session."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "What we found / did"],
            ["No trained model ships; the app answers with a heuristic", "Measured it (9.1 %), trained the repository's CNN (12.0 %) and a MobileNetV2 reference (50.3 %)"],
            ["train.py validates on the test folder and shifts two grape labels", "Our runs use a held-out validation split; defect D5 recorded"],
            ["PlantDoc is small, noisy and imbalanced (2 to 180 per class)", "Stratified splits, 3 seeds, per-class scores; no cropping yet"],
            ["Displayed confidence is not evidence", "Documented with a chart; calibration listed as future work"],
            ["Advice is generic and not agronomist-reviewed", "Stated as a limit; expert review planned"]]
    K.table(s, 0.6, 1.45, [5.4, 6.73], rows, font_size=14, row_h=0.85)
    notes[18] = "Each challenge changed either the experiment design or how results are reported."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Install a real model", "Export the MobileNetV2 weights and labels.json to agrivision/models/ so the application stops using the heuristic.", K.BLUE, "1"),
        ("Fix the defects", "Crop options with few classes, score sums, secret and rate limit, train.py labels and docstring.", K.GREEN, "2"),
        ("Improve accuracy", "Crop and segment leaves, try EfficientNet-style backbones, add data, report per-crop scores.", K.ORANGE, "3"),
        ("Complete the scope", "Translate advice text, add fertiliser, weather and yield advice, and ask an agronomist to review.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.09, 1.6, 2.85, 4.4, t, b_, col, gl, body_size=17)
    notes[19] = "Plan to the final review. None of these items is claimed as done."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Likely questions: why the shipped engine is weak; why PlantDoc; why not 99 percent; what is installed in the app today."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
