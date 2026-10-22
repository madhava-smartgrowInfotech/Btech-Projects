"""Chapter 6: Methodology and Software Implementation. methodology_blocks() feeds document 9, application_blocks() feeds document 12."""

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R

TBF = "[to be filled]"


def c(*keys):
    return "[" + ", ".join(str(R[k]) for k in keys) + "]"


def lat(*keys, fmt="{:.0f}", default=TBF):
    cur = F.LATENCY
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    try:
        return fmt.format(cur)
    except (ValueError, TypeError):
        return default


def methodology_blocks():
    D = F.DM
    S = F.SHIPPED
    g = F.GEN
    cc = D["class_counts"]
    b = []
    b += [H2("6.1 Overall methodology"),
          P("PeerScope follows a hybrid method: deterministic text processing, one trained statistical classifier, a local language model used only to draft review text, and an embedding-based "
            "matching stage whose score can be audited term by term. The method has two outputs for every uploaded paper: a *preliminary assessment* (structural signals, a historical decision signal, a "
            "reviewer-style critique and related literature) and a *ranked list of reviewers* with the arithmetic behind every rank. The design follows the principle of auditable matching "
            f"stated in the base paper {c('base')}, but the project's scope is broader (it adds the assessment of the paper) and its scale is much smaller (Chapter 8 states the differences). The steps are:"),
          N("**Upload and validate** a PDF (extension, content type, size at most 20 MB, `%PDF` header).",
            "**Extract** page text with PyMuPDF, normalise whitespace, guess the title, detect up to nine sections and parse the reference list.",
            "**Derive features**: frequency keywords, method terms from a 21-term lexicon, topic hints from an 18-term list, and four structural signals combined into one structural score.",
            "**Classify** the opening text with the trained TF-IDF + logistic-regression model to give a historical decision signal (accept / borderline / reject) with class probabilities.",
            "**Review**: always produce the deterministic rule-based review; when the local Qwen2.5 model loads, add a three-step analyse, critique and synthesise pass; otherwise say plainly that it is unavailable.",
            "**Ground** the paper in literature by querying OpenAlex with the title and ranking the six returned works by embedding similarity.",
            "**Match** the paper profile against every reviewer profile: embedding cosine, keyword overlap, method and topic overlap, availability and a conflict penalty, combined with fixed, documented weights.",
            "**Store and export** the result in SQLite and offer it as JSON or as a PDF report."),
          FIG(F.diag("12_pdf_extraction_flow.png"), "Text extraction, section detection and structural scoring of an uploaded paper.", 5.4),
          P("Two further procedures sit outside the request path. The *training pipeline* builds the decision model once from a labelled CSV file and writes the model, the vectoriser and a metrics file; the "
            "*evaluation scripts* in this project (`scripts/measure_metrics.py`, `scripts/measure_latency.py`) re-evaluate the shipped model, run baselines and five further splits, and score the reviewer matcher "
            "on a probe set. Their output is the single source for every number in this report.")]

    b += [H2("6.2 Datasets"),
          H3("6.2.1 Decision-model data: a synthetic corpus"),
          P("The project looked for a public corpus of papers with reviewer decisions. The preparation script (`scripts/prepare_dataset.py`) probes one PeerRead-style file on a public repository "
            f"{c('peerread')} with a six-second timeout and, because no usable data came back, falls back to a generated corpus. The shipped model is therefore trained on **{D['rows']:,} synthetic rows**; "
            "`models/metrics.json` records `dataset_source: synthetic-fallback` and the web application shows a visible warning beside every metric. This is the most important limitation of the "
            "decision model and the rest of this section explains exactly what the data can and cannot show."),
          P("Each row is made by a seeded random generator (seed 42). One of six topics is drawn (vision, language, learning, systems, security, data), each with seven topic words, and a latent "
            "*quality* value q is drawn uniformly from 0 to 1. If q is above 0.52 the paper is given three of seven *strength phrases* (for example \"strong baselines\", \"comprehensive ablations\"); otherwise it is given three of seven "
            "*weakness phrases* (for example \"missing baselines\", \"unsupported claims\"). The label is **accept** when q > 0.72, **reject** when q < 0.30 and **borderline** otherwise, which includes "
            "both the upper-middle strength papers (0.52 < q <= 0.72) and the lower-middle weakness papers (0.30 <= q <= 0.52). A title and a short template paragraph containing the phrases and topic words form the text. "
            f"The resulting class counts are accept {cc['accept']}, borderline {cc['borderline']} and reject {cc['reject']}."),
          FIG(F.fig("f06_dataset_structure.png"), "Class counts of the synthetic corpus and how the label relates to the text signal that the classifier can see.", 5.6),
          P(f"The right-hand panel shows why the data are limited. Of the {g['strong_phrase_papers']['n']} papers that contain strength phrases, {g['strong_phrase_papers']['label_counts'].get('accept', 0)} are labelled accept and "
            f"{g['strong_phrase_papers']['label_counts'].get('borderline', 0)} borderline; of the {g['weak_phrase_papers']['n']} papers with weakness phrases, {g['weak_phrase_papers']['label_counts'].get('reject', 0)} are "
            f"reject and {g['weak_phrase_papers']['label_counts'].get('borderline', 0)} borderline. The borderline class is generated from *both* phrase groups, so the text alone cannot separate it from accept or reject. "
            f"A rule that reads the phrases and always answers accept or reject reaches only {F.pct(g['phrase_rule_accuracy_all_rows'])} accuracy on the whole corpus, and no text classifier can do better than about "
            f"{F.pct(g['best_possible_accuracy_from_phrases'])}. Accuracy near 0.55 is therefore what the data allow, not a sign of a weak method; equally, it says nothing about real peer-review decisions."),
          P(f"The corpus is split 80/20 with a stratified split and seed 42 into **{D['train']:,} training and {D['test']:,} test rows**."),
          H3("6.2.2 Reviewer data"),
          P(f"The reviewer directory is seeded at first start with **{F.REVIEWER_POOL} clearly labelled demo profiles** (Reviewer Alpha to Reviewer Zeta; Epsilon is inactive). Each profile has a display name, affiliation, "
            "free-text expertise description, comma-separated research topics, methods and keywords, publication titles, a current and a maximum review load, an active flag and comma-separated conflict terms. "
            "The areas are computer vision, language processing, applied machine learning and reproducibility, network security, medical informatics and robotics. The directory can be extended by form or by CSV import. "
            "No real person's publication history is stored, and no h-index is computed; the project abstract mentions publication history, and the closest implemented element is the `publication_titles` text field."),
          H3("6.2.3 Probe set for the matching evaluation"),
          P("To measure the matcher without real submissions the team wrote **40 short abstracts** (`scripts/eval_data.py`): six for each of the six reviewer areas and four deliberately cross-area papers for which two "
            "reviewers are acceptable. The abstracts avoid copying the reviewers' keyword lists. A second list of **15 conflict cases** adds one sentence to a paper that links it to a reviewer by a conflict term (6), an "
            "affiliation string (4), the reviewer's full name (2), a reworded affiliation (2) or a first name alone (1). The labels are the team's own judgement. They are not independent expert judgements, "
            "so the matching results in Chapter 8 are optimistic and are a check of the mechanism, not a validation on real submissions."),
          H3("6.2.4 Real documents used for observation"),
          P(f"Four real PDFs were run through the extraction, feature and decision stages to observe behaviour on genuine papers: the generated demo paper (3 pages) and three research PDFs kept with the batch "
            f"({F.REAL[1]['pages']}, {F.REAL[2]['pages']} and {F.REAL[3]['pages']} pages). They are not labelled and therefore support no accuracy claim.")]

    b += [H2("6.3 Extraction and preprocessing"),
          P("All extraction is local and deterministic (`app/services/pdf_extract.py`). The steps, in order:"),
          TAB("Extraction steps and the reason for each", ["Step", "Operation", "Reason"],
              [["1. Page text", "`page.get_text('text')` for every page with PyMuPDF; text of each page is kept with its page number", "Local, fast and layout-preserving; page numbers let the review point to evidence"],
               ["2. Normalise", "Collapse tabs and spaces, drop repeated blank lines, keep paragraph breaks", "Makes sentence and section statistics stable"],
               ["3. Title", "First line among the first 25 that is 12-220 characters and does not end with a full stop", "Cheap heuristic; fails on papers whose first lines are identifiers (observed on the IEEE base paper)"],
               ["4. Sections", "Lines shorter than 81 characters matched against regular expressions for nine sections (summary, introduction, related work, methodology, experiments, results, discussion, conclusion, references); the text up to the next heading is the section body", "Gives per-section word counts for the structural signals; fragile for roman-numeral headings"],
               ["5. References", "Text after a line `References` (or `Bibliography`) split at `[n]` or `n.` markers; fall back to bracketed lines", "Reference count and density feed the evidence signal"],
               ["6. Summary", "Preview of the summary or introduction section, else the first paragraph longer than 120 characters (max 900 characters)", "Short text for the classifier, the matcher and the literature query"]],
              widths=[0.9, 3.0, 2.4], align=["l", "l", "l"], size=9.5),
          P("Feature extraction (`app/services/features.py`) then computes word, sentence and reference statistics; the 15 most frequent non-stop-word tokens of three or more letters as *keywords*; the method terms "
            "(from a lexicon such as neural, transformer, regression, baseline, cross-validation, Bayesian) found in the text; and topic hints (vision, language, security, graph, medical and so on). These "
            "lists are simple on purpose: they are transparent, instant and easy to audit, and their weakness (no stemming, no phrase detection) is stated in Chapter 10.")]

    b += [H2("6.4 Algorithm choice and justification"),
          TAB("Algorithms used and why they were chosen", ["Component", "Choice", "Reason", "Alternative not chosen"],
              [["Text features for the decision model", f"TF-IDF, word 1-2-grams (8,000) + character 3-5-grams (4,000) {c('tfidf', 'idf')}", "Strong, fast, interpretable baseline for short text; trains in seconds on a CPU", "Fine-tuned transformer: needs real labelled data and a GPU"],
               ["Decision classifier", f"Multinomial logistic regression, `class_weight=balanced` {c('sklearn')}", "Gives calibrated-looking class probabilities for the confidence display; convex, deterministic with a seed", "Boosted trees / neural network: no gain was possible on data with this label structure"],
               ["Expertise similarity", f"Sentence embeddings `all-MiniLM-L6-v2`, cosine {c('sbert', 'minilm')}", "Same encoder family as the base paper's bi-encoder baseline; 384 dimensions; runs on a CPU", f"SPECTER {c('specter')}: larger and not needed for the small pool; LLM keyword ensembles of the base paper: costly"],
               ["Lexical evidence", "Keyword overlap and method / topic overlap (exact and substring hits)", "Gives the human-readable *matching terms* shown beside each rank", "Embeddings alone cannot name what matched"],
               ["Availability and conflict", "Load ratio and literal-string conflict penalty inside the score", "Makes workload and conflicts visible in the same audit table", "External assignment solver: out of scope"],
               ["Review drafting", f"Qwen2.5-1.5B-Instruct (fallback 0.5B), CPU, greedy decoding {c('qwen25', 'hf_transformers')}", "Open weights, runs locally so no manuscript leaves the machine; small enough for 16 GB RAM", "Hosted LLM: would send unpublished manuscripts to a third party"],
               ["Literature context", f"OpenAlex works search {c('openalex')}", "Free, no key, open index", "Paid APIs"]],
              widths=[1.2, 1.9, 1.9, 1.3], align=["l", "l", "l", "l"], size=9),
          P("The central design choice is *separation of roles*. The trained classifier gives one weak signal; the structural signals are deterministic; the language model writes prose but never ranks "
            "reviewers or changes a score; and the matching score is arithmetic that a reader can recompute from the audit table. This separation answers the concern that dense-embedding matchers are hard "
            f"to audit {c('base')} and the evidence that LLM reviewers can be steered by hidden text in a manuscript {c('inject_aro', 'keuper')}: the model's text is displayed as an aid and never feeds a number."),
          P("Two inexpensive improvements were considered and left for future work because they need real data to justify: learning the matching weights from historical assignments (the base paper's data "
            "of this kind is not available to the project), and replacing the keyword lists with an LLM keyword ensemble."),
          H3("6.4.1 Deterministic review rules"),
          P("The review that is always produced (`review_synthesis.deterministic_review`) is a set of explicit rules over the extracted features, so that every sentence can be traced to a number. "
            "Strengths are added when a methodology section exists (with its word count), when an experiments or results section exists, when at least eight references are found and when at least five sections are recognised. "
            "Major concerns are raised when no methodology section is found or it has fewer than 120 words, when no experiments or results section is found, when fewer than five references are found and when the mean sentence "
            "length exceeds 32 words. Minor concerns cover short sections, each missing section, a title shorter than 20 characters and an opening summary shorter than 200 characters. Five generic recommendations "
            "(state the contribution early, document reproducibility details, add ablations, discuss threats to validity, proofread) are always listed. A six-axis *coverage* object (method, evidence, clarity, "
            "reproducibility, novelty, limitations) is computed from the same features for the radar chart; the novelty axis is a fixed value of 55 because novelty cannot be measured from one paper, and the accompanying "
            "text says that novelty is inconclusive and requires verification against the literature."),
          H3("6.4.2 Local language-model review"),
          P("When the language model loads, `llm_review` runs three prompts on the first 6,000 characters of the paper. The *analyse* prompt asks for the problem, contribution, approach, set-up, claims, evidence, strengths, "
            "weaknesses and missing information; the *critique* prompt asks for a critique of method clarity, evidence, completeness, reproducibility, limitations and consistency, with cautious wording such as *novelty "
            "signal* and *requires verification*; the *synthesise* prompt combines both into a structured assessment with ten headings. The system prompts forbid inventing experiments, data or citations. Generation is "
            "greedy (no sampling) with budgets of 512, 512 and 700 new tokens. If the model cannot be loaded the review carries `llm_status: unavailable` and the reason; if generation fails it carries `error`. In both cases "
            "the deterministic review is shown unchanged. The model is loaded once, on the first analysis, under a lock, with the 0.5B model as a fallback if the 1.5B model cannot be loaded."),
          H3("6.4.3 Conflict-of-interest detection"),
          P("`detect_conflict` lower-cases the first 3,000 characters of the paper text and tests three things: any comma-separated *conflict term* of the reviewer, the reviewer's full display name, and the full "
            "affiliation string (longer than four characters). A match sets the conflict flag, adds the penalty and replaces the explanation with the reason (for example *Conflict term match: ...*). The method is "
            "exact and therefore predictable, which suits an audit, but it cannot recognise a reworded affiliation, a first name alone, co-authorship or a citation relationship; these limits are measured in Chapter 8 "
            "and listed in Chapter 10."),
          H3("6.4.4 Literature grounding and embeddings"),
          P(f"The OpenAlex query uses the extracted title (or the first six keywords), asks for six works and selects identifier, title, year, authors, source and DOI. The works are re-ranked by the cosine between the query "
            f"and each title in the embedding space, with a word-overlap fallback if embeddings are unavailable. Any network error returns `literature_retrieval_status: unavailable` and an error text. Embeddings come from "
            f"`all-MiniLM-L6-v2` (inputs truncated to 2,000 characters). If it cannot be loaded, a TF-IDF vectoriser with at most 512 features and 1-2-grams is fitted on the first batch of texts it receives and then reused "
            f"unchanged; the consequence, that the vocabulary is frozen by the first request, explains the lower matching accuracy of the offline mode reported in Chapter 8 "
            f"(top-1 {F.f2(F.TFIDF['full_hybrid_shipped_weights']['top1'])} against {F.f2(F.MINILM['full_hybrid_shipped_weights']['top1'])})."),
          H3("6.4.5 Decision signal at inference time"),
          P("For an uploaded paper the classifier receives the extracted title, the paper summary and the first 4,000 characters of the full text, vectorised with the training vectorisers. The service returns the label with "
            "the highest probability, that probability as the confidence, all three probabilities and a fixed note that the signal is learned from prior review records and is not a judgement of correctness. "
            "If the artifacts are missing it returns `model_unavailable` instead of a guess.")]

    b += [H2("6.5 Mathematical formulation"),
          H3("6.5.1 Text representation and classifier"),
          P("With N training documents, a term t that occurs in df(t) of them and a raw count tf(t, d), the TF-IDF weight (scikit-learn's smoothed form) is"),
          EQ("x(t,d) = tf(t,d) × [ ln((1 + N) / (1 + df(t))) + 1 ]      (each vector then scaled to unit Euclidean length)"),
          P("The word and character vectors are concatenated into one 12,000-dimensional sparse vector x. For K = 3 classes the multinomial logistic model gives"),
          EQ("P(y = k | x) = exp(wₖ·x + bₖ) / Σⱼ exp(wⱼ·x + bⱼ)"),
          P("and is fitted by minimising the class-weighted regularised log-loss"),
          EQ("L(W, b) = − Σᵢ ωᵧᵢ · ln P(yᵢ | xᵢ) + (1 / 2C) · ‖W‖²,      ωₖ = n / (K · nₖ),  C = 1"),
          P("where nₖ is the number of training documents in class k; the weights ωₖ increase the influence of rarer classes. The reported **confidence** of a prediction is the largest class probability. "
            "Macro precision, recall and F1 average the per-class values with equal weight; the multi-class ROC-AUC is the one-versus-rest average."),
          H3("6.5.2 Reviewer matching"),
          P("For a paper profile p and a reviewer profile r (text, keyword set, method set), the expertise similarity is the clipped cosine of their embeddings u and v:"),
          EQ("sim(p, r) = max(0, u·v / (‖u‖ ‖v‖))"),
          P("Keyword and method overlaps compare two term sets A and B by the number h of hits, where a hit is an exact match or a term contained in a term of the other set:"),
          EQ("overlap(A, B) = min(1, 1.1 · h / max(|A|, |B|))      (0 if either set is empty)"),
          P("Availability falls linearly with the reviewer's current load, and the conflict flag c is 1 when a conflict term, the reviewer's full name or the affiliation string occurs in the first 3,000 characters of the paper text:"),
          EQ("avail(r) = clip(1 − load(r) / max_load(r), 0, 1)"),
          P("The final match score, reported from 0 to 100, is the audited weighted sum (weights from `app/config.py`, adjustable by environment variables):"),
          EQ("score(p, r) = 100 · clip( 0.55·sim + 0.20·kw + 0.15·method + 0.10·avail − 0.60·c , 0, 1 )"),
          P("The labels Strong, Good, Possible and Weak correspond to scores of at least 65, 45, 25 and below 25. A conflict therefore subtracts 60 points, which in practice drives the reviewer to the bottom of the list "
            "while the breakdown still shows the other components."),
          FIG(F.fig("f12_score_breakdown.png"), "Weighted contribution of each component to the match score of the five best reviewers for the demo paper.", 5.2),
          H3("6.5.3 Structural score"),
          P("Four signals in the range 0 to 100 are derived from the extracted document. With S the number of detected sections out of nine, R the number of references, G the page count, "
            "w̄ the mean sentence length in words and q the share of detected sections shorter than 40 words:"),
          EQ("structure = 100·S/9;    evidence = min(100, 22·R/G + 10·[experiments or results present])"),
          EQ("method clarity = 100 if the methodology section has ≥ 120 words, 70 if it exists, 45 if method terms occur, else 25"),
          EQ("presentation = 100 if 12 ≤ w̄ ≤ 26 and q < 40 %, 75 if 8 ≤ w̄ ≤ 32, else 50"),
          EQ("structural score = 0.35·structure + 0.25·evidence + 0.25·method clarity + 0.15·presentation"),
          P("The weights and thresholds are design decisions chosen so that a complete, referenced paper scores high; they were not fitted to human judgements and the score is presented as one input among several. "
            "The overall wording (*Strong*, *Moderate*, *Early-stage*) uses cut-offs of 75 and 55.")]

    b += [H2("6.6 Model training and configuration"),
          P("`scripts/train_model.py` reads the CSV, joins title and text, encodes the labels alphabetically (accept, borderline, reject), splits 80/20 with a stratified split and seed 42, fits the two TF-IDF vectorisers on the "
            "training part only, fits the classifier and writes `models/decision_model.joblib`, `models/tfidf_vectorizer.joblib` and `models/metrics.json`."),
          TAB("Training configuration", ["Item", "Value"],
              [["Rows / train / test", f"{D['rows']:,} / {D['train']:,} / {D['test']:,}"],
               ["Split", "80/20, stratified by label, `random_state` 42"],
               ["Word TF-IDF", "1-2-grams, 8,000 features, English stop words removed, lower-cased"],
               ["Character TF-IDF", "`char_wb` 3-5-grams, 4,000 features"],
               ["Classifier", "`LogisticRegression(max_iter=1000, class_weight='balanced', C=1.0, random_state=42)`"],
               ["Inference text", "Title + summary + first 4,000 characters of the paper"],
               ["Training time", "Seconds on the CPU (measured step: all of `decision_model` evaluation, five re-fits and baselines took under 10 s)"],
               ["Software", f"Python {F.ENV['python']}, scikit-learn {F.ENV['packages']['scikit-learn']}, NumPy {F.ENV['packages']['numpy']}, pandas {F.ENV['packages']['pandas']}"],
               ["Hardware", f"{F.ENV['cpu']}, {F.ENV['ram_gb']} GB RAM, {F.ENV['gpu']}"]],
              widths=[1.6, 4.7], align=["l", "l"], size=10),
          P(f"Re-loading the saved artifacts and scoring the same split reproduces the saved `metrics.json` exactly (accuracy {F.f3(S['accuracy'])}, macro F1 {F.f3(S['f1_macro'])}, ROC-AUC {F.f3(S['roc_auc'])}). "
            f"The artifacts were written by scikit-learn 1.9.0 and loaded under {F.ENV['packages']['scikit-learn']}; scikit-learn warns about the version difference, and a model pickled by an older release does not load "
            "reliably, which is why the model is retrained by `run.bat` on a new machine."),
          FIG(F.diag("11_ml_training_pipeline.png"), "Training pipeline of the decision model.", 5.6),
          P("Beyond the single run, the evaluation scripts re-fit the same configuration on five further stratified splits (seeds 0 to 4) and on three simpler baselines so that the accuracy can be put in context. "
            "Chapter 8 reports those results. No hyper-parameter search was run: on data whose labels are partly random by construction, tuning would only fit noise, and the unweighted and word-only variants "
            "tried as baselines performed within the spread of the seeds."),
          H3("6.6.1 Evaluation protocol"),
          P("The decision model is evaluated on the held-out 20 % only, once, with accuracy, macro precision, macro recall, macro F1, one-versus-rest ROC-AUC, the confusion matrix and per-class scores. Because the classifier "
            "outputs probabilities, a confidence-threshold analysis reports the share of papers kept and the accuracy on the kept papers for thresholds from 0.4 to 0.9. Three baselines on the same split put the result in context: "
            "the majority class, multinomial Naive Bayes on word TF-IDF, and the same logistic regression without class weights or without character features. A last check re-fits the shipped configuration on five different "
            "splits to show how much the numbers depend on the split."),
          P("The matcher is evaluated on the 40 probe papers against all six reviewers (inactive ones included, because the question is similarity, not eligibility). For each paper the rank of the best acceptable reviewer is "
            "found and three scores are reported: **top-1** (the best acceptable reviewer is ranked first), **top-3** (within the first three) and the **mean reciprocal rank** (the average of 1/rank). The same probe set is "
            "scored under four weight settings (shipped hybrid, semantic similarity only, lexical overlap only, hybrid without availability) and two embedding back-ends (MiniLM and the offline TF-IDF fallback), and a "
            "random ranking gives the reference level. Conflict handling is scored as the share of injected links that set the flag, with the number of false flags over all 240 clean paper-reviewer pairs as the "
            "complementary figure. Finally the ranking time is measured for pools of 6, 50, 200 and 500 reviewers.")]
    return b


def application_blocks():
    L = F.LOC
    b = []
    b += [H2("6.7 Application architecture and implementation"),
          P(f"PeerScope is a three-tier local application of about {L['backend_app']:,} lines of Python (`app/`), {L['frontend_src']:,} lines of React code and styles (`frontend/src/`) and {L['scripts_core']:,} lines of supporting scripts, "
            f"with {L['tests']} lines of tests. The architecture is shown in Chapter 5; the points below describe how it is realised."),
          P("**API tier.** `app/main.py` creates one FastAPI application, initialises the SQLite schema through SQLAlchemy, seeds the six demo reviewers if the table is empty (a seeding failure is logged and never stops "
            "start-up) and declares all routes. The routes are thin: file validation and persistence are in `main.py`, everything else is delegated to service modules in `app/services/` "
            "(`pdf_extract`, `features`, `ml_predict`, `review_synthesis`, `llm_service`, `literature`, `embeddings`, `matching`, `pipeline`, `export_service`, `seed`). The services are plain function modules without hidden "
            "state, except three lazily created singletons: the classifier and vectoriser (loaded on first use), the sentence-embedding model and the language model. Each loader catches its own exceptions "
            "and records the error, so a missing package or an offline machine degrades one feature instead of the whole request."),
          P("**Pipeline module.** `pipeline.run_analysis` is the only place where the stages are composed. It runs them in a fixed order, applies the user's filters to the ranked reviewers "
            "(active only, minimum score, topic text, method text), keeps the five best and assembles the result dictionary that is returned to the browser and stored as JSON."),
          P("**Web tier.** The React application (Vite, port 5408) calls the API through a small client (`lib/api.js`) whose errors carry a message that is safe to show. It has eight views: landing page, dashboard, "
            "analysis form and result, reviewer directory, model performance, history, saved analysis and an about page that states responsible use. A result is shown in five tabs (Overview, Review, Literature, Reviewers, "
            "Audit and export), and each reviewer card opens a table with the five score components, their values and weights. The original vanilla-JavaScript interface remains in `static/` and is served by the API at `/` "
            "as a fallback."),
          P("The interface is built from a small component set (layout, navigation, form controls, feedback and display components) with design tokens for dark and light themes, Recharts for the metric and class "
            "charts, motion libraries for entrance animation and a three.js scene on the landing page with a static fallback image. Data loading uses a small `useAsync` hook; the analysis request can be aborted by the "
            "user (an `AbortController` signal is passed to `fetch`), and when the backend cannot be reached the client throws an error that tells the user to start it with `run.bat`. The model-performance page reads "
            "`/api/model/metrics` and shows the synthetic-data warning whenever `synthetic_fallback` is true, so the figures cannot be mistaken for a benchmark."),
          P("**Storage.** Two SQLite tables: `reviewers` and `analyses`. The second keeps a summary (file name, time, overall assessment, concern and recommendation counts, top reviewer name) and the complete "
            "result as a JSON text column, so a saved analysis can be re-opened and exported without recomputation. There is deliberately no foreign key between them; the ranked reviewers are a snapshot inside the JSON."),
          H3("6.7.1 Key code: the match score"),
          CODE("""    for r, sim in zip(reviewers, sims):
        rp = reviewer_profile(r)
        kw_s, kw_hits = _overlap(paper["keywords"], rp["keywords"])
        m_s, m_hits = _overlap(paper["methods"] + paper["topics"], rp["methods"] + rp["topics"])
        maxload = max(int(r.maximum_load or 5), 1)
        avail = max(0.0, min(1.0, 1.0 - (int(r.current_load or 0) / maxload)))
        conf = detect_conflict(paper_text_extra, "", r)
        penalty = float(w["conflict_penalty"]) if conf["conflicted"] else 0.0
        raw = (w["expertise_similarity"] * sim + w["keyword_score"] * kw_s
               + w["method_score"] * m_s + w["availability_score"] * avail - penalty)
        score100 = round(max(0.0, min(100.0, raw * 100)), 1)
        strength = "Strong" if score100 >= 65 else ("Good" if score100 >= 45 else ("Possible" if score100 >= 25 else "Weak"))""", 8.5),
          P("The function is a direct transcription of the formula in Section 6.5.2. Every intermediate value is returned in a `breakdown` dictionary together with the weights, and an explanation sentence is generated "
            "from the same values, so what the interface shows is exactly what was computed."),
          H3("6.7.2 Key code: the analysis pipeline"),
          CODE("""    doc = pdf_svc.extract_pdf(pdf_path)
    feats = feat_svc.extract_features(doc)
    ml = ml_svc.predict_decision(doc.get("title", ""), doc.get("paper_summary", ""), doc.get("full_text", ""))
    review = rev_svc.llm_review(doc, feats)           # deterministic review + optional 3-step local LLM
    lit = lit_svc.retrieve_literature(doc.get("title", ""), feats["keywords"], feats["research_topics"])
    paper_prof = match_svc.paper_profile(doc["title"], doc["paper_summary"], feats["keywords"],
                                         feats["methodology_terms"], feats["research_topics"])
    ranked = match_svc.match_reviewers(paper_prof, reviewers, doc["full_text"][:4000])""", 8.5),
          P("Each stage returns plain dictionaries with an explicit status field where it can fail (`llm_status`, `literature_retrieval_status`, the decision model's `status`), and the front end shows those statuses "
            "instead of hiding a missing component.")]

    b += [H2("6.8 API design"),
          P(f"The API is a JSON-over-HTTP interface on port {F.API_PORT}, documented automatically at `/docs` by FastAPI. Request bodies are validated by Pydantic schemas; the reviewer schema limits "
            "name length (1-200), text fields (2,000-4,000 characters) and loads (0-100, maximum load 1-100)."),
          TAB("Endpoints", ["Method and path", "Request", "Success response", "Error responses"],
              [["GET `/api/health`", "-", "Status, product, LLM state (`loaded` or `lazy-not-loaded`), embedding backend, model-loaded flag, reviewer count", "-"],
               ["GET `/api/model/metrics`", "-", "Contents of `models/metrics.json`, or `status: missing`", "-"],
               ["GET `/api/reviewers`", "-", "List of reviewers (12 fields)", "-"],
               ["POST `/api/reviewers`", "JSON reviewer; `display_name` required", "201 and the stored reviewer", "422 invalid field; 400 save failure"],
               ["PUT `/api/reviewers/{id}`", "JSON reviewer", "200 and the updated reviewer", "404 unknown id; 422; 400"],
               ["DELETE `/api/reviewers/{id}`", "-", "`{\"deleted\": id}`", "404 unknown id"],
               ["GET `/api/reviewers/export/csv`", "-", "CSV attachment `peerscope_reviewers.csv`", "-"],
               ["POST `/api/reviewers/import`", "Multipart CSV file", "`{\"imported\": n}`", "400 unreadable or malformed CSV"],
               ["POST `/api/analyze`", "Multipart: `file` (PDF), `active_only`, `min_score`, `topic`, `method`", "Full analysis result and `analysis_id`; a `warning` if fewer than 50 words were extracted", "400 not a PDF, empty, bad header or no reviewers; 413 over 20 MB; 500 analysis failure"],
               ["GET `/api/analyses`", "-", "Stored analyses, newest first", "-"],
               ["GET `/api/analyses/{id}`", "-", "Stored result JSON", "404 unknown id; 500 corrupted record"],
               ["GET `/api/analyses/{id}/export`", "`format=json` or `pdf`", "Attachment: JSON file or a PDF report built with ReportLab", "404 unknown id"]],
              widths=[1.7, 1.5, 1.9, 1.2], align=["l", "l", "l", "l"], size=9),
          P("The analysis result contains these top-level fields: `paper` (title, summary, pages, words, references, detected sections, preview of the first four pages), `features`, `ml_decision_signal` "
            "(label, confidence, probabilities, note), `structural_assessment`, `review` (strengths, major and minor concerns, method, evidence, clarity and reproducibility comments, novelty considerations, "
            "recommendations, a six-axis coverage object, evidence references, `llm_status` and, when available, the AI synthesis), `review_quality`, `literature` (status and works), `reviewers` (the five best, each with "
            "score, strength, matching terms, availability, conflict result, breakdown and explanation), the pool size, the disclaimer and the responsible-use statement."),
          P("A global exception handler turns any unexpected error into `500 Internal server error` without a stack trace, and `HTTPException` responses keep their detail message, which the web client shows to the user.")]

    b += [H2("6.9 Security and error handling"),
          B("**Upload validation.** The extension must be `.pdf`; a declared content type must mention `pdf` or `octet`; the body must be non-empty, at most 20 MB (configurable) and start with `%PDF`. The bytes are written "
            "to a temporary file that is deleted in a `finally` block whatever the outcome, and no uploaded paper is kept on disk or sent to a paid service.",
            "**Input limits.** Reviewer fields have maximum lengths and numeric ranges (Pydantic); CSV import truncates long names and affiliations, tolerates missing columns and turns any parsing error into a 400 after rolling back the transaction.",
            "**Injection.** All database access goes through the SQLAlchemy ORM with bound parameters; the React interface escapes text; the PDF export escapes `&`, `<` and `>` before ReportLab renders it.",
            "**Degrade, do not fail.** A missing classifier, embedding model, language model or network connection sets a status field and the interface says so; the pipeline continues with the deterministic parts.",
            "**Privacy.** Text extraction, classification, embeddings and the language model run on the local machine. Only the paper's title (or its keywords) is sent to OpenAlex, with an 8-second timeout.",
            f"**What is not protected.** The API has no authentication and allows every origin because it is meant for one user on one machine; it must not be exposed to a network as it stands. PyMuPDF parses untrusted PDFs in the server process. "
            f"Text hidden in a PDF could steer the local language model {c('inject_aro')}; the mitigation is architectural (the model's text never changes a score and is labelled as AI output) rather than a filter."),
          P("The functional and security tests of Chapter 7 exercise these checks.")]

    b += [H2("6.10 Installation and execution"),
          P(f"**Quick start (Windows).** Install Python 3.11 or 3.12 and Node.js 18 or newer and double-click `run.bat`. The script checks both tools, creates or repairs the virtual environment, installs `requirements.txt`, "
            f"prepares the dataset and trains the decision model if the artifacts are missing, creates the demo PDF, installs the frontend packages, and starts the API on port {F.API_PORT} and the web application on port {F.WEB_PORT} in two windows. "
            "The first analysis downloads the sentence-embedding model and the Qwen language model (about 3 GB in `models/hf_cache`) from Hugging Face; if that fails the application keeps working with the "
            "deterministic analysis and a TF-IDF fallback embedder."),
          CODE("""python -m venv .venv && .venv\\Scripts\\activate
python -m pip install -r requirements.txt
python scripts/prepare_dataset.py            # synthetic corpus (unless a public file is reachable)
python scripts/train_model.py                # writes models/decision_model.joblib, tfidf_vectorizer.joblib, metrics.json
python scripts/make_demo_pdf.py              # demo paper fixture
python -m uvicorn app.main:app --host 127.0.0.1 --port 8408         # terminal 1
cd frontend && npm install && npm run dev                           # terminal 2 (http://localhost:5408)
python -m pytest tests                                              # 7 automated tests
python scripts/smoke_test.py                                        # live API checks against the running server
python scripts/capture_screens.py                                   # real screenshots with Playwright""", 9),
          TAB("Configuration variables (`.env`, `app/config.py`)", ["Variable", "Default", "Meaning"],
              [["`PEERSCOPE_PORT` / `FRONTEND_PORT`", "8408 / 5408", "API and web ports"],
               ["`PEERSCOPE_MAX_UPLOAD_MB`", "20", "Largest accepted PDF"],
               ["`PEERSCOPE_LLM_MODEL` / `PEERSCOPE_LLM_FALLBACK`", "Qwen2.5-1.5B-Instruct / 0.5B-Instruct", "Local review models (set to an unknown name to switch the AI review off)"],
               ["`PEERSCOPE_EMBED_MODEL`", "sentence-transformers/all-MiniLM-L6-v2", "Embedding model"],
               ["`PEERSCOPE_LITERATURE_COUNT` / `_TIMEOUT`", "6 / 8 s", "OpenAlex results and timeout"],
               ["`PEERSCOPE_W_EXPERTISE`, `_KEYWORD`, `_METHOD`, `_AVAIL`, `_CONFLICT`", "0.55, 0.20, 0.15, 0.10, 0.60", "Matching weights (positive weights sum to 1)"],
               ["`PEERSCOPE_DB`", "`sqlite:///data/peerscope.db`", "Database URL"],
               ["`VITE_API_URL`", "`http://127.0.0.1:8408`", "API address used by the web application"]],
              widths=[2.4, 1.9, 2.0], align=["l", "l", "l"], size=9.5),
          P("A `Dockerfile` builds the API image (Python 3.12) and trains the model at build time; the web application is started separately. Configuration is read from `.env` (host, ports, upload limit, model "
            "names, number of literature results, timeout and the five matching weights), and real environment variables take precedence. Appendix B gives the step-by-step user guide.")]
    return b



# ---------------------------------------------------------------- compact variant for the full report (F.REPORT True)
_KEEP_FIGS = ("12_pdf_extraction_flow.png", "f06_dataset_structure.png", "f12_score_breakdown.png", "11_ml_training_pipeline.png")

_DROP_P = ("Two further procedures", "Feature extraction (", "Two inexpensive", "The interface is built from", "Re-loading the saved", "Beyond the single run",
           "The matcher is evaluated", "A `Dockerfile`", "The functional and security tests",
           "The labels Strong, Good", "These probes", "A global exception handler")

_SHORT_P = {
    "The review that is always produced": (
        "The always-produced review (`deterministic_review`) is a set of explicit rules over the extracted features, so every sentence traces to a number: strengths when a methodology section, "
        "an experiments or results section, at least eight references or at least five sections are found; major concerns when the methodology is missing or under 120 words, no evaluation section is found, "
        "fewer than five references are found or the mean sentence exceeds 32 words; minor concerns for short or missing sections, a short title or summary; and five generic recommendations. A six-axis "
        "coverage object feeds the radar chart; its novelty axis is a fixed 55 because novelty cannot be measured from one paper, and the text says novelty is inconclusive."),
    "When the language model loads": (
        "When the language model loads, three prompts run on the first 6,000 characters of the paper: *analyse* (problem, contribution, approach, claims, evidence, weaknesses), *critique* (method clarity, evidence, "
        "reproducibility, limitations, in cautious wording) and *synthesise* (a structured assessment with ten headings). System prompts forbid invented experiments, data or citations; decoding is greedy with "
        "budgets of 512, 512 and 700 tokens. If the model cannot be loaded or generation fails, `llm_status` records `unavailable` or `error` and the deterministic review is shown unchanged; the 0.5B model is a fallback."),
    "`detect_conflict` lower-cases": (
        "`detect_conflict` tests the first 3,000 characters of the paper for any conflict term of the reviewer, the reviewer's full name and the full affiliation string; a match sets the flag, adds the penalty "
        "and replaces the explanation with the reason. The test is exact and therefore auditable, but it cannot see a reworded affiliation, a first name alone, co-authorship or citation links (Chapters 8 and 10)."),
    "The OpenAlex query uses": (
        "The OpenAlex query uses the title (or the first six keywords), asks for six works and re-ranks them by embedding cosine, with a word-overlap fallback; any network error gives `unavailable`. Embeddings come from "
        "`all-MiniLM-L6-v2`; if it cannot be loaded, a TF-IDF vectoriser (512 features) is fitted on the first batch of texts and reused unchanged, so the vocabulary is frozen by the first request, which explains the lower "
        f"offline accuracy (top-1 {F.f2(F.TFIDF['full_hybrid_shipped_weights']['top1'])} against {F.f2(F.MINILM['full_hybrid_shipped_weights']['top1'])})."),
    "For an uploaded paper the classifier": (
        "At inference the classifier receives the title, summary and first 4,000 characters of the paper and returns the most probable label, its probability as the confidence, all three probabilities and a fixed note "
        "that the signal is not a judgement of correctness; if the artifacts are missing it returns `model_unavailable`."),
    "The function is a direct transcription": (
        "The function transcribes the formula of Section 6.5.2; every intermediate value is returned in a `breakdown` dictionary with the weights, and the explanation sentence is generated from the same values "
        "(listing in Appendix A)."),
    "Each stage returns plain dictionaries": (
        "`pipeline.run_analysis` composes the stages in a fixed order; each stage that can fail returns an explicit status field (`llm_status`, `literature_retrieval_status`, the classifier's `status`) that the "
        "interface shows instead of hiding a missing component."),
    "The model-performance page": None,
}


def _report_blocks():
    out = []
    for blk in methodology_blocks() + application_blocks():
        k = blk[0]
        if k == "fig":
            if blk[1].endswith(_KEEP_FIGS):
                out.append(("fig", blk[1], blk[2], min(blk[3], 4.8)))
            continue
        if k == "code":
            continue
        if k == "tab" and blk[1].startswith("Configuration variables"):
            continue
        if k == "p":
            t = blk[1]
            if t.startswith(_DROP_P):
                continue
            repl = next((v for key, v in _SHORT_P.items() if t.startswith(key)), "no")
            if repl != "no":
                if repl:
                    out.append(("p", repl))
                continue
        out.append(blk)
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + out


def blocks():
    if F.REPORT:
        return _report_blocks()
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
