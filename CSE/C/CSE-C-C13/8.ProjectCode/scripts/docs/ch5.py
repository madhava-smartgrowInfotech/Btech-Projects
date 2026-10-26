"""Chapter 5: System Design for CipherVault.

build_docs.doc12 renders blocks()[1:], so the first element must be the chapter H1.
Line counts are measured from the code at build time; diagrams are drawn by make_diagrams.py.
"""

import os

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .diagram_index import DIAGRAMS
from .refs import N as cite

_D = {k: (t, f, cap, txt) for k, t, f, cap, txt in DIAGRAMS}


def _lines(rel):
    path = os.path.join(F.CODE, rel)
    with open(path, encoding="utf-8", errors="ignore") as fh:
        return sum(1 for _ in fh)


def _tree_lines(rel, exts):
    total = 0
    for root, dirs, files in os.walk(os.path.join(F.CODE, rel)):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "dist", "__pycache__")]
        for f in files:
            if f.endswith(exts):
                with open(os.path.join(root, f), encoding="utf-8", errors="ignore") as fh:
                    total += sum(1 for _ in fh)
    return total


def _dg(key, width=5.6, text=True):
    """Diagram figure block (and its explanatory paragraph from diagram_index)."""
    t, f, cap, txt = _D[key]
    out = [FIG(F.diag(f), cap, width)]
    if text:
        if F.REPORT:   # report variant: the full explanation is in document 11; keep the first two sentences here
            import re as _re
            sents = _re.split(r"(?<=[.!?])\s+", txt.strip())
            txt = " ".join(sents[:1])
        out.append(P(txt))
    return out


def _shot(name, cap, base=5.0, mh=3.6):
    path = F.shot(name)
    return [FIG(path, cap, F.shot_w(path, base, mh))] if os.path.exists(path) else []


_DROP_P = ("The deliberate gaps", "Three decisions about this structure", "Every design has costs")
_DROP_TAB = ("Principal design decisions", "Pages of the web application")


def _trim(out):
    """Report variant: same 12 diagrams, but no design screenshots (Chapter 8 shows the screens) and fewer tables."""
    res = []
    for b in out:
        if b[0] == "p" and b[1].startswith(_DROP_P):
            continue
        if b[0] == "tab" and b[1].startswith(_DROP_TAB):
            continue
        if b[0] == "fig" and os.sep + "screenshots" + os.sep in b[1]:
            continue
        res.append(b)
    return res


def blocks():
    out = _blocks()
    return _trim(out) if F.REPORT else out


def _blocks():
    a, w = F.API_PORT, F.WEB_PORT

    mods = [
        ("`backend/app/main.py`", "backend/app/main.py", "Creates the FastAPI application, mounts the five routers, CORS for ports 8413 and 5413, the health and config routes and the single-page-app fallback"),
        ("`backend/app/core/config.py`", "backend/app/core/config.py", "Settings read from `.env` (database URL, JWT secret, token lifetime, upload limit, login throttle)"),
        ("`backend/app/core/security.py`", "backend/app/core/security.py", f"bcrypt hashing (cost {F.BCRYPT_COST}) and verification; JWT creation and decoding (HS256)"),
        ("`backend/app/db/database.py`", "backend/app/db/database.py", "SQLAlchemy engine, session dependency and table creation for SQLite or PostgreSQL"),
        ("`backend/app/db/models.py`", "backend/app/db/models.py", "ORM classes User, FileRecord, FilePermission and AuditLog"),
        ("`backend/app/schemas/schemas.py`", "backend/app/schemas/schemas.py", "Pydantic request and response models (registration, login, share, role change, audit)"),
        ("`backend/app/api/deps.py`", "backend/app/api/deps.py", "Current-user dependency (bearer token to user), client address, in-memory login throttle"),
        ("`backend/app/api/auth.py`", "backend/app/api/auth.py", "Register, login, current user, key update, key bundle, logout"),
        ("`backend/app/api/users.py`", "backend/app/api/users.py", "User directory search and public-key lookup used by sharing"),
        ("`backend/app/api/files.py`", "backend/app/api/files.py", "Upload, list, shared list, metadata, download, replace content, delete"),
        ("`backend/app/api/sharing.py`", "backend/app/api/sharing.py", "Share, list permissions, change role, revoke (owner only except listing)"),
        ("`backend/app/api/audit.py`", "backend/app/api/audit.py", "Audit list, per-file history, chain verification"),
        ("`backend/app/services/permission_service.py`", "backend/app/services/permission_service.py", "`get_effective_role` and the predicates `can_read`, `can_write`, `can_delete`, `can_share`"),
        ("`backend/app/services/audit_service.py`", "backend/app/services/audit_service.py", "`record_event` (append to the hash chain) and `verify_chain`"),
    ]
    mod_rows = [[n, str(_lines(rel)), d] for n, rel, d in mods]
    fe = [
        ("`frontend/src/lib/vaultCrypto.js`", "frontend/src/lib/vaultCrypto.js", "Web Crypto wrappers: key pairs, PBKDF2 key sealing, AES-256-GCM file encryption, RSA-OAEP key wrapping, SHA-256"),
        ("`frontend/src/lib/vault.js`", "frontend/src/lib/vault.js", "Upload, replace, fetch-and-decrypt and share, combining the API with the crypto module"),
        ("`frontend/src/lib/api.js`", "frontend/src/lib/api.js", "Fetch client, bearer token in `sessionStorage`, error type, one function per endpoint"),
        ("`frontend/src/lib/auth.jsx`", "frontend/src/lib/auth.jsx", "Authentication context: login, registration with key generation, unlock, lock, logout"),
        ("`frontend/src/features/UnlockGate.jsx`", "frontend/src/features/UnlockGate.jsx", "Unlock dialog that every key-needing action can await"),
        ("`frontend/src/features/ShareModal.jsx`", "frontend/src/features/ShareModal.jsx", "Share, change role and revoke dialog"),
        ("`frontend/src/features/useFileActions.jsx`", "frontend/src/features/useFileActions.jsx", "Upload, download, replace and delete actions with progress and error messages"),
        ("`frontend/src/features/VerifyChain.jsx`", "frontend/src/features/VerifyChain.jsx", "Audit chain verification control"),
    ]
    fe_rows = [[n, str(_lines(rel)), d] for n, rel, d in fe]
    pages_lines = _tree_lines("frontend/src/pages", (".jsx",))
    comp_lines = _tree_lines("frontend/src/components", (".jsx", ".js"))
    css_lines = _tree_lines("frontend/src/styles", (".css",))
    fe_rows.append(["`frontend/src/pages/` (8 pages)", f"{pages_lines:,}", "Landing, Auth (sign-in and register), Dashboard, Files (owned and shared), FileDetail, Audit, Security, NotFound"])
    fe_rows.append(["`frontend/src/components/`", f"{comp_lines:,}", "In-house UI kit, charts, motion helpers and the three.js landing scene"])
    fe_rows.append(["`frontend/src/styles/`", f"{css_lines:,}", "Design tokens, base, component and landing styles"])
    test_lines = _tree_lines("tests", (".py",))
    mod_rows.append(["`tests/`", str(test_lines), f"{F.PYTEST_TOTAL} pytest tests: auth 6, crypto 5, files 3, rbac 5, audit 2"])
    mod_rows.append(["`scripts/`", "-", "Measurement (`measure_metrics.py`), end-to-end and browser smoke tests, screenshot capture, demo seeding, evaluation"])

    routes = [
        ["GET", "/api/health", "-", "Liveness: status and application name", "-"],
        ["GET", "/api/config", "-", "Application name and upload limit (25 MB) for the interface", "-"],
        ["POST", "/api/auth/register", "-", "Create the account with the public key and the sealed private-key bundle; bcrypt hash of the password", "400 duplicate e-mail; 422 invalid fields"],
        ["POST", "/api/auth/login", "-", f"Check the password and return a JWT ({F.JWT_MINUTES} min); throttled", "401 wrong credentials; 429 throttle"],
        ["GET", "/api/auth/me", "JWT", "The signed-in user (never the password hash)", "401"],
        ["PUT", "/api/auth/keys", "JWT", "Replace the public key and the sealed private-key bundle", "401; 422"],
        ["GET", "/api/auth/key-bundle", "JWT", "The caller's own sealed private-key bundle", "404 none stored"],
        ["POST", "/api/auth/logout", "JWT", "Write the logout event (the token itself is not revoked)", "401"],
        ["GET", "/api/users?q=", "JWT", "Search active users by name or e-mail (at most 50)", "401"],
        ["GET", "/api/users/{id}/public-key", "JWT", "Public key of one user, used to wrap a file key for them", "404"],
        ["POST", "/api/files/upload", "JWT", "Multipart upload of ciphertext, IV, wrapped key, digest and metadata; stores the object under a random name", "400 empty, bad IV, digest or name; 413 over 25 MB"],
        ["GET", "/api/files", "JWT", "Files the caller owns, newest first", "401"],
        ["GET", "/api/files/shared", "JWT", "Files shared with the caller, with the effective role", "401"],
        ["GET", "/api/files/{id}", "Any role", "Metadata, IV and the caller's own wrapped key", "403 no role (logged); 404"],
        ["GET", "/api/files/{id}/download", "Any role", "Ciphertext with IV, wrapped key and digest in headers; writes a download event", "403 (logged); 404 missing object"],
        ["PUT", "/api/files/{id}", "Owner, Editor", "Replace the ciphertext, IV and digest; the owner may also replace the wrapped key", "403 (logged); 400; 413"],
        ["DELETE", "/api/files/{id}", "Owner", "Delete the ciphertext object and the rows", "403 (logged); 404"],
        ["POST", "/api/files/{id}/share", "Owner", "Grant Viewer or Editor with the recipient's wrapped key (must be 256 bytes)", "403; 404 user; 400 invalid; 409 already shared"],
        ["GET", "/api/files/{id}/permissions", "Any role", "Owner and every grantee with role", "403 (logged); 404"],
        ["PUT", "/api/files/{id}/permissions/{uid}", "Owner", "Change a grantee's role to viewer or editor", "403; 404"],
        ["DELETE", "/api/files/{id}/permissions/{uid}", "Owner", "Revoke: delete the grant and the stored wrapped key", "403; 404"],
        ["GET", "/api/audit?limit=", "JWT", "Newest audit entries (limit up to 500), optionally filtered by action", "422 limit above 500"],
        ["GET", "/api/audit/file/{id}", "Owner", "Audit history of one file", "403 not owner"],
        ["GET", "/api/audit/verify", "JWT", "Recompute the chain; returns validity, count and first failing id; logs the verification", "401"],
    ]

    tables = [
        ["users", "id PK; name; email UNIQUE; password_hash; role (default 'user', unused); public_key (base64 SPKI); encrypted_private_key (JSON bundle); private_key_salt; is_active; created_at; updated_at",
         "One row per account. The server never holds the password or an unsealed private key"],
        ["files", "id PK; owner_id FK users; original_filename; stored_filename UNIQUE (random 32 hex characters); mime_type; encrypted_size; original_size; iv (base64, 12 bytes); owner_wrapped_fek; plaintext_sha256; created_at; updated_at",
         "Metadata and the owner's wrapped key; the ciphertext lives in `storage/encrypted`. Index on (owner_id, created_at)"],
        ["file_permissions", "id PK; file_id FK files; user_id FK users; role ('viewer' or 'editor'); wrapped_fek; created_at; updated_at",
         "One row per grantee; UNIQUE (file_id, user_id). Deleting the row deletes the grantee's wrapped key"],
        ["audit_logs", "id PK; timestamp_utc; user_id FK users (nullable, SET NULL); file_id FK files (nullable, SET NULL); action; success; ip_address; details (at most 2,000 characters); previous_hash; current_hash",
         "Append-only by convention; indexes on timestamp, user, file, action and (file_id, timestamp_utc)"],
    ]

    pages = [
        ["Landing", "/", "GET /api/health, /api/config", "Product page with the three.js hero scene and the security model"],
        ["Sign in / Register", "/login, /register", "POST /api/auth/login, /api/auth/register; GET /api/auth/key-bundle, /me", "Key generation at registration, vault unlock at sign-in, one-click demo accounts"],
        ["Dashboard", "/app", "GET /api/files, /api/files/shared, /api/audit", "Counters, security events per day, access by role, recent activity, security status"],
        ["My files, Shared with me", "/app/files, /app/shared", "GET /api/files, /api/files/shared, /api/config", "Drop-zone upload with progress, file table with role badges"],
        ["File detail", "/app/files/:id", "GET /api/files/{id}, /permissions, /audit/file/{id}; download, replace, delete, share", "Details, access list, history, decrypt and download"],
        ["Audit log", "/app/audit", "GET /api/audit, /api/audit/verify", "Filterable event table and chain verification"],
        ["Security", "/app/security", "(client state)", "Account details, key status, lock and sign out"],
    ]

    decisions = [
        ["Encrypt in the browser, not on the server", "Server-side encryption with a master key", "The server then holds no key that opens a file", "Password loss means data loss; the delivered JavaScript is trusted"],
        ["One random AES-256-GCM key per file, wrapped per recipient", "One key per user, or proxy re-encryption", "Sharing re-wraps 32 bytes instead of re-encrypting the file; revocation deletes one row", "No re-keying on revoke; downloaded keys cannot be recalled"],
        ["RSA-2048-OAEP with SHA-256 for key wrapping", "Elliptic-curve or hybrid key encapsulation", "Natively supported by Web Crypto in every current browser; 256-byte outputs are easy to validate", "Larger keys and slower key generation than curves"],
        ["Password-sealed private key stored on the server", "Key kept only on the device, or hardware token", "The same account works from any browser; the server stores only a sealed bundle", f"Offline guessing of a weak password is limited only by PBKDF2 ({F.PBKDF2_ITER:,} iterations)"],
        ["Roles per file (Owner, Editor, Viewer)", "Account-wide roles or attribute policies", "Matches how files are shared; three roles are easy to verify exhaustively", "No groups, no inheritance, no administrator"],
        ["Hash-chained audit log in the same database", "Signed log shipped to external storage", "Needs no extra service and makes edits, deletions and insertions detectable", "No secret key or anchor: tail truncation and a full rewrite are not detected"],
        ["Whole-file encryption with a 25 MB limit", "Chunked streaming encryption", "A single GCM operation is simple and has one tag and one IV to check", "Memory use grows with file size; no resumable upload"],
        ["SQLite by default, PostgreSQL by configuration", "PostgreSQL only", "Zero-setup local deployment", "Single-writer assumptions in the audit service; PostgreSQL path untested"],
    ]

    out = [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter describes how CipherVault is put together: the architecture and workflow, the data flow, the UML and data design, the cryptographic design, the modules, the API and the user interface. "
          "The diagrams were drawn from the code in `backend/app` and `frontend/src`; the complete set, each with a longer explanation, is also in the Block Diagrams document. "
          "A note on scope: the product is a single-organisation file vault with three roles. It has no groups, no administrator console, no multi-factor authentication and no chunked transfer, and these absences are design choices that the sections below explain rather than hide."),

        H2("5.1 Design goals and architecture"),
        P("Five goals shaped the design. First, **confidentiality against the server**: the server must be able to store, authorise and audit files without ever being able to read them. "
          "Second, **least privilege per file**: a person's rights are attached to each file as Owner, Editor or Viewer and are checked on the server for every request, never trusted from the client. "
          "Third, **integrity visible to the user**: a downloaded file is accepted only if both the AES-GCM tag and the stored SHA-256 verify. "
          "Fourth, **accountability**: every sensitive action, including refused ones, leaves a hash-chained audit entry. "
          f"Fifth, **small and standard parts**: the cryptography is composed from the primitives of the Web Crypto API {cite('webcrypto')} and the server uses a conventional stack, so the design can be reviewed in full."),
        *_dg("arch", 5.7),
        P(f"In development the React application is served by Vite on port {w} and the Vite proxy forwards every `/api` request to the FastAPI application on 127.0.0.1:{a}; after `npm run build` the same FastAPI process serves `frontend/dist`, "
          "with a fallback route that returns `index.html` for any path that is not an API route or an asset, so the browser sees one origin. CORS is nevertheless enabled for the two local ports. "
          "Configuration comes from the environment (`.env`), and the database is chosen by one URL, so SQLite for a local run and PostgreSQL for the Docker deployment need no code change."),
        P("The deliberate gaps in this architecture are worth stating. There is no job queue and no background worker: every request is handled inside the request. "
          "There is no server-side session store: a JWT is valid until it expires (the logout route only writes an audit event). "
          "The login throttle lives in process memory, so it is reset by a restart and is not shared between several worker processes. "
          "The storage layer is a directory of files named by random 32-hex-character strings, which keeps original names out of the file system but also means that integrity of the folder depends on the operating system."),

        H2("5.2 High-level workflow"),
        *_dg("flow", 5.7),
        P("Two properties of the workflow drive the rest of the design. The first is that every step that touches file content or key material happens in the browser, and the server's role is limited to validation, storage, authorisation and logging. "
          "The second is that sharing is an operation on keys, not on files: the owner's browser unwraps its copy of the file key, wraps it for the recipient and posts the 256-byte result. "
          "The server cannot perform this step itself, which is why a recipient who has not registered cannot be given access and why an owner who is locked out of their own vault cannot share."),

        H2("5.3 Data flow diagrams"),
        H3("5.3.1 Level 0: context"),
        *_dg("dfd0", 5.4),
        H3("5.3.2 Level 1: five processes"),
        *_dg("dfd1", 5.7),
        P("The split follows the routers of the application: authentication, sharing, upload, retrieval and audit. Process 5.0 is the only writer of the audit store, and it is called by all the others, which is why in most routes the audit entry is written after the request's main effect has been committed (the delete route records first and then removes the file), so a failure between the two steps can leave an effect without an entry; this is one reason the chain is described as evidence, not proof."),
        H3("5.3.3 Level 2: encrypt and store a file"),
        *_dg("dfd2", 5.7),

        H2("5.4 UML design"),
        H3("5.4.1 Class diagram"),
        *_dg("uml", 5.7),
        P("The data classes are ordinary SQLAlchemy models, and behaviour lives in two small service modules rather than in the classes. This keeps the access rules in one place (`permission_service.py`, 35 lines) where they can be read and tested exhaustively, and keeps the hashing rule of the audit chain in one function (`_hash_event`) shared by the writer and the verifier."),
        H3("5.4.2 Sequence diagram"),
        *_dg("seq", 5.7),
        H3("5.4.3 Use-case diagram"),
        *_dg("usecase", 5.5),

        H2("5.5 Database design"),
        *_dg("er", 5.5),
        TAB("Tables of the database", ["Table", "Columns", "Notes"], tables, widths=[1.0, 3.6, 1.9], align=["l", "l", "l"], size=8.8),
        P("Four design points deserve mention. Keys are stored only in wrapped form: `files.owner_wrapped_fek` and `file_permissions.wrapped_fek` are RSA-OAEP outputs, so a database dump contains no usable file key without the users' private keys. "
          "Deleting a file removes its permission rows through the ORM cascade, which removes every grantee's wrapped key together with the file. "
          "The audit table keeps nullable foreign keys with `ON DELETE SET NULL`, so history survives the deletion of a file or a user. "
          "Finally, the original file name is stored in clear in the files table (the stored object name is random), because the interface must list files; file names, sizes, MIME types, owners and timestamps are therefore visible to anyone with database access."),

        H2("5.6 Core algorithm and cryptographic design"),
        *_dg("algo", 5.7),
        *_dg("keyh", 5.7),
        P(f"The key hierarchy follows the usual hybrid pattern {cite('kamara')}: a slow password-based step protects the long-term private key, a public-key step distributes per-file keys, and a fast symmetric step protects the data. "
          f"PBKDF2-HMAC-SHA-256 with {F.PBKDF2_ITER:,} iterations and a 16-byte random salt derives the sealing key {cite('pbkdf2', 'sp800132')}; AES-256-GCM with a fresh 12-byte IV encrypts and authenticates the file {cite('gcm')}; and RSA-OAEP with SHA-256 wraps the 32-byte file key into a 256-byte value {cite('oaep')}. "
          f"The login password is verified separately with bcrypt at cost {F.BCRYPT_COST} {cite('bcrypt')} and plays no part in the key path. The iteration count is lower than the 310,000 that the closest-architecture paper reports {cite('ijedr')} and is a measured trade-off: one derivation took a median of {F.ms(F.CRY['pbkdf2_120k']['median'])} ms."),
        *_dg("chain", 5.7),
        P(f"The audit design follows the idea of a forward-linked secure log {cite('audit99', 'tamper09')} in its simplest form: each entry commits to its predecessor, so changing or removing an entry in the middle breaks every later link. "
          "The design stops there. It uses no key and no external anchor, which is why it cannot detect truncation of the newest entries or a complete rewrite, and the service reads the last hash and commits without a lock, which is why concurrent writers fork the chain. "
          "These two properties were measured rather than assumed (Chapter 8), and the corresponding improvements are a keyed or signed chain, periodic anchoring outside the database, and a lock or sequence number on the write path."),

        H2("5.7 Module design"),
        TAB("Backend modules, sizes and responsibilities", ["Module", "Lines", "Responsibility"], mod_rows, widths=[2.3, 0.55, 3.65], align=["l", "r", "l"], size=8.8),
        TAB("Front-end modules, sizes and responsibilities", ["Module", "Lines", "Responsibility"], fe_rows, widths=[2.3, 0.55, 3.65], align=["l", "r", "l"], size=8.8),
        P(f"In total the backend has {F.LOC['backend_py']['lines']:,} lines in {F.LOC['backend_py']['files']} Python files, the tests {F.LOC['tests_py']['lines']} lines in {F.LOC['tests_py']['files']} files and the front end {F.LOC['frontend_src']['lines']:,} lines in {F.LOC['frontend_src']['files']} source files. "
          "The routers are thin: they validate input, call the permission service, write the file or row, and record an audit event. All cryptography on file contents is in `vaultCrypto.js`, which is the only module that calls `crypto.subtle`; the other front-end modules pass it buffers and keys. "
          "This separation is what allows the server-side tests to treat the ciphertext as opaque bytes and the browser tests to exercise the same functions the interface uses."),

        H2("5.8 API design"),
        P("The API is a JSON and multipart REST interface under `/api`. There are 24 endpoints; all except the four public ones (health, config, register and login) require a bearer token, and every file operation additionally resolves the caller's effective role on the file. "
          "File content travels as multipart form data (`ciphertext` plus text fields), and the download returns the ciphertext as `application/octet-stream` with the IV, the caller's wrapped key, the digest, the file name and the MIME type in `X-CipherVault-*` response headers, which the CORS configuration exposes to the browser."),
        TAB("The 24 endpoints of the CipherVault API", ["Method", "Path", "Access", "Purpose", "Errors"], routes, widths=[0.6, 1.5, 0.75, 2.45, 1.2], align=["c", "l", "l", "l", "l"], size=8),
        P("Error behaviour is part of the design. A caller without a role on a file receives HTTP 403, not 404, for an existing file, and the refusal is logged as `unauthorized_access`; a request for a file id that does not exist receives 404. "
          "Responses never contain key material other than the caller's own wrapped key, the caller's own sealed private-key bundle and the public keys that sharing needs. Validation is strict where the server can check it without decrypting: the IV must decode to 12 bytes, the digest must be 64 hexadecimal characters, a wrapped key accepted by the share route must decode to exactly 256 bytes, and the ciphertext may not exceed the size limit."),

        H2("5.9 User interface design"),
        P("The interface is a React single-page application with a dark and a light theme (the saved choice, otherwise the system preference), reduced-motion support and layouts that were checked down to 360 px. "
          "Its structure mirrors the security model: the sidebar offers the dashboard, the user's own files, the files shared with the user, the audit log and the security profile, and a status chip at the top of every page shows whether the vault is unlocked. "
          "If an action needs the private key while the vault is locked, the unlock dialog opens and the action resumes after the password is accepted."),
        TAB("Pages of the web application", ["Page", "Route", "Endpoints used", "Purpose"], pages, widths=[1.2, 1.1, 2.2, 2.0], align=["l", "l", "l", "l"], size=8.8),
        *_shot("04_sign-in.png", "Sign-in page of CipherVault (1440 x 900): the password both authenticates the user and unlocks the private key.", 4.8, 3.4),
        *_shot("07_my-files.png", "The My files page with synthetic demo files, role badges and the encrypted-upload drop zone.", 4.8, 3.4),
        P("Design choices in the interface follow the security model. Role badges and the access list make the effective role visible before an action is attempted; destructive actions (delete, revoke) ask for confirmation; error messages say what failed (for example that the AES-GCM tag or the SHA-256 digest did not verify) without suggesting that a corrupt file was saved; "
          "and the demo-login buttons create three fictional accounts (owner, editor and viewer at `example.com`) with synthetic files so that the role rules can be seen without real data."),

        H2("5.10 Design decisions and trade-offs"),
        P("The table below records the principal decisions with the alternative that was not taken, the reason, and the cost that the decision brought. The costs are the same limitations that Chapters 8 and 9 report from measurement."),
        TAB("Principal design decisions", ["Decision", "Alternative", "Reason", "Cost"], decisions, widths=[1.5, 1.3, 1.9, 1.8], align=["l", "l", "l", "l"], size=8.5),
        P("Every design has costs, and this one is no exception. The strongest property of CipherVault, that the server cannot read files, is also the source of its two hardest user-facing limits: a lost password cannot be recovered, and revocation cannot undo what a recipient already holds. "
          f"The comparison with the base paper {cite('base')} is therefore one of different trade-offs, not of a better scheme: attribute-based encryption gives policy-based access without a per-recipient key list, at the price of heavier infrastructure, while CipherVault accepts a per-recipient wrapped key to keep the system small and measurable."),
    ]
    return out
