"""Chapter 2 content: literature survey, base paper analysis, related work, algorithms, strengths and limitations, gap."""
from __future__ import annotations

from doc_common import BASE_PAPER, PRODUCT


def sec_lit_overview(d):
    d.h2("Overview of the Literature Survey")
    d.paras(
        "The survey covers four groups of work. The first is the base paper [1], which predicts software vulnerabilities from "
        "source-code metrics with machine learning. The second is work on automating pull-request review and on vulnerability "
        "detection and repair with learned models: the Sphinx framework for LLM-driven pull-request review [2] and four recent papers "
        "listed in the batch survey [3]-[6]. The third is earlier research on vulnerability prediction and detection [7]-[14]. The "
        "fourth is the techniques from which the system is built: class balancing by SMOTE and Tomek links [15]-[17], tree-ensemble "
        "classifiers [18], [19], the scikit-learn toolkit [20], cyclomatic complexity [21], TF-IDF weighting [22], graph ranking [23] "
        "and the vocabularies and formats used to report findings [24]-[26].",
        "The base paper [1] and the Sphinx paper [2] were read in full or in large part. The papers [3]-[6] are listed in the batch "
        "survey but were not retrieved, so they are described by title and year only. The works [7]-[14] are cited from the base "
        "paper's reference list, and only what their titles and the base paper's summary state is repeated here.")


def sec_base_paper(d):
    d.h2("Base Paper Analysis")
    d.p(f"**Base paper.** {BASE_PAPER}")
    d.paras(
        "**Problem and data.** Abbasi and Shameli-Sendi ask which properties of source code make a function vulnerable, and whether "
        "the same properties reveal the type of vulnerability. They collected 21,759 functions from ten open-source C and C++ projects "
        "(including SQLite, FreeType, LibTIFF, Libxslt, Binutils, FFmpeg, ImageMagick, OpenSC and rdesktop, and OpenSSL according to the "
        "abstract). Only 275 of them, about 1.26 %, are vulnerable. Six projects were used for training and testing and four (FFmpeg, "
        "ImageMagick, OpenSC and rdesktop) only for testing. Vulnerable functions are labelled with eight types, taken from the CVE and "
        "NVD databases: denial of service, buffer overflow, memory corruption, SQL injection, code execution, bypass, gain of sensitive "
        "information and gain of privilege.",
        "**Method.** The source code is parsed by a fuzzy parser (ANTLR grammar, Joern tool) into a code property graph that combines "
        "the abstract syntax tree, the control-flow graph and the program-dependence graph. Fourteen metrics, M1 to M14, are computed "
        "from the graph, among them cyclomatic complexity (M1), the number of variables in the arguments of the caller (M5), "
        "pointer-arithmetic counts (M6, M7), nested control structures (M9) and control dependency (M11). Seven feature-selection "
        "techniques (Pearson correlation, a support vector machine, Lasso, chi-squared, RFE with logistic regression, RFE with a random "
        "forest and a variance threshold) each rank the metrics, and the five that recur are kept. The classes are balanced with "
        "SmoteTomek [17], the metrics are scaled with Min-Max normalisation, and nine machine-learning models are trained, with their "
        "hyper-parameters set by grid search and evaluated with repeated k-fold cross-validation. The same procedure is applied to eight "
        "smaller datasets, one per vulnerability type.",
        "**Reported results.** The five metrics found most important for predicting vulnerability were M5, M6, M1, M9 and M11. The "
        "Random Forest was the best of the nine models, with an accuracy of 0.96, a precision of 0.948, a recall of 0.974 and an F1-score "
        "of 0.961. Across all projects the model found 261 of the 275 vulnerable functions, compared with 244 in the authors' earlier "
        "work. For denial-of-service vulnerabilities, the Random Forest reached an accuracy of 0.972 and an F1-score of 0.972, against "
        "an accuracy of 0.89 in the earlier work.",
        "**Limitations stated by the authors.** Code property graphs rest on static analysis, so conservative approximations can add "
        "false edges, and macros and compiler extensions can disturb the syntax tree. The grammar is limited to C and C++; the authors "
        "propose extending the framework to Python and Java and combining the models with autonomous security systems.",
        f"**What {PRODUCT} adopts.** The central idea, that a small set of interpretable source-code metrics, chosen by several "
        "selectors and used with a balanced training set, separates vulnerable from safe functions, and that the metrics also hint at the "
        "vulnerability type. The Model Lab reproduces the full pipeline: fourteen metrics, the same seven selectors with a vote-and-rank "
        "consensus, SMOTE and Tomek-link cleaning, Min-Max scaling, nine classifiers and a type classifier. The paper's Python-and-Java "
        "future work is the starting point of the adaptation.",
        f"**What {PRODUCT} changes.** The data (generated Python functions instead of real C and C++ projects), the metric source (the "
        "Python `ast` module and an analogue of control dependency instead of a code property graph), three added metrics (M12 risky API "
        "calls, M13 string-built sinks, M14 untrusted sources) that capture how Python injection flaws arise, the number of metrics kept "
        "(chosen by a validation sweep from 5 to 14 rather than fixed at five), and above all the setting: the model is one agent of a "
        "pull-request pipeline that also runs rule-based taint analysis, explains each finding, proposes verified patches and gives a "
        "merge verdict. The paper evaluates a classifier; this project builds a reviewer around one.",
        "**Why the results cannot be compared directly.** The evaluations differ in language, in the origin of the data (real "
        "projects labelled from CVE records against generated code with injected patterns), in class balance (1.26 % against 8.35 % "
        "vulnerable) and in test protocol; Chapter 8 repeats this caution beside the numbers.")


def sec_related(d):
    d.h2("Related Work")
    d.h3("Automated pull-request review")
    d.paras(
        "Zhang et al. [2] present Sphinx, a framework for LLM-based pull-request review. They argue that existing review data are "
        "noisy because they come from human-written comments, that many methods treat a pull request as an isolated diff and ignore "
        "its context, and that BLEU and ROUGE scores do not show whether a review finds the substantive issues. Sphinx therefore "
        "(i) generates review comments by comparing a pseudo-modified solution, synthesised from the pull request's intent, with the "
        "code that was actually merged, (ii) evaluates a review with a checklist of verification points derived from the structured "
        "diff, and (iii) trains models with Checklist Reward Policy Optimization, a reinforcement-style method whose rewards come from "
        "the checklist. The abstract reports that models trained with Sphinx outperform proprietary and open-source baselines by up to "
        "40 % in checklist coverage. The paper supports two design choices here: reviews should be grounded in the changed code and its context, and "
        "evaluation should count issues found, not words that overlap. It differs in method (Sphinx trains an LLM; this project "
        "analyses code with rules and metrics) and in evaluation data, which this project does not have.",
        "Four further papers in the batch survey concern learned vulnerability detection and repair: a CNN-LSTM hybrid model for "
        "vulnerability detection (2025) [3]; real-time AI code-security auditing with automated detection and remediation (2025) [4]; a "
        "multi-modal framework that combines code simplification and meta-learning (2025) [5]; and DcodeBERT for automatic "
        "vulnerability detection and repair (2024) [6]. Their titles show a move towards deep and transformer models and towards joining detection with repair; their methods "
        "and results were not read and are not summarised.")
    d.h3("Vulnerability prediction from metrics and text")
    d.paras(
        "Shin and Williams [8] ask whether models designed for fault prediction can predict vulnerabilities, and use complexity "
        "metrics for the purpose; the base paper summarises their JavaScript study as having a low false-positive rate but a relatively "
        "high false-negative rate [1]. The base paper also reviews work that combined code complexity, code reduction and development "
        "metrics (about 80 % recall with a 52 % false-positive rate), that adapted fault predictors to Firefox versions (about 70 % "
        "accuracy), and that applied logistic regression to Windows Vista code (about 60 % accuracy) [1]. Generic metric models thus carry a real but modest signal, which is why the base paper selects its metrics "
        "systematically and balances the classes.",
        "Shahriar and Zulkernine [7] and Hanif et al. [14] survey approaches and taxonomies for vulnerability detection and prediction; "
        "Chernis and Verma [9] study machine-learning methods for the task. Yamaguchi et al. [10] use abstract syntax trees to "
        "extrapolate known vulnerabilities to similar code, which is close in spirit to the AST analysis used here.")
    d.h3("Deep-learning detectors")
    d.paras(
        "Russell et al. [11] learn representations of source code for vulnerability detection, VulDeePecker [12] is a deep-learning "
        "system for the same purpose, and VUDENC [13] applies deep learning to a natural code base for Python. The base paper adds "
        "a summary of statement-level neural detectors, recurrent networks for C and C++, and SecureQwen, a decoder-only LLM trained on "
        "about 1.9 million Python function snippets that classifies fourteen weakness types with F1-scores between 84 % and 99 % [1]. "
        "These detectors need large labelled corpora and much computation and explain little; the cheaper, interpretable metric "
        "approach of the base paper is the basis of the ML agent here.")
    d.table([["Work", "Approach", "Data", "Reported result", "Limitation relevant here"],
             ["Abbasi and Shameli-Sendi [1] (base)", "14 code-property-graph metrics, 7 selectors, SmoteTomek, 9 classifiers", "21,759 C/C++ functions, 275 vulnerable", "Random Forest: accuracy 0.96, F1 0.961", "C/C++ only; offline; no explanation or fix"],
             ["Zhang et al. [2] (Sphinx)", "Pseudo-modified vs merged code to make review comments; checklist evaluation; CRPO training", "Pull-request data (not detailed here)", "Up to 40 % higher checklist coverage than baselines (abstract)", "Trains an LLM; no static analysis of security flaws"],
             ["Shin and Williams [8], as summarised in [1]", "Complexity metrics to predict vulnerabilities", "JavaScript projects", "Low false-positive, relatively high false-negative rate", "Generic metrics, small signal"],
             ["SecureQwen, as summarised in [1]", "Decoder-only LLM, 64K context", "About 1.9 million Python function snippets", "F1 84 % to 99 % over 14 CWEs", "Needs large data and compute; opaque"],
             ["CNN-LSTM hybrid [3]; AI code auditing [4]; multi-modal meta-learning [5]; DcodeBERT [6]", "Learned detection and repair", "Not retrieved", "Not read", "Not read"]],
            "Summary of the main related works", widths=[0.2, 0.26, 0.17, 0.19, 0.18], font=8.5)


def sec_lit_algorithms(d):
    d.h2("Datasets and Algorithms Used in the Field")
    d.paras(
        "**Datasets.** Vulnerability research uses labelled functions from open-source projects and public vulnerability databases. "
        "The base paper [1] labels functions from ten C and C++ projects with CVE and NVD records; such data are extremely imbalanced "
        "(1.26 % vulnerable) and unsuitable for training a Python reviewer. No equivalent labelled set of Python functions was "
        "available, so a generator that injects eight vulnerability patterns into random Python functions, with look-alike safe code, "
        "supplies the training data (Chapter 6).",
        "**Algorithms.** The table lists the algorithms that recur in the surveyed work, the role they play, and where this project "
        "uses them.")
    d.table([["Algorithm", "Role", "Source", "Used in this project"],
             ["Cyclomatic complexity", "Counts independent paths through a function", "McCabe [21]", "Metric M1 and the complexity quality rule"],
             ["Feature selection by seven methods", "Ranks metrics; consensus keeps the most useful", "Base paper [1]; scikit-learn [20]", "Model Lab and the ML agent's metric set"],
             ["SMOTE", "Creates synthetic minority samples between neighbours", "Chawla et al. [15]", "Implemented in `mlmodel.py`"],
             ["Tomek links", "Removes majority samples that form a boundary pair with a minority sample", "Tomek [16]; Batista et al. [17]", "Applied after SMOTE"],
             ["Random Forest", "Ensemble of decision trees, robust to noisy metrics", "Breiman [18]", "Stored for importances; best AUC of the single models"],
             ["Gradient boosting, XGBoost", "Boosted trees", "Chen and Guestrin [19]", f"XGBoost is the stored model"],
             ["AST and taint analysis", "Follows untrusted data from sources to sinks", "Yamaguchi et al. [10] (AST use)", "`rules.py`: 30 security rules"],
             ["TF-IDF", "Weights terms by informativeness", "Salton and Buckley [22]", "Repository retrieval"],
             ["Personalised PageRank", "Spreads relevance over a graph from seed nodes", "Page et al. [23]", "Boosts code related to the best matches"],
             ["CWE, OWASP Top 10, SARIF", "Names, groups and exchanges findings", "[24]-[26]", "Every finding and the SARIF export"]],
            "Algorithms and standards used", widths=[0.22, 0.31, 0.2, 0.27], font=9)


def sec_lit_strengths(d):
    d.h2("Strengths and Limitations of Existing Approaches")
    d.table([["Approach", "Strengths", "Limitations"],
             ["Manual review", "Understands design intent and context", "Slow, inconsistent, depends on the reviewer's security expertise"],
             ["Rule-based static analysers", "Precise on known patterns; fast; explainable", "Many warnings with little context; blind to patterns not in the rules"],
             ["Metric-based machine learning [1], [8]", "Interpretable, cheap, finds risky functions without a rule for each flaw", "Needs labelled data; reported only offline and for C/C++; gives no explanation of its own"],
             ["Deep and transformer detectors [3], [5], [6], [11]-[13]", "Learn features automatically; can reach high scores on large data", "Large data and compute; opaque; the surveyed papers were evaluated on their own corpora"],
             ["LLM review generation [2]", "Fluent, contextual comments", "Evaluation by text overlap is misleading; comments can be shallow or unsupported; training needs reward design"],
             ["Combined, agentic pipelines (this project)", "Independent evidence that can be cross-checked; explanations and verified patches", "More components to test; the quality of the learned part depends on the data; real-world precision unmeasured here"]],
            "Strengths and limitations of the approaches", widths=[0.27, 0.36, 0.37], font=9.5)
    d.p("No single approach covers detection, explanation, repair and context. Interpretable metrics carry a signal [1] and automatic "
        "reviews need structured evaluation [2]; both point to a pipeline that combines several kinds of evidence and reports how each "
        "was measured.")


def sec_gap(d):
    d.h2("Research Gap")
    d.paras(
        "The surveyed work predicts vulnerabilities from code metrics offline. The gap is applying that signal inside the live pull-request "
        "workflow, combined with agentic review that explains each finding. Five more specific gaps follow from the survey.")
    d.table([["Gap found in the literature", "How this project addresses it", "Evidence in this report"],
             ["Metric-based prediction is evaluated offline on finished projects, not on pull requests [1]", "The ML Risk Agent scores the functions touched by a diff and feeds its evidence to the Reasoner and the Judge", "Review of the demo pull request; Chapter 8"],
             ["The metric method is limited to C and C++ and names Python and Java as future work [1]", "14 Python AST metrics, three of them new, and a Model Lab that reproduces the pipeline", "Model results on the generated corpus; Chapter 6"],
             ["A learned score alone gives no explanation, impact or fix", "A rule knowledge base, taint evidence, impact text and patches that are re-scanned", "Verified patches on the demo pull request"],
             ["Warning lists lack context and prioritisation", "De-duplication, severity-and-confidence scoring, and a verdict", "Risk-score formula and verdicts, Chapter 6"],
             ["Review automation is hard to evaluate; text-overlap scores mislead [2]", "Detection measured by counts of true and false positives against labelled functions; stated limits of the evidence", "Engine against model against both, Chapter 8"],
             ["Reviewers lack code-base context when judging a small diff", "A repository assistant with cited answers, a map and an onboarding guide", "Twelve-question retrieval check, Chapter 8"]],
            "Research gaps and how they are addressed", widths=[0.36, 0.38, 0.26], font=9.5)
    d.p("The gaps are addressed to different degrees: the pipeline, the metric set and the detectors are built and measured on generated "
        "data, while a labelled set of real pull requests remains future work.")
