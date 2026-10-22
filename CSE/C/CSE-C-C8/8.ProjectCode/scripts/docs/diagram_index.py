"""Index of the PeerScope design diagrams: (key, title, file, caption, explanatory paragraph).

The files are written by scripts/docs_build/make_diagrams.py and diagrams_more.py into docs/diagrams/.
Used by the block-diagram document and the full report (same tuple shape as the previous ch5.DIAGRAMS).
"""

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "Four-tier architecture of PeerScope: React web app, FastAPI application, Python services and local data stores.",
     "The browser tier is a React and Vite single-page application on port 5408 that talks to the API only through JSON and one multipart PDF upload. "
     "The FastAPI tier on port 8408 exposes the health, model, reviewer-directory and analysis routes and applies the upload guards. "
     "Behind it, pipeline.run_analysis calls the service modules for PDF extraction, structural features, the decision signal, the review, literature retrieval, embeddings and matching. "
     "Data stay on the machine in SQLite, the model files, the training CSV and the Hugging Face cache; only the title query to OpenAlex leaves it."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "High-level workflow of PeerScope for one POST /api/analyze request.",
     "A request passes through ten stages. The PDF is validated, its text, title, sections and references are extracted, structural features are computed and the trained classifier gives a decision signal. "
     "A review is then drafted by the local Qwen model, or by the deterministic rules when the model cannot load, related literature is fetched from OpenAlex, and reviewers are scored. "
     "The assembled result is stored as a row in the analyses table and shown in the dashboard tabs or exported as JSON or PDF. "
     "The two degradation paths, an unavailable model and an unreachable OpenAlex service, leave the rest of the result intact."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Context diagram (DFD level 0) of PeerScope with its two users and one external service.",
     "At level 0 the whole system is a single process. The editor or programme chair sends a paper PDF with filters and receives the preliminary assessment, the ranked reviewers, the stored history and JSON or PDF exports. "
     "The directory administrator sends reviewer profiles or a CSV file and receives the directory and its CSV export. "
     "The only external system is the OpenAlex public API, which receives a title or keyword query and returns related works. "
     "Model metrics are read from local files and need no external actor."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "DFD level 1 of PeerScope: seven processes and three data stores.",
     "Level 1 splits the system into validation and extraction (1.0), assessment (2.0), literature retrieval (3.0), reviewer matching (4.0), storing and exporting results (6.0), directory management (5.0) and the model-performance report (7.0). "
     "Process 2.0 passes keywords, methods and topics to matching and its assessment to process 6.0, which writes the analyses table. "
     "Process 4.0 reads reviewer profiles from the reviewers table, and process 7.0 reads the stored metrics. "
     "Three data stores appear: the model files, the reviewers table and the analyses table."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "DFD level 2 of PeerScope: expansion of the analysis pipeline into eight sub-processes.",
     "Level 2 follows pipeline.run_analysis. Page text is extracted (1.1), the title, sections and references are detected (1.2) and structural features are computed (2.1). "
     "The decision signal (2.2) reads the saved model files, and the review (2.3) optionally reads the local Qwen weights. "
     "Literature retrieval (3.1) exchanges a query and works with OpenAlex, while profile building and embedding (4.1) and scoring and ranking (4.2) read the reviewers table. "
     "Each stage adds its output to one result dictionary that is handed to process 6.0."),
    ("uml", "UML class diagram", "06_uml_class.png",
     "UML class diagram of PeerScope showing the ORM tables, the request schema, the FastAPI application and the service modules.",
     "The two ORM classes, Reviewer and Analysis, map to the SQLite tables, and ReviewerIn is the Pydantic schema that validates reviewer input. "
     "The FastAPI application calls the Pipeline, which uses the PdfExtractor, FeatureExtractor, MLPredictor, ReviewSynthesis, LiteratureService and MatchingService modules. "
     "ReviewSynthesis optionally uses LLMService, and both LiteratureService and MatchingService depend on EmbeddingService. "
     "The service modules are written as functions in Python modules; they are drawn as classes to show their responsibilities."),
    ("seq", "Sequence diagram of an analysis", "07_sequence_analyze.png",
     "Sequence diagram of a paper analysis, from the browser upload to the stored JSON response.",
     "The browser posts the PDF. FastAPI checks the extension, content type, size and PDF header, writes a temporary file and loads the reviewer rows. "
     "It then calls run_analysis, which extracts the document and features, asks the classifier for the decision signal, drafts the review, retrieves literature from OpenAlex and ranks the reviewers. "
     "The pipeline applies the filters, keeps the top five and returns one result dictionary. "
     "FastAPI inserts it into the analyses table, deletes the temporary file and returns the JSON with its analysis identifier."),
    ("uc", "Use-case diagram", "08_use_case.png",
     "Use-case diagram of PeerScope with its two human actors and two supporting systems.",
     "The editor or programme chair uploads a paper, reads the preliminary assessment and the review, sees related literature, obtains ranked reviewers with an audit breakdown, exports the analysis, browses the history and views the model performance. "
     "Obtaining reviewers includes the conflict-of-interest check. "
     "The directory administrator manages reviewer records and imports or exports them as CSV. "
     "The local Qwen model supports the review and OpenAlex supports the literature view; neither is a human user."),
    ("er", "Entity-relationship diagram", "09_er_diagram.png",
     "Entity-relationship diagram of the PeerScope SQLite tables and file-based stores.",
     "PeerScope keeps two SQLite tables. The reviewers table holds the directory with expertise text, comma-separated topics, methods and keywords, load limits, an active flag and conflict terms. "
     "The analyses table stores one row per analysis with summary columns and the complete result as JSON text. "
     "There is no foreign key between them: top_reviewer is a copy of a name and the ranked reviewers are snapshotted inside result_json. "
     "The dataset CSV, the two joblib model files and metrics.json are file stores written by the training scripts."),
    ("match", "Reviewer-matching flowchart", "10_flowchart_matching.png",
     "Flowchart of the auditable reviewer-matching algorithm.",
     "The paper profile and every reviewer profile are embedded, and the cosine similarity, keyword overlap, method and topic overlap and availability are computed for each reviewer. "
     "A conflict check looks for a conflict term, the reviewer's full name or the affiliation in the first 3,000 characters of the paper and applies a penalty of 0.60 when one is found. "
     "The final score is 0.55 similarity plus 0.20 keyword, 0.15 method and 0.10 availability, minus the penalty, scaled to 0-100 and labelled Strong, Good, Possible or Weak. "
     "Reviewers are sorted, ranked and filtered, and the top five are returned with their breakdown."),
    ("train", "Decision-model training pipeline", "11_ml_training_pipeline.png",
     "Training and serving pipeline of the decision model.",
     "prepare_dataset.py writes a labelled CSV of 1,400 rows; because the public probe was not reachable it used its synthetic fallback. "
     "train_model.py cleans and encodes the rows, makes a stratified 80/20 split with seed 42 and fits a word TF-IDF and a character TF-IDF on the training part only. "
     "The stacked features feed a class-balanced logistic regression, which is evaluated on the 280 test rows. "
     "The model, the vectorizer and metrics.json are saved, and at request time ml_predict transforms the title, summary and first 4,000 characters of a paper and returns the class probabilities."),
    ("pdf", "PDF extraction and structural scoring", "12_pdf_extraction_flow.png",
     "Flow of PDF extraction and structural scoring in PeerScope.",
     "After the upload checks, PyMuPDF extracts the text of each page, which is normalised and joined. "
     "The title is the first suitable line among the first 25, sections are found from short heading lines matched to nine patterns, references are split after a References heading, and a summary is taken from the summary or introduction text. "
     "Four signals are then computed: structure completeness, evidence coverage, method clarity and presentation. "
     "They are combined with weights 0.35, 0.25, 0.25 and 0.15 into an overall structural score, which selects the wording of the overall assessment."),
]
