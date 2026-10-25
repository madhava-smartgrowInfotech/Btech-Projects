"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx."""

import os
import tempfile

from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K
from .refs import cite

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"
BACKEND = os.path.join(F.CODE, "backend")


# ------------------------------------------------------------------ slide helpers (same mechanics for every deck)
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
    cp.keywords = "credit card fraud, restricted Boltzmann machine, class imbalance, machine learning"
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
            K.replace_text(sh, F.TITLE, 34)
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


def crop(name, box, tag):
    """Crop a real screenshot to the part that matters on a slide (written to the temp folder, source untouched)."""
    out = os.path.join(tempfile.gettempdir(), f"a4_deck_{tag}.png")
    with Image.open(F.shot(name)) as im:
        im.crop(box).save(out)
    return out


def loc(fname):
    with open(os.path.join(BACKEND, fname), encoding="utf-8") as f:
        return sum(1 for _ in f)


def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}
    sv, bb, sd = F.SAVED, F.BASE_BAL, F.SERVING
    ens, sas, qs, pcd = sv["ensemble"], sv["sa"], sv["qa"], sv["classical"]
    L = F.LATENCY
    C = [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE]
    n_train, n_test = F.SPLIT["train"][0], F.SPLIT["test"][0]

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: three restricted-Boltzmann-machine classifiers behind a real-time screening interface",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = "This review shows how SecurePay AI is designed and built: the data and models, what is implemented, the first measured results and what is still open."

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and dataset"), ("03", "Preprocessing and model"), ("04", "Training and decision logic"),
               ("05", "Data flow, database and UML"), ("06", "Technology stack"), ("07", "Progress and preliminary results"),
               ("08", "Output screens and testing"), ("09", "Challenges and next steps")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Fraud is rare, so a classifier can look accurate while catching almost none of it. Rule systems are static and raise false alarms, and missing a fraud costs far more than reviewing a genuine payment.", K.ORANGE, "!"),
        ("Proposed system", "SecurePay AI: three Gaussian RBM classifiers trained by PCD, simulated annealing and a quantum-inspired sampler, averaged into one fraud probability with approve, challenge and decline bands.", K.BLUE, "i"),
        ("Base paper link", f"Neto et al. train the same model on 145 M real transactions and a D-Wave quantum annealer {cite('base')}. We use a synthetic 39,000-row set and a classical simulation, so results are not comparable.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.6, W, 4.5, t, b_, col, gl, body_size=20)
    notes[3] = "One-minute recap of Review 1: the imbalance problem, our system, and how the base paper relates: same model family, different data and no quantum hardware."

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.6, 1.3, 6.5, 5.6)
    K.text(s, 7.4, 1.5, 5.3, 5.3, [
        ("**Four tiers**", {"space_after": 8}),
        (f"Presentation: React and Vite single-page app (port {F.WEB_PORT}), 7 pages.", {"bullet": True}),
        (f"Application: Flask 3.1 API (port {F.API_PORT}), {F.N_ENDPOINTS} routes; 12 in app.py and 4 read-only ones in api_extra.py.", {"bullet": True}),
        ("Model tier: preprocessing, the GRBMC class, two samplers, the training loop and the metrics module.", {"bullet": True}),
        ("Data tier: a CSV, one pipeline pickle, three model pickles and history files. There is no SQL database and nothing leaves the machine.", {"bullet": True}),
    ], size=16, color=K.INK)
    notes[4] = "All routes live in backend/app.py and backend/api_extra.py. Storage is local files; an in-memory dictionary holds the loaded data, pipeline and models."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: end-to-end workflow")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.2, [("Synthetic transactions", K.NAVY), ("One-hot + z-score", K.PURPLE), ("Undersample + top-18", K.PURPLE), ("80 / 20 split", K.GREEN),
                                      ("Train 3 RBMs", K.ORANGE), ("Average + bands", K.BLUE), ("Flask + React", K.NAVY)], size=13, gap=0.22)
    for i, (t, b_) in enumerate([("One data path", "The Lab page, the seed script and the API call the same preprocessing and training functions, so the application and the measurements use the same code."),
                                 ("Same recipe as the paper", "Z-scored Gaussian visible units, one-hot categories, correlation filter, importance filter, manual undersampling to 50/50 and an 80/20 split, as in the base paper."),
                                 ("Measured, not typed", "scripts/run_experiments.py writes every reported number to experiments/metrics.json; figures and documents read from it.")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 3.2, 3.85, 3.2)
        K.text(s, x + 0.25, 3.35, 3.4, 0.5, t, size=21, color=K.INK, bold=True)
        K.text(s, x + 0.25, 4.0, 3.4, 2.3, b_, size=19, color=K.TXT)
    notes[5] = "Three design principles: one data path, the paper's preprocessing recipe, and numbers that come from a script."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Dataset")
    wipe(s)
    d = F.DATASET
    for i, (v, l, c) in enumerate([(f"{d['rows']:,}", "synthetic transactions, 29 columns", K.BLUE), (f"{d['fraud']:,} / {d['legit']:,}", "fraud / legitimate (50 / 50)", K.GREEN),
                                   (f"{n_train:,} / {n_test:,}", "train / test rows used by the app", K.ORANGE), ("1 %", "fraud variant used in experiments", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, c, vsize=24, lsize=12)
    K.picture(s, F.fig("f01_dataset_overview.png"), 0.6, 2.85, 12.13, 3.0)
    for i, t_ in enumerate([
        "Generated by backend/synthetic_data.py (seed 42) to imitate the base paper's balanced 39 k set. It is not the Stone data.",
        f"Fraud is built to look different: mean amount {d['amount_mean_fraud']:.0f} against {d['amount_mean_legit']:.0f}, more online and card-not-present payments, shifts in V3, V7, V10, V14 and V17.",
        "The planted signal makes scores higher than a real stream would give: a pipeline check, not a forecast. A 1 % fraud variant (390 fraud rows) is generated for the imbalance study."]):
        K.text(s, 0.6 + i * 4.14, 5.95, 3.85, 1.4, t_, size=13, color=K.INK if i < 2 else K.TXT, italic=(i == 2))
    notes[6] = "Be frank: the data is synthetic and the fraud pattern is planted by the generator. Published figures on real data would be lower and are not claimed."

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Preprocessing")
    wipe(s)
    K.picture(s, F.diag("10_flowchart_training.png"), 0.6, 1.3, 5.2, 5.65)
    K.text(s, 6.1, 1.45, 6.6, 5.5, [
        ("1  One-hot encode Merchant_Category (7 values) and Transaction_Type (4)", {}),
        ("2  Z-score the 24 numeric columns (Amount, Time, V1 to V22)", {}),
        (f"3  Correlation filter at 0.95: dropped {len(F.SPLIT['dropped_by_correlation']) or 'none'}", {}),
        ("4  Manual undersampling to equal class counts (SMOTE and Tomek links are options)", {}),
        ("5  Random-forest importance, keep the top 18 features", {}),
        (f"6  Stratified 80 / 20 split: {n_train:,} train and {n_test:,} test rows", {}),
        ("Known weakness: undersampling and feature selection happen before the split, so the test rows influenced which features were kept. Effect not measured.", {"italic": True, "size": 14, "color": K.TXT}),
    ], size=17, color=K.INK, space_after=12)
    notes[7] = "The recipe follows the base paper. The one flaw we found: balancing and feature selection run before the split. With synthetic data the effect is probably small, but it is not measured, so it is listed as a limitation."

    # ---- 8 model
    s = S[7]
    set_title(s, "Model: Gaussian RBM classifier")
    wipe(s)
    K.picture(s, F.diag("12_grbmc_structure.png"), 0.6, 1.3, 6.6, 4.1)
    rows = [["Trainer", "Hidden", "Batch", "Parameters"],
            ["PCD (classical)", "200", "512", "4,220"],
            ["SAS (simulated annealing)", "65", "32", "1,385"],
            ["QS (quantum-inspired)", "65", "32", "1,385"]]
    K.table(s, 7.5, 1.45, [2.4, 0.9, 0.9, 1.03], rows, font_size=13, row_h=0.5, first_bold=True, align=["l", "c", "c", "c"])
    K.text(s, 7.5, 3.65, 5.2, 3.3, [
        ("Visible layer: 18 z-scored features. Label layer: 2 units. Hidden units are binary.", {"bullet": True}),
        ("Prediction compares the free energy of label 0 and label 1 and turns it into a probability.", {"bullet": True}),
        ("The three differ only in how the negative phase is sampled.", {"bullet": True}),
    ], size=14, color=K.INK, space_after=7)
    K.tile(s, 0.6, 5.65, 3.8, 1.2, "numpy", "no deep-learning framework", K.BLUE, vsize=24)
    K.tile(s, 4.7, 5.65, 2.5, 1.2, "CPU", "seconds per run", K.GREEN, vsize=24)
    notes[8] = "Same architecture and hidden sizes as the base paper (200 for classical, 65 for the annealing variants). Parameter counts are W, U and the three bias vectors. The code is a simplified numpy version of the paper's setup."

    # ---- 9 training configuration
    s = S[8]
    set_title(s, "Training configuration")
    wipe(s)
    rows = [["Setting", "Value (from backend/train.py and samplers.py)"],
            ["Epochs, seed", "20 epochs per run in the saved histories; model seed 42; weights N(0, 0.01), sigma = 1"],
            ["PCD", "Persistent chain, one Gibbs step, batch 512, learning rate 0.01 x exp(-0.08 e)"],
            ["SAS", "10 sweeps x 16 reads, temperature 2.0 to 0.1, batch 32, 3,000 rows per epoch, same learning-rate decay"],
            ["QS", "Transverse-field flip with probability 0.3 x A(s), gamma 0.8, 10 sweeps x 16 reads, rate 0.005 x exp(-0.15 e) + 0.0005"],
            ["Hardware", "Windows 11, Intel i5-12500, CPU only; training takes " + f"{F.SEEDS['classical']['elapsed_sec']['mean']:.0f}-{F.SEEDS['sa']['elapsed_sec']['mean']:.0f} s per trainer"]]
    K.table(s, 0.6, 1.4, [2.0, 10.13], rows, font_size=14, row_h=0.56, first_bold=True)
    K.picture(s, F.fig("f07_seed_study.png"), 0.6, 4.95, 6.0, 2.0)
    K.text(s, 6.9, 5.0, 5.8, 1.9, f"Five retrainings: PCD F1 {F.seed_cell('classical', 'f1')} (unstable), SAS {F.seed_cell('sa', 'f1')}, QS {F.seed_cell('qa', 'f1')}. Metrics are the final epoch, not the best epoch, because best-epoch selection on the test split is optimistic.", size=14, color=K.TXT)
    notes[9] = "Settings come from the code. The seed study retrains in memory only and leaves the shipped models untouched. PCD's spread shows one run is not a reliable estimate."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: from score to action")
    wipe(s)
    K.picture(s, F.diag("11_flowchart_decision.png"), 0.6, 1.3, 4.9, 5.65)
    r4, r5, r6 = (next(r for r in sv["ensemble_threshold_sweep"] if abs(r["threshold"] - t) < 1e-9) for t in (0.4, 0.5, 0.6))
    K.text(s, 5.8, 1.5, 6.9, 5.4, [
        ("**Probability.** The mean of the three models' fraud probabilities.", {"bullet": True, "space_after": 9}),
        ("**Label.** FRAUD above 0.5, otherwise LEGITIMATE.", {"bullet": True, "space_after": 9}),
        ("**Action bands.** Below 40 % approve, 40 to 70 % challenge with 3-D Secure, above 70 % decline and alert.", {"bullet": True, "space_after": 9}),
        (f"**Threshold matters.** On the test split the ensemble gives precision {F.pct(r4['precision'], 0)} and recall {F.pct(r4['recall'], 0)} at 0.4, {F.pct(r5['precision'], 0)} and {F.pct(r5['recall'], 0)} at 0.5, {F.pct(r6['precision'], 0)} and {F.pct(r6['recall'], 0)} at 0.6. The 0.5 cut was never tuned on validation data.", {"bullet": True, "space_after": 9}),
        ("**Defect.** The scaling step in the batch route is skipped when it raises an exception (dashed box in the flowchart).", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[10] = "The decision logic is deliberately simple. We report the threshold trade-off because a fraud team would choose the cut by cost, not by default. The skipped scaling step is explained in the results review."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, F.diag("04_dfd_level1.png"), 0.6, 1.3, 6.4, 5.65)
    rows = [["Module", "Role", "Lines"], ["app.py", "routes, store, ensemble", str(loc("app.py"))], ["api_extra.py", "read-only chart data", str(loc("api_extra.py"))],
            ["preprocessing.py", "encode, scale, filter, balance", str(loc("preprocessing.py"))], ["rbm_classifier.py", "GRBMC, PCD, free energy", str(loc("rbm_classifier.py"))],
            ["samplers.py", "SA and QS gradients", str(loc("samplers.py"))], ["train.py", "epoch loop, schedules", str(loc("train.py"))],
            ["evaluation.py", "metrics", str(loc("evaluation.py"))], ["synthetic_data.py", "data generator", str(loc("synthetic_data.py"))]]
    K.table(s, 7.3, 1.4, [1.9, 2.5, 0.73], rows, font_size=12, row_h=0.5, align=["l", "l", "c"])
    K.text(s, 7.3, 6.05, 5.4, 0.8, f"Backend {F.BACKEND_LINES:,} lines; React front end {F.FRONTEND_LINES:,} lines.", size=13, color=K.TXT, italic=True)
    notes[11] = "Level-1 data flow: a transaction or CSV is encoded and scaled, scored by the three models, averaged and returned. Training reads the same dataset file and writes model and history files."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Persistence design and UML")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.6, 1.35, 6.4, 4.3)
    K.picture(s, F.diag("06_uml_class.png"), 7.2, 1.3, 5.5, 5.65)
    K.text(s, 0.6, 5.8, 6.4, 1.2, "No SQL database. State is a CSV, one pipeline pickle (scaler, columns, importances), three model pickles and three history files; a dictionary in app.py holds them while the server runs.", size=13, color=K.TXT, italic=True)
    notes[12] = "Honest point: persistence is file based, so the ER-style figure shows files and their relations. The class diagram shows GRBMC, the samplers and the Flask store."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    rows = [["Layer", "Technology"],
            ["Backend", "Python 3.11.9, Flask 3.1.0, Flask-Cors 5.0.0 (development server)"],
            ["Data and ML", "NumPy 1.26.4 (the RBM itself), pandas 2.2.1, scikit-learn 1.5.0 (scaler, forest, metrics), imbalanced-learn 0.12.4, joblib"],
            ["Experiments", "XGBoost 2.0.3 and scikit-learn baselines, Matplotlib 3.9.0 (figures)"],
            ["Front end", "React 19, Vite 8, React Router 7, Recharts 3, Framer Motion, GSAP, Lenis (port 5304)"],
            ["Persistence", "CSV, joblib pickles and JSON files on local disk"],
            ["Testing", "scripts/smoke_test.py (20 checks, standard library only); Playwright script for screenshots"],
            ["Run", "run.bat or run.ps1: installs requirements, starts Flask on 8304 and Vite on 5304"]]
    K.table(s, 0.6, 1.5, [2.6, 9.53], rows, font_size=15, row_h=0.62, first_bold=True)
    notes[13] = "Everything is open source and runs on a CPU. The RBM is plain numpy so every step is visible; scikit-learn is used for preprocessing and metrics."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Data generator and preprocessing pipeline", "Done", f"{F.DATASET['rows']:,} rows; 18 features; {n_train:,} / {n_test:,} split"],
            ["GRBMC with PCD, SA and QS trainers", "Done", f"saved F1 {F.pct(sas['f1'], 0)} (SAS), {F.pct(qs['f1'], 0)} (QS); PCD needs a tuned threshold"],
            ["Flask API ({} routes)".format(F.N_ENDPOINTS), "Done", f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} smoke checks pass; median {L['predict_single_fraud_example']['median_ms']:.0f} ms per check"],
            ["React interface (7 pages, light and dark)", "Done", "22 real screenshots incl. mobile and offline states"],
            ["Baselines and imbalance study", "Done (scripts)", "LR, RF, XGBoost; SMOTE, class weights, undersampling at 1 % fraud"],
            ["Feature scaling in the batch route", "Defect found", f"accuracy {F.pct(sd['as_served_no_scaling']['ensemble']['accuracy'], 0)} as served, {F.pct(sd['with_scaling']['ensemble']['accuracy'], 0)} when scaled"],
            ["Real transaction data, quantum hardware", "Not done", "synthetic data; classical simulation only"],
            ["Authentication, production server", "Not done", "no login; Flask development server"]]
    K.table(s, 0.6, 1.4, [4.6, 1.8, 5.73], rows, font_size=13, row_h=0.62)
    notes[14] = "State of the code base. The honest gaps: no real data, no quantum hardware, no authentication, and a scaling defect in the batch route found during the code review."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results")
    wipe(s)
    for i, (v, l, c) in enumerate([(F.pct(ens["f1"]), f"ensemble F1 (acc {F.pct(ens['accuracy'])}, n = {n_test:,})", K.BLUE), (f"{F.pct(sas['f1'], 0)} / {F.pct(qs['f1'], 0)}", "SAS / QS F1", K.GREEN),
                                   (F.pct(pcd["accuracy"]), "PCD accuracy: it flags 92 % of all transactions", K.ORANGE),
                                   (F.pct(bb["Logistic Regression"]["f1"]), "logistic regression F1, same split", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, c, vsize=24, lsize=12)
    K.picture(s, F.fig("f02_model_metrics.png"), 0.6, 2.9, 5.4, 3.1)
    K.picture(s, F.fig("f03_confusion_matrices.png"), 6.2, 2.9, 6.5, 1.65)
    K.text(s, 6.2, 4.65, 6.5, 2.3, [
        (f"ROC-AUC is {F.f3(ens['roc_auc'])} for all three, so PCD ranks well but its 0.5 cut is wrong.", {"bullet": True}),
        ("Logistic regression, random forest and XGBoost score higher on this synthetic data; the planted signal is easy.", {"bullet": True}),
        ("Base-paper F1 (83 / 88 / 84) is on real data and is not comparable.", {"bullet": True}),
    ], size=14, color=K.INK, space_after=6)
    K.text(s, 0.6, 6.15, 5.4, 0.8, "Shipped models on the held-out 20 % split, threshold 0.5.", size=12, color=K.TXT, italic=True)
    notes[15] = (f"Headline numbers with their caveats. Ensemble F1 {F.pct(ens['f1'])}; SAS {F.pct(sas['f1'])}; QS {F.pct(qs['f1'])}; PCD accuracy {F.pct(pcd['accuracy'])} with recall 100 percent and "
                 f"{pcd['fp']} false positives at 0.5 although its ROC-AUC is {F.f3(pcd['roc_auc'])}. Baselines: LR {F.pct(bb['Logistic Regression']['f1'])}, RF {F.pct(bb['Random Forest']['f1'])}, XGBoost {F.pct(bb['XGBoost']['f1'])}.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    shots = [("03_dashboard.png", (264, 72, 1440, 900), "dash"), ("04_verify.png", (264, 72, 1440, 900), "ver"),
             ("05_bulk.png", (264, 72, 1440, 900), "bulk"), ("10_models-comparison.png", (264, 72, 1440, 900), "cmp")]
    iw, ih = 3.55, 2.72
    for k, (name, box_, tag) in enumerate(shots):
        r, c = divmod(k, 2)
        K.picture(s, crop(name, box_, tag), 0.6 + c * (iw + 0.15), 1.3 + r * (ih + 0.12), iw, ih, border=True)
    K.text(s, 7.95, 1.4, 4.8, 5.6, [
        ("**Dashboard.** Real counts from the 39,000-row file and the best F1 of each model.", {"bullet": True, "space_after": 8}),
        ("**Verify.** A 1,200 online, card-not-present payment: ensemble 68.4 %, challenge band, per-model bars (50.9 / 59.5 / 94.7 %).", {"bullet": True, "space_after": 8}),
        ("**Bulk.** The 20-row sample: 20 of 20 flagged, 50 % accuracy. This is the bulk-route unscaled-input defect, shown as captured.", {"bullet": True, "space_after": 8}),
        ("**Model comparison.** Metrics, curves, features and the QUBO matrix of each trained model.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[16] = "Real captures of the running application at 1440 by 900, with the sidebar cropped off. The bulk screen is kept as captured: it shows the serving defect that the results review explains."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.SMOKE_PASSED} / {F.SMOKE_TOTAL}", "API smoke checks passed", K.GREEN), (f"{L['predict_single_fraud_example']['median_ms']:.0f} ms", "median single check (p95 " + f"{L['predict_single_fraud_example']['p95_ms']:.0f} ms)", K.BLUE),
                                   (f"{L['predict_batch_20_rows']['median_ms']:.0f} ms", "median 20-row CSV batch", K.ORANGE), ("No pytest", "unit suite not written", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, c, vsize=24, lsize=12)
    rows = [["Observation", "Action"],
            ["The batch route receives unscaled values: a bare except hides the scaler error", "Documented with measured impact; fix is first on the next-steps list"],
            ["PCD at threshold 0.5 flags " + F.pct(pcd["fp"] / (pcd["fp"] + pcd["tn"]), 0) + " of legitimate transactions (" + str(pcd["fp"]) + " of " + str(pcd["fp"] + pcd["tn"]) + ")", "Reported with the threshold sweep; threshold to be tuned on validation data"],
            ["History tables pick the best epoch on the test split", "Primary numbers use the final epoch; best-epoch kept as a labelled upper bound"]]
    K.table(s, 0.6, 3.0, [6.3, 5.83], rows, font_size=15, row_h=0.88)
    notes[17] = "The smoke test runs against the live API (read-only). No pytest suite exists; we say so rather than count tests that were never written. Each observation is documented, not hidden."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "Corrective action"],
            ["No quantum hardware and no real transaction data", "Classical simulation of the sampler and a synthetic dataset, stated on every results slide"],
            [f"PCD unstable: F1 {F.seed_cell('classical', 'f1')} over five seeds", "Report mean and spread; use SAS and QS in the ensemble; threshold tuning planned"],
            ["The batch route skips feature scaling", f"Measured the effect ({F.pct(sd['as_served_no_scaling']['ensemble']['accuracy'], 0)} against {F.pct(sd['with_scaling']['ensemble']['accuracy'], 0)} accuracy); documented, fix planned"],
            ["Simple baselines beat the RBM on this data", f"Reported openly: LR F1 {F.pct(bb['Logistic Regression']['f1'])} against {F.pct(ens['f1'])}"],
            ["Shared PC short of memory during experiments", "Resumable experiment script with allocation retries; one process at a time"]]
    K.table(s, 0.6, 1.5, [5.2, 6.93], rows, font_size=15, row_h=0.9)
    notes[18] = "Each challenge was met by a concrete step or by measuring it and saying so. The memory problem was environmental: a runaway process on the shared machine."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Fix and test", "Apply the scaler correctly in the batch route and add a regression test that would have caught it.", K.BLUE, "1"),
        ("Tune the decision", "Choose the threshold on validation data, calibrate PCD, and report cost-based operating points.", K.GREEN, "2"),
        ("Real data pilot", "Evaluate on a public real card dataset and on imbalance close to real life, with PR-AUC as the main metric.", K.ORANGE, "3"),
        ("Strengthen the sampler", "Replace the mean-field shortcuts with a proper annealing sampler; try D-Wave Leap access if it becomes available.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.09, 1.7, 2.85, 4.0, t, b_, col, gl, body_size=19)
    notes[19] = "Plan to the final review: fix the defect, tune the decision, test on real data and strengthen the sampler. The first two are small and are the most valuable."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Likely questions: why an RBM when baselines score higher (it is the base paper's model; we report the comparison openly); is it quantum (no, a classical simulation); is the data real (no, synthetic)."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
