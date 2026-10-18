"""Chapters 9 and 10, implementation decisions, references and appendices for the AutoSecAI documents."""
from __future__ import annotations

import textwrap

from docx.shared import Inches

from doc_common import (API, BEST, CHARTS, DEMO, EV, LAT, MODELS, REFERENCES, REP, RET, ROOT, SEEDS, SHOTS,
                        RULE_ENTRIES, RULES_QUALITY, RULES_SECURITY, SMOKE_CHECKS, TESTS_API, TESTS_ENGINE, UI_FLOWS, f3)
from rc_results import extra_block

S = SEEDS["summary"]


def ms(model: str, metric: str) -> str:
    v = S[f"{model}|{metric}"]
    return f"{v['mean']:.3f} +/- {v['sd']:.3f}"


# ------------------------------------------------------------------ source extraction (so listings match the code)
def _lines(path: str) -> list[str]:
    return (ROOT / path).read_text(encoding="utf-8").splitlines()


def src(path: str, start: int, end: int) -> str:
    """Lines start..end (1-based, inclusive) of a repository file."""
    return "\n".join(_lines(path)[start - 1:end])


def grab(path: str, marker: str, n: int, until: str | None = None) -> str:
    """The first line that contains `marker` and the n - 1 lines after it (or up to the first line containing `until`), dedented."""
    lines = _lines(path)
    i = next(k for k, ln in enumerate(lines) if marker in ln)
    chunk = lines[i:i + n]
    if until:
        j = next(k for k, ln in enumerate(chunk) if until in ln)
        chunk = chunk[:j + 1]
    return textwrap.dedent("\n".join(chunk)).rstrip()


# ------------------------------------------------------------------ implementation decisions
def sec_decisions(d):
    d.h2("Implementation Decisions and Reasoning")
    d.p("The table lists the main decisions taken while building AutoSecAI, the reason for each and the price that was paid. Most of them follow one "
        "principle: every claim the tool makes about a pull request must come with evidence that a developer can check, and the tool must keep working "
        "on a laptop without any account or network.")
    d.table([["Decision", "Why", "Trade-off"],
             ["Seven deterministic agents; a language model only rewrites text, and only if a key is supplied",
              "Results are reproducible, testable and available offline; every finding carries a rule, a line, a CWE and a trace entry",
              "Less flexible than a free-form reviewer; the optional language-model mode is not measured"],
             ["Python `ast` with lightweight taint tracking instead of a full data-flow engine",
              f"About {EV['rule_engine_seconds_per_function_ms']} ms per function, a source-to-sink explanation for every injection finding, and rewrites that can be re-scanned",
              "Taint is followed inside one function and parameters are treated as tainted; flows across modules and unknown frameworks are missed"],
             ["Regex rules for JavaScript, PHP and Java next to the Python engine", "A pull request often touches several languages and a cheap check is better than silence", "Higher false-positive and false-negative rates than the Python path"],
             ["Python-AST adaptation of the base paper's 14 metrics, with M12-M14 added", "The paper's code property graph is built for C; injection flaws in Python are better described by risky calls, string-built sinks and untrusted sources",
              "Only M1-M11 mirror the paper; the added metrics are this project's own design"],
             ["A generated corpus for the metric model", "No labelled Python vulnerability data of suitable size was available, and the C datasets of the paper cannot be reused", "Scores describe a generator, not real code; stated on every screen of the Model Lab"],
             ["Own SMOTE and Tomek-link code (NumPy and scikit-learn only)", "One dependency fewer and a transparent implementation that can be unit tested (test_smote_tomek_balances)", "A simple version of the algorithms [15], [16], [17] that was not compared with a library"],
             [f"Production model chosen by held-out F1 ({BEST}), Random Forest kept for importances", f"{BEST} had the best F1 ({f3(MODELS[BEST]['f1'])} against {f3(MODELS['Random Forest']['f1'])}); Random Forest gives the importance chart of the base paper", "Selection on the test set; the five-corpus study shows the ranking is stable but small differences are not significant"],
             ["A patch is marked verified only if a re-scan no longer finds the same rule near the same line and the patched file still parses", "A suggestion that does not remove the problem is worse than none", "A re-scan proves the rule no longer fires, not that behaviour is preserved; the repository's own tests are not run"],
             ["Risk score 100 x (1 - exp(-W / 18)); findings outside the diff count 15%", "A bounded, saturating score; only lines changed by the pull request should block a merge", "The constants were chosen by judgement, not fitted"],
             ["Verdict from rules (a high or critical security finding in the diff blocks) as well as from the score", "A single serious flaw must block the merge even when the score is moderate", "Conservative: low-confidence high-severity findings do not block, but medium-confidence ones do"],
             ["Reviews run as background threads polled by the browser", "No broker to install; the interface shows each agent's message as it appears", "The job table is in memory and is lost on restart; one process only"],
             ["SQLite with one JSON document per review", "A review is read and written as a whole; no migrations when a field is added", "No queries inside findings and no owner column, so the history is shared by all accounts"],
             ["A thin FastAPI layer over the unchanged engine; the Streamlit interface left in place", "The engine and its ten tests were not touched; the API adds authentication, jobs and exports only", "A second front end to maintain; the Streamlit version could not be run on the build machine"],
             ["React 19 and TypeScript application from an interface kit (Aurora Glass)", "Designed states for loading, empty and error cases, dark mode, reduced motion and keyboard use from the start; 22 scripted flows verify it", "A larger dependency tree than the original interface"],
             ["TF-IDF, concept words and an import / call graph for the codebase assistant", "Works offline without downloading an embedding model; each answer lists why a location matched", f"Lexical: the expected file was first for {RET['top1']} of {RET['questions']} questions only"],
             ["Local-first settings: the optional API key and token stay in the browser", "Nothing leaves the machine unless the user turns the option on", "Keys are visible to anyone with access to the browser profile"]],
            "Implementation decisions", widths=[0.3, 0.38, 0.32], font=8.5)


# ------------------------------------------------------------------ chapter 9: conclusion
def sec_conclusion_summary(d):
    m = MODELS[BEST]
    d.h2("Summary of the Work")
    d.paras(
        "This project built AutoSecAI, an analyser that reviews a pull request for security flaws and code-quality problems and explains what it found. "
        "A change can be supplied as a diff, two versions of a file, a GitHub link or uploaded files. Seven cooperating agents then parse it, apply abstract-syntax-tree "
        "and taint rules, score every changed function with the metric model of the base paper [1], explain each finding with its weakness class, impact and "
        "source-to-sink flow, propose a patch that is re-scanned to check that it works, summarise maintainability, and issue a risk score and a verdict. A codebase "
        "assistant answers natural-language questions about a repository, and a Model Lab reproduces the base-paper pipeline on Python. The tool is a "
        f"FastAPI service with a React interface, {TESTS_ENGINE + TESTS_API} automated tests and a demonstration account.",
        f"On a generated corpus of {REP['n_functions']:,} Python functions the metric model ({BEST}) reached an F1 of {f3(m['f1'])} (mean {ms(BEST, 'f1')} over five corpora), the rule engine "
        f"{f3(EV['rule_engine']['f1'])} and the two together {f3(EV['combined_or']['f1'])}. The built-in vulnerable pull request was reviewed in a median of {LAT['median_s'] * 1000:.0f} ms and "
        f"blocked with a risk score of {DEMO['score']}, and the codebase assistant ranked the expected file first for {RET['top1']} of {RET['questions']} questions. "
        "These results come from generated data and a small repository; no real labelled pull requests were available.")


def sec_conclusion_objectives(d):
    d.h2("Objectives Achieved")
    d.p(f"Of the six objectives, the first three were achieved with the limits noted in the results chapter: diff context is extracted on request, not by a webhook; "
        f"metrics rank the changed functions; and {RULES_SECURITY} security rules detect injection and validation flaws but not missing object-level authorisation. The objective of deploying "
        f"LLM agents is met only in part, because the agents are deterministic programs with an optional language-model layer, and related repository code is retrieved by the "
        f"codebase assistant but not yet fed into the review comments. A consolidated comment is generated and exported, but not posted to GitHub, and **precision against "
        f"manually reviewed pull requests was not evaluated**, because no such set was available.")


def sec_conclusion_findings(d):
    imp = REP["importance"]
    taint = sum(v for k, v in imp.items() if k.split()[0] in ("M12", "M13", "M14"))
    kc = REP["k_scores"]
    d.h2("Key Findings")
    d.numbered([
        f"**Two detectors are better than one.** On 1,500 held-out functions the rule engine found {EV['rule_engine']['tp']} of 125 vulnerable functions and the model {EV['ml_model']['tp']}; together they found {EV['combined_or']['tp']} (F1 {f3(EV['combined_or']['f1'])}).",
        f"**Taint-oriented metrics carry the signal.** The three metrics added for Python injection (M12, M13, M14) hold {taint * 100:.1f}% of the importance; keeping only five metrics gave a validation F1 of {f3(kc['5'])}, keeping thirteen {f3(kc['13'])}.",
        f"**The headline is the best case.** XGBoost reached {f3(MODELS[BEST]['f1'])} on the stored corpus but {ms(BEST, 'f1')} on average over five; Random Forest averaged {ms('Random Forest', 'f1')}.",
        "**Balancing was not shown to help.** Recall was identical with and without SMOTE-Tomek and precision fell; because the feature count also differed, the effect of balancing alone remains unmeasured.",
        f"**The model cannot be trusted alone.** It gave a probability of 0.006 to a plain SQL-injection function that builds its query in a variable, which the rule SQLI flagged; the type classifier reached only {f3(REP['type_accuracy'])} accuracy.",
        f"**Fast, but patches need judgement.** A review took a median of {LAT['median_s'] * 1000:.0f} ms; seven of the 15 security findings of the demonstration received a verified patch and the other eight were left to the developer.",
    ])
    if not getattr(d, "report", False):  # repeated in another chapter of the full report
        d.figure(CHARTS / "engine_vs_ml.png", "Rule engine, metric model and their combination on the same held-out functions", width=4.6)


def sec_conclusion_applications(d):
    d.h2("Practical Applications")
    d.bullets([
        "**Teams that review pull requests** can run the tool before a human reviewer, read the verdict and the findings, and paste the generated comment or upload the SARIF file to code scanning [26].",
        "**Junior developers** can index an unfamiliar repository and ask where authentication, routes or the database layer are handled, and read the generated onboarding guide.",
        "**Security trainers** can use the demonstration pull request and the explanations, with their CWE [25] and OWASP [24] mapping, to teach the common injection flaws.",
        "**Students of machine learning for software engineering** can use the Model Lab to see the effect of feature selection, balancing and model choice on a documented generator.",
        "**Maintainers of small projects** without a security team can run the checks locally, because nothing leaves the machine unless the optional language-model layer is switched on.",
    ])


def sec_conclusion_limits(d):
    d.h2("Known Limitations")
    d.bullets([
        "The metric model was trained and tested on generated Python functions; its scores are a prioritisation signal and the figures do not transfer to real repositories. The rule-engine figures are optimistic, and no comparison with Bandit, Semgrep or CodeQL was run.",
        "Deep analysis covers Python only; JavaScript, PHP and Java have regex rules, and missing authorisation checks are not detected. Whole-file fixes exist only for full-file input.",
        "The optional language-model mode and the real GitHub pull-request fetch were not measured; the job table is in memory and the history is shared by all accounts.",
        f"The retrieval check used {RET['questions']} questions on one small repository, and no load test or user study was carried out. No numeric comparison with the base paper is possible.",
    ])


# ------------------------------------------------------------------ chapter 10: future scope
def sec_future_improvements(d):
    d.h2("Improvements")
    d.bullets([
        "Collect a labelled set of real pull requests and measure precision, recall and the false-alarm rate of the whole system on it, next to Bandit, Semgrep and CodeQL.",
        "Replace the generated corpus with real Python functions labelled from public vulnerability records, retrain, and report both results.",
        "Re-select the number of metrics for every corpus and run a single-factor experiment for balancing.",
        "Follow taint across function and module boundaries, add checks for missing authorisation, and add a per-user owner column to the review history.",
    ])


def sec_future_features(d):
    d.h2("Additional Features")
    d.bullets([
        "A GitHub App or webhook that reviews a pull request when it is opened and posts the consolidated comment and the suggested patches back.",
        "Feeding the codebase assistant's retrieval into the review, so that a finding can mention the callers and related code of the changed function.",
        "Running the project's own test suite against a patch before it is marked verified.",
        "More languages with real parsers (JavaScript and TypeScript first), a baseline file for known findings, and a dependency-vulnerability check.",
    ])


def sec_future_deploy(d):
    d.h2("Scalability and Deployment")
    d.bullets([
        "Move the job table to a queue with a worker process, so that reviews survive a restart and several can run in parallel.",
        "Replace SQLite with a server database, store the findings in tables, and add user and team ownership with role-based access.",
        "Serve over HTTPS with a generated signing secret instead of the development default, add rate limiting, and complete a security review of the service itself.",
        f"Package the service as containers with a production build of the interface, measure load and concurrency (not tested here), and run the {TESTS_ENGINE + TESTS_API} tests, the smoke test and the {UI_FLOWS} browser flows in continuous integration.",
    ])


def sec_future_research(d):
    d.h2("Further Research")
    d.bullets([
        "Compare the metric model with learned detectors of the kind listed in the batch survey, such as hybrid CNN-LSTM [3] and code-language-model approaches [6], on the same real labelled set.",
        "Study whether a checklist-based evaluation of review comments, as proposed in [2], can be applied to the explanations that AutoSecAI generates, and how a language model should be trained or prompted to meet it.",
        "Learn the weights of the risk score and the verdict rule from developers' decisions, and calibrate the model probability before combining it with the rule evidence.",
        "Investigate metrics that capture taint across functions, and whether M12-M14 generalise to other languages.",
    ])


# ------------------------------------------------------------------ references
def sec_references(d, heading=True):
    if heading:
        d.h2("References")
    for i, ref in enumerate(REFERENCES, 1):
        p = d.p(f"[{i}]\t{ref}", align="left", size=11, line=1.2, space_after=4)
        p.paragraph_format.left_indent = Inches(0.45)
        p.paragraph_format.first_line_indent = Inches(-0.45)


# ------------------------------------------------------------------ appendices
def appendix_a(d):
    d.p("The listings below are extracted from the source files when this report is built, so they match the code that produced the results. "
        "Only the parts that carry the main ideas are shown; each listing names its file.")
    d.h2("Risk Score and Verdict (Judge Agent)")
    d.p("After de-duplication the Judge Agent applies the minimum-severity filter, weights each finding by severity and confidence, counts findings outside the "
        "changed lines at 15%, turns the sum into a bounded score and applies the verdict rule.")
    d.code(grab("autosecai/agents.py", "floor = SEVERITY_ORDER[min_severity]", 30, until='verdict = "APPROVE"'), "Scoring and verdict in review_changes(), autosecai/agents.py")
    d.h2("Patch Verification (Remediation Agent)")
    d.p("A patch is applied to a copy of the source and the analyser is run again; the patch counts as verified only when the same rule no longer fires near the same line and the patched Python file still parses.")
    d.code(grab("autosecai/agents.py", "new, ok = apply_fixes(base, [fx])", 16, until='verified["ok"] +='), "Verification by re-scan in review_changes(), autosecai/agents.py")
    d.h2("Taint Level of an Expression")
    d.p("Each name is given a level: 0 for constants and sanitised values, 1 for strings built from other values, 2 for function parameters and 3 for direct request input. "
        "The level of an expression is the highest level of its parts.")
    d.code(grab("autosecai/rules.py", "def _level_of", 26), "_level_of() in PyAnalyzer, autosecai/rules.py")
    d.h2("SQL Injection Rule")
    d.code(grab("autosecai/rules.py", "# --- SQL injection", 14, until="return"), "SQL injection check in PyAnalyzer._check_call(), autosecai/rules.py")
    d.h2("SMOTE and Tomek Links")
    d.code(grab("autosecai/mlmodel.py", "def smote(X", 17), "smote() in autosecai/mlmodel.py")
    d.code(grab("autosecai/mlmodel.py", "def tomek_clean", 13), "tomek_clean() in autosecai/mlmodel.py")
    d.h2("Scoring One Function with the Metric Model")
    d.code(grab("autosecai/mlmodel.py", "def predict_metrics", 26, until="for f, c, v, mu in contrib[:3]"), "predict_metrics() in autosecai/mlmodel.py")
    d.h2("Codebase Retrieval")
    d.p("A question is scored by TF-IDF similarity, a bonus for the detected concept (authentication, routes, database ...) and bonuses for exact identifier and path "
        "matches; personalised PageRank over the import and call graph then adds a small boost to neighbours of the strongest matches.")
    d.code(grab("autosecai/codeintel.py", "intents = self.detect_intent(question)", 24), "Scoring in RepoIndex.ask(), autosecai/codeintel.py")
    d.h2("Review Storage")
    d.code(src("autosecai/store.py", 1, 44), "autosecai/store.py")
    d.h2("Background Jobs")
    d.code(grab("backend/main.py", "def start_job", 24, until='return job["id"]'), "start_job() in backend/main.py")
    d.h2("Passwords and Tokens")
    d.code(grab("backend/auth.py", "def _hash", 3) + "\n\n" + grab("backend/auth.py", "def make_token", 4) + "\n\n" + grab("backend/auth.py", "def current_user", 15),
           "Password hashing and token functions in backend/auth.py")
    d.h2("SARIF Export")
    d.code(grab("autosecai/report.py", "def to_sarif", 18), "to_sarif() in autosecai/report.py")


def appendix_b(d):
    d.h2("Installation Guide")
    d.p("AutoSecAI runs on Windows 10 or 11 with Python 3.11 and Node.js. The ports are fixed in the file `.env`: **8311** for the API and **5311** for the web application.")
    d.numbered([
        "Install Python 3.11 (with `python` on the PATH) and Node.js.",
        "Open the project folder (`8.ProjectCode`) and double-click `run.bat`. It reads the ports from `.env`, installs the Python packages from `requirements.txt` and, when `frontend/node_modules` is missing, the web packages; it then starts the API and the web application in two windows and opens http://localhost:5311.",
        "On the first start the models are trained (about 30 seconds) if `autosecai/artifacts/` is missing; the demonstration account is created automatically.",
        "Press \"Use the demo account\" on the sign-in page, or sign in with `demo@autosecai.dev` and `Demo@1234`, or create your own account (password of at least 8 characters).",
        "To stop, close the two windows. The data (`data/app.db`, `data/history.db`) stays in the project folder.",
    ])
    d.p("To start the two servers by hand, run the commands below in two terminals.")
    d.code("pip install -r requirements.txt\npython -m backend                    # API on http://127.0.0.1:8311 (documentation at /docs)\ncd frontend\nnpm install\nnpm run dev                          # web app on http://localhost:5311",
           "Manual start")
    d.code("python -m pytest tests -q          # 17 tests: engine and API\npython scripts/smoke_test.py       # 16 API checks (API running)\npip install playwright && playwright install chromium\npython scripts/ui_flows.py         # 22 browser flows\npython scripts/capture_screens.py  # rewrites docs/screenshots\ncd frontend && npm run build       # production build",
           "Checks")
    d.p("Optional settings (Settings page): an Anthropic API key switches on language-model explanations; a GitHub token raises the rate limit and allows private repositories. "
        "Without them everything runs offline. The original Streamlit interface still starts with `run_streamlit.bat` when `streamlit` and `plotly` are installed.")
    d.h2("User Guide")
    d.table([["Task", "How"],
             ["Sign in", "Use the demo account button, or enter an e-mail and password; \"Create account\" registers a new user"],
             ["Review the demonstration pull request", "Overview, then \"Run demo pull request review\" (or PR review, tab Demo PR, button \"Run multi-agent review\"); each agent's message appears while it works"],
             ["Review your own change", "PR review, then Paste diff (or drop a .diff / .patch file), Compare versions (old and new text of one file), GitHub PR link, or Upload files / repo (files, a zip or a local folder)"],
             ["Read the result", "The banner gives the verdict and the risk score; the Findings tab lists findings with filters (severity, security or quality, only changed lines, search) and expandable cards with explanation, impact, flow, remediation, safe example and the verified patch"],
             ["See which functions the model distrusts", "Function risk (ML) tab: probability, type and drivers per function; \"Inspect a function\" shows the radar chart against typical safe functions"],
             ["Check what each agent did", "Agent trace tab: the seven agents, their time and their summary"],
             ["Export", "Export tab: PR comment (.md), SARIF 2.1, full JSON, findings CSV, and whole fixed files when the input was a full file"],
             ["Ask about a repository", "Codebase assistant: choose the demo shop, this project, a zip, a folder or a GitHub URL, press Index repository, then ask or pick a suggested question; the Repository map and Onboarding guide tabs summarise the code"],
             ["Study or try the model", "Model Lab: pipeline, feature selection, models, ROC and confusion, vulnerability types, ablation; \"Try it\" scores a pasted function; \"Retrain models\" rebuilds the report in about half a minute"],
             ["Look at earlier reviews", "History: search, open or delete a review; the chart shows the risk score over time"],
             ["Change the settings", "Settings: ML risk agent on or off, minimum severity, optional API key and GitHub token, theme (Light, Dark, System); settings are kept in the browser"]],
            "User guide", widths=[0.28, 0.72], font=10)
    d.p("AutoSecAI supports a reviewer; it does not replace one. A finding is a lead with evidence, and the decision to merge stays with the people responsible for the code.")


def appendix_c(d):
    d.p("Additional captures of the running application (18 October 2026). The main screens are shown in the chapter on results and output screens.")
    extra_block(d)
