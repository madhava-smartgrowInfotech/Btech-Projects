"""Chapter 6: Methodology and Software Implementation (SymptoTrackAI, implemented as CareLens AI).

methodology_blocks() feeds 9.METHODOLOGY..., application_blocks() feeds 12.DESIGN & IMPLEMENTATION, blocks() is the report chapter.
"""

import ast
import os

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def _fn(rel, name):
    """Exact source text of a top-level function or of a method (Class.method) read from the repository."""
    path = os.path.join(F.CODE, rel)
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    tree = ast.parse(text)
    want = name.split(".")
    nodes = tree.body
    node = None
    for part in want:
        node = next(n for n in nodes if getattr(n, "name", None) == part)
        nodes = getattr(node, "body", [])
    return "\n".join(lines[node.lineno - 1:node.end_lineno])


def _lines(rel, a, b):
    path = os.path.join(F.CODE, rel)
    return "\n".join(open(path, encoding="utf-8").read().splitlines()[a - 1:b])


S1, S2, S3, S4 = "S1_leave_one_out_30", "S2_verbatim_leave_one_out_176", "S3_two_symptoms_leave_one_out_176", "S4_lay_language_60"
SP = "S1_shipped_protocol_30"


def methodology_blocks():
    n_gen = 30 * 6
    removed = n_gen - F.KB["records"]
    L = F.REPORT
    b = [
        H2("6.1 Overall Methodology"),
        P(f"SymptoTrackAI, implemented as the {F.APP_NAME} web application, answers a symptom description in everyday language with information retrieved from a medical knowledge base. "
          f"The methodology follows the retrieval-augmented generation idea [{R['rag']}], in which a language model's answer is conditioned on passages fetched from a document store instead of on its own memory, "
          f"because ungrounded models can produce fluent but wrong statements [{R['halluc']}], which is unacceptable for health information. The base paper [{R['base']}] applies this idea with FAISS similarity search and a "
          "sentence-transformer over a symptom-disease knowledge base, and keeps each consultation for later review. This project keeps that skeleton and extends the retrieval stage in the way "
          "the title promises: lexical search is added to dense search, a query-expansion step precedes retrieval, a neural reranker follows it, and a rule-based safety layer surrounds the answer."),
        P("The method has seven steps, executed for every message. (1) The text is **normalised** and a **hypothetical description** is built around it (query expansion). (2) The combined text is **embedded** with a sentence-transformer. "
          "(3) The embedding is searched in a **FAISS** index and the same text is searched with **BM25**, each returning fifteen candidates. (4) The two score lists are **min-max normalised and fused** with weights 0.65 and 0.35. "
          "(5) A **cross-encoder** rescores the fused candidates and the best five are kept; their scores are rescaled to a 0 to 1 relevance. (6) The original message is checked by a **rule layer** for emergency or caution wording, "
          "a **generator** composes the answer from the five records, and a **filter** removes listed medication phrases. (7) The question, answer and evidence are **stored** for the signed-in user."),
        P("The pre-trained models are used as they are. **No model was trained or fine-tuned in this project**, so there are no training curves, no training and validation split, and no training hyper-parameters; "
          "what is tuned by hand is the retrieval configuration (candidate pool, fusion weights, number of records shown). The experimental method is therefore an evaluation of the pipeline: "
          "the knowledge base is the retrieval corpus, queries are the test cases, and the correct answer is the condition of the record that the query was written from (Section 6.2.3)."),
        H2("6.2 Knowledge Base and Evaluation Data"),
        H3("6.2.1 Construction of the knowledge base"),
        P(f"The knowledge base is built by scripts/prepare_data.py. The script contains a hand-written table of {F.KB['conditions']} common conditions (for example Common Cold, Influenza, Dengue, Pneumonia, Appendicitis, Stroke and Heart Attack), "
          "each with a list of typical symptoms, a one-sentence description, a self-care and when-to-seek-care text, a severity level and a list of red-flag signs. For every condition the script generates up to six records, "
          "each a random subset of three to five of its symptoms (the random generator is seeded with 42), and drops records whose condition and symptom list are identical to an earlier one. "
          f"{n_gen} records were generated and {removed} duplicates removed, leaving **{F.KB['records']} records**. Each record carries the canonical retrieval text 'Disease: ... Symptoms: ... Description: ... Guidance: ...'."),
        P("**The knowledge base is synthetic.** It was written by the project team from general knowledge, was not taken from a clinical source and has not been reviewed by a clinician; every record is labelled source_type = synthetic, "
          "and the interface says so on the About page. The same pipeline accepts a downloaded symptom-disease table in the same columns, but no public dataset was used in this work, so no dataset licence applies. "
          f"Because the description and guidance are shared by all records of a condition, there are only {F.KB['distinct_description_guidance_pairs']} distinct description and guidance pairs in {F.KB['records']} records, "
          f"and the symptom vocabulary is {F.KB['symptom_vocabulary']} distinct phrases with {F.KB['mean_symptoms_per_record']} symptoms per record on average."),
        TAB("Knowledge-base facts", ["Item", "Value"], [
            ["Records / conditions", f"{F.KB['records']} / {F.KB['conditions']} (4 to 6 records per condition)"],
            ["Severity labels", ", ".join(f"{k} {v}" for k, v in F.KB["severity"].items())],
            ["Symptoms per record", f"{F.KB['mean_symptoms_per_record']} on average (range {F.KB['min_symptoms']} to {F.KB['max_symptoms']})"],
            ["Distinct symptom phrases", str(F.KB["symptom_vocabulary"])],
            ["Distinct description and guidance pairs", f"{F.KB['distinct_description_guidance_pairs']} (one per condition)"],
            ["Source", "Written by the team; source_type = synthetic; not clinically reviewed"],
            ["Index", f"FAISS flat inner-product index, {F.KB['embedding_dim']} dimensions, plus a BM25 corpus"],
        ], widths=[2.2, 4.1], size=10, align=["l", "l"]),
        FIG(F.fig("f07_kb_composition.png"), "Composition of the knowledge base: records per condition and severity labels.", 5.6),
        H3("6.2.2 Preprocessing"),
        P("Preprocessing happens in two places. When the knowledge base is built, symptom phrases are lower-cased, whitespace is collapsed and repeated symptoms inside a record are removed. "
          "At query time normalize_query lower-cases the message, collapses whitespace, turns '?', '!' and ';' into full stops and truncates to 2000 characters. expand_query_hyde then splits the normalised text on commas, full stops, "
          "' and ' and ' with ' into at most eight fragments and builds the hypothetical description. Both functions are quoted below exactly as they are in the code."),
        CODE(_fn("app/rag/query_expansion.py", "normalize_query") + "\n\n" + _fn("app/rag/query_expansion.py", "expand_query_hyde"), 8),
        P(f"The expansion is a **template**, not a second language model: it wraps the symptom fragments in a fixed sentence about 'medical symptom presentation'. The idea comes from HyDE [{R['hyde']}], where a language model writes a "
          "hypothetical answer document and the retriever searches with that document instead of the short question. Writing the document with a model would add a generation step to every query, so the project uses a "
          "deterministic stand-in, and the experiments in Chapter 8 test whether it helps."),
        H3("6.2.3 Evaluation query sets"),
        P("Because nothing is trained, the evaluation needs only queries with known answers. Four query sets were used; all are small, all are for the bundled synthetic knowledge base, and none was reviewed by a clinician."),
        TAB("Evaluation query sets", ["Set", "Queries", "How they were made", "What they test"], [
            ["S1", str(F.RET["bm25"][SP]["n"]), "One random record per condition (the protocol of scripts/evaluate.py, seed 7); the query is 'I have' plus the record's symptoms", "Wiring. Shipped protocol leaves the record in the index; leave-one-out removes it"],
            ["S2", str(F.RET["bm25"][S2]["n"]), "Every record in turn, same wording, record removed from the index", "Retrieval from sibling records"],
            ["S3", str(F.RET["bm25"][S3]["n"]), "Every record in turn, two randomly chosen symptoms only (seed 11), record removed", "Short, ambiguous queries"],
            ["S4", str(F.RET["bm25"][S4]["n"]), "Two everyday-language descriptions per condition written by the authors (scripts/probe_data.py)", "Paraphrase and word choice not in the knowledge base"],
        ], widths=[0.5, 0.7, 3.2, 1.9], size=9.5, align=["c", "c", "l", "l"]),
        P(f"For each query the system's answer is the condition of its top-ranked record, and it is counted correct when it equals the condition the query was written for. Two further probe sets test parts of the system other than retrieval: "
          f"{F.REL['out_kb_n']} complaints that no condition in the knowledge base covers, and {F.SAF['n_pos']} emergency descriptions with {F.SAF['n_neg']} non-emergency texts for the safety rules (Chapter 7)."),
    ]
    b += [
        H2("6.3 Algorithms and the Reasons for Choosing Them"),
        H3("6.3.1 Dense retrieval: sentence embeddings and FAISS"),
        P(f"Symptom descriptions are matched to records by meaning, so that 'my chest feels tight' can retrieve a record that says 'chest tightness'. The encoder is all-MiniLM-L6-v2, a six-layer Sentence-BERT model [{R['sbert']}] "
          f"built on the compact MiniLM transformer [{R['minilm']}] that maps a text to a {F.KB['embedding_dim']}-dimensional unit vector. It was chosen because it is small (about 22 million parameters), fast on a CPU and widely used for semantic search. "
          f"With unit vectors the inner product equals the cosine similarity, so the index is a FAISS IndexFlatIP [{R['faiss']}], an exact search that compares the query with all {F.KB['records']} vectors. For a base of this size an approximate index would add "
          "complexity and error for no speed benefit. Dense retrieval follows the dual-encoder approach of dense passage retrieval [" + str(R['dpr']) + "]."),
        EQ("sim(q, d) = (q · d) / (‖q‖ ‖d‖) = q · d     for unit vectors q and d"),
        H3("6.3.2 Lexical retrieval: BM25"),
        P(f"Symptom words are short and exact, and a dense model can blur them. BM25 [{R['bm25']}], a probabilistic extension of TF-IDF [{R['irbook']}], rewards records that "
          "contain the query's words, weights rare words more and normalises for record length. The implementation is rank_bm25's BM25Okapi with its default constants (k1 = 1.5, b = 0.75) over lower-case alphanumeric tokens of the retrieval text."),
        EQ("BM25(q, d) = Σ over terms t in q of  IDF(t) · f(t,d)·(k1 + 1) / ( f(t,d) + k1·(1 − b + b·|d| / avgdl) )"),
        H3("6.3.3 Score fusion"),
        P("The two retrievers return scores on different scales (cosine values between about 0 and 1, BM25 values that are unbounded), so each list is rescaled to the interval from 0 to 1 by min-max normalisation before the weighted sum. "
          "A record that only one retriever returned receives the score 0 from the other. The weights are 0.65 for the dense score and 0.35 for the lexical score; they are the project's initial choice and were not tuned. "
          f"Rank-based fusion [{R['rrf']}] is an alternative that needs no weights; it was not tried."),
        EQ("ŝ(i) = (s(i) − min s) / (max s − min s)      h(i) = 0.65 · ŝ_dense(i) + 0.35 · ŝ_lex(i)"),
        CODE(_fn("app/rag/hybrid_retriever.py", "fuse"), 8),
        H3("6.3.4 Reranking with a cross-encoder"),
        P(f"A bi-encoder embeds the query and the record separately, so it cannot see how the two words interact. A cross-encoder reads them together and outputs one relevance score, which is more precise but too slow to run on the whole base [{R['monobert']}]. "
          f"The standard design, used here, is to let the cheap retrievers pick fifteen candidates and let the cross-encoder reorder them. The model is cross-encoder/ms-marco-MiniLM-L-6-v2, trained on the MS MARCO passage-ranking data [{R['msmarco']}]; "
          "it is a general web-search reranker and has not been adapted to medical text. It scores fifteen (query, record text) pairs per request, and the best five are returned."),
        H3("6.3.5 Relevance display"),
        P("To give the user a simple bar, the cross-encoder scores of the candidates are rescaled by min-max to the interval from 0 to 1 and shown as a percentage; 0.66 and above is labelled 'Strong match', 0.33 and above 'Moderate match' and "
          "anything lower 'Weak match'. The code is quoted below. **Because the rescaling uses the minimum and maximum of the same list, the best candidate always receives exactly 1.0**, whatever the raw scores were; "
          "the display therefore says how a record compares with the other candidates of the same query and nothing about how well the query is covered by the knowledge base. Chapter 8 measures the consequence."),
        EQ("ρ(i) = (r(i) − min r) / (max r − min r),   r(i) = CrossEncoder(q, d_i);   label = Strong if ρ ≥ 0.66, Moderate if ρ ≥ 0.33, else Weak"),
        CODE(_fn("app/rag/reranker.py", "Reranker.rerank"), 7.5),
        H3("6.3.6 Grounded generation and its fallback"),
        P(f"The generator receives the normalised message and the five records as numbered context and is instructed to answer only from that context, avoid a definitive diagnosis, avoid prescribing medication and mention uncertainty. "
          f"The model is Flan-T5-small, an instruction-tuned encoder-decoder with about 77 million parameters [{R['flan']}], run on the CPU with greedy decoding and at most 220 new tokens; a small model was chosen so that the system runs on an ordinary laptop. "
          "After generation, the text 'You have ' is replaced by a neutral phrase and a sentence stating that the output is not a diagnosis is appended if it is missing."),
        P("If the model cannot be loaded or fails, fallback_answer composes the answer deterministically: it names the condition of the best record, lists the five records with their symptoms, concatenates the guidance texts of the first three, "
          "and ends with the warning and the disclaimer. Every condition and every symptom in this text comes from a retrieved record, so it cannot state anything outside the evidence; the price is that it is repetitive. "
          "**In the tested environment the model path did not produce an answer**: the installed Transformers 5.20 no longer provides the text2text-generation task, the loader falls back to text-generation, and for a T5 model that task returns the "
          f"prompt unchanged. In {F.GEN['echo_answers']} of {F.GEN['n']} test queries the 'answer' was the instruction and the retrieved context, labelled with the generator's name (Chapter 8 shows the screen). The fallback path is the one that gives a usable answer."),
        CODE(_fn("app/rag/generator.py", "Generator.generate"), 7.5),
        H3("6.3.7 Safety rules"),
        P("The safety layer is a list of ten regular expressions, each with a one-sentence advice: severe chest pain or chest pressure, difficulty breathing, severe bleeding, loss of consciousness, stroke-like signs, severe allergic reaction, "
          "self-harm, sudden severe neurological symptoms, seizures and severe abdominal pain. A match returns the flag 'emergency' with an urgent-care message that includes the disclaimer. If none matches, six keywords (chest pain, breathing, bleeding, pregnant, infant, newborn) return 'caution'; "
          "otherwise the flag is 'routine'. The rules look at the user's message, not at the retrieved records, so they work even when retrieval fails. They are literal patterns: they do not understand negation, history or paraphrase "
          "(Chapter 7 measures this). The answer filter then replaces five phrases (take ibuprofen, take antibiotics, dosage, prescribe, mg twice daily) with a marker."),
        CODE(_fn("app/rag/safety.py", "check_safety"), 7.5),
        H2("6.4 Mathematical Formulation of the Evaluation"),
        P(f"For n queries, let rank_i be the position of the first record whose condition equals the correct one in the returned list (infinite if absent). Top-k accuracy is the share of queries with rank_i ≤ k and the mean reciprocal rank at 5 is the mean of 1/rank_i over rank_i ≤ 5 "
          f"(0 otherwise). Because a condition has four to six records, the first three records often belong to one condition, so Top-3 over records is almost the same as Top-1 and the tables also give the mean number of distinct conditions in the five evidence cards. "
          f"Since every set is small, Top-1 accuracy is reported with the Wilson score interval [{R['wilson']}] at 95% confidence, and the separation of in-base and out-of-base queries by a score is summarised by the area under the ROC curve [{R['sklearn']}]."),
        EQ("Top-k = (1/n) Σ 1[rank_i ≤ k]        MRR@5 = (1/n) Σ 1/rank_i  (rank_i ≤ 5)"),
        EQ("Wilson 95% interval = ( p̂ + z²/2n ± z·√( p̂(1 − p̂)/n + z²/4n² ) ) / ( 1 + z²/n ),   z = 1.96"),
    ]
    if True:
        b += [H2("6.5 Retrieval Configuration"),
              TAB("Retrieval configuration (app/config.py)", ["Parameter", "Value"], [
                  ["Embedding model", F.ENV["embedding_model"]], ["Reranker", F.ENV["reranker_model"]], ["Generator", F.ENV["generator_model"]],
                  ["Candidate pool per retriever", str(F.CANDIDATE_K)], ["Records returned", str(F.TOP_K)], ["Fusion weights (dense, lexical)", f"{F.FUSION_WEIGHTS[0]}, {F.FUSION_WEIGHTS[1]}"],
                  ["Maximum message length", "2000 characters (minimum 3)"], ["Token lifetime", "1440 minutes"]], widths=[2.6, 3.7], size=10, align=["l", "l"])]
    return b


def application_blocks():
    cfg = TAB("Configuration of the pipeline (app/config.py; each value can be overridden by a CARELENS_* environment variable)", ["Parameter", "Value"], [
        ["Embedding model", F.ENV["embedding_model"]], ["Reranker", F.ENV["reranker_model"]], ["Generator", F.ENV["generator_model"]],
        ["Candidate pool per retriever / records returned", f"{F.CANDIDATE_K} / {F.TOP_K}"], ["Fusion weights (dense, lexical)", f"{F.FUSION_WEIGHTS[0]}, {F.FUSION_WEIGHTS[1]}"],
        ["Message length", "3 to 2000 characters"], ["Token lifetime", "1440 minutes (24 h)"], ["Database", "data/carelens.db (SQLite)"]], widths=[2.9, 3.4], size=10, align=["l", "l"])
    api = TAB("API endpoints", ["Method and path", "Auth", "Request", "Success response", "Errors"], [
        ["GET /api/health", "no", "-", "{status, product}", "-"],
        ["POST /api/auth/register", "no", "{email, password 6-128}", "{email, token} + cookie", "400 e-mail exists; 422"],
        ["POST /api/auth/login", "no", "{email, password}", "{email, token} + cookie", "401 invalid; 422"],
        ["POST /api/auth/logout", "no", "-", "{ok}, cookie cleared", "-"],
        ["GET /api/auth/me", "cookie", "-", "{email, id}", "401"],
        ["POST /api/chat", "yes", "{query 3-2000}", "{answer, top_condition, evidence[5], safety_flag, safety_message, relevance_label, consultation_id, created_at, generated_by}", "400 blank; 401; 422; 503 knowledge base missing; 500"],
        ["GET /api/history?search=", "yes", "optional search text", "list of up to 200 consultations, newest first", "401"],
        ["GET /api/history/{id}", "yes", "-", "one consultation", "401; 404 not found or not yours"],
        ["DELETE /api/history/{id}", "yes", "-", "{ok}", "401; 404"],
        ["GET /api/about/metrics", "no", "-", "stored metrics + kb_records, kb_conditions, data_source", "404 metrics file missing"],
    ], widths=[1.5, 0.5, 1.1, 2.1, 1.1], size=8.5, align=["l", "c", "l", "l", "l"])
    b = [
        H2("6.5 Application Architecture and Implementation"),
        P(f"The backend is a FastAPI application served by Uvicorn on port {F.API_PORT}. At start-up it creates the tables and the demo user; it does not load any model. The first call to POST /api/chat creates the Pipeline "
          f"singleton, which loads the sentence-transformer, the cross-encoder and the generator and the two indexes; in the measurement environment this took about 62 seconds, and later requests reuse the loaded objects. "
          "If the index files are missing the Pipeline rebuilds them from the knowledge base before it answers. Every route obtains a database session from the get_db dependency and closes it after the response."),
        P(f"The frontend is a React application served by Vite on port {F.WEB_PORT}. State is kept in components and in one authentication context; there is no global store. The API client lib/api.js adds credentials to every request, "
          "converts network failures and error responses into an ApiError with a readable message, and fires an 'unauthorized' event on a 401 so that an expired session sends the user to the sign-in page. "
          "The Vite server proxies every /api path to the backend, so the browser sees one origin and the cookie works without cross-origin configuration; in Docker the same job is done by an nginx container."),
        P("Four details of the interface code are worth recording. The authentication context keeps a small hint in browser storage that records whether a session may exist, because the session cookie is httponly and cannot be read by the page; "
          "without the hint the application would call /api/auth/me on every first visit and log an expected 401. The assistant page keeps the conversation in component state, aborts an unfinished request when the user leaves the page, and shows a toast with the consultation number when an answer is saved. "
          "The history page sends the search text to the server after a delay of 300 ms, so a request is not made for every keystroke, and asks for confirmation before it deletes. Every page sets its own document title, and every list has a loading, an empty and an error state."),
        TAB("Main software components and versions in the measurement environment", ["Component", "Version", "Used for"], [
            ["Python", F.ENV["python"], "Backend and scripts"],
            ["FastAPI / SQLAlchemy", f"{F.ENV['fastapi']} / {F.ENV['sqlalchemy']}", "API and database access"],
            ["PyTorch (CPU) / Transformers", f"{F.ENV['torch']} / {F.ENV['transformers']}", "Model execution; the Transformers version removed the task the generator needs"],
            ["sentence-transformers / FAISS", f"{F.ENV['sentence_transformers']} / {F.ENV['faiss']}", "Embeddings and cross-encoder; vector index"],
            ["scikit-learn", F.ENV["scikit_learn"], "TF-IDF fallback and evaluation metrics"],
            ["React / Vite", "19 / 8 (package.json)", "Single-page application and dev server"],
        ], widths=[2.0, 1.8, 2.5], size=9.5, align=["l", "l", "l"]),
        H2("6.6 API Design"),
        P("The API is JSON over HTTP. Errors always have the form {detail: message}; validation errors from Pydantic return 422 with a list of messages that the client joins into one sentence. "
          "Sign-in is by an httponly cookie named carelens_token; an Authorization: Bearer header is also accepted, which the tests use."),
        api,
        P("A 404 rather than a 403 is returned when a consultation exists but belongs to another user, so that the existence of other users' records is not revealed."),
        H2("6.7 Security and Error Handling"),
        P(f"Passwords are hashed with bcrypt [{R['bcrypt']}] with a random salt before storage, and verification catches malformed hashes and returns false. A successful sign-in creates a JSON Web Token [{R['jwt']}] signed with HMAC-SHA256 that holds the user id, the e-mail and an expiry "
          "after 1440 minutes, and sets it as an httponly cookie with SameSite=lax. Every history route filters on the user id of the token, and a message is accepted only between 3 and 2000 characters. "
          "The chat route separates three failure causes: a missing knowledge base returns 503 with the name of the missing file, any other pipeline error returns 500 with a generic message and prints the detail to the server log, "
          "and a failure while saving returns 500 after a rollback. The interface turns each of these into a message in the conversation with a retry button."),
        P("Three weaknesses are known and are tested in Chapter 7: the signing key has a built-in default value, 'carelens-local-dev-secret-change-me', that is used unless CARELENS_SECRET_KEY is set; the cookie has no Secure flag, which "
          "matters when the application is served over HTTPS; and there is no limit on failed sign-in attempts. The registration route also reveals whether an e-mail is already registered. "
          "The application was designed for one machine and is not hardened for a public deployment."),
        H2("6.8 Installation and Execution"),
        P(f"The project runs on Windows with Python 3.10 or newer and Node.js 18 or newer. The simplest way is to double-click run.bat in the project folder. The launcher reads the ports from .env (backend {F.API_PORT}, frontend {F.WEB_PORT}), "
          "creates a virtual environment if there is none, installs the Python requirements, prepares the knowledge base and the index when they are missing, installs the frontend packages, seeds the demo account, opens two server windows (CareLens API and CareLens Web) "
          f"and opens the browser at http://localhost:{F.WEB_PORT}. The first start downloads the three models from Hugging Face and takes longer; later starts need only the time to load the models at the first message."),
        B(f"**Demo login:** {F.DEMO_LOGIN[0]} / {F.DEMO_LOGIN[1]}; the account is created automatically and has sample consultations.",
          "**Docker:** docker compose up --build builds the React app, runs the API container and an nginx container on the same ports.",
          "**Manual:** python -m venv .venv; pip install -r requirements.txt; python scripts/prepare_data.py; python scripts/build_index.py; python scripts/seed_demo.py; python -m uvicorn app.main:app --port 8412; then npm install and npm run dev in frontend/.",
          "**Checks:** python -m pytest tests (unit and API tests), python scripts/smoke_test.py (end-to-end through the web port) and python scripts/capture_screens.py (screenshots).",
          "**Offline mode:** if a model cannot be downloaded the application falls back to TF-IDF retrieval and evidence-based answers and continues to work."),
    ]
    if not F.REPORT:
        b.insert(1, cfg)
    return b


def blocks():
    b = [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")]
    b += methodology_blocks()
    b += application_blocks()
    return b
