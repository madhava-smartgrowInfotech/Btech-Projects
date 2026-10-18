"""Chapter 6 content: methodology and software implementation."""
from __future__ import annotations

import sys

from doc_common import (API, BEST, CHARTS, DEMO, DIAG, EV, LAT, MODELS, REP, ROOT, ROUTES_PROTECTED, ROUTES_PUBLIC, SEEDS, SIZE, f3)
from rc_design import diagram

sys.path.insert(0, str(ROOT))
from autosecai.metrics import METRICS  # noqa: E402


def src(path: str, start: int, end: int) -> str:
    """Real source lines (1-based, inclusive) from the project, so listings never drift from the code."""
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[start - 1:end])


def grab(path: str, marker: str, n: int) -> str:
    """`n` real source lines starting at the first line that contains `marker`."""
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    i = next(k for k, line in enumerate(lines) if marker in line)
    return "\n".join(lines[i:i + n])


def sec_method_overview(d):
    d.h2("Overall Methodology")
    d.paras(
        "AutoSecAI turns a code change into a reasoned review. The method has two parts. **Preparation** is done once, before the product is used: a "
        "labelled corpus of Python functions is generated, fourteen metrics are measured on it, features are selected, the classes are balanced, nine "
        "classifiers are trained and the best one is stored together with a report. **Use** happens for every pull request: the change is parsed, seven "
        "agents analyse it in sequence, and the result is a score, a verdict, explained findings and verified patches. A second use, the codebase "
        "assistant, indexes a repository and answers questions with cited locations.",
        "The central idea comes from the base paper [1], which showed that a small set of source-code metrics predicts which functions are vulnerable. The paper "
        "applies the idea offline to C and C++ functions. This project applies it inside the pull-request workflow and combines it with two other kinds of "
        "evidence: an abstract-syntax-tree analyser with taint tracking, which names the exact line and the weakness class, and a rule knowledge base, which "
        "supplies the explanation, impact and fix. Each kind of evidence is weak alone, and the combination is evaluated later in this document.")
    d.table([["Step", "Method", "Output"],
             ["1 Ingest", "Unified-diff parser, before/after diff, zip or folder reader, GitHub pull-request download", "List of changed files with hunks and added line numbers"],
             ["2 Static analysis", "Python AST, taint levels 0-3, 30 security rules, quality rules; regex rules for JavaScript, PHP and Java", "Findings with rule, line, confidence, optional fix"],
             ["3 ML risk", "14 metrics per function, Min-Max scaling, stored XGBoost model, type classifier", "Probability, predicted type and top drivers per function"],
             ["4 Reasoner", "Knowledge-base lookup, source-to-sink description, corroboration with the model", "Explanation, impact, remediation, CWE, OWASP"],
             ["5 Remediation", "Fix generators for SQL, shell and similar calls; apply to a copy; analyse again", "Patch and a verified flag"],
             ["6 Quality", "Complexity, nesting, size, error handling, dead imports", "Maintainability findings"],
             ["7 Judge", "De-duplication by file, line and CWE; weights; exponential score; verdict rule", "Score 0-100, verdict, PR comment"],
             ["8 Report", "Markdown, SARIF 2.1.0, JSON, CSV, patched files; SQLite history", "Exports and stored review"]],
            "Pipeline of AutoSecAI", widths=[0.16, 0.5, 0.34], font=9.5)
    d.p("The seven agents are ordinary Python functions that append an entry (agent, role, seconds, summary, details) to a shared trace; none is a "
        "language model. An optional language-model call can rewrite the explanation of the six most serious findings; it was not measured.")
    if not getattr(d, "report", False):
        diagram(d, "workflow")


def sec_dataset(d):
    d.h2("Dataset")
    d.paras(
        "The metric model needs labelled functions. The base paper used 21,759 C and C++ functions from ten open-source projects, of which only 275 "
        "(1.26 %) were vulnerable, labelled from public vulnerability databases [1]. Those datasets are written in C and C++, are not distributed with the "
        "paper, and cannot be analysed by a Python pull-request tool. For this reason the project **generates** its own corpus of Python functions. "
        "This is the most important limitation of the learned component, and every result in this document must be read with it in mind: the model "
        "has been shown to learn the patterns the generator contains, not the patterns of real-world vulnerable code.",
        f"The generator (`autosecai/dataset.py`) produces {REP['n_functions']:,} functions with a fixed seed. Each function starts as random benign logic "
        "whose complexity follows a heavy-tailed choice: it may contain no blocks at all or up to six, drawn from conditionals, loops, nested structures, "
        "try blocks, arithmetic, list comprehensions and index expressions. A vulnerable snippet of one of eight types is then inserted at a block "
        "boundary, so that the function stays syntactically valid. In 55 % of the non-vulnerable functions a look-alike safe snippet (a hard negative) is "
        "inserted instead: a parameterised query, a list-form subprocess call, `ast.literal_eval`, `json.loads`, `yaml.safe_load`, `os.path.basename`, an "
        "escaped HTML fragment, `hashlib.sha256`, `secrets.token_hex` or a password read from the environment. Half of the vulnerable snippets read their "
        "value directly from a request object, and half use a function parameter. Finally 1 % of the labels are flipped to imitate annotation noise.")
    rows = [["Vulnerability type", "Pattern inserted", "Functions in the corpus"]]
    patterns = {"xss": "HTML built from a value by f-string", "weak_crypto": "MD5 digest or predictable random value", "sql_injection": "query built by f-string, concatenation or %",
                "hardcoded_secret": "password literal passed to a connection", "deserialization": "pickle, yaml.load or marshal on input",
                "code_execution": "eval or exec on input", "path_traversal": "open, send_file or remove on an unchecked path", "command_injection": "os.system, os.popen or shell=True with input"}
    for k, v in REP["type_counts"].items():
        rows.append([k.replace("_", " "), patterns[k], str(v)])
    d.table(rows, "The eight vulnerability types of the generated corpus", widths=[0.25, 0.55, 0.2], font=9.5)
    d.table([["Property", "Value"],
             ["Functions", f"{REP['n_functions']:,} (seed 7)"],
             ["Vulnerable", f"{REP['n_vulnerable']} ({REP['class_ratio'] * 100:.2f} %), after 1 % label noise"],
             ["Split", f"75 % training ({REP['train_size']:,}) and 25 % test ({REP['test_size']:,}), stratified, seed 42"],
             ["Test set", "125 vulnerable and 1,375 safe functions, never balanced"],
             ["Balanced training set", f"{REP['balanced_train_size']:,} rows after SMOTE and {REP['tomek_removed']} Tomek removals"],
             ["Licence and provenance", "Generated by the project's own code; no third-party data and no licence restriction"]],
            "Dataset summary", widths=[0.3, 0.7], font=10)
    d.p("Two consequences follow. The analyser's rules and the generator were written by the same team around the same eight weakness classes, so the "
        "analyser's score on the corpus is optimistic for real code; and the headline model scores are an upper bound for production code, with no "
        "claim of equivalence with the base paper.")


def sec_preprocessing(d):
    d.h2("Data Preprocessing")
    d.h3("Metric extraction")
    d.p("Every function is parsed with Python's `ast` module and fourteen metrics are measured on it. The metrics are the Python counterparts of the "
        "metrics of the base paper [1], which derived them from a code property graph of C and C++ functions. The first eleven keep the families and the "
        "numbering of the paper (complexity, size, variables, calls, parameters, index arithmetic in place of pointer arithmetic, input and output calls, "
        "nesting, loops and control dependency). Metrics M12 to M14 were added by this project, because injection flaws in Python are not memory flaws and "
        "are better indicated by risky calls, string-built call arguments and untrusted sources.")
    rows = [["Id", "Metric", "Meaning", "Origin"]]
    for mid, key, name, meaning in METRICS:
        rows.append([mid, name, meaning, "added by this project" if mid in ("M12", "M13", "M14") else "paper family"])
    d.table(rows, "The fourteen source-code metrics", widths=[0.07, 0.24, 0.5, 0.19], font=9)
    d.h3("Scaling and balancing")
    d.p("Metric values have very different ranges (lines of code against a count of risky calls), so the selected metrics are scaled to the interval "
        "from 0 to 1 with Min-Max scaling fitted on the training data only. The training set is highly imbalanced, so the minority class is enlarged "
        "with SMOTE and the result is cleaned with Tomek links [15], [16], [17]. SMOTE draws a minority sample, picks one of its five nearest minority "
        "neighbours and creates a new sample on the line between them. A Tomek link is a pair of samples from different classes that are each other's "
        "nearest neighbour; the majority-class member of every such pair is removed. Both steps are implemented in the project (about thirty-five lines using "
        "scikit-learn's nearest-neighbour search), and they are applied to the training data only, so that the test set keeps its natural class ratio.")
    d.code(grab("autosecai/mlmodel.py", "def smote(", 18), "SMOTE as implemented in autosecai/mlmodel.py")


def sec_algorithm_choice(d):
    d.h2("Algorithm Choice and Justification")
    d.paras(
        "**Feature selection.** Following the base paper, seven methods rank the metrics: absolute Pearson correlation with the label, the coefficients of a "
        "linear support-vector machine, Lasso coefficients, the chi-squared statistic, recursive feature elimination with logistic regression, recursive "
        "feature elimination with a random forest, and the variance threshold. Each method votes for its five best metrics; the metrics are sorted by votes "
        "and, for ties, by mean rank. The paper keeps the top five. This project instead validated the number of metrics k from 5 to 14 on a quarter of "
        f"the training data and chose k = {REP['best_k']} (validation F1 {f3(REP['k_scores'][str(REP['best_k'])])}, against {f3(REP['k_scores']['5'])} for k = 5). The only metric "
        "dropped is the number of variables used in index arithmetic (M7), which received no vote.",
        "**Classifiers.** Nine classifiers were trained, as in the paper: random forest, decision tree, logistic regression, support-vector machine with an RBF "
        "kernel, k-nearest neighbours, naive Bayes, gradient boosting, XGBoost [19] and a soft-voting ensemble of random forest, gradient boosting and logistic "
        f"regression. The model with the best F1 on the held-out data, {BEST} (F1 {f3(MODELS[BEST]['f1'])}), is the one stored and used by the ML Risk agent; "
        f"the random forest (F1 {f3(MODELS['Random Forest']['f1'])}, the winner of the paper) is also kept for the importance chart. F1 was chosen as the "
        "selection criterion because accuracy is meaningless when 91.7 % of the functions are safe, and a security tool needs a balance between missed "
        "flaws and false alarms.",
        "**Why a rule engine as well.** A metric model can say that a function looks vulnerable, but not where, why or how to fix it. The AST and taint "
        "analyser tracks values from requests and parameters to dangerous calls, names the line and weakness class and can propose a patch. The two "
        "detectors fail differently (the measured comparison is given in the testing chapter), which is why the pipeline correlates both kinds of evidence.")
    rows = [["Metric", "Votes (of 7)", "Mean rank"]]
    order = REP["fs_order"]
    for k in sorted(order["votes"], key=lambda k: (-order["votes"][k], order["mean_rank"][k])):
        rows.append([k, str(order["votes"][k]), f"{order['mean_rank'][k]:.2f}"])
    d.table(rows, "Consensus of the seven feature-selection methods (training data)", widths=[0.5, 0.25, 0.25], font=9.5)


def sec_math(d):
    d.h2("Mathematical Formulation")
    d.p("This section states the formulas that the implementation uses. The notation is local to this document.")
    d.h3("Cyclomatic complexity (metric M1)")
    d.p("Following McCabe [21], the complexity of a function is one plus the number of decision points: each `if`, conditional expression, `while`, `for`, "
        "exception handler and assertion adds one; each comprehension adds one plus the number of its filters; a boolean expression with n operands adds "
        "n - 1; each `match` case adds one.")
    d.h3("SMOTE and Tomek links")
    d.p("For a minority sample x_i and one of its k = 5 nearest minority neighbours x_nn, a synthetic sample is x_new = x_i + u (x_nn - x_i), where u is drawn "
        "uniformly from [0, 1) [15]. The number of samples created is the difference between the sizes of the majority and the minority class. A pair (x_a, "
        "x_b) is a Tomek link if their classes differ and each is the other's nearest neighbour [16]; the majority member of the pair is deleted [17].")
    d.h3("Evaluation measures")
    d.p("With TP, FP, FN and TN as the cells of the confusion matrix, precision P = TP / (TP + FP), recall R = TP / (TP + FN), accuracy = (TP + TN) / (TP + FP + "
        "FN + TN) and F1 = 2 P R / (P + R). The area under the ROC curve (AUC) is the probability that a random vulnerable function receives a higher score than a "
        "random safe one.")
    d.h3("Risk score and verdict")
    d.p("Let the visible findings be f_1 ... f_n. Each has a severity weight s (critical 10, high 6, medium 3, low 1, info 0.2) and a confidence weight c (high "
        "1.0, medium 0.7, low 0.4). Info-level quality findings are skipped. A finding outside the changed lines counts only 15 % of its weight. With w_i = s_i "
        "c_i m_i, where m_i is 1 inside the diff and 0.15 outside, the total is W = sum of w_i and the risk score is")
    d.p("**score = round( 100 x (1 - exp(-W / 18)) )**", align="center")
    d.p("The exponential form maps any amount of evidence onto 0-100 with diminishing returns: one medium-severity finding of medium confidence gives a score of 11, and the demo pull "
        f"request, whose total weight is large, gives {DEMO['score']}. The verdict is BLOCK if at least one security finding of high or critical severity with at "
        "least medium confidence lies in the changed lines, or if the score is 70 or more; REQUEST_CHANGES if a finding of medium or higher severity lies in the "
        "changed lines, or the score is 30 or more; and APPROVE otherwise.")
    d.h3("Retrieval in the codebase assistant")
    d.p("Each function, class or window of a source file is a chunk. Names are split at underscores and capital letters, and chunks are represented by TF-IDF "
        "vectors over unigrams and bigrams with sublinear term frequency [22]. For a question q the score of chunk c is")
    d.p("**score(c) = cos(q, c) + 0.30 x max concept affinity(c) / 2 + 0.5 [name(c) = identifier in q] + 0.1 [path(c) contains a long token of q]**", align="center")
    d.p("then multiplied by 1.15 for function chunks and 1.05 for class chunks. The affinity of a chunk to each of eight concepts (authentication, routing, user "
        "interface, database, configuration, tests, security controls, entry points) is computed from keyword counts in the code and from matches in the path, capped at 2. For the five "
        "strongest chunks a personalised PageRank [23] is run on the import and call graph with damping 0.6 and the scores as the personalisation vector; "
        "its normalised value times 0.08 is added to every chunk. Chunks with a final score of at most 0.02 are discarded and the top k (default 6) are returned.")


def sec_model_training(d):
    d.h2("Model Architecture and Training")
    d.p(f"Training is a single function, `train_all()`, which takes {REP['seconds']} s on the development machine (Intel Core i5-12500, 12 threads, no GPU). It "
        "generates the corpus, splits it, selects features on the training part, balances it, fits the nine classifiers, evaluates them on the untouched test part, "
        "runs the ablation, trains the type classifier and writes the model bundle, the report and two CSV files. All random choices use fixed seeds. The "
        "hyper-parameters were not tuned with a grid search (the paper used one [1]); they are library defaults except where listed.")
    d.table([["Model", "Configuration"],
             ["Random forest", "300 trees, seed 42"],
             ["Decision tree", "maximum depth 12"],
             ["Logistic regression", "up to 2,000 iterations"],
             ["SVM", "RBF kernel, probability estimates on"],
             ["k-nearest neighbours", "k = 7"],
             ["Naive Bayes", "Gaussian"],
             ["Gradient boosting", "library defaults, seed 42"],
             ["XGBoost", "200 trees, depth 5, learning rate 0.1, log-loss"],
             ["Voting ensemble", "soft vote of random forest (200 trees), gradient boosting and logistic regression"],
             ["Type classifier", "random forest, 400 trees, class-balanced, 14 metrics, trained on the vulnerable functions only"]],
            "Model configuration", widths=[0.28, 0.72], font=9.5)
    rows = [["Model", "Accuracy", "Precision", "Recall", "F1", "AUC"]]
    for n, m in MODELS.items():
        rows.append([n + (" (stored)" if n == BEST else ""), f3(m["accuracy"]), f3(m["precision"]), f3(m["recall"]), f3(m["f1"]), f3(m["auc"])])
    d.table(rows, "Results of the nine classifiers on the 1,500 held-out functions", widths=[0.28, 0.14, 0.14, 0.14, 0.15, 0.15], font=9.5)
    if not getattr(d, "report", False):  # repeated in another chapter of the full report
        d.figure(CHARTS / "models_prf.png", "Precision, recall and F1 of the nine classifiers", width=5.4, max_h=3.0)
    d.p(f"{BEST} gave the best F1 ({f3(MODELS[BEST]['f1'])}) through the highest precision ({f3(MODELS[BEST]['precision'])}), at the same recall as the "
        f"random forest ({f3(MODELS[BEST]['recall'])}). Logistic regression and naive Bayes had the highest recall (0.920) but a precision near 0.40, which "
        "would flood a reviewer with false alarms.")
    if not getattr(d, "report", False):  # repeated in another chapter of the full report
        d.figure_pair([(CHARTS / "roc.png", "ROC curves of the nine models"), (CHARTS / "confusion.png", "Confusion matrices of XGBoost and Random Forest")], width=3.2, max_h=3.0)
    d.h3("Ablation, feature count and stability")
    ab = REP["ablation"]
    rows = [["Random-forest configuration", "Precision", "Recall", "F1"]] + [[k, f3(v["precision"]), f3(v["recall"]), f3(v["f1"])] for k, v in ab.items()]
    d.table(rows, "Ablation of the random forest", widths=[0.58, 0.14, 0.14, 0.14], font=9.5)
    d.p("All fourteen metrics without balancing gave the best F1 (0.847); the paper's top-five setting with SMOTE-Tomek gave only 0.645; the system's "
        "setting (top 13 with balancing) gave 0.826. Recall is the same (0.776) with and without balancing and balancing lowered precision, so on this "
        "corpus it did not help; but the configurations differ in the number of metrics as well, so the effects cannot be separated and no single-factor "
        "experiment was run. The sweep shows that the taint-oriented metrics matter: five metrics lower the validation F1 from 0.786 to 0.566.")
    if not getattr(d, "report", False):  # repeated in another chapter of the full report
        d.figure_pair([(CHARTS / "k_sweep.png", "Validation F1 against the number of metrics kept"), (CHARTS / "ablation.png", "Ablation of the random forest")], width=3.2, max_h=2.8)
    d.p("To check that the result is not an accident of one random corpus, the Random Forest and XGBoost pipelines were repeated on five corpora generated with "
        "different seeds (k fixed at 13, same split rule). The first seed reproduces the stored report exactly.")
    rows = [["Corpus seed", "Vulnerable", "RF F1", "RF precision", "RF recall", "XGB F1", "XGB precision", "XGB recall"]]
    for r in SEEDS["runs"]:
        rows.append([str(r["seed"]), str(r["positives"]), f3(r["Random Forest"]["f1"]), f3(r["Random Forest"]["precision"]), f3(r["Random Forest"]["recall"]),
                     f3(r["XGBoost"]["f1"]), f3(r["XGBoost"]["precision"]), f3(r["XGBoost"]["recall"])])
    s = SEEDS["summary"]
    rows.append(["**Mean +/- sd**", "", f"{s['Random Forest|f1']['mean']:.3f} +/- {s['Random Forest|f1']['sd']:.3f}", "", "",
                 f"{s['XGBoost|f1']['mean']:.3f} +/- {s['XGBoost|f1']['sd']:.3f}", "", ""])
    d.table(rows, "Five independently generated corpora", widths=[0.12, 0.11, 0.1, 0.13, 0.11, 0.1, 0.13, 0.1], font=8.5, align=["l"] + ["c"] * 7)
    d.p(f"The headline F1 of {f3(MODELS[BEST]['f1'])} for {BEST} is the best of the five seeds; the mean is {s['XGBoost|f1']['mean']:.3f} with a standard "
        f"deviation of {s['XGBoost|f1']['sd']:.3f}. For the random forest the headline {f3(MODELS['Random Forest']['f1'])} is also the best seed (mean "
        f"{s['Random Forest|f1']['mean']:.3f} +/- {s['Random Forest|f1']['sd']:.3f}). XGBoost ranks above the random forest on all five seeds, which "
        "supports the stored choice. The number of metrics was not re-selected per seed.")
    if not getattr(d, "report", False):  # repeated in another chapter of the full report
        d.figure_pair([(CHARTS / "importance.png", "Random-forest importance of the selected metrics"), (CHARTS / "type_f1.png", "F1 of the vulnerability-type classifier")], width=3.2, max_h=2.8)
    d.p(f"Risky API calls, untrusted sources and string-built sinks carry about 46 % of the importance; the paper's complexity metrics matter less for "
        f"these injection-type flaws. The type classifier reaches an accuracy of {f3(REP['type_accuracy'])} on 126 functions (macro F1 "
        f"{f3(REP['type_report']['macro avg']['f1-score'])}): reliable for SQL injection, XSS, command injection, weak cryptography and hard-coded "
        "secrets (F1 0.77 to 0.88), unreliable for deserialization (0.21), path traversal (0.33) and code execution (0.38).")


def sec_app_arch(d):
    d.h2("Application Architecture")
    d.paras(
        "The application has three tiers. The **web tier** is a single-page React application written in TypeScript and bundled with Vite. Pages are loaded "
        "lazily by route, server state is cached by TanStack Query, and an axios instance adds the bearer token to every request and redirects to the sign-in page "
        "on a 401. Long operations use a hook that starts a job, polls it every 350 ms and shows the agents' messages as they arrive. User settings (minimum "
        "severity, ML agent on or off, optional keys) live in the browser's local storage and are sent with each request; the server never stores them.",
        "The **API tier** is a FastAPI application. Routes validate their input with Pydantic models, call the engine functions unchanged and return JSON; "
        "a helper replaces non-finite floating-point numbers, which JSON cannot carry. Reviews and the retraining run as jobs: `start_job` creates a record in the "
        "in-memory job table, runs the work in a daemon thread and stores either the result or a readable error. Repository indexes are kept in an ordered "
        "dictionary limited to six entries. The **engine tier** is the Python package; it has no knowledge of HTTP.",
        "The trained model is loaded lazily and cached; if the artefacts are missing the first call trains them "
        f"(about {REP['seconds']:.0f} s), and the Model Lab can retrain on request as a job.")


def sec_walkthrough(d):
    d.h2("Key Code Walkthroughs")
    d.h3("Taint levels in the static analyser")
    d.p("The analyser assigns each expression a taint level: 0 for constants and sanitised values, 1 for a value built by string formatting, 2 for a value derived "
        "from a function parameter, and 3 for a value read from a request, the command line or standard input. The level of a compound expression is the highest "
        "level of its parts, and a call to a known sanitiser resets the level to 0. A sink such as `cursor.execute` is reported when its argument is string-built "
        "or its level is at least 2, and the confidence is high for level 3, medium for level 2 and low otherwise.")
    if not getattr(d, "report", False):  # repeated in another chapter of the full report
        d.code(grab("autosecai/rules.py", "def _level_of", 22), "Taint level of an expression (autosecai/rules.py)")
    d.h3("Verified fixes")
    d.p("A fix is a replacement of a source segment with a start position, an end position and new text. For SQL calls built by string formatting, the fixer "
        "flattens the expression into literal parts and embedded expressions, replaces each expression by a placeholder, and returns the same call with the "
        "values as a parameter tuple. The remediation agent applies the fix to a copy of the source, re-runs the analyser and keeps the patch only if a "
        "finding of the same rule no longer appears within one line of the original. On the demo pull request all seven generated patches passed this check.")
    if not getattr(d, "report", False):  # repeated in another chapter of the full report
        d.code(grab("autosecai/rules.py", "def sql_parametrize", 16), "Rewriting a string-built SQL call into a parameterised one (autosecai/rules.py)")
    d.h3("Risk score and verdict")
    if not getattr(d, "report", False):  # repeated in another chapter of the full report
        d.code(grab("autosecai/agents.py", "floor = SEVERITY_ORDER[min_severity]", 22), "Scoring and verdict in the judge step (autosecai/agents.py)")
    d.h3("Background jobs")
    d.p("The job runner is deliberately small. A new job removes jobs older than one hour, registers a record and starts a daemon thread. The thread's "
        "exceptions are converted into a message, so the interface always receives either a result or a reason.")
    if not getattr(d, "report", False):  # repeated in another chapter of the full report
        d.code(grab("backend/main.py", "def start_job", 22), "Background job runner (backend/main.py)")


API_ROWS = [
    ["GET", "/api/health", "public", "Liveness and version"],
    ["GET", "/api/public/stats", "public", "Model statistics from the stored report, for the landing page"],
    ["GET", "/api/public/rules", "public", "Titles of the security weakness classes in the knowledge base"],
    ["GET", "/api/public/example", "public", "One real finding from the demo pull request (computed once, not saved)"],
    ["POST", "/api/auth/login", "public", "E-mail and password to token and user; 401 on a wrong password"],
    ["POST", "/api/auth/register", "public", "Create an account (201); 409 for a duplicate, 422 for invalid input"],
    ["GET", "/api/auth/demo", "public", "The seeded demo credentials"],
    ["GET", "/api/auth/me", "JWT", "The signed-in user"],
    ["GET", "/api/meta", "JWT", "Version, severities, the seven agents, the 14 metrics with safe-function means, suggested questions"],
    ["GET", "/api/samples", "JWT", "Demo diff, before and after versions, demo repository file list"],
    ["POST", "/api/reviews", "JWT", "Start a review (kinds demo-diff, demo-versions, diff, versions, github, folder); 202 with a job id"],
    ["POST", "/api/reviews/upload", "JWT", "Start a review from uploaded files or zips (multipart); 202"],
    ["GET", "/api/jobs/{id}", "JWT", "Status, live messages, result or error of a job"],
    ["GET", "/api/reviews", "JWT", "List stored reviews (limit 1-500)"],
    ["GET", "/api/reviews/{id}", "JWT", "One complete review; 404 if it does not exist"],
    ["DELETE", "/api/reviews/{id}", "JWT", "Delete a review"],
    ["GET", "/api/reviews/{id}/export/{fmt}", "JWT", "Download md, sarif, json or csv"],
    ["GET", "/api/reviews/{id}/patched", "JWT", "Download one automatically fixed file (full-file input only)"],
    ["POST", "/api/codebase/index", "JWT", "Index the demo shop, this project, a folder or a GitHub repository"],
    ["POST", "/api/codebase/index/upload", "JWT", "Index uploaded zips"],
    ["GET", "/api/codebase/{id}", "JWT", "Overview, onboarding guide and graph of a loaded index"],
    ["POST", "/api/codebase/{id}/ask", "JWT", "Answer a question with cited locations (k limited to 1-12)"],
    ["GET", "/api/lab/report", "JWT", "The stored model report"],
    ["POST", "/api/lab/analyze", "JWT", "Metrics, probability, type and security findings for pasted code"],
    ["POST", "/api/lab/retrain", "JWT", "Retrain all models as a job; 202"],
]


def sec_api(d):
    d.h2("API Design")
    d.p(f"The API has {len(API_ROWS)} route handlers: {ROUTES_PUBLIC} public and {ROUTES_PROTECTED} that require a bearer token. Paths are grouped by resource under "
        "`/api`, request bodies are JSON (except uploads, which are multipart), and errors have the shape `{\"detail\": \"...\"}` with a readable message. A review is "
        "created by an asynchronous call that answers `202` with a job identifier, because it can take longer than a request should; all other calls are "
        "synchronous. The interactive documentation of FastAPI is available at `/docs` on port 8311.")
    d.table([["Method", "Path", "Access", "Purpose"]] + API_ROWS, "HTTP endpoints of AutoSecAI", widths=[0.1, 0.3, 0.09, 0.51], font=8.5)


def sec_security(d):
    d.h2("Security and Error Handling")
    d.paras(
        "**Authentication.** Passwords are hashed with bcrypt [28] (10 rounds, input limited to 72 bytes) and never stored or logged. A successful login returns "
        "a JSON Web Token [27] signed with HS256, valid for 12 hours; the signing key is the SHA-256 digest of the `JWT_SECRET` setting so that its length is always "
        "sufficient. Every route except the public ones depends on a function that validates the token and loads the user, and answers 401 with a specific "
        "message for a missing, expired or invalid token or a deleted account. Registration checks the name (two characters), the e-mail format and the "
        "password length (eight characters) and answers 409 for a duplicate address.",
        "**Input handling.** Request bodies are validated by Pydantic models; invalid combinations (an empty diff, a folder that does not exist, a diff without "
        "files) answer 422 with an actionable message. A review is limited to 300 files; zip archives and folders are read up to 1,500 files of at most 800,000 bytes "
        "each; GitHub requests time out after 20 s (pull request) or 40 s (archive); repository questions ask for between 1 and 12 results; uploaded text is decoded "
        "with replacement characters so that binary content cannot raise an exception. The codebase index of the project itself excludes the front end, the "
        "documents, the scripts, the data folder and the environment file, so that secrets are never indexed. Cross-origin requests are allowed only from the "
        "two local front-end addresses.",
        "**Error surfacing.** Failures inside a job (a bad GitHub link, a network error) are caught in the job thread and appear in the job record, from which the "
        "interface shows them with a retry option. Any other uncaught exception is converted by a global handler into a 500 response with the exception type and "
        "message. The interface has a distinct state for every case, including an unreachable API.")
    d.p("**What is not protected.** The history of reviews is not linked to users, so every account sees every review. Jobs and repository indexes are "
        "in memory and lost on restart. There is no rate limit other than the cost of bcrypt. The global error handler returns exception text, and the "
        "`folder` input reads any directory of the API host; both suit a local tool, not a server. The default `JWT_SECRET` is a placeholder, the demo "
        "credentials are published by a public endpoint by design, and tokens in local storage are exposed to any script injected into the page; the "
        "interface sanitises the Markdown it renders to reduce that risk.")


def sec_install(d):
    d.h2("Installation and Execution")
    d.p("The product runs on Windows with Python 3.11 and Node.js. The ports are fixed in the `.env` file: 8311 for the API and 5311 for the web application. "
        "The sequence below was used for the final tests.")
    d.table([["Step", "Command", "Effect"],
             ["1", "`run.bat`", "Reads the ports, installs the Python requirements, installs the npm packages when `frontend/node_modules` is missing, opens two windows (API and web) and then the browser at port 5311"],
             ["2", "Press 'Use the demo account'", "Signs in as demo@autosecai.dev with the password Demo@1234, or create an account on the same page"],
             ["3", "Overview, 'Run demo pull request review'", "Runs the seven agents on the built-in vulnerable pull request and opens the review"],
             ["4", "`python -m pytest tests -q`", f"{17} engine and API tests"],
             ["5", "`python scripts/smoke_test.py`", "16 checks against the running API"],
             ["6", "`python scripts/ui_flows.py`", "22 browser flows with Playwright (needs `playwright install chromium`)"],
             ["7", "`python scripts/capture_screens.py`", "Rewrites the screenshots in `docs/screenshots`"],
             ["8", "`cd frontend && npm run build`", "Type-checks and bundles the web application"]],
            "Installation and verification commands", widths=[0.07, 0.38, 0.55], font=9)
    d.p("To run the parts by hand: `python -m backend` starts the API and `npm run dev` inside `frontend` starts the web application, which proxies `/api` to "
        "the API. The first start trains the models if the artefacts are missing (about 30 s). Anthropic keys and GitHub tokens are optional and are entered on "
        "the settings page. The original Streamlit interface is still started with `run_streamlit.bat` but requires `streamlit` and `plotly`, which were not installed "
        "on the test machine and therefore were not tested.")
