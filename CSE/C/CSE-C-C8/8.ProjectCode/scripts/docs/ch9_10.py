"""Novelty, contributions, scope, limitations, walkthroughs, decisions, conclusion (Chapter 9) and future scope (Chapter 10)."""

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def src(rel, start=None, end=None):
    """Lines start..end (1-based, inclusive) of a source file of 8.ProjectCode, for code listings."""
    import os

    lines = open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    return "\n".join(lines[(start or 1) - 1:end or len(lines)]).rstrip("\n")


def c(*keys):
    """Citation string such as [1], [6] from CITE keys."""
    return "[" + ", ".join(str(R[k]) for k in keys) + "]"


def _v():
    """Frequently quoted measured values, read from the facts module."""
    hy = F.MINILM["full_hybrid_shipped_weights"]
    tf = F.TFIDF["full_hybrid_shipped_weights"]
    conf = F.MINILM["conflict"]
    kinds = conf["detected_by_kind"]
    lit_n = sum(kinds[k]["detected"] for k in ("conflict term", "affiliation", "full name"))
    lit_t = sum(kinds[k]["n"] for k in ("conflict term", "affiliation", "full name"))
    par_n = sum(kinds[k]["detected"] for k in ("paraphrased affiliation", "first name only"))
    par_t = sum(kinds[k]["n"] for k in ("paraphrased affiliation", "first name only"))
    st = (F.LATENCY.get("pipeline_stages") or {}).get("demo", {})
    llm_s = st.get("Local AI review (3 steps)", 0) / 1000.0
    http_on = F.LATENCY.get("http_llm_on_s", {})
    return {
        "hy": hy, "tf": tf, "lit_n": lit_n, "lit_t": lit_t, "par_n": par_n, "par_t": par_t,
        "fp": conf["false_flags_on_clean_papers"], "pairs": conf["clean_pairs_checked"],
        "acc": F.pct(F.SHIPPED["accuracy"], 0), "acc2": F.f2(F.SHIPPED["accuracy"]), "f1": F.f3(F.SHIPPED["f1_macro"]),
        "auc": F.f2(F.SHIPPED["roc_auc"]),
        "dec": F.pct(F.DM["decisive_only"]["accuracy"], 0), "ceil": F.f2(F.GEN["best_possible_accuracy_from_phrases"]),
        "bord_rec": F.pct(F.PER_CLASS["borderline"]["recall"], 0),
        "seed_m": F.f3(F.SEEDS["accuracy"]["mean"]), "seed_sd": F.f3(F.SEEDS["accuracy"]["sd"]),
        "tot_s": f"{st.get('_total_ms', 0) / 1000.0:.0f}" if st else "several hundred",
        "llm_s": f"{llm_s:.0f}" if llm_s else "several hundred", "llm_min": f"{llm_s / 60:.1f}" if llm_s else "several",
        "http_lo": f"{min(v for k, v in http_on.items() if isinstance(v, (int, float))):.0f}" if http_on else "several hundred",
        "http_hi": f"{max(v for k, v in http_on.items() if isinstance(v, (int, float))):.0f}" if http_on else "several hundred",
        "s6": F.MINILM["scaling_ms"][0]["median_ms"], "s500": F.MINILM["scaling_ms"][-1]["median_ms"] / 1000.0,
        "s500_tf": F.TFIDF["scaling_ms"][-1]["median_ms"],
    }


# ------------------------------------------------------------------ document 9
def novelty_blocks():
    v = _v()
    base, survey = c("base"), c("survey_wu")
    return [
        P(f"{F.PRODUCT} does not propose a new learning algorithm or a new similarity measure, and we do not claim one. Its building blocks (TF-IDF, logistic regression, sentence embeddings, "
          "cosine similarity, an instruction-tuned language model, a public scholarly index) are standard. What is new is the combination, the way availability and conflict of interest are brought "
          "inside an auditable score, the delivery as a complete local application, and the care taken to measure the parts and to say where the measurement is weak. This section states the "
          "difference from the base paper first and then separates what is new from what is not."),
        H2("2.1 Difference from the base paper"),
        P(f"The base paper {base} studies the reviewer assignment problem. Its central idea is to restrict language models to inducing keywords, to choose among an ensemble's candidate lists with a judge model, "
          "to normalise the keywords deterministically and to store every intermediate artefact as an audit trail, so that a reviewer's score can be traced. It evaluates many matchers on 663 papers and "
          "524 reviewer profiles with MRR@3, P@3 and MAP@3. It does not assess the submission itself and leaves conflict of interest and workload outside its experiments. "
          f"The survey {survey} and the other works of the literature chapter address automated review and decision prediction, but not reviewer assignment."),
        TAB(f"{F.PRODUCT} and the base paper compared", ["Dimension", "Base paper [1]", F.PRODUCT, "What differs"],
            [["Problem", "Reviewer assignment: affinity between papers and reviewers", "Preliminary paper assessment plus reviewer ranking in one tool", "Both halves of the editorial workload in one application"],
             ["Input", "Titles, summaries and abstracts of 663 papers; up to 20 publications of each of 524 reviewers", "An uploaded PDF (up to 20 MB) and six demo reviewer profiles", "Raw PDF intake and text extraction; far smaller reviewer data"],
             ["Keyword step", "Ensemble of producer LLMs plus a judge LLM, then lemmatisation", "Frequency keywords and fixed method and topic lists", "No LLM in the ranking path; weaker, but deterministic and cheap"],
             ["Similarity", "TF-IDF, Jaccard, SBERT, cross-encoder, keyword graphs", "all-MiniLM-L6-v2 cosine (TF-IDF fallback) plus keyword and method overlap", "Same encoder family as the base paper's SBERT baseline; one fixed hybrid"],
             ["Auditability", "Stored prompts, model ids, candidate lists, score matrices", "Per-recommendation breakdown of every weighted term, matched terms and an explanation", "Shown in the interface, not only stored"],
             ["Availability and conflict of interest", "Left to a downstream solver; not benchmarked", "Inside the score: load term and a 0.60 penalty", "Measured only by an injection test"],
             ["Paper assessment", "None", "Structural signals, decision signal, local-LLM critique, OpenAlex context", "Not present in the base paper"],
             ["Evaluation", f"663 papers, 524 reviewers, historical assignments as labels, paired tests", f"40 team-written probe abstracts, {F.REVIEWER_POOL} demo reviewers, synthetic decision data", "Far weaker; numbers are not comparable"],
             ["Deliverable", "Method and offline study", "Runnable local web application with directory, history and export", "A usable system around the method"]],
            widths=[1.0, 1.9, 1.9, 1.8], align=["l", "l", "l", "l"], size=9),
        P("The batch documents describe the project as reusing the base paper's technique. In fairness to the paper we state what was taken from it: the auditable principle (every recommendation "
          "can be explained from its parts) and the sentence encoder family. The keyword-induction ensemble, the judge, the keyword graphs and the statistical protocol were not reproduced."),
        H2("2.2 What is standard and what is new"),
        TAB("Standard components and project-specific elements", ["Element", "Standard or new", "Comment"],
            [["TF-IDF with logistic regression", "Standard", f"Textbook text classification {c('tfidf', 'idf', 'sklearn')}"],
             ["Sentence embeddings and cosine similarity", "Standard", f"Pre-trained encoder used unchanged {c('sbert', 'minilm')}"],
             ["Local instruction-tuned language model", "Standard", f"Open-weight model loaded through a public library {c('qwen25', 'hf_transformers')}"],
             ["OpenAlex retrieval", "Standard", f"Public API {c('openalex')}"],
             ["Weighted score with itemised terms, availability and conflict penalty in one number", "Project-specific", "Brings workload and conflict into the same auditable breakdown; weights are unfitted"],
             ["Visible fall-back for every optional component", "Project-specific", "The interface reports an unavailable model, literature service or decision artefact instead of hiding it"],
             ["Structural signals from section detection and reference parsing", "Project-specific", "Transparent heuristics with documented weights; not validated against human judgement"],
             ["Synthetic-data warning carried from the metrics file to the interface", "Project-specific", "The figures cannot be mistaken for a benchmark"],
             ["Local-first processing with no account", "Design choice", "Manuscripts stay on the machine except title and keyword text sent to OpenAlex"],
             ["Honest evaluation: baselines, five splits, label-ceiling analysis, probe set, injection test, stage timings", "Project-specific", "States which numbers are weak and why"]],
            widths=[2.8, 1.2, 2.6], align=["l", "c", "l"], size=9.5),
    ]


def contribution_blocks():
    v = _v()
    hy, tf = v["hy"], v["tf"]
    return [
        P("The key contributions, in the order in which the evidence supports them, are:"),
        N("**An end-to-end local application.** One tool takes a research-paper PDF through extraction, assessment, literature context and reviewer matching, stores the result and exports it as JSON or PDF "
          f"({F.LOC['backend_app']:,} lines of backend code, {F.LOC['frontend_src']:,} lines of web interface, {F.PYTEST_TOTAL} automated tests and {F.SMOKE_TOTAL} end-to-end smoke checks, all passing).",
          f"**An auditable matching score.** Every recommendation shows the weighted terms of 0.55 expertise similarity, 0.20 keyword overlap, 0.15 method and topic overlap and 0.10 availability, minus a 0.60 conflict penalty, with matched terms and a "
          f"plain-language explanation; on 40 probe abstracts the hybrid ranking puts an acceptable reviewer first in {F.pct(hy['top1'], 1)} of cases with sentence embeddings.",
          f"**Availability and conflict of interest inside the score.** All {v['lit_n']} of {v['lit_t']} literal conflict links injected into papers were flagged and none of {v['pairs']} clean paper-reviewer pairs was flagged falsely; "
          f"the {v['par_t']} paraphrased links were missed, and this is reported.",
          f"**A hybrid assessment with honest fall-backs.** Structural signals, a trained decision signal and a local-LLM critique are combined, each reporting its own status; the offline TF-IDF fall-back reaches top-1 {F.pct(tf['top1'], 1)} "
          "against the sentence-embedding result, and the interface says which one was used.",
          f"**A frank account of the decision model.** Accuracy {v['acc2']} (macro F1 {v['f1']}) on a synthetic corpus whose labelling caps accuracy near {v['ceil']}, accept against reject separated {v['dec']} of the time, borderline almost never predicted, "
          f"five-split mean {v['seed_m']} with a standard deviation of {v['seed_sd']}, and three baselines on the same split.",
          f"**Measured cost of local AI.** A stage-by-stage timing shows the local language model takes about {v['llm_s']} s of the roughly {v['http_lo']}-{v['http_hi']} s a full analysis needs on a CPU-only PC, whereas the deterministic path answers in about a second.",
          "**A reproducible evaluation kit.** `scripts/measure_metrics.py`, `scripts/measure_latency.py`, the probe set and a verifier regenerate every number quoted in the documents."),
    ]


# ------------------------------------------------------------------ document 10
def scope_blocks():
    v = _v()
    hy = v["hy"]
    return [
        P("The scope is what the delivered system does and was tested to do. Each in-scope item exists in the code base and is covered by the evidence named in the last column."),
        TAB("In scope", ["Capability", "Detail", "Evidence"],
            [["PDF intake", f"PDF files up to {F.UPLOAD_LIMIT_MB} MB; extension, content type, empty-file and %PDF header checks", "Smoke test: non-PDF and fake PDF rejected (400)"],
             ["Extraction", "Page text, normalisation, title heuristic, nine section types, reference parsing", "Four real PDFs, test_pdf_extraction"],
             ["Structural signals", "Structure, evidence, method clarity and presentation combined into one score", "test_features; Chapter 8 real-paper table"],
             ["Decision signal", "Three-class TF-IDF and logistic-regression model with probabilities", f"Accuracy {v['acc2']} on synthetic data (limits stated)"],
             ["Review", "Deterministic review always; three-step Qwen2.5-1.5B critique when it loads", f"Stage timing; about {v['llm_s']} s on a CPU"],
             ["Literature grounding", "Six OpenAlex works ranked by similarity, 8 s timeout, visible failure status", "Three live queries, one failure case"],
             ["Reviewer matching", "Embedding, keyword, method, availability and conflict terms; filters; breakdown", f"Top-1 {F.pct(hy['top1'], 1)} on 40 probes"],
             ["Reviewer directory", "Create, update, delete, activate, CSV import and export, conflict terms, load", "test_reviewer_crud; smoke test"],
             ["History and export", "Stored analyses; JSON and PDF export", "Smoke test export checks"],
             ["Interface", "Landing page, dashboard, analysis, directory, model performance, history, saved analysis, about", "Seventeen real screen captures"]],
            widths=[1.5, 3.3, 1.8], align=["l", "l", "l"], size=9.5),
        H2("1.1 Out of scope"),
        B("**Judging scientific correctness or novelty.** The assessment reports structure and evidence; it does not verify claims, and the novelty value of the coverage chart is a fixed placeholder.",
          "**Predicting real review outcomes.** The decision signal comes from synthetic data and is a demonstration of the pipeline only.",
          "**Global assignment.** No optimiser balances load across a whole conference, and there is no bidding or reviewer self-selection.",
          "**Harvesting publication records.** Reviewer expertise comes from a free-text profile and publication titles typed or imported by the editor; there is no h-index, citation count or database harvesting.",
          "**Accounts, roles and multi-user operation.** There is no login; the interface and the API are open on the local machine.",
          "**Scanned documents, other languages and other file types.** Only English-language PDFs with a text layer are analysed.",
          "**Cloud hosting and mobile clients.** The application runs on one personal computer."),
        H2("1.2 Users, inputs and outputs"),
        TAB("Users, inputs and outputs", ["Item", "Description"],
            [["Editor or programme chair", "Uploads a submission, reads the assessment and the ranked list, exports the report"],
             ["Reviewer-directory administrator", "Maintains the profiles, conflict terms and loads (the same person in practice; there are no separate accounts)"],
             ["Input", "A research-paper PDF, optional filters (active only, minimum score, topic, method), reviewer profiles typed or imported as CSV"],
             ["Output", "On screen: structural score, decision signal, review, literature, ranked reviewers with audit breakdown. Files: JSON and PDF report"],
             ["External services", "OpenAlex (title and keyword text only); Hugging Face for the first download of models"]],
            widths=[1.9, 4.7], align=["l", "l"], size=10),
    ]


def assumption_blocks():
    return [
        P("The results hold under these assumptions; where one fails, the quality of the output is expected to fall."),
        B("**English-language papers with a text layer.** The extraction reads the PDF text; scanned pages without a text layer give almost nothing, and the interface warns when fewer than 50 words are found.",
          "**Conventional section headings.** Section detection matches headings such as Introduction, Methodology or Conclusion on short lines; roman-numeral headings are not recognised.",
          "**A maintained reviewer directory.** Matching quality depends on the profile text, topics, methods and conflict terms filled in by the editor; the demo profiles are placeholders.",
          "**Conflict terms are written the way they appear in papers.** Detection compares literal strings, so affiliations and names must be entered in the form used in manuscripts.",
          "**One trusted user at a time on a local machine.** No authentication, open cross-origin access and a single SQLite file are acceptable only in that setting.",
          "**An editor reads the output as advice.** The assessment and the ranking are decision support; the final judgement stays with a qualified human.",
          "**Internet access is occasional.** It is needed for the first model download and for OpenAlex; without it the literature step reports `unavailable` and the rest continues.",
          f"**A modern PC.** Windows, Python 3.11, Node.js 18 or newer and about 6 GB of free memory for the local language model. Timings are for the measured {F.ENV['cpu']} with {F.ENV['ram_gb']} GB of memory and no GPU.",
          "**The synthetic decision data are understood as such.** The decision signal is read as a demonstration; its confidence is not a probability of acceptance."),
    ]


def limitation_blocks():
    v = _v()
    hy, tf = v["hy"], v["tf"]
    rows = [
        ["L1", "Decision model trained on 1,400 synthetic, template-generated rows; the public PeerRead probe returned no data",
         f"Accuracy {v['acc2']} is close to the ceiling of about {v['ceil']} set by the labelling; borderline recall {v['bord_rec']}; all four real papers were labelled borderline (confidence 0.55-0.66); not evidence of predicting real decisions",
         "Train on real review data (PeerRead, OpenReview) with decisions"],
        ["L2", f"Reviewer pool of {F.REVIEWER_POOL} demo profiles; no publication histories, no h-index",
         "Ranking quality on a real committee is unknown; the abstract's h-index and history ranking is not implemented", "Import real profiles and publication lists"],
        ["L3", "Matching evaluated on 40 abstracts written by the team with the team's labels",
         f"Top-1 {F.pct(hy['top1'], 1)} (embeddings) and {F.pct(tf['top1'], 1)} (fall-back) are optimistic and not comparable with the base paper", "Independent expert labels on real submissions"],
        ["L4", "TF-IDF fall-back fitted once on the first request and then frozen",
         f"Offline matching is weaker (top-1 {F.pct(tf['top1'], 1)} against {F.pct(hy['top1'], 1)}) and depends on which paper came first", "Fit on the reviewer profiles or ship a fixed vocabulary"],
        ["L5", "Novelty is not assessed; the coverage chart shows a fixed Novelty value of 55",
         "The review cannot say how original a paper is; OpenAlex results are context, not a novelty test", "A citation- or embedding-based novelty measure"],
        ["L6", "Structural weights (0.35, 0.25, 0.25, 0.15) and thresholds are unfitted heuristics; section detection is regex based",
         "Roman-numeral headings missed (the IEEE base paper: no introduction, title returned as the DOI line); words such as model or approach can mark a methodology heading", "Fit weights on human ratings; layout-aware parsing"],
        ["L7", "Conflict detection is literal string matching on the first 3,000 characters",
         f"{v['lit_n']} of {v['lit_t']} literal links found, {v['par_n']} of {v['par_t']} paraphrased links found, {v['fp']} false flags on {v['pairs']} clean pairs; co-authorship is not checked", "Co-authorship and affiliation graphs; fuzzy matching"],
        ["L8", "Local Qwen2.5-1.5B on a CPU at about three tokens per second; output not fact-checked",
         f"About {v['llm_s']} s for the review step; the synthesis of a real paper contained wrong statements; hidden text in a PDF could steer it {c('inject_aro', 'keuper')}", "Quantised or GPU model, claim checking, injection filter"],
        ["L9", "Every reviewer profile is re-embedded on every request",
         f"Ranking takes {v['s6']:.0f} ms for 6 reviewers and {v['s500']:.1f} s for 500 with sentence embeddings", "Cache profile embeddings, update on change"],
        ["L10", "OpenAlex needs internet and the query is not sanitised",
         "A title containing a question mark gives HTTP 400 and the status `unavailable` (the survey PDF)", "Strip punctuation; cache results"],
        ["L11", "No authentication, open CORS, single user; timestamps stored as UTC and shown without a zone; a corrupt but %PDF-headed file returns 200; a CSV without names imports 0 rows silently",
         "Safe only on one trusted machine; times read about 5.5 hours behind local time", "Authentication, zone-aware times, stricter validation"],
        ["L12", "Items of the batch abstract not implemented: deep-learning area classifier, originality score, readability indices beyond sentence length, scope alignment with a venue",
         "Objectives 2 and 5 are met with simple methods only", "See Chapter 10"],
    ]
    return [
        P("The limitations below are real and affect how the system should be used. Each is listed with its effect and with what could reduce it."),
        TAB("Limitations", ["No.", "Limitation", "Effect", "What would help"], rows,
            widths=[0.4, 2.1, 2.3, 1.8], align=["c", "l", "l", "l"], size=9),
    ]


def not_measured_blocks():
    return [
        P("Honesty about gaps matters more than a longer list of numbers. The following were **not measured**, and nothing in these documents should be read as a claim about them:"),
        B("accuracy of the decision model on real peer-review decisions;",
          "reviewer-assignment quality against independent expert judgement or against the real assignments of a conference;",
          "the quality of the language-model critique (no human rated it, and no factual-consistency check was run);",
          "a user study with editors or reviewers, and the time saved in a real editorial workflow;",
          "behaviour on scanned PDFs, non-English papers and unusual layouts beyond the four real papers tried;",
          "performance with a GPU, with a quantised model or under many simultaneous users;",
          "the effect of tuning the matching weights (the shipped weights were not searched), and the sensitivity of the structural weights;",
          "robustness to deliberately manipulated PDFs (hidden instructions), although the literature shows it is a risk."),
        P("The 40-abstract probe result and the conflict injection test were measured, but both use material written by the team and are optimistic for that reason; they are not used as evidence of real-world accuracy."),
    ]


# ------------------------------------------------------------------ document 12
def walkthrough_blocks():
    return [
        P("This section walks through the code that carries the design. The listings are copied from the repository at the state in which the results were measured."),
        H2("3.1 From a PDF to sections"),
        CODE(src("app/services/pdf_extract.py", 7, 17), 8.5),
        CODE(src("app/services/pdf_extract.py", 87, 112), 8.5),
        P("Every short line (80 characters or fewer) is lower-cased, stripped of digits, dots and spaces at its ends and tested against the pattern lists of the nine section types. The first heading found for a type "
          "starts that section, which ends at the next heading; word counts and a 600-character preview are stored. The patterns are deliberately simple, which explains two measured weaknesses: `I. INTRODUCTION` "
          "does not match `^\\s*1?\\s*introduction\\s*$`, so the IEEE base paper reports no introduction, and loose patterns such as `model` or `approach` can mark an ordinary heading as the methodology."),
        H2("3.2 Structural score"),
        CODE(src("app/services/features.py", 56, 63), 8.5),
        P("Structure completeness is the share of nine expected sections found. Evidence coverage grows with references per page (22 points each, plus 10 when an experiments or results section exists) and is capped at 100. "
          "Method clarity is 100 for a methodology section of at least 120 words, 70 for a shorter one, 45 when only method terms occur and 25 otherwise. Presentation rewards an average sentence length of 12 to 26 words "
          "and few very short sections. The four values are combined as 0.35, 0.25, 0.25 and 0.15. None of these constants was fitted to human ratings."),
        H2("3.3 Decision signal"),
        CODE(src("app/services/ml_predict.py", 29, 41), 8.5),
        CODE(src("app/services/ml_predict.py", 62, 80), 8.5),
        P("The classifier is loaded lazily from the two joblib artefacts; if either is missing the function returns `model_unavailable` instead of raising, and the interface shows that state. The input is the title, "
          "the summary and the first 4,000 characters of the text, vectorised by the saved word and character TF-IDF pair. Class names come from the metrics file, because the label encoder sorted them alphabetically "
          "(accept, borderline, reject). The returned dictionary carries the label, its probability and all three probabilities, together with a note that the signal is historical and not a judgement of correctness."),
        H2("3.4 Overlap and conflict check"),
        CODE(src("app/services/matching.py", 18, 30), 8.5),
        CODE(src("app/services/matching.py", 48, 63), 8.5),
        P("`_overlap` counts exact shared terms plus substring hits (reported as `x~y`) and divides by the larger set, so a long profile is not rewarded for length. `detect_conflict` lower-cases the first 3,000 characters of the "
          "paper and looks for the reviewer's conflict terms, the full display name, or the affiliation. Any hit sets `conflicted` and supplies a reason that the interface prints beside the reviewer. The test is a plain "
          "substring test, which is why reworded affiliations and first-name-only mentions are not found. The weighted loop that turns these values into the 0-100 score is listed in Chapter 6."),
        H2("3.5 Local language-model review with a visible fall-back"),
        CODE(src("app/services/review_synthesis.py", 119, 144), 8.5),
        P("The deterministic review is always built first, so a result exists whatever happens next. If the model cannot be loaded, the function records `llm_status = unavailable` with the reason and returns the deterministic "
          "review. Otherwise three prompts are run on the first 6,000 characters: analyse, critique and synthesise. If the final generation fails or is empty the status becomes `error` and the deterministic review is kept. "
          "On success the three texts, the model name and `source = deterministic+llm` are added. The three generations produce about 1,400 tokens and account for almost all of the time of an analysis."),
        H2("3.6 Validation at the analysis endpoint"),
        CODE(src("app/main.py", 162, 173), 8.5),
        CODE(src("app/main.py", 181, 189), 8.5),
        P("The file name must end in `.pdf`, the declared content type must mention pdf or be an octet stream, the body must not be empty, must not exceed the configured limit (413) and must begin with `%PDF`. "
          "A directory without reviewers is refused (400). A `ValueError` from the pipeline becomes a 400 with its message; any other exception is logged and returned as a generic 500, so internal details do not reach the "
          "client. The temporary file is removed in a `finally` block."),
    ]


def decision_blocks():
    v = _v()
    return [
        P("Each decision below is stated with the alternative that was available and the reason for the choice."),
        TAB("Implementation decisions", ["Decision", "Alternative", "Reason"],
            [["Process papers locally; send only title and keywords to OpenAlex", "Cloud language-model API", "Manuscripts are confidential; no key, no cost, no data leaves the machine; the price is speed and quality"],
             ["Always build the deterministic review, add the LLM when available", "Fail the request without the model", "A useful result exists on any machine; the interface shows which components ran"],
             ["Visible status for every optional part (LLM, literature, decision model)", "Silent fall-back", "Nothing is fabricated and the editor knows what to trust"],
             ["TF-IDF word and character features with logistic regression", "Fine-tuned transformer classifier", f"Small, fast, inspectable; with synthetic labels a larger model could not add real signal (accuracy {v['acc2']} against a ceiling near {v['ceil']})"],
             ["`class_weight=balanced`", "Unweighted training", "Gives minority classes weight; macro recall rises to 0.65 from 0.56 while accuracy changes little"],
             ["all-MiniLM-L6-v2 cosine as the expertise term", "Larger or domain-specific encoder (SPECTER)", f"Small enough for a CPU, the same family as the base paper's baseline; semantic-only ranking reached top-1 {F.pct(F.MINILM['semantic_similarity_only']['top1'], 1)} on the probe set"],
             ["Weights 0.55, 0.20, 0.15, 0.10 and a 0.60 penalty", "Learned weights", "No real labels to fit them; documented, configurable by environment variable and shown in every breakdown; semantic-only scored a little higher on the probe set, so the lexical terms mainly serve explanation"],
             ["Availability as 1 - load / maximum load", "Hard capacity filter", "Keeps a loaded but expert reviewer visible with a lower score; an inactive reviewer can be filtered"],
             ["Conflict as a score penalty, not removal", "Exclude conflicted reviewers", "The editor can see who was penalised and why, and decide"],
             ["Two SQLite tables, result stored as a JSON text column, no foreign key", "Normalised schema", "A saved analysis re-opens and exports exactly as computed; ranked reviewers are a snapshot that must not change if a profile is edited later"],
             ["No login or roles", "Authentication", "Single-user local tool; adding it was outside the time available and is listed as future work"],
             ["Load the language model on first use, with a fall-back size", "Load at start-up", "Start-up stays fast; memory is only used when a review is requested"],
             ["Report the synthetic nature of the decision data in the interface", "Show the metrics alone", "The 55 % accuracy cannot be mistaken for a benchmark result"]],
            widths=[2.2, 1.8, 2.6], align=["l", "l", "l"], size=9.5),
    ]


# ------------------------------------------------------------------ chapters 9 and 10
def _conclusion_compact():
    v = _v()
    hy, tf = v["hy"], v["tf"]
    return [
        H2("9.1 Summary"),
        P(f"{F.PRODUCT} is a working local application that turns a research-paper PDF into a preliminary assessment and an auditable ranking of candidate reviewers. It extracts the text, detects sections and references, "
          "computes structural signals, adds a decision signal from a TF-IDF and logistic-regression model, drafts a critique with a local Qwen2.5-1.5B model when it can be loaded, retrieves related work from OpenAlex "
          "and ranks reviewers with a score combining embedding similarity, keyword and method overlap, availability and a conflict penalty. Every result and its audit breakdown is shown in a React interface and stored for export. "
          "The whole system runs on one CPU-only PC."),
        H2("9.2 Objectives achieved and key findings"),
        TAB("Objectives against outcomes", ["No.", "Status", "Outcome"],
            [["1", "Partly met", f"Analyses stored; {F.REVIEWER_POOL} demo reviewer profiles with CSV import; no real publication corpus; decision data synthetic"],
             ["2", "Met (simple)", "Frequency keywords, a 21-term method lexicon and 18 topic hints"],
             ["3", "Met", "Profile text and titles embedded with all-MiniLM-L6-v2; no real publication history"],
             ["4", "Met", f"Top-1 {F.pct(hy['top1'], 1)} with embeddings, {F.pct(tf['top1'], 1)} with the fall-back, on 40 probe abstracts"],
             ["5", "Met except novelty", "Structure, evidence, method clarity, presentation, decision signal and critique; novelty inconclusive"],
             ["6", "Partly met", f"Team-written labels, not experts; {v['lit_n']} of {v['lit_t']} literal conflict links found, {v['par_n']} of {v['par_t']} paraphrased"]],
            widths=[0.4, 1.3, 4.9], align=["c", "c", "l"], size=9.5),
        B(f"Embedding similarity carries the matching: semantic-only top-1 {F.pct(F.MINILM['semantic_similarity_only']['top1'], 1)}, hybrid {F.pct(hy['top1'], 1)}, lexical overlap alone {F.pct(F.MINILM['lexical_only_keyword_and_method']['top1'], 1)}; the TF-IDF fall-back is weaker, so the interface states which embedder ran.",
          f"The decision model shows the pipeline works, not that it predicts real decisions: accuracy {v['acc2']}, macro F1 {v['f1']}, accept against reject {v['dec']} correct, borderline recall {v['bord_rec']}, accuracy ceiling near {v['ceil']}.",
          f"The local language model costs about {v['llm_s']} s of the {v['tot_s']} s of an analysis; without it a paper takes about a second. Conflict detection is reliable for literal links but blind to paraphrase.",
          f"Against the base paper {c('base')}, PeerScope adds paper assessment, availability and conflict handling and an application, and gives up its keyword-induction ensemble and large evaluation; results are not comparable."),
        H2("9.3 Applications and known limitations"),
        P("Applications: first-pass screening for an editor, a reviewer short list with reasons and conflict warnings, a teaching example of auditable decision support, and a local workflow where manuscripts must not leave the machine. "
          "Limitations: synthetic decision data, demo reviewer pool, team-written probe labels, no novelty assessment, literal conflict matching, a slow unverified local model, no authentication and no user study. "
          "It is a prototype for decision support, not the sole basis for publication decisions."),
    ]


def conclusion_blocks():
    if F.REPORT:
        return _conclusion_compact()
    return _conclusion_full()


def _conclusion_full():
    v = _v()
    hy, tf = v["hy"], v["tf"]
    base = c("base")
    return [
        H2("9.1 Summary"),
        P(f"{F.PRODUCT} is a working local application that turns a research-paper PDF into a preliminary assessment and an auditable ranking of candidate reviewers. A FastAPI service extracts the text with PyMuPDF, "
          "detects sections and references, computes structural signals, adds a historical decision signal from a TF-IDF and logistic-regression model, drafts a critique with a local Qwen2.5-1.5B model when it can be loaded, "
          "retrieves related work from OpenAlex and ranks reviewers with a score that combines sentence-embedding similarity, keyword and method overlap, availability and a conflict penalty. A React interface shows every "
          "result and its audit breakdown, and the analyses are stored and can be exported. The whole system runs on one CPU-only PC."),
        H2("9.2 Objectives achieved"),
        P("Of the six objectives, three were met (topics, methods and keywords were extracted; reviewer expertise was represented as comparable vectors; similarity-based ranking was computed and measured) and three were met in part. "
          "The table gives the status of each and the reason."),
        TAB("Objectives against outcomes", ["No.", "Objective", "Status", "Outcome"],
            [["1", "Build a corpus of papers and reviewer publication profiles", "Partly met", f"Analyses are stored; {F.REVIEWER_POOL} demo reviewer profiles with CSV import; no real publication corpus; decision data synthetic"],
             ["2", "Extract topics, methods and keywords with NLP", "Met (simple)", "Frequency keywords, a 21-term method lexicon and 18 topic hints"],
             ["3", "Represent reviewer expertise as comparable vectors", "Met", "Profile text and titles embedded with all-MiniLM-L6-v2; no real publication history"],
             ["4", "Compute semantic similarity to rank reviewers", "Met", f"Top-1 {F.pct(hy['top1'], 1)} with embeddings and {F.pct(tf['top1'], 1)} with the fall-back on 40 probe abstracts"],
             ["5", "Preliminary assessment of structure, novelty signals and completeness", "Met except novelty", "Structure, evidence, method clarity, presentation, decision signal and critique; novelty reported as inconclusive"],
             ["6", "Evaluate assignment quality against expert judgement and conflict handling", "Partly met", f"Team-written labels, not independent experts; {v['lit_n']} of {v['lit_t']} literal conflict links found, {v['par_n']} of {v['par_t']} paraphrased"]],
            widths=[0.4, 2.2, 1.0, 3.0], align=["c", "l", "c", "l"], size=9.5),
        H2("9.3 Key findings"),
        N(f"Sentence-embedding similarity is the signal that matters for matching: on the probe set semantic-only ranking reached top-1 {F.pct(F.MINILM['semantic_similarity_only']['top1'], 1)}, the shipped hybrid {F.pct(hy['top1'], 1)} and keyword-and-method overlap alone {F.pct(F.MINILM['lexical_only_keyword_and_method']['top1'], 1)}; the lexical terms mainly make the score explainable.",
          f"The offline TF-IDF fall-back is clearly weaker (top-1 {F.pct(tf['top1'], 1)}), so the interface must, and does, say which embedder was used.",
          f"Auditing is cheap and useful: because every term is returned, a wrong recommendation can be traced; in both probe misses the reviewer ranked first was Reviewer Gamma (applied machine learning and statistics), and the breakdown shows the expected reviewer's lower semantic term.",
          f"The decision model shows the pipeline works but not that it predicts real decisions: accuracy {v['acc2']}, macro F1 {v['f1']}, ROC-AUC {v['auc']}, accept against reject {v['dec']} correct, borderline recall {v['bord_rec']}, with the accuracy ceiling near {v['ceil']} fixed by the synthetic labelling.",
          f"The local language model dominates the cost: about {v['llm_s']} s of the {v['tot_s']} s that one analysis of the demo paper takes in-process; without it a paper is analysed in about a second.",
          f"Literal conflict detection is reliable ({v['lit_n']} of {v['lit_t']}, no false flags on {v['pairs']} pairs) but blind to paraphrase ({v['par_n']} of {v['par_t']}).",
          f"Compared with the base paper {base}, PeerScope adds paper assessment, availability and conflict handling and an application, and gives up its keyword-induction ensemble and its large, statistically tested evaluation; the results cannot be compared directly."),
        H2("9.4 Practical applications"),
        B("A first-pass screening aid for an editor or programme chair, showing at once whether a paper has the sections, references and method detail a review needs.",
          "A short list of reviewers with reasons, matched terms, workload and conflict warnings, to be checked by the editor before any invitation.",
          "A teaching example of auditable decision support: how a transparent score, visible fall-backs and honest metrics can be combined.",
          "A base for a departmental or small-conference workflow where manuscripts must stay on local machines."),
        H2("9.5 Known limitations"),
        P("The decision model rests on synthetic data, the reviewer pool is a set of demo profiles, the matching evidence comes from abstracts written by the team, novelty is not assessed, conflict detection is literal, "
          "the local model is slow and unverified, and the application has no authentication and has had no user study. It is a research and teaching prototype for decision support, not a system to be used as the sole basis for "
          "publication decisions. The scope document lists the twelve limitations with their effects."),
    ]


def _future_compact():
    return [
        H2("10.1 Improvements and additional features"),
        B(f"**Real data first.** Replace the synthetic corpus with PeerRead {c('peerread')} or OpenReview decisions, and judge matching against independent expert labels or historical assignments, reporting MRR@3 and P@3 for comparability.",
          "**Assessment.** Measure novelty from embedding neighbours and citation context, recognise roman-numeral headings, take titles from metadata and fit the structural weights on human ratings.",
          "**Reviewer data and matching.** Build profiles from OpenAlex or Semantic Scholar records with h-index and recency, add load-balanced global assignment, co-authorship and fuzzy conflict checks.",
          "**Robustness.** Sanitise OpenAlex queries (a question mark gives HTTP 400), show times in the user's zone and report skipped CSV rows."),
        H2("10.2 Scalability and deployment"),
        B(f"Cache profile embeddings (500 reviewers currently take about {_v()['s500']:.1f} s), run a quantised or GPU model and stream the critique, add authentication and roles, package the system in a container with a multi-user database, and run the measurements in continuous integration."),
        H2("10.3 Further research"),
        B(f"Test LLM keyword induction with a judge {c('base')}; filter and evaluate prompt injection hidden in PDFs {c('inject_aro', 'keuper')}; check the faithfulness of the critique; run a user study with editors; examine fairness effects of embedding-based ranking."),
    ]


def future_blocks():
    if F.REPORT:
        return _future_compact()
    return _future_full()


def _future_full():
    return [
        H2("10.1 Improvements to the assessment"),
        B(f"**Real decision data first.** Replace the synthetic corpus with PeerRead {c('peerread')} or decisions and reviews crawled from OpenReview, split by venue and year, and report accuracy and macro F1 against a majority baseline; this is the most important missing measurement.",
          "**Independent labels for matching.** Ask domain experts to judge the suitability of reviewers for real submissions, or reuse the historical assignments as the base paper does, and report MRR@3 and P@3 so that results become comparable.",
          "**Novelty.** Compare the paper's embedding with its retrieved neighbours and with a citation context, and replace the fixed Novelty value by a measured, caveated signal.",
          "**Better parsing.** Recognise roman-numeral and unnumbered headings, take the title from document metadata and the first page layout, and use a layout-aware parser for two-column papers.",
          "**Fitted structural weights.** Collect human ratings of structure and fit or at least sensitivity-test the 0.35, 0.25, 0.25 and 0.15 weights."),
        H2("10.2 Additional features"),
        B("**Publication-history ingestion.** Build reviewer vectors from OpenAlex or Semantic Scholar records (titles, abstracts, venues) and add h-index and recency, as the batch abstract intended.",
          "**Global assignment.** Add an optimiser with load balancing and per-paper coverage constraints on top of the ranking, with bidding as an optional signal.",
          "**Stronger conflict handling.** Co-authorship and affiliation graphs, fuzzy matching of names and institutions, and a review of flagged pairs by the editor.",
          "**Sanitised literature queries.** Strip punctuation, retry with keywords when the title fails, and cache results; this also removes the HTTP 400 seen on titles with a question mark.",
          "**Zone-aware times and stricter validation.** Show times in the user's zone, reject files from which almost no text can be read, and report CSV rows that were skipped."),
        H2("10.3 Scalability and deployment"),
        B(f"**Embedding cache.** Store profile embeddings and refresh them when a profile changes; ranking 500 reviewers currently takes about {_v()['s500']:.1f} s because every profile is re-embedded on each request.",
          "**Faster local model.** Run a quantised model or use a GPU, stream the tokens to the interface and let the user see the deterministic result while the critique is still being written.",
          "**Authentication and roles.** Accounts for editors and administrators, restricted origins, audit of who exported what, before any use beyond one machine.",
          "**Packaging.** A container for the whole application including the web interface, a database such as PostgreSQL for several users and a job queue for long analyses.",
          "**Continuous evaluation.** Run the measurement scripts, the seven tests and the smoke test in a CI pipeline."),
        H2("10.4 Further research"),
        B(f"Study whether LLM keyword induction with a judge, as in the base paper {c('base')}, improves the keyword and method terms of this system, and measure its cost.",
          f"Add a filter and an evaluation for prompt injection hidden in PDFs {c('inject_aro', 'keuper')}, and measure how far the critique can be steered.",
          "Check the faithfulness of the language-model critique against the paper text and measure how often it states things the paper does not contain.",
          "Run a user study with editors and reviewers to measure time saved, trust in the explanations and the effect of the disclaimers.",
          "Investigate fairness and diversity effects of embedding-based ranking, such as reviewers from small institutions or new fields being ranked lower."),
    ]


def chapter9_blocks():
    return [H1("CHAPTER 9: CONCLUSION")] + conclusion_blocks()


def chapter10_blocks():
    return [H1("CHAPTER 10: FUTURE SCOPE")] + future_blocks()
