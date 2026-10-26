"""Literature rows shared by the report (Chapter 2), the decks and the paper:
(key, work, approach, data, reported result, limitation). Only facts checked against the paper itself, a standards page, a DOI record or an abstract page
(details per entry in docs/LIT_NOTES.md). The batch-survey items that could not be located (refs s2, s3, s4) are deliberately absent from ROWS:
nothing is claimed about them."""

from .refs import N as C

ROWS = [
    ("base", "Nekouie et al., Scientific Reports 2026 (base paper)",
     "Electronic-health-record sharing: elliptic-curve ciphertext-policy attribute-based encryption (ABE) over both user and data attributes; ClinicalBERT extracts data attributes from clinical notes; "
     "a private Hyperledger Fabric ledger stores attribute public keys and policies; several key-generation centres, no key escrow; ciphertext on a semi-trusted cloud",
     "No dataset and no extraction accuracy are reported; cost is calculated from operation counts and primitive timings measured on an HPE server (6-core E5-2620 v3, 32 GB) and a Raspberry Pi 3 B+ with OpenSSL",
     "Total encryption + decryption cost of about 8,506 us (x = 5 attributes, Raspberry Pi timings) against 8,812 to 71,323 us for the compared ABE schemes; IND-CPA, collusion-resistance and escrow-freeness arguments",
     "Not a file-storage product (no upload, download, role model or audit-log latency); cost is analytic, not a measured end-to-end system; code and data only on request; needs a key-generation-centre network"),
    ("ijedr", "Sowmiya et al., IJEDR 2026",
     "Zero-trust cloud file storage: client-side AES-256-GCM, RSA-2048 key wrapping (OAEP-SHA256), Owner / Editor / Viewer RBAC, SHA-256 hash-chained audit log with ECDSA-signed entries, TOTP multi-factor sign-in, 4 MB chunking, PBKDF2 with 310,000 iterations, S3 + Vault",
     "50 users in 3 roles; 900 access attempts; 30-day adversarial test; 50 simulated log-tampering events (population details are not given in the paper)",
     "+320 ms upload overhead for a 10 MB file; 98.6% access-control accuracy (13 of 900 misclassified); 0 unauthorised exposure events in 30 days; 100% of 50 audit-tamper events detected; 1,240 simulated credential-stuffing attempts blocked",
     "Evaluation protocol is only sketched (no hardware, no per-operation timings, no tamper-method list); key recovery needs admin escrow; no offline mode; very large files add about 1.8 s"),
    ("geo", "Thenmozhi, Saralesh and Sakthi, Geocrypt",
     "RSA-encrypted file exchange with access gated by physical location and time-limited sessions; Ethereum smart contracts (Truffle, Ganache) record file-sharing transactions",
     "Only the abstract and front matter were read; no dataset stated there",
     "Presented as suitable for government, corporate, healthcare and defence settings (qualitative claim in the abstract)",
     "Location can be spoofed on the client; blockchain adds latency and a test-net dependency; no role model beyond location and time; no quantitative result was read"),
    ("sagi", "Saginayev et al., Computing & Engineering 2024",
     "Hybrid cryptography for cloud file storage: AES-256 for data, RSA for key management, SHA-256 hash before encryption and after decryption to check integrity",
     "Not stated in the abstract",
     "States better protection against unauthorised access and tampering; no benchmark figures in the abstract",
     "Abstract-level evidence only; no role model, audit trail or timing study was read"),
    ("mega", "Backendal, Haller and Paterson, MEGA",
     "Cryptanalysis of the MEGA end-to-end encrypted storage service: five attacks on its key hierarchy and file encryption",
     "The deployed MEGA service and its client code",
     "The attacks together allow full compromise of the confidentiality of user files (as stated in the abstract); MEGA's developers added RSA key checks after disclosure",
     "A lesson, not a system: unauthenticated or malleable key wrapping and encryption modes break an otherwise end-to-end design"),
    ("sirius", "Goh et al., SiRiUS",
     "File layer over untrusted network storage (NFS, CIFS and similar) with its own read / write cryptographic access control and hash-tree freshness",
     "Prototype file system",
     "Shows that per-file keys and signatures can give file-level sharing over a server that is not trusted",
     "Design for network file systems rather than a web application; the abstract describes no tamper-evident audit log"),
    ("plutus", "Kallahalla et al., Plutus",
     "Cryptographic storage with filegroups to reduce the number of keys users exchange, separate read and write access, efficient revocation and a way for the untrusted server to check writes",
     "Prototype on OpenAFS",
     "Security comparable to systems that encrypt all network traffic, at similar overhead (as stated in the abstract)",
     "Design for a file-system client (OpenAFS), not a web application; no tamper-evident audit log is described in the abstract"),
    ("tahoe", "Wilcox-O'Hearn and Warner, Tahoe-LAFS",
     "Least-authority file system: capabilities for access control, cryptography for confidentiality and integrity, erasure coding for fault tolerance",
     "Distributed storage grid design",
     "Cryptography provides confidentiality and integrity against the storage servers (as stated in the abstract); a design report rather than a benchmark",
     "Access is by capabilities rather than user roles; no role model or audit log is described in the abstract"),
    ("cryptdb", "Popa et al., CryptDB",
     "SQL queries over encrypted data using onions of layered encryption schemes",
     "Trace of 126 million SQL queries from a production MySQL server",
     "Operations over encrypted data supported for 99.5% of the 128,840 columns in the trace (as reported in the paper)",
     "Database-level encryption for queries, not an encrypted file store with sharing"),
    ("kamara", "Kamara and Lauter, Cryptographic cloud storage",
     "Architecture for a virtual private storage service on a public cloud using newer, non-standard cryptographic primitives",
     "Architectural survey",
     "Argues that provider-blind storage is feasible with newer cryptographic primitives",
     "An architecture and survey; no measurements of a file-sharing application were read"),
    ("abe06", "Goyal et al., key-policy ABE",
     "Attribute-based encryption in which ciphertexts carry attributes and keys carry access structures; also used to share audit-log data",
     "Theoretical construction",
     "Introduces key-policy ABE and shows it can also serve audit-log sharing and broadcast encryption (as stated in the abstract); CCS 2016 test-of-time award",
     "Policy lives in the key, so it fits enterprise policies but is heavier than a symmetric-key design; the base paper and the IJEDR paper both treat ABE as expensive"),
    ("cpabe", "Bethencourt, Sahai and Waters, CP-ABE",
     "Ciphertext-policy ABE: the encryptor chooses an access structure over attributes; user keys carry attributes",
     "Theoretical construction with a prototype",
     "Introduces the ciphertext-policy variant, the family the base paper builds on",
     "Pairing-based construction; the IJEDR paper calls ABE computationally expensive for large files"),
    ("pre06", "Ateniese et al., proxy re-encryption",
     "Semi-trusted proxy transforms ciphertexts from one key to another without seeing plaintext; applied to access control for the SFS read-only file system",
     "Experimental file system",
     "Shows that proxy re-encryption can work effectively in practice (as stated in the abstract)",
     "Adds a proxy trust assumption and a pairing-based primitive"),
    ("rbac01", "Ferraiolo et al., NIST RBAC",
     "Proposed standard for role-based access control: core, hierarchical and constrained RBAC reference models",
     "Standards proposal",
     "Defines the user-role-permission model with separation-of-duty constraints that most RBAC systems follow",
     "A model, not a storage system; says nothing about key management or audit integrity"),
    ("audit99", "Schneier and Kelsey, secure audit logs",
     "Forward-secure, hash-chained audit logs for untrusted machines",
     "Protocol design",
     "Entries written before a compromise cannot be read, or undetectably modified or destroyed, by the attacker (as stated in the abstract)",
     "Designed for a machine that may later be compromised, with a separate verifier; a plain unsigned hash chain without it does not stop a full rewrite"),
    ("tamper09", "Crosby and Wallach, tamper-evident logging",
     "Tree-based (Merkle) log structure that gives logarithmic-size membership and consistency proofs to auditors",
     "Prototype logger with untrusted-logger model",
     "Proofs of logarithmic size and space, improving on linear constructions (as stated in the abstract)",
     "Needs commitments published to auditors; more complex than a simple chain"),
]

GAP = ("The surveyed work covers four separate things: attribute-based encryption and blockchain for health records, cryptographic storage systems built for research prototypes, role-based access models "
       "as abstract standards, and a few recent file-storage papers that combine client-side AES with RSA key wrapping, roles and an audit log. "
       "The closest of these, the IJEDR architecture, reports its headline results (+320 ms, 98.6% access accuracy, 100% tamper detection) without publishing hardware, per-operation timings, the method of tampering or the list of operations tested, "
       "and the base paper measures neither a file upload nor a role check. None of the works we found gives a general-purpose, runnable file store that joins browser-side AES-256-GCM, per-recipient RSA key wrapping, "
       "server-enforced Owner / Editor / Viewer roles, plaintext-hash integrity checks and a hash-chained audit log, and then measures every layer on one machine and reports the weaknesses it finds. "
       "Such a measured study, including what the audit chain does not detect, is the gap this project fills.")

THEMES = [
    ("Client-side encrypted storage and untrusted servers",
     f"The idea that the storage server should not be trusted is old. SiRiUS {C('sirius')} layers its own read and write cryptographic access control over network file systems, Plutus {C('plutus')} reduces key distribution by grouping files, "
     f"and Tahoe-LAFS {C('tahoe')} builds a least-authority file system from capabilities, cryptography and erasure coding. Kamara and Lauter {C('kamara')} describe a virtual private storage service that keeps the provider blind to data, "
     f"and CryptDB {C('cryptdb')} extends the idea to SQL queries over encrypted columns. Recent file-storage papers follow the same pattern with commodity primitives: AES-256, RSA and SHA-256 {C('sagi')}, "
     f"and the IJEDR architecture with browser-side AES-256-GCM, RSA-2048 key wrapping, roles and a chained audit log {C('ijedr')}. "
     f"Deployed services are not automatically safe: the attacks on MEGA {C('mega')} show that malleable key handling and unauthenticated modes undo end-to-end encryption in practice. "
     "These works either remain research prototypes or report little measurement; CipherVault takes the browser-side hybrid design and measures it."),
    ("Access control: roles, attributes and proxy re-encryption",
     f"Role-based access control grants permissions to roles rather than to individual users {C('rbac96')}, {C('rbac01')}, and fits the three-level Owner / Editor / Viewer pattern of file sharing; the protection principles of "
     f"Saltzer and Schroeder {C('saltzer')} (least privilege, complete mediation, fail-safe defaults) apply directly. Attribute-based encryption moves the policy into the ciphertext, with key-policy {C('abe06')} and ciphertext-policy {C('cpabe')} variants, "
     f"which is fine-grained but computationally heavy; proxy re-encryption {C('pre06')} lets a semi-trusted proxy re-target ciphertexts but adds a trusted proxy. "
     f"The base paper {C('base')} follows the attribute route for health records, adding ClinicalBERT {C('clinbert')} to derive data attributes. "
     "For a general file store with a handful of roles, per-recipient key wrapping plus a server-side role check is much cheaper, and that is the design CipherVault uses."),
    ("Key management and password-derived keys",
     f"Hybrid encryption wraps a fresh random file key under each recipient's RSA public key with OAEP padding {C('oaep94')}, {C('oaep')}, and encrypts the file with AES {C('aes')} in Galois/Counter Mode {C('gcm')}, "
     f"which authenticates as well as encrypts; random 96-bit nonces must not repeat under one key, as forgery attacks on repeated GCM nonces in TLS showed {C('boeck')}. "
     f"A private key that must survive on the server is protected by a key derived from the password with PBKDF2 {C('pbkdf2')}, {C('sp800132')}; the IJEDR paper uses 310,000 iterations {C('ijedr')}, CipherVault 120,000. "
     f"Server-side passwords use the adaptive bcrypt scheme {C('bcrypt')}, and sessions use signed JSON Web Tokens {C('jwt')}. In the browser all of this runs through the Web Cryptography API {C('webcrypto')}. "
     "Password loss therefore means data loss unless an escrow is added, a limitation both CipherVault and the IJEDR paper state."),
    ("Tamper-evident audit logging and blockchain",
     f"Schneier and Kelsey {C('audit99')} showed how a hash-linked log on an untrusted machine can make earlier entries impossible to modify undetectably, using SHA-256-class hashes {C('sha')}; "
     f"Crosby and Wallach {C('tamper09')} replaced the linear chain with a Merkle tree so auditors can check membership with logarithmic proofs. "
     f"The base paper puts attribute public keys on a permissioned Hyperledger Fabric ledger {C('fabric')}, Geocrypt records transactions with Ethereum smart contracts {C('geo')}, "
     f"and the IJEDR paper uses a SHA-256 chain with ECDSA signatures and reports that all 50 simulated tampering events were detected {C('ijedr')}. "
     "A bare hash chain detects an edit, a deletion in the middle or a swap, but not a rewrite that recomputes every later hash, and not truncation of the tail, unless the head hash is signed or published elsewhere; "
     "CipherVault's own tamper study measures exactly these two limits (Chapter 8)."),
    ("What the surveyed systems measure",
     f"Papers on attribute-based schemes compare computation cost in microseconds of primitive operations: the base paper {C('base')} calculates total cost from operation counts and timings on a server and a Raspberry Pi 3 B+ "
     "and reports about 8,506 microseconds for its scheme with five attributes. File-storage papers report system-level outcomes: +320 ms for a 10 MB upload, 98.6% access-control accuracy over 900 attempts, "
     f"100% detection of 50 tamper events {C('ijedr')}. CryptDB reports coverage of 99.5% of columns in a 126-million-query trace {C('cryptdb')}. "
     "These numbers answer different questions on different machines and workloads, so they cannot be compared directly with one another or with CipherVault's measurements; "
     "the report states plainly where its conditions differ."),
]

BASE_ANALYSIS = {
    "summary": "The base paper proposes a scheme for sharing electronic health records through a semi-trusted cloud. Data owners extract data attributes (symptoms, diagnoses, medications) from unstructured clinical notes with ClinicalBERT, "
               "then encrypt the record with elliptic-curve ciphertext-policy attribute-based encryption in which the policy mentions both user attributes and data attributes. Several key-generation centres issue partial private keys, "
               "so no single authority holds a user's key (no key escrow), and a private Hyperledger Fabric ledger stores the attribute public keys and policies, which also simplifies revocation. "
               "The design has 23 phases, uses a fixed 160-bit elliptic-curve key length, and ends with the user computing a hash of the decrypted record and comparing it with the stored hash. "
               "The evaluation is analytic: total encryption and decryption cost is calculated from operation counts and the measured time of each primitive, and security is argued with IND-CPA, collusion-resistance and escrow-freeness sketches.",
    "strengths": ["Fine-grained, policy-based access that depends on both who the user is and what the record contains.",
                  "No key escrow, thanks to multiple key-generation centres, and collusion resistance argued formally.",
                  "A cost comparison against ten other ABE-scheme cost entries using the same primitive timings, run on a server and a constrained device (Raspberry Pi 3 B+).",
                  "Only lightweight metadata (public keys, policies) goes on the ledger; encrypted records stay off-chain, so ledger growth is small."],
    "limitations": ["The evaluation is a calculation from primitive timings, not a measured system: no end-to-end upload or download time, no access-check latency and no audit-log cost are given.",
                    "No dataset and no extraction accuracy for the ClinicalBERT step are reported; data and code are available only on request.",
                    "Key-generation-centre and ledger infrastructure is heavy for a small deployment, and attribute policies are harder to administer than three roles.",
                    "The domain is healthcare records, so file-level concerns such as upload limits, replace-content, per-file sharing and a user-visible audit trail are not addressed."],
    "numbers": {
        "table3_unit": "microseconds per operation, OpenSSL",
        "hpe": "HPE server: 6-core E5-2620 v3 at 2.40 GHz, 32 GB RAM, Ubuntu 20.04",
        "pi": "Raspberry Pi 3 B+: 1.4 GHz quad-core Cortex-A53, 1 GB RAM, 64-bit Raspbian 12",
        "primitives_pi_us": {"random number": 11.1, "hash": 2.3, "symmetric encryption/decryption": 0.5, "EC point multiplication": 557,
                             "EC point addition": 2.3, "exponentiation": 1187, "bilinear pairing": 1520, "modular multiplication": 0.5, "modular addition": 0.2},
        "primitives_hpe_us": {"random number": 2.2, "hash": 0.11, "symmetric encryption/decryption": 0.11, "EC point multiplication": 67,
                              "EC point addition": 0.3, "exponentiation": 137, "bilinear pairing": 175, "modular multiplication": 0.06, "modular addition": 0.02},
        "proposed_us": {"encryption": "1362.3x + 1131", "decryption": "0.2x + 563", "total": "1362.5x + 1694", "total_x5": 8506},
        "compared_totals_us": [8812, 8912, 8912, 11577, 11697, 21166, 40605, 41647, 71296, 71323],
        "setting": "x = 5 encryption attributes, l = 10 leaf nodes, r = 30 matrix rows, Raspberry Pi timings",
    },
    "adopts": ["The same trust model: the cloud store is untrusted and sees only ciphertext.",
               "A hash of the plaintext is stored and compared after decryption.",
               "Revocation and the audit of access are treated as part of the design, not extras.",
               "Cost is reported per cryptographic primitive so that overhead can be understood."],
    "not_adopts": ["Attribute-based encryption, ClinicalBERT attribute extraction, multiple key-generation centres and the Hyperledger Fabric ledger are not implemented: CipherVault uses AES-256-GCM, per-recipient RSA-OAEP key wrapping and a server-side Owner / Editor / Viewer role check.",
                   "The audit trail is a SHA-256 hash chain in the application database, not a blockchain.",
                   "The scheme is a general file store, not a health-record system, and it is a runnable web application rather than a calculation."],
    "comparability": "The base paper calculates the cost of a pairing-free attribute-based scheme in microseconds on a Raspberry Pi and an HPE server; CipherVault measures real uploads, downloads, role checks and audit verification in milliseconds "
                     "in Chrome and over loopback on an i5-12500 desktop shared with other jobs. The workloads (policy encryption of a record vs. AES-256-GCM of an arbitrary file), the hardware and the metrics differ, "
                     "so the numbers must not be ranked against each other. Only the qualitative aims (provider-blind storage, integrity check, revocation, auditability) are comparable.",
}


def rows():
    return [[w, a, d, r, l] for _, w, a, d, r, l in ROWS]
