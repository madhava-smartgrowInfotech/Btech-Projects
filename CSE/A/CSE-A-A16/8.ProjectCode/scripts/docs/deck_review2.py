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
    T, DS, LAT = F.T, F.DS, F.LAT

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: a segmentation-plus-CNN recogniser behind a FastAPI service and a React interface",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = "This review shows how the system is designed and built: the data and model, what is implemented, the first measured results and the open items."

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and dataset"), ("03", "Preprocessing and model"), ("04", "Training and decision logic"),
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
        ("Problem", "Deaf and hearing people cannot converse without an interpreter, and interpreters are scarce. Recognisers that exist often need special sensors or stop at a static-image accuracy figure.", K.ORANGE, "!"),
        ("Proposed system", "A webcam frame is cropped to a hand region, segmented, resized to 64 x 64 and classified by a CNN into 29 classes; a decision layer turns letters into a sentence that is shown and spoken.", K.BLUE, "i"),
        ("Base paper link", "Shares the aim of accessible, real-time recognition. Does not use skeletons or knowledge distillation; it is an image CNN for letters, and its results are not comparable.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, 4.7, t, b_, col, gl, body_size=18)
    notes[3] = "One-minute recap of Review 1: the communication gap, our CNN-based approach, and how the base paper relates (motivation only)."

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.6, 1.3, 7.6, 5.5)
    K.text(s, 8.5, 1.5, 4.2, 5.2, [
        ("**Three tiers**", {"space_after": 8}),
        ("Presentation: React 18 app (port 5316) owns the webcam through getUserMedia.", {"bullet": True}),
        ("Application: FastAPI (port 8316), 16 endpoints under /api, in-memory sessions.", {"bullet": True}),
        ("Domain: the original desktop modules (preprocessing, model, recognizer, tts) reused unchanged.", {"bullet": True}),
        ("Storage: image folders and model files on disk.", {"bullet": True}),
    ], size=16, color=K.INK)
    notes[4] = "The FastAPI layer wraps the original sign_language_app modules, so the web and desktop apps run the same pipeline and the same model."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: end-to-end workflow")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.2, [("Kaggle ASL Alphabet", K.NAVY), ("250 images per class", K.NAVY), ("ROI + segmentation", K.PURPLE), ("70 / 15 / 15 split", K.GREEN),
                                      ("Train CNN (Adam)", K.ORANGE), ("Test once", K.BLUE), ("metrics.json + figures", K.NAVY)], size=13, gap=0.22)
    for i, (t, b_) in enumerate([("One pipeline", "Collection, training and live recognition call the same preprocessing function, so there is no train/serve mismatch."),
                                 ("Stratified split", "Same 250 images per class in every class; split 5,075 / 1,087 / 1,088 with seed 42; the test part is used once."),
                                 ("Reproducible", "scripts/measure_metrics.py writes every number to docs/metrics/metrics.json; figures are regenerated from it.")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 3.1, 3.85, 2.9)
        K.text(s, x + 0.25, 3.25, 3.4, 0.5, t, size=18, color=K.INK, bold=True)
        K.text(s, x + 0.25, 3.85, 3.4, 2.0, b_, size=18, color=K.TXT)
    notes[5] = "The training script and the measurement script are one command each. Preprocessing is the same function the live recogniser uses."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Dataset")
    wipe(s)
    for i, (v, l, c) in enumerate([("87,000", "images in the Kaggle archive (29 x 3,000)", K.BLUE), ("29", "classes: A-Z, space, del, nothing", K.GREEN),
                                   ("7,250", "images used: 250 per class", K.ORANGE), ("5,075 / 1,087 / 1,088", "train / validation / test", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.1, 1.45, 2.9, 1.25, v, l, c, vsize=19 if i == 3 else 28, lsize=12)
    K.picture(s, F.fig("f09_dataset_samples.png"), 0.6, 2.9, 5.4, 3.9)
    K.picture(s, F.fig("f08_dataset_split.png"), 6.2, 2.9, 6.5, 2.4)
    K.text(s, 6.3, 5.4, 6.4, 1.5, [
        ("Frames from video: neighbouring images are near-duplicates, and no signer id is given.", {"bullet": True, "size": 14}),
        ("So the test split is not an unseen-signer test. Licence is not bundled; Kaggle page to be re-checked.", {"bullet": True, "size": 14}),
    ], size=14, color=K.INK)
    notes[6] = "Kaggle ASL Alphabet: 87,000 training images of 200 x 200 pixels. We used an evenly spaced subset of 250 per class to keep CPU training practical. Important caveat: frames come from video, so the split is not signer-independent."

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Data preprocessing")
    wipe(s)
    K.picture(s, F.fig("f10_preprocessing_stages.png"), 0.6, 1.35, 6.5, 5.45)
    K.text(s, 7.4, 1.5, 5.3, 5.2, [
        ("1  Crop the 300 x 300 region of interest", {}), ("2  Convert to grayscale", {}), ("3  Gaussian blur, 7 x 7", {}), ("4  Otsu threshold (invert if mean > 127)", {}),
        ("5  Morphology: open once, close twice (3 x 3)", {}), ("6  Resize to 64 x 64, divide by 255", {}),
        ("Same six steps for collection, training and recognition. Training adds rotation, shift, zoom and shear.", {"italic": True, "size": 14, "color": K.TXT}),
    ], size=17, color=K.INK, space_after=10)
    notes[7] = "The six steps. Weakness: Otsu thresholding does not isolate the hand on a cluttered background, so some masks contain background structure; this is a stated limitation."

    # ---- 8 model architecture
    s = S[7]
    set_title(s, "Model architecture")
    wipe(s)
    rows = [["Block", "Layers", "Output"], ["1", "Conv 3x3, 32 · BN · MaxPool", "32 x 32 x 32"], ["2", "Conv 3x3, 64 · BN · MaxPool · Dropout 0.25", "16 x 16 x 64"],
            ["3", "Conv 3x3, 128 · BN · MaxPool · Dropout 0.25", "8 x 8 x 128"], ["Head", "Flatten · Dense 256 · BN · Dropout 0.4", "8,192 -> 256"], ["Output", "Dense 29, softmax", "29 class probabilities"]]
    K.table(s, 0.6, 1.5, [1.1, 5.2, 2.3], rows, font_size=14, row_h=0.62, align=["c", "l", "l"])
    K.tile(s, 9.6, 1.5, 3.13, 1.45, f"{F.MODEL['parameters']:,}", "parameters", K.BLUE, vsize=26)
    K.tile(s, 9.6, 3.15, 3.13, 1.45, f"{F.MODEL['file_size_mb']} MB", "saved model file", K.GREEN, vsize=26)
    K.tile(s, 9.6, 4.8, 3.13, 1.45, "No GPU", "trains and runs on a CPU", K.ORANGE, vsize=26)
    K.text(s, 0.6, 5.5, 8.7, 1.2, "Input is one 64 x 64 channel (the segmented mask). 'same' padding keeps the size before each 2 x 2 pooling. ReLU after each convolution and the first dense layer.", size=14, color=K.TXT)
    notes[8] = "A compact CNN written for the project: three convolution blocks and one dense layer, 2,199,453 parameters, 26.48 MB on disk."

    # ---- 9 training configuration
    s = S[8]
    set_title(s, "Training configuration")
    wipe(s)
    rows = [["Setting", "Value"],
            ["Optimiser / loss", "Adam, learning rate 1e-3 / categorical cross-entropy"],
            ["Batch / epochs", "32 / UI default 25; the saved run used 30"],
            ["Split", "70 / 15 / 15 stratified, seed 42"],
            ["Augmentation", "rotation 12 deg, shift 10 %, zoom 12 %, shear 8 % (training only)"],
            ["Callbacks", "EarlyStopping on val. accuracy (patience 6, restore best), ModelCheckpoint"],
            ["Hardware", f"Intel Core i5-12500, CPU only, about {F.TRAIN_SPEED['seconds_per_epoch']} s per epoch (2-epoch benchmark)"]]
    K.table(s, 0.6, 1.4, [3.0, 9.13], rows, font_size=14, row_h=0.5, first_bold=True)
    K.picture(s, F.fig("f01_training_curves.png"), 0.6, 5.0, 5.4, 1.95)
    K.text(s, 6.3, 5.15, 6.4, 1.7, f"Saved run: 30 epochs, best validation accuracy {F.pct(F.RUN['best_val_accuracy'])} at epoch {F.RUN['best_epoch']} (the cap; accuracy was still rising). "
           f"Validation exceeds training accuracy ({F.pct(F.RUN['final_train_accuracy'])}) because dropout and augmentation act only during training.", size=14, color=K.TXT)
    notes[9] = "Training configuration from sign_language_app/config.py and train.py. The saved run reached the 30-epoch cap, so it may be slightly under-trained; this is stated, not hidden."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic")
    wipe(s)
    K.picture(s, F.diag("10_core_algorithm_flowchart.png"), 0.6, 1.3, 5.2, 5.6)
    K.text(s, 6.2, 1.5, 6.5, 5.3, [
        ("**Confidence gate.** If the top softmax probability is below 0.75 the frame counts as 'nothing'.", {"bullet": True, "space_after": 10}),
        ("**Majority vote.** The last 15 frame labels are voted, which removes single-frame flicker.", {"bullet": True, "space_after": 10}),
        ("**Stability counter.** A letter is committed after 18 consecutive stable frames, if it is not 'nothing' and differs from the last committed letter.", {"bullet": True, "space_after": 10}),
        ("**Control signs.** 'space' and 'del' commit as edit actions; 'nothing' resets the repeat guard.", {"bullet": True}),
    ], size=16, color=K.INK)
    notes[10] = "The decision rules are in SignRecognizer.predict_frame. They trade speed for accuracy: a letter needs about 18 stable frames, roughly a second at 17-19 frames per second."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, F.diag("04_dfd_level1.png"), 0.6, 1.3, 7.3, 5.5)
    rows = [["Module", "Role"], ["preprocessing.py", "ROI, blur, Otsu, 64x64"], ["model.py", "build the CNN"], ["dataset.py", "load, split, augment"], ["train.py", "training loop, report"],
            ["recognizer.py", "vote, stability, commit"], ["tts.py", "offline speech"], ["backend/main.py", "FastAPI routes"], ["frontend/src", "React screens"]]
    K.table(s, 8.2, 1.5, [2.2, 2.33], rows, font_size=12, row_h=0.5)
    notes[11] = "Level-1 data flow. The original desktop modules are untouched; the backend and frontend are new."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database design and UML")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.6, 1.35, 6.0, 5.1)
    K.picture(s, F.diag("06_class_diagram.png"), 6.8, 1.35, 5.9, 5.1)
    K.text(s, 0.6, 6.55, 12.13, 0.4, "There is no SQL database: training images are files under data/<CLASS>/, model files live in models/, recognition sessions are in memory (at most 20). The ER diagram shows these stores.", size=12, color=K.TXT, align="c", italic=True)
    notes[12] = "Honest point: the project stores files, not rows. The ER diagram therefore models the file-system entities; the class diagram shows the real Python classes."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    E = F.ENV
    rows = [["Layer", "Technology"], ["Deep learning", f"TensorFlow / Keras {E['tensorflow']}, NumPy {E['numpy']}, scikit-learn, matplotlib"],
            ["Image processing", f"OpenCV {E['opencv']}, Pillow"], ["Speech", "pyttsx3 (offline); browser voice fallback"],
            ["Desktop app", "customtkinter (original, unchanged)"], ["API", "FastAPI, Uvicorn, python-multipart (port 8316)"],
            ["Front end", "React 18, Vite 8, Tailwind 4, TanStack Query, Recharts (port 5316)"], ["Testing", "pytest, FastAPI TestClient, Playwright, smoke script"]]
    K.table(s, 0.6, 1.5, [3.0, 9.13], rows, font_size=16, row_h=0.62, first_bold=True)
    notes[13] = f"Python {E['python']} on Windows. Everything is open source and starts with run.bat."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Preprocessing, CNN, recogniser, speech", "Done", "sign_language_app/, 25 unit tests"],
            ["Training and evaluation", "Done", "models/, scripts/measure_metrics.py"],
            ["FastAPI service (16 endpoints)", "Done", "27 API tests, 26/26 smoke checks"],
            ["React interface (7 screens)", "Done", "16 screenshots, browser walk 360-1440 px"],
            ["Recognition of words / dynamic signs", "Not done", "letters only; stated as a limitation"],
            ["Evaluation on unseen signers", "Not done", "dataset has no signer ids"],
            ["Model optimisation (quantisation, TFLite)", "Not done", "CNN call is 50 ms via model.predict"]]
    K.table(s, 0.6, 1.5, [4.8, 1.6, 5.73], rows, font_size=14, row_h=0.62)
    notes[14] = "State of the code base. Three honest gaps: words, unseen signers, and model optimisation."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results: held-out test split")
    wipe(s)
    for i, (v, l, c) in enumerate([(F.pct(T["accuracy"], 2), "test accuracy (n = 1,088)", K.BLUE), (F.f3(T["macro_f1"]), "macro F1", K.GREEN),
                                   (F.pct(T["top3_accuracy"]), "top-3 accuracy", K.ORANGE), (f"{F.OFFICIAL['correct']} / {F.OFFICIAL['n']}", "official Kaggle test photos", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.1, 1.45, 2.9, 1.25, v, l, c, vsize=28)
    K.picture(s, F.fig("f02_per_class.png"), 0.6, 2.95, 7.6, 3.9)
    K.card(s, 8.5, 2.95, 4.23, 3.8, "Reading", "Test split = the 15 % never used for training or model selection. Weakest: Y, V, X, U, W, E (F1 0.62-0.70). Best: nothing, C, Q. 87.2 % on other archive photos is optimistic (near-duplicate frames) and is not used as the headline.", K.BLUE, "i", body_size=14)
    notes[15] = ("Headline: 82.81 % on the 1,088-image test split (loss 0.5569, macro F1 0.830). The 87.24 % on 2,900 other archive photos is inflated by near-duplicate frames, so it is context only.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    K.picture(s, F.shot("04_recognize.png"), 0.6, 1.3, 7.4, 4.65, border=True)
    K.picture(s, F.shot("05_collect.png"), 8.3, 1.3, 4.43, 2.77, border=True)
    K.picture(s, F.shot("03_dashboard.png"), 8.3, 4.2, 4.43, 2.77, border=True)
    K.text(s, 0.6, 6.05, 7.4, 0.9, "Live recognition: letter H at 87 %, segmentation mask preview and the sentence built so far. Collection and dashboard screens on the right. Real application, trained model, 7,250 real images; the camera was a Chromium fake camera fed with real photos.", size=12, color=K.TXT)
    notes[16] = "Real screenshots from the running application. The recognition clip was assembled from real held-out photos and fed to a fake camera because the build machine had no physical webcam."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(str(F.PYTEST_TOTAL), "pytest tests passed", K.GREEN), (f"{F.SMOKE_TOTAL} / {F.SMOKE_TOTAL}", "smoke-test checks", K.BLUE),
                                   ("0", "console errors in the browser walk", K.ORANGE), ("360-1440 px", "light and dark themes", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.1, 1.45, 2.9, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Observation", "Action"],
            ["Archive photos beyond the training subset are near-duplicates of trained frames", "Headline uses the held-out split; the 87.2 % figure is flagged as optimistic"],
            ["Rotating a hand by +/- 10 degrees drops accuracy from 85.0 % to about 68 %", "Documented; rotation augmentation planned"],
            ["No physical webcam on the build machine", "Browser flow tested with a fake camera; live webcam test left to the user"]]
    K.table(s, 0.6, 3.1, [6.0, 6.13], rows, font_size=15, row_h=1.0)
    notes[17] = "27 API, 10 preprocessing, 7 recogniser and 8 dataset/model tests. The observations on the right shaped how results are reported."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "Corrective action"],
            ["87,000 images are too slow to train on a CPU", "Evenly spaced 250 per class (7,250 images); 75 s to load and preprocess"],
            ["Otsu masks keep background structure on cluttered scenes", "Stated as a limitation; skin-colour mode exists in config for future work"],
            ["Validation loss spiked in the first epochs (BatchNorm warm-up)", "Settled by epoch 6; best-weights checkpoint kept"],
            ["TensorFlow failed to load after scikit-learn on Windows", "Import TensorFlow first in the scripts"],
            ["CNN forward pass dominates latency (50 ms)", "Measured; optimisation listed as future work"]]
    K.table(s, 0.6, 1.5, [5.6, 6.53], rows, font_size=15, row_h=0.85)
    notes[18] = "Each challenge was met by a concrete change in the data, the scripts or the way results are reported."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Evaluate", "Test on signers and backgrounds the model has never seen, and with a physical webcam.", K.BLUE, "1"),
        ("Improve robustness", "Add rotation and brightness augmentation; compare with skin-colour segmentation.", K.GREEN, "2"),
        ("Speed up", "Export the model for faster inference than model.predict (quantisation, TFLite).", K.ORANGE, "3"),
        ("Extend (future)", "Common words and motion signs, two-hand signs, sentence-level translation.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.1, 1.6, 2.9, 4.4, t, b_, col, gl, body_size=18)
    notes[19] = "Plan to the final review and beyond. Unseen-signer evaluation needs new data with signer ids; it is not possible with the Kaggle archive alone."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Likely questions: why a 64 x 64 mask instead of the colour image; how the system handles unseen signers (not tested); why letters only."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
