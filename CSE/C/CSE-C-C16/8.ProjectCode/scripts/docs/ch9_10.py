"""Chapters 9 and 10 and the blocks shared by the chapter documents 9, 10, 12 and 15: novelty, contributions, scope, assumptions, limitations,
what was not measured, code walk-throughs, implementation decisions, conclusion and future scope. All numbers come from facts.py."""

from . import facts as F
from .blocks import B, CODE, H1, H2, H3, N, P, TAB
from .refs import cite

HC, HG, C, CS, CT, MB, BL = F.HC, F.HG, F.C, F.CS, F.CT, F.MB, F.BL


def src(rel, a=None, b=None):
    return F.src(rel, a, b)


# ------------------------------------------------------------------ shared numbers (strings)
ACC_H = F.pm(HC, "accuracy")                   # heuristic, crop chosen
ACC_H0 = F.pct(F.H0["accuracy"])               # hash seed 0 (run.bat)
ACC_HG = F.pm(HG, "accuracy")
TOP3_H = F.pm(HC, "top3_accuracy")
FAIL_H = F.pct(HC["failed_share"]["mean"])
HVD_H = F.pm(HC, "healthy_vs_diseased_accuracy")
ACC_C = F.pm(C, "accuracy")
F1_C = f"{C['macro_f1']['mean']:.3f}"
ACC_CS = F.mean_pct(CS, "accuracy")
ACC_CT = F.mean_pct(CT, "accuracy")
ACC_MB = F.pm(MB, "accuracy")
F1_MB = f"{MB['macro_f1']['mean']:.3f}"
TOP3_MB = F.pm(MB, "top3_accuracy")
HVD_MB = F.pm(MB, "healthy_vs_diseased_accuracy")
ACC_RF = F.pct(BL["random_forest"]["accuracy"])
ACC_HEAD = F.pm(MB, "head_only_accuracy")
LAT_MED = f"{F.LAT['detect_client_ms']['median']:.0f}"
LAT_P95 = f"{F.LAT['detect_client_ms']['p95']:.0f}"
TRAIN_ACC = F.pm(C, "train_accuracy")
MAJ = F.pct(F.H["majority_class_test"])
CH_KNOWN = F.pct(F.H["chance_with_crop_hint"])
CH_GEN = F.pct(F.H["chance_general"])
CONF_SUM = F.pct(F.HCONF["share_sum_over_102"], 0)
MAX_SUM = F.pct(F.HCONF["max_sum"], 0)
EDGE = f"{F.N_EDGE} checks, {F.N_EDGE_PASS} pass, {F.N_EDGE_DEFECT} reproduce defects"

OBJ_ROWS = [
    ["1. Labelled dataset of healthy and diseased leaves", f"PlantDoc: {F.NTRAIN + F.NTEST:,} web-scraped field photographs, 28 classes, 13 crops, split {F.NTRAIN:,} train / {F.NTEST} test; not collected by the team.", "Achieved (borrowed data)"],
    ["2. Preprocess and augment for lighting, angle, background", "Resize to 224 px and in-model flip, rotation, zoom and contrast augmentation in `train.py`; the shipped heuristic only resizes to 256 px.", "Partly achieved"],
    ["3. Train a CNN for specific disease categories", f"Compact CNN trained here: {ACC_C} accuracy (3 seeds), under-fitting; MobileNetV2 reference {ACC_MB}. No network is installed in the application.", "Trained, not accurate, not shipped"],
    ["4. Map each disease to a treatment and fertiliser recommendation", "All 38 classes return symptoms, severity and three treatments (chemical, organic, cultural) plus prevention. No fertiliser, yield or weather advice; not agronomist-validated.", "Treatment achieved; fertiliser not implemented"],
    ["5. Web interface with multilingual support", "React application with 12 pages, history, exports, analytics; English, Hindi and Marathi for interface strings only (disease text stays English).", "Web achieved; multilingual partly"],
    ["6. Per-class accuracy and validation of recommendations", "Per-class precision, recall and F1 and confusion matrices measured on 27 test classes; recommendations were not validated against agronomic guidance.", "Accuracy measured; validation not done"],
]


# ------------------------------------------------------------------ conclusion (chapter 9 and document 15)
def _conclusion(prefix):
    return [
        H2(f"{prefix}.1 Summary"),
        P(f"AgriVision turns a leaf photograph into a diagnosis card. A farmer signs in, chooses the crop, uploads a photograph and receives the most likely disease or 'healthy', "
          "a severity label, the three highest-scoring alternatives and chemical, organic and cultural treatment advice with prevention notes, for 38 classes of 14 crops. "
          "Every scan is stored, can be filtered, exported as CSV or PDF, deleted and summarised in a dashboard and in analytics. The interface works in English, Hindi and Marathi. "
          f"The application is a React single-page application over a FastAPI service that imports the original Flask product unchanged, with one SQLite database; it starts with one command, "
          f"answers a diagnosis request in a median of {LAT_MED} ms on the same machine and passes {F.N_SMOKE} of {F.N_SMOKE} smoke checks."),
        P(f"The project also measured what the application can recognise. No trained network is installed, so the engine that runs is a colour and texture heuristic. On the {F.NTEST} PlantDoc test photographs "
          f"it names the correct class for {ACC_H} of photographs when the crop is chosen and {ACC_HG} when it is not; the chance level is {CH_KNOWN} and {CH_GEN} respectively. "
          f"The compact CNN of the training script reaches {ACC_C}, and a reference MobileNetV2 with ImageNet weights reaches {ACC_MB} (macro-F1 {F1_MB}). "
          "The software is therefore complete as an application and incomplete as a diagnostic instrument."),
        H2(f"{prefix}.2 Objectives achieved"),
        P("The table below sets each objective of the batch document against what was delivered."),
        TAB("Objectives against outcomes", ["Objective", "What was delivered and measured", "Status"], OBJ_ROWS, widths=[1.7, 3.6, 1.2], align=["l", "l", "l"], size=9.5),
        H2(f"{prefix}.3 Key findings"),
        N(f"**The shipped heuristic does not diagnose.** Top-1 accuracy {ACC_H} with the crop chosen ({ACC_H0} with the hash seed that `run.bat` sets), top-3 {TOP3_H}, and {ACC_HG} with the crop left on 'general'. "
          f"Healthy-versus-diseased accuracy {HVD_H} is below the 61.9% obtained by always answering 'diseased'.",
          f"**The displayed confidence carries no information.** The mean displayed confidence is {F.pct(F.HCONF['mean_conf'], 0)}, while top-1 is correct on only {min(x for x in F.HCONF['acc_by_bin'] if x):.0f} % to {max(F.HCONF['acc_by_bin']):.0f} % of photographs "
          f"in the confidence bins that occur, and the three displayed scores add up to more than 102 % on {CONF_SUM} of answerable photographs (largest sum {MAX_SUM}).",
          f"**{FAIL_H} of test photographs get no answer** when the crop is chosen: ten of the engine's 19 crop keys (nine of the 18 offered in the web form) leave fewer than three candidate classes and the heuristic raises an error that the API reports as an unreadable image (defect D1).",
          f"**The shipped CNN recipe under-fits and reaches {ACC_C}.** Training accuracy is only {TRAIN_ACC}; the recipe that validates on the test folder gives {ACC_CS} and a run without learning-rate decay {ACC_CT}, so the cause is the model and the data size, not the schedule. "
          "The same script also mislabels the two grape classes during evaluation (defect D5).",
          f"**Transfer learning is the realistic route on field photographs.** MobileNetV2 reaches {ACC_MB} accuracy, {TOP3_MB} top-3 and {HVD_MB} healthy-versus-diseased accuracy; a random forest on colour and texture features reaches {ACC_RF}. "
          f"The PlantDoc authors report 29.7 % for VGG16 on raw photographs and 44.5 % to 70.5 % on cropped leaves {cite('plantdoc')}, so {ACC_MB} is in the expected range.",
          f"**The application layer is sound but has security gaps.** {EDGE}; the defects are the default public signing secret (D3) and the absence of login rate limiting (D4), besides D1, D2 and D7."),
        H2(f"{prefix}.4 Practical applications"),
        B("As a prototype for agricultural extension offices and student projects: the full path from photograph to advice, history and export is in place and runs on one CPU laptop.",
          "As a test bed for a real model: dropping `plantdoc_cnn.h5` and `labels.json` into `agrivision/models/` switches the engine, and the experiment script gives a repeatable way to compare candidates.",
          "As a disease reference: the disease guide with symptoms, lifecycle and treatments for 38 classes is usable without any model.",
          "Not as a decision tool for spraying: advice must be confirmed by an agricultural officer, as the application itself states on every result."),
        H2(f"{prefix}.5 Known limitations"),
        P("The limitations are listed with evidence in Chapter 7 and in the document on scope and limitations. In short: no accurate model in the product, 50 % at best in the reference experiment; "
          "seven defects, of which D1 and D5 matter most; no fertiliser, yield or weather advice; unvalidated advice; translated interface but not translated advice; PlantDoc only, no own photographs, no field trial or user study."),
    ]


def chapter9_blocks():
    return [H1("CHAPTER 9: CONCLUSION")] + _conclusion("9")


def conclusion_blocks():
    return _conclusion("1")


# ------------------------------------------------------------------ future scope (chapter 10 and document 15)
def _future(prefix):
    return [
        P("The measurements of Chapter 8 define the order of work: first make the recognition trustworthy, then widen what the application advises on, then prepare it for more users. "
          "Each item below is tied to a limitation or defect of this report."),
        H2(f"{prefix}.1 Improvements to the diagnosis"),
        P("The recognition quality is the weakest part of the project, so improvements start there. The first step costs little: a trained network that is already better than the heuristic exists in the experiment script."),
        N("**Ship a trained network.** Fine-tune MobileNetV2 (2.29 million parameters, "
          f"{F.MB['latency_ms_median']['mean']:.0f} ms per image on this CPU) or EfficientNet {cite('efficientnet')} on more data, save it as `plantdoc_cnn.h5` with `labels.json` and let `try_load_model()` pick it up. The expected level on this data is 50 % to 70 %, so the interface must keep its warning.",
          "**Fix defects D1 to D7.** Guard `_heuristic_predict` for crops with fewer than three candidates (or pad the candidate list); sum the three displayed scores to 100 % or hide them; require `AGRIVISION_SECRET` at start-up; add rate limiting to login; correct the class-name list and the validation split in `train.py`; remove the constant latency padding.",
          "**Crop first, then classify.** PlantDoc authors obtain their best results after cropping to the leaf; a leaf detector or a simple segmentation step would remove most background noise.",
          "**Calibrate and abstain.** Replace the saturating score with calibrated probabilities (temperature scaling) and return 'not sure, ask an officer' below a threshold, evaluated on a held-out set.",
          f"**Explain the decision.** Grad-CAM {cite('gradcam')} maps on the leaf photograph would show the farmer which region drove the answer; the nested-backbone limitation of the shipped Grad-CAM helper has to be solved first.",
          f"**Collect own photographs.** Field photographs from the target region, labelled by an agronomist, are needed to measure real accuracy; the base paper's idea of generating foliage images {cite('base')} could extend a small set but is a research task of its own."),
        H2(f"{prefix}.2 Additional features"),
        P("The batch abstract proposes several services that this implementation does not contain. They are listed here in the order in which they would add most for a farmer."),
        B("**Fertiliser advice:** nutrient-deficiency classes and dose tables per crop and growth stage, reviewed by an agronomist.",
          "**Yield prediction and weather:** rainfall, temperature and soil data (the batch abstract proposes OpenWeatherMap) to give spray timing and expected yield; none of this exists yet.",
          "**Translation of advice:** treatment, symptoms and prevention text in Hindi, Marathi and further languages; today only about 44 interface strings are translated.",
          "**Voice and low-literacy input:** speech output of the diagnosis and voice-driven navigation.",
          "**Administrative dashboard:** user management, disease trends by region and model monitoring for an extension office.",
          "**Multiple diseases and foliage images:** several leaves or a whole canopy in one photograph, as in the base paper."),
        H2(f"{prefix}.3 Scalability and deployment"),
        P("The present deployment is one process on one PC, which suits a demonstration. A service for an extension office needs the following changes."),
        B("Move from SQLite to PostgreSQL and the image folder to object storage when more than one server is used.",
          "Containerise the API and the web build, serve the web build from a static host or reverse proxy rather than the Vite server, and terminate TLS.",
          "Add rate limiting, account lock-out, password reset and token refresh, and keep the signing secret in a secret store.",
          f"Run load tests: the current latency figures (median {LAT_MED} ms, 95th percentile {LAT_P95} ms) are for one client on one PC.",
          "Offline use: convert the network to TensorFlow Lite and cache the disease guide so that a phone can diagnose without a connection."),
        H2(f"{prefix}.4 Further research"),
        P("Beyond engineering, the experiments raise questions that a longer project could answer."),
        B("Domain adaptation from laboratory images (PlantVillage) to field photographs, where the literature reports large drops.",
          "Few-shot learning for rare diseases (the PlantDoc spider-mite class has two training photographs).",
          "Severity estimation from lesion area instead of a fixed per-disease label.",
          "Evaluating whether the generated foliage images of the base paper improve diagnosis of the crops covered here.",
          "A user study with farmers on whether the advice is understood and acted on."),
    ]


def chapter10_blocks():
    return [H1("CHAPTER 10: FUTURE SCOPE")] + _future("10")


def future_blocks():
    return _future("2")


# ------------------------------------------------------------------ novelty and contributions
def novelty_blocks():
    return [
        H2("Position against the base paper"),
        P(f"The base paper, Foliagen {cite('base')}, is a data-generation framework: it removes the background of single-leaf photographs, places leaves following the phyllotaxis of soybean or tomato "
          "and sets a chosen share of diseased leaves, so that classifiers can be trained and fine-tuned for foliage images taken in the field. Its reported result is up to 98 % accuracy on a natural foliage set when "
          "5 % of that set is added to generated data, measured on two RTX 6000 Ada GPUs. It contains no application, no treatment advice and no multilingual support, and the batch literature survey names exactly that as the gap: joining reliable classification "
          "to actionable, multilingual treatment and fertiliser recommendation."),
        P("AgriVision does not implement Foliagen. It takes the problem that remains once a classifier exists: how a farmer receives and uses the answer. The comparison below is therefore qualitative; task, crops, data and hardware differ and no number of this project can be set against the 98 % of the base paper."),
        TAB("AgriVision against the work it builds on", ["Work", "What it delivers", "Data and result", "What AgriVision adds or changes"],
            [[f"Foliagen {cite('base')}", "Generated, annotated foliage images; classifier training and fine-tuning", "Soybean and tomato; up to 98 % on natural foliage with 5 % real data", "Does not generate data; single-leaf photographs, 14 crops in the knowledge base, an application around the classifier"],
             [f"PD36-C {cite('pd36c')}", "18-layer CNN of 1.25 M parameters and a desktop GUI", "87 k laboratory-style images, 38 classes, 99.53 %", "Web application with accounts, history and advice; measured on field photographs, where accuracy is far lower"],
             [f"Kanakala and Ningappa {cite('lstm')}", "CNN and LSTM leaf classifiers", "70,295 training images, 38 classes, 96.4 % validation", "Reports a held-out test on field photographs and the failure analysis, not only validation accuracy"],
             [f"PlantDoc {cite('plantdoc')}", "Dataset and benchmark of field photographs", "27 classes, 44.5 % to 70.5 % on cropped leaves", "Uses its official split; reproduces the difficulty (50.3 % for MobileNetV2 on uncropped photographs)"]],
            widths=[1.2, 1.8, 1.8, 1.9], align=["l", "l", "l", "l"], size=9),
        H2("What is standard"),
        B("Transfer learning from ImageNet weights with a small classification head, as in the MobileNetV2 reference experiment.",
          "A compact separable-convolution CNN trained from scratch (the shipped `train.py`).",
          "A FastAPI service, a SQLite database, a React front end and bearer-token authentication.",
          "Per-class precision, recall and F1, a confusion matrix and several seeds as evaluation practice."),
        H2("What is new here, modestly"),
        N("**A farmer-facing path from photograph to advice in one deployable stack** that runs on a CPU laptop with one command and keeps history, exports and analytics per user.",
          "**A clean layering over a legacy product:** the FastAPI service imports the Flask product's detection, knowledge and database modules and shares its database and uploads, so both front ends see the same scans.",
          "**A reproducible, seeded benchmark on PlantDoc** that measures the shipped heuristic engine (5 hash seeds), the shipped CNN recipe (3 seeds), a transfer-learning reference (3 seeds) and classical baselines under one protocol, with the test folder never used for selection.",
          "**Documented defects and an honest account of what the product does and does not recognise**, which the batch abstract does not anticipate: the heuristic is no better than chance, ten crop options crash it, the displayed confidence is meaningless."),
        H2("What is not claimed"),
        B("No new network architecture, no new dataset and no new learning algorithm.",
          "No improvement over the base paper or over PD36-C; no like-for-like comparison with them is possible.",
          "No validated agronomic advice and no field trial."),
    ]


def contribution_blocks():
    items = [
        ("A complete diagnosis-and-advice application.", "Upload, diagnose, store, filter, export, delete, dashboard and analytics, three interface languages and light and dark themes, in 12 pages and 16 API routes (about 5,600 lines of TypeScript and 437 lines of API code over the original product)."),
        ("A tested contract between the new API and the legacy product.", f"The FastAPI layer reuses `inference.py`, `disease_db.py` and `init_db()` without copying them. {F.N_SMOKE} smoke checks and {F.N_EDGE} further checks (unit and API) exercise it."),
        ("A knowledge base of 38 classes with structured advice.", "Each class has a severity, symptoms, lifecycle, three treatment types with cost text, prevention and an urgent flag; 26 diseases are curated and the remainder fall back to five generic kinds."),
        ("A reproducible measurement of recognition quality.", f"`scripts/run_experiments.py` evaluates the heuristic, the compact CNN, MobileNetV2 and two classical baselines on the official PlantDoc split with fixed seeds: {ACC_H} (heuristic), {ACC_C} (compact CNN), {ACC_MB} (MobileNetV2)."),
        ("A defect register.", "Seven defects (D1 to D7) found by measurement and by tests, each with evidence and a proposed fix, which turns a prototype into a work list."),
    ]
    out = [N(*[t for t, _ in items])]
    for i, (t, d) in enumerate(items, 1):
        out.append(P(f"**Contribution {i}: {t}** {d}"))
    return out


# ------------------------------------------------------------------ scope, assumptions, limitations
def scope_blocks():
    return [
        H2("In scope"),
        TAB("What the project covers", ["Area", "Included"],
            [["Input", "One photograph of one leaf (JPG, PNG, JPEG or WEBP, up to 10 MB) and a crop chosen from 18 options plus 'general'"],
             ["Output", "Most likely class of 38 (26 diseases, 12 healthy), top-3 list, severity (high, medium, none), urgent flag, symptoms, lifecycle, three treatments, prevention"],
             ["Users", "Anonymous visitors (disease guide) and registered farmers (diagnosis, history, exports, dashboard, analytics, profile)"],
             ["Platform", "Web application on a local PC, English, Hindi and Marathi interface, light and dark theme, desktop and phone widths"],
             ["Data", f"PlantDoc ({F.NTRAIN:,} train and {F.NTEST} test photographs) for the measurements; one SQLite database"],
             ["Evaluation", "Accuracy, top-3, macro-F1, per-class scores, confusion matrix, healthy-versus-diseased accuracy, CPU latency, API response times, automated tests"]],
            widths=[1.2, 5.3], align=["l", "l"], size=10),
        H2("Out of scope"),
        TAB("What the project does not cover", ["Area", "Not covered", "Reason"],
            [["Yield prediction", "Not implemented", "Proposed in the batch abstract; needs environmental data and a separate model"],
             ["Weather advice", "Not implemented", "Needs an external weather service and region model"],
             ["Fertiliser dosing", "Treatment text only", "Needs agronomist-reviewed dose tables"],
             ["Voice interface", "Not implemented", "Outside the time available"],
             ["Administrative dashboard", "Not implemented", "Only per-user views exist"],
             ["Foliage or multi-leaf images", "Single leaf only", f"Foliagen {cite('base')} generates foliage data; not reproduced here"],
             ["A trained network in the app", "Heuristic only", f"The CNN was trained offline ({ACC_C}); MobileNetV2 ({ACC_MB}) is a reference experiment"],
             ["Field trial, user study", "Not done", "No farmers involved; PlantDoc photographs only"]],
            widths=[1.6, 1.4, 3.5], align=["l", "l", "l"], size=10),
        H2("Hardware and software boundary"),
        P(f"All measurements were made on {F.HARDWARE}. Software: {F.SOFTWARE}. Training times are indicative because other jobs shared the processor."),
    ]


def assumption_blocks():
    return [
        P("The work rests on the following assumptions; each is stated so that a reader can judge how far the results travel."),
        N("The user photographs a single leaf in daylight and chooses the correct crop; the heuristic and the crop filter assume this.",
          "PlantDoc photographs represent field conditions well enough to measure accuracy; they are web-scraped, of mixed quality and may contain duplicates between classes.",
          "The official PlantDoc test folder is untouched by training and model selection in the experiments reported here; selection used a 10 % validation split of the training folder.",
          "The knowledge base text (doses, products, prices in rupees) is general guidance written for the project; it is not region-specific and was not reviewed by an agronomist.",
          "One user works on one PC; the application is a local deployment with a single backend process and one SQLite file.",
          "The signing secret, ports and demo account are development defaults and are changed before any real deployment."),
    ]


def limitation_blocks():
    return [
        P("Each limitation is given with the evidence that supports it; defect numbers D1 to D7 are used throughout the report."),
        TAB("Limitations and defects", ["No.", "Limitation", "Evidence"],
            [["L1", "The application ships no trained network; the heuristic engine does not diagnose.", f"Top-1 {ACC_H} with the crop chosen, {ACC_HG} on 'general'; chance {CH_KNOWN} and {CH_GEN}; healthy-versus-diseased {HVD_H}."],
             ["L2", "Even the best measured model is not usable on its own.", f"MobileNetV2 {ACC_MB}, macro-F1 {F1_MB}; several classes have F1 0 (bell pepper leaf spot, tomato bacterial spot, tomato mosaic virus)."],
             ["L3 (D1)", "Ten of the engine's 19 crop keys (nine of the 18 offered in the web form) make the heuristic fail.", f"IndexError for fewer than three candidates; API answers HTTP 400 'unreadable image'; {FAIL_H} of test photographs unanswered (screenshot 16)."],
             ["L4 (D2)", "The displayed confidence is not a probability.", f"Floor 0.62, saturates near 97 %; the three scores sum to more than 102 % on {CONF_SUM} of photographs, up to {MAX_SUM}."],
             ["L5 (D3)", "Default token-signing secret is public.", "A token signed with `agrivision-dev-secret-change-me` is accepted unless `AGRIVISION_SECRET` is set (edge test)."],
             ["L6 (D4)", "No rate limiting on login.", "Eight wrong passwords in 2.8 s were all answered (edge test)."],
             ["L7 (D5, D6)", "The shipped training script is unreliable.", "Validates and selects on the test folder; 27 test class names against a 28-class model shift the two grape labels; docstring claims about 1.1 M parameters, measured 189,655."],
             ["L8 (D7)", "Reported latency is padded.", "`predict()` adds a constant 40 ms to the heuristic's measured time."],
             ["L9", "The data are small, imbalanced and web-scraped.", f"{F.NTRAIN:,} training photographs, 2 to 180 per class, 27 test classes, 236 test photographs (about 9 per class); one test class missing."],
             ["L10", "Advice is general and unvalidated.", "No agronomist review; doses are not tied to region, growth stage or area; costs are indicative."],
             ["L11", "Fertiliser, yield and weather advice, voice and admin are missing.", "Proposed in the batch abstract; not present in the code."],
             ["L12", "Multilingual support covers interface strings only.", "44 translated keys; symptoms, treatments and prevention remain English (screenshot 17)."],
             ["L13", "Single-leaf photographs only; the base paper's foliage setting is not addressed.", "Upload takes one image; no foliage-level model."],
             ["L14", "Statistical and field validation is limited.", "Three seeds, no significance test; one seed for the shipped-protocol and tuned-CNN runs; no field trial, user study or load test; UI checks not re-run in this documentation run."]],
            widths=[0.8, 2.4, 3.3], align=["l", "l", "l"], size=9),
    ]


def not_measured_blocks():
    return [
        P("The following were not measured, and no number is given for them in this report."),
        B("Accuracy on photographs other than PlantDoc, on photographs taken by the team, or on crops outside the 13 PlantDoc crops.",
          "Agreement of the treatment advice with agronomic guidance, or its usefulness to farmers (no expert review, no user study).",
          "Behaviour under concurrent users or large histories (no load test); only one client on one PC was timed.",
          "Latency on a phone, on a GPU, or of the application when a Keras model is installed (the CNN latency of about 70 ms was measured outside the application).",
          "Calibration of the MobileNetV2 probabilities; probabilities of the compact CNN beyond the top-3 accuracy.",
          "Statistical significance of differences between models (three seeds only; the shipped-protocol and tuned-CNN runs used one seed).",
          "Effect of Foliagen-generated images on diagnosis of the crops covered here.",
          "Browser compatibility beyond Chrome in headless mode; the 55 UI checks were run in the previous session and not repeated here.",
          "Accessibility testing with assistive technology."),
    ]


# ------------------------------------------------------------------ code walk-throughs
def walkthrough_blocks():
    return [
        H2("Signed bearer token"),
        P("The API does not use a library for sessions. `make_token` encodes the user id and an expiry (seven days) as base64 JSON and appends an HMAC-SHA256 signature computed with a server secret; "
          "`read_token` recomputes the signature, compares it in constant time and checks the expiry. `current_user` reads the `Authorization: Bearer` header, resolves the id against the `users` table and refuses inactive accounts with HTTP 401. "
          "The scheme is small and testable, but its safety rests entirely on the secret: the default value in `config.py` is public (defect D3)."),
        CODE(src("backend/main.py", 94, 110) + "\n\n" + src("backend/main.py", 123, 130), 8),
        H2("The detection endpoint"),
        P("`detect` is the only route that changes both disk and database. It rejects a missing or empty file, a disallowed extension (400) and a file over 10 MB (413), calls `predict`, and turns any exception into HTTP 400 'unreadable image' - which is how defect D1 surfaces for a valid photograph. "
          "It then looks up the knowledge card of the top-1 class, writes the upload under a random UUID name (so the URL is the capability), inserts one `results` row with the top-3 list as JSON and returns the card's treatments."),
        CODE(src("backend/main.py", 306, 340), 7.5),
        H2("Feature extraction"),
        P("The heuristic reduces a photograph to six numbers on a 256 x 256 copy: the share of pixels that are greener than red and blue, brownish, yellowish, dark and near-white, and the overall standard deviation. "
          "These are cheap and explainable, but they confuse a lesion with soil, a shadow or a pale leaf."),
        CODE(src("agrivision/inference.py", 87, 100), 8),
        H2("Scoring and calibration"),
        P("For each candidate class the score is a hand-written linear formula: a healthy class gains from green and loses from brown, yellow and dark pixels; a diseased class gains from brown, yellow, dark and white pixels, with bonuses for words in its name (mildew, rust, blight, mosaic, mite). "
          "A hash-based jitter keeps the order stable per image. The top score is then mapped into 0.62 to 0.99, which is why almost every answer shows 97 %; the second and third values are fractions of the first taken from the image hash, which is why the three scores add up to more than 100 % (D2). "
          "When a crop has fewer than three candidates `ranked[1]` does not exist and the function raises (D1)."),
        CODE(src("agrivision/inference.py", 108, 145), 7),
        H2("Knowledge card"),
        P("`get_disease_info` assembles the card from a curated override where one exists and from five generic kinds otherwise, so every class returns three treatments, a prevention note, a lifecycle text and a severity; "
          "an unknown class silently falls back to 'Tomato healthy', which hides errors."),
        CODE(src("agrivision/disease_db.py", 177, 221), 7),
        H2("The compact CNN"),
        P(f"`build_model` stacks five depthwise-separable convolution blocks (32 to 256 filters) with batch normalisation, max-pooling and dropout, global average pooling and a 256-unit dense layer, in the spirit of efficient mobile networks {cite('xception')}, {cite('mobilenet')}. "
          "Augmentation layers are part of the model and only act in training. The network has 189,655 parameters and 2.4 MB on disk."),
        CODE(src("agrivision/train.py", 25, 52), 7.5),
        H2("Evaluation code"),
        P("`metrics_from_preds` computes the confusion matrix and, from it, per-class precision, recall and F1, macro and weighted F1 over the classes that have test photographs, and top-3 accuracy. "
          "Classes without test photographs (spider mites) are excluded from the macro average rather than counted as zero."),
        CODE(src("scripts/run_experiments.py", 62, 95), 7),
    ]


def decision_blocks():
    return [
        P("The table lists the decisions that shaped the implementation, the alternatives and why each was taken or accepted."),
        TAB("Implementation decisions", ["Decision", "Alternative", "Reason and consequence"],
            [["FastAPI layer over the original Flask product", "Rewrite the product, or extend Flask", "The detection, knowledge and database code already existed; importing it avoids a second copy and keeps the Flask pages working. Consequence: the Flask quirks (positional INSERT, `UNREADABLE_IMAGE` mapping) are inherited."],
             ["React single-page application with a Vite proxy to `/api`", "Server-rendered Flask templates", "Faster interaction, charts and responsive layout; no CORS or port constants in the browser code."],
             ["SQLite with two tables", "PostgreSQL", "Zero set-up on a student PC; one file shared by both front ends. Not suitable for several servers."],
             ["Heuristic engine as the default, Keras or ONNX model when present", "Block the product until a model exists", "The application stays demonstrable and the engine is swappable by dropping a file. Consequence: the shipped answers are close to chance, so the interface says 'Heuristic engine' everywhere."],
             ["Knowledge base in Python code", "Database table or CMS", "Versioned with the code and available without a database; an agronomist cannot edit it without a developer."],
             ["HMAC-signed bearer token, seven days", "Server sessions or a JWT library", "Stateless and about 20 lines; no revocation, and safe only if the secret is set (D3)."],
             ["`PYTHONHASHSEED=0` in `run.bat`", "Remove the hash from the score", "Keeps the hash-based jitter of the heuristic identical between runs; the root cause (using `hash()`) remains."],
             ["Interface strings translated, advice text not", "Translate the knowledge base", "A 44-key dictionary is cheap and safe; translating agronomic advice needs expert review."],
             ["Random file names for uploads, served without a token", "Authenticated file route", "Simple `<img>` tags; the unguessable name is the capability."],
             ["Experiments with a 10 % validation split from the train folder", "Select on the test folder as `train.py` does", "Keeps the 236 test photographs untouched; costs 10 % of the training data."],
             ["MobileNetV2 as the reference model", "EfficientNet or a larger backbone", f"ImageNet weights are available, the model is small ({F.MB['params']['mean'] / 1e6:.2f} million parameters) and trains in about {F.MB['train_seconds']['mean'] / 60:.0f} minutes on CPU."]],
            widths=[1.8, 1.5, 3.2], align=["l", "l", "l"], size=9),
    ]
