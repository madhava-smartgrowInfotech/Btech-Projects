"""Index of the CipherVault design diagrams: (key, title, file, caption, explanatory paragraph).

The files are written by scripts/docs/make_diagrams.py into docs/diagrams/ (matplotlib, 150 dpi).
Used by the block-diagram document (11), the full report, the decks and the paper.
"""

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "Layered architecture of CipherVault: the browser as the cryptographic endpoint, the FastAPI application with 24 endpoints, the service and core layer, and the database and ciphertext store.",
     "The browser tier is a React 19 single-page application built with Vite (port 5413). Its vaultCrypto.js module wraps the Web Crypto API (AES-256-GCM, RSA-2048-OAEP, PBKDF2, SHA-256), and the unlocked private key lives in memory only, so a reload locks the vault. "
     "The Vite proxy forwards /api requests to the FastAPI application on port 8413; after npm run build the same process serves frontend/dist. "
     "The application tier consists of five routers (auth 6 routes, users 2, files 7, sharing 4, audit 3) plus the health and config routes, 24 endpoints in all. All but four of them require a JWT bearer token, which api/deps.py checks together with the login throttle. "
     "Two service modules sit behind the routers: permission_service decides the effective role of a caller and audit_service writes and verifies the hash chain; core/security.py provides bcrypt (cost 12) and JWT HS256 tokens. "
     "Persistence is a SQLAlchemy database (SQLite by default, PostgreSQL through DATABASE_URL) with four tables, and a storage/encrypted directory that holds ciphertext objects under random 32-hex names."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "End-to-end workflow: register, sign in, unlock the vault, encrypt and upload, store, share, download and decrypt, audit, revoke.",
     "At registration the browser generates an RSA-2048 key pair, seals the private key under an AES key derived from the password with PBKDF2, and sends the public key and the sealed bundle (the server hashes the password with bcrypt). "
     "Signing in returns a JWT valid for 120 minutes; the browser fetches the key bundle and unlocks the vault by deriving the same key from the typed password. "
     "To upload, the browser hashes the file with SHA-256, draws a random 256-bit file key and 12-byte IV, encrypts with AES-256-GCM, wraps the file key with the owner's public key and posts the ciphertext. "
     "The server validates the request, writes the ciphertext under a random name, inserts the files row and records an audit event. Sharing re-wraps the file key in the owner's browser for the recipient's public key and stores it in a file_permissions row. "
     "A recipient downloads, unwraps, decrypts and compares the digest before saving. Every step writes a hash-chained audit entry, and the audit page recomputes the chain on request."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Context diagram (DFD level 0): CipherVault as one process with the signed-in user, the visitor and the deployer.",
     "At level 0 the whole product is a single process. A visitor who is not signed in can only register and log in. A signed-in user, acting as owner, editor or viewer of particular files, sends credentials, ciphertext with its IV and wrapped key, and share, revoke, download and verify-chain requests, and receives the JWT, the sealed key bundle, ciphertext, wrapped keys, file lists, the audit view and the chain result. "
     "The deployer is an external source of configuration: the .env file supplies the JWT secret, the database URL, the upload limit and the throttle values to the Settings object. "
     "No third-party service appears on the diagram because the product contacts none: there is no cloud storage, key-management service, e-mail or analytics call. The browser-side cryptography is part of the process boundary, since the plaintext and the private key never cross it."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "DFD level 1: five processes (authenticate, manage sharing, encrypt and store, retrieve and decrypt, audit and verify) and the stores D1 to D5.",
     "Level 1 splits the product along its routers. Process 1.0 registers users, checks credentials with bcrypt, issues the JWT and hands out the sealed key bundle; it writes the users store (D1). "
     "Process 2.0 manages sharing: it reads public keys from D1 and the owner from D2, and writes or deletes permission rows in D3 together with the recipient's wrapped file key. "
     "Process 3.0 receives the ciphertext, IV, wrapped key and digest, writes the ciphertext object to the storage directory (D5) and the metadata row to D2. "
     "Process 4.0 answers list, metadata and download requests; it reads D2, D3 and D5, checks the caller's role and returns the ciphertext with the caller's own wrapped key. "
     "Process 5.0 receives an audit event from each of the other processes, appends it to the hash chain in D4 and answers the audit view and verify requests. Dashed arrows are reads and solid arrows are writes."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "DFD level 2: process 3.0 (encrypt and store file) expanded into four browser sub-processes and four server sub-processes.",
     "Level 2 expands process 3.0, because it carries the central security property of the product. In the browser, process 3.1 computes the SHA-256 digest of the plaintext, 3.2 draws a random file key and IV and encrypts with AES-256-GCM, 3.3 wraps the file key with the owner's RSA public key into a 256-byte value, and 3.4 builds the multipart request with the JWT. "
     "On the server, process 3.5 validates the request: authenticated user, base64 fields, an IV that decodes to 12 bytes, a 64-hex digest, and a size within 25 MB (HTTP 413 otherwise). "
     "Process 3.6 writes the ciphertext to storage/encrypted under a random 32-hex name, 3.7 inserts the files row with the IV, the wrapped key and the digest, and 3.8 records the upload event in the audit chain. "
     "The plaintext exists only in the browser part of the diagram, and the same decomposition applies to replacing file content, which reuses the existing file key."),
    ("uml", "UML class diagram", "06_uml_class.png",
     "UML class diagram: the four ORM classes (User, FileRecord, FilePermission, AuditLog) and the service and core modules that use them.",
     "The four ORM classes of backend/app/db/models.py carry the data. A User owns zero or more FileRecord objects and receives zero or more FilePermission objects; both relationships delete their children with the parent through the ORM cascade. "
     "A FileRecord holds the original and stored file names, the sizes, the IV, the owner's wrapped file key and the plaintext SHA-256, and has many FilePermission rows, each with a role of viewer or editor and the recipient's own wrapped key, unique per file and user. "
     "AuditLog rows refer to a user and a file by optional foreign keys declared with ON DELETE SET NULL and carry the previous_hash and current_hash fields. "
     "The behaviour is in plain modules rather than classes: permission_service (get_effective_role and the four can_ predicates), audit_service (record_event, verify_chain and the private _hash_event), core.security (bcrypt and JWT functions) and the Settings object, which reads the .env file. The global users.role column exists, but no decision uses it."),
    ("seq", "Sequence diagram of the main flow", "07_sequence_upload_share_download.png",
     "Sequence diagram of the main flow: owner uploads an encrypted file, shares it, and a recipient downloads it; an editor or viewer is refused deletion.",
     "Part A shows the upload. The owner's browser hashes and encrypts the file, wraps the key, and posts the multipart request; FastAPI validates it, writes the ciphertext object, inserts the files row and an audit entry, and answers 201 with metadata that contains no key material. "
     "Part B shows sharing. The browser fetches the recipient's public key, unwraps its own copy of the file key, wraps it again for the recipient and posts the 256-byte result with the chosen role; only the owner is accepted (HTTP 403 otherwise) and a file_permissions row is inserted. "
     "Part C shows the recipient's download: the role is resolved, the caller's wrapped key is read, the download is audited, and the ciphertext is returned with the IV, wrapped key and digest as headers. The recipient's browser unwraps, decrypts, checks the tag and the SHA-256 and then saves the file. "
     "The last pair of messages shows access control at work: a delete request from an editor or viewer is answered with 403 and logged as unauthorized_access."),
    ("usecase", "Use-case diagram", "08_use_case.png",
     "Use-case diagram: visitor, viewer, editor, owner and auditor actors with the twelve file use cases and the two audit use cases.",
     "A visitor can register, which generates the key pair in the browser, and sign in. Roles belong to files rather than to accounts: the viewer can unlock the vault, list files and download and decrypt; the editor inherits that and can also replace file content; the owner inherits both and can upload, share a file as viewer or editor, change a role, revoke access, delete the file and see its history. "
     "These rights follow the can_read, can_write, can_delete and can_share predicates of permission_service. The auditor is not a separate role: any signed-in user can view the vault-wide audit log and ask the server to verify the chain, which the limitations chapter records as a weakness. "
     "Every use case writes one hash-chained audit entry and a refused attempt is logged as unauthorized_access. There is no administrator role, no multi-factor authentication and no group or organisation concept in this build."),
    ("er", "Entity-relationship diagram", "09_er_diagram.png",
     "Entity-relationship diagram: users, files, file_permissions and audit_logs, with the ciphertext objects that the files table points to.",
     "The database has four tables created by SQLAlchemy from db/models.py. The users table holds the unique e-mail, the bcrypt hash, the public key, the sealed private-key bundle and its salt. "
     "The files table stores the owner as a foreign key, the original and unique stored file names, the MIME type, both sizes, the 12-byte IV in base64, the owner's wrapped file key and the plaintext SHA-256; the ciphertext itself lives in storage/encrypted under the stored name. "
     "The file_permissions table links a file and a user with the role and the recipient's wrapped key and has a unique constraint on the pair, so one user holds at most one role per file; revoking deletes the row and with it the server's copy of that key. "
     "The audit_logs table keeps the action, outcome, IP address, details and the two hash fields, with optional foreign keys to user and file. The hash chain is a convention of the application code: the database does not enforce it."),
    ("algo", "Flowchart of the core algorithm", "10_flowchart_encrypt_upload.png",
     "Flowchart of the core algorithm: encrypt and upload on the left, download, decrypt and verify on the right, with every rejection path.",
     "The left column follows uploadFile. The browser rejects an empty file or one above 25 MB, computes the SHA-256 digest, draws a random AES-256 file key and a 12-byte IV, encrypts with AES-256-GCM (the 16-byte tag is appended to the ciphertext), wraps the key with RSA-OAEP and posts the request. "
     "The server answers 401 for a bad token, 400 for an invalid IV, digest or base64 value and 413 above the size limit; otherwise it stores the ciphertext, inserts the row and writes the audit event. "
     "The right column follows fetchAndDecrypt. The server first resolves the caller's role and answers 403, logged as unauthorized_access, if there is none. The browser unwraps the file key with the private key and decrypts; a failed GCM tag stops the process with an error about a corrupt file or wrong key. "
     "Only when the SHA-256 of the plaintext equals the stored digest is the file saved, which gives two independent integrity checks: the authentication tag and the digest."),
    ("keyh", "Key hierarchy", "11_key_hierarchy.png",
     "Key hierarchy: password, PBKDF2 key, sealed RSA private key, wrapped per-file keys and what the server stores.",
     "Three layers of keys separate the password from the file data. The password is stretched with PBKDF2-HMAC-SHA-256 (120,000 iterations, 16-byte random salt) into an AES-256-GCM key that is never exported; this key encrypts the PKCS#8 private key, and the JSON bundle with salt, IV, ciphertext and iteration count is stored in the users table. "
     "The RSA-2048 public key (SPKI) is stored in clear because senders need it. Each file has its own random AES-256 file key, which encrypts the file with a fresh 12-byte IV and is stored only in wrapped form: RSA-OAEP with SHA-256 turns it into a 256-byte value for the owner (files.owner_wrapped_fek) and one per recipient (file_permissions.wrapped_fek). "
     "The login password is checked separately by bcrypt (cost 12) on the server. The server never holds the password, the private key or a file key in clear, which is the property the test suite and the measurements exercise. Losing the password means losing the private key, and therefore the files."),
    ("chain", "Audit hash chain", "12_audit_hash_chain.png",
     "Audit hash chain: each entry stores the previous entry's hash; verify_chain recomputes every hash; the measured weaknesses are noted.",
     "Every security-relevant event becomes an audit_logs row. The service reads the current_hash of the latest row (or the constant GENESIS for the first), hashes the string previous_hash, ISO timestamp, user id, file id, action, success flag and details with SHA-256, and stores the result as the new row's current_hash. "
     "verify_chain walks the rows in id order, checks that each previous_hash equals the preceding current_hash and recomputes each hash, returning the first failing id. In the measurements an edit of any field, a deleted middle entry, a swapped pair and an inserted forged entry were detected in every trial. "
     "Two weaknesses were also measured and are not hidden: removing entries from the end of the log is not detected (0 of 199), nor is a rewrite that recomputes all later hashes, because the chain has no secret key or external anchor. "
     "Concurrent writers can also fork the chain, since record_event reads the last hash and commits without a lock."),
]

BY_KEY = {d[0]: d for d in DIAGRAMS}
