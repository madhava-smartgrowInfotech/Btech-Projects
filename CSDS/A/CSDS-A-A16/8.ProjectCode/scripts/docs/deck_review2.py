"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx.

All numbers come from facts.py (experiments/**/metrics.json, pytest junit file); nothing is typed in by hand except configuration constants
that are read from the code (layer sizes, learning rates, Haar parameters) and library pins read from backend/requirements.txt.
    python -m scripts.docs.deck_review2        # from 8.ProjectCode
"""
import os

from pptx import Presentation

from . import facts as F
from . import pptkit as K
from .deck_review1 import prepare, set_title, wipe, agenda, title_slide, thank_you, trim, render  # noqa: F401

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"


def shot_box(slide, name, x, y, w, h, caption):
    """Real screenshot in a w x h area with a one-line caption under it."""
    K.picture(slide, F.shot(name), x, y, w, h - 0.34, border=True)
    K.text(slide, x, y + h - 0.3, w, 0.3, caption, size=11, color=K.TXT, align="c", italic=True)


def lat(label_start):
    for r in F.APIM["latency"]:
        if r["label"].startswith(label_start):
            return r
    raise KeyError(label_start)


def pc(x, d=2):
    return f"{x * 100:.{d}f} %"


# ------------------------------------------------------------------ the deck
def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}
    B, N, G, SY, D, DT = F.BASE, F.FIN, F.GAN, F.SYN, F.DATA, F.DET
    ra, sa = F.abl_vals("real_only", "accuracy"), F.abl_vals("synth", "accuracy")
    rf, sf = F.abl_vals("real_only", "macro_f1"), F.abl_vals("synth", "macro_f1")
    c = N["compound_on_real_test"]
    auc = SY["final_model"]["0.5"]["compound_roc_auc_macro"]
    probes_ok, probes_total = F.APIM["probes_ok"], F.APIM["probes_total"]
    n_tests = F.TESTS["tests"]
    an = lat("POST /api/analyze anonymous")

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: a conditional GAN, an 18-output multi-label CNN and a FastAPI + Next.js application",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS", 28)
    notes[1] = ("This review shows how Mosaic is designed and built, what is implemented, the first measured results and the open items. "
                "Introduce the four team members and the guide. The headline is honest: the application works end to end, the basic-emotion head is a plain FER2013 CNN, "
                "and the compound-emotion head does not yet recognise compound emotions.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and data"), ("03", "Preprocessing and model"), ("04", "Training and decision logic"),
               ("05", "Data flow, database and UML"), ("06", "Technology stack"), ("07", "Progress and preliminary results"),
               ("08", "Output screens and testing"), ("09", "Challenges and next steps")],
           [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    Wd = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Existing systems recognise only single basic emotions, although real expressions often mix several. Complex-emotion training data is scarce, and expression-editing GANs distort identity.", K.ORANGE, "!"),
        ("Proposed system", "Mosaic detects a face, classifies it with one CNN that has 18 sigmoid outputs (7 basic and 11 compound emotions), trains the compound outputs on faces synthesised by a conditional GAN, and serves the result through a FastAPI service and a Next.js console with accounts and history.", K.BLUE, "i"),
        ("Base paper link [1]", "Khine et al. (IEEE Access, 2025) generate identity-preserving mixed expressions with cEmoGANs and train a multi-label CNN on them. Mosaic follows the two-stage idea on FER2013 but has no identity encoder, and its recogniser is scored on real test faces.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (Wd + 0.29), 1.6, Wd, 4.8, t, b_, col, gl, body_size=16)
    notes[3] = "Recap of Review 1. We say plainly what is borrowed (analysis by synthesis, multi-label sigmoid CNN) and what is not implemented (the identity-preserving encoder)."

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, trim(F.diag("01_system_architecture.png"), "r2_01"), 0.6, 1.3, 7.2, 5.7)
    K.text(s, 8.0, 1.45, 4.75, 5.4, [
        ("**Four tiers, one process**", {"space_after": 8}),
        ("Console: Next.js 16 + React 19, port 3000; landing, login, register, analyze (upload or webcam), history.", {"bullet": True}),
        ("API: FastAPI, eight JSON endpoints plus static thumbnails; the code defaults to port 8000.", {"bullet": True}),
        ("ML modules: Haar face detector, 64 x 64 preprocessing, EmotionCNN with 18 outputs; the GAN is used only at training time.", {"bullet": True}),
        ("State: SQLite (users, analyses), checkpoint files and a thumbnail folder. No external service is called at run time.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[4] = "One uvicorn process serves the API and loads the classifier once at start-up. Accounts and history are in SQLite; uploaded photos are never stored, only the cropped grayscale face."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: train offline, then one pass per image")
    wipe(s)
    K.picture(s, trim(F.diag("02_high_level_workflow.png"), "r2_02"), 0.6, 1.4, 7.4, 4.9)
    for i, (t, b_) in enumerate([("Train", "FER2013 backbone, conditional GAN on 2,800 faces, 2,200 synthetic compound faces, final 18-output CNN."),
                                 ("Serve", "Upload, Haar face crop, 64 x 64 tensor, CNN, sigmoid, sorted basic and compound lists, dominant emotion."),
                                 ("Evaluate", "Accuracy and macro-F1 on 7,178 real test faces; seeded ablation with and without synthetic data; GAN fidelity; API probes.")]):
        y = 1.4 + i * 1.78
        K.box(s, 8.3, y, 4.43, 1.65)
        K.text(s, 8.45, y + 0.07, 4.15, 0.4, t, size=15, color=K.INK, bold=True)
        K.text(s, 8.45, y + 0.42, 4.15, 1.2, b_, size=12.5, color=K.TXT)
    K.text(s, 0.6, 6.45, 7.4, 0.45, "High-level workflow of run_pipeline.py and one request to /api/analyze.", size=12, color=K.TXT, align="c", italic=True)
    notes[5] = "Offline training happens once; every request then costs one Haar detection and one CNN forward pass (about 19 ms median over HTTP on this PC)."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Dataset: FER2013 and the synthetic compound faces")
    wipe(s)
    for i, (v, l, col) in enumerate([(f"{D['n_train']:,}", "FER2013 training faces (48 x 48 grayscale)", K.ORANGE),
                                     (f"{D['n_test']:,}", "FER2013 test faces, basic labels only", K.BLUE),
                                     ("2,800", "real faces (400 per class) used to train the GAN", K.GREEN),
                                     ("2,200", "synthetic compound faces (11 classes x 200)", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, col, vsize=26, lsize=11)
    K.picture(s, trim(F.fig("fig_class_distribution.png"), "r2_cd"), 0.6, 2.85, 6.2, 3.3)
    rows = [["", "Detail"],
            ["Source", "Hugging Face mirror Jeneral/fer-2013 (tag apache-2.0); original FER2013 by Goodfellow et al. [11]"],
            ["Labels", "angry, disgust, fear, happy, sad, surprise, neutral; no compound labels exist"],
            ["Imbalance", f"disgust is {D['class_counts']['train']['disgust'] / D['n_train'] * 100:.1f} % of training; always-'happy' scores {pc(D['test_majority_baseline'], 1)}"],
            ["Synthetic", "target = both component bits + the compound bit (three bits set)"]]
    K.table(s, 7.0, 2.85, [1.35, 4.4], rows, font_size=11.5, row_h=0.6, first_bold=True)
    K.text(s, 0.6, 6.3, 12.13, 0.7, "The base paper uses CK+, JAFFE and MUG (laboratory sets) with morphed two-emotion ground truth; Mosaic uses FER2013 because it is open and unconstrained, but then has no real compound labels to test against.",
           size=12, color=K.TXT, italic=True)
    notes[6] = "FER2013 is the only dataset used. The test split is also what the training script prints as validation accuracy; it is never used to pick a model."

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Preprocessing: from photo to a 64 x 64 tensor")
    wipe(s)
    K.flow(s, 0.6, 1.45, 12.13, 1.0, [("Upload (JPEG / PNG)", K.NAVY), ("Decode, BGR", K.PURPLE), ("Haar cascade", K.PURPLE),
                                       ("Largest face, gray", K.GREEN), ("Resize 64 x 64", K.GREEN), ("Scale to [-1, 1]", K.ORANGE)], size=12, gap=0.22)
    for i, (v, l, col) in enumerate([("64 x 64", "model input; native FER2013 faces are 48 x 48", K.BLUE),
                                     ("0 % -> 54 %", "Haar detection of native 48 px faces vs 2x upscale (1,000 test faces)", K.GREEN)]):
        K.tile(s, 0.6 + i * 6.2, 2.8, 5.95, 1.25, v, l, col, vsize=28, lsize=12)
    K.text(s, 0.6, 4.3, 12.13, 2.7, [
        ("Haar settings: scale factor 1.1, 5 neighbours, minimum face 40 x 40; the largest detection is kept, so a photo with several faces analyses only one.", {"bullet": True}),
        ("Training faces are aligned 48 x 48 FER crops resized to 64; serving faces are Haar crops of a photo, so the two are framed differently.", {"bullet": True}),
        (f"Measured effect: on the {DT['detected_at_3x']} faces detected after a 3x upscale, accuracy is {pc(DT['accuracy_via_haar_crop_on_detected'], 1)} through the Haar crop and {pc(DT['accuracy_direct_64px_on_same_images'], 1)} when the same images are resized directly.", {"bullet": True}),
        ("No augmentation, face alignment or histogram equalisation is applied; no photo is stored.", {"bullet": True}),
    ], size=16, color=K.INK, space_after=9)
    notes[7] = "app/ml/face.py and inference._preprocess. The detector is the weakest link: it misses all native-size FER faces and about half of upscaled ones."

    # ---- 8 model
    s = S[7]
    set_title(s, "Model: EmotionCNN (18 outputs) and the conditional GAN")
    wipe(s)
    n18 = N["parameters"]
    n7 = n18 - (256 * 18 + 18) + (256 * 7 + 7)
    rows = [["Component", "Architecture", "Parameters"],
            ["EmotionCNN (stage 1: 7 outputs; final: 18)", "4 x [Conv 3x3 - BatchNorm - ReLU - MaxPool] with 32, 64, 128, 128 channels; Flatten 2,048; FC 256 + ReLU; Dropout 0.4; FC out", f"{n7:,} / {n18:,}"],
            ["ConditionalGenerator", "noise 100 + condition 7 -> 5 x ConvTranspose (256, 128, 64, 32, 1), BatchNorm + ReLU, Tanh; 64 x 64 output", f"{G['generator_parameters']:,}"],
            ["ConditionalDiscriminator", "4 x Conv (32 - 256) with LeakyReLU, condition projected to 16 values, one logit", "not reported"],
            ["Loss and outputs", "stage 1 softmax cross-entropy with class weights; final BCE-with-logits on 18 sigmoids; GAN BCE with real label 0.9", ""]]
    K.table(s, 0.6, 1.4, [3.0, 7.0, 2.13], rows, font_size=12.5, row_h=0.78, first_bold=True)
    K.text(s, 0.6, 5.5, 12.13, 1.4, [
        ("**Why this design**: a small CNN trains on a CPU in minutes, sigmoid outputs let one face carry several labels, and a conditional GAN is the cheapest way to make compound-labelled training faces.", {"bullet": True, "space_after": 6}),
        ("**What is missing from the base paper's design**: its encoder that keeps identity, and its 6-dimensional multi-hot generator label; Mosaic trains the GAN with one-hot labels and blends two conditions only when synthesising.", {"bullet": True}),
    ], size=14, color=K.INK)
    notes[8] = "Layer shapes are read from backend/app/ml/classifier_model.py and gan_model.py. The 7-output parameter count is the 18-output count minus the larger last layer."

    # ---- 9 training configuration
    s = S[8]
    set_title(s, "Training and evaluation configuration")
    wipe(s)
    mins = F.ABL["synth_s1"]["config"]["minutes"]
    rows = [["Stage", "Settings", "Result / time"],
            ["1  Backbone", "EmotionCNN(7), Adam 1e-3, batch 256, 5 epochs, class-weighted CE, 28,709 train", f"test accuracy {pc(B['accuracy'])}"],
            ["2  cEmoGAN", "Adam 2e-4 (0.5, 0.999), batch 64, 10 epochs, 400 faces per class, real label 0.9", "final D loss 0.7731, G loss 3.7240"],
            ["3  Final classifier", "EmotionCNN(18) from backbone conv weights, BCE-with-logits, Adam 5e-4, batch 256, 5 epochs, 28,709 real + 2,200 synthetic", f"basic accuracy {pc(N['accuracy'])}; 10 min 37 s"],
            ["Seeded ablation", "same recipe, seeds 1-3, with and without the 2,200 synthetic faces; extra runs at 50 and 800 per class (seed 1)", f"about {mins:.0f} min per run"],
            ["Machine", "Intel Core i5-12500, 15.7 GB RAM, CPU only, Windows 11; PyTorch 2.14.1 CPU; other jobs shared the CPU", ""]]
    K.table(s, 0.6, 1.45, [2.1, 7.0, 3.03], rows, font_size=13, row_h=0.8, first_bold=True)
    K.text(s, 0.6, 6.5, 12.13, 0.5, "Hyper-parameters are the defaults in app/ml/train_*.py; no tuning was done and no early stopping or learning-rate schedule is used.", size=12, color=K.TXT, italic=True)
    notes[9] = "The final-classifier checkpoint did not exist when the batch was received, so stage 3 was run once with the unchanged script. Everything else was produced by scripts/run_experiments.py."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: from 18 sigmoids to the answer")
    wipe(s)
    K.picture(s, trim(F.diag("10_flowchart_core_algorithm.png"), "r2_10"), 0.6, 1.3, 5.2, 5.7)
    rows = [["Step", "Rule (from inference.py)"],
            ["No face", "HTTP 200 with face_detected false, empty lists, dominant null (the contract says 422)"],
            ["Scores", "sigmoid of the 18 logits; basic = outputs 0-6, compound = outputs 7-17, each list sorted descending"],
            ["Dominant", "argmax over all 18; kind is 'basic' when its index is below 7, otherwise 'compound'"],
            ["Threshold", "none is applied: the threshold argument of analyze_image_bytes is never used"],
            ["Consequence", f"compound outputs average {c['mean_top_compound_confidence']:.4f} on real faces, so the dominant label is never a compound one"]]
    K.table(s, 6.0, 1.4, [1.55, 5.18], rows, font_size=13, row_h=0.9, first_bold=True)
    notes[10] = "This mirrors app/ml/inference.py. The decision rule is argmax, not a threshold; with sigmoid outputs trained on 7 percent compound examples the compound probabilities never win."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, trim(F.diag("04_dfd_level1.png"), "r2_04"), 0.6, 1.3, 7.0, 5.65)
    rows = [["Module", "Role"], ["app/main.py", "FastAPI app, CORS, router mounting, model load"], ["app/routers/", "auth, analyze, history, health"], ["app/deps.py, security.py", "Bearer token, bcrypt, JWT"],
            ["app/models.py, db.py", "SQLAlchemy User and Analysis"], ["app/ml/", "face, inference, CNN, GAN, training"], ["frontend/src", "Next.js pages and components"],
            ["backend/tests/", f"{n_tests} pytest tests"], ["scripts/", "experiments, screenshots, API probes"]]
    K.table(s, 7.9, 1.4, [1.95, 2.88], rows, font_size=11.5, row_h=0.52, first_bold=True)
    K.text(s, 7.9, 6.3, 4.83, 0.6, "Level-1 data flow diagram: seven processes, four stores.", size=11.5, color=K.TXT, italic=True)
    notes[11] = "Level 1: account and token, face detection, classification, ranking, storage, history, and the offline training run."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database and UML")
    wipe(s)
    K.picture(s, trim(F.diag("09_er_diagram.png"), "r2_09"), 0.6, 1.3, 5.9, 4.4)
    K.picture(s, trim(F.diag("06_uml_class.png"), "r2_06"), 6.6, 1.2, 6.2, 5.35)
    K.text(s, 0.6, 5.8, 5.9, 0.7, "SQLite database: users and analyses joined one-to-many; emotion lists are stored as JSON.", size=11.5, color=K.TXT, italic=True)
    K.text(s, 6.6, 6.6, 6.2, 0.4, "Classes and module interfaces present in the code.", size=11.5, color=K.TXT, italic=True)
    notes[12] = "Two tables only. Analyses are stored for signed-in users, including a no-face row; the uploaded photo itself is not stored."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    rows = [["Layer", "Technology (pins from requirements.txt / package.json)"],
            ["API", "Python 3.11.9; FastAPI 0.115.0, uvicorn 0.30.6, SQLAlchemy 2.0.35, pydantic 2.9.2, python-jose, passlib + bcrypt 4.0.1"],
            ["Machine learning", "PyTorch 2.4.1 (2.14.1 CPU was used in this run), torchvision, NumPy 1.26.4, pandas 2.2.2, scikit-learn 1.5.0 for metrics"],
            ["Vision", "OpenCV 4.10 (Haar cascade haarcascade_frontalface_default.xml), Pillow 10.4"],
            ["Storage", "SQLite file mosaic.db; checkpoints (.pt) and cropped-face JPEG thumbnails on disk"],
            ["Front end", "Next.js 16.3.6, React 19.2.8, TypeScript, Tailwind 4, Recharts, Framer Motion, GSAP, Lenis, Three.js, zustand, react-webcam"],
            ["Testing", f"pytest ({n_tests} tests), Playwright for the screenshots, a Python probe script for the API"]]
    K.table(s, 0.6, 1.45, [2.3, 9.83], rows, font_size=14, row_h=0.78, first_bold=True)
    notes[13] = "Pins are those in the repository. The documentation run used newer installed packages for some libraries; bcrypt had to stay at 4.0.1 because bcrypt 5 breaks passlib."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Accounts, JWT login, per-user history with delete", "Done", f"{n_tests} pytest tests; history of another user returns 404"],
            ["Upload and webcam capture, Haar detection, 18-output CNN, result screens", "Done (webcam not exercised)", f"analyze median {an['p50_ms']:.0f} ms over HTTP; 19 real screenshots"],
            ["Conditional GAN and synthetic compound faces", "Implemented, weak", f"stage-1 reads the intended emotion on {pc(G['mean_basic_conditional_accuracy'], 0)} of generated faces (chance 14 %)"],
            ["Recognition of compound emotions", "Not achieved", f"ROC-AUC {auc:.2f} on synthetic hold-out; max probability {c['mean_top_compound_confidence']:.4f} on real faces"],
            ["Identity-preserving encoder (base paper)", "Not implemented", "no encoder in the code; objective 1 only partly met"],
            ["Evaluation against a single-label baseline", "Done", f"{pc(B['accuracy'])} baseline vs {pc(N['accuracy'])}; no-synthesis control with 3 seeds"],
            ["Real compound-emotion test data", "Not available", "FER2013 has basic labels only; RAF-DB compound needs a licence"]]
    K.table(s, 0.6, 1.4, [5.2, 2.2, 4.73], rows, font_size=12.5, row_h=0.7)
    notes[14] = "State of the code base against the five objectives. The two 'not' rows are the honest gaps."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results")
    wipe(s)
    for i, (v, l, col) in enumerate([(pc(B["accuracy"], 1), "stage-1 single-label baseline, 7,178 real test faces", K.ORANGE),
                                     (pc(N["accuracy"], 1), "final 18-output model (macro-F1 " + f"{N['macro_f1']:.2f})", K.BLUE),
                                     (f"{F.mstd(ra, 1)} vs {F.mstd(sa, 1)}", "no synthetic data vs 2,200 synthetic faces, 3 seeds", K.GREEN),
                                     (f"{auc:.2f}", "compound ROC-AUC on 1,100 fresh synthetic faces (0.50 = chance)", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.35, 2.85, 1.3, v, l, col, vsize=(16 if i == 2 else 22), lsize=10.5)
    K.picture(s, trim(F.fig("fig_per_class_f1.png"), "r2_f1"), 0.6, 2.8, 6.0, 3.3)
    K.picture(s, trim(F.fig("fig_ablation.png"), "r2_ab"), 6.75, 2.8, 6.0, 3.3)
    K.text(s, 0.6, 6.2, 12.13, 0.9,
           f"The gain over the baseline comes from five more epochs, not from the GAN data: the no-synthesis control scores {pc(sum(ra) / len(ra), 1)}. Macro-F1 is {F.mstd(rf, 1)} without and {F.mstd(sf, 1)} with synthetic faces. "
           "The base paper's f-beta 0.99 / 0.99 / 0.80 is measured on its own generated images (CK+, JAFFE, MUG) and is not comparable.",
           size=12, color=K.TXT)
    notes[15] = ("Be explicit: the real-data accuracy is 58 percent on FER2013, in line with a small CNN; the synthetic data neither helps nor hurts accuracy beyond seed noise. "
                 f"Compound outputs are inert: no real test face has any compound output above 0.3 and the hold-out AUC is {auc:.3f}.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    cw, ch = 3.95, 2.62
    grid = [("08_result_happy.png", "Happy face: basic bars, compound bars near 0 %"), ("09_result_angry.png", "Angry face, 75 % confidence"),
            ("12_result_neutral_misread.png", "Neutral face read as Fear (failure case)"), ("14_result_gan_happily_surprised.png", "Generator output: compound scores only 1 %"),
            ("16_result_no_face.png", "Native 48 px face: no face detected"), ("17_history.png", "History of the signed-in user")]
    for i, (n_, cap) in enumerate(grid):
        r, col = divmod(i, 3)
        shot_box(s, n_, 0.6 + col * (cw + 0.19), 1.3 + r * (ch + 0.14), cw, ch, cap)
    K.text(s, 0.6, 6.72, 12.13, 0.3, "Real captures of the running application at 1440 x 900; inputs are FER2013 test faces and cEmoGAN output.", size=11, color=K.TXT, italic=True)
    notes[16] = "Real screenshots of the production build against the real model. The thumbnail beside the dominant label is a broken image because of a front-end defect described on the testing slide."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, col) in enumerate([(f"{n_tests} / {n_tests}", "pytest tests passed (temporary database)", K.GREEN), (f"{probes_ok} / {probes_total}", "malformed-input and abuse probes behaved as expected", K.BLUE),
                                     (f"{an['p50_ms']:.0f} ms", "median POST /api/analyze over HTTP (127.0.0.1)", K.ORANGE),
                                     (f"{lat('POST /api/auth/login')['p50_ms']:.0f} ms", "median login (bcrypt hashing)", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, col, vsize=26, lsize=12)
    rows = [["Observation", "Treatment"],
            ["A photo without a face returns 200 with face_detected false (API_CONTRACT.md says 422); an undecodable upload returns HTTP 500", "Recorded as defects and covered by characterisation tests; not changed"],
            ["The result thumbnail is a broken image: the relative URL is resolved against the front-end origin", "Recorded; visible in the screenshots"],
            ["/app/history/[id] exists but nothing links to it; a hard reload of /app in dev mode returns to the login page", "Recorded; screenshots use client-side navigation"],
            ["Registration accepts an e-mail address without an @ sign", "Recorded"]]
    K.table(s, 0.6, 2.9, [7.0, 5.13], rows, font_size=12, row_h=0.74)
    notes[17] = "Tests run against a temporary SQLite database; the probes and latency come from the live API over real HTTP. Latency was taken while other jobs used the CPU, so the numbers are upper bounds."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "Corrective action"],
            ["The final classifier checkpoint was missing, so the API reported model_loaded false", "Stage 3 of the unchanged pipeline was run once (10 min 37 s) and its log line recorded"],
            ["The GAN trained for 10 epochs on 2,800 faces produces blurred faces that ignore their condition", "Measured and reported (fidelity 15 % vs 14 % chance); a longer, better-conditioned GAN is the first next step"],
            ["FER2013 has no compound labels, so compound recognition cannot be scored on real faces", "Scored on a fresh synthetic hold-out with a no-synthesis control, and the limit is stated"],
            ["Haar detection misses native 48 px faces and about half of upscaled ones", "Detection rate and the accuracy cost are measured; a better detector is listed"],
            ["Environment: port 8000 taken, bcrypt 5 breaks passlib, the old .venv was a Python 3.10 copy", "API run on 8116, bcrypt pinned to 4.0.1, a clean virtual environment used"]]
    K.table(s, 0.6, 1.5, [5.9, 6.23], rows, font_size=13.5, row_h=0.9)
    notes[18] = "Each challenge was met by a design choice or by measuring it and saying so in the report."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Better generator", "Train the cEmoGAN longer on more faces, with the base paper's multi-hot label and an identity encoder, and check it with the stage-1 classifier before using its images.", K.BLUE, "1"),
        ("Real compound labels", "Obtain RAF-DB compound or a similar set so compound outputs can be scored on real faces, with precision, recall and exact-match ratio.", K.GREEN, "2"),
        ("Close the serving gap", "Train on Haar-style crops, add a stronger face detector and alignment, and apply a decision threshold instead of a plain argmax.", K.ORANGE, "3"),
        ("Product fixes", "Return 422 or 415 for bad uploads, fix the thumbnail URL, link the detail page, validate e-mail addresses, keep the session on reload.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.09, 1.6, 2.85, 3.9, t, b_, col, gl, body_size=14)
    K.box(s, 0.6, 5.75, 12.13, 0.95, fill=K.FHEAD, line=None)
    K.text(s, 0.85, 5.9, 11.6, 0.7, "Priority: items 1 and 2 decide whether compound emotions can be recognised at all; items 3 and 4 make the application usable on real photos.", size=15, color=K.INK, anchor="m")
    notes[19] = "Plan to the final review. The first two items address the biggest gaps found by the measurements."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = ("Likely questions: why compound outputs are near zero; why the multi-label model beats the baseline (more epochs, not the GAN); how our numbers compare with the base paper "
                 "(different data, scored on generated images, not comparable); why the GAN faces look blurred.")

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
