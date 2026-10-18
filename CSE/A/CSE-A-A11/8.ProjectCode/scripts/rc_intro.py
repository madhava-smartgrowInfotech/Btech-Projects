"""Chapter 1 content: domain, motivation, problem, need, objectives, scope, contributions, limitations, organisation."""
from __future__ import annotations

from doc_common import (BEST, DEMO, EV, LAT, MODELS, PRODUCT, REP, RET, RULE_ENTRIES, RULES_QUALITY, RULES_SECURITY, SEEDS,
                        SIZE, TESTS_API, TESTS_ENGINE, f3)


def sec_domain(d):
    d.h2("Introduction to the Project Domain")
    d.paras(
        "Modern software is built by teams that change the same code base many times a day. In most teams every change arrives as a "
        "**pull request** (PR): a proposed set of modified files, shown as a diff, that another engineer must read and approve before it "
        "is merged. The PR is the last point at which a flaw can be stopped cheaply. A SQL query built by string concatenation, a "
        "password in a source file or a call to `os.system` with user input is only a few lines long, yet can open the whole application "
        "to an attacker. Such flaws are catalogued in the Common Weakness Enumeration [25] and ranked by the OWASP Top 10 [24].",
        "The domain of this project is therefore **artificial intelligence for software engineering and cybersecurity**, and more "
        "precisely **automated security and quality review of code changes**, together with **code-base comprehension** for engineers "
        "who must work in a repository they did not write. It draws on static analysis (abstract syntax trees and taint "
        "tracking that follow untrusted data from source to sink), software metrics [21] that relate to the likelihood of a "
        "vulnerability [1], [8], machine learning with balancing techniques [15]-[17], information retrieval with TF-IDF [22] and graph "
        "ranking [23], and large language models (LLMs) that can write the explanations that make a warning actionable.",
        f"**{PRODUCT}**, the system built in this project, combines these ideas in one application. A developer gives it a pull "
        "request in one of five forms (a diff, two versions of a file, a GitHub PR link, uploaded files or a zip, or a local folder). "
        "Seven cooperating software agents then ingest the change, analyse it statically, score every changed function with a trained "
        "model, explain each finding, propose a patch verified by re-scanning, summarise maintainability issues and weigh the evidence "
        "into a risk score and a verdict of approve, request changes or block. A second module indexes a repository so that a new team "
        "member can ask where authentication, routing or configuration lives. The \"multi-agent LLM\" of the title should be read in "
        "that sense: specialised agents hand evidence to one another, an optional language-model layer can rewrite their explanations, "
        "but every finding is produced and verified by deterministic components that run on the user's machine.")


def sec_motivation(d):
    d.h2("Background and Motivation")
    d.paras(
        "Three observations motivated the project. First, review effort does not scale with the pace of development. A reviewer who "
        "reads many diffs a week cannot give each the attention of a security audit, and flaws such as injection, path traversal and "
        "unsafe deserialisation look harmless in a diff because the untrusted value may enter in a different function. Whether a "
        "reviewer notices them depends on that person's security expertise.",
        "Second, the usual automatic help is noisy. Static analysers report every pattern that resembles a weakness, so developers "
        "learn to ignore long lists of warnings that are mostly false alarms, and a warning such as \"possible injection\" does not "
        "say why the code is dangerous, what an attacker could do, or what safe code would look like. The literature on vulnerability "
        "prediction offers a complementary signal: measurable properties of a function, such as its complexity, its number of risky "
        "calls and its use of untrusted input, correlate with the presence of a vulnerability [1], [8]. The base paper [1] shows that a "
        "small set of such metrics, selected by seven methods and used with a balanced training set, lets a random forest separate "
        "vulnerable from safe C and C++ functions with an F1-score of 0.961 on its data. That work is offline, classifying functions of "
        "finished projects rather than live pull requests, and the authors name Python and Java as future work.",
        "Third, a change cannot be judged without its context. A reviewer who is new to a repository does not know which module "
        "handles authentication, where requests are routed or how the database is reached, and so cannot tell whether a changed line "
        "bypasses a control that exists elsewhere. Recent LLM-based review work, such as the Sphinx framework [2], argues that review "
        "comments must be grounded in the code change and judged by structured checklists rather than text overlap, so evaluation is "
        "as hard as generation. These observations suggest a reviewer that combines static evidence, a learned risk signal "
        "and repository context and explains its findings; this project builds one.")


def sec_problem(d):
    d.h2("Problem Statement")
    d.paras(
        "Manual pull request review does not scale with the pace of modern development. Security review depends on whether the "
        "reviewer happens to have security expertise. Static analysers overwhelm developers with warnings that are mostly false "
        "positives. Reviewers lack the context of a large code base when judging a small diff.",
        "**Formal statement.** Given a code change (a unified diff, a pair of file versions, a pull request fetched from GitHub, or a "
        "set of files), produce (i) a list of security findings, each tied to a file and line, classified by weakness (CWE) and "
        "severity, explained in terms of the flow from untrusted source to dangerous sink, and accompanied, where a safe rewrite is "
        "possible, by a patch that has been checked by re-analysing the patched code; (ii) a maintainability summary; (iii) for every "
        "changed function, a learned probability that it is vulnerable and the code metrics that drive that probability; and (iv) a "
        "single risk score and a merge verdict. Given a repository, answer natural-language questions about where a feature is "
        "implemented, citing the code that supports the answer. The system must state how it was measured and where it has not been.",
        "**Need.** An autonomous reviewer that analyses each pull request for security and quality using code-base-aware, multi-agent "
        "reasoning.")


def sec_need(d):
    d.h2("Need for the Proposed System")
    d.bullets([
        "**Scalable first-pass review.** A tool that reads every change in seconds frees reviewers for design and logic.",
        "**Fewer, better warnings.** Evidence from independent detectors (rules, taint tracking, a learned model) is combined, de-duplicated and ranked.",
        "**Explanations and fixes, not raw warnings.** Each finding needs what is wrong, the impact, the data flow, a safe example and, where possible, a patch known to remove it.",
        "**A measurable risk signal.** Metrics are interpretable [1]; a model that shows which metrics drive a function's score gives reviewers a reason to look closer.",
        "**Context for reviewers and newcomers.** A repository assistant that locates authentication, routing and database code shortens onboarding.",
        "**Standard outputs.** Results should be exportable as a Markdown PR comment and as SARIF 2.1.0 [26], so that they fit existing code-hosting and security tooling.",
        "**Low cost and privacy.** The reviewer should run on an ordinary laptop, keep source code on the user's machine, and use an external language model only if the user explicitly turns it on.",
    ])


def sec_objectives(d):
    d.h2("Objectives")
    d.numbered([
        "Extract changed files and diff context automatically when a pull request is opened.",
        "Compute source-code metrics for changed files and use them to rank vulnerability likelihood.",
        "Perform AST-based static analysis to detect injection, access-control and validation flaws.",
        "Deploy multiple LLM agents covering security, code quality and maintainability concerns.",
        "Retrieve related code from the repository so review comments reflect the wider code base.",
        "Post consolidated review comments and evaluate precision against manually reviewed pull requests.",
    ])
    d.p("These are the six objectives of the project as defined at its start. The table shows which part of the system addresses each "
        "one; Chapter 8 measures each of them against the results and states plainly where the evidence is incomplete.")
    d.table([["No.", "Objective (short form)", "Addressed by"],
             ["1", "Extract changed files and diff context", "`diffutil.py`: unified-diff parser, before/after comparison, GitHub PR and zip/folder readers; Ingestion Agent"],
             ["2", "Source-code metrics rank vulnerability likelihood", "`metrics.py` (14 AST metrics), `mlmodel.py` (feature selection, SMOTE-Tomek, nine models); ML Risk Agent"],
             ["3", "AST-based static analysis for injection, access-control and validation flaws", "`rules.py` (AST and taint engine) and `knowledge.py` (rule entries with CWE and OWASP); Static Analysis Agent"],
             ["4", "Multiple agents for security, quality and maintainability", "`agents.py`: seven agents with a trace; optional LLM text layer in `llm.py`"],
             ["5", "Retrieve related code from the repository", "`codeintel.py`: repository index, concept scores, call graph, cited answers"],
             ["6", "Consolidated review comments; precision against manually reviewed pull requests", "Judge Agent and `report.py` produce the comment; the manual-review precision study was **not** carried out (no labelled set exists)"]],
            "Objectives and the modules that address them", widths=[0.07, 0.38, 0.55], font=9.5)


def sec_scope(d):
    d.h2("Scope of the Project")
    d.h3("In scope")
    d.bullets([
        "Review of code changes in five input forms: a built-in demo pull request, a pasted or uploaded unified diff, two versions of one file, a GitHub PR URL (public API, optional token), and uploaded files, a zip or a local folder.",
        f"Deep AST and taint analysis of **Python**, and regex rules for JavaScript, PHP and Java; {RULE_ENTRIES} rule-knowledge entries ({RULES_SECURITY} security, {RULES_QUALITY} quality and one ML-derived), each with CWE, OWASP category, severity, explanation, impact, remediation and a safe pattern.",
        "Computation of 14 source-code metrics per function and scoring with a trained classifier, with the three metrics that drive each score.",
        "Automatic patches for the weakness classes that have a safe rewrite, each verified by re-scanning; a 0 to 100 risk score and a verdict (approve, request changes, block).",
        "A repository assistant (demo shop, this project, zip, local folder or GitHub repository) with cited answers, a repository map and an onboarding guide.",
        "Exports as Markdown, SARIF 2.1.0, JSON and CSV, patched files, and a review history with a risk trend.",
        "A Model Lab that reproduces the base-paper pipeline on Python code, with charts and a single-function scorer.",
        "A web application with accounts (bcrypt, JWT) and a demo account, a landing page with real model figures, light and dark themes, reduced-motion support and a layout that works from 360 px wide.",
    ])
    d.h3("Out of scope")
    d.bullets([
        "Merging, approving or commenting on a pull request on the code host automatically: a person decides.",
        "Dynamic analysis, fuzzing, and dependency, container or commit-history scanning.",
        "Deep taint analysis of languages other than Python; JavaScript, PHP and Java are covered by simpler pattern rules only.",
        "Proof that a finding is exploitable: a finding is evidence for a reviewer.",
        "Training a language model; the optional LLM layer only rewrites text and is off by default.",
        "Multi-tenant production deployment: HTTPS termination, rate limiting by address, per-user separation of stored reviews and distributed job execution.",
        "Precision and recall of the whole system on real, manually reviewed pull requests (no labelled set was available).",
    ])
    d.h3("Assumptions")
    d.bullets([
        "The submitted change or repository is source text that the user is entitled to analyse; Python files are syntactically valid (otherwise they are scanned with generic rules).",
        "The base-paper technique, source-code metrics with a balanced classifier, transfers in spirit from C/C++ to Python, although the metrics are Python analogues and the training data are generated.",
        "One developer uses the application on one machine; the `data` folder stays on that machine.",
        "The optional Anthropic key and GitHub token are supplied by the user; without them everything except GitHub fetching works offline.",
    ])


def sec_contrib(d):
    ev, seeds = EV, SEEDS["summary"]
    d.h2("Key Contributions")
    d.numbered([
        "**A seven-agent pull-request reviewer with an auditable trace.** Ingestion, Static Analysis, ML Risk, Security Reasoner, Remediation, Quality Reviewer and Judge agents run in sequence; each records its role, duration, summary and details, and the interface shows them live as the job runs. The built-in demo pull request (1 file, +67/-1 lines) is reviewed in a median of "
        f"{LAT['median_s']:.3f} s and yields {DEMO['findings']} findings, a risk score of {DEMO['score']} and a {DEMO['verdict']} verdict.",
        f"**An AST and taint engine for Python with a rule knowledge base.** {RULES_SECURITY} security rules and {RULES_QUALITY} quality rules, each mapped to a CWE and an OWASP category with an explanation, impact, remediation and safe pattern. On the 1,500 held-out functions the engine alone reached precision {f3(ev['rule_engine']['precision'])}, recall {f3(ev['rule_engine']['recall'])} and F1 {f3(ev['rule_engine']['f1'])}.",
        f"**Verified auto-fixes.** For SQL injection, shell commands and similar classes the Remediation Agent rewrites the code, re-analyses the result and keeps the patch only if the finding has disappeared; on the demo pull request {DEMO['stats']['autofix_verified']} of {DEMO['stats']['autofix']} patches were verified.",
        f"**A Python adaptation of the base-paper metric model.** Fourteen AST metrics (M1 to M11 follow the paper's families; M12 to M14 for risky calls, string-built sinks and untrusted sources were added for Python injection flaws), seven feature selectors, SMOTE-Tomek implemented from scratch, and nine classifiers. {BEST} gave F1 {f3(MODELS[BEST]['f1'])} (mean {seeds['XGBoost|f1']['mean']:.3f} over five corpus seeds) on a generated corpus.",
        f"**Evidence that the two detectors complement each other.** Flagging a function when either the rule engine or the model flags it raised F1 to {f3(ev['combined_or']['f1'])} (recall {f3(ev['combined_or']['recall'])}) from {f3(ev['ml_model']['f1'])} for the model and {f3(ev['rule_engine']['f1'])} for the rules alone, on the same held-out functions.",
        f"**A repository assistant for code comprehension.** TF-IDF similarity, concept scores for authentication, routing, database and other themes, and personalised PageRank over an import and call graph; on twelve hand-written questions about the demo repository the expected file ranked first for {RET['top1']} and in the first three for {RET['top3']}.",
        "**Standard outputs and a complete application.** Markdown, SARIF 2.1.0, JSON and CSV exports; a FastAPI service of 25 routes, JWT authentication and a React 19 interface with every state designed.",
        f"**A repeatable test and measurement suite.** {TESTS_ENGINE + TESTS_API} automated tests, a 16-check API smoke test, 22 browser flows, and a measurement script that re-computes the engine, seed, latency and retrieval figures quoted in this report.",
    ])
    d.p("Contributions 1, 3, 7 and 8 are engineering contributions; contributions 2, 4, 5 and 6 are the elements whose quality was "
        "measured. Compared with the base paper [1], this project moves the technique into the pull-request workflow, adapts it to Python and "
        "adds taint-oriented metrics, rule-based analysis, explanation, patching and repository context. The ML measurements are made on a generated corpus, so they "
        "show that the pipeline works, not how well it would score on real vulnerabilities.")


def sec_limits(d):
    d.h2("Limitations and Assumptions")
    d.p("The limitations below qualify every number in this report; Chapter 8 returns to them with the evidence.")
    d.table([["Limitation", "Consequence for the reader"],
             [f"The classifier is trained on a **generated** Python corpus of {REP['n_functions']:,} functions ({REP['n_vulnerable']} vulnerable, {REP['class_ratio'] * 100:.2f} %). The base paper's C/C++ data are not bundled.", "Scores show that the pipeline works; they are a prioritisation signal, not proof of exploitability, and are not comparable with the paper's F1 of 0.961."],
             ["The corpus generator and the rules were written by the same team around the same eight weakness patterns, and 1 % of labels are deliberately noisy.", "The rule-engine figures are optimistic for real code; a few positives contain no vulnerable code and no detector can find them."],
             [f"The headline F1 of {f3(MODELS[BEST]['f1'])} is the best of five corpus seeds (mean {seeds_mean('XGBoost')} for {BEST}).", "Quote the mean when comparing; the number of metrics kept (k = 13) was not re-selected for each seed."],
             ["The ablation changes the number of metrics and the balancing at the same time.", "The separate effect of SMOTE-Tomek was not isolated; recall was identical with and without it."],
             ["No labelled set of real, manually reviewed pull requests exists, so objective 6 (precision against manual review) was not measured. No comparison with Bandit, Semgrep or CodeQL was run.", "The real-world precision of the review is unknown."],
             ["The 'multi-agent' design is seven deterministic software agents plus an optional LLM text layer. The LLM layer was not measured (no API key was available).", "All reported results describe the offline pipeline."],
             ["Deep analysis is Python-only; JavaScript, PHP and Java use regex rules. Whole-file fixes exist only when a full file is supplied, not for a bare diff hunk.", "Findings in other languages are less precise; some diff-only findings have no patch."],
             ["The review history is shared by all accounts (the `reviews` table has no user column), and jobs live in memory.", "Not suitable for several users on one deployment; running jobs are lost on restart."],
             ["Fetching a real GitHub pull request was tested only with an invalid URL (readable error); the Streamlit interface could not be run on the build machine.", "The GitHub path rests on the code and its error handling, not on a live fetch."]],
            "Limitations of the system and of the evidence", widths=[0.55, 0.45], font=9.5)
    d.p("Assumptions are listed in the section on scope. The most important is that source-code metrics carry a vulnerability signal in "
        "Python as in C and C++ [1]; this project does not test that on real Python vulnerabilities.")


def seeds_mean(name):
    s = SEEDS["summary"][f"{name}|f1"]
    return f"{s['mean']:.3f} +/- {s['sd']:.3f}"


def sec_organisation(d):
    d.h2("Organisation of the Report")
    d.table([["Chapter", "Title", "Content"],
             ["1", "Introduction", "Domain, motivation, problem statement, need, objectives, scope, contributions, limitations"],
             ["2", "Literature Survey", "The base paper, related work on vulnerability prediction and pull-request review, the algorithms used, strengths, limitations and the research gap"],
             ["3", "Feasibility Study", "Technical, economic, operational and schedule feasibility; advantages and constraints"],
             ["4", "System Requirements and Analysis", "Existing and proposed system, functional and non-functional requirements, hardware, software, user roles"],
             ["5", "System Design", "Architecture, workflow, data-flow diagrams, UML, database, modules and user interface"],
             ["6", "Methodology and Software Implementation", "Method, corpus, preprocessing, algorithms, formulation, training, application, API, security, installation"],
             ["7", "System Testing", "Strategy, unit, integration, functional, security, validation, performance, acceptance and the limits of testing"],
             ["8", "Results and Output Screens", "Output screens, model and engine results, comparison with the base paper, success and failure analysis, objectives against outcomes"],
             ["9", "Conclusion", "Summary, objectives achieved, findings, applications, limitations"],
             ["10", "Future Scope", "Improvements, features, deployment and research directions"]],
            "Chapters of this report", widths=[0.1, 0.3, 0.6], font=9.5)
    d.p(f"The report ends with the references, Appendix A (important code), Appendix B (installation and user guide) and Appendix C "
        f"(additional screens). Every figure is taken from the project's own artefacts: the trained-model report, the "
        f"measurement script, the test runs and the recorded screens.")
