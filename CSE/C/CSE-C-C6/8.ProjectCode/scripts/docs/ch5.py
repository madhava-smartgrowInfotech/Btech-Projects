"""Chapter 5: System Design. Also holds DIAGRAMS, the list used by 11. BLOCK DIAGRAMS ALL.docx."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, PAIR, TAB

_D = F.DEMO
_A = F.A

# (key, title, file, caption, explanatory paragraph(s)); every box and arrow of the images mirrors the code
DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "System architecture of TruthGlow: presentation, application and domain tiers over two file stores.",
     "The system has three tiers over two stores. The presentation tier is a React 18 + TypeScript single-page application built with Vite and Tailwind CSS and served on port 5406; "
     "it has six screens (the landing page and the Detect, Batch check, Model analytics, Retrain and About screens), an axios client that sends every call to `/api`, and TanStack Query hooks. "
     "The application tier is a thin FastAPI service (`backend/main.py`, port 8406) with eight endpoints under `/api`, one pipeline object held in memory behind a re-entrant lock, and a "
     "background thread for retraining whose state lives in a dictionary. The domain tier is the library `src/` (preprocessing, dataset, firefly, pipeline) built on scikit-learn; "
     "the same library is used by the command-line scripts and by the original Streamlit application, so the three front ends cannot drift apart. The first store is the joblib bundle "
     "`models/msvm_model.pkl` (with `metrics.json` written by `train.py`); the second is the temporary file that holds an uploaded labelled CSV while it is parsed and is deleted afterwards. "
     "There is no SQL database and no user account."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "High-level workflow: the training path (offline or from the Retrain screen) and the inference path.",
     "The workflow has two paths that share the same fitted objects. The training path takes labelled text, cleans it, builds TF-IDF (one- and two-word groups) and 25 stylometric features, standardises "
     "and reduces them with PCA, splits the result 80/20 with stratification, lets the Firefly algorithm choose a subset of the PCA components together with C and gamma, fits the final RBF multi-class SVM "
     "with balanced class weights, evaluates it and saves the whole bundle. The inference path takes a headline and body text, applies the same fitted vectoriser, scaler and PCA, keeps only the "
     "components the Firefly search selected, and asks the SVM for a class and for class probabilities. Because the fitted vectoriser, scaler, PCA and mask are stored together in one file, "
     "training and prediction cannot use different preprocessing."),
    ("dfd0", "Data flow diagram, level 0 (context)", "03_dfd_level0.png",
     "Level 0 data flow diagram: the system as one process with three external entities.",
     "At the context level the system is one process. The reader or analyst sends article text (a headline and body) or a CSV of articles and receives a verdict, a confidence, class probabilities and cue "
     "words, or a results CSV with the distribution of verdicts. The model owner sends a retrain request with the Firefly budget and receives the accuracy, the macro-F1 and the model statistics. "
     "The labelled corpus, a CSV file with a text column and a label column, supplies the training rows. The two human entities use the same screens; they are separated only to show who typically starts each flow."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "Level 1 data flow diagram: four processes and two data stores.",
     "Level 1 has four processes. 1.0 Detect single article takes article text from the reader and returns the verdict, confidence, probabilities and cues, reading the fitted vectoriser, scaler, PCA, mask, "
     "C, gamma and classifier from D1, the model bundle. 2.0 Batch detect CSV takes a CSV of articles, reads D1 in the same way and returns the results CSV and the distribution of verdicts. "
     "3.0 Train / retrain model takes the retrain request from the model owner and the labelled rows held temporarily in D2, writes a new bundle to D1 and returns the accuracy and macro-F1. "
     "4.0 Report model statistics reads the statistics stored inside D1 and returns them (accuracy, macro-F1, confusion matrix, Firefly curve, classification report, baseline) to the screens. "
     "Process 3.0 is expanded in the level 2 diagram."),
    ("dfd2", "Data flow diagram, level 2 (process 3.0)", "05_dfd_level2.png",
     "Level 2 data flow diagram: the seven steps inside process 3.0, Train / retrain model.",
     "Process 3.0 expands into seven steps that follow `FakeNewsMSVMPipeline.fit` and the retraining endpoint. 3.1 validates the request (Firefly budget within range, at least 30 rows, a label column) and loads the labelled "
     "rows from the temporary CSV (D2) or builds the demo corpus. 3.2 cleans the text and builds the 4,025-column matrix of TF-IDF and stylometric features. 3.3 standardises it and applies PCA. 3.4 performs the stratified 80/20 split. "
     "3.5 runs the Firefly search on the training part and returns the mask, C and gamma. 3.6 fits the final SVM on the masked training part and evaluates it on the test part, producing the statistics. "
     "3.7 saves the bundle to a temporary file, replaces the model file atomically, swaps the in-memory pipeline under the lock and reports the accuracy and macro-F1 as the job status."),
    ("uml", "UML class diagram", "06_uml_class_diagram.png",
     "UML class diagram of the main classes and modules.",
     "The library is small, so the diagram shows the real classes and the modules around them. `backend.main` holds the module-level state (`_pipe`, `_lock`, `_jobs`) and the upload limits, and its endpoint functions "
     "call `get_pipe()`, which returns the one `FakeNewsMSVMPipeline`. The pipeline owns exactly one `FireflyOptimizer` and composes the scikit-learn parts: `TfidfVectorizer`, `StandardScaler`, `PCA` and `SVC`; it uses the "
     "`preprocessing` module (`clean_text`, `stylometric_features`, the label constants). The `dataset` module (`load_csv`, `build_demo_dataset`) is used by the backend when it builds or retrains a model. "
     "The optimiser is needed only while fitting; at prediction time only its best mask is kept, so a loaded pipeline carries a minimal optimiser object holding the mask, C and gamma."),
    ("seq", "Sequence diagram: detecting one article", "07_sequence_diagram.png",
     "Sequence diagram of one detection request, from the Detect screen to the SVM and back.",
     "The user types or loads an article and presses Detect (step 1); the page posts `{title, text}` to `/api/predict` (2). The backend joins the title and text and rejects fewer than five words with status 422 (3), "
     "then asks the pipeline to predict (4). The pipeline cleans the text, computes the stylometric features and the TF-IDF transform (5-6), scales and projects with PCA (7-8), keeps the selected components and asks the SVM for the class "
     "and the probabilities (9-10). The pipeline returns the class ids and probabilities (11); the backend builds the label, the confidence (the largest probability), the latency in milliseconds and the cue words (12) and returns the JSON verdict (13), which the "
     "page shows as a verdict badge, a class-probability chart and two cue lists (14)."),
    ("uc", "Use case diagram", "08_use_case_diagram.png",
     "Use case diagram: seven use cases and two actors.",
     "The reader or analyst can check one article (UC1), which includes seeing the cue words and class probabilities (UC2); check a CSV of articles (UC3), with the option to download the results CSV (UC4); view the model analytics (UC5); "
     "and read how the system works (UC7). The model owner retrains the model with the demo corpus or an own CSV (UC6) and also views the analytics. The application has no login, so every user can open every screen; "
     "the two actors only show who typically starts which use case."),
    ("er", "Entity-relationship diagram (file store)", "09_er_diagram.png",
     "Entity-relationship diagram of the data model; the product has no SQL database.",
     "TruthGlow stores no records in a database. A TrainingCSV, an upload with a text column and a label column, feeds at most one RetrainJob; the job lives only in the memory of the API process (identified by a 12-character job id, with its status, "
     "source, settings and result). A finished job replaces the single ModelBundle file, which holds the fitted vectoriser, scaler, PCA, mask, C, gamma, classifier and parameters together with its ModelStats (document count, feature counts, "
     "Firefly history, accuracy, macro-F1, classification report, confusion matrix, baseline scores and training time). One bundle produces many Predictions and BatchResults, but these are transient responses and are never stored."),
    ("algo", "Flowchart of the core algorithm", "10_core_algorithm_flowchart.png",
     "Flowchart of the core algorithm: (A) the Firefly search and (B) the final model and inference.",
     "Part A is `FireflyOptimizer.optimize`. A population of ten fireflies is created; each is a vector of one mask logit per PCA component plus log10 C and log10 gamma. The brightness of a firefly is the three-fold cross-validated macro-F1 of an "
     "RBF SVM trained on the masked training data, minus 0.02 times the share of components kept. For each of twelve generations every firefly moves towards every brighter one by a step that shrinks with distance, plus a random term "
     "whose size decays by 0.97 per generation; C and gamma are clipped to their ranges and the brightness is re-evaluated. The best vector is kept, the dimmest firefly is replaced by the best plus noise, the best brightness is recorded in the history "
     "and the loop repeats. The best vector is then decoded: a component is kept when its sigmoid exceeds 0.5. Part B fits the final SVM on the masked training data, scores the held-out 20 %, fits a default SVM on all components "
     "as the baseline, saves the bundle and then serves predictions as arg-max of the decision function with probabilities from Platt scaling."),
    ("feat", "Feature pipeline", "11_feature_pipeline.png",
     "Feature pipeline: the shape of one article's representation after each stage.",
     f"One article becomes a vector of up to 4,000 TF-IDF values (unigrams and bigrams, sublinear term frequency, minimum document frequency 2, maximum 0.9) joined to 25 stylometric values, 4,025 numbers in all. "
     f"Standardisation gives each column zero mean and unit variance. PCA then keeps as many components as are needed for 95 % of the variance, but never more than 300; the Firefly mask keeps a subset of those; and the RBF multi-class SVM "
     f"decides between the three classes. On the real LIAR2 training data the 300-component cap is reached every time and keeps only {F.pct(_A['pca_variance']['mean'])} of the variance; on the synthetic demo corpus 95 % is reached with {_D['n_pca']} components."),
    ("retrain", "Sequence diagram: retraining", "12_retrain_sequence.png",
     "Sequence diagram of retraining: upload, background job, polling and hot swap.",
     "The user attaches a CSV, sets the sliders and confirms (1). The page posts the multipart form to `/api/retrain` (2); the backend validates the ranges and the file, parses it, registers the job and starts a daemon thread (3) "
     "and answers at once with status 202 and the job id (4). The thread fits a new pipeline (5). Meanwhile the page polls `/api/retrain/{job_id}` every two seconds (6-7); the job id is also kept in the browser's local storage so that a page reload can resume the polling. "
     "When fitting ends (8) the thread saves the bundle to a `.tmp` file and renames it over the model file (9), swaps the in-memory pipeline under the lock and marks the job done (10); the next poll returns the accuracy and macro-F1 (11-12) "
     "and the page shows the success card and refreshes the analytics (13). If training fails the job is marked as an error and the previous model stays in use."),
]
_DG = {k: (t, f, c, x) for k, t, f, c, x in DIAGRAMS}


def _fig(key, width=5.6):
    t, f, c, x = _DG[key]
    return FIG(F.diag(f), c, width)


def _lat():
    return F.LAT[0]


def blocks():
    l = _lat()
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter describes how the detector is organised: its goals, architecture, data flow, main classes, stored data, core algorithm, modules and user interface. "
          "Every diagram was generated from the real code (`backend/main.py`, `src/` and `frontend/src/`)."),

        H2("5.1 Design Goals"),
        B("**One pipeline, one file.** Vectoriser, scaler, PCA, mask, C, gamma and classifier are fitted and saved together, so training and prediction cannot disagree.",
          "**A thin web layer.** The API holds no model logic; it calls the library that the command-line scripts and the Streamlit application also use.",
          "**Three honest verdicts** with the probability of every class and the cue words noticed.",
          "**Runs on a student laptop:** CPU only, open-source packages, no data leaving the machine.",
          "**Retrainable without restarting,** and **measured, not promised:** the analytics screen reads every number from the loaded model and shows the baseline beside it."),

        H2("5.2 System Architecture"),
        _fig("arch", 5.2),
        P("There are three tiers over two stores. The presentation tier is a React 18 and TypeScript application (Vite, Tailwind CSS, port 5406) with six screens and an axios client for `/api`. "
          "The application tier is a FastAPI service (`backend/main.py`, port 8406) with eight endpoints, one pipeline held in memory behind a re-entrant lock, and a background thread for retraining. "
          "The domain tier is the library `src/` on scikit-learn. The stores are the joblib bundle `models/msvm_model.pkl` and the temporary file that holds an uploaded CSV while it is parsed. "
          "There is no SQL database and no user account. The Vite server proxies `/api` to port 8406 and the API also allows the two local origins on port 5406; both ports are set in `.env`."),

        H2("5.3 High-Level Workflow"),
        _fig("flow", 5.2),
        P("The training path cleans labelled text, builds TF-IDF and 25 stylometric features, standardises and reduces them with PCA, splits 80/20, lets the Firefly algorithm choose a subset of components with C and gamma, "
          "fits the RBF multi-class SVM with balanced class weights, evaluates and saves the bundle. The inference path applies the same fitted objects, keeps the selected components and asks the SVM for a class and probabilities."),

        H2("5.4 Data Flow Diagrams"),
        _fig("dfd0", 4.8),
        P("**Level 0.** The reader or analyst sends article text or a CSV and receives verdicts and results; the model owner sends a retrain request and receives accuracy, macro-F1 and statistics; a labelled CSV supplies training rows."),
        _fig("dfd1", 4.8),
        P("**Level 1.** Four processes: 1.0 Detect single article, 2.0 Batch detect CSV (both read the model bundle D1), 3.0 Train / retrain model (reads the temporary labelled CSV D2, writes D1) and 4.0 Report model statistics (reads the statistics inside D1)."),
        _fig("dfd2", 4.8),
        P("**Level 2.** Process 3.0 follows `fit`: 3.1 validate and load labels, 3.2 clean and featurise (4,025 columns), 3.3 standardise and PCA, 3.4 stratified 80/20 split, 3.5 Firefly search, 3.6 fit the final SVM and evaluate, "
          "3.7 save the bundle, swap the in-memory pipeline under the lock and report the accuracy and macro-F1 as job status."),

        H2("5.5 UML Diagrams"),
        _fig("uml", 4.6),
        P("**Class diagram.** `backend.main` holds `_pipe`, `_lock` and `_jobs` and calls `get_pipe()`, which returns the one `FakeNewsMSVMPipeline`. The pipeline owns one `FireflyOptimizer`, composes the four scikit-learn parts and uses the `preprocessing` module; "
          "the backend uses the `dataset` module. The optimiser is needed only while fitting; at prediction time only its best mask, C and gamma are kept."),
        _fig("seq", 4.5),
        P(f"**Sequence: one detection.** The page posts `{{title, text}}` to `/api/predict`; the backend rejects fewer than five words (422), asks the pipeline to predict, which cleans, featurises, scales, projects, masks and queries the SVM; "
          f"the backend adds the confidence (largest probability), latency and cue words. Measured on the development machine: {l['predict_server_ms']['mean']:.1f} ms mean inside the server and a median of {l['predict_client_ms']['p50']:.1f} ms for the HTTP round trip."),
        _fig("retrain", 4.5),
        P("**Sequence: retraining.** `/api/retrain` validates the request, starts a daemon thread and answers 202 with a job id; the page polls every two seconds (the id is kept in local storage so a reload resumes). "
          "The thread fits a new pipeline, saves it to a `.tmp` file, renames it over the model file, swaps the in-memory pipeline under the lock and marks the job done. On failure the previous model stays in use."),
        _fig("uc", 4.4),
        P("**Use cases.** The reader checks one article (UC1, including cues and probabilities UC2), checks a CSV (UC3, with download UC4), views analytics (UC5) and reads how it works (UC7); the model owner retrains (UC6) and views analytics. There is no login."),

        H2("5.6 Data Design"),
        _fig("er", 5.0),
        P("The product has no SQL database because it keeps no records; the diagram shows the file and in-memory data model. A TrainingCSV feeds at most one RetrainJob (in memory, 12-character id); a finished job replaces the single ModelBundle, "
          "which contains its ModelStats; one bundle produces many Predictions and BatchResults, which are never stored."),
        TAB("Persistent and transient data", ["Item", "Where", "Lifetime and content"], [
            ["Model bundle", "`models/msvm_model.pkl` (joblib dictionary)", "Until the next retrain: vectorizer, scaler, pca, optimizer_mask, best_C, best_gamma, clf, stats, params"],
            ["Model statistics", "Inside the bundle", "n_docs, feature counts, n_pca, pca_variance, n_selected, firefly_history, accuracy, f1_macro, report, confusion_matrix, baseline scores, training time; y_test and y_pred are removed by `/api/model`"],
            ["Retrain job", "`_jobs` in the API process", "Until restart: status, times, source, settings, result or error"],
            ["Uploaded CSV", "Temporary file", "Deleted once parsed; text (or title + text, statement, news, content) and label"],
        ], widths=[1.2, 1.8, 3.3], size=9.5, align=["l", "l", "l"]),
        P(f"Two bundles exist: the shipped demo bundle (0.81 MB, {_D['n_docs']} synthetic documents) and `models/liar2_msvm_model.pkl` (12.0 MB, trained on {F.NTRAIN:,} real statements). Labels in a CSV may be REAL, PARTIALLY TRUE, FAKE, the numbers 0, 1, 2, "
          "or LIAR names (true and mostly-true become REAL, half-true PARTIALLY TRUE, barely-true, false and pants-fire FAKE)."),

        H2("5.7 Algorithm Design"),
        _fig("feat", 5.8),
        P(f"One article becomes up to 4,000 TF-IDF values (1-2 grams, sublinear tf, min_df 2, max_df 0.9) joined to 25 stylometric values. After standardisation PCA keeps components for 95 % of the variance, capped at 300; the Firefly mask keeps a subset; the RBF SVM decides. "
          f"On real statements the cap is always reached and keeps only {F.pct(_A['pca_variance']['mean'])} of the variance; on the demo corpus 95 % needs {_D['n_pca']} components."),
        _fig("algo", 4.3),
        P("**Encoding.** A firefly has k + 2 entries: one logit per PCA component (kept when sigmoid exceeds 0.5; one is forced on if none is), log10 C in [-1, 3] and log10 gamma in [-4, 1]. **Fitness.** Mean macro-F1 of a three-fold stratified cross-validation of "
          "`SVC(rbf, class_weight='balanced')` on the masked data, minus 0.02 times the share of components kept; macro-F1 is used because FAKE is the largest class and accuracy would reward majority guessing. "
          "**Movement.** Attractiveness is beta0 exp(-gamma r^2 / length) with beta0 = gamma = 1; noise alpha starts at 0.2 and decays by 0.97 per generation; after each generation the dimmest firefly is replaced by the best vector plus noise. Ten fireflies and twelve generations are the defaults."),

        H2("5.8 Module Design"),
        TAB("Modules and their responsibilities", ["Module", "Lines", "Main contents"], [
            ["`src/preprocessing.py`", "91", "`clean_text`; `stylometric_features` (25 values: lengths, ratios of unique, stop, capitalised, long and short words, punctuation, digits, URLs, first person, superlatives and three lexicon scores); `LABELS`"],
            ["`src/dataset.py`", "110", "`load_csv` (file or folder; LIAR and ISOT layouts); `build_demo_dataset` (synthetic template corpus)"],
            ["`src/firefly.py`", "106", "`FireflyOptimizer`: `_decode`, `_fitness`, `optimize`"],
            ["`src/pipeline.py`", "181", "`FakeNewsMSVMPipeline`: `fit`, `transform`, `predict`, `save`, `load`; statistics and baseline"],
            ["`backend/main.py`", "339", "Eight endpoints, `get_pipe()`, `_cues()` (13 sensational and 8 credibility words), `_read_csv_upload()`, one validation handler; status codes 422, 400, 413, 409, 404"],
            ["`frontend/src/pages/`", "1,303", "Landing, Detect, Batch, Analytics, Retrain, About, NotFound; each a lazily loaded chunk"],
            ["`frontend/src/components`, `lib`", "-", "Aurora Glass kit (AppShell, Card, Button, Field, Slider, Table, FileDrop, Toast, charts, motion), `api.ts`, `queries.ts`, `verdict.ts`, `theme.tsx`"],
        ], widths=[1.6, 0.6, 4.1], size=9.5, align=["l", "c", "l"]),
        P("Server state is handled by TanStack Query: model information is cached for 60 seconds, the examples for the session, the API health is polled every 20 seconds and a retraining job every 2 seconds while it runs."),

        H2("5.9 User Interface Design"),
        P("The interface follows the Aurora Glass kit: translucent cards over a dark aurora background with a light theme remembered in the browser. The application screens share one shell: a collapsible sidebar (a drawer on narrow screens), "
          "a top bar with a live \"Model online\" indicator and the theme toggle. Colour is never the only signal: each verdict has its own icon and word, and every field has a label, hint and error sentence."),
        TAB("Screens", ["Route", "Screen", "Main elements"], [
            ["/", "Landing", "Hero with live demo verdict, technology strip, metric strip, how it works, feature cards"],
            ["/app", "Detect", "Headline and text fields (five words needed, Ctrl+Enter), examples, verdict badge, confidence bar, probability chart, cue lists"],
            ["/app/batch", "Batch check", "CSV drop zone, ten-row preview, column selector, summary cards, distribution chart, sortable table (first 50 rows), results download"],
            ["/app/analytics", "Model analytics", "Stat cards, what the optimisation did, confusion matrix, Firefly curve, classification report, baseline against proposed"],
            ["/app/retrain", "Retrain", "Optional labelled CSV, sliders (fireflies 4-20, generations 3-30, TF-IDF 1,000-8,000), confirm dialog, progress and success cards"],
            ["/app/about", "About", "Pipeline steps, output classes, loaded model read live, how to run"],
        ], widths=[0.9, 1.2, 4.2], size=9.5, align=["l", "l", "l"]),
        PAIR([(F.shot("11_liar2_detect_fake_input.png"), "Detect screen with a real LIAR2 test statement entered."),
              (F.shot("20_liar2_retrain.png"), "Retrain screen with a 600-row labelled CSV attached.")], 2.9),
        P("The results of each screen, produced by the model trained on real data, are shown and discussed in Chapter 8."),

        H2("5.10 Design Decisions and Their Consequences"),
        TAB("Design decisions", ["Decision", "Reason", "Consequence"], [
            ["Thin API over the library", "One code path for web, CLI and Streamlit", "A fix in `src/` reaches all front ends"],
            ["One model in memory behind a lock", f"Prediction costs {l['predict_server_ms']['mean']:.1f} ms; loading takes seconds", "Retraining swaps the object under the lock"],
            ["Everything in one joblib file", "Keeps fitted parts consistent", "12.0 MB real-data bundle; needs the scikit-learn version that wrote it (1.9)"],
            ["Retraining as a polled background thread", "Training takes minutes; browsers time out", "Job state is lost on restart; the page then reports an unknown job"],
            ["Atomic replacement of the model file", "A failed run leaves the previous model usable", "Retraining overwrites the shipped model unless `FAKENEWS_MODEL` points elsewhere"],
            ["PCA capped at 300 components", "Bounds search space and SVM cost", f"Only {F.pct(_A['pca_variance']['mean'])} of the variance is kept on real text"],
            ["Class weights and macro-F1 fitness", "Real data is unbalanced", "Accuracy falls below the majority-class rate (0.576) while macro-F1 rises"],
            ["`SVC(probability=True)` for probabilities", "Per-class probabilities with no extra code", f"Verdict and largest probability disagree on {F.pct(F.LV['disagree_rate'])} of real test statements (found in testing)"],
            ["No login or database", "Local single-user tool; privacy by default", "No audit trail; anyone who can reach the port can retrain"],
            ["Results CSV returned in the batch response", "Simple, nothing stored", f"Limit 20,000 rows and 25 MB; {l['batch']['2296']['rows']:,} rows took {l['batch']['2296']['server_s']} s"],
        ], widths=[1.9, 2.1, 2.3], size=9, align=["l", "l", "l"]),
        P("The design favours a system that can be run, inspected and measured over a large one. The cost shows in the missing stemming step, the single-user assumption and the in-memory job table; none affects the correctness of a verdict, but each limits deployment."),
    ]
