"""Index of the CipherVeil design diagrams: (key, title, file, caption, explanatory paragraph).

The files are written by scripts/docs/make_diagrams.py and diagrams_more.py into docs/diagrams/.
Used by the block-diagram document (11), the full report, the decks and the paper.
"""

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "Four-tier architecture of CipherVeil: React console, FastAPI application with 24 routes, service layer of seven modules, and SQLite plus files.",
     "The presentation tier is the React console on port 5315; its axios client sends a JWT with every call and Vite proxies /api to the backend. The FastAPI tier on port 8315 exposes 24 routes in five routers: "
     "authentication and health, keys, samples, send and receive, and analysis. All but register, login and health depend on current_user(). Below it, seven pure-function modules do the work: crypto, lsb, metrics, "
     "pipeline, plots, robustness and benchmark. Persistence is a SQLite file with three tables, plus plain files for the sample covers, the sample payloads and the per-operation outputs."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "Sender lane, lossless hand-over of the stego PNG, receiver lane, and the analysis tools that read the stored operation.",
     "Lane A is the Send page: choose the receiver's public key, a file and a cover image, encrypt with AES-256-GCM, wrap the session key with RSA-OAEP, check capacity, embed one bit per colour value, and return a PNG with "
     "its PSNR, SSIM and file hash. The PNG then travels outside the system over any lossless channel. Lane B is the Receive page: read the 32-bit length and the bundle bits, unwrap the key, decrypt with tag "
     "verification, and compare SHA-256 values. Analysis, robustness, benchmark and log pages read the cover and stego pair and the oplog rows written by lane A."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Context diagram (DFD level 0): one process, the sender and receiver roles, the read-only sample library, and the evaluator or developer.",
     "At level 0 the whole product is a single process. The sender supplies credentials, a key choice, a file and a cover image and receives the stego PNG, its PSNR and SSIM and the SHA-256 of the file. "
     "The receiver supplies credentials, the private key and the stego PNG and receives the restored file, both hash values and a verdict. The sample library of six covers and four payloads is read-only data "
     "that ships with the product. The evaluator or developer runs ml/eval.py, the tests and run_experiments.py and receives metrics files, test results and screenshots."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "DFD level 1: six functional processes, a logging process, and five data stores (users, keypairs, outputs, oplog, samples).",
     "Level 1 splits the platform into seven processes. Process 1.0 authenticates against D1 users. Process 2.0 manages key pairs in D2. Process 3.0 reads a public key from D2 and a sample from D5, and writes "
     "cover.png and stego.png into D4. Process 4.0 reads a private key and writes restored.bin. Process 5.0 reads the cover and stego pair to compute metrics and plots. Process 6.0 reads the stego image and "
     "writes robustness.json. Every process hands an event record to process 7.0, which appends a row to D3 oplog without any key or file content."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "DFD level 2: process 3.0 (encrypt and hide) expanded into seven sub-processes.",
     "Level 2 follows one send request. Process 3.1 validates the inputs: the key must belong to the user, the file must be non-empty and below 25 MB, and the cover must decode to RGB. Process 3.2 builds "
     "the header and encrypts it with the file under AES-256-GCM, and process 3.3 wraps the session key with RSA-OAEP. Process 3.4 assembles the CVL1 bundle. Process 3.5 refuses a bundle larger than the "
     "capacity and otherwise embeds it. Process 3.6 encodes the PNG and measures PSNR, SSIM and MSE, and process 3.7 stores the images and writes the oplog row."),
    ("uml", "UML class diagram", "06_uml_class.png",
     "UML class diagram: the three SQLAlchemy tables, the service modules shown as classes with static functions, the five routers and the two exception classes.",
     "User owns many KeyPair rows and performs many OpLog rows. The crypto module holds the CVL1 magic and the allowed key sizes and builds and parses bundles; lsb loads images, computes capacity and embeds "
     "or extracts bits; metrics returns PSNR, SSIM, MSE and the largest change. The pipeline module composes the three in hide() and reveal(). The robustness module reuses crypto and lsb to attack a stego image "
     "and test decryption, and benchmark reuses pipeline. The routers depend on the ORM session and on these modules, and map CryptoError and StegoError to HTTP 400."),
    ("seq", "Sequence diagram of the main flow", "07_sequence_flow.png",
     "Sequence diagram: sending a file (part A) and receiving it (part B), from the browser through the routes to the services and the database.",
     "Part A starts when the user presses Encrypt and hide. The console posts a multipart request with the JWT; the route checks the token and the key, calls pipeline.hide, which asks crypto to encrypt and wrap, "
     "then lsb to embed and encode the PNG and metrics to measure quality. The route then writes the oplog row and the two images and returns a JSON summary. Part B posts the stego image; reveal() extracts the "
     "bits, crypto verifies magic, key size, RSA unwrap, GCM tag and hash, and the route stores restored.bin, logs the receive and returns the hash comparison."),
    ("uc", "Use-case diagram", "08_use_case.png",
     "Use cases of CipherVeil for the sender, the receiver and the evaluator, with the two include relations.",
     "The sender and the receiver are roles of one signed-in user. Both register or sign in, generate RSA key pairs of 2048, 3072 or 4096 bits, and import or export keys. The sender encrypts and hides a file, "
     "which includes the capacity check; the receiver extracts and decrypts, which includes verifying the GCM tag and the SHA-256 hash. Any user can view the PSNR, SSIM, histograms and bit planes, run the nine "
     "robustness attacks, run the capacity and speed benchmark and browse the operation log. The evaluator additionally runs the evaluation script and the tests from the command line."),
    ("er", "Entity-relationship diagram", "09_er_diagram.png",
     "Entity-relationship diagram of the SQLite database (users, keypairs, oplog) and of the per-operation output folder.",
     "The database has three tables created by SQLAlchemy. A user has a unique username and a bcrypt hash. A user owns zero or more keypairs, each with a name, size, fingerprint and PEM texts; private_pem is "
     "empty for public-only entries imported from a partner. A user performs zero or more oplog rows, each with an operation name, an ok flag and a JSON details field that holds sizes, timings, metrics and "
     "key fingerprints but never secrets. The key used by an operation is recorded inside details rather than by a foreign key. Each send or receive creates a folder named by its operation id on disk."),
    ("algo", "Flowchart of the embedding and extraction algorithm", "10_flowchart_algorithm.png",
     "Flowchart: embedding with the capacity check (left) and extraction with its four rejection tests (right).",
     "Embedding builds the header, encrypts, wraps the key and assembles the bundle, then compares its length with (height x width x 3 - 32) / 8. A larger bundle is rejected before any pixel is touched. Otherwise the "
     "32-bit length and the bundle bits replace the lowest bit of consecutive colour values and the PNG is encoded. Extraction reads the length and rejects zero or impossible values, then checks the magic and the "
     "wrapped-key size, unwraps the session key and verifies the GCM tag. Only when all tests pass is the header parsed and the SHA-256 of the restored file compared with the recorded hash."),
    ("bundle", "Bundle layout and bit embedding", "11_bundle_layout.png",
     "Byte layout of the CVL1 bundle (top) and the way its bits, preceded by a 32-bit length, occupy the lowest bit of consecutive colour values (bottom).",
     "The bundle starts with the four-byte magic CVL1 and a two-byte length of the wrapped key, followed by the RSA-OAEP wrapped AES key (256, 384 or 512 bytes), a 12-byte nonce, and the AES-256-GCM "
     "ciphertext with its 16-byte tag. The encrypted part holds a two-byte header length, the JSON header with name, size and SHA-256, and the file. For hiding, the length of the bundle as 32 bits is "
     "written first, then the bundle bits, one per colour value from the top-left pixel in row order. Each value keeps its upper seven bits, so it changes by at most one."),
]

if __name__ == "__main__":
    for k, t, f, c, x in DIAGRAMS:
        print(k, len(x.split()), len(c.split()))
