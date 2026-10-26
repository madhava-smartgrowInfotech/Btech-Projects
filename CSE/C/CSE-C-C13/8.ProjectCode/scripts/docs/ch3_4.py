"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis) for CipherVault.

Every measured number is read from facts.py (docs/metrics/metrics.json); nothing is typed in by hand except values that
come straight from the source tree (ports, limits, iteration counts, versions recorded in REPORT_FACTS.md).
"""

from . import facts as F
from .blocks import B, H1, H2, N, P, TAB
from .refs import N as C


def blocks():
    out = chapter3() + chapter4()
    if F.REPORT:   # compact report variant: the schedule table becomes a paragraph
        out = _trim(out)
    return out


def _trim(bl):
    res = []
    for b in bl:
        if b[0] == "tab" and b[1].startswith("Project phases"):
            res.append(P("The work followed the dependencies of the system, with calendar dates left as placeholders [DATES]: problem study and base-paper reading; the backend (models, authentication, "
                         "file and sharing routes, audit chain); the browser cryptography module; the web application; the measurement, test and screenshot scripts; and finally the documentation run. "
                         "Each phase depends on the one before it, and the schedule risk lay in the cryptographic design decisions rather than in programming effort."))
            continue
        res.append(b)
    return res


def _med(d, key=None):
    """Median of a metrics record, formatted."""
    d = d[key] if key is not None else d
    return F.ms(d["median"])


def _up(size):
    return F.API["upload_ms"][str(size)]["median"]


def _dn(size):
    return F.API["download_ms"][str(size)]["median"]


MIB = 1024 * 1024


# =====================================================================================================================
def chapter3():
    aes10, aes25 = F.AES[str(10 * MIB)], F.AES[str(25 * MIB)]
    e10 = F.E2E[str(10 * MIB)]
    over10 = e10["encrypted_up"]["median"] - e10["plain_up"]["median"]
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        H2("3.1 Technical Feasibility"),
        P(f"**Hardware.** All measurements in this report were taken on an {F.ENV['cpu']} with {F.ENV['ram_gb']} GB of memory running Windows 11, with the browser (Chrome {F.BR['browser_version']}) and the server on the same machine, "
          "so the network contributes only the loopback interface. No special hardware is needed: AES-256 and SHA-256 are executed by the browser's native Web Crypto implementation, and the server never performs bulk cryptography. "
          f"Encrypting a 10 MiB file took a median of {F.ms(aes10['encrypt']['median'])} ms and decrypting it {F.ms(aes10['decrypt']['median'])} ms in the browser; the largest file the system accepts, 25 MiB, took {F.ms(aes25['encrypt']['median'])} ms to encrypt. "
          "Smaller machines, mobile browsers and other browsers were not tested."),
        P(f"**Software.** The components are open-source packages that were already in common use: Python {F.ENV['python']} with FastAPI, SQLAlchemy, PyJWT, bcrypt and the `cryptography` package on the server; React 19 with Vite 8 in the browser; "
          f"and the W3C Web Cryptography API {C('webcrypto')} for AES-GCM {C('gcm')}, RSA-OAEP {C('oaep')}, PBKDF2 {C('pbkdf2')} and SHA-256 {C('sha')}. "
          "Because the browser's own implementation is used, the project writes no cryptographic primitive of its own; it composes standard ones. "
          "This is the main technical risk-reduction decision of the design: most failures of real storage products arise from how primitives are combined, not from the primitives themselves "
          f"{C('mega')}, and the combination here is deliberately small (one random key per file, one key pair per user)."),
        P(f"**Feasibility evidence.** The full flow of the product has been run end to end and measured: {F.PYTEST_PASSED} backend tests pass in {F.PYTEST_SECONDS:.0f} s, an API walk-through of {F.E2E_TOTAL} checks and a real-browser walk-through of {F.UI_TOTAL} checks pass, "
          f"and a 4 principals x 9 operations access-control matrix produced the expected answer in {F.RBAC['matched']} of {F.RBAC['total']} cells. The project is therefore technically feasible on a single ordinary computer for the file sizes it supports (up to {F.UPLOAD_LIMIT_MB} MB)."),
        P("**Technical limits.** Three limits constrain feasibility and are examined later. The file is encrypted as one block in memory, so the browser must hold the plaintext and the ciphertext at once; this is why a 25 MB cap exists and why very large files would need chunked encryption. "
          "The server is trusted to deliver the JavaScript that performs the cryptography, so a compromised server could change the code (a limit shared by every web-delivered end-to-end design). "
          "The audit chain has no secret key, so it detects accidental or partial tampering but not a determined rewrite by someone who controls the database."),

        H2("3.2 Economic Feasibility"),
        P("The project has no licence cost. Every dependency is open source, the default database is SQLite (a file with no server process), and the system runs on a computer the team already used for development. "
          "PostgreSQL is optional and is supplied through the Docker files (`docker-compose.yml`) for a production-style run; that path was not exercised in this work. "
          "No cloud service, key-management service or paid API is called, so there is no recurring cost. The only costs are the student effort of the four team members and the guide's time, neither of which was logged in hours, so no effort figure is claimed here."),
        TAB("Cost view of the project", ["Item", "Cost", "Comment"],
            [["Software licences", "None", "FastAPI, SQLAlchemy, React, Vite and the browser's Web Crypto API are free and open source"],
             ["Hardware", "Existing PC", f"{F.ENV['cpu']}; no GPU; no dedicated server"],
             ["Hosting and cloud", "None", "Local deployment on 127.0.0.1; the storage layer is one small module that can later be replaced by object storage"],
             ["Operating cost", "Electricity only", "No recurring services"],
             ["Staff effort", "[EFFORT NOT RECORDED]", "Four students under the guidance of " + F.GUIDE]],
            widths=[1.5, 1.4, 3.6], align=["l", "l", "l"], size=10),
        P("The economic argument for the design, as opposed to the cost of building it, is that moving encryption to the user's browser avoids the cost of operating a key-management service for plaintext access: the server holds no key that can decrypt a file, "
          "so a database leak or a stolen backup exposes only ciphertext. The price of that choice is paid by the user, who must remember a password that cannot be recovered."),

        H2("3.3 Operational Feasibility"),
        P("Day-to-day use needs no technical knowledge beyond a password. A user registers once; the browser creates the key pair in about "
          f"{F.ms(F.CRY['rsa_keygen']['median'])} ms (median of {F.CRY['rsa_keygen']['n']} runs) and the registration form does not ask the user to handle any key. After sign-in the vault unlocks with the same password, "
          f"which costs a median of {F.ms(F.CRY['pbkdf2_120k']['median'])} ms of key derivation. Uploading, sharing and downloading are single actions in the interface, and the extra work of encryption is hidden behind progress messages ('Encrypting in your browser', 'Uploading ciphertext'). "
          f"For a 10 MiB file the whole encrypted upload took a median of {F.ms(e10['encrypted_up']['median'])} ms against {F.ms(e10['plain_up']['median'])} ms for the same transfer without encryption, an increase of about {F.ms(over10)} ms on this machine. "
          "These figures were measured while other work was running on the same computer, so they should be read as indicative."),
        P("Operations are simple to run. `run.bat` creates the Python environment, installs the Python and Node packages, starts the backend and the Vite development server in two windows and opens the browser; `run-docker.bat` starts the PostgreSQL variant. "
          "The system needs a periodic backup of two things, the database and the `storage/encrypted` folder, and an administrator who keeps the `JWT_SECRET` private. "
          "Two operational cautions follow from the design and are stated in the user guide: a forgotten password cannot be reset without losing access to the files, and the in-memory login throttle is cleared whenever the server restarts."),

        H2("3.4 Schedule Feasibility"),
        P("The project was planned as five dependent phases. Calendar dates are left as placeholders because they were not recorded in the repository; the order is what matters, since each phase builds on the one before it."),
        TAB("Project phases", ["Phase", "Work", "Output"],
            [["1", "Problem study, base-paper and literature reading, objectives", "Abstract, introduction, literature survey, objectives [DATES]"],
             ["2", "Backend: models, bcrypt/JWT authentication, file, sharing and audit routes, hash-chained audit service", f"{F.LOC['backend_py']['lines']:,} lines in {F.LOC['backend_py']['files']} Python files; 24 endpoints"],
             ["3", "Browser cryptography (Web Crypto) and web application with the Owner / Editor / Viewer views", f"{F.LOC['frontend_src']['lines']:,} lines in {F.LOC['frontend_src']['files']} source files"],
             ["4", "Tests, measurement and screenshot scripts, hardening found by testing", f"{F.PYTEST_TOTAL} pytest tests; measurement run of {F.ENV['date']}"],
             ["5", "Documentation: diagrams, figures, report, presentations, paper", "The eleven submission documents"]],
            widths=[0.6, 3.6, 2.3], align=["c", "l", "l"], size=10),
        P("The phase with the most design consequences is phase 3. The decision to keep the private key out of the server and in browser memory only means that a page reload locks the vault, so the interface needed an unlock dialog (`UnlockGate`) that every operation needing the key can call, "
          "and uploads, downloads and sharing all wait for it. Effort per phase was not recorded, so no claim is made about how the time was divided."),

        H2("3.5 Advantages and Constraints"),
        P("The advantages of the chosen design, each of which is backed by a test or a measurement later in this report, are:"),
        B("**Confidentiality against the server.** The server receives ciphertext, an IV, wrapped keys and a digest, never plaintext or a private key.",
          f"**Server-enforced roles.** Owner, Editor and Viewer rights are decided on the server for every request; the access matrix matched in {F.RBAC['matched']} of {F.RBAC['total']} cells and unauthenticated or forged tokens were refused with HTTP 401.",
          "**Two independent integrity checks.** The AES-GCM authentication tag and the stored SHA-256 of the plaintext must both pass before the browser saves a downloaded file.",
          "**Accountability.** Every sensitive action, including refused ones, is written to a hash-chained audit log that any signed-in user can ask the server to verify.",
          "**Small, replaceable parts.** SQLite or PostgreSQL, a filesystem store that can be swapped for object storage, and a single JWT secret."),
        P("The constraints are equally part of the feasibility picture:"),
        B(f"**Size.** Whole-file in-memory encryption limits files to {F.UPLOAD_LIMIT_MB} MB.",
          "**Revocation.** Removing a user deletes the server's copy of that user's wrapped key but cannot recall a key or ciphertext already downloaded; the file key is not rotated on revoke.",
          "**Audit chain.** Tail truncation (0 of 199 trials detected) and a full rewrite that recomputes every later hash are not detected; concurrent writers can fork the chain.",
          "**No recovery and no second factor.** There is no password reset (the password protects the private key) and no multi-factor authentication.",
          "**Trust in delivered code.** The server that stores ciphertext also serves the JavaScript that encrypts it."),
    ]


# =====================================================================================================================
def chapter4():
    api = F.API
    aes1, aes64 = F.AES["1024"], F.AES["65536"]
    e1m = F.E2E[str(MIB)]
    e10 = F.E2E[str(10 * MIB)]
    fr = [
        ["FR-1", "Register an account with a name, an e-mail address and a password of at least 8 characters; reject a duplicate e-mail", "Register page", "POST /api/auth/register"],
        ["FR-2", "Generate an RSA-2048 key pair in the browser at registration and store only the public key and the password-sealed private-key bundle on the server", "Register page", "POST /api/auth/register, GET /api/auth/key-bundle"],
        ["FR-3", f"Authenticate with e-mail and password (bcrypt, cost {F.BCRYPT_COST}) and issue a JWT that expires after {F.JWT_MINUTES} minutes; throttle repeated attempts", "Sign-in page", "POST /api/auth/login, GET /api/auth/me"],
        ["FR-4", "Unlock the vault by deriving the key from the password in the browser, keep the private key in memory only, and allow a manual lock", "Unlock dialog, Security page", "GET /api/auth/key-bundle"],
        ["FR-5", f"Encrypt a file of up to {F.UPLOAD_LIMIT_MB} MB with AES-256-GCM and a fresh 12-byte IV before upload, wrap its key with the owner's public key, and send the SHA-256 of the plaintext", "My files", "POST /api/files/upload"],
        ["FR-6", "List the files the user owns and the files shared with the user, with the effective role of each", "My files, Shared with me, Dashboard", "GET /api/files, GET /api/files/shared"],
        ["FR-7", "Download the ciphertext only to a caller with a role, decrypt it in the browser, and refuse to save the file unless both the GCM tag and the SHA-256 digest verify", "File detail", "GET /api/files/{id}, GET /api/files/{id}/download"],
        ["FR-8", "Replace the content of a file (Owner or Editor) by re-encrypting under the existing file key so existing shares keep working", "File detail", "PUT /api/files/{id}"],
        ["FR-9", "Delete a file together with its ciphertext object (Owner only)", "File detail", "DELETE /api/files/{id}"],
        ["FR-10", "Share a file with a registered user as Viewer or Editor by re-wrapping the file key in the owner's browser for the recipient's public key", "Share dialog", "GET /api/users, POST /api/files/{id}/share"],
        ["FR-11", "List who has access; change a role; revoke access, which deletes the recipient's wrapped key (Owner only for changes)", "Share dialog", "GET/PUT/DELETE /api/files/{id}/permissions"],
        ["FR-12", "Enforce the rules Owner = read, update, delete, share and manage; Editor = read and update; Viewer = read; no role = nothing, on the server for every request", "All pages", "permission_service in every file route"],
        ["FR-13", "Record login, logout, registration, upload, download, update, delete, share, role change, revocation and every refused attempt in a hash-chained audit log", "Audit log, File history", "GET /api/audit, GET /api/audit/file/{id}"],
        ["FR-14", "Recompute the audit chain on request and report the first failing entry, and write the verification itself to the log", "Audit log, Dashboard", "GET /api/audit/verify"],
        ["FR-15", "Show a dashboard of the user's files, access by role and recent security events, and a security profile of the account", "Dashboard, Security", "GET /api/files, GET /api/audit"],
    ]
    nfr = [
        ["NFR-1", "Confidentiality: the server must not be able to read file contents", "Upload carries ciphertext, IV, wrapped key and digest only; the API walk-through checks that the stored object has the ciphertext size (plaintext plus 16 bytes), not the plaintext"],
        ["NFR-2", "Access-control correctness", f"{F.RBAC['matched']} of {F.RBAC['total']} cells of the 4 x 9 matrix as expected; unauthenticated requests 401; forged, expired, wrong-secret and alg=none tokens 401"],
        ["NFR-3", "Integrity of stored files", f"{F.TAMPER['ciphertext_bitflip']['detected']} of {F.TAMPER['ciphertext_bitflip']['trials']} single-bit ciphertext flips detected by AES-GCM; decryption with a wrong key rejected"],
        ["NFR-4", "Tamper evidence of the audit log", "8 of 9 tamper classes detected in every trial; tail truncation not detected (0 of 199); a full rewrite that recomputes every hash not detected"],
        ["NFR-5", "Encryption overhead acceptable for interactive use",
         f"AES-256-GCM median {F.ms(aes1['encrypt']['median'])} ms (1 KiB), {F.ms(aes64['encrypt']['median'])} ms (64 KiB), {F.ms(F.AES[str(10 * MIB)]['encrypt']['median'])} ms (10 MiB); ciphertext is exactly 16 bytes larger than the plaintext"],
        ["NFR-6", "End-to-end transfer time",
         f"Encrypted vs plain upload, median: {F.ms(e1m['encrypted_up']['median'])} vs {F.ms(e1m['plain_up']['median'])} ms (1 MiB); {F.ms(e10['encrypted_up']['median'])} vs {F.ms(e10['plain_up']['median'])} ms (10 MiB)"],
        ["NFR-7", "API responsiveness", f"Median {F.ms(api['health_ms']['median'])} ms (health), {F.ms(api['me_ms']['median'])} ms (current user), {F.ms(api['list_files_ms']['median'])} ms (list of 65 files); login {F.ms(api['login_ms']['median'])} ms because bcrypt is deliberately slow"],
        ["NFR-8", "Input validation", f"Empty upload 400, IV not 12 bytes 400, bad digest 400, wrapped key on share not 256 bytes 400, file above {F.UPLOAD_LIMIT_MB} MB 413"],
        ["NFR-9", "Testability and repeatability", f"{F.PYTEST_PASSED} pytest tests in {F.PYTEST_SECONDS:.0f} s; scripts/measure_metrics.py regenerates every reported number into docs/metrics/metrics.json"],
        ["NFR-10", "Usability and accessibility", "Light and dark themes, reduced-motion support, responsive down to 360 px (checked by the browser walk-through); no screen-reader audit and no user study were done"],
        ["NFR-11", "Portability", "Windows 11, Python 3.11, Node 24, Chrome; SQLite by default, PostgreSQL and Docker files provided but not exercised"],
    ]
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Existing System"),
        P("Organisations and individuals who keep sensitive files off their own machines usually rely on one of three arrangements: a shared network folder, a cloud-drive service, or files sent as attachments. "
          "In the first two the storage provider encrypts data at rest with keys that the provider itself holds, so the provider, its administrators, an attacker who gains access to the service and anyone who obtains a database backup can all reach the plaintext. "
          "Access control is typically a list of users and permissions kept by the same provider, and the audit trail, if one exists, is an ordinary log that the provider can edit."),
        P("Research prototypes address the problem by moving encryption to the client. SiRiUS, Plutus and Tahoe-LAFS keep file keys away from untrusted storage "
          f"{C('sirius', 'plutus', 'tahoe')}, and attribute-based encryption gives fine-grained policies without a per-file key list {C('abe06', 'cpabe')}. "
          f"The declared base paper of this project applies attribute-based encryption, a permissioned blockchain and a language model to health records {C('base')}, and the closest file-storage architecture we found combines client-side AES, RSA key management, role-based access and an audit log {C('ijedr')}. "
          f"Client-side encryption is not safe merely because it is client-side: the analysis of MEGA {C('mega')} showed that a design with an unauthenticated or malleable use of keys can leak them, which is why authenticated encryption and a documented key hierarchy are central requirements here."),
        H2("4.2 Limitations of the Existing System"),
        B("**Provider-readable data.** Server-side encryption at rest protects a stolen disk but not a malicious or compromised administrator, an application bug or a leaked backup together with its keys.",
          "**Coarse or absent roles.** A user who is authenticated can often reach any file in a shared area; per-file Owner / Editor / Viewer separation is not the default, and role changes do not change the keys.",
          "**No integrity check on retrieval.** A file altered in storage is returned as it is; the user has no digest or authentication tag to compare against.",
          "**Weak accountability.** Logs that the operator can edit cannot establish after an incident who read or changed which file.",
          "**Heavy mechanisms for small deployments.** Attribute-based encryption, key-generation centres and blockchain ledgers need infrastructure that a small team does not run, and the base paper evaluates them by calculation from primitive timings rather than by measuring a working system."),
        H2("4.3 Proposed System"),
        P("CipherVault is a web application that moves every cryptographic operation on file contents into the user's browser and keeps all authorisation decisions on the server. "
          "At registration the browser creates an RSA-2048 key pair, seals the private key under a key derived from the password, and sends only the public key and the sealed bundle. "
          "To upload a file the browser hashes it, encrypts it with a fresh AES-256-GCM key, wraps that key with the owner's public key and posts the ciphertext. "
          "To share a file the owner's browser re-wraps the key for the recipient, so the server stores one wrapped key per authorised user and never a key in clear. "
          "The server enforces Owner, Editor and Viewer rights on every request, records every event in a hash-chained audit log, and lets any signed-in user ask it to recompute the chain."),
        H2("4.4 Advantages of the Proposed System"),
        TAB("Existing practice compared with the proposed system", ["Property", "Typical existing practice", "CipherVault"],
            [["Who can read file contents", "Provider and anyone holding its keys", "Only users whose private key can unwrap a file key"],
             ["Where encryption happens", "Server, after upload", "Browser, before upload"],
             ["Key per file", "Often one provider key for many files", "A random AES-256 key for every file, wrapped separately for every recipient"],
             ["Access rules", "Provider-defined sharing links or folders", "Owner / Editor / Viewer per file, checked on the server for every request"],
             ["Integrity on download", "Rarely visible to the user", "GCM tag and SHA-256 of the plaintext checked before the file is saved"],
             ["Audit trail", "Operator-editable log", "Hash-chained log with a user-run verification (with the limits stated in Chapter 8)"],
             ["Infrastructure", "Cloud account or key-management service", "One FastAPI process, a database and a folder"]],
            widths=[1.6, 2.2, 2.7], align=["l", "l", "l"], size=10),
        P("The proposed system does not claim to remove every risk of the existing practice. It removes the provider's ability to read file contents and gives users two independent checks of what they receive; it does not protect a user whose browser or password is compromised, "
          "and it does not prevent a recipient from keeping a copy of a file they were once allowed to read."),
        H2("4.5 Functional Requirements"),
        P("The requirements below are those the delivered system meets; each is tied to the page that offers it and the route that implements it."),
        TAB("Functional requirements", ["ID", "Requirement", "Page", "Route(s)"], fr, widths=[0.55, 3.3, 1.05, 1.6], align=["c", "l", "l", "l"], size=8.8),
        P("The six objectives set at the start of the project map onto these requirements as follows: objective 1 (registration, hashed credentials, JWT sessions) to FR-1, FR-3; objective 2 (encrypt every upload with AES-256-GCM before it reaches storage) to FR-2 and FR-5; "
          "objective 3 (role-based access with ownership checks) to FR-10 to FR-12; objective 4 (integrity verification on download) to FR-7; objective 5 (audit logs of every upload, download, delete and denial) to FR-13 and FR-14; "
          "and objective 6 (evaluation of overhead, access-control correctness and integrity) to the non-functional requirements below, which are each tied to a measurement."),
        H2("4.6 Non-Functional Requirements"),
        TAB("Non-functional requirements and the evidence for each", ["ID", "Requirement", "Measured value or evidence"], nfr, widths=[0.65, 2.0, 3.85], align=["c", "l", "l"], size=9),
        P("All timings were taken on the machine described in Section 4.7 while other programs were using the processor, with run-to-run spread of up to about three times for the 10 MiB case; they show the order of magnitude and the shape of the cost, not a benchmark. "
          "Requirement NFR-4 is reported in full, including the two cases that are not detected, because an audit log that claims more than it delivers is worse than none."),
        H2("4.7 Hardware Requirements"),
        TAB("Hardware", ["Item", "Suggested minimum (estimate, not tested)", "Used for the measurements"],
            [["Processor", "Any recent 2-core CPU", F.ENV["cpu"]],
             ["Memory", "4 GB (a 25 MB file is held in memory as plaintext and ciphertext)", f"{F.ENV['ram_gb']} GB"],
             ["Storage", "1 GB plus the space the ciphertext objects need", "Local disk; ciphertext folder holds one object per file"],
             ["Graphics", "None (a hero animation on the landing page uses WebGL; a static fallback exists)", "Integrated; no GPU compute used"],
             ["Display", "360 px wide or larger", "Screenshots at 1440 x 900; mobile layouts at 360 px"],
             ["Network", "Loopback or local network", "Loopback 127.0.0.1"]],
            widths=[1.1, 2.9, 2.5], align=["l", "l", "l"], size=10),
        P("The suggested minimums are our estimates; only the right-hand column was measured or observed."),
        H2("4.8 Software Requirements"),
        TAB("Software", ["Component", "Version used", "Role"],
            [["Python", F.ENV["python"], "Server language"],
             ["FastAPI / Starlette / Uvicorn", "0.159.1 / 1.9.0 / 0.54.0", "REST application and ASGI server"],
             ["SQLAlchemy / Pydantic", "2.1.6 / 2.14.1", "ORM (SQLite or PostgreSQL through `psycopg`) and request validation"],
             ["PyJWT / bcrypt", "2.15.1 / 5.0.0", "Access tokens (HS256) and password hashing"],
             ["cryptography", "50.0.2", "Declared in requirements.txt and used by the tests and the demo-seeding script for AES-GCM and RSA-OAEP; no server route imports it"],
             ["React / Vite / React Router", "19.3.1 / 8.3.5 / 7.18.4", "Single-page application, build and routing"],
             ["Recharts / three.js / Framer Motion", "3.10.1 / 0.186.1 / 14.6.0", "Dashboard charts, landing-page scene, motion"],
             ["Web Crypto API", "Browser built-in", "AES-256-GCM, RSA-OAEP, PBKDF2-HMAC-SHA-256, SHA-256"],
             ["pytest / httpx", "9.1.1 / 0.28.1", "Automated tests"],
             ["Node.js", "24.19.0", "Front-end build tooling"],
             ["Playwright / Chrome", "1.44.0 / " + F.BR["browser_version"], "Browser walk-through, screenshots and in-browser measurements"],
             ["PostgreSQL / Docker", "16 (image) / not tested", "Optional production-style deployment"]],
            widths=[2.2, 1.7, 2.6], align=["l", "l", "l"], size=9.8),
        P("The package versions are those installed in the project environment during the measurement run; `requirements.txt` lists only minimum versions so that the project installs on newer interpreters."),
        H2("4.9 User Roles and System Constraints"),
        P("Roles belong to a file, not to an account. The account-level `role` column of the users table holds the value `user` for every account and is not used in any decision. A person can be Owner of one file, Editor of a second and Viewer of a third. "
          "The rights, as implemented in `permission_service.py` and exercised by the access matrix, are:"),
        TAB("Rights by role", ["Operation", "Owner", "Editor", "Viewer", "No role"],
            [["Read metadata, download ciphertext and own wrapped key", "yes", "yes", "yes", "403"],
             ["List who has access", "yes", "yes", "yes", "403"],
             ["Replace content (update)", "yes", "yes", "403", "403"],
             ["Share, change role, revoke", "yes", "403", "403", "403"],
             ["View the file's own audit history", "yes", "403", "403", "403"],
             ["Delete the file", "yes", "403", "403", "403"]],
            widths=[3.1, 0.8, 0.8, 0.8, 1.0], align=["l", "c", "c", "c", "c"], size=10),
        P("A refused request is answered with HTTP 403 and is itself written to the audit log as `unauthorized_access`. Two further actors appear in the design: the **visitor**, who may only register and sign in, and the **deployer**, who supplies the `.env` configuration. "
          "Any signed-in user can open the vault-wide audit log and run the chain verification; this is a convenience of the current build and is recorded as a limitation."),
        P("The constraints within which the system was designed and tested are:"),
        B(f"**Size and memory.** Files up to {F.UPLOAD_LIMIT_MB} MB; the browser encrypts the file as one block.",
          f"**Session.** A JWT is valid for {F.JWT_MINUTES} minutes and is kept in `sessionStorage`; a reload clears the in-memory private key and the vault must be unlocked again.",
          f"**Login throttle.** {F.LOGIN_LIMIT[0]} attempts per {F.LOGIN_LIMIT[1]} seconds for each address and e-mail pair, held in server memory and lost on restart.",
          "**Single-writer audit chain.** The service reads the last hash and commits without a lock, so it assumes one writer at a time; concurrent writers were shown to fork the chain.",
          "**Not tested.** Multi-user load, files above 25 MB, Firefox and Safari, the PostgreSQL path, the Docker build and a screen-reader accessibility audit."),
    ]
