"""Builds 19.IEEE_Paper.docx (two-column, 6 pages) for PeerScope from facts.py (metrics.json, latency.json), the diagrams and the screenshots.

    python -m scripts.docs.build_paper            # from 8.ProjectCode, system python
"""

import os

from PIL import Image

from . import facts as F
from .paper import Paper

pct, f2, f3 = F.pct, F.f2, F.f3


def make_figures():
    """Compact figures for the paper, written to docs/figures/paper_*.png."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 12})
    out = {}
    NAVY, BLUE, TEAL, ORANGE, RED = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#C0392B"
    B, SH = F.BASELINES, F.SHIPPED
    fig, (a, b) = plt.subplots(2, 1, figsize=(6.8, 7.0), gridspec_kw={"hspace": 0.62})
    rows = [("Majority\nclass", B["majority_class"]), ("Naive Bayes", B["naive_bayes_word_tfidf"]), ("LogReg\nunweighted", B["logreg_unweighted_word_char"]),
            ("PeerScope\nmodel", SH)]
    x = np.arange(len(rows))
    b1 = a.bar(x - 0.2, [r["accuracy"] for _, r in rows], 0.4, color=BLUE, label="accuracy")
    b2 = a.bar(x + 0.2, [r["f1_macro"] for _, r in rows], 0.4, color=ORANGE, label="macro F1")
    for bars in (b1, b2):
        for bb in bars:
            a.text(bb.get_x() + bb.get_width() / 2, bb.get_height() + 0.012, f"{bb.get_height():.2f}", ha="center", fontsize=11)
    ceil = F.GEN["best_possible_accuracy_from_phrases"]
    a.axhline(ceil, color=RED, ls="--", lw=1.4)
    a.text(-0.45, ceil + 0.05, f"label ceiling {ceil:.2f}", color=RED, fontsize=11)
    a.set_xticks(x)
    a.set_xticklabels([n for n, _ in rows], fontsize=11)
    a.set_ylim(0, 0.85)
    a.set_ylabel("score, 280 test papers")
    a.legend(frameon=False, fontsize=11, loc="upper right", ncol=2)
    a.set_title("(a) Decision model on synthetic labels", fontsize=12)
    a.spines[["top", "right"]].set_visible(False)
    names = [("full_hybrid_shipped_weights", "hybrid\n(shipped)"), ("semantic_similarity_only", "semantic\nonly"), ("lexical_only_keyword_and_method", "lexical\nonly")]
    xs = np.arange(len(names))
    mm, tf = F.MINILM, F.TFIDF
    c1 = b.bar(xs - 0.2, [mm[k]["top1"] for k, _ in names], 0.4, color=TEAL, label="MiniLM embeddings")
    c2 = b.bar(xs + 0.2, [tf[k]["top1"] for k, _ in names], 0.4, color=ORANGE, label="TF-IDF fallback")
    for bars in (c1, c2):
        for bb in bars:
            b.text(bb.get_x() + bb.get_width() / 2, bb.get_height() + 0.012, f"{bb.get_height():.2f}", ha="center", fontsize=11)
    b.axhline(mm["random_expectation_top1"], color=RED, ls=":", lw=1.4)
    b.text(2.45, mm["random_expectation_top1"] + 0.025, "random", color=RED, fontsize=11, ha="right")
    b.set_xticks(xs)
    b.set_xticklabels([n for _, n in names], fontsize=11)
    b.set_ylim(0, 1.2)
    b.set_ylabel("top-1, 40 probe papers")
    b.legend(frameon=False, fontsize=11, loc="upper right", ncol=2)
    b.set_title("(b) Reviewer ranking on the probe set", fontsize=12)
    b.spines[["top", "right"]].set_visible(False)
    p = os.path.join(F.FIGS, "paper_results.png")
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    out["results"] = p

    # Fig. 4: KPI tiles + preliminary assessment of the real analysis (screen 06); Fig. 5: top reviewer card with audit breakdown (screen 09)
    s06 = Image.open(F.shot("06_analyze_result_overview.png")).convert("RGB")
    top = s06.crop((250, 835, 1420, 1030))
    bot = s06.crop((250, 1585, 1420, 1960))
    im = Image.new("RGB", (1170, top.height + bot.height + 10), (11, 13, 16))
    im.paste(top, (0, 0))
    im.paste(bot, (0, top.height + 10))
    p = os.path.join(F.FIGS, "paper_screen_assessment.png")
    im.save(p)
    out["assessment"] = p
    s09 = Image.open(F.shot("09_result_reviewers.png")).convert("RGB")
    p = os.path.join(F.FIGS, "paper_screen_reviewers.png")
    s09.crop((270, 1140, 1420, 1930)).save(p)
    out["reviewers"] = p
    return out


def build(path):
    figs = make_figures()
    env = F.ENV
    pk = env["packages"]
    L = F.LATENCY
    sh = F.SHIPPED
    mm, tf = F.MINILM, F.TFIDF
    hy, se, lx = mm["full_hybrid_shipped_weights"], mm["semantic_similarity_only"], mm["lexical_only_keyword_and_method"]
    thy, tse = tf["full_hybrid_shipped_weights"], tf["semantic_similarity_only"]
    cf = mm["conflict"]
    kinds = cf["detected_by_kind"]
    lit_det = sum(kinds[k]["detected"] for k in ("conflict term", "affiliation", "full name"))
    lit_n = sum(kinds[k]["n"] for k in ("conflict term", "affiliation", "full name"))
    para_n = kinds["paraphrased affiliation"]["n"] + kinds["first name only"]["n"]
    gen = F.GEN
    ceil = gen["best_possible_accuracy_from_phrases"]
    demo = L["pipeline_stages"]["demo"]
    llm_s = demo["Local AI review (3 steps)"] / 1000
    tot_s = demo["_total_ms"] / 1000
    http = L["http_api"]
    llm_on = L["http_llm_on_s"]
    dec = F.DM["decisive_only"]
    seeds = F.SEEDS
    real = F.REAL
    scal = mm["scaling_ms"]

    P = Paper()
    authors = [[n, f"Roll No. {r}", "Dept. of Computer Science and Engineering", "TKR College of Engineering & Technology", "[CITY], India", "[EMAIL]"] for n, r in F.STUDENTS]
    authors.append([F.GUIDE, f"{F.GUIDE_DESIGNATION} (project guide)", "Dept. of Computer Science and Engineering", "TKR College of Engineering & Technology", "[CITY], India", "[EMAIL]"])
    P.title_block("PeerScope: Paper Evaluation and Auditable Reviewer Recommendation with Local AI", authors)
    P.begin_two_columns()

    P.abstract(
        "Journals and conferences receive more submissions than their reviewers can absorb, and both first-pass screening and the choice of reviewer remain largely manual. "
        "This paper presents PeerScope, a local web application that turns a research-paper PDF into a preliminary, clearly caveated assessment and an auditable ranking of candidate reviewers. "
        "The paper is parsed into sections and structural signals, a TF-IDF logistic-regression model supplies a historical decision signal, a locally run Qwen2.5-1.5B model drafts a critique, "
        "and related work is retrieved from OpenAlex. Reviewers are ranked by a transparent score that combines sentence-embedding similarity, keyword and method overlap, availability and a conflict penalty. "
        f"On 40 probe abstracts written by the team and six demo reviewers, the hybrid score ranks an acceptable reviewer first in {pct(hy['top1'], 0)} of cases ({pct(thy['top1'], 0)} with an offline TF-IDF fallback). "
        f"The decision model, trained on synthetic labels, reaches {f2(sh['accuracy'])} accuracy, close to the {f2(ceil)} ceiling of those labels, so it demonstrates the pipeline and does not predict real decisions. "
        "The results are not comparable with earlier work on real conference data.",
        ["artificial intelligence", "conflict of interest", "natural language processing", "peer review", "reviewer recommendation", "semantic similarity", "sentence embeddings"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Scholarly publishing is limited by reviewer capacity. When two independent NeurIPS 2021 committees reviewed the same papers they disagreed on about 23 % of accept-or-reject outcomes {r:13}, "
           "and each submission still has to be matched to qualified reviewers, a task studied for about thirty years as the reviewer assignment problem {r:9}. In most venues an editor shortlists "
           "reviewers from personal knowledge or keyword search, which favours people who share vocabulary rather than expertise, and screens each submission by hand before any reviewer sees it.")
    P.para("Research has served the two halves of this workload separately. Assignment methods compute paper-reviewer affinity from text, from topic models or from learned suitability scores {r:10,11,16}; "
           "automated-review work, surveyed in {r:6}, predicts decisions or writes review text {r:7,22,23,24}. The base paper {r:1} argues that the affinity score is the hard part and that dense embeddings are hard to audit, "
           "so it restricts language models to extracting keywords and keeps a full audit trail. It does not assess the submission itself, and it left conflict of interest and reviewer capacity out of its experiments. "
           "Language-model reviewers also carry risks: hidden instructions in a manuscript steer them {r:2,27}.")
    P.para("PeerScope closes the first gap on a small scale. It is a local application, with no cloud service for the paper text, that gives an editor both a preliminary assessment of an uploaded PDF and a "
           "reviewer ranking whose every term is visible. The contributions are: (1) an end-to-end pipeline from PDF to assessment to ranked reviewers, with a stored history and JSON and PDF export; "
           "(2) an auditable score that puts embedding similarity, keyword and method overlap, availability and a conflict penalty in one explicit formula; "
           "(3) a measured evaluation, including a baseline study, a probe-set test of ranking quality, a conflict-injection test and latency, reported together with what it cannot show; and "
           "(4) a record of the defects found in testing. Section II reviews related work, Section III the method, Section IV the results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para(f"Every measurement used one desktop PC: {env['cpu'].replace('12th Gen ', '').replace('(R)', '').replace('(TM)', '')} with {env['ram_gb']} GB of RAM, no graphics processor and Windows 11. "
           "Language-model generation therefore ran on the CPU in 32-bit floating point.")
    P.sub("B", "Software Requirements")
    P.para(f"Python {env['python']}; FastAPI {pk['fastapi']} with SQLite through SQLAlchemy {pk['SQLAlchemy']}; PyMuPDF {pk['PyMuPDF']} for text extraction; scikit-learn {pk['scikit-learn']} {{r:31}}; "
           f"sentence-transformers {pk['sentence-transformers']} with all-MiniLM-L6-v2 {{r:20}}; PyTorch {pk['torch']} and Transformers {pk['transformers']} running Qwen2.5-1.5B-Instruct {{r:29}}; "
           "the OpenAlex API {r:32} for literature; and a React and Vite interface for the browser.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para("**Base paper.** Bagheri et al. {r:1} treat reviewer assignment as an affinity-construction problem. Producer language models each return six to twelve keyphrases for a paper view "
           "(title, abstract summary or abstract) or for each prior publication of a reviewer; a stronger judge model picks the best list without rewriting it; deterministic normalisation follows; "
           "and every stage stores prompts, model identifiers and score matrices as an audit trail. Matchers include TF-IDF cosine, keyword Jaccard, an SBERT bi-encoder (all-MiniLM-L6-v2) with a cross-encoder re-ranker, "
           "and keyword knowledge graphs. The data are 663 papers from 85 computer-science conferences with 1,989 historical assignments and 524 reviewer profiles built from Semantic Scholar. "
           "The best mean reciprocal rank at three (MRR@3) is 0.7778 on titles (two-stage re-ranking) and 0.7843 on abstracts (graph edge Jaccard); the best precision at three is 0.4545. "
           "Most differences between text encoders were not statistically significant. The authors state that historical assignments are an imperfect label, that no human expert judgements were used, "
           "and that conflict of interest and capacity could not be benchmarked.")
    P.para("**Reviewer assignment.** Charlin et al. {r:10} learn suitability scores from a few provided scores and then solve an integer program; Mimno and McCallum {r:11} compare language-model and "
           "author-persona-topic models against human relevance judgements; Chain-of-Factors {r:16} chains semantic, topic and citation factors in one instruction-tuned model; "
           "and Jecmen et al. {r:15} randomise assignments to limit manipulation. A survey {r:9} organises the field into candidate database, matching degree and assignment optimisation.")
    P.para("**Representations.** Sentence-BERT {r:19} makes sentence embeddings comparable by cosine similarity (finding the closest pair among 10,000 sentences falls from about 65 hours to about 5 seconds), "
           "and MiniLM {r:20} is the compact model family used here and in the base paper.")
    P.para("**Automated review.** PeerRead {r:22} offers 14.7 thousand drafts with decisions and 10.7 thousand reviews, where simple models cut error by up to 21 % against the majority baseline. "
           "Debate graphs over simulated reviewer-author exchanges (ReViewGraph) {r:7} reach 66-72 % accuracy on ICLR 2023-2025 decisions. Generated reviews cover more aspects than human ones but are less constructive {r:23}; "
           "GPT-4 feedback overlaps with human reviewers about as much as two humans overlap with each other {r:24}. Hidden instructions were followed in 78 % to 86 % of trials with two chatbots {r:2}, "
           "and simple prompt injection raised acceptance scores up to 100 % {r:27}.")
    P.table("Representative related work", ["Work", "Approach", "Data", "Reported result", "Limitation"], [
        ["{r:1}", "LLM keywords, audit trail, SBERT and graph matchers", "663 papers, 524 reviewers", "MRR@3 up to 0.78", "No paper assessment; no COI test"],
        ["{r:10}", "Learned suitability + integer program", "Two conferences", "Better than baselines", "Needs provided scores"],
        ["{r:11}", "Author-persona-topic model", "Rexa, human judgements", "APT best of three", "Topic model only"],
        ["{r:22}", "Decision and review dataset", "14.7K drafts", "Up to 21 % error cut", "Old text models"],
        ["{r:24}", "GPT-4 feedback on PDFs", "Nature, ICLR papers", "31-39 % overlap", "No reviewer matching"],
        ["{r:7}", "Debate graph + GNN", "ICLR 2023-25", "66-72 % accuracy", "Decisions only"],
    ], widths=[0.3, 0.95, 0.72, 0.72, 0.71], size=7, align=["c", "l", "l", "l", "l"])
    P.para("**Gap.** Assignment research scores affinity but does not look at the submission; review research looks at the submission but does not choose reviewers; the base paper leaves availability and conflict of "
           "interest outside its experiments; and no work in this survey delivers both halves, locally and with a visible score, as one application. PeerScope targets that combination at demonstration scale; "
           "it does not attempt to match the base paper's data or its keyword-induction ensemble.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.para("**Architecture.** Fig. 1 shows the three tiers. A React single-page application calls a FastAPI service on the same machine; the service runs a set of plain Python service modules and keeps two SQLite "
           "tables, one for reviewers and one for stored analyses, plus the trained model files. There is no login and nothing is sent to a cloud service apart from a title query to OpenAlex.")
    P.figure(F.diag("01_system_architecture.png"), "PeerScope architecture: browser tier, FastAPI service with its service modules, and file and database storage.")
    P.para("**Main flow.** Fig. 2 follows one upload (at most 20 MB, with a PDF header check). PyMuPDF extracts text page by page; the text is normalised, the title is taken from the first plausible line, "
           "nine section types are found by pattern matching and references are parsed. Frequency keywords, a 21-term method lexicon and 18 topic hints describe the paper, and four structural signals "
           "(section completeness A, evidence coverage B, method clarity C and presentation D) combine as")
    P.eq("S_struct = 0.35 A + 0.25 B + 0.25 C + 0.15 D.")
    P.figure(F.diag("02_high_level_workflow.png"), "Main flow: extraction, signals, decision model, review, literature and reviewer ranking.")
    P.para(f"**Decision signal.** A TF-IDF representation (8,000 word 1-2-grams and 4,000 character 3-5-grams) feeds a logistic regression with balanced class weights {{r:31}} that outputs probabilities for accept, borderline "
           f"and reject, p(k|x) = softmax(Wx + b). No public peer-review corpus could be fetched, so the model is trained on a synthetic set of {F.DM['rows']:,} papers generated by the project (80/20 stratified split, seed 42). "
           f"Its labels are drawn from the same strength and weakness phrases that appear in the text, and the borderline class arises from both groups, so no text classifier can exceed about {f2(ceil)} accuracy on it.")
    P.para("**Review.** Deterministic rules always produce strengths, concerns and recommendations from the signals. If it can be loaded, a locally run Qwen2.5-1.5B-Instruct model {r:29} adds a three-step "
           "analyse, critique and synthesise text; if not, the interface says so and shows only the deterministic part. Related work is searched in OpenAlex by title and ranked by embedding similarity.")
    P.para("**Reviewer matching.** Paper and reviewer profile texts are embedded with all-MiniLM-L6-v2, with a TF-IDF fallback when the model cannot be loaded. The score of reviewer r for paper p is")
    P.eq("S(p, r) = 100 · clip(0.55 s_emb + 0.20 s_kw + 0.15 s_meth + 0.10 s_avail − 0.60 c),")
    P.para(indent=0, text="where s_emb is the cosine similarity of the embeddings, s_kw and s_meth are overlap scores between paper and reviewer keywords, and between methods and topics, "
           "s_avail = 1 − load/capacity, and c is 1 when a conflict is detected and 0 otherwise. A conflict is a listed conflict term, the reviewer's full name or the reviewer's affiliation appearing in the first 3,000 "
           "characters of the paper. Scores of at least 65, 45 and 25 are labelled Strong, Good and Possible. Every recommendation shows all five terms, the matching words and a one-line explanation, which is the "
           "auditability inherited from the base paper's principle {r:1}. The directory holds six clearly labelled demo reviewers; the ranking is only a ranking, with no global assignment optimiser.")
    P.figure(F.diag("10_flowchart_matching.png"), "Core algorithm: profile construction, embedding similarity, overlap, availability, conflict detection, weighted score and ranking.", width=3.1)
    P.para("**Implementation.** The service exposes twelve endpoints: health, model metrics, create, list, update, delete, import and export of reviewers, analysis upload, history, retrieval and export "
           "as JSON or PDF. Uploads are rejected with a clear message when the extension or content type is wrong, the file is empty, the PDF header is missing (HTTP 400) or the size exceeds 20 MB (HTTP 413); "
           "reviewer fields are length-limited by Pydantic schemas (HTTP 422), unknown identifiers return 404, and an unexpected error returns a generic 500 without internal details. A stored analysis keeps the "
           f"full result as JSON. The code base is {F.LOC['backend_app']:,} lines of Python for the service, {F.LOC['frontend_src']:,} lines for the eight-page interface and {F.LOC['tests']} lines of tests.")
    P.para(f"**Evaluation protocol.** The decision model is evaluated on the {F.DM['test']} held-out synthetic papers, against majority-class, naive Bayes and unweighted logistic-regression baselines, and over five different splits. "
           "Ranking is evaluated on 40 abstracts written by the team, each labelled with the demo reviewer or reviewers whose profile fits; top-1, top-3 and mean reciprocal rank are reported for four score "
           f"configurations. Fifteen conflict links were injected into a paper (12 literal, {para_n} paraphrased) and {cf['clean_pairs_checked']} clean paper-reviewer pairs were checked for false flags. "
           "Four real PDFs, including the base paper, were run through the pipeline, and latency was measured stage by stage and over HTTP.")
    P.para(f"**Verification.** {F.PYTEST_TOTAL} pytest tests (extraction, features, matching and conflict, model service, health, reviewer create-read-update-delete and a full analysis) and a {F.SMOKE_TOTAL}-check smoke test "
           f"against a running server (validation, CRUD, CSV, analysis, history, export, CORS) pass in {F.PYTEST_SECONDS:.0f} s with the language model switched off.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.para(f"**Test conditions.** All numbers come from one machine (Section I-A). The decision-model figures use the {F.DM['test']}-paper synthetic test split; the ranking figures use the 40-abstract probe set and "
           "the six demo reviewers, whose profiles and labels were written by the same team, so they are optimistic and are not independent expert judgements. Table II lists the main results.")
    P.table("Measured results", ["Evaluation", "Setting", "Result"], [
        ["Decision model, 280 test papers", "accuracy / macro F1", f"{f2(sh['accuracy'])} / {f3(sh['f1_macro'])}"],
        ["", "macro precision / recall", f"{f2(sh['precision_macro'])} / {f2(sh['recall_macro'])}"],
        ["", "ROC-AUC (one vs rest)", f3(sh["roc_auc"])],
        ["", "5 splits, accuracy", f"{f3(seeds['accuracy']['mean'])} +/- {f3(seeds['accuracy']['sd'])}"],
        ["", "accept vs reject only", f"{pct(dec['accuracy'], 0)} ({dec['correct']}/{dec['n']})"],
        ["", "baselines, accuracy", f"majority {f2(F.BASELINES['majority_class']['accuracy'])}, NB {f2(F.BASELINES['naive_bayes_word_tfidf']['accuracy'])}"],
        ["Ranking, 40 probes", "hybrid, MiniLM: top-1 / top-3 / MRR", f"{f2(hy['top1'])} / {f2(hy['top3'])} / {f2(hy['mrr'])}"],
        ["", "semantic only, MiniLM", f"{f2(se['top1'])} / {f2(se['top3'])} / {f2(se['mrr'])}"],
        ["", "lexical only", f"{f2(lx['top1'])} / {f2(lx['top3'])} / {f2(lx['mrr'])}"],
        ["", "hybrid, TF-IDF fallback", f"{f2(thy['top1'])} / {f2(thy['top3'])} / {f2(thy['mrr'])}"],
        ["", "random choice, top-1 / top-3", f"{f2(mm['random_expectation_top1'])} / {f2(mm['random_expectation_top3'])}"],
        ["Conflict check", "literal / paraphrased links flagged", f"{lit_det}/{lit_n} / 0/{para_n}"],
        ["", "false flags, clean pairs", f"0/{cf['clean_pairs_checked']}"],
    ], widths=[1.15, 1.45, 0.8], size=7, align=["l", "l", "c"])
    P.figure(figs["results"], "(a) Decision model against baselines, with the ceiling set by the synthetic labels. (b) Top-1 ranking accuracy on the probe set for three score configurations with two embedders.")
    P.para(f"**Decision model.** Accuracy {f2(sh['accuracy'])} is only {f2(ceil - sh['accuracy'])} below the {f2(ceil)} ceiling of the labels, and it is {f2(sh['accuracy'] - F.BASELINES['majority_class']['accuracy'])} above the majority baseline "
           f"({f2(F.BASELINES['majority_class']['accuracy'])}). Accept and reject are found (recall {f2(F.PER_CLASS['accept']['recall'])} and {f2(F.PER_CLASS['reject']['recall'])}) but borderline is not "
           f"(recall {f2(F.PER_CLASS['borderline']['recall'])}): 45 of 124 borderline papers were called accept and 70 reject. Over five splits accuracy varies from {f2(seeds['accuracy']['min'])} to {f2(seeds['accuracy']['max'])}. "
           f"On the four real PDFs, including the base paper, the model answered borderline every time with confidence {f2(min(r['ml_confidence'] for r in real))} to {f2(max(r['ml_confidence'] for r in real))}, so its signal carries no "
           "evidence about real papers and the interface labels it as synthetic.")
    P.para(f"**Ranking.** With sentence embeddings the hybrid score ranks an acceptable reviewer first for {pct(hy['top1'], 0)} of the probes, against {pct(mm['random_expectation_top1'], 0)} for a random choice, "
           f"and in the top three for {pct(hy['top3'], 1)}. Semantic similarity alone is slightly better ({pct(se['top1'], 1)}), lexical overlap alone is clearly worse ({pct(lx['top1'], 1)}), and the offline fallback falls to "
           f"{pct(thy['top1'], 0)}, because its vocabulary is fitted once on the first request and then frozen. The hybrid terms therefore do not improve ranking on this probe set; their value is the explanation and "
           f"the availability and conflict terms, which the probe set does not test. Ranking is fast with six reviewers ({scal[0]['median_ms']:.0f} ms) but every profile is re-embedded on every request, so 500 reviewers take {scal[-1]['median_ms'] / 1000:.1f} s.")
    P.para(f"**Conflicts.** All {lit_det} literal links (conflict terms, affiliations, full names) were flagged and the penalty moved the reviewer to the bottom of the ranking; none of the {para_n} paraphrased links "
           f"(a reworded affiliation, a first name only) was found, and there were no false flags in {cf['clean_pairs_checked']} clean pairs. Detection is string matching, not a co-authorship check.")
    P.para(f"**Speed.** The deterministic path needs {http['analyze_demo_3_pages']['median_ms'] / 1000:.1f} s per analysis over HTTP (median of {http['analyze_demo_3_pages']['n']}); "
           f"reading and ranking need well under a second apart from OpenAlex ({demo['Literature (OpenAlex)'] / 1000:.1f} s). With the language model on, one analysis took {llm_on['ieee_base_paper_30_pages']} to "
           f"{llm_on['reviewgraph_17_pages_via_browser']} s, of which the three-step review alone took {llm_s:.0f} s for {demo['_ai_tokens_all_steps']:,} generated tokens (about 3 tokens per second).")
    thr = {r["threshold"]: r for r in F.THR}
    P.para(f"**Confidence and score separation.** The decision model's confidence is informative but weak: papers with confidence of at least 0.6 are {pct(thr[0.6]['coverage'], 0)} of the test set at "
           f"{f2(thr[0.6]['accuracy_on_kept'])} accuracy, at least 0.7 are {pct(thr[0.7]['coverage'], 0)} at {f2(thr[0.7]['accuracy_on_kept'])}, and the 11 papers above 0.8 reach {f2(thr[0.8]['accuracy_on_kept'])}; "
           "no setting approaches the accuracy a clean label would allow. For ranking, the first-ranked reviewer leads the second by "
           f"{mm['mean_gap_rank1_rank2']:.1f} points on average over the probe set, so a Strong or Good band is usually not reached for short abstracts, and the bands should be read as relative to the pool.")
    P.table("Real PDFs through the pipeline", ["Paper", "Pages", "Words", "Struct.", "Sections", "Decision"], [
        ["Demo fixture", str(real[0]["pages"]), f"{real[0]['words']:,}", str(real[0]["structural_score"]), f"{len(real[0]['sections_detected'])}/9", f"{real[0]['ml_label']} {f2(real[0]['ml_confidence'])}"],
        ["Survey {r:6}", str(real[1]["pages"]), f"{real[1]['words']:,}", str(real[1]["structural_score"]), f"{len(real[1]['sections_detected'])}/9", f"{real[1]['ml_label']} {f2(real[1]['ml_confidence'])}"],
        ["ReViewGraph {r:7}", str(real[2]["pages"]), f"{real[2]['words']:,}", str(real[2]["structural_score"]), f"{len(real[2]['sections_detected'])}/9", f"{real[2]['ml_label']} {f2(real[2]['ml_confidence'])}"],
        ["Base paper {r:1}", str(real[3]["pages"]), f"{real[3]['words']:,}", str(real[3]["structural_score"]), f"{len(real[3]['sections_detected'])}/9", f"{real[3]['ml_label']} {f2(real[3]['ml_confidence'])}"],
    ], widths=[0.95, 0.4, 0.5, 0.45, 0.55, 0.75], size=7, align=["l", "c", "c", "c", "c", "c"])
    P.para("**Real papers.** Table III shows that the extraction and signals behave sensibly on a three-page fixture and on three real 17- to 30-page papers: 6 to 9 of the 9 expected sections are found and the "
           "structural score stays between 65 and 76. The score is a heuristic with unvalidated weights and cannot rank papers by quality; it mainly flags missing sections, short methodology text and sparse references. "
           "The fixture is a generated document, not a real submission.")
    P.figure(figs["assessment"],"Output screen: analysis of a real 17-page paper, showing the structural score, concerns, top reviewer, decision signal and the language-model status.")
    P.figure(figs["reviewers"], "Output screen: top-ranked reviewer with the auditable score breakdown (expertise similarity 0.260, method overlap 0.275, availability 1.0).")
    P.para("**Failure cases.** (1) For the 17-page paper in Fig. 5 and 6 the best reviewer scored only 28.4 of 100 and two reviewers tied; the NLP reviewer ranked fourth, because the demo pool has no "
           "reviewer on language-model reviewing. Ranks also skip a number when an inactive reviewer is filtered out afterwards. (2) The two misses on the probe set were a malware-evasion abstract assigned to the "
           "applied-statistics reviewer instead of the security reviewer and a cross-area log-analysis abstract. (3) For the base paper's PDF the introduction was not detected, because the heading is a roman numeral, "
           "and the title heuristic returned the DOI line. (4) The title of the survey PDF contains a question mark, which made OpenAlex answer HTTP 400, so related work was reported unavailable. "
           "(5) The language-model text for the 17-page paper misdescribes its datasets, which is why it is shown as generated text that can contain errors. (6) The coverage chart's novelty value is a fixed 55; novelty is not measured.")
    pa, pt = mm["per_area_top1"], tf["per_area_top1"]
    P.para(f"**Per-area results and uncertainty.** The probe set has six abstracts for each of six areas plus four cross-area abstracts with two acceptable reviewers. With sentence embeddings the hybrid score is right "
           f"for all six abstracts in five areas and five of six in security, and for {pa['cross-area']['correct']} of 4 cross-area abstracts; the fallback embedder drops to {pt['Reviewer Alpha']['correct']} of 6 in vision and "
           f"{pt['Reviewer Delta']['correct']} of 6 in security. With 40 probes the 95 % binomial interval around {pct(hy['top1'], 0)} is about +/-{1.96 * (hy['top1'] * (1 - hy['top1']) / 40) ** 0.5 * 100:.0f} points, "
           "so the difference between the hybrid and the semantic-only score (one abstract) is within noise, while the gap to lexical-only is not.")
    P.para("**Threats to validity.** The reviewer profiles and the probe abstracts were written by the same team, which favours embedding similarity; the six profiles are far apart in topic, so the task is easier than "
           "a real pool of hundreds of overlapping researchers; the decision model was trained and tested on data of one synthetic kind; the language-model text was not rated by human reviewers; no user study was run; "
           "and every timing comes from one CPU-only machine. These limits are why the numbers above are read as evidence that the pipeline works, not as a benchmark.")
    P.para("**Comparison with the base paper.** The comparison is context only. The base paper reports MRR@3 up to 0.78 on 663 real conference papers and 524 reviewers with historical assignments as labels, "
           f"whereas PeerScope reports MRR {f2(hy['mrr'])} on 40 team-written abstracts and six demo reviewers, and adds paper assessment, availability and conflict terms that the base paper did not benchmark. "
           "Data, task size, labels and metric (rank of the first acceptable reviewer, not MRR@3 over three) differ, so no claim of superiority is made.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para("PeerScope delivers a working local pipeline that turns a PDF into an assessment and an auditable reviewer ranking. Against the six objectives: corpus building is partial (stored analyses and a "
           "six-profile reviewer directory, no real publication corpus); topic, method and keyword extraction and embedding-based reviewer vectors are done with simple lexicons and profile text; ranking is done and "
           f"measured; the preliminary assessment is done except for novelty; and evaluation against expert judgement is only partial, using the team's own labels. The key finding is that the explicit hybrid score "
           f"ranks well on the probe set ({pct(hy['top1'], 0)} top-1) but a plain embedding does as well, and that the decision model's {f2(sh['accuracy'])} accuracy reflects the synthetic labels, not real peer-review decisions. "
           "Other limits are the six demo reviewers, literal-match conflict detection, minutes-long CPU generation, an unvalidated structural weighting and the defects listed above.")
    P.para("Future work: evaluate ranking on real conference assignments with independent expert labels; train the decision model on real review data such as PeerRead {r:22}; build reviewer profiles from "
           "publication records; add a co-authorship conflict check and a capacity-aware assignment optimiser; cache reviewer embeddings; sanitise the literature query and recognise roman-numeral headings; "
           "and defend the language-model step against hidden instructions in the PDF.")

    P.references()
    P.save(path)
    return path, P.order


if __name__ == "__main__":
    out = os.path.join(F.BATCH, "19.IEEE_Paper.docx")
    path, order = build(out)
    print(path, "refs:", len(order), order)
