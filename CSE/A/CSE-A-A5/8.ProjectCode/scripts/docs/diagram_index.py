"""Index of the CipherGuard Shield design diagrams: (key, title, file, caption, explanatory paragraph).

The files are written by scripts/docs_build/make_diagrams.py, diagrams_dfd.py and diagrams_more.py into docs/diagrams/.
Used by the block-diagram document (11) and the full report.
"""

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "Four-tier architecture of CipherGuard Shield: console, FastAPI application, core Python packages with in-memory state, and file stores.",
     "The presentation tier is the React console on port 5305, which reaches the API through a Vite proxy, plus the original HTML dashboard served by the API at the root path. "
     "The FastAPI tier on 127.0.0.1:8305 groups the health and metrics routes, the ThreatSense routes for scoring and alerts, and the SecureChannel routes for encryption, "
     "decryption and file encryption, with the upload and size guards. Beneath it are the cipherguard/crypto and cipherguard/ids packages and the in-memory state: the alert log, "
     "the session-key cache and the mock cloud key pair. The data tier is files only: models, reports, the synthetic CSV and the offline experiment outputs. There is no database."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "Two lanes around one transfer: SecureChannel encrypts the payload while ThreatSense scores the traffic.",
     "Lane A takes a payload of up to 1 MB of text or 5 MB of file, generates an ephemeral P-256 key pair, derives a 32-byte key with ECDH and HKDF, encrypts with AES-256-GCM, "
     "builds the envelope of ciphertext, nonce, tag and ephemeral public key, and lets the cloud derive the key, check the tag and return plaintext or an error. "
     "Lane B takes a flow record or CSV, preprocesses it, obtains the XGBoost and CNN probabilities, stacks them, and returns a verdict that appends attacks to the alert log. "
     "The console runs both lanes side by side; the API does not hold a transfer back because of a verdict."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Context diagram (DFD level 0) with two human actors, the mock cloud and the dataset.",
     "At level 0 the whole platform is one process. The operator sends flow records, CSV files, text or files and ciphertext, and receives verdicts, alerts, envelopes, "
     "decrypted plaintext and metrics. The developer or administrator sends a retrain command and receives the new models and metrics file. The cloud endpoint receives an "
     "envelope and returns verified plaintext or a tag failure. Labelled flows from UNSW-NB15 or the synthetic CSV enter only at training time. The cloud endpoint is drawn as an "
     "external entity although it runs in the same process in this build, because a real deployment would place it elsewhere."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "DFD level 1: seven processes and five data stores.",
     "Level 1 splits the platform into seven processes. Process 1.0 validates and parses every request. Process 2.0 scores flows with the stored models (D4) and passes scores to "
     "3.0, which reports verdicts and appends attacks to the alert log (D1). Process 4.0 encrypts a payload and stores the session key in the cache (D2); process 5.0 looks the key up, "
     "or derives it again, decrypts, and returns plaintext or a 400 error. Process 6.0 serves the metrics file (D3). Process 7.0 trains the models offline from the training CSV (D5) "
     "and writes the model files and the metrics report."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "DFD level 2: the scoring process 2.0 expanded into six sub-processes.",
     "Level 2 follows ThreatSenseEngine.predict_proba. A valid record is completed with defaults and its column names are aligned (2.1). The saved preprocessor scales the 39 numeric "
     "features with MinMax and one-hot encodes proto, service and state (2.2), producing 70 inputs for the shipped bundle or 192 for the real-data bundle. XGBoost (2.3) and the "
     "1D CNN (2.4, input reshaped to N x 1 x F) each return an attack probability. The logistic-regression meta-model fuses them (2.5), and a threshold of 0.5 and the severity bands "
     "produce the label, confidence and severity (2.6)."),
    ("uml", "UML class diagram", "06_uml_class.png",
     "UML class diagram of the FastAPI application, the ThreatSense Engine, the CNN, the training pipeline, SecureChannel and KeyPair.",
     "The FastAPI application holds the engine, the alert list, the session-key cache and the two directory settings, and uses both ThreatSenseEngine and SecureChannel. "
     "ThreatSenseEngine owns the preprocessor, the XGBoost model, the CNN and the meta-model and exposes load, predict_proba and score_single. CNN1D_Torch defines the layer stack that "
     "the engine redefines when loading. SecureChannel is a set of static methods that create KeyPair instances. The Pydantic request schemas validate input, the alert is a plain dictionary "
     "entry, and the training pipeline in train.py produces the artefacts that the engine reads."),
    ("seq", "Sequence diagram of a protected transfer", "07_sequence_flow.png",
     "Sequence diagram: score a flow, encrypt a payload, decrypt and verify it.",
     "Three requests are shown. POST /api/ids/score reaches the engine, which preprocesses the record, runs XGBoost and the CNN and stacks them; an attack verdict is inserted into the alert "
     "log. POST /api/crypto/encrypt creates an ephemeral KeyPair, derives the session key against the cloud public key, encrypts with AES-256-GCM and caches the key by ephemeral public key. "
     "POST /api/crypto/decrypt checks the cache, otherwise derives the key with the cloud private key, decrypts, and returns the plaintext with verified true, or a 400 response when the tag "
     "does not verify."),
    ("uc", "Use-case diagram", "08_use_case.png",
     "Use-case diagram with the operator, the mock cloud endpoint and the developer.",
     "The operator can score one traffic record, score a CSV batch, review and clear alerts, encrypt text or a file, decrypt and verify at the cloud, run a tamper test and view model "
     "performance. The cloud endpoint takes part in decrypt and verify, because it holds the key pair. The developer or administrator retrains the models from the command line, which is "
     "why that use case sits at the edge of the system boundary. The tamper test is a decrypt-and-verify after one ciphertext byte is changed, so it includes the verification use case."),
    ("er", "Entity-relationship diagram (logical)", "09_er_diagram.png",
     "Logical entity-relationship diagram: CipherGuard Shield stores no tables, only memory structures and files.",
     "The flow record is scored as one verdict, and an attack verdict raises zero or one alert in a list capped at 500 entries. Verdicts are produced with a model bundle of five files, "
     "which is described by one metrics report. An encryption envelope is derived against the cloud key pair, which exists once per server process, and may be cached as an "
     "ephemeral-key to session-key entry. No foreign keys exist; these are call-time dependencies. The diagram is logical because the system has no database, and alerts and keys are lost on restart."),
    ("flow_score", "Scoring flowchart", "10_flowchart_scoring.png",
     "Flowchart of the ThreatSense scoring algorithm, from request to verdict.",
     "A request is refused with 400 or 503 if the payload is invalid or the engine is not loaded. Otherwise missing features are filled with defaults, categorical fields are cast to text and the "
     "preprocessor scales and one-hot encodes them, ignoring unseen categories. XGBoost and the CNN produce two probabilities, and the meta-model computes the sigmoid of their weighted sum. "
     "A probability of 0.5 or more makes the label attack, with severity critical at 0.85, high at 0.70 and medium otherwise, and the alert is appended; below 0.5 the label is normal "
     "with severity low and no alert."),
    ("flow_sc", "SecureChannel flowchart", "11_flowchart_securechannel.png",
     "Flowchart of encryption on the sender side and decryption with tag verification on the cloud side.",
     "The sender checks the payload, generates an ephemeral P-256 key pair, computes the ECDH secret with the cloud public key, derives a 32-byte key with HKDF-SHA256, draws a 12-byte "
     "random nonce and encrypts with AES-256-GCM. The envelope carries ciphertext, nonce, 16-byte tag and the 65-byte ephemeral public key. The cloud decodes the base64 fields and checks "
     "their lengths, obtains the key from its cache or by ECDH with its private key, and decrypts. A valid tag returns the plaintext with verified true; a wrong tag or key returns HTTP 400."),
    ("model", "Model architecture", "12_model_architecture.png",
     "Architecture of the stacked detector: preprocessing, XGBoost, 1D CNN and logistic-regression stacking.",
     "The 42-feature record is encoded into 70 inputs (192 with real UNSW-NB15). Branch A is an XGBoost classifier of 200 trees, depth 6 and learning rate 0.08. Branch B reshapes the vector "
     "to N x 1 x F and applies Conv1d 1 to 32, max-pool, Conv1d 32 to 64, max-pool, flatten, a 64-unit dense layer with dropout 0.3 and a sigmoid output, 76,097 parameters at 70 inputs. "
     "A logistic regression fitted on the validation split combines the two probabilities, and a threshold of 0.5 gives the label. The design is a simple analogue of the score-level fusion in the base paper."),
]
