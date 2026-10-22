"""Novelty, contributions, scope, limitations, walkthroughs, decisions, conclusion (Chapter 9) and future scope (Chapter 10)."""

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R

S1P, S1L, S2, S3, S4 = F.SETS


def src(rel, start=None, end=None):
    """Lines start..end (1-based, inclusive) of a source file of 8.ProjectCode, for code listings."""
    import os

    lines = open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    return "\n".join(lines[(start or 1) - 1:end or len(lines)]).rstrip("\n")


def src_fn(rel, qualname):
    """Source of one function or method ('Pipeline.answer', 'fuse') found with ast, so line numbers never go stale."""
    import ast
    import os

    text = open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n")
    tree = ast.parse(text)
    lines = text.split("\n")
    parts = qualname.split(".")
    nodes = tree.body
    node = None
    for p in parts:
        node = next(n for n in nodes if getattr(n, "name", None) == p)
        nodes = getattr(node, "body", [])
    first = (node.decorator_list[0].lineno if node.decorator_list else node.lineno)
    body = lines[first - 1:node.end_lineno]
    if len(parts) > 1:  # de-indent a method
        body = [ln[4:] if ln.startswith("    ") else ln for ln in body]
    return "\n".join(body)


def c(*keys):
    """Citation string such as [1], [6] from CITE keys."""
    return "[" + ", ".join(str(R[k]) for k in keys) + "]"


def _r(cfg, s, key="top1"):
    return F.RET[cfg][s][key]


# ------------------------------------------------------------------ document 9
def novelty_blocks():
    base = c("base")
    return [
        P(f"{F.PRODUCT} does not propose a new retrieval algorithm, and we do not claim one. Its building blocks (sentence embeddings, a flat FAISS index, BM25, a cross-encoder, an instruction-tuned T5 model, bcrypt and signed tokens) "
          f"are standard {c('sbert', 'faiss', 'bm25', 'monobert', 'flan')}. What is new is the combination, the safety and privacy handling around it, the delivery as a complete local application, and the care taken to measure it and to say where the measurement is weak. "
          "This section states the difference from the base paper first and then separates what is new from what is not."),
        H2("2.1 Difference from the base paper"),
        P(f"The base paper {base} describes a symptom-monitoring chatbot built from a \"Sequence-NQ transformer\", FAISS similarity search and retrieval-augmented generation over a symptom-disease knowledge base, with registration, login and a stored consultation history. "
          "Its results are qualitative. This project keeps that outline and changes the following."),
        TAB("What this project adds to the base paper", ["Element", "Base paper", "This project"],
            [["Retrieval", "Dense similarity search with FAISS", f"Dense search and BM25 run side by side, min-max fused with weights {F.FUSION_WEIGHTS[0]} and {F.FUSION_WEIGHTS[1]} over a pool of {F.CANDIDATE_K} records"],
             ["Ranking", "Similarity order", f"Cross-encoder reranking of the pool to the top {F.TOP_K}"],
             ["Query handling", "Query embedded as typed", "Normalisation and a HyDE-style expansion template"],
             ["Safety", "Not described", "Emergency rules, caution keywords, answer filter and a permanent disclaimer"],
             ["Resilience", "Not described", "TF-IDF embedding fallback, hybrid order without reranker, evidence-based answer without generator"],
             ["Application", "Web application with log-in", "FastAPI service and React interface, bcrypt hashing, signed cookie tokens, per-user history with search, detail and delete"],
             ["Evaluation", "Qualitative observations", "Five query sets, an ablation, probes for relevance display and safety, latency and tests, with the defects reported"]],
            widths=[1.2, 1.7, 3.4], align=["l", "l", "l"], size=9.5),
        H2("2.2 What is new, and why it is not oversold"),
        N(f"**Hybrid fusion plus reranking in a symptom assistant.** The measured gain of the cross-encoder over plain fusion is real on lay language ({F.pct(_r('hybrid', S4), 1)} to {F.pct(_r('hybrid_rerank', S4), 1)} top-1 on {F.SHIP[S4]['n']} probes) but is small in absolute terms and BM25 alone is strong on this data ({F.pct(_r('bm25', S4), 1)}).",
          "**A safety layer around the answer.** Rules escalate emergencies and an answer filter removes some medication instructions. The layer works on the wording it was written for and fails on paraphrase (Chapter 8), which is itself a finding.",
          "**Graceful degradation.** Every model has a fallback, so the application starts and answers on a laptop with no network after the first download.",
          "**Private, local operation.** Consultations stay in a local SQLite file and are isolated per user; a test checks that one user cannot open another's record.",
          "**An honest evaluation harness.** It separates the shipped protocol, whose 100% is an upper bound, from leave-one-out, two-symptom and lay-language queries, and it measures the relevance display, the generator and the safety rules."),
        H2("2.3 What is not new"),
        B("The embedding model, the FAISS index, BM25, the cross-encoder and Flan-T5 are used as published; nothing was trained or fine-tuned.",
          "HyDE-style expansion here is a fixed template, not the language-model generation of the original HyDE method " + c("hyde") + ", and it showed no measurable benefit.",
          "Retrieval-augmented generation itself is established " + c("rag", "medrag") + "; the guarantee of grounding comes from using only retrieved text.",
          "The knowledge base is synthetic; the project contributes no medical knowledge."),
    ]


def contribution_blocks():
    return [
        H2("3.1 Contributions"),
        N("A working local hybrid-RAG symptom assistant, implemented as the CareLens AI web application, that retrieves grounded information for symptoms described in everyday language and shows it with evidence cards, severity and red flags.",
          f"A retrieval stage that fuses FAISS semantic search and BM25 lexical search ({F.FUSION_WEIGHTS[0]}/{F.FUSION_WEIGHTS[1]}) and reranks with a cross-encoder, with an ablation of seven configurations on five query sets.",
          "A safety and privacy design: emergency escalation, caution keywords, an answer filter, bcrypt-hashed accounts, signed cookies and per-user history.",
          "Offline fallbacks for every model so the system runs without network access after installation.",
          "An evaluation harness (`scripts/measure_metrics.py`) that exposes weaknesses the original evaluation hid: the leaking shipped protocol, the constant relevance display, the echoing generator and the paraphrase blind spot of the safety rules.",
          f"A reproducible documentation set: {F.PYTEST_TOTAL} unit tests, an {F.SMOKE_TOTAL}-check end-to-end test, a screenshot capture script and a facts file from which every number in these documents is read."),
    ]


# ------------------------------------------------------------------ document 10
def scope_blocks():
    return [
        H2("1.1 In scope"),
        B("Free-text symptom input of 3 to 2000 characters, normalised and expanded locally.",
          f"Retrieval over a knowledge base of {F.KB['records']} records for {F.KB['conditions']} common conditions, with hybrid fusion and reranking.",
          "A grounded answer, ranked evidence cards with symptoms, description, guidance, severity and red flags, and a match indicator.",
          "Emergency and caution banners and a permanent not-a-diagnosis disclaimer.",
          "Registration, sign-in and sign-out; a private consultation history with search, detail view and deletion.",
          "A React interface with light and dark themes and phone-width layouts; Docker files and a one-click `run.bat` for Windows."),
        H2("1.2 Out of scope"),
        B("Diagnosis, triage decisions, prescriptions or any clinical use; the application states that it gives preliminary information only.",
          "Trend analysis, timelines, symptom scoring or alerts over a user's history (objective 5 is met only as storage).",
          "Medical images, laboratory reports, wearable data, voice input and languages other than English.",
          "Clinician accounts, sharing of records, e-mail, notifications and any cloud service.",
          "Training or fine-tuning any model; the three models are used as published."),
        H2("1.3 Users and platform"),
        P("The intended user is a member of the public who wants preliminary information before seeing a professional, and an examiner or developer who explores the pipeline. The application runs on a Windows PC with Python 3.10 or newer and Node.js 18 or newer; "
          f"it was measured on a CPU-only machine ({F.ENV['cpu']}, {F.ENV['ram_gb']} GB)."),
    ]


def assumption_blocks():
    return [
        H2("2.1 Assumptions"),
        B("The user describes symptoms in English, in plain words, and is the person who has them.",
          "The knowledge base covers the condition: the pipeline always returns the nearest records, whether or not the right condition is present.",
          "The application runs on a trusted machine; the secret key and the database file are protected by the operating system.",
          "The three models can be downloaded once; afterwards the application is offline-capable.",
          "A single user session at a time is typical; no concurrency requirement was set."),
    ]


def limitation_blocks():
    s, g, r = F.SAF, F.GEN, F.REL
    return [
        H2("3.1 Limitations"),
        N(f"**Synthetic knowledge base.** {F.KB['records']} records written by the team, one description per condition; no public dataset, no clinical review. Scores describe lookup in this table, not medical accuracy (Chapter 8).",
          f"**Evidence cards are near-duplicates.** Mean distinct conditions among the five records: {F.SHIP[S4]['mean_distinct_conditions_in_top5']} on lay probes. The list is not a differential.",
          f"**The relevance indicator is relative.** The top record is always 100% and all {r['out_kb_n']} out-of-knowledge-base complaints were labelled Strong match; the system cannot abstain.",
          f"**The local generator echoes its prompt** in the tested environment ({g['echo_answers']} of {g['n']} answers; transformers {g['transformers_version']}); answers come from the fallback template.",
          f"**Safety rules are wording-bound.** Recall {F.pct(s['emergency_recall'], 1)} on {s['n_pos']} emergencies, 0 of {s['by_group_pos']['paraphrase']['n']} paraphrased ones; {len(s['by_group_neg']['hard']['false_emergency'])} of {s['by_group_neg']['hard']['n']} hard negatives raised a false alarm; the answer filter is case-sensitive.",
          "**No symptom tracking over time.** The history is a list; there are no trends or progression.",
          "**No per-statement citations** and no judgement of groundedness by humans or a model.",
          f"**Hardware.** On a CPU the cross-encoder costs about {F.LAT['stages_ms']['rerank']['mean']:.0f} ms per query and the first request loads the models (about a minute).",
          "**Single-user scale.** SQLite, one process, no concurrency or load testing; the signing key defaults to a development value that must be changed for any shared use."),
    ]


def not_measured_blocks():
    return [
        H2("4.1 What was not measured"),
        B("Clinical accuracy on real patient descriptions or a licensed medical knowledge base.",
          "Answer quality or groundedness as judged by clinicians or by a model; any user-study measure such as trust, comprehension or time saved.",
          "Retrieval accuracy as a function of knowledge-base size; only 176 records were available.",
          "Throughput, concurrency and memory under load; cold-start time was measured once.",
          "Browser accessibility and compatibility beyond the Chrome captures; mobile behaviour was seen only at one phone width.",
          "The behaviour of the generator under transformers 4.x, where the `text2text-generation` task exists."),
    ]


def walkthrough_blocks():
    return [
        P("The excerpts below are copied from the repository in the state in which the results were measured. Each is followed by the reason it is written the way it is."),
        H2("3.1 Query expansion (`app/rag/query_expansion.py`)"),
        CODE(src_fn("app/rag/query_expansion.py", "expand_query_hyde"), 8),
        P("The user's text is lower-cased and split on commas, full stops, \"and\" and \"with\" into at most eight fragments. A fixed sentence wraps them as a \"hypothetical\" description, and the combined string is what both retrievers receive. "
          "The method needs no model and no network, which is why it was chosen; the ablation shows it adds nothing measurable."),
        H2("3.2 Score fusion (`app/rag/hybrid_retriever.py`)"),
        CODE(src_fn("app/rag/hybrid_retriever.py", "fuse"), 8),
        P("FAISS inner products and BM25 scores live on different scales, so each is min-max normalised over the candidates before the weighted sum. A record found by only one retriever scores 0 on the other. "
          "The weights 0.65 and 0.35 are configuration values; they were not tuned in this project."),
        H2("3.3 Reranking and the displayed relevance (`app/rag/reranker.py`)"),
        CODE(src_fn("app/rag/reranker.py", "Reranker.rerank"), 8),
        P("The cross-encoder scores each query-record pair. The lines at the end rescale the scores of the candidates to 0 to 1 for display; because the lowest and highest candidates become exactly 0 and 1, the top record is always 100%, "
          "which is the cause of the constant relevance display measured in Chapter 8. Showing the raw score, or a threshold on it, would preserve the uncertainty."),
        H2("3.4 The pipeline (`app/rag/pipeline.py`)"),
        CODE(src_fn("app/rag/pipeline.py", "Pipeline.answer"), 7.5),
        P("`answer` strings the stages together: expansion, embedding, the two searches, fusion, reranking, evidence assembly, safety check, generation, the answer filter and, for emergencies, a prepended notice. "
          "The label bands 0.66 and 0.33 are applied to the rescaled score. The pipeline is a lazily created singleton, so the models load once, on the first request."),
        H2("3.5 Safety rules (`app/rag/safety.py`)"),
        CODE(src_fn("app/rag/safety.py", "check_safety"), 8),
        CODE(src_fn("app/rag/safety.py", "apply_safety_filter"), 8),
        P("Ten regular expressions map wording to an emergency advice sentence; six keywords raise a caution. The rules are fast and transparent and can be read by a clinician, but they match words, not meaning: negation, history and paraphrase are outside their reach. "
          "In the filter, detection lower-cases the text while the replacement does not, so a capitalised phrase is detected and left in place."),
        H2("3.6 Answer generation and its fallback (`app/rag/generator.py`)"),
        CODE(src_fn("app/rag/generator.py", "Generator.generate"), 8),
        P("If a model is loaded its output is post-processed (\"You have\" is reworded, a disclaimer is appended when missing). Any failure drops to the deterministic text built from the evidence. "
          "In the measured environment the model task silently becomes `text-generation` and the output equals the prompt; because the code treats any non-empty text as success, the failure is not detected."),
        H2("3.7 The chat route and its guards (`app/routes/chat.py`)"),
        CODE(src_fn("app/routes/chat.py", "chat"), 7.5),
        P("The route requires a signed-in user, rejects empty or over-long input, runs the pipeline, stores the consultation for that user only and returns the evidence fields the interface needs. A missing knowledge base returns 503; any other failure returns a generic 500 message without internals."),
    ]


def decision_blocks():
    return [
        H2("4.1 Decisions and reasons"),
        TAB("Implementation decisions", ["Decision", "Reason", "Cost or alternative"],
            [["Hybrid of FAISS and BM25", "Symptom phrases are short; word overlap and meaning both help, and fusion is cheap", "Weights untuned; BM25 alone is nearly as good on this data"],
             ["Cross-encoder rerank on 15 candidates", "Reads query and record together and fixes ordering among close candidates", f"About {F.LAT['stages_ms']['rerank']['mean']:.0f} ms per query on a CPU"],
             ["MiniLM sentence model (384-d)", "Small, fast on CPU, widely used " + c("sbert", "minilm"), "Not medical-domain; a biomedical encoder could do better"],
             ["Flat FAISS index", "176 vectors; exact search costs microseconds", "Would need an approximate index at millions of records"],
             ["Rule-based expansion", "No model or network; deterministic", "Measured no gain; an LLM-based HyDE would cost latency"],
             ["Flan-T5-small with a template fallback", "Runs on a CPU; the fallback guarantees an answer and structural grounding", "Echo defect with transformers 5; template text is repetitive"],
             ["Regex safety rules", "Transparent, instant, clinician-readable", "Blind to paraphrase and negation"],
             ["SQLite + SQLAlchemy", "Zero-setup local storage, per-user rows", "Single-writer; fine for one machine"],
             ["bcrypt and JWT in an httponly cookie", "Slow salted hashing " + c("bcrypt") + "; token not readable by page scripts " + c("jwt"), "Default signing key must be replaced for shared use"],
             ["React + Vite frontend with a proxy", "Single origin for cookies; modern, responsive interface", "Needs Node.js on the machine"],
             ["Local-only processing", "Health text is private; no paid API", "Models must be downloaded once"]],
            widths=[1.6, 2.7, 2.0], align=["l", "l", "l"], size=9),
    ]


# ------------------------------------------------------------------ chapters 9 and 10
def conclusion_blocks():
    s, g, r = F.SAF, F.GEN, F.REL
    return [
        H2("9.1 Summary"),
        P(f"{F.PRODUCT}, implemented as the CareLens AI web application, lets a user describe symptoms in everyday language and returns grounded information about matching conditions. A FastAPI service normalises the text, expands it with a template, "
          f"searches a {F.KB['records']}-record knowledge base with FAISS and BM25, fuses the scores, reranks with a cross-encoder, builds an answer from the retrieved records, applies safety rules and stores the consultation in a private history. "
          "A React interface shows the answer, the evidence cards, the safety banners and the history. The whole system runs on one CPU-only PC."),
        H2("9.2 Objectives achieved and key findings"),
        P("Of the six objectives two are achieved, two are achieved with a stated qualification, one is partly met and one is not met beyond storage."),
        TAB("Objectives against outcomes", ["No.", "Status", "Outcome"],
            [["1", "Achieved (synthetic data)", f"{F.KB['records']} records, {F.KB['conditions']} conditions, FAISS and BM25 indexes"],
             ["2", "Achieved", "Free-text input with a rule-based expansion that gave no measurable benefit"],
             ["3", "Achieved, measured", f"Top-1 {F.pct(_r('hybrid_rerank', S4), 1)} on lay probes, {F.pct(_r('hybrid_rerank', S3), 1)} on two-symptom queries"],
             ["4", "Partly", "Answers built from retrieved records with evidence cards; no per-statement citation; generator echo"],
             ["5", "Not achieved beyond storage", "History saved, searched and deleted; no trends"],
             ["6", "Partly", "Retrieval and speed measured; groundedness checked structurally only"]],
            widths=[0.4, 1.7, 4.2], align=["c", "c", "l"], size=9.5),
        B(f"The retrieval half works: {F.pct(_r('hybrid_rerank', S2), 1)} top-1 on verbatim leave-one-out, {F.pct(_r('hybrid_rerank', S4), 1)} on lay-language probes. The shipped 100% is an upper bound because the held-out record stays in the index.",
          f"BM25 alone is a strong baseline on this synthetic data ({F.pct(_r('bm25', S4), 1)} on lay probes); the cross-encoder adds a little on paraphrase; the HyDE-style template adds nothing measurable.",
          f"Three defects matter for a health tool: the default generator echoes its prompt ({g['echo_answers']} of {g['n']}), the relevance display says 100% even when nothing in the knowledge base matches, and the safety rules missed all {s['by_group_pos']['paraphrase']['n']} paraphrased emergencies.",
          f"Against the base paper {c('base')}, which reports no figures, this project adds BM25 fusion, reranking, safety rules, an application with private history and a measurement; neither work is validated on real clinical data."),
        P(f"The most useful result of the evaluation is a negative one about the original evaluation. The shipped script reports 100% because it searches for records that are still in the index with their own symptom list as the query. "
          f"Once the held-out record is removed the pipeline scores {F.pct(_r('hybrid_rerank', S1L), 1)} on the same queries; with two random symptoms it scores {F.pct(_r('hybrid_rerank', S3), 1)}, "
          f"and a team of four people writing everyday descriptions got {F.pct(_r('hybrid_rerank', S4), 1)}. None of these is a clinical accuracy, because the data are synthetic, but they are honest measures of how robust the retrieval is as queries move away from the stored text."),
        P(f"The ablation also shows where effort pays. The cross-encoder and the embedding model help on paraphrased input, and the TF-IDF fallback keeps the application usable offline ({F.pct(_r('hybrid_tfidf', S4), 1)} on lay probes). "
          f"The HyDE-style template, which the project description lists as a core component, did not improve any set. We kept it in the shipped pipeline and report the result as measured."),
        H2("9.3 Applications and known limitations"),
        P("Applications: a teaching example of a hybrid RAG pipeline with its failure modes visible, a private first-look tool for symptom information once the knowledge base is replaced by reviewed content, and a base for a symptom-tracking product. "
          "Limitations: synthetic knowledge base, near-duplicate evidence, a relative relevance score, a wording-bound safety layer, no symptom trends, no user study. It is a prototype and must not be used for medical decisions."),
        H2("9.4 What the project taught us"),
        B("A health assistant needs its failure modes measured before its accuracy: the missed paraphrased emergencies and the constant 100% matter more than another point of top-1.",
          "A pipeline with fallbacks can fail quietly: the echoing generator was reported as a success by the code, so a check on the output (not only on exceptions) is needed.",
          "A good-looking number needs its protocol read: the shipped 100% was correct arithmetic on a test that could not fail.",
          "Strong, simple baselines (BM25) are worth keeping in the comparison; they show which complexity pays for itself."),
    ]


def future_blocks():
    return [
        P("The future work below follows directly from the measured weaknesses: first repair what exists, then add what the objectives promised and the base paper's gap statement called for, then prepare for real use, and finally evaluate with people."),
        H2("10.1 Improvements to what exists"),
        N("**Repair generation.** Load the T5 model with the sequence-to-sequence classes directly, or pin `transformers` below version 5, and detect an echoed prompt (output equal to input) so the fallback is used; then judge the generated answers.",
          "**Show absolute confidence.** Use the raw cross-encoder score or a calibrated version, add an abstain threshold and say \"no good match\" for out-of-knowledge-base complaints; the raw score already separates the groups in our probes.",
          "**Diversify evidence.** Collapse records of the same condition so the five cards show different conditions, giving a real differential.",
          "**Make the safety layer meaning-aware.** Add negation and history handling, many more paraphrases, a small classifier trained on reviewed examples, and a test set written with clinicians; fix the case-sensitive filter and extend it to drug names.",
          "**Per-statement citations.** Number each statement with its record id so objective 4 is met literally."),
        P("These five items are small in code but large in effect. Repairing generation and the uncertainty display would change what a user sees on every screen, and a meaning-aware safety layer is the precondition for any real use. "
          "Each can be checked with the harness already in the repository by re-running `scripts/measure_metrics.py` and comparing the new numbers with those in Chapter 8."),
        H2("10.2 Additional features"),
        B("A symptom-tracking module for objective 5: structured symptom entries with severity and onset, a timeline, trend charts and a gentle alert when symptoms worsen.",
          "Follow-up questions about duration, severity and age, to narrow ambiguous two-symptom queries.",
          "Multilingual input and output, starting with Telugu and Hindi, using a multilingual encoder.",
          "Export of a consultation summary that a user can hand to a doctor.",
          "An evaluation page that shows the honest metrics of this report instead of the upper-bound figures."),
        P("The tracking module is the most important addition. The base paper's gap statement and objective 5 call for revealing progression and trends, but the application stores each consultation as an isolated free-text event. "
          "A structured symptom log (symptom, severity, onset, date) would let the system draw a timeline, compare the latest entry with earlier ones and retrieve guidance with that context."),
        H2("10.3 Scalability and deployment"),
        B("Replace the synthetic table with reviewed content from licensed or open medical sources, at thousands of records, with an approximate FAISS index and source attribution per record.",
          "Run the API behind a production server with a persistent database, a managed secret key and rate limiting; the Docker files are a start.",
          "Cache the query embedding and reuse the pipeline across workers; consider a quantised or smaller reranker to cut the reranking cost."),
        H2("10.4 Further research"),
        B("A user study with patients and clinicians on trust, comprehension and safety of the answers and escalation messages.",
          "A benchmark of symptom-description queries with expert-labelled conditions, to measure accuracy honestly and to compare retrieval-augmented and plain-model assistants " + c("medrag", "medpalm") + ".",
          "Study of hallucination and refusal behaviour when a generator is actually working " + c("halluc") + ", and of fairness across languages and demographic descriptions."),
    ]


def chapter9_blocks():
    return [H1("CHAPTER 9: CONCLUSION")] + conclusion_blocks()


def chapter10_blocks():
    return [H1("CHAPTER 10: FUTURE SCOPE")] + future_blocks()
