"""Chapter 5: System Design for CipherVeil.

build_docs.doc12 renders blocks()[1:], so the first element must be the chapter H1.
"""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, PAIR, TAB
from .refs import CITE as R


def c(*keys):
    return "[" + "], [".join(str(R[k]) for k in keys) + "]"


def shot(name, caption, base=5.4, max_h=3.7):
    return FIG(F.shot(name), caption, F.shot_w(F.shot(name), base, max_h))


def blocks():
    a, w = F.API_PORT, F.WEB_PORT
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter describes the architecture, the workflow, the data flow, the UML and data design, the modules, the interface design and the security design of CipherVeil. The diagrams were drawn from "
          "the code in `backend/app/` and `frontend/src/`; the complete set, with longer explanations, is also in the Block Diagrams document."),

        H2("5.1 Design Goals and Architecture"),
        P("Five goals shaped the design. **Two independent layers**: the content must stay confidential even if the hiding is found, and the transfer must look like a picture. "
          f"**Standard primitives only**: AES-256-GCM and RSA-OAEP-SHA256 from a maintained library {c('aes', 'gcm', 'rfc8017')}, with no home-made cipher. "
          "**Measurable behaviour**: every message records PSNR, SSIM, capacity and timings. **Honest limits**: the interface must say what fails (a JPEG pass, a wrong key, an oversize file) and why. "
          "**Small and testable**: about 1,040 lines of backend code in 16 modules, each testable on its own."),
        FIG(F.diag("01_system_architecture.png"), "System architecture of CipherVeil: React console, FastAPI application with 24 endpoints, service layer, and the SQLite database and output files.", 5.4),
        P(f"The React console on port {w} calls the FastAPI application on 127.0.0.1:{a} through a Vite proxy that forwards `/api`. The application layer (`backend/app/routes/`) validates input, checks the bearer "
          "token and the ownership of every key and operation, and delegates to the service layer (`backend/app/services/`). The services hold the actual work: `crypto` (keys, AES-GCM, RSA-OAEP, bundle), "
          "`lsb` (capacity, embed, extract, PNG encoding), `metrics` (PSNR, SSIM), `pipeline` (the send and receive sequences, shared by the API, the benchmark and `ml/eval.py`), `plots`, `robustness` and `benchmark`. "
          "State is kept in a SQLite file (`data/app.db`, three tables) and in `data/outputs/<op>/`, where each send operation keeps its cover, its stego PNG and later its histogram and bit-plane images."),

        H2("5.2 High-Level Workflow and Core Algorithm"),
        FIG(F.diag("02_high_level_workflow.png"), "High-level workflow: the sender's path (encrypt, wrap, check capacity, embed, measure) and the receiver's path (extract, unwrap, verify).", 5.4),
        P("**Send.** The sender selects the receiver's public key, a file and a cover. The service builds a header `{name, size, sha256}`, encrypts `header_len | header | file` with a fresh 256-bit AES key and "
          "a fresh 96-bit nonce (additional data: the magic `CVL1`), wraps the session key with the receiver's RSA public key, and assembles the bundle. If the bundle is longer than the cover capacity "
          "`(width x height x 3 - 32) / 8` bytes the request is refused before anything is embedded. Otherwise the 32-bit length and the bundle are written, bit by bit, into the lowest bit of each "
          "red, green and blue value from the top-left pixel onwards, and the result is saved as a PNG. PSNR, SSIM and timings are then computed against the untouched cover."),
        P("**Receive.** The receiver extracts the length and the bundle from the lowest bits, rejects an image without a plausible header, checks the magic and the wrapped-key length, unwraps the "
          "session key with the private key, and decrypts. A wrong key, a flipped bit or a truncated bundle fails the GCM tag check and nothing is released. Finally the SHA-256 stored inside the "
          "encrypted header is compared with the hash of the restored file."),
        FIG(F.diag("10_flowchart_algorithm.png"), "Flowchart of the core algorithm: encrypt and embed, extract and decrypt, with the refusal branches.", 5.0),
        FIG(F.diag("11_bundle_layout.png"), "Layout of the CVL1 bundle that is hidden in the image, and its position in the LSB stream.", 5.4),
        P("The bundle carries everything the receiver needs and nothing secret in the clear: the magic and the length of the wrapped key (6 bytes), the RSA-wrapped session key (256, 384 or 512 bytes for "
          "RSA-2048, 3072 or 4096), the nonce (12 bytes) and the ciphertext with its 16-byte tag. The fixed overhead is 401, 529 and 657 bytes for the three key sizes with a short file name."),

        H2("5.3 Data Flow Diagrams"),
        H3("5.3.1 Level 0: context"),
        FIG(F.diag("03_dfd_level0.png"), "Data flow diagram, level 0: the user, the cover and payload files and the receiver exchange data with the CipherVeil platform.", 4.0),
        P("At level 0 the platform is one process. The **user** sends credentials, key requests, a payload file, a cover image and a stego image to receive, and gets back keys, the stego PNG, the restored file, "
          "the two hashes, quality metrics and the log. The **receiver** is outside the platform in the sense that the public key goes to the sender and the stego PNG travels between them over a channel "
          "CipherVeil does not control. The **evaluator** runs the scripts and reads the result files."),
        H3("5.3.2 Level 1: main processes"),
        FIG(F.diag("04_dfd_level1.png"), "Data flow diagram, level 1: authenticate, manage keys, encrypt and embed, extract and decrypt, analyse, attack and benchmark, and log.", 4.5),
        P("Level 1 splits the platform into processes for authentication (1.0), key management (2.0), encrypt and embed (3.0), extract and decrypt (4.0), analysis of imperceptibility (5.0), "
          "robustness and benchmark (6.0) and logging (7.0). The data stores are the user table, the key table (with the private half only for the owner's own keypairs), the operation log, and the "
          "output folder of cover, stego and restored files. The log never receives keys, passwords or file contents."),
        H3("5.3.3 Level 2: encrypt and embed"),
        FIG(F.diag("05_dfd_level2.png"), "Data flow diagram, level 2: process 3.0 expanded into header, AES-GCM, key wrap, capacity check, embedding and metrics.", 4.5),
        P("Process 3.0 expands into building the header and hashing the file, encrypting with AES-256-GCM, wrapping the session key with RSA-OAEP, assembling the bundle, checking capacity, embedding the "
          "bits, encoding the PNG and measuring PSNR and SSIM. The same sequence is used by the API, by the benchmark and by `ml/eval.py`, so the evaluation measures the code the user runs."),

        H2("5.4 UML Design"),
        H3("5.4.1 Class diagram"),
        FIG(F.diag("06_uml_class.png"), "UML class diagram: the ORM classes, the service modules, the two error classes and the FastAPI routers.", 5.0),
        TAB("Principal classes and modules",
            ["Element", "File", "Role"],
            [["`User`, `KeyPair`, `OpLog`", "backend/app/db.py", "The three database tables as SQLAlchemy classes"],
             ["`CryptoError`", "services/crypto.py", "Raised for a bad key, wrong key, tag failure or foreign bundle"],
             ["`StegoError`", "services/lsb.py", "Raised for an unreadable image, oversize payload or missing header"],
             ["`crypto`", "services/crypto.py", "Key generation and loading, fingerprint, `encrypt_bundle`, `decrypt_bundle`"],
             ["`lsb`", "services/lsb.py", "`capacity_bytes`, `embed`, `extract`, `to_png_bytes`, `load_rgb`"],
             ["`pipeline`", "services/pipeline.py", "`hide` and `reveal`: the whole send and receive sequences with timings"],
             ["`robustness`, `benchmark`, `plots`, `metrics`", "services/", "Attacks and verdicts, capacity and speed tables, charts, PSNR and SSIM"]],
            widths=[1.9, 1.5, 3.0], align=["l", "l", "l"], size=9.5),
        P("The service layer is written as plain functions rather than a class hierarchy because the operations are pure transformations of bytes and arrays; only the database entities and the two error types are "
          "classes. This keeps the cryptography and the embedding free of web code and makes them directly testable."),
        H3("5.4.2 Sequence diagram"),
        FIG(F.diag("07_sequence_flow.png"), "Sequence diagram of the main flow: the sender sends a file, the receiver extracts and decrypts it.", 4.4),
        P("In the send scenario the console posts a multipart request to `POST /api/send` with the bearer token. `current_user` verifies the HS256 signature and expiry; the route loads the key (an ownership check), "
          "reads the payload and the cover, and calls `pipeline.hide`; on success it writes a row to `oplog`, stores the cover and the stego PNG under the operation number, and returns the metrics. "
          "In the receive scenario `POST /api/receive` loads the private key, calls `pipeline.reveal`, and returns the filename, the two hashes and `gcm_verified`; any `CryptoError` or `StegoError` becomes a 400 "
          "response with a message and a failed row in the log."),
        H3("5.4.3 Use-case diagram"),
        FIG(F.diag("08_use_case.png"), "Use-case diagram with the sender, the receiver and the evaluator.", 4.2),
        P("The **sender** imports or receives a public key, sends a file, reads the analysis and runs the robustness tests. The **receiver** generates a keypair, exports the public key, and extracts and decrypts. "
          "Both are the same application role (a signed-in user); the diagram separates them because they perform different use cases. The **evaluator** runs the benchmark and the scripts and reads the log."),

        H2("5.5 Data Design"),
        FIG(F.diag("09_er_diagram.png"), "Entity-relationship diagram of the SQLite database: users, keypairs and the operation log.", 4.4),
        P("The database has three tables. One user owns many keypairs and many log rows (1 : n each). A `keypairs` row stores the public PEM, a SHA-256 fingerprint of the public key (shown as twelve hex pairs) "
          "and, only for the owner's own keypairs, the private PEM; an imported recipient key has `private_pem` empty. The `oplog` row stores the operation, a success flag and a JSON text of sizes, timings and metrics."),
        TAB("Database schema", ["Table", "Columns", "Notes"],
            [["`users`", "id, username (unique, 3-40 characters), pw_hash, created_at", "Passwords stored as bcrypt hashes (72-byte limit)"],
             ["`keypairs`", "id, user_id (FK), name, bits, fingerprint, public_pem, private_pem (nullable), created_at", "`private_pem` is stored unencrypted: a known gap"],
             ["`oplog`", "id, user_id (FK), op, ok, details (JSON text), created_at", "No keys, passwords or file contents are ever passed to the logger"]],
            widths=[1.0, 3.3, 2.1], align=["l", "l", "l"], size=9.5),
        P("Files are kept beside the database: `data/covers/` and `data/payloads/` hold the six sample covers and four sample payloads; `data/outputs/<operation id>/` holds `cover.png`, `stego.png`, the cached "
          "histogram and bit-plane images, `restored.bin` and `robustness.json`. The database and the outputs are not committed to the repository."),

        H2("5.6 Module Design"),
        TAB("Backend modules", ["Module", "Lines", "Responsibility"],
            [["`services/crypto.py`", "128", "RSA keypairs (2048, 3072, 4096), PEM loading with a 2048-bit floor, fingerprint, bundle encrypt and decrypt"],
             ["`services/lsb.py`", "59", "Capacity, embedding and extraction with a 32-bit length prefix, PNG encoding"],
             ["`services/metrics.py`", "21", "PSNR, SSIM, MSE, largest change, share of values changed"],
             ["`services/pipeline.py`", "55", "`hide` and `reveal` with per-stage timings"],
             ["`services/robustness.py`", "106", "Nine attacks, bit-error rate, a real decrypt attempt and a verdict per attack"],
             ["`services/benchmark.py`, `plots.py`", "51 + 50", "Capacity and speed tables; histograms and bit-plane charts"],
             ["`routes/` (auth, keys, ops, analysis, samples)", "399", "24 endpoints with validation, ownership checks and error mapping"],
             ["`auth.py`, `db.py`, `config.py`, `main.py`", "171", "bcrypt and JWT, tables, settings from `.env`, application start-up and the demo account"]],
            widths=[2.3, 0.7, 3.4], align=["l", "c", "l"], size=9.5),
        P("The frontend has eight pages: Landing, Login, Keys, Send, Receive, Analysis, Robustness and Log, built from a small component set (controls, cards, tables, charts, feedback). "
          "A single Axios client adds the token, logs method, path and status to an in-browser activity log, and sends a signed-out user back to the login page on a 401."),

        H2("5.7 API Design"),
        TAB("The 24 endpoints (all under `/api`; JWT required except health and auth)", ["Group", "Endpoints"],
            [["Health and auth (4)", "`GET /health`; `POST /auth/register`, `/auth/login`; `GET /auth/me`"],
             ["Keys (5)", "`GET /keys`; `POST /keys/generate`, `/keys/import`; `GET /keys/{id}/export?part=public|private`; `DELETE /keys/{id}`"],
             ["Samples (4)", "`GET /samples/covers`, `/samples/payloads`, `/samples/covers/{name}`, `/samples/payloads/{name}`"],
             ["Operations (3)", "`POST /send`; `POST /receive`; `GET /ops/{id}/cover|stego|restored`"],
             ["Analysis (8)", "`GET /analysis/{op}`, `/analysis/{op}/histogram.png`, `/analysis/{op}/bitplanes.png`; `POST` and `GET /robustness/{op}`; `GET /benchmark/capacity`; `POST /benchmark/run`; `GET /log`"]],
            widths=[1.5, 4.9], align=["l", "l"], size=9.5),
        P("Errors follow one pattern: a 400 with a plain-language `detail` for a user mistake (oversize file, wrong key, unreadable image), 401 for a missing or expired token, 404 for something that "
          "does not exist or belongs to another user, 409 for a taken username, 413 for an upload above 25 MB and 422 for failed validation."),

        H2("5.8 Security Design"),
        B("**Confidentiality.** A fresh AES-256 key and 96-bit nonce per message; the key is wrapped under RSA-OAEP with SHA-256 and MGF1-SHA-256; keys below 2048 bits are rejected.",
          "**Integrity.** The GCM tag covers the ciphertext and the magic as additional data; the SHA-256 in the header is checked after decryption.",
          "**Access control.** HS256 JWT valid for 12 hours; each key and operation is looked up with its owner and answers 404 to anyone else; sample names are resolved from a directory listing and never joined to a path.",
          "**Input limits.** 25 MB per upload; username pattern and password length checks; bcrypt on the first 72 bytes.",
          "**Logging.** The log records fingerprints and sizes only; a test scans it for key material."),
        P("Three gaps are part of the design and are stated rather than hidden: private keys are stored unencrypted in the local SQLite file, so `data/app.db` must be treated as sensitive; the repository's `.env` "
          "carries a placeholder JWT secret that must be replaced before any real use; and there is no rate limit on login. In addition, embedding is sequential from the first pixel and does not depend on a key, "
          f"which is why statistical steganalysis can detect medium and high fill {c('westfeld', 'ws')} (Chapter 8)."),

        H2("5.9 User Interface Design"),
        P("The console uses a dark theme with a left navigation (Keys, Send, Receive, Analysis, Robustness, Operation log) and a status panel that names the suite (AES-256-GCM, RSA-OAEP, LSB in PNG). "
          "Each action page has the same shape: a form on the left with a step indicator (Key, File, Cover, Hide), and the result on the right with the numbers and the images that matter. Errors appear in a red panel "
          "that says what failed and what to try, and the Send page warns before the request if the estimated bundle exceeds the cover capacity."),
        PAIR([(F.shot("04_keys.png"), "Keys page: two generated RSA-3072 keypairs and one imported public-only RSA-2048 key, with fingerprints."),
              (F.shot("05_send_form.png"), "Send page: key, file and cover selected before the request.")], 2.95),
        PAIR([(F.shot("06_send_result.png"), "Send result: stego PNG, PSNR 57.642 dB, SSIM 0.9991, 22.445 % of capacity, hash of the sent file."),
              (F.shot("11_receive_result.png"), "Receive result: tag verified, both SHA-256 values identical, file restored.")], 2.95),
        shot("08_analysis.png", "Analysis page: PSNR, SSIM, MSE, largest change, share of values changed and capacity used."),
        P("The remaining screens (histograms, bit planes, wrong-key failure, robustness, benchmark and log) are shown with their results in Chapter 8 and in Appendix C."),

        H2("5.10 Design Decisions and Alternatives"),
        TAB("Main design decisions", ["Decision", "Chosen", "Alternative considered", "Reason"],
            [["Data cipher", "AES-256-GCM", "AES-CBC with a separate MAC", "One authenticated primitive; a flipped bit is rejected before any output"],
             ["Key transport", "RSA-OAEP, SHA-256, 3072-bit default", "Raw RSA, PKCS#1 v1.5, ECC", f"OAEP is the recommended RSA encryption padding {c('oaep', 'rfc8017')}; RSA keeps the key-pair story simple for a user"],
             ["Session key", "Fresh per message", "One key per receiver", "A compromised message key never exposes another message"],
             ["Embedding", "1 bit per R, G, B value, sequential", "Key-driven permutation, LSB matching, adaptive embedding", f"Simplest scheme with a closed-form PSNR and 3.0 bits per pixel; the stronger schemes {c('mielikainen', 'stc')} are future work"],
             ["Carrier format", "PNG, RGB, alpha dropped", "JPEG domain embedding", "Lossless carrier keeps spatial LSBs exact; the price is that only lossless handling survives"],
             ["Length header", "32 bits in the first LSBs", "Terminator pattern", "Capacity check and extraction need the length; a bad header is detected early"],
             ["Persistence", "SQLite via SQLAlchemy", "Files only, or a server database", "One file, no service to install; enough for a local tool"],
             ["Service shape", "Plain functions, shared `pipeline`", "Class hierarchy per stage", "The API, the benchmark and the evaluation run exactly the same code"]],
            widths=[1.1, 1.6, 1.7, 2.0], align=["l", "l", "l", "l"], size=9),
        P("Two of these choices carry the main trade-off of the project: a fixed, key-independent embedding order makes the arithmetic exact and the evaluation simple, but also makes the hiding "
          "detectable at medium and high fill; and the choice of a lossless carrier makes the extraction exact but limits the usable channels. Both are measured in Chapter 8."),

        H2("5.11 Summary"),
        P("The design keeps the cryptography and the embedding in small pure functions, shares one send and receive sequence between the API and the evaluation, scopes every key and operation to its owner, "
          "and records measurements instead of secrets. Chapter 6 gives the methodology and the implementation that realise it."),
    ]
