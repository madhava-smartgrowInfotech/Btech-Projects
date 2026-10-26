"""Chapter 6 content: methodology and software implementation (ClauseGuard). All numbers come from docs/REPORT_FACTS.md and experiments/*/metrics.json."""
from __future__ import annotations

from doc_common import CHARTS, DIAG, ROOT, metrics

CL = metrics("classification")
RU = metrics("rules")
CO = metrics("corpus")
PA = metrics("parity")
AP = metrics("api")


def src(path: str, start: int, end: int) -> str:
    """Real source lines (1-based, inclusive) from the project, so listings never drift from the code."""
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[start - 1:end])


def grab(path: str, marker: str, n: int, back: int = 0) -> str:
    """`n` real source lines starting `back` lines before the first line that contains `marker`."""
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    i = next(k for k, line in enumerate(lines) if marker in line)
    return "\n".join(lines[max(0, i - back):i - back + n])


def pct(x, nd=1):
    return f"{x * 100:.{nd}f} %"


def _rep(d):
    return bool(getattr(d, "report", False))


# ---------------------------------------------------------------------------------------------------------------- 6.1
def sec_method_overview(d):
    d.h2("Overall Methodology")
    d.paras(
        "ClauseGuard follows a review chain that a careful reader would follow by hand, and automates each link: the contract is read, split into clauses, "
        "each clause is given a type, each clause is tested against a short list of terms that Indian contract law treats as suspect, the clauses that "
        "are dangerous only in combination are found, the wording is scored for difficulty, and the findings are written back in plain language with a "
        "fairer alternative. The base paper [1] builds a retrieval-augmented consultation system and a contract-analysis module on Gemini 1.5 Flash for Saudi "
        "law, and checks contracts against a checklist of essential clauses with an LLM-assisted semantic test. ClauseGuard keeps the idea of a "
        "jurisdiction-aware, Gemini-based analysis, but changes the division of labour: the decision that a clause is predatory is taken by deterministic "
        "rules, and the language model is used for embeddings and for wording.",
        "Three differences from the project abstract and from the base paper must be stated at the outset. First, the build uses **Gemini** for embeddings "
        "and text; the abstract names the Claude API. Second, vectors are stored as blobs in **SQLite** and compared with NumPy, and the clause graph "
        "is a **NetworkX** graph rebuilt for every request; the abstract names pgvector and Neo4j. Third, there is **no retrieval over a legal corpus**: the "
        "only retrieval step is the nearest-centroid match of a clause against 20 CUAD category centroids, and Gemini is given the rule's legal basis in the "
        "prompt rather than retrieved passages. The method is therefore a rule-and-embedding pipeline with an LLM writing layer, and it should be judged as that.")
    if not _rep(d):
        d.figure(DIAG / "02_high_level_workflow.png", "High-level workflow of ClauseGuard, from upload to report", width=6.2)
    d.table([["Step", "Method", "Output"],
             ["1 Parse", "PyMuPDF for PDF (one page per page); python-docx for DOCX (whole file is page 1)", "Pages of raw text"],
             ["2 Segment", "Split each page at numbered headings (`1.`, `2.1`, `Section 3`); if a page has fewer than two headings, merge blank-line paragraphs up to about 400 characters", "Clauses with index and page number"],
             ["3 Classify", "Gemini embedding (3,072 values); cosine similarity to 20 CUAD category centroids; Gemini tie-break when two categories are close", "Clause type, confidence, method"],
             ["4 Detect", "Eight case-insensitive regular-expression rules, each tagged with severity and an Indian statute", "Flags per clause"],
             ["5 Explain", "One Gemini call per flag: reason, quoted provision, safer wording", "Plain-language flag record"],
             ["6 Combine", "Three combinations of rule ids matched anywhere in the contract; NetworkX graph", "Risky combinations and graph edges"],
             ["7 Score", "Flesch reading ease, legalese density, cross-references, sentence length; weighted 0-100 score; grade A-F", "Complexity grade and four component values"],
             ["8 Summarise", "One Gemini call over the first 40 clause excerpts and the flag list", "Plain summary and key obligations"],
             ["9 Store and show", "One SQLite transaction; report, clause and graph endpoints", "Report, clause detail, graph"]],
            "Pipeline of ClauseGuard", widths=[0.14, 0.58, 0.28], font=9.5)


# ---------------------------------------------------------------------------------------------------------------- 6.2
def sec_dataset(d):
    d.h2("Dataset")
    d.p("The project has no labelled corpus of Indian contracts, and none is publicly available in a form that could be used here. The only labelled "
        "clause data is the Contract Understanding Atticus Dataset (CUAD) [8], a corpus of United States commercial contracts filed with the Securities "
        "and Exchange Commission and annotated by lawyers with 41 clause categories. The predatory-clause rules are therefore written by hand, and the "
        "classification step is trained and tested on CUAD. The datasets used are summarised below.")
    d.table([["Dataset", "Role", "Source and licence", "Size"],
             ["CUAD v1 [8]", "Source of all classification data; corpus-scale run", "The Atticus Project, `data/cuad/CUADv1.json` (about 40 MB), CC BY 4.0", "510 contracts, 41 categories; 20 substantive categories used"],
             ["Training spans", "Build 20 category centroids", "Derived from CUAD by `scripts/build_cuad_samples.py`, seed 42", "500 spans (497 distinct texts), 25 per category"],
             ["Held-out spans", "Classification test", "Derived from CUAD, same script and seed", "240 spans, 12 per category"],
             ["Shipped rule test set", "Rule precision and recall", "Written for the project by the author of the rules", "40 labelled clauses"],
             ["Independent probe set", "Second rule test", "Written in the documentation run after the rules were final", "40 clauses: 24 predatory paraphrases, 16 benign look-alikes"],
             ["Sample contracts", "End-to-end runs and screenshots", "Two invented contracts and one real CUAD contract typeset to PDF", "3 files, 8 to 11 clauses each"]],
            "Datasets used", widths=[0.18, 0.22, 0.34, 0.26], font=9)
    d.h3("How the classification data were derived")
    d.p("The script walks every annotation of CUAD, keeps the answer spans of the 20 chosen categories (Governing Law, Termination For Convenience, "
        "Non-Compete, Exclusivity, Audit Rights, Cap On Liability, Change Of Control, Insurance, Ip Ownership Assignment, License Grant, Liquidated Damages, "
        "Minimum Commitment, No-Solicit Of Customers, No-Solicit Of Employees, Non-Disparagement, Post-Termination Services, Renewal Term, Revenue/Profit "
        "Sharing, Uncapped Liability and Warranty Duration), normalises whitespace, keeps spans of 40 to 900 characters, removes duplicates within a "
        "category, shuffles with seed 42, and takes the first 25 spans of each category for training and the next 12 for testing. The administrative "
        "categories (document name, parties, dates) are left out because they describe metadata and not clauses.")
    d.p("The split has three properties that limit what the scores mean. It is by **span text, not by contract**: 192 of the 240 held-out spans come from a contract "
        "that also supplied a training span (the contract-disjoint check in section 6.6 shows that this did not inflate the result). Four held-out texts "
        "are exact duplicates of training texts. And the items are annotation **spans**, with a mean length of about 300 characters (306 for the training spans, 290 for the held-out spans), whereas the clauses that the product "
        "segments from a contract have a median length of 1,158 characters (measured over the 510 CUAD contracts), so the classification score describes "
        "short, focused text and not whole clauses.")
    d.h3("The rule set")
    d.p("Each rule is a case-insensitive regular expression with a severity and a statement of its legal basis, which is also the text given to Gemini when it "
        "explains a hit. The legal basis is a short description written by the project, not a quotation of the statute.")
    d.table([["Rule id", "Severity", "Pattern recognises", "Legal basis stated in the code"],
             ["restraint_of_trade", "high", "non-compete wording, \"shall not engage / work / provide services\", competing business, solicitation of clients or employees", "Indian Contract Act 1872 [20], s. 27: agreements in restraint of trade are void, with narrow exceptions"],
             ["penalty_clause", "medium", "\"penalty\", \"liquidated damages\", forfeiture of the entire amount", "ICA s. 74: only a genuine pre-estimate of loss is enforceable"],
             ["unilateral_termination", "high", "termination at sole or absolute discretion; \"company may terminate ... without cause / at any time\"", "Mutuality of termination rights under Indian contract principles (no section cited)"],
             ["unlimited_liability", "high", "\"unlimited liability\", \"no limitation of liability\", \"liable for any and all losses\"", "Reasonableness of liability terms under ICA ss. 73 and 74"],
             ["one_sided_arbitration", "medium", "arbitrator \"solely appointed by\" one party; arbitration only at one party's option", "Arbitration and Conciliation Act 1996 [21]: fairness of appointment and venue"],
             ["auto_renewal", "medium", "\"automatically renew\", \"auto-renew\", \"deemed renewed\", renewal for successive terms unless notice", "Consumer Protection Act 2019 [22]: unfair contract terms for consumers"],
             ["ip_overreach", "high", "assignment of all intellectual property including prior or unrelated work; work made for hire", "Copyright Act 1957 [23] and the ICA: assignment beyond the scope of the engagement"],
             ["no_refund", "medium", "\"non-refundable\", \"no refund shall be made\", \"not entitled to any refund\"", "Consumer Protection Act 2019: blanket no-refund terms"]],
            "The eight predatory-clause rules", widths=[0.17, 0.09, 0.40, 0.34], font=8.5)
    if not _rep(d):
        d.h3("Sample contracts")
        d.p("Three contracts were used for the end-to-end runs and the screenshots. `freelance_services_agreement` (DOCX and PDF with identical text) is an "
            "invented one-sided contract with eleven numbered clauses that contains all eight patterns; `balanced_consulting_agreement.docx` is an invented fair "
            "agreement with eight clauses; `supply_agreement_cuad.pdf` is a real CUAD contract (a supply agreement filed as an SEC exhibit) typeset into a ten-page PDF. "
            "Company and person names in the two invented contracts are fictitious. They are inputs used to exercise the system, not a test set.")


# ---------------------------------------------------------------------------------------------------------------- 6.3
def sec_preprocessing(d):
    d.h2("Preprocessing: Parsing and Segmentation")
    d.h3("Text extraction")
    d.p("A PDF is read with PyMuPDF page by page, so every clause keeps its real page number. A DOCX is read with python-docx as the list of paragraph "
        "texts joined by line breaks; python-docx exposes no page breaks, so the whole file is treated as page 1. Other extensions are rejected before any "
        "work is done. Scanned PDFs without a text layer return no text and are therefore refused with the message that no readable clauses were found. "
        "The text is not otherwise cleaned: line breaks, hyphenation and running headers of a PDF stay exactly as extracted.")
    d.h3("Segmentation into clauses")
    d.p("Each page is split at lines that start with a heading number. The pattern accepts an optional word (Article, Section or Clause), one or two digits, "
        "optional sub-numbers such as `2.1`, an optional full stop, bracket or colon, and then text. If the page has at least two such headings, the text from "
        "one heading to the next is one clause; otherwise the page is split into blank-line paragraphs, and consecutive paragraphs are merged until the buffer "
        "reaches about 400 characters. A chunk shorter than 25 characters is discarded.")
    d.code(grab("backend/app/services/parsing.py", "CLAUSE_HEADER_RE = re.compile", 4), "Heading pattern in services/parsing.py")
    d.p("Four consequences follow from this design and were verified, by unit tests and by the corpus run. (1) **Text before the first numbered heading is dropped** "
        "whenever the page has two or more headings: the title, the parties and the recitals do not become clauses. (2) A clause that runs across a page break is "
        "cut in two, because pages are segmented independently. (3) Headings in other styles (\"ARTICLE I\", roman numerals, lettered lists) are not recognised, and "
        f"such a page falls back to paragraph merging. Over the {CO['contracts']} CUAD contracts {CO['contracts_with_header_split']} were split on numbered headings and "
        f"**{CO['contracts_with_fewer_than_5_clauses']} produced fewer than five clauses**; the median clause had {CO['mean_clause_chars_median']:,.0f} characters, "
        f"and the {CO['contracts']} contracts gave {CO['clauses_total']:,} clauses (median {CO['clauses_median']:.1f} per contract, maximum {CO['clauses_max']}). "
        "(4) Text without headings or blank lines, which is what PDF extraction usually produces, is not split at all: the real CUAD contract typeset into ten PDF pages gave eleven clauses, about one per page.")
    d.h3("Whitespace and the PDF problem")
    p = PA["freelance_services_agreement.pdf"]
    q = PA["freelance_services_agreement.docx"]
    d.p("Several rules contain a gap of the form `.{0,60}` between two key phrases. In a regular expression the dot does not match a line break, and a PDF keeps the "
        "line breaks of its layout, so a phrase that wraps onto the next line can break a rule. The same invented contract was uploaded as a DOCX and as a PDF with "
        f"identical text: the DOCX fired **{q['as_uploaded']['n_rules']} of 8** rules and the PDF **{p['as_uploaded']['n_rules']} of 8** (`ip_overreach` and "
        f"`one_sided_arbitration` were missed); when the whitespace of each clause was collapsed to single spaces before matching, the PDF again fired "
        f"{p['whitespace_collapsed']['n_rules']} of 8. The product does not collapse whitespace; the finding is reported as a defect with a one-line remedy.")
    if not _rep(d):
        d.figure(CHARTS / "10_format_parity.png", "The same contract as DOCX, as PDF, and as PDF with whitespace collapsed before matching", width=3.9)
    d.h3("Limits applied before calling the model")
    d.p("To bound cost and prompt size, the embedding call receives the first 8,000 characters of a clause, the tie-break and explanation prompts the first 1,500 "
        "characters, and the summary prompt the first 40 clauses with 400 characters each. A contract with more than 40 clauses is therefore summarised from "
        "its first 40 clauses only, although every clause is still classified and checked by the rules.")


# ---------------------------------------------------------------------------------------------------------------- 6.4
def sec_algorithm_choice(d):
    d.h2("Algorithm Choice and Justification")
    b = CL["baselines_top1"]
    d.table([["Decision", "Chosen", "Alternatives", "Why"],
             ["Clause type", "Gemini embedding + nearest centroid of 20 CUAD categories [13]", f"TF-IDF [14] centroid {b['TF-IDF nearest centroid']:.3f}, TF-IDF + logistic regression (scikit-learn [17]) {b['TF-IDF + logistic regression']:.3f}, 1-NN {b['Gemini embedding 1-NN']:.3f}, 5-NN {b['Gemini embedding 5-NN']:.3f}, embedding + logistic regression {b['Gemini embedding + logistic regression']:.3f} (all measured)", "No training step and no extra service beyond the embedding call; 500 spans are enough to give 20 centroids; new categories need only examples"],
             ["Predatory decision", "Eight regular-expression rules", "A classifier trained on labelled predatory clauses; an LLM verdict", "No labelled Indian predatory-clause data exists; a rule is auditable, deterministic and free; the price is recall (section 6.6)"],
             ["Combinations", "Three fixed rule-id sets matched anywhere in the contract; NetworkX graph [16]", "Neo4j knowledge graph with concepts and precedents (abstract)", "A single-process, dependency-light build; three patterns need no query language; edges are derived, not stored"],
             ["Wording", "Gemini, one call per flag and one for the summary", "Fixed templates", "The reason must refer to the actual wording and the safer clause must keep its purpose, which a template cannot do"],
             ["Complexity", "Weighted sum of four lexical measures [15]", "A model trained on human difficulty ratings", "No ratings exist; the formula is transparent; weights are the author's and not validated"],
             ["Storage", "SQLite blobs + NumPy cosine", "pgvector, a vector database", "At 20 centroids and tens of clauses per contract a linear scan is immediate"]],
            "Algorithm choices", widths=[0.12, 0.22, 0.34, 0.32], font=8.5)
    d.p("The comparison on the held-out spans is an honest one. The shipped nearest-centroid classifier scores "
       f"{b['Gemini embedding nearest centroid (shipped)']:.3f}, while a logistic regression trained on the same embeddings scores {b['Gemini embedding + logistic regression']:.3f}. "
       "With 240 test items the binomial standard error of an accuracy near 0.80 is about 2.6 points, so the two are indistinguishable; the nearest-centroid method was kept "
       "because it needs no fitting and is easy to explain, not because it is more accurate. The embedding methods are clearly better than the TF-IDF baselines "
       f"({b['Gemini embedding nearest centroid (shipped)'] - b['TF-IDF + logistic regression']:.3f} above the best of them), and all are far above chance (0.05).")
    if not _rep(d):
        d.figure(CHARTS / "02_classification_baselines.png", "Shipped classifier against simple baselines on the same 240 held-out spans", width=5.2)
    d.p("The rule engine was kept simple for a reason that is also its weakness. A regular expression never changes its answer, so a lawyer can read every rule; but "
        "it only recognises the vocabulary it was written for. The rules were written before the independent probe set existed and were not changed after it, so the "
        "probe scores in section 6.6 are an honest estimate of how the rules behave on wording they were not tuned for.")


# ---------------------------------------------------------------------------------------------------------------- 6.5
def sec_math(d):
    d.h2("Mathematical Formulation")
    d.p("The formulas below are those implemented in the code; symbols are defined where they are used.")
    d.h3("Clause classification")
    d.p("Let e(t) in R^3072 be the Gemini embedding of a text t. For each of the K = 20 categories, the centroid is the mean of the embeddings of its n = 25 training spans, "
        "c_k = (1 / n) Σ_(t in S_k) e(t), computed with the task type RETRIEVAL_DOCUMENT; a clause x is embedded with RETRIEVAL_QUERY. The similarity of the clause to "
        "category k is the cosine s_k = (e(x) · c_k) / ( ||e(x)|| ||c_k|| ). Sort the similarities so that s_(1) >= s_(2) >= s_(3) ... and let k_1, k_2, k_3 be the corresponding "
        "categories. The embedding label is k_1 with confidence s_(1).")
    d.p("**Tie-break rule.** If s_(1) - s_(2) < 0.03 **and** s_(1) < 0.60, Gemini is asked to choose one of {k_1, k_2, k_3}; if it answers with a category outside this "
        "set, the label is k_1 and the confidence s_(1); otherwise the label is the chosen category and the confidence is the value that Gemini returns. "
        "**Confidence floor.** If the final confidence is below 0.35 the label is replaced by \"Other / Unclassified\". The margin is the named constant "
        "TIE_BREAK_MARGIN = 0.03 in `classification.py`; 0.60 and 0.35 are literals in the same function.")
    d.h3("Predatory-clause rules and combinations")
    d.p("Each rule j is a regular expression ρ_j, and the flag indicator for clause x is r_j(x) = 1 if ρ_j matches x (case-insensitively) and 0 otherwise. The flag set "
        "is F(x) = { j : r_j(x) = 1 }. A combination C is a fixed set of rule ids; with U the union of F(x) over all clauses x of the contract, C fires when C is a subset of U, "
        "and the clauses involved are all clauses carrying at least one rule of C. Edges are drawn between every pair of involved clauses. Because the test uses only the "
        "set U, it does not require the rules to occur in neighbouring clauses or to disadvantage the same party.")
    d.h3("Complexity score")
    d.p("Let W be the number of words, S the number of sentences, Y the number of syllables (counted as groups of vowels `aeiouy`, minus a silent final e), L the number "
        "of hits of 34 legal-jargon terms (substring counts), X the number of cross-references (\"Section 4.2\", \"Clause 9\", \"herein\", \"hereof\" and similar) and n the number of clauses. "
        "The Flesch reading ease [15] is FRE = 206.835 - 1.015 (W / S) - 84.6 (Y / W), clipped to [0, 100]. The legalese density is D_L = 100 L / W and the average "
        "sentence length is a = W / S. Four difficulty values in [0, 100] are formed:")
    d.numbered([
        "readability difficulty D_r = 100 - FRE;",
        "jargon difficulty D_j = min(100, 8 D_L);",
        "cross-reference difficulty D_x = min(100, 40 X / n);",
        "sentence difficulty D_s = min(100, max(0, 3 (a - 15))).",
    ])
    d.p("The complexity score is Score = 0.35 D_r + 0.30 D_j + 0.20 D_x + 0.15 D_s, rounded to one decimal, and the grade is A for Score < 20, B for < 40, C for < 60, D for < 80 "
        "and F otherwise. The weights and cut-offs were chosen by the author and have not been validated against human ratings.")
    d.h3("Evaluation measures")
    d.p("For the rules, true positives, false positives and false negatives are counted over (clause, rule) pairs: TP = Σ |F(x) ∩ G(x)|, FP = Σ |F(x) \\ G(x)|, FN = Σ |G(x) \\ F(x)|, where G(x) "
        "is the set of expected rule ids. Precision P = TP / (TP + FP), recall R = TP / (TP + FN) and F1 = 2 P R / (P + R); these are micro-averaged over rules. For classification, "
        "top-k accuracy is the share of held-out spans whose true category is among the k most similar centroids, and the per-category recall is the share of that category's "
        "12 spans that receive its label. The standard error of an accuracy p measured on N items is √( p (1 - p) / N ), which is about 0.026 for p = 0.79 and N = 240.")


# ---------------------------------------------------------------------------------------------------------------- 6.6
def sec_model_training(d):
    d.h2("Model Construction, Thresholds and Measured Results")
    d.p("**No model is trained in this project.** The embedding model and the text model are remote Gemini services that were used as they are. The only fitted "
        "quantities are the 20 centroids, which are means of 25 embeddings each and are built once and cached in `data/cuad_centroids.npz`, and the three "
        "thresholds (0.03, 0.60, 0.35) and the weights of the complexity score, which are constants chosen by the author. This section describes how these were "
        "evaluated.")
    d.table([["Item", "Value"],
             ["Embedding model", "gemini-embedding-001, 3,072 values per vector; RETRIEVAL_DOCUMENT for the training spans, RETRIEVAL_QUERY for clauses"],
             ["Centroids", "20 categories x 25 spans, mean of float32 vectors; cached after the first build"],
             ["Tie-break", "margin < 0.03 and top-1 similarity < 0.60; Gemini chooses among the top 3"],
             ["Confidence floor", "below 0.35 gives \"Other / Unclassified\""],
             ["Text model", "default `gemini-flash-latest`; the measured runs used `gemini-3.1-flash-lite` because the default exceeded the free-tier limit of 20 requests per day"],
             ["Retries", "3 attempts per text call, sleeping 1.5 s, 3 s and 4.5 s"],
             ["Randomness", "None in the product; the data split uses seed 42"]],
            "Configuration of the analysis pipeline", widths=[0.22, 0.78], font=9.5)
    c = CL["centroid"]
    if _rep(d):
        d.p("The measured results (classification scores and baselines, the rule scores on the two test sets, the CUAD cross-check, the 510-contract run and the "
            "latencies) are reported in Chapter 8, where they are set beside the output screens. In short: the classifier reaches "
            f"{c['top1'] * 100:.1f} % top-1 and {c['top3'] * 100:.1f} % top-3 accuracy on 240 held-out CUAD spans; the rules reach precision "
            f"{RU['shipped_set']['overall']['precision']:.2f} and recall {RU['shipped_set']['overall']['recall']:.2f} on the 40 clauses written with them, but only "
            f"{RU['probe_set']['overall']['precision']:.2f} and {RU['probe_set']['overall']['recall']:.2f} on an independent set of 40.")
        return
    d.h3("Experimental protocol")
    d.numbered([
        "`scripts/exp_embed_cache.py` embeds the 500 training spans and the 240 held-out spans with the same Gemini calls the product makes and caches the 740 vectors (about 7 minutes).",
        "`scripts/exp_classification.py` runs the unmodified `ml/eval.py` with its embedding call answered from the cache, so `experiments/eval/metrics.json` holds exactly what the shipped evaluation code computes. It then adds checks the shipped evaluation does not make.",
        "`scripts/exp_rules_corpus.py` scores the rules on the shipped 40-clause set, on a second independent set, on CUAD spans, and runs the non-API pipeline over all 510 CUAD contracts.",
        "`scripts/exp_format_parity.py` compares the flags for a DOCX and a PDF of the same text.",
    ])
    d.h3("Classification on 240 held-out CUAD spans")
    ev = CL["shipped_eval"]
    d.p(f"The shipped evaluation code reports top-1 accuracy **{ev['top1_accuracy']:.3f}** and top-3 accuracy **{ev['top3_accuracy']:.3f}** over {ev['num_examples']} spans and "
        f"{ev['num_categories']} categories (chance is 0.05); top-5 is {c['top5']:.3f}. After removing the {CL['exact_duplicates_eval_in_train']} spans that duplicate a training "
        f"text, top-1 is {c['top1_without_duplicates']:.3f}. Rebuilding the centroids without any training span from the same contract as the test span (192 of the 240 items "
        f"had such a span) gives {CL['contract_disjoint']['top1']:.3f}, so the contract overlap did not inflate the score. Recall is highest for Governing Law, Ip Ownership "
        "Assignment and Renewal Term (1.00 each) and lowest for Non-Compete and Cap On Liability (0.50 each), No-Solicit Of Customers (0.58) and Exclusivity, Liquidated Damages "
        "and Uncapped Liability (0.67 each). The largest confusions are Uncapped Liability predicted as Cap On Liability (4), Non-Compete as No-Solicit Of Customers (4) and "
        "the two no-solicit categories with each other (3 and 3): neighbouring legal concepts with similar vocabulary.")
    d.figure(CHARTS / "01_classification_per_category.png", "Recall of the classifier in each of the 20 categories (12 held-out spans each)", width=5.4)
    d.figure(CHARTS / "05_confusion_matrix.png", "Confusion matrix on the 240 held-out spans", width=5.2)
    d.h3("Two thresholds that never act")
    tb = CL["tie_break"]
    d.p(f"On the 240 spans the best cosine similarity ranges from {tb['confidence_min_median_max'][0]:.3f} to {tb['confidence_min_median_max'][2]:.3f} (median "
        f"{tb['confidence_min_median_max'][1]:.3f}). The margin test alone would pass for 152 spans (the median margin between the best two categories is 0.023), but "
        "the tie-break also requires the best similarity to be below 0.60, and no span is below 0.657; and the floor of 0.35 is never reached. The same holds in the three real "
        "uploads: all 30 clauses carry the method `embedding` and confidences between 0.72 and 0.83. With this embedding model the two branches are dead code, and **every clause "
        "is forced into one of the 20 labels**, including boilerplate that belongs to none of them. The constants were evidently tuned for an embedding model with a different "
        "similarity scale. Accuracy by band confirms that confidence is a weak signal: 0.600 for the five spans between 0.65 and 0.70 and 0.796 for the 235 above 0.70.")
    d.figure(CHARTS / "09_confidence_thresholds.png", "Where the two thresholds sit relative to the measured similarities", width=5.8)
    d.p("A further observation concerns whole clauses. In a manual reading of the 19 clauses of the two invented contracts, 9 received a plausible label (5 of 11 and 4 of 8), "
        "noticeably below the 79 % obtained on short spans. For example, the fees clause of the fair contract was labelled Liquidated Damages and its confidentiality clause Post-Termination "
        "Services. This is a small, informal check, but it agrees with the difference in text length between the test spans and real clauses.")
    d.h3("Predatory-clause rules")
    s, pb = RU["shipped_set"]["overall"], RU["probe_set"]["overall"]
    d.table([["Test set", "Items", "TP", "FP", "FN", "Precision", "Recall", "F1"],
             ["Shipped set (written with the rules)", "40 clauses", str(s["tp"]), str(s["fp"]), str(s["fn"]), f"{s['precision']:.3f}", f"{s['recall']:.3f}", f"{s['f1']:.3f}"],
             ["Independent probe set", "24 + 16 clauses", str(pb["tp"]), str(pb["fp"]), str(pb["fn"]), f"{pb['precision']:.3f}", f"{pb['recall']:.3f}", f"{pb['f1']:.3f}"]],
            "Rule scores on the two test sets", widths=[0.3, 0.14, 0.07, 0.07, 0.07, 0.12, 0.11, 0.12], font=9.5, align=["l", "l", "c", "c", "c", "c", "c", "c"])
    d.p("The shipped set reproduces the published figures (precision 1.00, recall 0.94, F1 0.97), but it was written by the author of the rules, so it measures whether the rules "
        "find the wording they were written for. On 40 clauses phrased independently, 24 predatory paraphrases and 16 benign look-alikes, the same rules give precision "
        f"{pb['precision']:.2f} and recall {pb['recall']:.2f}. Thirteen paraphrases were missed (for example \"agrees not to accept any engagement\", \"cannot be returned for any reason\", "
        "\"liability ... shall be unlimited\", \"sole arbitrator appointed by the Company\") and three benign clauses were flagged (a capped liquidated-damages clause, a "
        "conflict-of-interest restriction and mutual liability for gross negligence). Per-rule recall on the probe set is 0.67 for auto_renewal, ip_overreach and "
        "unilateral_termination and 0.33 for the other five rules.")
    d.figure(CHARTS / "03_rules_two_test_sets.png", "Rule precision, recall and F1 on the shipped set and on the independent probe set", width=4.6)
    rp, fp = RU["cuad_spans"]["recall_proxy"], RU["cuad_spans"]["false_positive_proxy"]
    d.p("A second view comes from CUAD. CUAD's categories are not the same concept as \"predatory\", so the figures below are a proxy and not a recall: they give the share of "
        "CUAD spans of the closest category on which a rule fires. The rule fires on "
        f"{rp['Liquidated Damages']['rate'] * 100:.1f} % of Liquidated Damages spans, {rp['Renewal Term']['rate'] * 100:.1f} % of Renewal Term, {rp['Termination For Convenience']['rate'] * 100:.1f} % "
        f"of Termination For Convenience, {rp['Non-Compete']['rate'] * 100:.1f} % of Non-Compete, and on none of the {rp['Uncapped Liability']['n_spans']} Uncapped Liability or "
        f"{rp['Ip Ownership Assignment']['n_spans']} Ip Ownership Assignment spans, because United States drafting uses different phrases. On {fp['n_spans']:,} spans of 11 unrelated "
        f"categories a rule fires on {fp['any_rule_fires']} ({fp['any_rule_fires'] / fp['n_spans'] * 100:.2f} %).")
    d.figure(CHARTS / "07_cuad_rule_hits.png", "Share of CUAD spans of the closest category on which each rule fires", width=5.2)
    d.h3("Complexity score over the CUAD corpus")
    g = CO["grades"]
    d.p(f"Over the {CO['contracts']} CUAD contracts the score has minimum {CO['score']['min']}, median {CO['score']['median']}, mean {CO['score']['mean']} and maximum {CO['score']['max']} "
        f"(standard deviation {CO['score']['stdev']}); the grades are A {g['A']}, B {g['B']}, C {g['C']}, D {g['D']} and F {g['F']}. The score correlates only weakly with contract length "
        f"(r = {CO['corr_score_vs_words']}). The measure is lexical: the invented one-sided freelance contract, written in plain words, received grade B (23.3), and the fair contract grade A (13.7). "
        "The grade measures how hard a contract is to read, not how fair it is, and the interface labels it accordingly.")
    d.figure(CHARTS / "06_complexity_distribution.png", "Complexity scores of the 510 CUAD contracts", width=4.9)
    d.h3("Run time")
    d.p(f"The non-API part of the pipeline (segmentation, rules, combinations and complexity) processed the {CO['contracts']} contracts in {CO['total_seconds']} s, "
        f"{CO['mean_seconds_per_contract'] * 1000:.0f} ms per contract. An upload is dominated by Gemini: the measured uploads took "
        f"{AP['uploads']['balanced']['seconds']} s (8 clauses, no flag), {AP['uploads']['cuad_pdf']['seconds']} s (11 clauses, 1 flag) and {AP['uploads']['freelance']['seconds']} s "
        "(11 clauses, 8 flags), that is, about 12 seconds per text call. The API endpoints that do not call Gemini answered in 2 to 15 ms, with the bcrypt endpoints near 255 ms.")


# ---------------------------------------------------------------------------------------------------------------- 6.7
def sec_app_arch(d):
    d.h2("Application Architecture")
    if not _rep(d):
        d.figure(DIAG / "01_system_architecture.png", "System architecture of ClauseGuard", width=6.2)
    d.paras(
        "The backend is a FastAPI application organised in three layers. Routers in `routes/` (auth, contracts, eval) validate input, map exceptions to status codes and "
        "check ownership; the analysis logic lives in `services/`, where `pipeline.process_upload()` calls parsing, classification, the rules, the combination graph, the "
        "complexity score and the explanation service; and `db.py` defines four SQLAlchemy models over SQLite. Pydantic schemas in `schemas.py` define the "
        "request and response types, `auth.py` holds the password and token helpers, and `config.py` reads the settings from `.env`. The centroid matrix is loaded lazily on "
        "the first classification and cached in memory; Gemini is configured on the first call.",
        "The frontend is a single-page React 19 application built with Vite. React Router defines the public and the protected routes, TanStack Query fetches and caches "
        "the API data, Axios attaches the bearer token and raises a session-expired event on a 401 from a protected call, Recharts draws the severity chart, and Tailwind "
        "CSS 4 with Radix primitives provides the components; Framer Motion, GSAP and Lenis supply the motion on the landing page. The token and the e-mail are kept in "
        "local storage. The Vite development server proxies `/api` to the backend, so the browser uses one origin.")
    d.table([["Layer", "Technology", "Version"],
             ["Language and runtime", "Python; Node.js", "3.11.9; 24.19.0"],
             ["Web framework", "FastAPI with uvicorn; python-multipart; email-validator", "0.115.0; 0.30.6; 0.0.9; 2.2.0"],
             ["Database", "SQLAlchemy over SQLite", "2.0.35"],
             ["Documents", "PyMuPDF; python-docx", "1.24.10; 1.1.2"],
             ["Numerics and graph", "NumPy; NetworkX", "1.26.4; 3.3"],
             ["Language model", "google-generativeai (Gemini API client)", "0.8.3"],
             ["Security", "PyJWT (HS256); bcrypt", "2.9.0; 4.2.0"],
             ["Frontend", "React; Vite; Tailwind CSS; TanStack Query; React Router; TypeScript", "19.3.1; 6.4.4; 4.3.3; 5.104.2; 8.4.0; 7.0.2"],
             ["Size", "Backend application code; frontend sources", "about 1,250 lines in 17 files; 56 files, 4,507 lines"]],
            "Technology stack of the implementation", widths=[0.24, 0.5, 0.26], font=9.5)
    d.p("The pages follow the user's task. **Public:** landing (with the measured scores of the rule evaluation), sign-up, log-in and evaluation. **Signed in:** My contracts, "
        "Upload contract, the contract report, the clause detail page and the clause graph.")


# ---------------------------------------------------------------------------------------------------------------- 6.8
def sec_walkthrough(d):
    d.h2("Key Code Walkthroughs")
    d.h3("Segmentation")
    d.p("The splitter keeps a page as one clause list when it finds at least two numbered headings, which is also why text before the first heading is lost: the "
        "first chunk starts at the first match.")
    d.code(grab("backend/app/services/parsing.py", "def _split_page_text", 9), "Heading-based segmentation in services/parsing.py")
    d.h3("Classification")
    d.p("The clause is ranked against the centroids; the tie-break is attempted only when both conditions hold, and any Gemini failure silently falls back to the embedding result.")
    d.code(grab("backend/app/services/classification.py", "sims = cosine_similarity_matrix(embedding, centroids)", 28), "Nearest centroid, tie-break and floor in services/classification.py")
    d.h3("A rule")
    d.p("A rule bundles an id, a label, a severity, the stated legal basis and the compiled pattern; `detect_flags()` is a one-line filter over the list of rules.")
    d.code(grab("backend/app/services/rules.py", 'id="no_refund"', 12, back=1), "The no-refund rule in services/rules.py")
    if not _rep(d):
        d.code(grab("backend/app/services/rules.py", "def detect_flags", 2), "Rule application in services/rules.py")
    d.h3("Risky combinations")
    d.p("The rule ids found anywhere in the contract are collected, and a combination fires when all of its rule ids are present; the clauses involved are those carrying any of them.")
    d.code(grab("backend/app/services/graph.py", "def detect_risky_combinations", 22), "Combination detection in services/graph.py")
    d.h3("Complexity score")
    d.p("The four lexical measures are turned into difficulty values and combined with fixed weights; the grade is a lookup on the result.")
    d.code(grab("backend/app/services/complexity.py", "readability_difficulty = ", 12), "Weighted complexity score in services/complexity.py")
    d.h3("The pipeline loop")
    d.p("One loop classifies, flags and explains each clause; a Gemini failure raises out of the loop and, because the commit comes last, nothing is saved.")
    d.code(grab("backend/app/services/pipeline.py", "for raw in raw_clauses:", 34 if not _rep(d) else 17), "Per-clause processing in services/pipeline.py")
    d.h3("Ownership check and token guard")
    d.code(grab("backend/app/routes/contracts.py", "def _get_owned_contract", 5), "Ownership check in routes/contracts.py")
    if not _rep(d):
        d.code(grab("backend/app/auth.py", "def get_current_user", 9), "Authentication dependency in auth.py")
        d.code(grab("backend/app/services/gemini_client.py", "def _call_model", 12), "Gemini call with retries in services/gemini_client.py")


# ---------------------------------------------------------------------------------------------------------------- 6.9
def sec_api(d):
    d.h2("API Design")
    d.p("The API is REST over JSON under `/api`: nine endpoints and no WebSocket. Interactive documentation is generated by FastAPI at `/docs`. Every endpoint except "
        "health, registration, log-in and the evaluation results needs `Authorization: Bearer <token>`. Errors have the form `{\"detail\": \"message\"}`; the status codes in "
        "the table are those returned by the code or observed in the tests.")
    d.table([["Method", "Path", "Auth", "Purpose and responses"],
             ["GET", "/api/health", "no", "`{status, gemini_configured, port}`"],
             ["POST", "/api/auth/register", "no", "`{email, password >= 6}` returns `{token, email, user_id}`; 400 if the e-mail exists; 422 for an invalid e-mail or short password"],
             ["POST", "/api/auth/login", "no", "Returns `{token, email, user_id}`; 401 for a wrong password or unknown e-mail"],
             ["POST", "/api/contracts/upload", "yes", "Multipart `file` (.pdf or .docx): full pipeline, returns the report; 503 without an API key, 400 for another extension or no readable clause, 502 when Gemini fails"],
             ["GET", "/api/contracts", "yes", "The caller's contracts: id, filename, uploaded_at, grade, score, flag_count"],
             ["GET", "/api/contracts/{id}", "yes", "Report: grade, score, four component values, plain_summary, key_obligations, combo_flags, clause summaries; 404 if not the caller's"],
             ["GET", "/api/contracts/{id}/clauses/{cid}", "yes", "Clause text, type, confidence, method, flags with reason, provision and safer_wording; 404"],
             ["GET", "/api/contracts/{id}/graph", "yes", "Nodes, edges and risky combinations; 404"],
             ["GET", "/api/eval/metrics", "no", "Contents of `experiments/eval/metrics.json` with `available: true`, or a message when no evaluation has been run"]],
            "API endpoints", widths=[0.09, 0.3, 0.07, 0.54], font=8.5)
    d.p("**Example: the report of an upload.** An abbreviated response for the invented freelance contract:")
    d.code('POST /api/contracts/upload  (multipart: file = freelance_services_agreement.docx)\n'
           '-> 200 {"id": 1, "filename": "freelance_services_agreement.docx",\n'
           '        "complexity_grade": "B", "complexity_score": 23.3, "readability_score": 39.8,\n'
           '        "legalese_density": 0.71, "cross_reference_count": 0, "avg_sentence_length": 16.2,\n'
           '        "plain_summary": "...", "key_obligations": ["...", "..."],\n'
           '        "combo_flags": [{"combo_id": "termination_norefund_penalty", "rule_ids": [...], "clause_ids": [2, 3, 4], "reason": "..."}, ...],\n'
           '        "clauses": [{"id": 1, "index_in_doc": 0, "page_number": 1, "clause_type": "Ip Ownership Assignment",\n'
           '                     "text_preview": "...", "flag_count": 0, "max_severity": "none"}, ...]}',
           "Upload response (shape, abbreviated)")
    d.p("**Example: a clause.** `GET /api/contracts/1/clauses/2` returns the clause with `flags: [{rule_id: \"unilateral_termination\", rule_label, severity: \"high\", reason, provision, "
        "safer_wording}]`. Reason, provision and safer wording are the text returned by Gemini; the rule id, label and severity come from the rule. A caller who requests "
        "a contract or clause of another user receives 404, not 403, so the existence of the contract is not revealed.")
    d.p("The cost of an upload grows with the content: the server makes one embedding call per clause, one text call per flag and one for the summary, one after the other. "
        "The measured eleven-clause contract with eight flags took 113.6 s, which is inside the 180 s client timeout but leaves little margin.")


# ---------------------------------------------------------------------------------------------------------------- 6.10
def sec_security(d):
    d.h2("Security and Error Handling")
    ap = AP["endpoints"]
    d.bullets([
        "**Passwords** are hashed with bcrypt [18] before storage; registration requires a syntactically valid e-mail address (validated by the `email-validator` package) and a password of at least six characters. The hash check costs about 255 ms, which slows brute-force attempts.",
        "**Tokens.** A signed JSON Web Token [19] (HS256, PyJWT) with the user id and e-mail and an expiry of 1,440 minutes is issued at registration and log-in; every contract route decodes it and loads the user, and an invalid, expired or forged token, or a token for a deleted user, returns 401. A request without any token returns 403 (observed: "
        f"{ap['GET /api/contracts (no token -> 403)']['status']} in {ap['GET /api/contracts (no token -> 403)']['median_ms']} ms).",
        "**Ownership.** `_get_owned_contract()` returns 404 for a contract that does not belong to the caller, for the report, the clause and the graph routes alike; the list route filters by the caller's id.",
        "**Uploads.** Only the extensions `.pdf` and `.docx` are accepted, checked by file name and not by content. The file is written under a random UUID name and removed in a `finally` block whether the analysis succeeds or fails.",
        "**Atomicity.** The pipeline commits once at the end; a Gemini failure raises before the commit, the session is closed without saving, and a test confirms that no half-written contract is left.",
        "**Secrets.** The Gemini key and the JWT secret are read from `.env`, which is excluded from version control; if `JWT_SECRET` is missing, `config.py` falls back to a fixed development value.",
        "**Cross-origin requests** are allowed from any origin (`allow_origins=[\"*\"]`).",
    ])
    d.p("**Errors.** A `ValueError` from parsing becomes HTTP 400, a `RuntimeError` (the Gemini client raises it after three failed attempts) becomes HTTP 502 with the upstream message in "
        "the detail, and the missing key gives 503. By code reading, a malformed JSON answer from the model raises `json.JSONDecodeError`, which is a subclass of `ValueError`, "
        "so it would be reported as HTTP 400 and not 502; this path was not exercised. The browser translates the status codes into readable messages and shows an expired-session toast on a 401.")
    d.p("**Known gaps, stated so that they are not mistaken for features.** (1) The server does not limit the size of an uploaded file; the whole file is read into memory. "
        "(2) The file type is judged by its name only. (3) There is no rate limiting, no HTTPS in the development setup and no audit log. (4) The token is kept in the browser's local "
        "storage, where any script running on the page could read it. (5) The fallback JWT secret and the wildcard cross-origin policy are suitable for development only. "
        "(6) Contract text is sent to a third-party service (Google Gemini) for embedding, explanation and summary, and the extracted clause text is stored unencrypted in SQLite; "
        "for confidential contracts this needs an explicit decision by the user. (7) Text taken from a contract is placed in the prompts, so a contract can contain instructions "
        "addressed to the language model; the rules decide the flags, but the wording could be influenced. (8) The evaluation endpoint is public by design.")


# ---------------------------------------------------------------------------------------------------------------- 6.11
def sec_install(d):
    d.h2("Installation and Execution")
    d.p("The application needs Python 3.10 or later (3.11.9 was used), Node.js and a Gemini API key. All commands are run from the project folder `8.ProjectCode`.")
    d.table([["Step", "Command", "What it does"],
             ["1", "setup.bat", "Creates `venv`, installs `backend/requirements.txt`, runs `npm install` in `frontend`, creates `.env` from `.env.example` if missing, and downloads CUAD if `data/cuad/CUADv1.json` is absent (it is committed)"],
             ["2", "Edit `.env`: GEMINI_API_KEY, GEMINI_TEXT_MODEL, GEMINI_EMBEDDING_MODEL (`models/gemini-embedding-001`), JWT_SECRET", "The backend reads exactly these names; the template's default model names (`gemini-2.0-flash`, `models/text-embedding-004`) are no longer served, and the `GEMINI_MODEL` / `GEMINI_EMBED_MODEL` lines at the end of the template are not read"],
             ["3", "run.bat", "Starts uvicorn on port 8106 and `npm run dev` on port 5106 in two windows and opens http://localhost:5106 (use `localhost`: Vite listens on the IPv6 loopback)"],
             ["4", "Sign up in the browser", "There is no pre-seeded account; any e-mail with a 6-character password works (reserved domains such as `.local` are rejected by the validator)"],
             ["5", "venv\\Scripts\\python.exe -m pytest", "Runs the 73 tests (68 pass, 5 expected failures) in about 10 s, with Gemini stubbed; needs `pytest` and `httpx` in the venv"],
             ["6", "venv\\Scripts\\python.exe scripts\\smoke_test.py", "Live end-to-end test against the running API (needs a working key)"],
             ["7", "venv\\Scripts\\python.exe ml\\eval.py", "Recomputes `experiments/eval/metrics.json` (rules; CUAD classification if a key is set)"]],
            "Installation and execution", widths=[0.07, 0.38, 0.55], font=8.5)
    if not _rep(d):
        d.p("The experiments of this chapter are reproduced with `scripts/exp_embed_cache.py` (needs the key and takes about seven minutes), `exp_classification.py`, `exp_rules_corpus.py` and "
            "`exp_format_parity.py`; the screenshots with `scripts/capture_screens.py`; the latency table with `scripts/measure_api.py`. If the default text model is over quota, set "
            "`GEMINI_TEXT_MODEL` in the environment of the backend process to another model; the measured runs of this project used `gemini-3.1-flash-lite`.")
        d.p("**Golden path.** Sign up, upload a contract, wait for the analysis (about 15 s for a short contract without flags and about two minutes for one with many), read the grade and the "
            "summary, open a flagged clause to read the safer wording, open the clause graph for the combinations, return to My contracts, and open Evaluation for the measured scores.")
    else:
        d.p("The full user guide, with the commands for the experiments, is in Appendix B.")
