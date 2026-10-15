"""Chapter 8 content: output screens, measured results, comparison with the base paper, failure analysis, objectives."""
from __future__ import annotations

from doc_common import CATS, CHARTS, CLAIM_LABELS, CONFUSION, EXP, POLICIES, RETR, RUNS, SHOTS

# (file, caption, what it shows)
MAIN_SCREENS = [
    ("01_landing.png", "Landing page", "The public home page: the headline \"Understand your health insurance, clause by clause\", a sample question about cataract surgery answered with a cited clause and the badge \"Supported by the cited clause\", and the buttons Get started and Try the demo."),
    ("04_dashboard.png", "Dashboard", "Counters for policies (4 ready), questions asked (4), average faithfulness (73/100 over the three answers of this live session that were scored), median response time (5.9 s), claim checks (2) and high risks (9), the 14-day activity chart, and the faithfulness distribution of the answers asked so far."),
    ("05_policies.png", "My policies", "The library with the four sample policies, each tile showing its status, UIN, key values from the Policy Card (sum insured, pre-existing and specific-disease waiting periods, co-payment), the number of high and medium risks and the number of clauses."),
    ("06_policy_card.png", "Policy Card", "The Star Health Family Health Optima card: type, UIN, the share of values verified in the text (91%), a plain-language overview, the people it suits, what to watch out for and recommended next steps; the waiting periods and other values follow below, each with a clause and page chip."),
    ("07_policy_risks.png", "Risk highlights", "Nine risks for the Star Health wording (3 high, 6 medium), each with its category, the source (rule check or AI), an explanation, the quoted wording and the clause and page chip: the 20% co-payment from age 61, the room-rent limit with proportionate deduction and the three-year pre-existing-disease wait."),
    ("08b_policy_document_highlight.png", "Original document with the cited clause highlighted", "Page 28 of the original wording with the clause Excl02 (specified disease and procedure waiting period) outlined in yellow; the side panel shows the selected clause, its section path and text, and the other clauses on the page."),
    ("09_clause_search.png", "Clause search", "Hybrid search with re-ranking for \"cataract waiting period\": eight clauses, the timings of each stage (BM25 2 ms, dense 20 ms, fusion 0 ms, re-rank 1.0 s), and for each result its keyword rank, semantic rank and relevance with the matching words highlighted."),
    ("11_chat_answer.png", "Cited answer", "The answer to \"Is cataract surgery covered and after how long?\": covered after a 24-month specified-disease waiting period, with per-eye limits; two source chips (Clause 2, page 10; Clause Excl02, page 28), the badge Faithfulness 88, the response time 6.2 s, the model used and three follow-up questions."),
    ("11d_chat_not_in_policy.png", "Out-of-scope question declined", "\"Does this policy insure my house against fire?\" is answered \"Not covered in this policy document - I couldn't find any clause about it\" in 1.7 s, with no sources and no model call."),
    ("12_chat_citation.png", "Citation sheet", "Clicking a source chip opens the cited page of the original policy with the clause outlined, and the quoted text at the top."),
    ("13_chat_hindi.png", "Hindi answer", "A question about the room-rent limit asked in Hindi is answered in Hindi with four source chips, faithfulness 92 and the link Show in English."),
    ("15_claim_treatment_step.png", "Claim Copilot: treatment step", "Step 2 of the four-step wizard (Policy, Treatment, Details, Review) with quick picks (Knee replacement, Cataract surgery, Dengue hospitalisation and others), the type of admission, and the list of previous checks."),
    ("16_claim_result_partly.png", "Claim check: partly covered", "Knee replacement under the Star Health policy, cover from 1 October 2023, age 64: partly covered because the waiting periods have passed but a mandatory 20% co-payment applies from age 61; the eligibility pre-checks are marked Calculated and each carries its clause and page."),
    ("17_claim_result_not_covered.png", "Claim check: not covered", "The same treatment with cover from 1 April 2026: not covered because the 24-month specific-disease waiting period has not been completed (6 months of cover, 18 more to go)."),
    ("19_compare_result.png", "Plan comparison", "Star Health Family Health Optima against HDFC ERGO Optima Secure: an overview, the risk counts of each policy, \"choose A if / choose B if\" lists and the start of the side-by-side table."),
    ("20_model_performance.png", "Model performance", "The public page of measured results from run eval-20260922-0027: retrieval hit@5 100%, answer accuracy 100%, citation accuracy 100%, faithfulness 87.0/100, abstention 100%, median answer 4.3 s, card extraction 98.1%, claim verdicts 100%, and the retrieval ablation chart."),
]
EXTRA_SCREENS = [
    ("02_login.png", "Sign in", "The sign-in form with the e-mail and password fields.", None),
    ("10_chat_policy_picker.png", "Ask your policy: choose a policy", "The start of a conversation: the user picks which of the four policies the answers must come from.", None),
    ("21_settings.png", "Settings", "The answer language (English, Hindi, Telugu), the appearance (light, dark, system) and the account: name and password change.", None),
    ("03_register.png", "Create account", "The registration form (name, e-mail, password with the stated rule).", None),
    ("04b_dashboard_full.png", "Dashboard (full page)", "The whole dashboard including the answer faithfulness chart and the latest activity.", 7.2),
    ("06b_policy_card_full.png", "Policy Card (full page)", "The complete card: waiting periods, benefits, sub-limits, exclusions and claim deadlines, each with a clause and page chip.", 7.6),
    ("07b_policy_risks_full.png", "Risk highlights (full page)", "All nine risks of the Star Health wording.", 7.6),
    ("08_policy_document.png", "Original document viewer", "The viewer on the page of a cited clause before scrolling: page navigation, zoom, the selected clause and the clauses on the page.", None),
    ("11c_chat_copay.png", "Co-payment answer (weak support score)", "The answer to \"Is there a co-payment in this policy?\" received a faithfulness score of 38 in this run (99 in an earlier run of the same question), an example of the variability of the score discussed in Section 8.7.", None),
    ("14_claim_policy_step.png", "Claim Copilot: policy step", "Step 1: choose the policy to claim under.", None),
    ("16b_claim_result_partly_full.png", "Claim check, partly covered (full page)", "The complete plan: reasons, pre-checks, estimated split of the bill, document checklist and claim steps.", 7.6),
    ("17b_claim_result_not_covered_full.png", "Claim check, not covered (full page)", "The complete plan for the failed waiting period.", 7.6),
    ("18_compare_form.png", "Compare plans: form", "Choose two policies, swap them and choose the answer language.", None),
    ("20b_model_performance_full.png", "Model performance (full page)", "All charts of the measured-quality page.", 7.6),
    ("22_chat_dark.png", "Dark theme", "The cited answer in the dark theme.", None),
    ("22b_policy_card_dark.png", "Policy Card, dark theme", "The Policy Card in the dark theme.", None),
    ("25_card_telugu.png", "Policy Card translated to Telugu", "The card in Telugu. The third \"Suits\" line contains Bengali and Gurmukhi script mixed into the Telugu text and several terms stay in English in brackets; this is a known limitation of the translation step.", None),
]
SCREENS = [(f, c, t) for f, c, t in MAIN_SCREENS] + [(f, c, t) for f, c, t, _ in EXTRA_SCREENS] + [
    ("23_mobile_chat.png", "Phone layout: chat", "The cited answer at 390 px width."),
    ("24_mobile_policy_card.png", "Phone layout: Policy Card", "The Policy Card at 390 px width.")]


def sec_screens(d, all_screens=False):
    d.h2("Output Screens")
    d.p("Every screen below is a real capture of PolicyLens running with real data on 15 October 2026: the four sample policy wordings, "
        "answers produced by live Gemini calls, and claim checks and a comparison created through the application. The captures are 1440 by "
        "900 pixels unless stated.")
    for f, cap, text in MAIN_SCREENS:
        d.figure(SHOTS / f, cap, width=5.3)
        d.p(text, size=10.5, line=1.3)
    if all_screens:
        d.h3("Additional screens")
        extra_block(d)


def extra_block(d):
    """Additional screens in side-by-side pairs, each pair followed by one line per screen."""
    small = [e for e in EXTRA_SCREENS if e[3] is None]
    tall = [e for e in EXTRA_SCREENS if e[3] is not None]
    for group, width, mh in ((small, 3.15, 2.2), (tall, 2.9, 6.3)):
        for i in range(0, len(group), 2):
            pair = group[i:i + 2]
            d.figure_pair([(SHOTS / f, cap) for f, cap, _t, _m in pair], width=width, max_h=mh)
            for f, cap, text, _m in pair:
                d.p(f"**{cap}.** {text}", size=10.5, line=1.25)
    d.figure_pair([(SHOTS / "23_mobile_chat.png", "Phone layout: cited answer (390 px)"),
                   (SHOTS / "24_mobile_policy_card.png", "Phone layout: Policy Card (390 px)")], width=2.5, max_h=4.4)


def sec_engine_results(d):
    d.h2("Model Performance")
    d.p("PolicyLens trains no model, so there are no accuracy curves, confusion matrices of a classifier or F1 scores of a trained network. The "
        "evaluation measures the pipeline that PolicyLens actually runs, on the hand-built set described in Chapter 6, with the product's "
        "own code. All figures below come from run **eval-20260922-0027** (22 September 2026). During this run the free-tier quota of the "
        "two larger Gemini models was used up, so every answer, claim check and Policy Card came from `gemini-3.5-flash-lite`, the smallest "
        "model in the chain.")
    d.table([["Measure", "Result"],
             ["Retrieval: relevant clause in the top 5 (hybrid + re-rank)", "**100%** (51 / 51)"],
             ["Retrieval: relevant clause ranked first", "**80.4%** (hit@1 0.804, MRR@10 0.897)"],
             ["Answer accuracy (every key fact present)", "**100%** (51 / 51)"],
             ["Citation accuracy", "**100%** (51 / 51)"],
             ["Faithfulness score, mean / median", "**87.0 / 91.7** (56 answers scored)"],
             ["Out-of-scope questions declined", "**100%** (6 / 6), **0** false abstentions on 51 answerable questions"],
             ["Hindi / Telugu answers in the requested script with all key facts", "**5 / 5**"],
             ["Claim Copilot verdict accuracy", "**100%** (14 / 14)"],
             ["Policy Card extraction accuracy", "**98.1%** (51 / 52); 96.9% of values have a verified source quote"],
             ["Answer time, median / 95th percentile", "**4.3 s / 18.2 s**"]],
            "Headline results (run eval-20260922-0027)", widths=[0.55, 0.45], font=10)
    d.figure(CHARTS / "headline_metrics.png", "Headline results of the evaluation run", width=4.5)
    d.h3("Retrieval")
    rows = [["Method", "hit@1", "hit@3", "hit@5", "MRR@10", "recall@5", "median ms"]] + [[m, f"{a:.3f}", f"{b:.3f}", f"{c:.3f}", f"{e:.3f}", f"{f:.3f}", f"{g}"] for m, a, b, c, e, f, g, _ in RETR]
    d.table(rows, "Retrieval on 51 answerable questions", widths=[0.3, 0.11, 0.11, 0.11, 0.12, 0.13, 0.12], font=9.5, align=["l"] + ["c"] * 6)
    d.figure(EXP / "retrieval_ablation.png", "Retrieval ablation (hit@1, hit@3, hit@5, MRR@10) for the four methods", width=4.7)
    d.bullets([
        "**Keywords matter in policies.** BM25 alone already finds the clause in the top 5 every time, because questions and clauses share exact terms (\"cataract\", \"ambulance\", \"free look\").",
        "**Embeddings alone are weakest.** Policy clauses are formulaic and look alike to a general-purpose embedding model; dense search misses one question in five at rank 5 (hit@5 0.804). It still helps fusion with paraphrased questions.",
        "**The re-ranker makes the difference at the top.** Reading question and clause together lifts hit@1 from 0.686 (fusion) to 0.804 and MRR@10 from 0.795 to 0.897, at a cost of about 0.9 s on the CPU, the largest part of retrieval time.",
    ])
    d.h3("Answers, citations and faithfulness")
    rows = [["Category", "Questions", "Correct"]] + [[c, str(n), str(n)] for c, n in CATS] + [["**Total**", "**51**", "**51**"]]
    d.table(rows, "Answer accuracy by question category", widths=[0.5, 0.25, 0.25], font=10, align=["l", "c", "c"])
    d.figure(EXP / "answer_accuracy_by_category.png", "Answer accuracy by question category", width=4.3)
    d.p("Of the 56 answers that were scored for faithfulness (the 51 answerable questions and the 5 multilingual ones), 45 are well supported "
        "(80-100), 8 partly supported (50-79) and 3 weakly supported (below 50). All three weakly supported answers were still correct and "
        "correctly cited; they show where the small NLI model struggles: an exclusion-list item that does not itself say \"excluded\" (the heading "
        "above it does), a rule stated as the inverse of an exclusion, and a defined term replaced by its abbreviation.")
    d.figure(EXP / "faithfulness_distribution.png", "Distribution of faithfulness scores (56 answers)", width=4.3)
    d.p("Adding the clause heading to the evidence lifted the first kind of case (0.003 to 0.92) but also let the model confirm a wrong "
        "statement about an exception (\"ectopic pregnancy treatment is excluded\" scored 0.87 against a clause that excepts it). That change was "
        "therefore not adopted: a faithfulness score should err towards caution. It is shown next to every answer as a prompt to open the "
        "cited clause, not as a verdict.")
    d.h3("Knowing when to say \"not covered in this policy\"")
    d.table([["", "Best re-rank score", "Best BM25 score"],
             ["Out-of-scope questions (6)", "at most 0.0029", "at most 7.3"],
             ["Answerable questions (51)", "as low as 0.0020", "as low as 7.1"],
             ["Answerable with re-rank < 0.004 (3)", "0.0020-0.0021", "15.5 or more"]],
            "Scores used by the abstention rule", widths=[0.4, 0.3, 0.3], font=10, align=["l", "c", "c"])
    d.p("Neither score separates the two groups alone, but the pair does: answering \"not covered\" without a model call only when the re-rank "
        "score is below 0.004 **and** the BM25 score is below 9.0 declined 6 of 6 out-of-scope questions and none of the 51 answerable ones.")
    d.h3("Response time")
    d.table([["Stage", "Median", "95th percentile"],
             ["Retrieval (BM25 + dense + fusion + re-rank)", "0.86 s", "1.8 s"],
             ["Gemini answer", "2.5 s", "17.2 s"],
             ["Faithfulness (NLI)", "0.83 s", "1.7 s"],
             ["**Total**", "**4.3 s**", "**18.2 s**"]],
            "Answer time by stage (live Gemini calls)", widths=[0.5, 0.25, 0.25], font=10, align=["l", "c", "c"])
    d.figure(EXP / "latency_by_stage.png", "Median and 95th-percentile time by stage", width=4.3)
    d.p("The long tail comes from the fallback chain: when the primary models answer \"quota exceeded\" or \"overloaded\", the request moves to the "
        "next model and that wait is included. Claim Copilot checks take longer (one larger Gemini call plus retrieval for several queries): "
        "a mean of 13.8 s on four timed live calls.")
    d.h3("Claim Copilot")
    rows = [["expected \\ predicted"] + CLAIM_LABELS] + [[CLAIM_LABELS[i]] + [str(v) for v in CONFUSION[i]] for i in range(4)]
    d.table(rows, "Claim verdicts: expected (rows) against predicted (columns), 14 scenarios", widths=[0.28, 0.18, 0.18, 0.18, 0.18], font=10, align=["l", "c", "c", "c", "c"])
    d.figure(CHARTS / "claims_confusion.png", "Claim Copilot confusion matrix", width=3.4)
    d.p("Precision, recall and F1 are 1.0 for every verdict. The reasons behind the verdicts have a mean faithfulness of 82.7, and each check lists "
        "7.3 documents and 4.3 claim steps on average. Waiting periods, age-based and network co-payments, sub-limits and the cost estimate are "
        "calculated by rules from the Policy Card, not generated, and a failed waiting period always yields \"not covered\".")
    d.h3("Policy Card extraction")
    rows = [["Policy", "Values checked", "Correct"]] + [[p[0], p[11].split("/")[1], p[11].split("/")[0]] for p in POLICIES]
    d.table(rows, "Policy Card values by policy (52 hand-checked values)", widths=[0.5, 0.25, 0.25], font=10, align=["l", "c", "c"])
    d.figure(EXP / "extraction_accuracy_by_field.png", "Extraction accuracy by field", width=4.3)
    d.p("The single difference is the cumulative bonus of the HDFC ERGO wording, and it is an ambiguity in the document rather than a misreading: "
        "the wording covers seven plan variants (10% a year for Optima Suraksha and Optima Lite, 25% for Optima Select, none for Optima Secure, "
        "which instead grows cover by 50% a year through its Plus Benefit). The reference value takes the general clause (10%); the card "
        "reports the Optima Secure figure (50%, up to 100%). Letting the user pick the plan variant on the card is the planned fix.")


def sec_product_results(d):
    d.h2("Improvement Across the Three Runs")
    d.p("Three evaluation runs are kept in `experiments/`. Each fixed what the previous one revealed.")
    d.table([["Run", "Change", "hit@5", "Answer acc.", "Citation acc.", "False abstentions", "Claim verdicts"]] + [list(r) for r in RUNS],
            "Evaluation runs", widths=[0.17, 0.35, 0.08, 0.1, 0.1, 0.1, 0.1], font=8.5)
    d.figure(CHARTS / "improvement_runs.png", "Retrieval, answer and citation accuracy across the three runs", width=4.5)
    d.p("The first run's errors were of two kinds: the system answered \"not covered\" for answerable questions (5 false abstentions) and cited "
        "a neighbouring fragment instead of the governing rule. Requiring both a low re-rank score and a low keyword score before abstaining, and "
        "sending a rule together with the tables it governs, removed most of them. The remaining errors came from list items that carry an "
        "IRDAI exclusion code, which the segmenter had merged into one clause; making each its own clause removed them. Because these fixes "
        "were made by studying failures on the evaluation set itself, the final figures are optimistic.")


def sec_comparison(d):
    d.h2("Comparison with the Base Paper")
    d.p("The base paper [1] summarises Turkish court rulings and reports ROUGE scores; PolicyLens answers questions about English health-insurance "
        "wordings and reports retrieval, citation, faithfulness and verdict measures. **The datasets, the tasks, the languages and the metrics "
        "all differ, so the numbers cannot be compared and no head-to-head claim is made.** What can be compared is the approach.")
    d.table([["Aspect", "Base paper [1]", "PolicyLens"],
             ["Task", "Multi-document summarisation", "Cited question answering, claim guidance, comparison"],
             ["Documents", "2,000 Turkish court rulings (consumer-rights cases)", "4 English health-insurance wordings (166 pages, 801 clauses)"],
             ["Selection step", "TF-IDF and TextRank sentence extraction", "BM25 + dense retrieval, fusion and cross-encoder re-ranking, measured"],
             ["Generation", "LED, Long-T5, BART-large, GPT-3.5 Turbo", "Gemini with a JSON schema and tagged clauses"],
             ["Training", "Models fine-tuned for summarisation", "None; pre-trained models only"],
             ["Metric", "ROUGE-1 55%, ROUGE-2 35%, ROUGE-L 42% (best model); content F1 0.47 (TF-IDF)", "hit@5 100%, answer accuracy 100%, citation accuracy 100%, faithfulness 87.0, verdicts 14/14"],
             ["Support for statements", "Not measured; no citations", "Citations to clause and page; NLI faithfulness score"],
             ["Language", "Turkish", "English documents; English, Hindi, Telugu interaction"]],
            "PolicyLens and the base paper", widths=[0.2, 0.38, 0.42], font=9)
    d.p("The closest quantitative point of comparison is the policy-document RAG study [6], which reports faithfulness of 0.347 (plain LLM), "
        "0.621 (basic RAG) and 0.797 (RAG with a cross-encoder) with a different model, a different corpus (public-health guidance) and a "
        "different faithfulness measure. PolicyLens's mean faithfulness of 87.0 out of 100 is on its own NLI-based scale and is not comparable "
        "with those values either; the shared observation is that two-stage retrieval with re-ranking is what makes grounded answers reliable.")


def sec_samples(d):
    d.h2("Sample Inputs and Outputs")
    d.table([["Input", "Output"],
             ["Question: \"Is cataract surgery covered and after how long?\" (Star Health)", "Covered under the policy, subject to a specified disease/procedure waiting period of 24 months of continuous coverage; expenses for cataract are subject to limits per eye and per policy period depending on the sum insured. Sources: Clause 2 (p. 10), Clause Excl02 (p. 28). Faithfulness 88."],
             ["Question: \"Does this policy insure my house against fire?\"", "\"Not covered in this policy document - I couldn't find any clause about it. You may want to confirm with the insurer.\" No sources; 1.7 s."],
             ["Claim: knee replacement, planned, cashless, cover from 2023-10-01, age 64, Rs. 3,50,000", "Partly covered: waiting periods complete (36 months of cover); mandatory 20% co-payment from age 61; document checklist and claim steps; estimated split of the bill."],
             ["Claim: knee replacement, cover from 2026-04-01, age 45", "Not covered: the 24-month specific-disease waiting period has not been completed (6 months of cover)."],
             ["Compare: Star Health Family Health Optima and HDFC ERGO Optima Secure", "Overview; 21-row side-by-side table; Policy A better on 0 measurable items, Policy B on 2; choose-A and choose-B lists."]],
            "Sample inputs and outputs (live run, 15 October 2026)", widths=[0.4, 0.6], font=9)


def sec_success_failure(d):
    d.h2("Success and Failure Analysis")
    d.h3("Where it works")
    d.bullets([
        "Every answerable question in the evaluation set was answered correctly and cited correctly; every out-of-scope question was declined.",
        "Every claim scenario received the expected verdict, including the single \"needs information\" case.",
        "The Policy Card is right for 51 of 52 checked values and marks values whose quote it cannot find as unverified.",
        "Hindi and Telugu questions return answers in the requested script with the key facts (5 of 5).",
    ])
    d.h3("Where it fails or is weak")
    d.table([["Observation", "Cause", "Effect / handling"],
             ["Cumulative bonus of the HDFC ERGO card differs from the reference", "The wording covers seven plan variants with different bonuses", "Card reports the Optima Secure figure (50%) while the reference takes the general clause (10%); plan-variant selection is planned"],
             ["Three correct answers scored below 50 for faithfulness", "NLI limits: exclusion item vs heading; inverted rule; abbreviation vs defined term", "Score is shown as a prompt to open the cited clause; the heading-evidence fix was rejected because it confirmed a wrong statement"],
             ["Same co-payment question scored 99.0 and then 37.9", "The score depends on how the model phrases its claims and which windows the NLI model sees", "The score is a heuristic; sources are always shown"],
             ["Telugu card line mixes Bengali and Gurmukhi script; bracketed English terms", "Translation by the smaller model", "Known limitation; English card and citations remain correct"],
             ["Answer time up to 24.8 s", "Fallback chain waits when the larger models are out of quota or overloaded", "Median 4.3 s; the model used is shown"],
             ["Dashboard tiles at 1440 px wrap values and have uneven heights", "Layout of the tiles at that width", "Cosmetic; noted for the next UI pass"]],
            "Failure and weakness analysis", widths=[0.33, 0.33, 0.34], font=8.5)


def sec_results_limits(d):
    d.h2("Limits of the Results")
    d.bullets([
        "**Small set.** 51 answerable questions over four policies. 100% here means no errors were found on this set, not that PolicyLens never errs. Every answer shows its sources and a faithfulness score for that reason.",
        "**Tuned on the same set.** The abstention thresholds and the parsing fixes were made after studying failures on this set, so the final figures are optimistic. The next check is a fresh question set on policy wordings PolicyLens has not seen.",
        "**Model and quota.** The Gemini model used depends on the free-tier quota at the time. The run records which model produced each result; all results here are for the smallest model in the chain.",
        "**One machine, no user study.** All timings are from one desktop; no load testing; no policyholder has rated the answers.",
        "**No numeric comparison with the base paper** is possible, as explained above.",
    ])


def sec_objectives(d):
    d.h2("Objectives Against Outcomes")
    d.table([["Objective", "Outcome", "Evidence"],
             ["1. Extract key policy attributes automatically", "Achieved", "Policy Card with sourced values; 51 of 52 values correct; 96.9% verified in the text"],
             ["2. Build a RAG pipeline that retrieves the relevant clauses", "Achieved", "Hybrid + re-rank: relevant clause in the top 5 for 51 of 51 questions; first for 80.4%"],
             ["3. Generate plain-language answers grounded in and citing the clauses", "Achieved", "Answer accuracy 51/51, citation accuracy 100%; out-of-scope questions declined 6/6"],
             ["4. Provide guided claim support with pre-checks, checklists and steps", "Achieved", "14 of 14 verdicts correct; calculated pre-checks; checklist and steps; cost estimate"],
             ["5. Summarise risks, exclusions and trade-offs to support plan comparison", "Achieved", "Risk highlights with severity (23 across the four samples); 21-row comparison with trade-offs. The comparison quality was not scored against a reference"],
             ["6. Evaluate answer accuracy, faithfulness and response time", "Achieved, with limits", "Measured on a small set partly tuned on itself; faithfulness mean 87.0; median 4.3 s; no user study"]],
            "Objectives against outcomes", widths=[0.4, 0.14, 0.46], font=9)
