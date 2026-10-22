"""Index of the SymptoTrackAI (CareLens AI) design diagrams: (key, title, file, caption, explanatory paragraph).

The files are written by scripts/docs_build/make_diagrams.py (and diagrams_more.py, diagrams_dfd_uml.py) into docs/diagrams/.
Used by the block-diagram document and the full report.
"""

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "Four-tier architecture of SymptoTrackAI (CareLens AI): React web app, FastAPI application, RAG components and local data stores.",
     "The browser tier is a React and Vite single-page application on port 5412 whose pages (landing, login, register, assistant, history, consultation detail, about) talk to the API only through JSON; the Vite dev server proxies /api to port 8412. "
     "The FastAPI tier groups its routes into auth, chat, history, about and the legacy page router, and protects every private route with the require_user dependency. "
     "Behind it, the Pipeline object in app/rag is created once on the first chat request and holds the embedding backend, the FAISS and BM25 stores, the cross-encoder, the generator and the safety rules. "
     "All data stay on the machine: SQLite holds the users and consultations tables, the knowledge base and its three index files sit in data/, and the evaluation file is read by the About page. "
     "The only network use is the one-time download of the model weights from the Hugging Face Hub."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "High-level workflow of one consultation, from sign-in to the saved answer.",
     "A signed-in user types symptoms in everyday language; the request is accepted when it has between 3 and 2000 characters. "
     "The text is normalised and extended with a fixed hypothetical-description template, then searched twice, semantically with MiniLM vectors in FAISS and lexically with BM25, fifteen hits each. "
     "The two score lists are fused with weights 0.65 and 0.35 and the fifteen candidates are reranked by the cross-encoder, leaving five records. "
     "The safety rules inspect the raw text, the generator writes the answer from the five records, a filter removes listed medication phrases, and the result is saved as a consultation row and shown with a banner and evidence cards. "
     "Each model has a fallback (TF-IDF vectors, hybrid order, evidence-based text), so the flow still completes when a model cannot be loaded."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Context diagram (DFD level 0) of SymptoTrackAI with its user and the model hub.",
     "At level 0 the whole system is one process. The user sends registration details, credentials, symptom text, history searches and delete requests, and receives the answer, the evidence cards, the safety banner, the stored history and the metrics page. "
     "The only external entity besides the user is the Hugging Face Hub, which supplies the embedding, reranker and generator weights on the first run. "
     "The knowledge base, the index files and the evaluation metrics are local files and need no external actor. "
     "Accounts and consultations are kept in the local SQLite database."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "DFD level 1 of SymptoTrackAI: seven processes and four data stores.",
     "Level 1 splits the system into authentication (1.0), evidence retrieval (2.0), answer generation and safety screening (3.0), consultation storage (4.0), history management (5.0), metrics reporting (6.0) and the offline knowledge-base build (7.0). "
     "Process 1.0 reads and writes the users table and tells the other private processes which user the session belongs to. "
     "Process 2.0 reads the knowledge base and indexes (D2) and hands five records to 3.0, whose answer goes back to the user and to 4.0, which writes the consultations table (D3). "
     "Process 5.0 reads and deletes rows of D3 for the signed-in user only, and 6.0 reads the stored metrics file (D4). "
     "Process 7.0 is run by the developer scripts prepare_data.py and build_index.py and only writes D2."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "DFD level 2 of SymptoTrackAI: expansion of the retrieval, generation and safety processes of Pipeline.answer.",
     "Level 2 follows Pipeline.answer step by step. The query is normalised and extended (2.1), embedded (2.2) and searched in the FAISS index (2.3), while the same combined text is used as the BM25 query (2.4). "
     "The fifteen semantic and fifteen lexical hits are fused with min-max normalised scores (2.5) and the fifteen candidates are rescored by the cross-encoder (2.6), which returns five records with a relative relevance. "
     "The generator (3.1) writes the answer from those records and the normalised query, and the safety stage (3.2) checks the raw query, filters the answer and prepends the emergency message when needed. "
     "The output is one result dictionary that is passed to process 4.0 for storage."),
    ("uml", "UML class diagram", "06_uml_class.png",
     "UML class diagram of SymptoTrackAI showing the ORM tables, the request schemas, the API routers and the RAG classes.",
     "The two ORM classes, User and Consultation, map to the SQLite tables and are linked one to many; the Pydantic schemas validate registration, login and chat requests. "
     "The routers in app/routes use SQLAlchemy to read and write those tables, call the auth module for password hashing and JWT tokens, and call get_pipeline().answer() for every chat request. "
     "Pipeline owns one EmbeddingBackend, one FaissStore, one BM25Store, one Reranker and one Generator, and calls the query_expansion, hybrid_retriever and safety modules, with weights, model names and limits read from Settings. "
     "EmbeddingBackend, Reranker and Generator each carry a flag or a mode that records whether the model loaded, which is how the fallbacks are chosen."),
    ("seq", "Sequence diagram of a consultation", "07_sequence_chat.png",
     "Sequence diagram of POST /api/chat from the browser to the saved consultation.",
     "The browser posts the query with its httponly cookie; the chat router runs the require_user dependency, which decodes the JWT and loads the user row from SQLite and answers 401 when either step fails. "
     "After a length check the router asks the Pipeline for an answer: the Pipeline expands the query, has the embedding backend, FAISS and BM25 return their hits, fuses them, and asks the Reranker for the top five. "
     "It then calls the safety rules on the raw query, the Generator for the answer and the safety filter for the final text, prepends the emergency message when the flag requires it and returns one result dictionary. "
     "The router inserts the consultation row with the evidence as JSON, and the browser receives the answer, evidence, safety flag and consultation id."),
    ("uc", "Use-case diagram", "08_use_case.png",
     "Use-case diagram of SymptoTrackAI with the visitor, the registered user and the local models.",
     "A visitor can open the landing page, register and sign in, using either an own account or the demo account. "
     "A signed-in user can describe symptoms, read the grounded answer with its evidence cards, see the emergency or caution banner, view recent consultations, search the history, open a consultation and delete it. "
     "The About page with the measured metrics and the sign-out and theme controls are also available after sign-in. "
     "The local models are a system actor included by the answering use case; every use case from UC4 onward requires a valid session cookie."),
    ("er", "Entity-relationship diagram", "09_er_diagram.png",
     "Entity-relationship diagram: the users and consultations tables and the file-based knowledge base.",
     "The database has two tables. users stores a unique email and a bcrypt password hash; consultations stores the query, the generated response, the top condition, the retrieved evidence as a JSON text, the retrieval score, the safety flag and a timestamp, and carries a foreign key to users. "
     "One user has many consultations and deleting a user cascades to them. "
     "The knowledge base is not in the database: it is a JSON and CSV file of 176 records with ten fields each, indexed into faiss.index, records.json and bm25.json under data/index. "
     "Because consultations keep a JSON copy of the five matched records, a stored consultation stays readable even if the knowledge base changes."),
    ("flowchart", "Flowchart of the core algorithm", "10_flowchart_retrieval.png",
     "Flowchart of the hybrid retrieval and reranking algorithm in Pipeline.answer.",
     "The raw query is lower-cased, split into at most eight fragments and wrapped in a fixed hypothetical-description sentence to give the combined text. "
     "That text is embedded with all-MiniLM-L6-v2 and searched in the flat inner-product FAISS index, and it is also tokenised for BM25; each search returns fifteen records. "
     "The scores of each list are min-max normalised over the union of hits and mixed as 0.65 times the semantic and 0.35 times the lexical score. "
     "The cross-encoder then scores each (query, record) pair, the scores are rescaled to 0 to 1 over the fifteen candidates, and the top five become the evidence cards. "
     "Because of that rescaling the top record always shows a relevance of 1.00, which is why the label is relative and not a probability."),
    ("safety", "Safety decision flow", "11_safety_decision_flow.png",
     "Decision flow of the rule-based safety layer and the answer filter.",
     "The lower-cased query is tested against ten regular-expression rules for emergencies such as severe chest pain, breathing difficulty, severe bleeding, loss of consciousness, stroke-like signs, anaphylaxis, self-harm, sudden neurological symptoms, seizures and severe abdominal pain. "
     "A match sets the flag to emergency with the advice of that rule; otherwise six caution keywords set the flag to caution, and anything else is routine with the permanent disclaimer. "
     "Independently of the flag, the generated answer passes through a filter that replaces five listed medication phrases, and for an emergency the message is prepended to the answer. "
     "The rules match wording, not meaning, so paraphrased emergencies and negated or historical mentions are not handled correctly, as the measurements in the results chapter show."),
]
