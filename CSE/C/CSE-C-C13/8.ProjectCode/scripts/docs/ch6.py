"""Chapter 6: Methodology and Software Implementation for CipherVault.

methodology_blocks() is also rendered (renumbered) by document 9, application_blocks() by document 12; blocks() is the report chapter.
Numbers come from facts.py (docs/metrics/metrics.json, tests.json); formulas and code are exactly what backend/app and
frontend/src/lib compute. CipherVault trains no model and uses no dataset: "model architecture and training" is the cryptographic
design (Section 6.6) and its configuration parameters (Section 6.7).
"""

import os

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from .diagram_index import DIAGRAMS
from .refs import N as cite

_D = {k: (t, f, cap) for k, t, f, cap, _ in DIAGRAMS}


def _dg(key, caption=None, width=5.4):
    t, f, cap = _D[key]
    path = F.diag(f)
    return [FIG(path, caption or cap, width)] if os.path.exists(path) else []


def _fg(name, caption, width=5.6):
    path = F.fig(name)
    return [FIG(path, caption, width)] if os.path.exists(path) else []


def _a(size, op, stat="median"):
    return F.AES[str(size)][op][stat]


def _size(n):
    return {1024: "1 KiB", 65536: "64 KiB", 1048576: "1 MiB", 10485760: "10 MiB", 26214400: "25 MiB"}[n]


def _prim_rows():
    sizes = (1024, 1048576, 10485760, 26214400)
    rows = [[lab] + [f"{F.ms(_a(s, op))} ({F.ms(_a(s, op, 'p95'))})" for s in sizes]
            for lab, op in (("AES-256-GCM encrypt", "encrypt"), ("AES-256-GCM decrypt", "decrypt"), ("SHA-256 digest", "sha256"))]
    rows.append(["Ciphertext overhead (bytes)"] + [str(F.AES[str(s)]["overhead"]) for s in sizes])
    return rows


def methodology_blocks():
    cry, api = F.CRY, F.API
    api0 = F.API
    b = []

    # ------------------------------------------------------------------ 6.1
    b += [H2("6.1 Overall methodology"),
          P(f"CipherVault is built by the following method: decide who must be trusted with which secret, give each secret to exactly that party, express the decision in a small number of standard primitives, and then measure what the decision costs and what it still fails to protect. "
            f"The base paper {cite('base')} solves a related problem for health records with attribute-based encryption, a permissioned blockchain and a language model that extracts attributes from clinical notes, and evaluates it by calculation from primitive timings. "
            f"The closest architecture in the literature, the cloud file store of Sowmiya et al. {cite('ijedr')}, uses client-side AES, RSA key management, role-based access control and a signed audit log, and reports an evaluation with 50 users in three roles. "
            "CipherVault keeps the shared aim (the storage provider never holds readable content, access is role-based and every action is recorded) and replaces the heavy machinery by a design that one browser, one small server and a standard library can run. "
            "No model is trained, so the methodology is a protocol design plus a measurement protocol. The protocol has eight steps."),
          N("**Register.** The browser generates an RSA-2048 key pair, derives a key-encryption key from the password with PBKDF2, seals the private key with AES-256-GCM and sends the public key, the sealed bundle and the password; the server stores a bcrypt hash, not the password.",
            "**Authenticate.** The server checks the bcrypt hash, applies the login throttle, issues a JWT valid for 120 minutes and records the event; the browser fetches the sealed bundle and unlocks the private key in memory.",
            "**Encrypt and upload.** The browser hashes the file with SHA-256, draws a random 256-bit file key and a 12-byte IV, encrypts with AES-256-GCM, wraps the file key with the owner's public key and uploads ciphertext, IV, wrapped key and digest.",
            "**Store.** The server validates the fields, writes the ciphertext under a random 32-hex name, inserts one metadata row and appends an audit entry.",
            "**Share.** The owner's browser unwraps the file key, wraps it again for the recipient's public key and posts the result with the role (viewer or editor); the server stores it in a permission row.",
            "**Retrieve.** The server resolves the caller's role, returns the ciphertext with the IV, the caller's own wrapped key and the digest, and audits the download; the browser unwraps, decrypts, checks the AES-GCM tag and compares the SHA-256 before saving.",
            "**Account.** Every sensitive action, success or refusal, appends an entry to a hash chain; any signed-in user can ask the server to recompute the chain.",
            "**Measure.** Time every primitive in the browser, every endpoint over loopback and the whole pipeline end to end; test the access matrix, forged tokens and tampering on the live system; record what fails (Chapters 7 and 8).")]

    # ------------------------------------------------------------------ 6.2
    b += [H2("6.2 Dataset"),
          P("CipherVault uses no dataset in the machine-learning sense. A file store has no training data, no labels and no train-test split, and for that reason it has no accuracy, precision or F1 to report. "
            "Two kinds of data appear in this work, and both are synthetic. The first is the **demo data**: three fictional accounts and five small files created by the one-click demonstration login (`frontend/src/lib/demo.js`) through the normal API and the normal browser encryption, so that every screen of the application can be shown with real, populated records. "
            "The second is the **measurement workload**: random byte strings of fixed sizes and throw-away accounts created by `scripts/measure_metrics.py` on a scratch database, so that no figure depends on the content of a file."),
          TAB("Data used in this work.",
              ["Item", "What it is", "Size and origin"],
              [["Demo accounts", "owner@example.com, editor@example.com and viewer@example.com, with fictional names", "3 accounts; real RSA-2048 key pairs generated in the browser; example.com is a reserved documentation domain"],
               ["Demo files", "Q3-board-memo.txt, regional-revenue.csv, api-credentials.json, employee-handbook-draft.md, design-review-notes.txt", "5 small synthetic text files; shared as editor or viewer in the pattern defined in demo.js"],
               ["Crypto timing workload", "Random buffers encrypted, decrypted and hashed by the browser's Web Crypto API", "1 KiB, 64 KiB, 1 MiB, 10 MiB and 25 MiB; 50 to 4 repetitions per size"],
               ["Pipeline workload", "Encrypted and plain upload and download of random buffers from the browser to the same endpoint", "1 KiB (30 reps), 1 MiB (20 reps) and 10 MiB (15 reps)"],
               ["API workload", "Upload and download of random ciphertext of fixed sizes through the REST API", "1 KiB to 25 MiB less 2 KiB; 20 to 3 repetitions"],
               ["Access-control workload", "One file, four principals (owner, editor, viewer, stranger), nine operations", "36 cells, each compared with the expected decision"],
               ["Audit workload", f"The hash chain of the measurement database, copied and altered in nine ways; chains of up to {max(int(k) for k in F.SCALE)} entries", f"{F.TAMPER['audit_entries_available']} entries available for the tamper study; 199 to 200 trials per class"],
               ["Training data", "None: no model is trained or fine-tuned", "-"]],
              widths=[1.35, 2.85, 2.3], align=["l", "l", "l"], size=9.5),
          P("Three properties of this data shape every result. The files are small and random, so a figure describes the cost of the cryptography and of the server and says nothing about a user's real documents, whose compressibility, type or sensitivity has no effect on the timing. "
            "The user population is three fictional accounts, so no result describes behaviour with many users. And the host was an ordinary desktop that other jobs were also using, so all timings are indicative and are reported with their 95th percentiles; the values and their spread are discussed in Chapter 8. "
            f"The base paper {cite('base')} likewise reports no dataset and no extraction accuracy for its language-model step, and the paper of Sowmiya et al. {cite('ijedr')} describes a 50-user evaluation without giving its data, so neither provides numbers that can be re-computed here.")]

    # ------------------------------------------------------------------ 6.3
    b += [H2("6.3 Preprocessing"),
          P("In a file store, preprocessing is everything that happens to a file in the browser before a single byte leaves it, plus the validation that the server applies to what arrives. The client part is in `frontend/src/lib/vault.js` (`uploadFile`) and is the same for the demonstration, the tests and the real interface."),
          H3("6.3.1 Client-side steps"),
          N("**Size and emptiness check.** The browser reads `max_upload_mb` from `/api/config` and refuses a file larger than 25 MB or of zero bytes before any cryptography runs.",
            "**Read.** The whole file is read into one `ArrayBuffer`; there is no chunking, which is why the size limit exists (Section 6.11).",
            "**Digest.** `crypto.subtle.digest('SHA-256')` over the plaintext gives a 64-character hexadecimal string.",
            "**File key.** `generateKey` creates a random 256-bit AES-GCM key, the file-encryption key (FEK), for this file only.",
            "**Encryption.** `crypto.getRandomValues` draws a 12-byte IV and `encrypt` returns the ciphertext with the 16-byte tag appended, so the stored object is exactly 16 bytes longer than the plaintext in every size measured.",
            "**Wrapping.** `wrapKey('raw', ...)` encrypts the FEK with the owner's RSA-OAEP public key; the result is always 256 bytes.",
            "**Packaging.** The ciphertext goes into a `FormData` part named `ciphertext` (media type `application/octet-stream`) together with the original file name, MIME type, original size, IV (base64), wrapped FEK (base64) and digest."),
          H3("6.3.2 Server-side validation"),
          P("The server cannot inspect the plaintext, so its validation is structural: the ciphertext must be non-empty and at most 25 MB plus 1 KiB; the file name must be non-empty and at most 512 characters; the original size must lie between 0 and the limit; the IV must be valid base64 that decodes to exactly 12 bytes; the wrapped key must be valid, non-empty base64 of at most 5,000 characters; and the digest must match `^[0-9a-fA-F]{64}$`. "
            "A request that fails any rule is answered with HTTP 400 (HTTP 413 for the size) before anything is written. The server then replaces the client's name by a random 32-hex-digit `stored_filename` (`secrets.token_hex(16)`), so a file's original name never reaches the filesystem, and stores the digest in lower case. "
            "What the server cannot check is that the ciphertext really is AES-GCM output under the wrapped key: a client could upload arbitrary bytes. That is harmless to confidentiality, and it is caught at download time, because the AES-GCM tag then fails to verify in the recipient's browser."),
          ]
    if not F.REPORT:
        b += [H3("6.3.3 The download side"),
          P("Retrieval inverts the steps: fetch the metadata, unwrap the FEK with the private key, decrypt the ciphertext (a bad tag raises an error and nothing is saved), recompute SHA-256 over the plaintext and compare it with the stored digest, and only then offer the bytes to the browser as a download. "
            "The two checks are deliberately redundant: the tag authenticates the ciphertext under the key, and the digest, which the server stores, additionally ties the plaintext to the value recorded at upload time.")]

    # ------------------------------------------------------------------ 6.4
    b += [H2("6.4 Algorithm choice and justification"),
          P("Every primitive in CipherVault is one that the W3C Web Cryptography API " + cite("webcrypto") + " provides natively in the browser, with a standard behind it. This was the main selection rule: cryptographic code written in JavaScript by the project, or pulled from a library, would be both slower and harder to trust than the browser's own implementation. the table below gives the choices and the reasons; the alternatives are those named in the literature survey (Chapter 2)."),
          TAB("Algorithm choices and the reasons for them.",
              ["Purpose", "Choice and parameters", "Why this choice", "Alternative considered"],
              [["File encryption", f"AES-256-GCM {cite('gcm', 'aes')}; random 256-bit key per file, random 96-bit IV, 128-bit tag", "Confidentiality and integrity in one operation; native and fast in Web Crypto", "Attribute-based encryption " + cite("abe06", "cpabe") + ": finer policies but pairing arithmetic and no browser support"],
               ["Key wrapping", f"RSA-2048 with OAEP, SHA-256 and MGF1 {cite('oaep', 'oaep94')}; public exponent 65537; 256-byte output", "A key can be given to a user who is offline; the server needs the public key only", "Proxy re-encryption " + cite("pre06") + ": no re-wrapping by the owner, but not in Web Crypto"],
               ["Protection of the private key", f"PBKDF2-HMAC-SHA-256 {cite('pbkdf2', 'sp800132')}, 120,000 iterations, 16-byte salt, 256-bit AES-GCM key", "The only password-based KDF in Web Crypto; the iteration count is stored in the bundle", f"310,000 iterations in {cite('ijedr')}; scrypt and Argon2 are not available in Web Crypto"],
               ["Integrity digest", f"SHA-256 {cite('sha')} of the plaintext, stored as 64 hex digits", "Second check on the decrypted bytes; computed natively", "Digital signature (ECDSA) over the file: stronger, not implemented"],
               ["Password storage", f"bcrypt {cite('bcrypt')}, cost factor {F.BCRYPT_COST}, per-hash salt", f"Deliberately slow; measured at a median of {F.ms(api0['login_ms']['median'])} ms per login", "Argon2: not used"],
               ["Session token", f"JWT {cite('jwt')}, HS256, claims sub, iat and exp, lifetime {F.JWT_MINUTES} minutes", "Stateless; expiry is checked on every request", "Server-side sessions: allow revocation, need a store"],
               ["Access control", f"Role-based, per file: owner, editor, viewer {cite('rbac96', 'rbac01')}", "Three roles are enough for the stated use and are easy to audit", "ABE policies: heavier administration"],
               ["Audit trail", f"SHA-256 hash chain in the application database {cite('audit99', 'tamper09')}", "Detects edits, deletions, reorderings and insertions without a key", "Signed entries or an external anchor: not implemented (Section 6.5)"]],
              widths=[1.0, 2.0, 1.8, 1.7], align=["l", "l", "l", "l"], size=9),
          P("Two choices deserve a longer justification. **Why RSA key wrapping and not a password-derived file key?** If a file key were derived from the owner's password, sharing would require sharing the password. With a random file key wrapped under each recipient's public key, the owner can add and remove readers independently, and the cost of sharing is one RSA operation: "
            f"wrapping took a median of {F.ms(cry['rsa_wrap']['median'])} ms and unwrapping {F.ms(cry['rsa_unwrap']['median'])} ms in the measurements, so the number of recipients does not matter for speed. "
            "**Why one key per file and not one key per user?** A per-user key would mean that giving one file to a colleague gives every file. A per-file key limits the exposure of any wrapped key to one file and also limits the number of encryptions under one key, which matters for the nonce bound in Section 6.5."),
          P("The choices also have costs that are stated rather than hidden. The same password is sent to the server for the bcrypt check and used in the browser to derive the key that opens the private-key bundle, which the server also stores. A server that logs the password at login time could therefore open the bundle and decrypt every file the user can reach; "
            "protection against a passive thief of the database or of the storage directory holds, protection against an actively malicious server does not. The digest is stored in the clear and is unsalted, so a server can test whether a known file is stored (confirmation of a file), though it cannot read an unknown one. "
            "And 120,000 PBKDF2 iterations is lower than the 310,000 of Sowmiya et al. " + cite("ijedr") + ", so an attacker who obtains the key bundle can test passwords faster.")]

    # ------------------------------------------------------------------ 6.5
    b += [H2("6.5 Mathematical formulation"),
          P("The formulas below are exactly what the code computes; the symbols are P for plaintext, K_f for the 256-bit file key, IV for the 96-bit nonce, pk_u and sk_u for the RSA key pair of user u, and || for concatenation."),
          H3("6.5.1 File encryption and integrity"),
          P("AES-GCM encrypts and authenticates in one operation and the Web Crypto API appends the 128-bit tag to the ciphertext, so the object stored on the server has length |P| + 16 bytes:"),
          EQ("C || T = AES-GCM-Enc(K_f, IV, P),   |T| = 128 bits,   |C || T| = |P| + 16 bytes"),
          P("Decryption either returns P or fails when the tag does not verify. CipherVault accepts a download only if, in addition, the digest of the recovered bytes equals the digest recorded at upload:"),
          EQ("accept  ⇔  AES-GCM-Dec(K_f, IV, C || T) ≠ ⊥   and   SHA-256(P) = d"),
          P("Both conditions held for every honest transfer in the tests, and the tag check rejected every one of 2,000 randomly placed single-bit changes in a ciphertext (Chapter 7; run with the same AES-GCM primitive in Python). "
            "The IV is drawn at random, so two encryptions under the same key collide with probability at most q(q-1)/2 · 2^-96, about q² / 2^97, after q encryptions. NIST SP 800-38D " + cite("gcm") + " limits random-IV use to 2^32 invocations per key, for which the bound is 2^-33. "
            "A key is used once at upload and then once for each content replacement by the owner or an editor, so a file would need billions of replacements to approach the limit; the weakness of reusing one key is noted in Chapter 9 because an editor's update draws a fresh IV but keeps the file key."),
          H3("6.5.2 Key wrapping and key protection"),
          EQ("W_u = RSA-OAEP-Enc(pk_u, K_f; SHA-256, MGF1-SHA-256),   |W_u| = 256 bytes"),
          EQ("KEK = PBKDF2-HMAC-SHA-256(password, salt, 120,000, 256 bits);   bundle = AES-GCM-Enc(KEK, IV_b, sk_u)"),
          P("The first formula is evaluated once for the owner at upload and once for every recipient at sharing; the second is evaluated when a vault is created and every time it is unlocked, and costs about 33 ms at the median measured here, which is the price of one unlock."),
          H3("6.5.3 The audit hash chain"),
          P("Each audit entry i carries the hash of the previous entry and its own hash. With h_0 the constant GENESIS and (t_i, u_i, f_i, a_i, s_i, d_i) the time stamp, user, file, action, success flag and details of entry i:"),
          EQ("h_i = SHA-256( h_{i-1} | t_i | u_i | f_i | a_i | s_i | d_i )   (fields joined by the character |)"),
          P("Verification walks the entries in order of identifier, recomputes each hash and compares it with the stored one, and compares each stored previous hash with the hash of its predecessor. Changing any field of entry j, deleting or inserting an entry, or swapping two entries makes the walk fail at or after j. "
            "The scheme has no secret: anyone who can write to the database can recompute every later hash after an edit, and cutting off the last entries leaves a shorter chain that still verifies. Both gaps were measured and are reported in Chapter 7 (0 of 199 truncations detected, and a full re-hash not detected). "
            "The verification cost grows linearly with the length n of the chain, O(n) hash computations."),
          H3("6.5.4 The access-control predicate"),
          P("The effective role of user u on file f is owner if u owns f, otherwise the role stored in the permission row of (f, u), otherwise none. Four predicates then decide every operation; they are the functions in `permission_service.py`:"),
          EQ("read(r) = r ∈ {owner, editor, viewer};   write(r) = r ∈ {owner, editor};   delete(r) = share(r) = (r = owner)"),
          P("The global `users.role` column, which holds the string user for every account, takes no part in any decision: all authority is per file.")]

    # ------------------------------------------------------------------ 6.6
    b += [H2("6.6 Cryptographic design (the system's model architecture)"),
          P("A machine-learning project has a network architecture; the corresponding structure here is the hierarchy of keys, because that hierarchy decides which party can read which file. It has four levels."),
          B("**Password.** Known to the user; sent to the server at login for the bcrypt check and used in the browser to derive the key-encryption key. It is never stored.",
            "**Key-encryption key (KEK).** Derived from the password and a 16-byte salt by PBKDF2; used only to seal and unseal the private key; never stored or sent.",
            "**User key pair.** RSA-2048. The public key (SPKI, base64) is stored on the server and is readable by any signed-in user, because senders need it; the private key (PKCS#8) is stored only as an AES-GCM bundle `{salt, iv, data, iterations}` and exists in plaintext only in the memory of the browser tab, which a page reload erases.",
            "**File key (FEK).** A random AES-256 key per file. It exists in plaintext only in the browser; the server holds one RSA-wrapped copy for the owner (`files.owner_wrapped_fek`) and one for each recipient (`file_permissions.wrapped_fek`)."),
          P("The table below lists, for each item, where it lives and what the server can do with it. The last column is the basis of the confidentiality claim."),
          TAB("What the server holds and what it never receives.",
              ["Item", "Held by the server", "Form", "What the server learns from it"],
              [["File content", "Yes", "AES-256-GCM ciphertext in storage/encrypted under a random name", "Size (plaintext size plus 16 bytes); nothing of the content"],
               ["File name, type, owner, time", "Yes", "Plain columns of the files table", "Everything: metadata is not encrypted"],
               ["Plaintext digest", "Yes", "64 hexadecimal digits, unsalted SHA-256", "Whether a known candidate file is the one stored"],
               ["File key", "Only wrapped", "256-byte RSA-OAEP values", "Nothing without a private key"],
               ["Private key", "Only sealed", "PBKDF2 and AES-GCM bundle", "Nothing without the password, but see Section 6.4"],
               ["Public key", "Yes", "Base64 SPKI", "Public by design"],
               ["Password", "Hash only, after seeing it once", "bcrypt, cost 12", "The password itself is visible to the server process during login"],
               ["Audit trail", "Yes", "Hash-chained rows with user, file, action, IP address, details", "Who did what and when; the rows contain no key material"]],
              widths=[1.3, 1.1, 2.1, 2.0], align=["l", "l", "l", "l"], size=9)]

    # ------------------------------------------------------------------ 6.7
    b += [H2("6.7 Configuration parameters"),
          P("CipherVault has no training configuration; it has a set of fixed security parameters in the browser code and in `backend/app/core/config.py`, which `.env` can override. They are collected in the table below because every claim in this report about strength, cost or limits depends on them."),
          TAB("Security and system parameters (values as shipped).",
              ["Parameter", "Value", "Where set"],
              [["AES key length / IV length / tag length", "256 bits / 12 bytes / 128 bits", "vaultCrypto.js"],
               ["RSA modulus / public exponent / OAEP hash", "2048 bits / 65537 / SHA-256", "vaultCrypto.js"],
               ["PBKDF2 hash / iterations / salt", f"SHA-256 / {F.PBKDF2_ITER:,} / 16 random bytes", "vaultCrypto.js (iterations also stored in the bundle)"],
               ["Password hash", f"bcrypt, cost {F.BCRYPT_COST}", "core/security.py"],
               ["Minimum password length", "8 characters (maximum 128)", "schemas.py, auth.py"],
               ["JWT algorithm / lifetime", f"HS256 / {F.JWT_MINUTES} minutes", "config.py (JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES)"],
               ["JWT secret", "Placeholder in config.py and .env.example; to be replaced by the deployer", "JWT_SECRET"],
               ["Login throttle", f"{F.LOGIN_LIMIT[0]} attempts per {F.LOGIN_LIMIT[1]} seconds per IP address and e-mail, in memory, HTTP 429 beyond", "config.py, deps.py"],
               ["Upload limit", f"{F.UPLOAD_LIMIT_MB} MB of plaintext (ciphertext may exceed it by 1 KiB)", "MAX_UPLOAD_MB, files.py"],
               ["Database", "SQLite file by default; PostgreSQL by DATABASE_URL", "config.py, database.py"],
               ["Ciphertext store", "storage/encrypted, random 32-hex names", "STORAGE_DIR"],
               ["Ports", f"API {F.API_PORT}, web application {F.WEB_PORT}", ".env.example, vite.config.js"],
               ["Allowed CORS origins", "localhost and 127.0.0.1 on ports 8413 and 5413", "main.py"]],
              widths=[2.4, 2.6, 1.5], align=["l", "l", "l"], size=9.5)]

    # ------------------------------------------------------------------ 6.8
    if F.REPORT:
        b += [H2("6.8 Measured cost of the design"),
              P(f"The primitives are cheap compared with the network and the server. In the browser (Chrome {F.BR['browser_version']}, {F.ENV['cpu']}) AES-256-GCM encryption of 10 MiB takes a median of {F.ms(_a(10485760, 'encrypt'))} ms and the SHA-256 digest {F.ms(_a(10485760, 'sha256'))} ms, "
                f"whereas the complete encrypted upload takes {F.ms(F.E2E['10485760']['encrypted_up']['median'])} ms; RSA-2048 key generation takes {F.ms(cry['rsa_keygen']['median'])} ms once per account, wrapping a file key {F.ms(cry['rsa_wrap']['median'])} ms, unwrapping it {F.ms(cry['rsa_unwrap']['median'])} ms and the PBKDF2 step of an unlock {F.ms(cry['pbkdf2_120k']['median'])} ms. "
                f"The ciphertext is always {F.AES['1024']['overhead']} bytes longer than the plaintext. The full tables and charts are in Chapter 8. The base paper's primitive timings {cite('base')} were obtained with OpenSSL on a Raspberry Pi 3 B+ and an HPE server and feed a calculated cost model, so they are not ranked against these browser measurements.")]
    else:
        b += [H2("6.8 Measured cost of the design"),
              P(f"The measurements were taken in Chrome {F.BR['browser_version']} on the {F.ENV['cpu']} with {F.ENV['ram_gb']} GB of memory, and the figures are the medians of the repetitions, with the 95th percentile in brackets where several runs exist. "
                "The first table below gives the cost of the primitives and the second that of the key operations; the end-to-end figures are in Chapter 8. Encryption is far from being the bottleneck: at 10 MiB the browser needs " +
                f"{F.ms(_a(10485760, 'encrypt'))} ms to encrypt and {F.ms(_a(10485760, 'sha256'))} ms to hash, whereas the complete encrypted upload takes {F.ms(F.E2E['10485760']['encrypted_up']['median'])} ms."),
              TAB("Median cost of the primitives in the browser (ms, 95th percentile in brackets).",
                  ["Operation", "1 KiB", "1 MiB", "10 MiB", "25 MiB"],
                  _prim_rows(),
                  widths=[2.1, 1.1, 1.1, 1.1, 1.1], align=["l", "c", "c", "c", "c"], size=9.5),
              TAB("Median cost of the key-management operations in the browser.",
                  ["Operation", "Median (ms)", "95th percentile (ms)", "Runs"],
                  [["RSA-2048 key generation (once per account)", F.ms(cry["rsa_keygen"]["median"]), F.ms(cry["rsa_keygen"]["p95"]), str(cry["rsa_keygen"]["n"])],
                   ["RSA-OAEP wrap of a file key", F.ms(cry["rsa_wrap"]["median"]), F.ms(cry["rsa_wrap"]["p95"]), str(cry["rsa_wrap"]["n"])],
                   ["RSA-OAEP unwrap of a file key", F.ms(cry["rsa_unwrap"]["median"]), F.ms(cry["rsa_unwrap"]["p95"]), str(cry["rsa_unwrap"]["n"])],
                   [f"PBKDF2, {F.PBKDF2_ITER:,} iterations (once per unlock)", F.ms(cry["pbkdf2_120k"]["median"]), F.ms(cry["pbkdf2_120k"]["p95"]), str(cry["pbkdf2_120k"]["n"])]],
                  widths=[3.1, 1.0, 1.4, 0.8], align=["l", "c", "c", "c"], size=9.5),
              P("The 1 KiB and 64 KiB operations are faster than the 0.1 ms resolution of Chrome's clock, so they were timed in batches of 200 and divided. "
                f"The base paper reports primitive timings in microseconds on a Raspberry Pi 3 B+ and an HPE server (for example a hash in 2.3 µs and an exponentiation in 1,187 µs on the Raspberry Pi) {cite('base')}; those figures were obtained with OpenSSL on other hardware and are used there to calculate the cost of an attribute-based scheme, "
                "so they are not comparable with the browser measurements above and no ranking is made."),
              *_fg("f08_crypto_primitives.png", "Cost of the key-management primitives in the browser (median, log scale; tick = 95th percentile).", 5.0)]
    return b


def application_blocks():
    api = F.API
    b = []

    b += [H2("6.9 Application architecture"),
          P(f"The product is one FastAPI service (`backend/app/main.py`, port {F.API_PORT}) and one React 19 application built with Vite (port {F.WEB_PORT} in development, served by the same service after `npm run build`). "
            f"The backend has {F.LOC['backend_py']['lines']:,} lines in {F.LOC['backend_py']['files']} Python files, the tests {F.LOC['tests_py']['lines']} lines in {F.LOC['tests_py']['files']} files, the browser application {F.LOC['frontend_src']['lines']:,} lines in {F.LOC['frontend_src']['files']} files and the scripts {F.LOC['scripts_py']['lines']:,} lines in {F.LOC['scripts_py']['files']} files. "
            "The service follows one rule: **a route does HTTP work and calls a service function for the decision**. It validates the request with Pydantic and explicit checks, asks `permission_service` for the caller's role, performs the database and filesystem work through a per-request SQLAlchemy session, and records the outcome with `audit_service`."),
          *_dg("arch", None, 5.4),
          P("The two service modules are small enough to quote. The role lookup and the four predicates of `permission_service.py` are the entire access-control logic of the system:"),
          CODE('''def get_effective_role(db, file, user_id):
    if file.owner_id == user_id:
        return "owner"
    perm = (db.query(FilePermission)
              .filter(FilePermission.file_id == file.id, FilePermission.user_id == user_id)
              .first())
    return perm.role if perm else None

def can_read(role):   return role in ("owner", "editor", "viewer")
def can_write(role):  return role in ("owner", "editor")
def can_delete(role): return role == "owner"
def can_share(role):  return role == "owner"''', 8.5),
          P("The audit service reads the last hash, derives the new one and commits the entry. It reads and writes in two separate steps without a lock, which is correct for one writer at a time and is the cause of the concurrency defect measured in Chapter 7:"),
          CODE('''def record_event(db, *, action, success=True, user_id=None, file_id=None, details="", ip_address=None):
    last = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    previous_hash = last.current_hash if last else GENESIS
    now = datetime.now(timezone.utc)
    current_hash = _hash_event(previous_hash, now, user_id, file_id, action, success, details)
    entry = AuditLog(timestamp_utc=now, user_id=user_id, file_id=file_id, action=action,
                     success=success, ip_address=ip_address, details=details[:2000],
                     previous_hash=previous_hash, current_hash=current_hash)
    db.add(entry)
    db.commit()
    return entry''', 8.5),
          P("In the browser, the code is organised in three layers. `lib/vaultCrypto.js` is the only file that calls Web Crypto; `lib/vault.js` combines it with the API calls (`uploadFile`, `replaceFileContent`, `fetchAndDecrypt`, `shareWith`); and `lib/auth.jsx` and `features/UnlockGate.jsx` hold the session and the in-memory private key. "
            "A single fetch wrapper in `lib/api.js` attaches the bearer token, turns the `detail` field of an error response into the error message, and signs the user out on a 401. The pages (Landing, Auth, Dashboard, Files, FileDetail, Audit, Security, NotFound) call these functions and render the results; no page calls Web Crypto directly. "
            "The JWT is kept in `sessionStorage`, which is cleared when the tab closes, and the unlocked private key is kept only in React state, so a reload locks the vault and the next action that needs the key asks for the password again.")]

    b += [H2("6.10 API design"),
          P("The 24 endpoints are listed in Chapter 5. This section shows the shape of the two exchanges that carry the security design. Both are plain HTTP: the upload is a multipart form with a binary part, and the download returns the binary body with the cryptographic parameters in response headers, so that the ciphertext never has to be wrapped in JSON or base64."),
          CODE('''POST /api/files/upload                       Authorization: Bearer <JWT>
multipart/form-data
  ciphertext         (binary, application/octet-stream)
  original_filename  "Q3-board-memo.txt"      mime_type "text/plain"     original_size 217
  iv                 base64, 12 bytes         plaintext_sha256  64 hex digits
  wrapped_fek        base64, 256 bytes (RSA-OAEP under the owner's public key)

201 Created   {"id", "original_filename", "mime_type", "encrypted_size", "original_size",
               "owner_id", "owner_name", "effective_role": "owner", "plaintext_sha256", ...}

GET /api/files/{id}/download                 Authorization: Bearer <JWT>
200 OK        body = ciphertext (application/octet-stream)
              X-CipherVault-IV, X-CipherVault-Wrapped-FEK (the caller's own copy),
              X-CipherVault-SHA256, X-CipherVault-Filename, X-CipherVault-MIME
403 Forbidden {"detail": "Access denied"}    (and an unauthorized_access audit entry)''', 8.5),
          P("Three properties of this design are worth stating. The upload response carries no key material and no `iv`; they are returned only by `GET /api/files/{id}`, which attaches the wrapped key that belongs to the caller (the owner's or the recipient's). "
            "Every `403` caused by a missing role writes an `unauthorized_access` entry to the audit chain, so a refused attempt is itself evidence. And `PUT /api/files/{id}` replaces the content of an existing file: the browser unwraps the existing file key, encrypts the new content under it with a fresh IV and uploads, so every share keeps working without re-wrapping."),
          P(f"**Measured behaviour** (127.0.0.1, medians; the host was shared with other jobs). The health route answers in {F.ms(api['health_ms']['median'])} ms and `GET /api/auth/me` in {F.ms(api['me_ms']['median'])} ms; listing 65 owned files takes {F.ms(api['list_files_ms']['median'])} ms. "
            f"Login is dominated by bcrypt at cost {F.BCRYPT_COST}: {F.ms(api['login_ms']['median'])} ms for a correct password and {F.ms(api['login_fail_ms']['median'])} ms for a wrong one. "
            f"A 1 MiB ciphertext uploads in {F.ms(api['upload_ms']['1048576']['median'])} ms and downloads in {F.ms(api['download_ms']['1048576']['median'])} ms; a 10 MiB one in {F.ms(api['upload_ms']['10485760']['median'])} ms and {F.ms(api['download_ms']['10485760']['median'])} ms; the largest object (just under 25 MiB) in {F.ms(api['upload_ms']['26212352']['median'])} ms and {F.ms(api['download_ms']['26212352']['median'])} ms. "
            f"Sharing takes {F.ms(api['share_ms'])} ms, a role change {F.ms(api['change_role_ms'])} ms and a revocation {F.ms(api['revoke_ms'])} ms (one run each); the first download after the revocation was refused with HTTP {api['download_after_revoke_status']}. "
            f"Writing one audit event takes a median of {F.ms(F.M['audit_write_ms']['median'])} ms (95th percentile {F.ms(F.M['audit_write_ms']['p95'])} ms)."),
          *_fg("f03_api_latency.png", "Median API latency over loopback (marker = 95th percentile where several runs exist).", 5.4),
          *_fg("f04_api_transfer_scaling.png", "Upload and download of ciphertext through the API against object size.", 5.4)]

    b += [H2("6.11 Security and error handling"),
          P("The security model is stated first as a list of what each mechanism provides and then as a list of what it does not provide, so that no reader assumes more than the system delivers."),
          H3("6.11.1 What is implemented"),
          B("**Client-side encryption.** The server stores AES-256-GCM ciphertext only. Opening the stored objects, a database dump or a backup yields no plaintext and no usable key.",
            "**Authentication.** Passwords are checked against bcrypt hashes; a wrong e-mail or password gives the same message (`Invalid email or password`) and a `login_failure` entry. Tokens are signed with HS256 and expire after 120 minutes; a missing, malformed, expired or wrongly signed token is refused with HTTP 401 and a user who is deactivated or deleted is refused too.",
            "**Authorisation on every file route.** Each route resolves the effective role on the server and refuses with HTTP 403 when the predicate fails; the client's idea of the role is never trusted. Refusals are audited.",
            "**Input validation.** Pydantic enforces names (1 to 120 characters), e-mail syntax, passwords (8 to 128 characters), roles (`viewer` or `editor` only) and non-empty key fields (HTTP 422); the file routes enforce the structural rules of Section 6.3.2 (HTTP 400 and 413).",
            "**Storage safety.** Stored names are random, so path traversal through a file name is not possible; SQL goes through the ORM, so values are parameterised; deleting a file removes the object and its rows and records a `delete` event.",
            "**Login throttling.** Twenty attempts per five minutes per IP address and e-mail, counted in memory, then HTTP 429.",
            "**Browser side.** The application renders file names and details as React text, uses no raw HTML insertion, locks the vault on reload and on request, and shows a decryption or integrity failure as an error without saving the file."),
          H3("6.11.2 What is not provided"),
          B("**No protection against an active malicious server.** The server delivers the JavaScript that performs the encryption and receives the password at login; a modified server could capture either. This is the trust problem of every web-delivered end-to-end design, and attacks of this kind on a deployed encrypted store are documented in the literature " + cite("mega") + ".",
            "**Revocation is forward-only.** Revoking a user deletes the server-side wrapped key and refuses further downloads, but a user who already downloaded the ciphertext and unwrapped the key keeps both; the file is not re-encrypted under a new key.",
            "**Audit trail limits.** Any signed-in user can read the vault-wide event list; tail truncation and a complete re-hash are not detected; concurrent writers fork the chain (Chapter 7). The client IP address is taken from the `X-Forwarded-For` header when present, so behind no proxy it can be spoofed, which also weakens the throttle.",
            "**Metadata is public to the server.** File names, sizes, types, owners and times are stored in clear, the user list is searchable by any signed-in user, and the registration route confirms whether an e-mail address is registered.",
            "**Accounts.** No multi-factor authentication, no password reset (a lost password means lost data, because the private key cannot be unsealed), no account lockout other than the in-memory throttle that a restart clears, and a placeholder JWT secret that the deployer must change.",
            "**Size.** Whole-file encryption in memory limits files to 25 MB; there is no chunking, streaming or resumable upload."),
          TAB("HTTP status codes returned by the API and their causes (from the code).",
              ["Status", "Raised when"],
              [["400", "Invalid base64, IV length other than 12 bytes, malformed digest, invalid file name or size; duplicate e-mail at registration; sharing with the owner"],
               ["401", "Missing, malformed, expired or wrongly signed token; unknown or deactivated user; wrong credentials"],
               ["403", "The effective role does not allow the operation (read, update, delete, share, change role, revoke, file history)"],
               ["404", "File, share target, permission row or stored object not found; deleted file"],
               ["409", "The recipient already has access (use the change-role route)"],
               ["413", f"Ciphertext larger than {F.UPLOAD_LIMIT_MB} MB plus 1 KiB (measured: HTTP {api['upload_limit_check']['over_25MB_status']} for a 25 MB object plus 5,000 bytes)"],
               ["422", "Request body violates the schema (e-mail syntax, name or password length, role other than viewer or editor)"],
               ["429", "More than 20 login attempts in 300 seconds for one IP address and e-mail"],
               ["500", "The filesystem refused a write or a delete"]],
              widths=[0.7, 5.8], align=["c", "l"], size=9.5),
          P(f"The automated tests cover the registration and login rules, the missing and invalid token cases, the owner, editor, viewer and stranger decisions, the share, change-role and revoke operations, the malformed upload and the audit tamper check ({F.PYTEST_TOTAL} tests); the 429 response, the 409 response and the 500 responses were not exercised by any test (Chapter 7).")]

    b += [H2("6.12 Installation and execution"),
          P("The project guide (`HOW_TO_RUN.md`) asks for Python 3.11 or newer, Node.js 20 or newer, a current browser with Web Crypto support and about 500 MB of disk space. "
            "`requirements.txt` lists fastapi, uvicorn, sqlalchemy, psycopg, alembic, pydantic, pydantic-settings, email-validator, PyJWT, bcrypt, python-multipart, cryptography, python-dotenv, pytest, httpx and fpdf2 with minimum versions and no upper pins; the front end depends on React 19, Vite 8, React Router 7, Recharts, three.js, Framer Motion, GSAP and Lenis. "
            f"The measurements in this report used Python {F.ENV['python']} and Chrome {F.BR['browser_version']} on Windows 11."),
          N("Open the project folder `8.ProjectCode`. Copy `.env.example` to `.env` and replace `JWT_SECRET` by a long random string (the file is excluded from version control).",
            "Double-click `run.bat`. It checks Python and Node, creates `.venv`, installs `requirements.txt` and, on the first run, `npm install` in `frontend/`, then starts the API with `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8413` and the Vite server on port 5413 in two windows.",
            "Open http://localhost:5413. Choose **Try the demo** for a populated vault with the three demonstration roles, or register an account, which creates the key pair in the browser, and upload a file.",
            f"Run `python -m pytest` for the automated tests ({F.PYTEST_PASSED} passed in {F.PYTEST_SECONDS:.0f} s here). `python scripts/e2e_check.py --url http://localhost:8413` runs the API end-to-end check against a running server, and `python scripts/smoke_test.py` adds a Playwright walk of the interface.",
            "For the production-style variant, `docker compose build` and `docker compose up` start PostgreSQL 16 and the application, which serves the built front end on http://localhost:8413; the port is published to 127.0.0.1 only. This route was not run during the documentation work."),
          P("Three notes come from this project's own runs. The database is created at start-up from the SQLAlchemy models (`init_db`), and there is no migration: `alembic` is a dependency but no migration scripts exist, so a change of schema needs a new database. "
            "The measurements used a scratch database, a scratch ciphertext folder and a throttle limit raised to 100,000 attempts, so that the login timings were not disturbed by the throttle; the shipped limit of 20 was not exercised. "
            "To reproduce the numbers, run `python scripts/measure_metrics.py` with the browser available (it starts its own server on a scratch database) and `python scripts/evaluate.py`; Appendix B repeats the instructions as a user guide with the screens.")]
    return b


_DROP_REPORT = ("Two choices deserve", "The audit service reads the last hash", "def record_event", "In the browser, the code is organised", "**Measured behaviour**")


def _trim(bl):
    """Report variant: diagrams appear in Chapter 5 and the result charts and tables in Chapter 8, so only the text, tables and code that
    Chapters 5 and 8 do not repeat are kept (the audit-service listing is in Appendix A, the measured API behaviour in Chapter 8)."""
    out = []
    skip = False
    for b in bl:
        if b[0] == "h2":
            skip = b[1].startswith("6.12")
            if skip:
                out += [b, ("p", "Installation, the start-up scripts, the environment settings and the demo accounts are described step by step in Appendix B; "
                                 "the measurement and evaluation scripts are `scripts/measure_metrics.py` and `scripts/evaluate.py`, and the test suite runs with `pytest -q`.")]
                continue
        if skip:
            continue
        if b[0] == "fig" and (os.sep + "diagrams" + os.sep in b[1] or os.path.basename(b[1]).startswith("f0")):
            continue
        if b[0] in ("p", "code") and any(b[1].startswith(x) for x in _DROP_REPORT):
            continue
        out.append(b)
    return out


def blocks():
    bl = [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
    return _trim(bl) if F.REPORT else bl
