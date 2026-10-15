"""Chapter 6 sections (Methodology and Software Implementation); also reused by the methodology document."""
from __future__ import annotations

import ast
from pathlib import Path

from doc_common import CHARTS, CV, DEMO, LAT, M, R, ROOT, SHOTS, V2, X, RF, LR, p

PG = ROOT / "phishguard"


def src(path, name):
    """Source text of a function or class from a Python file (so listings are always the real code)."""
    text = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name:
            return ast.get_source_segment(text, node)
    raise KeyError(name)


def sec_method_overview(d):
    d.h2("Overall Methodology")
    d.p("The methodology implements the three phases of the base paper [1] as one pipeline. Phase 1 turns a URL into numbers; phase 2 classifies; phase 3 "
        "collects community evidence and refines the classifier. The pipeline is used in two modes: an offline mode that prepares the models, and an online "
        "mode that answers requests and learns.")
    d.table([["Step", "Stage", "What happens", "Code"],
             ["1", "Data collection", "40,000 labelled URLs (20,000 phishing, 20,000 legitimate) are read from a CSV file", "data.load_dataset"],
             ["2", "Cleaning", "Missing values dropped, labels mapped to 0/1, URLs trimmed and de-duplicated", "data.load_dataset"],
             ["3", "Feature extraction", "Each URL becomes a vector of 47 lexical, structural and domain features", "features.featurize_urls"],
             ["4", "Split", "Stratified 80/20 split with a fixed seed: 32,000 train, 8,000 test", "data.build_matrices"],
             ["5", "Training", "Random Forest, XGBoost and Logistic Regression are fitted on the same training data", "train.train_all"],
             ["6", "Evaluation", "Accuracy, precision, recall, F1, ROC-AUC, FPR and confusion matrix on the test set", "train.evaluate"],
             ["7", "Selection", "The model with the highest F1 (ROC-AUC breaks ties) is saved as best_model.joblib", "train.train_all"],
             ["8", "Real-time check", "Community verdict first; otherwise model score with adjustments and thresholds", "detector.check"],
             ["9", "Crowd feedback", "Users report URLs; votes are counted; trusted feeds confirm immediately", "threat_intel.report"],
             ["10", "Refinement", "Confirmed URLs join the training data (x3) and all models are retrained; the detector reloads", "retrain.retrain"]],
            "End-to-end pipeline", widths=[0.07, 0.17, 0.56, 0.2], font=9.5)


def sec_dataset(d):
    ds = R["dataset"]
    d.h2("Dataset")
    d.p("The training data is `data/urls_sample.csv`, a balanced sample of 40,000 URLs taken from the public \"Using machine learning to detect "
        "malicious URLs\" dataset of about 420,000 labelled URLs [25]. The sampling is described in the code (`phishguard/data.py`); the original dataset's "
        "licence is not stated in the repository and was not verified, and the project does not redistribute anything beyond this sample. The full "
        "file can be fetched with `python run.py download`; it was not used or evaluated.")
    d.table([["Property", "Value"],
             ["Rows", f"{ds['rows']:,} ({ds['phishing']:,} phishing, {ds['legitimate']:,} legitimate)"],
             ["Unique URLs", f"{ds['unique_urls']:,}"],
             ["URL length (characters)", f"mean {ds['length_mean']}, median {ds['length_median']:.0f}, maximum {ds['length_max']:,}"],
             ["Mean length by class", f"phishing {ds['length_mean_phishing']}, legitimate {ds['length_mean_legitimate']}"],
             ["URLs that contain a scheme", f"{ds['with_scheme']} of {ds['rows']:,} (the rest are scheme-less, e.g. host/path)"],
             ["File size", f"{ds['csv_bytes']:,} bytes"],
             ["Split", "80 % train (32,000) / 20 % test (8,000), stratified, random_state 42; test set 4,000 + 4,000"],
             ["Not used", "Page content, WHOIS, DNS, certificates, screenshots"]],
            "Dataset facts", widths=[0.3, 0.7], font=10)
    d.figure(CHARTS / "dataset_overview.png", "Class balance and URL length distribution of the training data", width=5.4)
    d.p("Two properties of the data matter later. The classes are balanced, so accuracy is meaningful and no resampling is needed. And most URLs have no "
        "scheme, so the extractor normalises each URL by prepending http:// before any feature is computed; the feature `has_https_in_path_or_host` "
        "therefore reflects the word \"https\" inside the host or path, not the scheme.")


FEATURE_GROUPS = [
    ("Lexical (23)", [
        ("url_length, host_length, path_length, query_length, fragment_length", "Lengths of the whole URL and of its parts"),
        ("num_dots, num_hyphens, num_underscores, num_slashes, num_equals, num_ampersands, num_percent", "Counts of separator and special characters"),
        ("num_digits, digit_ratio, letter_ratio", "Digits and letters in the URL and their share"),
        ("num_special_chars, has_at_symbol, has_encoded_chars", "Special characters, '@' (browsers ignore text before it), percent-encoding"),
        ("num_query_params", "Number of query parameters"),
        ("url_entropy", "Shannon entropy of the lower-cased URL"),
        ("suspicious_word_count", "Occurrences of 42 credential-related words (login, verify, secure, bank ...)"),
        ("longest_token_length", "Longest alphanumeric token"),
        ("has_https_in_path_or_host", "The word 'https' used inside the host or path")]),
    ("Structural (9)", [
        ("is_ip_host", "Host is an IP address (dotted, hexadecimal or decimal)"),
        ("has_port, nonstandard_port", "Explicit port; port other than 80 or 443"),
        ("num_subdomains", "Number of sub-domain labels"),
        ("path_depth, has_double_slash_in_path", "Path segments; '//' inside the path"),
        ("is_url_shortener", "Host is one of 20 known shorteners"),
        ("has_file_extension, has_executable_extension", "File extension in the path; .exe, .apk, .zip and similar")]),
    ("Domain (15)", [
        ("domain_length, domain_digit_count, domain_hyphen_count", "Registered-domain length, digits and hyphens"),
        ("domain_entropy, domain_vowel_ratio, domain_max_consonant_run", "Randomness of the domain name (generated names look unpronounceable)"),
        ("tld_length, is_suspicious_tld, is_common_tld", "Top-level domain length; in a list of 41 abused TLDs; in com/org/net/edu/gov/mil/int"),
        ("brand_in_domain, brand_outside_domain", "A well-known brand name in the registered domain, or in the sub-domain, path or query"),
        ("subdomain_length, subdomain_has_digit, tld_in_subdomain", "Sub-domain length and digits; a 'com' or 'net' token inside the sub-domain"),
        ("is_popular_domain", "Registered domain is in a built-in list of 145 popular sites (domain reputation)")]),
]


def sec_preprocessing(d):
    d.h2("Data Preprocessing and Feature Extraction")
    d.h3("Cleaning")
    d.p("`load_dataset` reads the CSV, skips malformed lines, drops rows with a missing URL or label, maps text labels (bad, phishing, malicious to 1; "
        "good, benign, legitimate to 0), trims whitespace, removes URLs shorter than four characters and drops duplicate URLs. No imputation or "
        "scaling is applied to the data; Logistic Regression receives a StandardScaler inside its pipeline.")
    d.h3("Normalisation")
    d.p("`normalize_url` makes the extraction deterministic: it trims the string, replaces spaces by %20, adds http:// when no scheme is present, "
        "lower-cases the scheme and host, strips a leading www., and keeps the port, credentials, path, query and fragment. A malformed port or "
        "an unmatched bracket never raises: the splitter falls back to a cleaned form, and as a last resort to a placeholder host. This is why 17 "
        "validation checks, including a malformed port and a 5,000-character URL, all return a normal response.")
    d.h3("The 47 features")
    d.p("Features are computed from the URL string alone and are grouped as the project objectives describe: lexical features describe the "
        "characters, structural features describe how the URL is built, and domain features describe the registered domain and its top-level domain. "
        "Nothing needs the network.")
    for g, rows in FEATURE_GROUPS:
        d.table([["Features", "Meaning"]] + [[a, b] for a, b in rows], f"{g} features", widths=[0.5, 0.5], font=9)
    d.h3("Red flags")
    d.p("`explain_features` turns the numbers into at most 16 plain sentences, for example \"Host is a raw IP address instead of a domain name\", "
        "\"Registered domain imitates a well-known brand but is not the official site\" or \"Top-level domain is frequently abused by phishing "
        "campaigns\". The red flags are shown beside every verdict.")


def sec_algorithm_choice(d):
    d.h2("Algorithm Choice and Justification")
    d.p("Three classifiers were chosen because the project objectives name them, they cover three model families, and all train in seconds on the "
        "feature matrix.")
    d.table([["Model", "Family", "Why it was included", "Settings (phishguard/train.py)"],
             ["Logistic Regression", "Linear", "Interpretable baseline; the base paper's related work uses it with mutual-information features [6]", "StandardScaler + LogisticRegression, C 1.0, max_iter 2000, class_weight balanced"],
             ["Random Forest [21]", "Bagged trees", "Robust to feature scale, gives importances, strong on tabular data", "300 trees, unlimited depth, class_weight balanced, n_jobs -1, random_state 42"],
             ["XGBoost [22]", "Boosted trees", "Usually the strongest tabular learner; fast", "400 trees, max_depth 8, learning rate 0.08, subsample 0.9, colsample 0.9, logloss, random_state 42"]],
            "Classifiers and settings", widths=[0.16, 0.12, 0.34, 0.38], font=9)
    d.p("The deployed model is the one with the highest F1 on the test set; ROC-AUC breaks a tie. In the shipped run this is XGBoost "
        f"(F1 {p(X['f1'])}), followed closely by Random Forest ({p(RF['f1'])}); Logistic Regression is clearly behind ({p(LR['f1'])}), which shows that a "
        "linear boundary over these features is not enough. The deep LSTM-attention network of the base paper was not reproduced: it needs the "
        "URL text and page features of a much larger dataset, and tree ensembles on engineered features are lighter, train in seconds and "
        "can explain their decisions.")
    d.p("No hyper-parameter search was run. The settings are common defaults, chosen once; the 5-fold cross-validation below shows that the "
        "results are stable, but a tuned model could score higher.")


def sec_math(d):
    d.h2("Mathematical Formulation")
    d.p("**Shannon entropy** of a string s with character frequencies p(c), used for url_entropy and domain_entropy [24]:")
    d.p("H(s) = - sum over characters c of p(c) log2 p(c)", align="center", italic=True)
    d.p("**Logistic regression** models the phishing probability of a feature vector x as P(y = 1 | x) = 1 / (1 + exp(-(w.x + b))), with the weights w "
        "fitted by regularised maximum likelihood (C = 1.0). **Random Forest** averages the class probabilities of 300 decision trees grown on bootstrap "
        "samples [21]. **XGBoost** adds 400 regression trees, each fitted to the gradient of the logistic loss, with a learning rate of 0.08 [22]; the "
        "probability is the logistic function of the summed tree outputs.")
    d.p("**Evaluation metrics**, with TP, TN, FP and FN counted on the 8,000 test URLs:")
    d.p("accuracy = (TP + TN) / (TP + TN + FP + FN);   precision = TP / (TP + FP);   recall = TP / (TP + FN);   F1 = 2 x precision x recall / (precision + recall);   "
        "FPR = FP / (FP + TN).", align="center", italic=True)
    d.p("ROC-AUC is the area under the curve of recall against FPR as the probability threshold varies.")
    d.p("**Consensus rule.** For a URL with a phishing votes and b safe votes, let n = a - b. The status is confirmed_phishing if n >= 2 or if the report comes "
        "from a trusted feed; confirmed_safe if n <= -2; otherwise pending. The constant 2 is CONSENSUS_THRESHOLD.")
    d.p("**Decision rule.** With the model probability p, the reputation factor r = 0.4 if the registered domain is popular and its TLD is common or longer "
        "than two letters (otherwise 1), and the net pending votes n:")
    d.p("p' = clip(r x p + 0.15 x n, 0, 1);   verdict = phishing if p' >= 0.60, suspicious if p' >= 0.35, otherwise safe.", align="center", italic=True)
    d.p("When a confirmed entry exists, the verdict is fixed (phishing with probability max(0.97, p), or safe with min(0.03, p)). The "
        "reputation discount is applied only when no community verdict exists, and the vote nudge applies to unconfirmed entries.")
    d.p("**Retraining weights.** Each confirmed URL is repeated round(3.0) = 3 times in the training matrix, so it counts three times in the fit; "
        "base-data rows that the crowd has re-labelled are removed first.")


def sec_model_training(d):
    d.h2("Model Training and Evaluation")
    d.table([["Property", "Value"],
             ["Training rows / test rows", f"{M['train_rows']:,} / {M['test_rows']:,}"],
             ["Features", f"{M['n_features']}"],
             ["Model version / trained", f"{M['model_version']} / {M['trained_at']}"],
             ["Training time", f"Random Forest {RF['train_seconds']} s, XGBoost {X['train_seconds']} s, Logistic Regression {LR['train_seconds']} s"],
             ["Feature extraction for 40,000 URLs", f"{R['dataset']['featurize_seconds_40k']} s"],
             ["Saved files", "random_forest.joblib 165 MB, xgboost.joblib 2.5 MB, logistic_regression.joblib 2.8 KB, best_model.joblib 2.5 MB, metrics.json"]],
            "Training configuration and cost", widths=[0.3, 0.7], font=10)
    d.p("`train_all` fits each model, evaluates it on the test set, stores the metrics, the confusion matrix and the top-15 feature importances, "
        "and writes `models/metrics.json` with an incremented version number. The shipped numbers were reproduced for this report: re-scoring the saved "
        "Random Forest and XGBoost files on the same split gives exactly the values in metrics.json, and the logistic-regression file, which cannot be loaded "
        "under the installed scikit-learn, was refitted and matched as well.")
    d.p("The results of the evaluation are presented in Chapter 8. The retraining loop is described in the next sections.")


def sec_app_arch(d):
    d.h2("Application Architecture")
    d.p("The application is a Flask app created by `create_app(ti, detector)`. `backend/server.py` calls it unchanged, adds five read-only endpoints "
        "(/api/health, /api/config, /api/checks, /api/intel, /api/intel/lookup) and a CORS header, and serves on port 8103. The React frontend on "
        "port 5103 proxies /api and /retrain to it, so the browser makes only same-origin requests.")
    d.bullets(["**Concurrency.** Flask runs threaded. SQLite connections are opened per call. Model access is guarded by a lock, and a retrain lock "
               "makes a second concurrent retrain return \"a retrain is already running\".",
               "**Hot reload.** After a retrain, `Detector.reload()` loads best_model.joblib under the lock, so requests in flight use either the old or the new model, never a mix.",
               "**Background retraining.** The form route `/retrain` and automatic retraining start a daemon thread; `/api/retrain` is blocking. "
               "The interface polls /api/stats for the `retraining` flag every three seconds.",
               "**State on disk.** The community store, the model files and metrics.json are the only state; the application itself is stateless between requests."])


def sec_api(d):
    d.h2("API Design")
    d.table([["Method", "Path", "Request", "Response"],
             ["GET", "/api/check?url=", "query url", "verdict, probability, ml_probability, decided_by, reason, red_flags[], features{47}, model, model_version, community; 400 {error} for an empty URL"],
             ["POST", "/api/report", "JSON url, verdict, reporter, note", "the intel entry (votes, status, source, times); 400 for a bad verdict or URL"],
             ["GET", "/api/stats", "-", "threat_intel counters, metrics.json, retraining flag"],
             ["POST", "/api/retrain", "-", "blocking retrain; the new metrics summary"],
             ["POST", "/api/sync", "-", "per-feed result {ok, added} or {ok: false, error}"],
             ["GET", "/api/health", "-", "ok, model_ready, model, model_version"],
             ["GET", "/api/config", "-", "thresholds, consensus and retrain constants, feature names by group"],
             ["GET", "/api/checks?limit=", "limit (1-500)", "recent checks"],
             ["GET", "/api/intel?limit=&status=", "optional filters", "intel entries; 400 for an unknown status"],
             ["GET", "/api/intel/lookup?url=", "query url", "one entry with its last 10 reports; 400 for no URL"]],
            "JSON API (port 8103)", widths=[0.09, 0.24, 0.22, 0.45], font=9)
    d.p("An example response of `GET /api/check?url=http://secure-paypal-login.account-verify.tk/signin?user=a` (abridged):")
    d.code('{"verdict": "phishing", "probability": 0.9989, "decided_by": "ml", "model": "xgboost", "model_version": 1,\n'
           ' "reason": "Xgboost estimates a 99.9% phishing probability from 47 lexical, structural and domain features.",\n'
           ' "red_flags": ["Registered domain imitates a well-known brand but is not the official site", "..."],\n'
           ' "community": null, "features": {"url_length": 54, "suspicious_word_count": 4, "...": "..."}}', "Abridged JSON response")


def sec_walkthrough(d):
    d.h2("Key Code Walkthroughs")
    d.h3("Consensus: when does a URL become confirmed")
    d.p("The status machine is a small pure function. Two net phishing votes, or a trusted feed, confirm phishing; two net safe votes confirm legitimate; anything else stays pending.")
    d.code(src(PG / "threat_intel.py", "_consensus").replace("    @staticmethod\n", ""), "ThreatIntel._consensus")
    d.h3("Retraining: weighting and hot reload")
    d.p("Confirmed URLs replace any base-data rows they re-label, are repeated three times, and are split with the same stratified seed.")
    d.code("\n".join(src(PG / "retrain.py", "retrain").splitlines()[7:30]), "retrain.retrain (excerpt)")
    d.h3("Decision order in the detector")
    d.p("The decision order is the heart of the system: community first, then the model, then adjustments and thresholds (see the flowchart in Chapter 5).")
    code = src(PG / "detector.py", "check").splitlines()
    i0 = next(i for i, l in enumerate(code) if "# 1. crowdsourced intelligence" in l)
    d.code("\n".join(code[i0:i0 + 38]), "Detector.check (excerpt)")


def sec_security(d):
    d.h2("Security and Error Handling")
    d.bullets(["**The URL is never fetched.** The system only reads the string, so a malicious URL cannot execute anything or make the server contact it.",
               "**Parameterised SQL.** Every statement binds its values; a SQL-injection string in a URL or reporter name is stored as plain data (tested).",
               "**Output escaping.** The Flask pages use Jinja auto-escaping and React escapes by default; script tags in reported URLs, notes and names are not executed (tested).",
               "**Input validation.** An empty or whitespace-only URL, an unknown verdict and an unknown status each return HTTP 400 with a JSON error.",
               "**Bounded work.** Batch checks are limited to 100 URLs in the interface; feed synchronisation adds at most 500 URLs per feed and has a 20-second timeout.",
               "**Failure isolation.** A failing feed is reported per feed and never stops the application; the interface shows a clear message if the backend is unreachable.",
               "**Secrets.** The application needs none. The `.env` file holds only ports (and an unrelated API key that PhishGuard does not read).",
               "**Known weaknesses.** No authentication, CORS `*`, anonymous reports, no rate limit, and feed URLs accepted without verification. These are listed as limitations."])


def sec_install(d):
    d.h2("Installation and Execution")
    d.p("**Windows, one command.** From `8.ProjectCode`, `run.bat` trains the models if `models/best_model.joblib` is missing, installs the frontend "
        "dependencies on first run, opens the API (port 8103) and the interface (port 5103) in two windows and launches the browser.")
    d.code("pip install -r requirements.txt\n"
           "python run.py train               # under a minute: features + three models\n"
           "python backend/server.py          # API on http://127.0.0.1:8103\n"
           "cd frontend && npm install && npm run dev    # UI on http://localhost:5103", "Manual start")
    d.table([["Command", "Purpose"],
             ["python run.py train", "Train and compare the three models; write models/ and metrics.json"],
             ["python run.py check <url>", "Classify from the terminal"],
             ["python run.py report <url> phishing|safe --reporter NAME", "File a community report"],
             ["python run.py sync", "Import OpenPhish and URLhaus URLs (needs internet)"],
             ["python run.py retrain", "Retrain with confirmed URLs"],
             ["python run.py serve", "Original Flask interface on port 5000"],
             ["python run.py download", "Fetch the full dataset (not used in this report)"],
             ["python tests.py; python scripts/smoke_test.py; python scripts/extra_tests.py", "Run the automated checks"]],
            "Command-line interface", widths=[0.5, 0.5], font=9.5)
