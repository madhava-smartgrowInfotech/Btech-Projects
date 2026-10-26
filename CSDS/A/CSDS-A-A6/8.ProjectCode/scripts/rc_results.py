"""Chapter 8 content: output screens, measured results, comparison with the base paper, samples, success and failure analysis, objectives (ClauseGuard).

All numbers come from docs/REPORT_FACTS.md and experiments/*/metrics.json (classification, rules, corpus, parity, api, eval) and from the application database
filled by the three real uploads of 26 October 2026.
"""
from __future__ import annotations

from doc_common import CHARTS, SHOTS, metrics

CL = metrics("classification")
RU = metrics("rules")
CO = metrics("corpus")
PA = metrics("parity")
AP = metrics("api")
EV = metrics("eval")


def pc(x, n=1):
    return f"{x * 100:.{n}f} %"


MAIN_SCREENS = [
    ("01_landing.png", "Landing page",
     "The public home page: the eyebrow \"Contract risk, in plain language\", the headline \"Know what you're signing.\" and the line that ClauseGuard scores contract complexity and flags predatory clauses in plain language, built for Indian agreements. "
     "The buttons Get started and See evaluation results sit under the headline, and four cards describe Upload & segment, Predatory clause detection, Risky combinations and Complexity grade. The navigation bar offers Evaluation, Log in and Sign up and a theme toggle."),
    ("03_register.png", "Sign-up form",
     "The Create your account page with the e-mail neha.legal@example.com typed in, the password masked and the hint \"At least 6 characters\". Registering through this form creates the demonstration user whose uploads appear in the following screens; there is no pre-seeded account."),
    ("06_upload_file_selected.png", "Upload page with a file selected",
     "The signed-in user (Neha Legal) has chosen freelance_services_agreement.docx (37 KB). The file chip shows the name and size with a remove button, and the Analyse contract button is now enabled. The note under the button says the file is read for analysis and removed from the server afterwards."),
    ("07_upload_analysing.png", "Analysis in progress",
     "About two and a half seconds after pressing Analyse contract the button reads Analysing... and is disabled, and the progress bar is at its start. The real analysis of this file took 113.6 s (11 embeddings, 8 flag explanations and one summary through Gemini), so the page stays in this state for nearly two minutes."),
    ("08_report_freelance_top.png", "Contract report: one-sided freelance agreement",
     "The report opens with the file name, \"Uploaded 26 Oct 2026, 07:58 pm - 11 clauses\" and the grade badge B. Six tiles give complexity grade B (score 23.3), readability 39.8 (Flesch), legalese density 0.7 % per 100 words, 0 cross-references, average sentence length 16.2 words and 8 flagged clauses out of 11. "
     "The plain-language summary calls the terms \"highly lopsided\" and lists termination without notice, daily penalties, a three-year non-compete across India, unlimited liability, total IP assignment, a one-sided arbitration and automatic renewal. The bar chart counts clauses by highest severity: 4 high, 4 medium, 0 low and 3 with no flag."),
    ("09_report_freelance_clauses.png", "Obligations and risky combinations",
     "The same report scrolled: seven key obligations extracted by Gemini (for example \"Pay a penalty of Rs. 25,000 per day for any delivery delays\") and the panel Risky clause combinations with three explanations: termination at will plus no refund plus penalty, non-compete plus unlimited liability, and automatic renewal plus one-sided termination. The first rows of the clause table begin below."),
    ("11_clause_detail_termination.png", "Clause detail: unilateral termination",
     "Clause 2 (page 1) is classified as Termination For Convenience with 79 % confidence by the embedding method. The Flags tab shows a High flag Unilateral Termination with the section Why it is flagged (an at-will termination lacks the mutuality expected under Indian contract principles), the Provision quoted from the clause (\"The Company may terminate this Agreement at any time, without cause or notice, at its sole discretion ...\") and a green Safer wording box proposing termination by either party on 30 days' written notice with compensation for work done."),
    ("12_clause_detail_penalty.png", "Clause detail: penalty versus liquidated damages",
     "Clause 4 is labelled Liquidated Damages with 75 % confidence. The Medium flag Penalty vs Liquidated Damages explains that a sum payable \"irrespective of the actual loss suffered\" is a penalty under Section 74 of the Indian Contract Act, quotes that phrase as the provision and proposes wording that calls the sum liquidated damages, a genuine pre-estimate, subject to a reasonable cap and a duty to mitigate."),
    ("14_clause_graph.png", "Clause graph",
     "Eleven nodes, one per clause, each labelled with its clause type. Red nodes (8) triggered a rule and violet nodes (3: Ip Ownership, Governing Law and Non-Disparagement) did not; orange lines join clauses that belong to a risky combination, for example the Termination node with the two Liquidated Damages nodes and with Renewal Term. "
     "The right-hand panel \"Risky combinations found\" repeats the three combination explanations; the Selected clause card asks the user to hover or focus a node."),
    ("15_report_balanced.png", "Contract report: fair consulting agreement",
     "The fair consulting agreement (8 clauses) receives grade A (score 13.7) with readability 63.4, legalese density 0.4 %, 0 cross-references, average sentence length 10.9 words and 0 flagged clauses; the severity chart has a single grey bar of 8 clauses without a flag. The summary says the contract is \"standard for consulting engagements with no significant flagged risks\"."),
    ("16_report_cuad_pdf.png", "Contract report: real supply agreement (PDF)",
     "A real supply agreement from the CUAD corpus, typeset to a ten-page PDF, gives grade C (score 53.8), readability 26.3, legalese density 1.1 %, 43 cross-references, average sentence length 27.1 words and 1 flagged clause out of 11. "
     "The summary identifies the parties as Fusion and CPDC, mentions product testing, recalls and record keeping and points to the unilateral termination right; the chart shows 1 high-severity clause and 10 without a flag."),
    ("18_upload_wrong_type.png", "Validation error for a wrong file type",
     "After a plain-text file is selected, the upload page shows the red message \"Only PDF and DOCX files are supported. Convert the file and try again.\" under the drop zone, and the Analyse contract button stays disabled (faded). The same rule is enforced again on the server, which answers HTTP 400."),
    ("19_contracts_list.png", "My contracts",
     "The list of the three uploads of the demonstration user, sorted by upload time: supply_agreement_cuad.pdf (grade C, 1 flag, 8:01 pm), balanced_consulting_agreement.docx (grade A, 0 flags, 8:01 pm) and freelance_services_agreement.docx (grade B, 8 flags, 7:58 pm). Rows are clickable and the Upload contract button is at the top right."),
    ("20_evaluation.png", "Evaluation page",
     "The public Evaluation page, captured after the stat counters finished counting: precision 100 %, recall 94 % and F1 97 % \"across 40 curated examples\", \"Run 2026-10-26\", and the per-rule table (Restraint of trade 4 TP / 0 FP / 1 FN, Unilateral termination 6 / 0 / 0, One sided arbitration 1 / 0 / 1 and so on). "
     "The page describes the scores as \"measured on a held-out set\"; Chapter 8 explains why the 40 examples were written by the author of the rules and are better described as a development set."),
]

EXTRA_SCREENS = [
    ("02_landing_how_it_works.png", "Landing page, measured results and how it works",
     "The landing page scrolled: the strip \"Tested on 40 curated Indian-law clause examples - run 2026-10-26\" with precision 100 %, recall 94 % and F1 97 %, and below it the section \"From a contract to a clear answer\" with the four steps (Upload the contract, See the predatory clauses, and two more) and the card for step 1 of 4.", None),
    ("04_login.png", "Log-in form",
     "The Log in page: \"Use the email and password you registered with\", empty e-mail and password fields and a link to Sign up for new users.", None),
    ("05_upload_empty.png", "Upload page before a file is chosen",
     "The Upload a contract page inside the signed-in shell: sidebar with My contracts and Upload contract, the drop zone \"Drop a contract here, or click to browse\", a disabled Analyse contract button and the privacy note.", None),
    ("10_report_freelance_table.png", "Clause table of the freelance agreement",
     "Rows 1 to 7 of the clause table with page, type, a 160-character preview, the number of flags and a risk badge: clause 1 Ip Ownership Assignment (no flag), 2 Termination For Convenience (High), 3 and 4 Liquidated Damages (Medium), 5 No-Solicit Of Customers (High), 6 Cap On Liability (High) and 7 Ip Ownership Assignment (High). The labels for clauses 1, 3, 5 and 6 are not the clauses' real subject.", None),
    ("13_clause_detail_noncompete.png", "Clause detail: restraint of trade",
     "Clause 5 is labelled No-Solicit Of Customers (78 %). The High flag Restraint of Trade / Non-Compete cites Section 27 of the Indian Contract Act, 1872, quotes \"for a period of three years thereafter, the Consultant shall not ... engage in any competing business ...\" and proposes a version limited to non-solicitation of clients and misuse of confidential information for six months.", None),
    ("17_report_cuad_pdf_table.png", "Clause table of the real PDF contract",
     "Rows 1 to 9 of the 11 clauses of the supply agreement with their page numbers (1 to 7). Clause 6 on page 6, Termination For Convenience, carries the only flag (High). Several rows begin with running headers such as \"Supply Agreement - FUSION\" because the PDF text keeps page headers, and five rows are labelled Post-Termination Services.", None),
    ("21_evaluation_lower.png", "Evaluation page, per-rule table and classification",
     "The Evaluation page scrolled: the per-rule table of the 40-clause set and the card CUAD clause classification with Top-1 accuracy 79 % and Top-3 accuracy 98 %, which are the values of the unmodified evaluation script on 240 held-out CUAD spans.", None),
]

KEY_SINGLE = {"08_report_freelance_top.png", "11_clause_detail_termination.png", "14_clause_graph.png", "16_report_cuad_pdf.png", "20_evaluation.png"}
SCREENS = [(f, c, t) for f, c, t in MAIN_SCREENS] + [(f, c, t) for f, c, t, _ in EXTRA_SCREENS]
_ORDER = sorted(SCREENS, key=lambda s: s[0])


def sec_screens(d, all_screens=False):
    d.h2("Output Screens")
    d.p("Every screen below is a real capture of ClauseGuard running with real data on 26 October 2026: a user registered through the sign-up page, three contracts uploaded through the upload page and analysed by the real "
        "pipeline (the embedding model `gemini-embedding-001` and the text model `gemini-3.1-flash-lite` through the Gemini API), and the Evaluation page reading the metrics file written by the evaluation script. "
        "Two of the three contracts are invented for this project and one is a real public contract from the CUAD corpus. The captures are viewport screenshots of 1440 by 900 pixels taken with Playwright in Chrome.")
    pending = []

    def flush():
        for i in range(0, len(pending), 2):
            pair = pending[i:i + 2]
            d.figure_pair([(SHOTS / f, cap) for f, cap, _t in pair], width=3.15, max_h=2.2)
            for f, cap, text in pair:
                if getattr(d, "report", False):
                    cut = text.find(". ", 160)
                    text = text[:cut + 1] if cut > 0 else text
                d.p(f"**{cap}.** {text}", size=10.5, line=1.25)
        pending.clear()

    for f, cap, text in MAIN_SCREENS:
        if f in KEY_SINGLE:
            flush()
            d.figure(SHOTS / f, cap, width=4.4)
            d.p(text, size=10.5, line=1.3)
        else:
            pending.append((f, cap, text))
    flush()
    if all_screens:
        d.h3("Additional screens")
        extra_block(d)


def extra_block(d):
    """Additional screens in side-by-side pairs, each pair followed by one paragraph per screen."""
    group = EXTRA_SCREENS
    for i in range(0, len(group), 2):
        pair = group[i:i + 2]
        d.figure_pair([(SHOTS / f, cap) for f, cap, _t, _m in pair], width=3.15, max_h=2.2)
        for f, cap, text, _m in pair:
            d.p(f"**{cap}.** {text}", size=10.5, line=1.25)


# --------------------------------------------------------------------------------------------------------- model performance
def sec_engine_results(d):
    d.h2("Model Performance")
    d.p("ClauseGuard has two measurable components of its own: a clause classifier (Gemini embeddings and 20 CUAD centroids) and a rule engine (eight regular expressions) with a clause graph and a complexity score. "
        "The text generation by Gemini, which writes the reasons, the safer wording and the summaries, cannot be scored automatically and was not measured. "
        "The two measurable components are evaluated **separately**, as objective 6 requires: classification against CUAD, predatory detection against labelled clauses. "
        "All figures come from `experiments/**/metrics.json`; the classification figures are produced by the unmodified `ml/eval.py` run on embeddings cached from the same Gemini calls the product makes. "
        "The measurements ran on an Intel Core i5-12500 with 15.7 GB of memory and no GPU.")

    d.h3("Clause classification on CUAD")
    c = CL["centroid"]
    d.table([["Measure", "Result"],
             ["Held-out CUAD annotation spans / categories", "240 / 20 (12 per category, seed 42)"],
             ["**Top-1 accuracy** (shipped nearest-centroid classifier)", f"**{c['top1']:.3f}** (190 of 240); {c['top1_without_duplicates']:.3f} after removing the {CL['exact_duplicates_eval_in_train']} spans that also occur in the training set"],
             ["**Top-3 accuracy**", f"**{c['top3']:.3f}** (235 of 240); top-5 {c['top5']:.3f}"],
             ["Top-1 when no training span of the same contract is used", f"{CL['contract_disjoint']['top1']:.3f} ({CL['contract_disjoint']['eval_items_whose_contract_also_in_train']} of 240 spans had a same-contract training span)"],
             ["Chance level", "0.050"]],
            "Clause classification results (unmodified ml/eval.py on cached embeddings)", widths=[0.5, 0.5], font=10)
    b = CL["baselines_top1"]
    d.table([["Method (same train/test split)", "Top-1 accuracy"],
             ["TF-IDF nearest centroid", f"{b['TF-IDF nearest centroid']:.3f}"],
             ["TF-IDF + logistic regression", f"{b['TF-IDF + logistic regression']:.3f}"],
             ["Embedding 1-nearest neighbour", f"{b['Gemini embedding 1-NN']:.3f}"],
             ["Embedding 5-nearest neighbours", f"{b['Gemini embedding 5-NN']:.3f}"],
             ["**Embedding nearest centroid (shipped)**", f"**{b['Gemini embedding nearest centroid (shipped)']:.3f}**"],
             ["Embedding + logistic regression", f"{b['Gemini embedding + logistic regression']:.3f}"]],
            "Shipped classifier against simple baselines", widths=[0.65, 0.35], font=10, align=["l", "c"])
    d.p("The shipped classifier is 12 to 17 points better than the two TF-IDF baselines and much better than a single nearest neighbour, which supports the choice of dense embeddings. A logistic regression on the same embeddings reaches "
        "0.800, two spans more than the shipped method, a difference too small to matter on 240 examples; the nearest-centroid method has the advantage of needing no training beyond averaging. "
        "Scoring the same 240 spans after rebuilding the centroids without any training span from the same contract changes the top-1 value from 0.792 to 0.800, so the span-level split of the shipped script does not inflate the score noticeably.")
    d.figure(CHARTS / "01_classification_per_category.png", "Recall of the classifier for each of the 20 CUAD categories (12 held-out spans each)", width=5.2)
    per = CL["per_category"]
    best = [k for k, v in per.items() if v["recall"] == 1.0]
    d.p(f"Recall is perfect for {', '.join(best[:-1])} and {best[-1]}, which have distinctive vocabulary. It is weakest for Non-Compete (0.50), Cap On Liability (0.50), No-Solicit Of Customers (0.58), Exclusivity (0.67), Liquidated Damages (0.67) and "
        "Uncapped Liability (0.67). The confusions are between neighbouring concepts: Uncapped Liability is read as Cap On Liability (4 spans) and the reverse (3), Non-Compete as No-Solicit Of Customers (4), the two no-solicit categories "
        "with each other (3 and 3), License Grant as Exclusivity (3) and Cap On Liability as Warranty Duration (3).")
    d.figure(CHARTS / "05_confusion_matrix.png", "Confusion matrix of the classifier on the 240 held-out spans (rows are true categories and sum to 12)", width=5.0, max_h=4.6)
    d.p("**The two safeguards of the classifier never act.** The top-1 cosine similarity of the 240 spans lies between 0.657 and 0.849 (median 0.767). The tie-break needs a margin below 0.03 **and** a top-1 similarity below 0.60; the margin test alone "
        "would fire on 152 of the 240 spans, but no span is below 0.657, so the tie-break fires on none. The 'Other / Unclassified' floor at 0.35 is never reached either. With the current embedding model both branches are dead code, and every clause, including "
        "definitions, notices and payment terms that are not among the 20 categories, receives one of the 20 labels. The same holds in the three real uploads: all 30 clauses carry the method `embedding` with a confidence between 0.72 and 0.83.")

    d.h3("Predatory-clause detection")
    s, p = RU["shipped_set"]["overall"], RU["probe_set"]["overall"]
    d.table([["Test set", "Clauses", "TP", "FP", "FN", "Precision", "Recall", "F1"],
             ["Shipped set, written together with the rules", "40", str(s["tp"]), str(s["fp"]), str(s["fn"]), f"{s['precision']:.3f}", f"{s['recall']:.3f}", f"{s['f1']:.3f}"],
             ["Independent probe set (24 predatory paraphrases, 16 benign look-alikes)", "40", str(p["tp"]), str(p["fp"]), str(p["fn"]), f"{p['precision']:.3f}", f"{p['recall']:.3f}", f"{p['f1']:.3f}"]],
            "Rule engine on two test sets", widths=[0.4, 0.09, 0.06, 0.06, 0.06, 0.12, 0.1, 0.11], font=9, align=["l", "c", "c", "c", "c", "c", "c", "c"])
    d.p("The shipped set of 40 clauses gives precision 1.00, recall 0.941 and F1 0.970, the numbers shown on the landing page and the Evaluation page. It was written by the author of the rules, who chose the wording the patterns recognise, so it measures whether the rules "
        "implement the author's intent, not whether they generalise. To test generalisation, 40 further clauses were written for this report after reading the rules: three predatory paraphrases for each rule that avoid the rule's key words, and 16 benign look-alikes. "
        "On this probe set precision falls to 0.786 and recall to 0.458, so the rules find fewer than half of the predatory clauses when the wording changes.")
    d.figure(CHARTS / "03_rules_two_test_sets.png", "Precision, recall and F1 of the rule engine on the shipped set and on the independent probe set", width=4.2)
    d.figure(CHARTS / "04_rule_recall.png", "Recall of each rule on the two test sets (three probe clauses per rule)", width=4.6)
    d.p("Per rule, the probe recall is 0.667 for auto-renewal, IP overreach and unilateral termination and 0.333 for the other five rules. The probe false alarms are instructive: a fair capped liquidated-damages clause is flagged as a penalty; "
        "\"shall not engage in any outside activity that creates a conflict of interest\" is flagged as restraint of trade; and \"both parties shall be liable for any and all losses caused by their own gross negligence\" is flagged as unlimited liability. "
        "The 13 misses are keyword-free paraphrases (for instance \"reserves the right to end this engagement whenever it chooses\" or \"fees once paid cannot be returned for any reason\") and one wording slip: \"shall not be entitled to any refund\" is missed because the pattern reads \"not entitled\".")
    rp = RU["cuad_spans"]["recall_proxy"]
    d.table([["CUAD category", "Closest rule", "Spans", "Rule fires", "Share"]] +
            [[k, v["rule"].replace("_", " "), str(v["n_spans"]), str(v["rule_fires"]), pc(v["rate"])] for k, v in rp.items()],
            "Rules against the closest CUAD categories (a proxy, not a recall)", widths=[0.3, 0.28, 0.12, 0.15, 0.15], font=9.5, align=["l", "l", "c", "c", "c"])
    fp = RU["cuad_spans"]["false_positive_proxy"]
    d.p(f"CUAD offers a second, independent view, with a caveat: its categories describe clause topics, not predatory terms, so the share is a proxy. The penalty rule fires on 56.2 % of the Liquidated Damages spans and the auto-renewal rule on 33.2 % of the Renewal Term spans, "
        f"while the unlimited-liability and IP-overreach rules never fire on the 167 Uncapped Liability and 317 Ip Ownership Assignment spans, whose wording differs from the patterns. On {fp['n_spans']:,} spans of eleven unrelated categories any rule fired on {fp['any_rule_fires']} "
        f"({pc(fp['any_rule_fires'] / fp['n_spans'], 2)}): restraint of trade 14, penalty 12, unilateral termination 10 and no-refund 3.")
    d.figure(CHARTS / "07_cuad_rule_hits.png", "Share of CUAD spans on which the closest rule fires", width=4.6)

    d.h3("Corpus-scale run and the complexity score")
    g = CO["grades"]
    d.table([["Measure", "Result"],
             ["Contracts parsed (segment, rules, combinations, complexity)", f"{CO['parsed']} of {CO['contracts']}"],
             ["Total time / per contract", f"{CO['total_seconds']} s / {CO['mean_seconds_per_contract'] * 1000:.0f} ms"],
             ["Clauses: total, median, mean, min, max", f"{CO['clauses_total']:,}; {CO['clauses_median']}; {CO['clauses_mean']}; {CO['clauses_min']}; {CO['clauses_max']}"],
             ["Contracts split on numbered headings / with fewer than 5 clauses", f"{CO['contracts_with_header_split']} / {CO['contracts_with_fewer_than_5_clauses']}"],
             ["Median clause length", f"{CO['mean_clause_chars_median']:,.0f} characters"],
             ["Clauses flagged / contracts with at least one flag", f"{pc(CO['flagged_clause_share'])} / {CO['contracts_with_any_flag']} of {CO['contracts']}"],
             ["Contracts with a risky combination", f"{CO['contracts_with_combo']} (auto-renewal + unilateral termination {CO['combo_counts']['autorenew_unilateral_termination']}, termination + no-refund + penalty {CO['combo_counts']['termination_norefund_penalty']})"],
             ["Clauses per rule", "restraint 163, penalty 152, unilateral termination 84, no-refund 72, auto-renewal 66, unlimited liability 4, one-sided arbitration 0, IP overreach 0"],
             ["Complexity grades A / B / C / D / F", f"{g['A']} / {g['B']} / {g['C']} / {g['D']} / {g['F']}"],
             ["Complexity score min / median / mean / max / sd", f"{CO['score']['min']} / {CO['score']['median']} / {CO['score']['mean']} / {CO['score']['max']} / {CO['score']['stdev']}"],
             ["Median components: Flesch, legalese per 100 words, cross-references, words per sentence", f"{CO['component_medians']['readability']}, {CO['component_medians']['legalese']}, {CO['component_medians']['xrefs']:.0f}, {CO['component_medians']['avg_sent']}"],
             ["Correlation of score with contract length", f"{CO['corr_score_vs_words']}"]],
            "Non-API pipeline over all 510 CUAD contracts", widths=[0.5, 0.5], font=9.5)
    d.figure(CHARTS / "06_complexity_distribution.png", "Complexity scores of the 510 CUAD contracts with the grade boundaries", width=4.8)
    d.p("The corpus run shows that the local part of the pipeline is fast and does not crash on any of 510 contracts, from a single clause to 611. Real contracts are mostly grades B and C (437 of 510); very few are A or F. "
        "The complexity score is a lexical measure and is only weakly related to length (correlation 0.30). Its weights and cut-offs were chosen by the author and have not been compared with human ratings of difficulty, so the grade is best read as a relative indicator.")

    d.h3("Same contract as DOCX and as PDF")
    f = PA["freelance_services_agreement.docx"]["as_uploaded"]
    g2 = PA["freelance_services_agreement.pdf"]
    d.table([["Input form of the same text", "Clauses", "Rules found", "Combinations"],
             ["DOCX, as uploaded", str(f["clauses"]), "8 of 8", str(len(f["combos"]))],
             ["PDF, as uploaded", str(g2["as_uploaded"]["clauses"]), "6 of 8 (IP overreach and one-sided arbitration missed)", str(len(g2["as_uploaded"]["combos"]))],
             ["PDF, whitespace collapsed before matching", str(g2["whitespace_collapsed"]["clauses"]), "8 of 8", str(len(g2["whitespace_collapsed"]["combos"]))],
             ["Fair DOCX (control)", "8", "0 of 8", "0"]],
            "Effect of the input format on the rule engine", widths=[0.34, 0.12, 0.38, 0.16], font=9.5, align=["l", "c", "l", "c"])
    d.p("PDF extraction keeps the visual line breaks, and several rules use `.{0,N}` between two key phrases, which does not cross a newline. The same contract therefore yields 8 rules as DOCX but only 6 as PDF; collapsing whitespace before matching restores all eight. "
        "The figure for this comparison is given with the testing in Chapter 7.")


def sec_product_results(d):
    d.h2("Results of the Application")
    up = AP["uploads"]
    d.p("The complete product was exercised with three real uploads through the browser. The table summarises what the pipeline returned and how long it took; the individual screens are shown in the section Output Screens.")
    d.table([["Upload", "Clauses", "Flags", "Risky combinations", "Complexity grade (score)", "Time"],
             ["freelance_services_agreement.docx (invented, one-sided)", "11", "8 (one per rule)", "3", "B (23.3)", f"{up['freelance']['seconds']} s"],
             ["balanced_consulting_agreement.docx (invented, fair)", "8", "0", "0", "A (13.7)", f"{up['balanced']['seconds']} s"],
             ["supply_agreement_cuad.pdf (real CUAD contract, 10 pages)", "11", "1", "0", "C (53.8)", f"{up['cuad_pdf']['seconds']} s"]],
            "Real uploads through the web application", widths=[0.36, 0.09, 0.13, 0.12, 0.17, 0.13], font=9, align=["l", "c", "c", "c", "c", "c"])
    d.p("**One-sided contract.** Every rule fired once on the DOCX, each on the intended clause, and the three combinations were found; the report quotes the triggering phrase of each clause and proposes a fairer wording. "
        "The complexity grade is B because the contract is written in plain words (average sentence of 16.2 words, no cross-references); the grade says nothing about fairness. "
        "**Fair contract.** No rule fired and no combination was found; this is the only evidence of the false-positive behaviour on a complete, realistic contract (the CUAD cross-check gives a false-alarm share of 0.74 % on unrelated clause types). "
        "**Real contract.** The real supply agreement is dense (grade C, 43 cross-references, 27.1 words per sentence) and only one termination clause was flagged. With the original CUAD text the same rules find 2 flags (auto-renewal and unilateral termination) and one combination in 25 clauses, "
        "but the typeset PDF changes the segmentation (11 clauses) and the run therefore found fewer; that comparison is not like-for-like and is given only as an illustration of how sensitive the output is to the input form.")
    d.p("**Classification of whole clauses.** In the author's reading, the label shown in the clause table is plausible for 5 of the 11 clauses of the freelance contract (termination, penalty, IP, renewal, governing law) and for 4 of the 8 clauses of the fair contract. "
        "Examples of wrong labels are Scope of Services as Ip Ownership Assignment, Fees as Liquidated Damages, Liability as Cap On Liability (the opposite of an unlimited liability clause), Dispute Resolution as Cap On Liability and Confidentiality as Non-Disparagement. This is lower than the 79 % on spans "
        "because a whole clause carries a heading and several topics, and because the classifier cannot answer 'none of the 20'. The reading covers 19 clauses and is indicative only.")
    d.p("**Responsiveness.** Reading endpoints answer within 20 ms at the median and the report endpoint within 9.3 ms; the bcrypt-based log-in takes about 255 ms. Upload time is dominated by the Gemini calls: 15.5 s with 1 text call, 54.6 s with 2 and 113.6 s with 9. The 180 s timeout of the browser request limits a contract to roughly fourteen flags with this model.")


def sec_comparison(d):
    d.h2("Comparison with the Base Paper")
    d.p("The base paper [1] is SmartLaw Advisor (IEEE Access, 2026), a retrieval-augmented legal assistant for Saudi Arabia built on Gemini 1.5 Flash. ClauseGuard keeps its jurisdiction-aware, LLM-backed idea and applies it to Indian contracts, "
        "but the two systems do different things and are evaluated on different data with different metrics, so **no numerical comparison is made and no superiority is claimed**. The table lists what each reports.")
    d.table([["Aspect", "SmartLaw Advisor [1]", "ClauseGuard (this project)"],
             ["Task", "Legal question answering (chatbot) and contract compliance analysis", "Clause segmentation and classification, predatory-clause flags, risky combinations, complexity grade, plain-language report"],
             ["Jurisdiction and language", "Saudi Arabia, Arabic", "India (rules cite Indian statutes), English"],
             ["Generative model", "Gemini 1.5 Flash (also GPT-4, GPT-3.5, ALLaM, Command-A compared)", "Gemini text model (this run: gemini-3.1-flash-lite) for explanations and summaries; Gemini embedding model for classification"],
             ["Retrieval", "Chroma vector store of Arabic legal chunks, GATE-AraBERT-v1 embeddings, cross-encoder reranking", "No retrieval from a legal corpus; nearest centroid over 20 CUAD categories; the rule's legal basis is placed in the prompt"],
             ["Knowledge base", "Custom Arabic corpus of Saudi regulations validated by legal specialists", "Eight hand-written rules with statute references; CUAD (US filings) for classification"],
             ["Evaluation data", "150 legal questions in ten domains; 50 real contract drafts", "240 held-out CUAD spans; 40-clause shipped set; 40-clause probe set; 510 CUAD contracts (non-API run); three real uploads"],
             ["Headline metric", "Answer accuracy 98.67 % (148 of 150) for Gemini 1.5 Flash; qualitative clause-by-clause review for contract analysis", f"Classification top-1 {CL['centroid']['top1']:.3f} and top-3 {CL['centroid']['top3']:.3f} on CUAD spans; rule precision / recall 1.00 / 0.94 (shipped set) and 0.79 / 0.46 (probe set)"],
             ["Speed reported", "1.63 s average response (baseline); 143.52 s per query in the full RAG evaluation pipeline", "9 ms to 15 ms for reading endpoints; 15.5 s to 113.6 s per upload, dominated by Gemini calls"],
             ["Contract analysis", "Checklist of essential clauses and LLM-assisted semantic compliance check", "Per-clause rule flags with quoted provision and safer wording; three clause combinations; no missing-clause checklist"],
             ["Not addressed", "Clause combinations, complexity scoring, Indian law", "Missing-clause detection, Arabic, retrieval-augmented answers, a legal chatbot"],
             ["Hardware", "Cloud virtual machine (Xeon Platinum 8272CL, 32 GB); Gemini hosted", "Desktop i5-12500, 15.7 GB, no GPU; Gemini hosted"]],
            "SmartLaw Advisor [1] and ClauseGuard side by side (figures are as reported or measured by each)", widths=[0.17, 0.41, 0.42], font=8.5)
    d.p("Three differences deserve emphasis. First, the headline figures measure different things: 98.67 % is the share of 150 Saudi-law questions answered correctly, whereas 79.2 % is the share of CUAD annotation spans assigned to the right one of 20 categories; neither can be read against the other. "
        "Second, the base paper's contract analysis is judged qualitatively on sample outputs, and ClauseGuard's detection is scored with precision and recall against labelled clauses, which is the more checkable of the two but rests on small, author-written sets. "
        "Third, the base paper's data are in Arabic and cover Saudi regulations validated by experts, while ClauseGuard has no Indian-law corpus and no lawyer-labelled contracts; its legal knowledge is eight rules.")
    d.table([["Related work (for orientation)", "Task and data", "Reported result"],
             ["ContractEval [2]", "19 LLMs, CUAD test data, 41 risk categories, span extraction", "F2 of 0.672 and 0.678 for the top two models; proprietary models ahead of open-source ones"],
             ["A few good clauses [3]", "Domain-trained small model against five frontier LLMs, 24 contracts, 508 field instances, 26 targets", "Macro F1 0.812, micro F1 0.842; extraction cost 78 % to 97 % lower"],
             ["Legal document analysis system [4]", "10 clause types, missing-clause detection, weighted risk score, AWS serverless", "94.2 % average extraction accuracy on 20 synthetic contracts; correlation 0.87 between score and expert rating on 30 contracts"]],
            "Related work, results as reported by their authors", widths=[0.24, 0.4, 0.36], font=9)
    d.p("None of these results is comparable with the present figures: ContractEval and [3] extract spans or fields from whole contracts with large models, whereas ClauseGuard classifies given spans with embeddings, and [4] scores missing clauses on synthetic documents. "
        "They are listed to show the kind of evaluation a stronger version of ClauseGuard should adopt: a lawyer-labelled test set of whole contracts, a span-level metric, and an agreement study between the risk score and expert ratings.")


def sec_samples(d):
    d.h2("Sample Inputs and Outputs")
    d.p("The three sample contracts are in `docs/sample_inputs/`; the outputs below are copied from the application database filled by the real uploads. The input is the clause text as segmented by the pipeline, and the flag texts were generated by Gemini.")
    d.table([["Clause (input, shortened)", "Flag and provision quoted", "Reason (generated)", "Safer wording (generated)"],
             ["2. Term and Termination: \"The Company may terminate this Agreement at any time, without cause or notice, at its sole discretion, and the Consultant shall have no right to object ...\"",
              "Unilateral termination (high): \"The Company may terminate this Agreement at any time, without cause or notice, at its sole discretion ...\"",
              "Grants the Company the power to end the contract at once without warning or justification and leaves the Consultant without recourse; such at-will termination lacks the mutuality expected under Indian contract principles.",
              "Either party may terminate by 30 days' written notice; the Consultant is entitled to compensation for services rendered and expenses incurred up to the effective date."],
             ["3. Fees and Payment: \"All payments made under this Agreement are non-refundable under any circumstances, including early termination by the Company ...\"",
              "No refund (medium): \"All payments made under this Agreement are non-refundable under any circumstances ...\"",
              "Prevents recovery of payments even if the company terminates early; may be an unfair trade practice under the Consumer Protection Act.",
              "Fees are payable for services rendered up to termination; on early termination by the Company without cause the Consultant is paid for all work performed and documented expenses."],
             ["4. Delay and Penalty: \"... the Consultant shall pay a penalty of Rs. 25,000 per day of delay, irrespective of the actual loss suffered by the Company ...\"",
              "Penalty vs liquidated damages (medium): \"irrespective of the actual loss suffered by the Company\"",
              "A sum payable irrespective of actual loss is a punitive penalty rather than a genuine pre-estimate; Section 74 of the Indian Contract Act lets courts refuse such clauses.",
              "The same sum as liquidated damages that the parties agree are a genuine pre-estimate, subject to a reasonable cap and a duty to mitigate."],
             ["6. Liability: \"The Consultant shall be liable for any and all losses, damages, claims and expenses ... with no limitation on liability whatsoever.\"",
              "Unlimited liability (high): \"with no limitation on liability whatsoever\"",
              "The Consultant must pay every possible loss without a ceiling, an unbounded and disproportionate financial risk.",
              "Total aggregate liability limited to the fees actually paid in the twelve months before the event giving rise to the claim."]],
            "Sample outputs for the one-sided freelance agreement", widths=[0.28, 0.2, 0.27, 0.25], font=8)
    d.p("The reasons and the provisions are faithful to the clauses in these examples, and the quoted provision is, as the prompt requires, a phrase copied from the clause. Two further examples show the limits. The safer wording for the three-year non-compete (clause 5) keeps a restriction: "
        "it forbids soliciting existing clients and using confidential information for six months after termination, which a lawyer might still question under Section 27. "
        "The report for the real supply agreement flags clause 6 (\"FUSION may terminate this Agreement without cause by providing CPDC with `[***]` prior written notice\") as unilateral termination and says that CPDC has no reciprocal right; "
        "the same contract gives CPDC a right to terminate for cause (clause 7.4), so the statement is true only for termination without cause. The notice period, redacted in the source with the marker `[***]`, is carried into the proposed wording unchanged.")
    d.table([["Contract", "Extract of the generated plain-language summary", "Extract of the key obligations"],
             ["Fair consulting agreement (grade A, 0 flags)", "\"... clarifies that the client owns the finished work once paid for, while you retain rights to your pre-existing tools and templates ... Overall, the contract is standard for consulting engagements with no significant flagged risks.\"",
              "Deliver quarterly sales reports and dashboards as specified in Schedule A; refund any pre-paid fees for work not yet performed if the contract ends early; provide 30 days' written notice if you wish to terminate early."],
             ["Real supply agreement (grade C, 1 flag)", "\"This is a Supply Agreement between Fusion and CPDC for the manufacturing of medical/research products at McMaster University in Canada ... the agreement includes significant unilateral termination rights ...\"",
              "Pay all invoices within the specified timeframe; notify CPDC promptly of any product recall; pay a recurring monthly production standby fee of $45,000."]],
            "Sample summaries", widths=[0.2, 0.46, 0.34], font=8.5)
    d.p("The summary of the real contract is accurate in outline but is framed by the same Indian-law prompt (\"From a risk perspective ...\") even though the contract concerns work at a Canadian university; the tool has no way to detect or change the jurisdiction. "
        "No lawyer reviewed these texts.")


def sec_success_failure(d):
    d.h2("Success and Failure Analysis")
    d.h3("What worked")
    d.bullets([
        "**End-to-end operation.** Three contracts, in two formats and with 8, 8 and 11 clauses, went from the browser to a clause-level report, with every flag tied to the clause text and page, a quoted provision and a safer wording.",
        "**All eight rules fire on a contract that contains them** (DOCX), and all three combinations are found; the fair contract raises no flag.",
        "**Dense embeddings classify CUAD spans well** (top-1 0.792, top-3 0.979) and beat TF-IDF baselines by 12 to 17 points.",
        "**The local pipeline is fast and robust**: 510 real contracts in 28.5 s without a failure.",
        "**The decision is auditable.** Whether a clause is predatory is decided by a regular expression that can be read and tested; Gemini only words the explanation, so the verdict does not change between runs.",
        "**Failures are reported cleanly**: a wrong file type, an empty document, a missing key and a Gemini error each give a specific message and leave no partial record.",
    ])
    d.h3("What failed, and why")
    d.table([["Failure", "Evidence", "Cause"],
             ["Predatory clauses written without the key word are missed", "Probe recall 0.458 against 0.941 on the shipped set; 13 of 24 paraphrases missed", "Rules are keyword regular expressions; the shipped set was written with the same vocabulary"],
             ["PDF input finds fewer flags than DOCX", "6 of 8 rules in the PDF, 8 of 8 in the DOCX with identical text", "PDF text keeps line breaks and `.{0,N}` does not cross a newline"],
             ["Title, parties and recitals disappear", "Test U5: preamble dropped when a page has two or more numbered headings", "Segmenter starts at the first heading"],
             ["Unusual heading styles give few clauses", "84 of 510 CUAD contracts give fewer than 5 clauses", "Only `1.`, `1.1` and `Section 1` style headings are recognised; a clause across a page break is split"],
             ["Every clause receives one of the 20 CUAD labels", "Top-1 similarity 0.657 to 0.849; tie-break and 'Unclassified' never fire; 5 of 11 and 4 of 8 labels plausible on real clauses", "Thresholds 0.60 and 0.35 were set for another embedding scale; classifier trained on spans, applied to whole clauses"],
             ["Fair clauses are flagged", "Capped liquidated damages flagged as a penalty; a conflict-of-interest clause as restraint of trade; mutual liability for gross negligence as unlimited liability", "Patterns match the phrase, not the legal effect"],
             ["The complexity grade does not reflect fairness", "One-sided freelance contract grade B (23.3); fair contract grade A (13.7)", "The score measures wording only"],
             ["Long uploads time out in the browser", "113.6 s for 8 flags; the request limit is 180 s", "One Gemini call per flag (about 12 s each) in sequence"],
             ["Gemini quota", "`gemini-flash-latest` returned 429 and timed out at the start of the run; free tier allows 20 text requests per day per model", "Shared free-tier key; the demonstration used `gemini-3.1-flash-lite` set through the environment"],
             ["The Evaluation page overstates its evidence", "It says scores are \"measured on a held-out set\" and \"nothing here is hand-picked\"", "The 40 clauses were written by the rule author"]],
            "Failure cases with cause", widths=[0.28, 0.4, 0.32], font=8.5)


def sec_results_limits(d):
    d.h2("Limitations of the Results")
    d.bullets([
        "The classification test is on annotation spans, not on the whole clauses the product classifies, and it uses US contracts. The split is by span, not by contract (checked: 0.800 when contract-disjoint).",
        "The rule test sets are small (40 clauses each), written by project members, and the probe set was written after the rules were read. Neither is a lawyer-labelled set of Indian contracts, so the precision and recall figures are indicative.",
        "The CUAD rule cross-check is a proxy: CUAD categories describe topics, not predatory terms.",
        "No Indian contract corpus was available; the only real contract analysed is a US/Canadian supply agreement, and its jurisdiction cannot be changed in the tool.",
        "The quality of the generated reasons, safer wording and summaries was read by the authors on 19 clauses and three summaries but not verified by a lawyer, and no measure of hallucination was made.",
        "Timings come from one desktop computer that was also running other jobs, over a shared free-tier key, with a lite text model chosen after the default model timed out.",
        "The complexity weights and grade boundaries were not validated against human ratings, and the combination logic matches rule ids anywhere in a contract without regard to proximity or party.",
    ])


def sec_objectives(d):
    d.h2("Objectives versus Outcomes")
    d.table([["No.", "Objective (batch document 6)", "Outcome", "Evidence"],
             ["1", "Segment uploaded contracts into clauses and classify clause types", "Achieved with limits", "Heading-based segmenter (84 of 510 CUAD contracts give fewer than 5 clauses); top-1 0.792 and top-3 0.979 on 240 CUAD spans"],
             ["2", "RAG pipeline with the Claude API and pgvector semantic search", "Not as stated", "Gemini replaces Claude; vectors are SQLite blobs compared with NumPy; no retrieval from a legal corpus, only nearest-centroid classification and a legal-basis text in the prompt"],
             ["3", "Neo4j knowledge graph of clause relationships, legal concepts and precedents", "Partly", "NetworkX graph per contract with one node per clause and three combination patterns; no concept or precedent nodes; not persisted"],
             ["4", "Flag predatory clauses and combinations using Indian contract-law criteria", "Achieved in a limited form", "Eight rules with Indian statute references and three combinations; shipped set precision 1.00 / recall 0.94, independent probe set 0.79 / 0.46"],
             ["5", "Overall complexity score and plain-language risk summary", "Achieved", "A-F grade from four components; Gemini summary and key obligations on all three uploads; text not expert-verified; grade does not measure fairness"],
             ["6", "Evaluate classification and predatory detection separately", "Achieved", "Separate metrics in `ml/eval.py`, plus a probe set, a CUAD cross-check, baselines and a 510-contract run"]],
            "Objectives against outcomes", widths=[0.06, 0.3, 0.17, 0.47], font=9)
    d.p("Of the six objectives, three are met in the form stated or close to it (1, 5, 6), one in a limited form (4), and two only in part or not as stated (2 and 3), because the build uses a lighter stack than the abstract describes. "
        "The measured results show that the system works end to end and that its classifier is useful; they also show that the rule engine is the weakest component and that the headline detection score depends on the test set that produced it.")
