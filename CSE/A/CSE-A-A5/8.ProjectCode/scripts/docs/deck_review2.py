"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx.

Self-contained: the small slide helpers (prepare, set_title, wipe, agenda, title_slide, thank_you) are defined here so the deck does not depend on
the Review 1 module. All numbers come from facts.py (experiments/**/metrics.json); nothing is typed in by hand.
    python -m scripts.docs.deck_review2        # from 8.ProjectCode
"""
import os

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"


# ------------------------------------------------------------------ helpers
def is_ph(sh, *types):
    return sh.is_placeholder and sh.placeholder_format.type in types


def prepare(prs, review_label):
    for lay in prs.slide_layouts:
        for sh in lay.shapes:
            if sh.has_text_frame and LAYOUT_FOOTER_OLD in sh.text_frame.text:
                K.replace_text(sh, f"{F.PRODUCT}  ·  {review_label}")
    cp = prs.core_properties
    cp.title = f"{F.FULL_TITLE}: {review_label}"
    cp.subject = f"Batch {F.BATCH_NO} ({F.SECTION})"
    cp.author = ", ".join(n for n, _ in F.STUDENTS)
    cp.keywords = "cloud security, AES-256-GCM, ECDH, intrusion detection, XGBoost, UNSW-NB15"
    cp.comments = ""
    cp.last_modified_by = ""


def set_title(slide, text, size=None):
    for sh in slide.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, text, size)
            return sh


def wipe(slide):
    K.clear(slide, lambda sh: sh.is_placeholder)


def agenda(slide, items, colors, cols=3):
    n = len(items)
    rows = (n + cols - 1) // cols
    gx, gy = 0.29, 0.3
    w = (12.13 - gx * (cols - 1)) / cols
    h = min(1.45, (5.3 - gy * (rows - 1)) / rows)
    x0, y0 = 0.6, 1.55
    for i, (n_, label) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = x0 + c * (w + gx), y0 + r * (h + gy)
        K.box(slide, x, y, w, h)
        K.text(slide, x + 0.25, y + 0.14, 1.0, 0.5, n_, size=26, color=colors[i % len(colors)], bold=True, font="Cambria")
        K.text(slide, x + 0.25, y + 0.72, w - 0.5, 0.65, label, size=16, color=K.INK, bold=True)


def title_slide(s, subtitle, label):
    for sh in s.shapes:
        nm = sh.name
        if is_ph(sh, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, F.TITLE, 32)
        elif is_ph(sh, PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.BODY):
            K.replace_text(sh, subtitle, 20)
        elif nm == "review label":
            K.replace_text(sh, label)
        elif nm == "team":
            K.replace_text(sh, "\n".join(f"{n_}  {r_}" for n_, r_ in F.STUDENTS))
        elif nm == "Text 6":
            K.replace_text(sh, f"{F.GUIDE}, {F.GUIDE_DESIGNATION}")
        elif nm == "Text 7":
            K.replace_text(sh, f"{F.DEPT}\n{F.COLLEGE_SHORT}  ·  Batch {F.BATCH_NO} ({F.SECTION})  ·  {F.YEAR}")


def thank_you(s):
    for sh in s.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
            K.replace_text(sh, "Thank you")
        elif is_ph(sh, PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.SUBTITLE):
            K.replace_text(sh, "Questions and suggestions are welcome.")


def trim(path, tag):
    """Copy of a diagram or chart with its white margins removed (written to the temp folder, source untouched)."""
    import tempfile

    from PIL import Image, ImageChops

    with Image.open(path) as im:
        im = im.convert("RGB")
        bbox = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
        if bbox:
            pad = 12
            bbox = (max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, im.size[0]), min(bbox[3] + pad, im.size[1]))
            im = im.crop(bbox)
        out = os.path.join(tempfile.gettempdir(), f"a5_r2_{tag}.png")
        im.save(out)
    return out


def shot_box(slide, name, x, y, w, h, caption):
    """Real screenshot in a w x h area with a one-line caption under it."""
    K.picture(slide, F.shot(name), x, y, w, h - 0.34, border=True)
    K.text(slide, x, y + h - 0.3, w, 0.3, caption, size=11, color=K.TXT, align="c", italic=True)


# ------------------------------------------------------------------ the deck
def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}
    OS, PS, S42, SH = F.OFFS, F.PAPS, F.S42, F.SHIPPED
    ts = F.OFF["train_seconds"]
    real = F.SHIFT["shipped_on_real_official_test"]["stack"]
    rev = F.SHIFT["real_trained_on_synthetic_demo_csv"]["stack"]
    cases = F.CRY["tamper_tests"]
    t_trials = next(iter(cases.values()))["trials"]
    t90, t50 = F.thr_row(0.9), F.thr_row(0.5)
    CNN, XGB = OS["cnn"]["accuracy"]["mean"], OS["xgb"]["accuracy"]["mean"]

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: an ECDH + AES-256-GCM secure channel and a stacked XGBoost + 1D-CNN intrusion detector",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = ("This review shows how CipherGuard Shield is designed and built, what is implemented, the first measured results on the real UNSW-NB15 dataset, "
                "and the open items. Introduce the four team members and the guide.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and datasets"), ("03", "Preprocessing and models"), ("04", "Training and decision logic"),
               ("05", "Data flow, entities and UML"), ("06", "Technology stack"), ("07", "Progress and preliminary results"),
               ("08", "Output screens and testing"), ("09", "Challenges and next steps")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Data in a public cloud is readable by the provider unless it is encrypted first, symmetric keys need a safe exchange, and encryption cannot spot an attacker who already holds valid credentials. Most academic systems treat cryptography and intrusion detection separately.", K.ORANGE, "!"),
        ("Proposed system", "CipherGuard Shield puts two protections around one data path: SecureChannel (ECDH P-256 + HKDF + AES-256-GCM) and the ThreatSense Engine (XGBoost + 1D CNN + logistic-regression stacking), with an alert log and a live console.", K.BLUE, "i"),
        ("Base paper link [1]", "Kalyanasundaram et al. combine a quantum-inspired network with LeNet and a custom elliptic-curve scheme (EECC). We keep their idea of joint detection and encryption but use standard, audited primitives and a classical ensemble. Results are not directly comparable.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.6, W, 4.5, t, b_, col, gl, body_size=19)
    notes[3] = ("Recap of Review 1: the batch survey gap was that cryptography and intrusion detection are treated separately and the combined overhead is never measured. "
                "We kept the joint idea, replaced the paper's quantum-inspired network and EECC by standard components, and measured the overhead.")

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, trim(F.diag("01_system_architecture.png"), "01"), 0.6, 1.3, 7.0, 5.7)
    K.text(s, 7.9, 1.45, 4.85, 5.4, [
        ("**Four tiers, no database**", {"space_after": 8}),
        (f"Presentation: React 19 console (port {F.WEB_PORT}, 5 routes) plus the original HTML dashboard served by the API.", {"bullet": True}),
        (f"Application: FastAPI (port {F.API_PORT}), 9 routes under /api, limits of 1 MB text, 5 MB file, 10 MB or 10,000-row CSV.", {"bullet": True}),
        ("Core: cipherguard/crypto (SecureChannel, KeyPair) and cipherguard/ids (preprocessing, XGBoost, CNN, stacking).", {"bullet": True}),
        ("State: alerts (max 500), session-key cache and a mock cloud key pair live in process memory.", {"bullet": True}),
        ("Files: models/, reports/metrics.json, data/raw/synthetic_demo.csv.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[4] = "All routes live in cipherguard/api/main.py. The cloud is a mock endpoint in the same process with its own long-term P-256 key pair; a real deployment would run it elsewhere."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: two lanes around one transfer")
    wipe(s)
    K.picture(s, trim(F.diag("02_high_level_workflow.png"), "02"), 0.6, 1.4, 7.4, 5.0)
    for i, (t, b_) in enumerate([("Lane A: SecureChannel", "A fresh ephemeral P-256 key per message, ECDH with the cloud's public key, HKDF-SHA256 to a 32-byte key, AES-256-GCM with a random 12-byte nonce. The envelope carries ciphertext, nonce, tag and ephemeral public key."),
                                 ("Lane B: ThreatSense", "A 42-feature flow record is scaled and encoded, scored by XGBoost and a 1D CNN, fused by logistic regression, and flagged at 0.5 with a severity band."),
                                 ("Not gated", "The API does not block a transfer on the verdict; the operator decides. Overhead is measured for both lanes together.")]):
        y = 1.4 + i * 1.78
        K.box(s, 8.3, y, 4.43, 1.65)
        K.text(s, 8.45, y + 0.07, 4.15, 0.4, t, size=15, color=K.INK, bold=True)
        K.text(s, 8.45, y + 0.42, 4.15, 1.2, b_, size=12.5, color=K.TXT)
    K.text(s, 0.6, 6.5, 7.4, 0.45, "Workflow of one protected transfer, as implemented in the API.", size=12, color=K.TXT, align="c", italic=True)
    notes[5] = "The two lanes are independent code paths that the console runs side by side. Making the detector gate a transfer is future work."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Datasets: shipped synthetic set and real UNSW-NB15")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.SYNTH_ROWS:,}", "synthetic rows in the shipped bundle", K.ORANGE), (f"{F.OFF['train_rows']:,}", "official UNSW-NB15 training flows", K.BLUE),
                                   (f"{F.OFF['test_rows']:,}", "official UNSW-NB15 testing flows", K.GREEN), ("42", "flow features (3 categorical, 39 numeric)", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["", "Shipped bundle (synthetic)", "Real UNSW-NB15 (experiments)"],
            ["Source", "cipherguard/ids/synthetic.py, seed 42, UNSW-NB15 schema", "UNSW Canberra Cyber Range Lab, Moustafa and Slay [7]"],
            ["Split", f"stratified 70/15/15 = {F.SYNTH_SPLIT[0]:,} / {F.SYNTH_SPLIT[1]:,} / {F.SYNTH_SPLIT[2]:,}", f"official train ({F.OFF['fit_rows']:,} fit + {F.OFF['val_rows']:,} validation) -> official test {F.OFF['test_rows']:,}"],
            ["Classes", "normal / attack; 2.5% label noise injected (300 rows)", f"normal / attack ({F.pct(F.OFF['test_attack_rate'])} attack in test); 9 attack categories"],
            ["Ceiling", "accuracy cannot exceed about 0.975 by construction", "train and test are temporally separated: harder than a random split"],
            ["Used for", "the app out of the box and its Model performance page", "all accuracy claims in the reports; base-paper-style runs (9,000 balanced flows)"]]
    K.table(s, 0.6, 2.95, [1.5, 5.3, 5.33], rows, font_size=13, row_h=0.62, first_bold=True)
    K.text(s, 0.6, 6.75, 12.13, 0.35, "The default model never saw real traffic; see the synthetic-versus-real result on slide 15.", size=12, color=K.TXT, italic=True)
    notes[6] = ("Be frank: the shipped 97.33 percent is accuracy on synthetic rows. We fetched the official UNSW-NB15 training and testing sets (175,341 and 82,332 flows) from a public repackaging "
                "and ran the same pipeline on them. The UNSW-NB15 data is free for academic use with citation.")

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Data preprocessing")
    wipe(s)
    K.flow(s, 0.6, 1.45, 12.13, 1.0, [("Flow record (42 fields)", K.NAVY), ("Fill defaults, match names", K.PURPLE), ("Cast proto, service, state to text", K.PURPLE),
                                       ("MinMax scale 39 numerics", K.GREEN), ("One-hot 3 categoricals", K.GREEN), ("Vector for the models", K.ORANGE)], size=12, gap=0.22)
    for i, (v, l, c) in enumerate([(str(F.INPUT_DIM_SYNTH), "encoded dimensions, synthetic bundle (39 numeric + 31 one-hot)", K.BLUE), (str(F.INPUT_DIM_REAL), "encoded dimensions on real UNSW-NB15 (more proto/service/state values)", K.GREEN)]):
        K.tile(s, 0.6 + i * 4.2, 2.8, 4.0, 1.25, v, l, c, vsize=28, lsize=12)
    K.text(s, 9.1, 2.8, 3.63, 1.3, "Unknown categories are ignored by the encoder, so a new protocol name cannot crash scoring.", size=14, color=K.TXT)
    K.text(s, 0.6, 4.35, 12.13, 2.6, [
        ("Missing features in a request default to typical values (for example sttl 62, rate 10,000); a CSV with absent columns is filled the same way.", {"bullet": True}),
        ("Class imbalance (real training set: 56,000 normal / 119,341 attack): XGBoost uses scale_pos_weight = normal / attack; the PyTorch CNN uses plain binary cross-entropy.", {"bullet": True}),
        ("One preprocessor object is fitted on the fit split only and saved with the models, so training and serving transform data identically.", {"bullet": True}),
        ("Known limit: only 42 of the 49 original UNSW-NB15 features are used, and identifiers such as addresses and ports are not part of the schema.", {"bullet": True}),
    ], size=16, color=K.INK, space_after=9)
    notes[7] = "Preprocessing is a scikit-learn ColumnTransformer: MinMaxScaler for numerics and OneHotEncoder with handle_unknown=ignore for the three categorical fields."

    # ---- 8 model
    s = S[7]
    set_title(s, "Model architecture: XGBoost + 1D CNN + stacking")
    wipe(s)
    K.picture(s, trim(F.diag("12_model_architecture.png"), "12"), 0.6, 1.35, 7.6, 5.0)
    K.text(s, 8.5, 1.45, 4.25, 5.4, [
        ("**XGBoost**: 200 trees, depth 6, learning rate 0.08, subsample and column sample 0.85.", {"bullet": True, "space_after": 8}),
        (f"**1D CNN** (PyTorch): two Conv1d + MaxPool blocks, Dense 64, dropout 0.3, sigmoid; {F.CNN_PARAMS_70:,} parameters at 70 inputs.", {"bullet": True, "space_after": 8}),
        ("**Stacking**: logistic regression on [p_xgb, p_cnn], fitted on the validation split; decision threshold 0.5.", {"bullet": True, "space_after": 8}),
        ("The base paper's score-level fusion (DSMMN-SLF) and quantum-inspired network are not reproduced.", {"bullet": True, "italic": True, "color": K.TXT}),
    ], size=14, color=K.INK)
    K.text(s, 0.6, 6.45, 7.6, 0.45, "Layer stack taken from cipherguard/ids/train.py.", size=12, color=K.TXT, align="c", italic=True)
    notes[8] = "Three components with separate jobs. The CNN reshapes the encoded vector to a one-channel sequence; it is a small network, trained on a CPU."

    # ---- 9 training configuration
    s = S[8]
    set_title(s, "Training configuration")
    wipe(s)
    ts = F.OFF["train_seconds"]
    rows = [["Setting", "Value"],
            ["Shipped bundle", f"{F.SYNTH_ROWS:,} synthetic rows, stratified 70/15/15, seed 42; test accuracy {F.f4(SH['accuracy'])} on {F.SYNTH_SPLIT[2]:,} rows"],
            ["XGBoost", "n_estimators 200, max_depth 6, learning rate 0.08, subsample 0.85, colsample 0.85, scale_pos_weight = neg / pos"],
            ["CNN", "Adam, learning rate 0.001, batch 256, up to 15 epochs, early stopping (patience 5), BCE loss, CPU only"],
            ["Stacking", "LogisticRegression fitted on validation-split probabilities; threshold 0.5"],
            ["Real-data runs", f"official train split 85/15 into {F.OFF['fit_rows']:,} fit / {F.OFF['val_rows']:,} validation; 5 seeds (42-46); 10 repetitions for the 9,000-flow protocol"],
            ["Cost on this PC", f"Core i5-12500, 15.7 GB RAM, no GPU: XGBoost {ts['xgb']:.1f} s, CNN {ts['cnn']:.0f} s (149,039 rows, machine shared with other jobs)"]]
    K.table(s, 0.6, 1.45, [2.3, 9.83], rows, font_size=14, row_h=0.72, first_bold=True)
    K.text(s, 0.6, 6.6, 12.13, 0.4, "Same hyper-parameters as the shipped code in every experiment; nothing was tuned on the test set.", size=12, color=K.TXT, italic=True)
    notes[9] = "Hyper-parameters are those in cipherguard/ids/train.py; the experiment script reuses the shipped training functions. Seeds change the fit/validation split and the CNN initialisation."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: verdict, severity and threshold")
    wipe(s)
    K.picture(s, trim(F.diag("10_flowchart_scoring.png"), "10"), 0.6, 1.3, 5.9, 5.65)
    K.text(s, 6.8, 1.45, 5.95, 2.1, [
        ("**Verdict.** Attack when the stacked probability is at least 0.5.", {"bullet": True, "space_after": 6}),
        ("**Severity.** Critical from 0.85, high from 0.70, otherwise medium; normal is low and raises no alert.", {"bullet": True, "space_after": 6}),
        ("**Alert log.** Attacks are appended, newest first, capped at 500 entries in memory.", {"bullet": True}),
    ], size=14, color=K.INK)
    rows = [["Threshold", "Accuracy", "Precision", "Recall", "False alarms"]] + [
        [f"{t:.1f}" + ("  (shipped)" if t == 0.5 else ""), F.f3(F.thr_row(t)["accuracy"]), F.f3(F.thr_row(t)["precision"]), F.f3(F.thr_row(t)["recall"]), F.pct(F.thr_row(t)["fpr"])] for t in (0.5, 0.7, 0.9)]
    K.table(s, 6.8, 3.75, [1.75, 1.0, 1.1, 0.95, 1.15], rows, font_size=13, row_h=0.46, align=["l", "c", "c", "c", "c"])
    K.text(s, 6.8, 5.75, 5.95, 1.2, f"Official test set, seed 42. Raising the threshold to 0.9 cuts false alarms from {F.pct(t50['fpr'])} to {F.pct(t90['fpr'])} and lifts accuracy to {F.f3(t90['accuracy'])}, at the cost of missed attacks. 0.5 is kept as the default; the sweep was run on the test set, so it shows the trade-off rather than a tuned result.", size=12.5, color=K.TXT)
    notes[10] = "The flowchart mirrors ThreatSenseEngine.score_single and the /api/ids/score route. A deployment would choose the threshold on a validation set according to how many false alarms an operator can tolerate."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, trim(F.diag("04_dfd_level1.png"), "04"), 0.6, 1.3, 7.0, 5.65)
    rows = [["Module", "Role"], ["crypto/secure_channel.py", "ECDH, HKDF, AES-GCM envelope"], ["ids/preprocessing.py", "MinMax + one-hot transformer"], ["ids/train.py", "XGBoost, CNN, stacking"],
            ["ids/inference.py", "load models, score records"], ["ids/synthetic.py", "synthetic flow generator"], ["api/main.py", "9 routes, alert log, limits"], ["frontend/ and web/", "React console, legacy page"],
            ["scripts/", "experiments, benchmarks, capture"]]
    K.table(s, 7.9, 1.45, [2.35, 2.48], rows, font_size=12, row_h=0.55, first_bold=True)
    K.text(s, 7.9, 6.5, 4.83, 0.5, "Level-1 data-flow diagram: seven processes, five stores.", size=11.5, color=K.TXT, italic=True)
    notes[11] = "Level 1 splits the system into validation, scoring, alert reporting, encryption, decryption, metrics serving and offline training."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Entities and UML (no database)")
    wipe(s)
    K.picture(s, trim(F.diag("09_er_diagram.png"), "09"), 0.6, 1.3, 6.0, 4.95)
    K.picture(s, trim(F.diag("06_uml_class.png"), "06"), 6.75, 1.3, 6.0, 5.2)
    K.text(s, 0.6, 6.35, 6.0, 0.7, "CipherGuard Shield keeps no database. Alerts and keys live in process memory; models and reports are files. The ER diagram shows logical entities and call-time relations.", size=11.5, color=K.TXT, italic=True)
    K.text(s, 6.75, 6.55, 6.0, 0.5, "Core classes: KeyPair, SecureChannel, ThreatSenseEngine, CNN1D_Torch, FastAPI app.", size=11.5, color=K.TXT, italic=True)
    notes[12] = "Honest point: persistence of alerts and of the cloud key is future work. SecureChannel is a class of static methods, drawn as such in the UML."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    rows = [["Layer", "Technology"],
            ["Language and API", "Python 3.11, FastAPI 0.110, Uvicorn 0.29, Pydantic 2.6, python-multipart"],
            ["Cryptography", "cryptography 42 (OpenSSL): ECDH on NIST P-256, HKDF-SHA256, AES-256-GCM with 12-byte nonce and 16-byte tag"],
            ["Machine learning", "XGBoost 2.0.3, scikit-learn 1.5.0 (ColumnTransformer, logistic regression), PyTorch (CPU) for the 1D CNN, pandas, NumPy, joblib"],
            ["Dataset", "UNSW-NB15 official training and testing sets (Hugging Face repackaging, parquet via pyarrow) and a built-in synthetic generator"],
            ["Front end", "React 19, Vite 8, Tailwind 4, Recharts, Framer Motion, GSAP, three.js; original HTML/JS dashboard in web/"],
            ["Testing and capture", "pytest, FastAPI TestClient, httpx smoke script, Playwright browser walk at 1440 x 900"],
            ["Run", "run.bat (virtual environment, training if needed, both servers) or Docker; ports 8305 and 5305"]]
    K.table(s, 0.6, 1.45, [2.6, 9.53], rows, font_size=14, row_h=0.65, first_bold=True)
    notes[13] = "Versions are those pinned in requirements.txt and package.json. On the measurement PC PyTorch 2.14 (CPU) was used; the pinned 2.2.0 is installed by run.bat."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["SecureChannel: ECDH + HKDF + AES-256-GCM, text and file", "Done", f"{len(cases)} tamper cases x {t_trials:,} trials all as expected; 10 unit tests"],
            ["ThreatSense: XGBoost + CNN + stacking, batch CSV, alerts", "Done", f"6 engine tests; 120-row batch scored in {F.IP['ids_batch_120_rows']['median_ms']:.1f} ms in process"],
            ["API (9 routes) and React console (5 routes)", "Done", f"{F.SMOKE_PASSED}/{F.SMOKE_TOTAL} smoke checks; {F.PYTEST_PASSED}/{F.PYTEST_TOTAL} pytest tests"],
            ["Real-data evaluation (official split, base-paper protocol)", "Done", "5 seeds + 10 repetitions; threshold, per-category, ROC"],
            ["RSA-OAEP + AES-GCM baseline benchmark", "Done", "RSA-2048 and RSA-3072 against SecureChannel, 1 KB to 5 MB"],
            ["Real-trained model bundle served by the API", "Done (optional)", "CIPHERGUARD_MODELS_DIR switch; default stays synthetic-trained"],
            ["Live packet capture, alert persistence, TLS and login", "Not done", "records and CSV only; alerts lost on restart; demo cloud in process"],
            ["Base paper's EECC and quantum-inspired network", "Not done", "standard primitives and a classical ensemble used instead"]]
    K.table(s, 0.6, 1.4, [5.2, 1.55, 5.38], rows, font_size=12.5, row_h=0.6)
    notes[14] = "State of the code base. The honest gaps are on the last two rows: detection is not coupled to transfers, nothing persists, and the base paper's own components are not reproduced."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results: real data versus synthetic")
    wipe(s)
    for i, (v, l, c) in enumerate([(F.mstd(OS, "stack", "accuracy"), "stacked, official test set (5 seeds)", K.ORANGE), (F.f3(XGB), "XGBoost alone, same test set", K.BLUE),
                                   (F.mstd(PS, "stack", "accuracy"), "stacked, 9,000-flow paper protocol (10 runs)", K.GREEN), (F.f3(real["accuracy"]), "shipped synthetic model on real test flows", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.35, 2.85, 1.2, v, l, c, vsize=24, lsize=11.5)
    K.picture(s, trim(F.fig("f07_synthetic_vs_real.png"), "f07"), 0.6, 2.7, 6.0, 3.3)
    K.picture(s, trim(F.fig("f09_crypto_latency.png"), "f09"), 6.75, 2.7, 6.0, 3.3)
    K.text(s, 0.6, 6.1, 12.13, 0.95, [
        (f"Shipped accuracy {F.pct(SH['accuracy'], 2)} is on synthetic rows; the same model scores {F.f3(real['accuracy'])} on {F.OFF['test_rows']:,} real flows. Real-trained: stacked {F.f3(OS['stack']['accuracy']['mean'])}, F1 {F.f3(OS['stack']['f1']['mean'])}, ROC-AUC {F.f3(OS['stack']['roc_auc']['mean'])}, "
         f"but XGBoost alone is better ({F.f3(XGB)}); CNN {F.f3(CNN)}. Encryption of 100 KB takes {F.crypto_row('sc', '100 KB', 'encrypt'):.2f} ms; one protected transfer {F.IP['protected_transfer_100kb']['median_ms']:.2f} ms, {F.IP['share_of_transfer_median']['ids'] * 100:.0f}% of it detection.", {}),
    ], size=12.5, color=K.TXT)
    notes[15] = (f"Headline findings. 1) The shipped 97.33 percent is a property of the synthetic generator (label noise caps it at 97.5). 2) On real UNSW-NB15 the stacked ensemble gets {F.f3(OS['stack']['accuracy']['mean'])}; "
                 f"XGBoost alone gets {F.f3(XGB)} so stacking does not help here. 3) Under the base paper's style of protocol the stacked model reaches {F.f3(PS['stack']['accuracy']['mean'])} against the paper's 0.949, on different subsets. "
                 "4) Cryptography is sub-millisecond for small payloads; detection dominates the per-transfer overhead.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    cw, ch = 3.95, 2.62
    grid = [("03_live-scoring.png", "Live scoring: attack verdict, severity, XGB and CNN scores"), ("06_secure-transfer-verified.png", "Secure transfer: decrypted and verified at the cloud"),
            ("07_secure-transfer-tampered.png", "Tampered ciphertext rejected (tag failure)"), ("10_real-flows-shipped-model.png", "120 real flows, shipped model: 78/120 agree with labels"),
            ("11_real-model-performance.png", "Real-trained bundle: 88.79% on 82,332 test flows"), ("12_real-flows-real-model.png", "Same 120 real flows, real-trained bundle: 101/120")]
    for i, (n_, cap) in enumerate(grid):
        r, c = divmod(i, 3)
        shot_box(s, n_, 0.6 + c * (cw + 0.19), 1.3 + r * (ch + 0.14), cw, ch, cap)
    K.text(s, 0.6, 6.72, 12.13, 0.3, "Real captures of the running application at 1440 x 900. The 120 real flows are a seeded sample of the official test set.", size=11, color=K.TXT, italic=True)
    notes[16] = ("Real screenshots. Screens 10 and 12 use the same 120 real UNSW-NB15 test flows: the shipped synthetic-trained model agrees with the labels on 78 of 120 (65.0 percent), "
                 "the real-trained bundle on 101 of 120 (84.2 percent).")

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.PYTEST_PASSED} / {F.PYTEST_TOTAL}", "pytest tests passed", K.GREEN), (f"{F.SMOKE_PASSED} / {F.SMOKE_TOTAL}", "smoke-test checks passed", K.BLUE),
                                   (f"{t_trials * len(cases):,}", f"tamper trials in {len(cases)} cases, every one as expected", K.ORANGE),
                                   (f"{F.CRY['uniqueness']['distinct_nonces']:,}", f"distinct nonces in {F.CRY['uniqueness']['encryptions']:,} encryptions", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Observation", "Action"],
            ["Shipped model scores 0.660 on real flows (AUC 0.657)", "Stated in every result; real-trained bundle built and servable"],
            ["torch fails to load (WinError 1114) if numpy/pandas are imported first on this host", "torch-first launcher, test conftest and experiment scripts"],
            ["README says the CNN uses balanced loss; the PyTorch path uses plain BCE", "Documented; CNN class weighting left as future work"],
            ["The console sample button says real flows; the 120-row sample is synthetic", "Documented; real sample added under data/samples"]]
    K.table(s, 0.6, 2.95, [6.4, 5.73], rows, font_size=14, row_h=0.78)
    notes[17] = "Tests cover crypto (10), the engine (6) and the API (10); the smoke script runs against the live server. The observations came from running the code, and each is recorded rather than hidden."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "Corrective action"],
            ["No real dataset shipped with the project; the demo ran on synthetic flows", "Fetched the official UNSW-NB15 split, re-ran the same pipeline, kept the shipped files unchanged"],
            ["Temporal shift: stacking (0.890) trails XGBoost (0.910) on the official test set", "Reported per seed, with baselines; threshold analysis; no claim of an ensemble gain"],
            [f"False alarms: {F.pct(S42['stack']['fpr'])} of normal test flows at threshold 0.5", f"Threshold sweep (0.9 gives {F.pct(t90['fpr'])}); operator-tunable threshold listed as next step"],
            ["The base paper's EECC and quantum-inspired network cannot be reproduced from the paper", "Standard primitives (ECDH, AES-GCM) and a classical ensemble; comparison marked indicative"],
            ["CPU-only training and a shared, memory-limited PC", f"Small CNN ({ts['cnn']:.0f} s); torch-first imports; timings reported as indicative"]]
    K.table(s, 0.6, 1.5, [5.7, 6.43], rows, font_size=14.5, row_h=0.88)
    notes[18] = "Each challenge was met by a concrete design choice or by measuring it and saying so in the report."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Adopt real data", "Make the real-trained bundle the default, add class weighting to the CNN, and choose the threshold on a validation set.", K.BLUE, "1"),
        ("Couple the lanes", "Score the traffic of a transfer session and quarantine or alert before decryption, instead of side-by-side lanes.", K.GREEN, "2"),
        ("Harden", "Persist alerts, keep the cloud key in a store, add TLS, login and rate limiting, and replace the demo cache by real key distribution.", K.ORANGE, "3"),
        ("Evaluate more", "Cross-dataset tests, adversarial evasion checks, load tests, and an RSA-hybrid option in the product.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.09, 1.6, 2.85, 3.9, t, b_, col, gl, body_size=19)
    K.box(s, 0.6, 5.75, 12.13, 0.95, fill=K.FHEAD, line=None)
    K.text(s, 0.85, 5.9, 11.6, 0.7, "Priority: items 1 and 2 close the largest honest gaps, the synthetic-trained default model and the missing link between detection and a transfer session.", size=16, color=K.INK, anchor="m")
    notes[19] = "Plan to the final review. The first two items address the largest honest gaps: synthetic default model and the missing coupling between detection and transfer."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Likely questions: why ECDH instead of RSA (objective deviation, benchmarked); why stacking does not beat XGBoost; how the shipped 97 percent relates to real traffic."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
