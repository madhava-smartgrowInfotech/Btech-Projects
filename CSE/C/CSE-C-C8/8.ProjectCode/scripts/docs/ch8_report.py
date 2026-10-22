"""Compact report variant of Chapter 8 (used when F.REPORT is True); the chapter document 14 keeps the full text of ch8.py."""

from . import facts as F
from .blocks import FIG, H1, H2, P, PAIR, TAB
from .ch8 import SH, _ms
from .refs import CITE as R


def _cap(name, text):
    return (SH(name), text)


def screens():
    return [
        H2("8.2 Output screens"),
        P("All 17 screens of the running application are shown (Chrome, 1440 by 900 pixels, with the local language model and MiniLM loaded and three real papers stored: the base paper, the survey and the ReViewGraph paper). "
          "The Analyze and Saved-analysis screens show the ReViewGraph paper (17 pages, 11,562 words); its several-minute run was done once and its stored result replayed into the page by the capture script."),
        PAIR([_cap("01_landing_dark.png", "Landing page, dark theme: pitch, WebGL hero and entry buttons."),
              _cap("02_landing_how_it_works_dark.png", "Landing page, how-it-works section: the pipeline steps.")], 2.8),
        PAIR([_cap("03_landing_light.png", "Landing page, light theme (sun button in the header)."),
              _cap("04_dashboard.png", "Dashboard: 6 reviewers, 3 analyses, accuracy 55.0% flagged as synthetic, AI status \"Loaded\".")], 2.8),
        PAIR([_cap("17_dashboard_light.png", "Dashboard, light theme."),
              _cap("05_analyze_empty.png", "Analyze screen before upload: drop zone and matching filters.")], 2.8),
        PAIR([_cap("06_analyze_result_overview.png", "Result overview: structural score 65.2, 2 concerns, top reviewer Gamma 28.4, decision signal borderline 58%, AI review by Qwen2.5-1.5B."),
              _cap("07_result_review.png", "Review tab: strengths, concerns, recommendations, coverage bars and the AI synthesis (with visible errors, Section 8.10).")], 2.8),
        PAIR([_cap("08_result_literature.png", "Literature tab: six OpenAlex works, three of them the paper itself."),
              _cap("09_result_reviewers.png", "Reviewers tab: five ranked cards with the opened audit table of the first.")], 2.8),
        PAIR([_cap("10_result_audit.png", "Audit and export tab: formula, analysis id 3, module statuses, JSON and PDF export."),
              _cap("15_saved_analysis.png", "Saved analysis reopened from history: the stored result, no recomputation.")], 2.8),
        PAIR([_cap("11_reviewers.png", "Reviewer directory: search, load bars, status, CSV import and export."),
              _cap("12_reviewers_add_modal.png", "Add-reviewer dialog with its eleven fields.")], 2.8),
        PAIR([_cap("13_model_performance.png", "Model performance: metrics, class distribution, confusion matrix and the synthetic-data banner."),
              _cap("14_history.png", "History of three analyses; its times are UTC without a zone (defect F8).")], 2.8),
        PAIR([_cap("16_about.png", "About and responsible use: pipeline, weights, rules, privacy, live status.")], 2.8),
        P("The Reviewers tab is the core of the recommendation: for Reviewer Gamma the audit table reads expertise 0.260 (x0.55), keyword 0.000 (x0.20), method 0.275 (x0.15), availability 1.000 (x0.10), conflict 0.000, final 28.4, so the score can be recomputed by hand. "
          "Gamma and Delta tie at 28.4, and the ranks run 1, 2, 4, 5, 6 because the inactive Reviewer Epsilon held rank 3 before the filter removed it."),
    ]


def _compact():
    sh, pc, mm, tf, L = F.SHIPPED, F.PER_CLASS, F.MINILM, F.TFIDF, F.LATENCY
    g, b, d = F.GEN, F.BASELINES, F.DM["decisive_only"]
    e = F.ENV
    d0, s0 = L["pipeline_stages"]["demo"], L["pipeline_stages"]["survey_30_pages"]
    h = L["http_api"]
    on = L["http_llm_on_s"]
    share = d0["Local AI review (3 steps)"] / d0["_total_ms"]
    cm_rows = [[k, F.f3(pc[k]["precision"]), F.f3(pc[k]["recall"]), F.f3(pc[k]["f1"]), str(pc[k]["support"]), " / ".join(str(x) for x in sh["confusion_matrix"][i])] for i, k in enumerate(F.DM["labels"])]
    cm_rows.append(["**macro / overall**", F.f3(sh["precision_macro"]), F.f3(sh["recall_macro"]), F.f3(sh["f1_macro"]), str(F.DM["test"]), f"accuracy {F.f3(sh['accuracy'])}, AUC {F.f3(sh['roc_auc'])}"])
    brow = [["Majority class", F.f3(b["majority_class"]["accuracy"]), F.f3(b["majority_class"]["f1_macro"]), "-"],
            ["Naive Bayes, word TF-IDF", F.f3(b["naive_bayes_word_tfidf"]["accuracy"]), F.f3(b["naive_bayes_word_tfidf"]["f1_macro"]), F.f3(b["naive_bayes_word_tfidf"]["roc_auc"])],
            ["Logistic regression, unweighted", F.f3(b["logreg_unweighted_word_char"]["accuracy"]), F.f3(b["logreg_unweighted_word_char"]["f1_macro"]), F.f3(b["logreg_unweighted_word_char"]["roc_auc"])],
            ["Logistic regression, word only", F.f3(b["logreg_balanced_word_only"]["accuracy"]), F.f3(b["logreg_balanced_word_only"]["f1_macro"]), F.f3(b["logreg_balanced_word_only"]["roc_auc"])],
            ["**PeerScope (balanced, word + char)**", F.f3(sh["accuracy"]), F.f3(sh["f1_macro"]), F.f3(sh["roc_auc"])],
            ["Five splits, mean +/- sd", f"{F.SEEDS['accuracy']['mean']:.3f} +/- {F.SEEDS['accuracy']['sd']:.3f}", f"{F.SEEDS['f1_macro']['mean']:.3f} +/- {F.SEEDS['f1_macro']['sd']:.3f}", f"{F.SEEDS['roc_auc']['mean']:.3f} +/- {F.SEEDS['roc_auc']['sd']:.3f}"]]
    names = [("full_hybrid_shipped_weights", "Hybrid, shipped weights"), ("semantic_similarity_only", "Semantic similarity only"),
             ("lexical_only_keyword_and_method", "Keyword and method overlap only"), ("hybrid_without_availability", "Hybrid without availability")]
    mrows = [[lab, F.f3(mm[k]["top1"]), F.f3(mm[k]["top3"]), F.f3(mm[k]["mrr"]), F.f3(tf[k]["top1"]), F.f3(tf[k]["top3"]), F.f3(tf[k]["mrr"])] for k, lab in names]
    mrows.append(["Random (expectation)", F.f3(mm["random_expectation_top1"]), F.f3(mm["random_expectation_top3"]), "-", F.f3(tf["random_expectation_top1"]), F.f3(tf["random_expectation_top3"]), "-"])
    c = mm["conflict"]
    det = c["detected_by_kind"]
    lit_n = sum(det[k]["n"] for k in ("conflict term", "affiliation", "full name"))
    lit_d = sum(det[k]["detected"] for k in ("conflict term", "affiliation", "full name"))
    par_n = det["paraphrased affiliation"]["n"] + det["first name only"]["n"]
    par_d = det["paraphrased affiliation"]["detected"] + det["first name only"]["detected"]
    real_rows = [[n, str(r["pages"]), f"{r['words']:,}", f"{len(r['sections_detected'])} / 9", F.f2(r["structural_score"]), f"{r['ml_label']} ({r['ml_confidence']:.2f})", r["title_extracted"][:36]]
                 for n, r in zip(["Demo fixture", "Survey [6]", "ReViewGraph [7]", "IEEE base paper [1]"], F.REAL)]
    lrows = [[k, _ms(d0[k]), _ms(s0[k])] for k in ["PDF extraction", "Local AI review (3 steps)", "Literature (OpenAlex)", "Reviewer matching"]] + [
        ["**Total (model on)**", _ms(d0["_total_ms"]), _ms(s0["_total_ms"])],
        ["HTTP analyze, model off (median)", _ms(h["analyze_demo_3_pages"]["median_ms"]), _ms(h["analyze_survey_30_pages"]["median_ms"])],
        ["Simple GET: health / model metrics (median)", f"{h['health']['median_ms']:.1f} ms", f"{h['model_metrics']['median_ms']:.1f} ms"]]
    out = [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS"),
           P("This chapter reports what was measured and what the running application shows. Where a result is weak it is reported as weak. All numbers come from `docs/metrics/`; Appendix B lists the scripts.")]
    out += [H2("8.1 Experimental set-up"),
            P(f"Machine: {e['cpu']}, {e['ram_gb']} GB, no GPU, Python {e['python']}; scikit-learn {e['packages']['scikit-learn']}, PyTorch {e['packages']['torch']}, Transformers {e['packages']['transformers']}. "
              f"Local model Qwen2.5-1.5B-Instruct [{R['qwen25']}] on the CPU; encoder all-MiniLM-L6-v2 [{R['sbert']}]. Data: a synthetic {F.DM['rows']:,}-row corpus for the decision model (80/20 stratified split, seed 42, {F.DM['test']} test papers), "
              "six demo reviewer profiles, 40 probe abstracts written by the team for matching, 15 injected conflict sentences and four real PDFs. The shipped model, re-evaluated on its split, reproduces `models/metrics.json` exactly. No significance tests were run.")]
    out += screens()
    out += [H2("8.3 Decision-model performance"),
            P("The model was trained on generated text whose label comes from the same hidden quality value as the strength or weakness phrases in the text, so it shows that the pipeline works, not that it predicts real decisions. "
              f"It finds accept (recall {F.f3(pc['accept']['recall'])}) and reject (recall {F.f3(pc['reject']['recall'])}) papers, with {d['correct']} of {d['n']} decisive-class papers correct ({F.pct(d['accuracy'])}), but only {F.f3(pc['borderline']['recall'])} of borderline papers. "
              f"The labels explain it: strength-phrase papers are accept in {g['strong_phrase_papers']['label_counts']['accept']} and borderline in {g['strong_phrase_papers']['label_counts']['borderline']} cases, weakness-phrase papers reject in {g['weak_phrase_papers']['label_counts']['reject']} and borderline in {g['weak_phrase_papers']['label_counts']['borderline']}, "
              f"so no text rule exceeds {F.f3(g['best_possible_accuracy_from_phrases'])} accuracy and the measured {F.f3(sh['accuracy'])} is near that ceiling. Accuracy over five splits ranges {F.f3(F.SEEDS['accuracy']['min'])} to {F.f3(F.SEEDS['accuracy']['max'])}, so differences of about three points between the variants are noise. "
              f"At a confidence threshold of 0.7 only {F.pct(F.thr_row(0.7)['coverage'])} of papers remain ({F.pct(F.thr_row(0.7)['accuracy_on_kept'])} accuracy), so the application shows the three probabilities and no threshold."),
            TAB("Shipped model: per-class results and confusion-matrix row (predicted accept / borderline / reject)", ["Class", "Precision", "Recall", "F1", "Support", "Predicted a / b / r"], cm_rows,
                widths=[1.3, 0.8, 0.8, 0.7, 0.7, 2.2], align=["l", "c", "c", "c", "c", "c"], size=9.5),
            TAB("Baselines on the same split and the five-split spread", ["Model", "Accuracy", "Macro F1", "ROC-AUC"], brow, widths=[3.0, 1.1, 1.1, 1.1], align=["l", "c", "c", "c"], size=9.5),
            PAIR([(F.fig("f01_confusion_matrix.png"), "Confusion matrix of the shipped model."), (F.fig("f03_baselines.png"), "Shipped model against baselines and the label-construction ceiling (dashed).")], 3.0)]
    out += [H2("8.4 Reviewer-matching results"),
            P(f"Forty team-written abstracts (six areas plus four cross-area cases) were ranked against the six demo reviewers by the production code; top-1 is the share with an acceptable reviewer first. With MiniLM the shipped hybrid score reaches {F.pct(mm['full_hybrid_shipped_weights']['top1'], 1)} top-1 "
              f"(random {F.pct(mm['random_expectation_top1'], 1)}) and semantic similarity alone {F.pct(mm['semantic_similarity_only']['top1'], 1)}: the keyword, method and availability terms serve auditability and workload, not accuracy. Lexical overlap alone reaches {F.pct(mm['lexical_only_keyword_and_method']['top1'], 1)}. "
              f"The offline TF-IDF fallback, whose vocabulary is frozen after the first request, reaches {F.pct(tf['full_hybrid_shipped_weights']['top1'], 1)}. The {len(mm['top1_misses_shipped'])} MiniLM misses (malware-classifier and log-based intrusion-detection abstracts) went to the generalist Reviewer Gamma. "
              f"Ranking time grows linearly because profiles are re-embedded per request: {_ms(mm['scaling_ms'][0]['median_ms'])} for 6 reviewers, {_ms(mm['scaling_ms'][3]['median_ms'])} for 500 (fallback {_ms(tf['scaling_ms'][3]['median_ms'])}). Labels are the team's own, so the figures describe a friendly sample."),
            TAB("Matching quality on 40 probe abstracts", ["Configuration", "MiniLM top-1", "top-3", "MRR", "TF-IDF top-1", "top-3", "MRR"], mrows, widths=[2.1, 0.8, 0.6, 0.6, 0.8, 0.6, 0.6], align=["l", "c", "c", "c", "c", "c", "c"], size=9.5),
            FIG(F.fig("f07_matching_configs.png"), "Top-1, top-3 and MRR for four score configurations, MiniLM (left) and TF-IDF fallback (right).", 5.4)]
    out += [H2("8.5 Conflict-of-interest results"),
            P(f"Fifteen sentences with a known link were injected into a probe abstract. The matcher flagged {lit_d} of {lit_n} literal links (conflict terms, affiliations, full names) and {par_d} of {par_n} paraphrased or first-name-only links, with {c['false_flags_on_clean_papers']} false flags on {c['clean_pairs_checked']} clean pairs. "
              "A flagged reviewer's score falls to zero (penalty 0.60) and the reviewer drops to the last rank. This is a literal string matcher; co-authorship and reworded affiliations are not visible to it."),
            PAIR([(F.fig("f08_conflict_detection.png"), "Conflict detection by kind of link."), (F.fig("f12_score_breakdown.png"), "Weighted score components of the five active reviewers for the demo paper.")], 3.0)]
    out += [H2("8.6 The pipeline on real papers"),
            TAB("Extraction and signals on four PDFs", ["File", "Pages", "Words", "Sections", "Structural", "Decision signal", "Title extracted"], real_rows, widths=[1.3, 0.5, 0.6, 0.7, 0.8, 1.1, 1.6], align=["l", "c", "c", "c", "c", "c", "l"], size=8.5),
            P(f"Extraction of 17 to 30 page text PDFs takes under half a second. The structural score barely moves ({min(r['structural_score'] for r in F.REAL):.1f} to {max(r['structural_score'] for r in F.REAL):.1f}); the IEEE paper's roman-numeral headings hide its introduction and its title comes back as the DOI line. "
              f"The decision model says borderline for all four real papers ({min(r['ml_confidence'] for r in F.REAL):.2f} to {max(r['ml_confidence'] for r in F.REAL):.2f}), as expected from a model trained on templated synthetic text.")]
    out += [H2("8.7 Performance and latency"),
            TAB("Time per stage and over HTTP (127.0.0.1)", ["Stage or request", "Demo paper, 3 pages", "Survey, 30 pages"], lrows, widths=[3.0, 1.7, 1.7], align=["l", "c", "c"], size=9.5),
            FIG(F.fig("f11_pipeline_timings.png"), "Where the time goes in one analysis of the demo paper (CPU only).", 4.6),
            P(f"The local language model takes {F.pct(share)} of an analysis (three generations, {d0['_ai_tokens_all_steps']:,} tokens, about {d0['_ai_tokens_all_steps'] / (d0['Local AI review (3 steps)'] / 1000):.1f} tokens per second). Through the server a cold analysis took {on['ieee_base_paper_30_pages']} s (base paper), "
              f"{on['arxiv_survey_30_pages']} s (survey) and {on['reviewgraph_17_pages_via_browser']} s (ReViewGraph, driven through the browser); with the model off it takes about {h['analyze_demo_3_pages']['median_ms'] / 1000:.1f} s. These are single runs on one CPU-only PC.")]
    out += [H2("8.8 Comparison with the base paper"),
            TAB("What the two works cover", ["Dimension", "Base paper [1]", "PeerScope"],
                [["Task", "Reviewer assignment only", "Preliminary paper assessment and reviewer ranking"],
                 ["Data", "663 papers, 85 conferences, 1,989 assignments, 524 reviewers", "40 team-written abstracts, 6 demo reviewers; 1,400 synthetic rows"],
                 ["Labels", "Historical assignments", "The team's own judgement"],
                 ["Language model", "Keyword induction by an ensemble and a judge, with audit trail", "Local Qwen2.5-1.5B writes a review; does not rank"],
                 ["Metrics", "MRR@3 up to 0.7778 (titles) and 0.7843 (abstracts)", f"Top-1 {F.f3(mm['full_hybrid_shipped_weights']['top1'])}, MRR {F.f3(mm['full_hybrid_shipped_weights']['mrr'])} among 6 reviewers"],
                 ["Conflicts, capacity", "Not benchmarked", "In the score; measured by injection"],
                 ["Delivery", "Offline experiments", "Local web application with directory, history, export"]],
                widths=[1.1, 2.7, 2.8], align=["l", "l", "l"], size=9),
            P(f"The results are not comparable: our top-1 of {F.f3(mm['full_hybrid_shipped_weights']['top1'])} ranks six reviewers for 40 abstracts we wrote (random {F.f3(mm['random_expectation_top1'])}); the base paper ranks hundreds of reviewers for real submissions against historical assignments. "
              "In the base paper the order of lexical and dense measures depends on the text view and most encoder differences were not significant [1]; our small sample favours the dense encoder and cannot confirm or contradict it.")]
    out += [H2("8.9 Sample input and output"),
            P("The sample input is the 17-page ReViewGraph PDF (728 KB, 11,562 words, nine references parsed). The server returned a 32 KB JSON document with the fields `paper`, `ml_decision_signal` (borderline 0.5829), `structural_assessment` (65.2), `review` (source deterministic+llm, coverage Method 90, Evidence 90, Clarity 85, Reproducibility 80, Novelty 55, Limitations 70), "
              "`literature` (status ok, six works), `reviewers` (Gamma 28.4 with its breakdown, four more) and the disclaimer. For the survey the literature block was `unavailable` with the HTTP 400 text and the rest of the analysis was complete.")]
    out += [H2("8.10 Success and failure analysis"),
            TAB("Cases that worked", ["No.", "Case", "Evidence"],
                [["S1", "Accept and reject papers separated", f"{d['correct']} of {d['n']} decisive-class papers correct"],
                 ["S2", "Acceptable reviewer ranked first (MiniLM)", f"{F.pct(mm['full_hybrid_shipped_weights']['top1'], 1)} top-1 on 40 probes"],
                 ["S3", "Literal conflicts penalised, no false flags", f"{lit_d} of {lit_n} flagged; 0 false flags in {c['clean_pairs_checked']} pairs"],
                 ["S4", "Scores recomputable by hand; graceful degradation", f"Audit table; AI off, literature down and inactive reviewer handled (pytest {F.PYTEST_PASSED} of {F.PYTEST_TOTAL}, smoke {F.SMOKE_PASSED} of {F.SMOKE_TOTAL})"],
                 ["S5", "Fast deterministic path, stored and exported analyses", f"About {h['analyze_demo_3_pages']['median_ms'] / 1000:.1f} s per analysis, model off"]],
                widths=[0.5, 2.8, 3.3], align=["c", "l", "l"], size=9.5),
            TAB("Failure cases observed", ["No.", "Case", "What happened / cause"],
                [["F1", "Language-model text has errors", "Synthesis of the ReViewGraph paper: invented title suffix, wrong datasets, contradictory code statement, cut at 700 tokens; no fact checking"],
                 ["F2", "Literature problems", "Survey title contains a question mark and OpenAlex answers HTTP 400; for ReViewGraph the paper itself is returned three times"],
                 ["F3", "Title and introduction missed", "IEEE paper: title is the DOI line, 6 of 9 sections; roman-numeral headings not recognised"],
                 ["F4", "Same decision signal for all real papers", "borderline, 0.55 to 0.66; classifier trained on templated synthetic text"],
                 ["F5", "Probe misses", f"{len(mm['top1_misses_shipped'])} of 40 (MiniLM), {len(tf['top1_misses_shipped'])} of 40 (fallback); generalist profile, frozen fallback vocabulary"],
                 ["F6", "Low and tied scores on a real paper", "Top 28.4 (Possible); Gamma and Delta tied; NLP reviewer fourth; the demo pool is far from the topic"],
                 ["F7", "Paraphrased conflicts invisible", f"{par_d} of {par_n} flagged; literal string matching"],
                 ["F8", "Display and validation defects", "Rank numbers skip; UTC times without zone; a corrupt file with a PDF header is accepted (HTTP 200)"]],
                widths=[0.4, 1.9, 4.3], align=["c", "l", "l"], size=9)]
    out += [H2("8.11 Limitations of the results"),
            P("The decision-model figures describe synthetic data; the probe set is small, team-written and friendly; the six reviewers are invented; nobody outside the team rated any output and no user study was run; novelty is a fixed value of 55, not a measurement; "
              "timings are single runs on one CPU-only PC; and accuracy on real decisions, scanned PDFs, non-English papers, GPU speed, concurrent users and language-model review quality were not measured.")]
    obj = [["1", "Corpus of papers and reviewer profiles", "Partly", f"Analyses stored; 6 demo profiles, CSV import; synthetic corpus ({F.DM['rows']:,} rows)"],
           ["2", "Topics, methods, keywords by NLP", "Met (heuristic)", "Frequency keywords, 21-term method lexicon, 18 topic hints"],
           ["3", "Reviewer expertise as vectors", "Met", "MiniLM embeddings of profile text; no real publication histories"],
           ["4", "Semantic similarity ranking", "Met", f"Top-1 {F.f3(mm['full_hybrid_shipped_weights']['top1'])} (MiniLM), {F.f3(tf['full_hybrid_shipped_weights']['top1'])} (fallback) on probes"],
           ["5", "Preliminary assessment incl. novelty signals", "Met except novelty", "Structure, evidence, method, presentation, decision signal, AI review; novelty fixed"],
           ["6", "Assignment quality vs experts; COI handling", "Partly", f"Team labels, not experts; COI {lit_d}/{lit_n} literal, {par_d}/{par_n} paraphrased, 0 false flags"],
           ["A", "Abstract: deep-learning area classifier, originality, h-index, venue scope", "Not implemented", "Keyword hints and a linear model; no originality score or h-index"]]
    out += [H2("8.12 Objectives against outcomes"),
            TAB("Objectives against outcomes", ["No.", "Objective", "Status", "Evidence"], obj, widths=[0.4, 2.2, 1.1, 2.9], align=["c", "l", "c", "l"], size=9),
            P("The engineering objectives are met; the evaluation objectives are met only at the scale of a demonstration.")]
    return out


def _prose(blocks):
    return [b for b in blocks if b[0] in ("p", "h3")]


def blocks():
    """Compact tables and figures of _compact() with the full prose of the full chapter restored for 8.3-8.8 and 8.9-8.11."""
    from . import ch8 as C

    out = _compact()
    full = {"8.3": C._decision(), "8.4": C._matching(), "8.5": C._conflict(), "8.6": C._real(), "8.7": C._latency(), "8.8": C._compare()}
    res, i = [], 0
    cur = None
    while i < len(out):
        b = out[i]
        if b[0] == "h2":
            cur = b[1][:3]
            res.append(b)
            if cur in full:
                res += _prose(full[cur])[0:]
            i += 1
            continue
        if cur in full and b[0] in ("p", "h3"):
            i += 1
            continue
        if cur == "8.9":
            res += [x for x in C._samples()[1:]]
            i += 1
            while i < len(out) and out[i][0] != "h2":
                i += 1
            continue
        if cur == "8.10" and b[0] == "tab" and b[1].startswith("Failure cases"):
            res.append([x for x in C._cases() if x[0] == "tab"][1])
            i += 1
            continue
        res.append(b)
        i += 1
    return res
