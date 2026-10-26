"""Chapters 9 (Conclusion) and 10 (Future scope), plus the shared block lists used by documents 9, 10, 12 and 15.

Every number is read from facts.py (docs/metrics/metrics.json, tests.json); code excerpts are cut from the real files in 8.ProjectCode.
"""
import ast
import os
import textwrap

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB, renum
from .refs import N as C


# ---------------------------------------------------------------------------- helpers
def _read(rel):
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        return f.read()


def fn(rel, name, doc=False):
    """Source of a module-level Python function exactly as it stands (docstring removed unless doc=True)."""
    text = _read(rel)
    lines = text.split("\n")
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            start = min([d.lineno for d in node.decorator_list] + [node.lineno])
            end = node.end_lineno
            body = lines[start - 1:end]
            if not doc and ast.get_docstring(node):
                d = node.body[0]
                body = lines[start - 1:d.lineno - 1] + lines[d.end_lineno:end]
            return "\n".join(body)
    raise KeyError(name)


def meth(rel, cls, name):
    """Source of a method of a class, dedented, without its docstring."""
    text = _read(rel)
    lines = text.split("\n")
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.ClassDef) and node.name == cls:
            for m in node.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name == name:
                    body = lines[m.lineno - 1:m.end_lineno]
                    if ast.get_docstring(m):
                        d = m.body[0]
                        body = lines[m.lineno - 1:d.lineno - 1] + lines[d.end_lineno:m.end_lineno]
                    return textwrap.dedent("\n".join(body))
    raise KeyError((cls, name))


def between(rel, first, last):
    """Lines from the first line containing `first` to the first later line containing `last` (inclusive), dedented."""
    lines = _read(rel).split("\n")
    i = next(k for k, l in enumerate(lines) if first in l)
    j = next(k for k in range(i, len(lines)) if last in lines[k])
    return textwrap.dedent("\n".join(lines[i:j + 1]))


def jsfn(rel, name):
    """Source of a top-level exported JavaScript function / const: up to the closing brace in column 0, or to the next blank line."""
    lines = _read(rel).split("\n")
    heads = (f"export async function {name}(", f"export function {name}(", f"export const {name} =")
    i = next(k for k, l in enumerate(lines) if l.startswith(heads))
    if lines[i].rstrip().endswith("{"):
        j = next(k for k in range(i + 1, len(lines)) if lines[k] == "}")
    else:
        j = next((k for k in range(i + 1, len(lines)) if not lines[k].strip()), len(lines))
        j -= 1
    return "\n".join(lines[i:j + 1])


def _fig(name, caption, width=5.6):
    """A result figure, only if it has been produced."""
    return [FIG(F.fig(name), caption, width)] if os.path.exists(F.fig(name)) else []


def _v():
    """Every figure quoted in this module, read from the measured metrics."""
    t = F.TAMPER["audit_tamper"]
    caught = {k: v for k, v in t.items() if k != "truncate_tail"}
    e2e = F.E2E
    return dict(
        rb_ok=F.RBAC["matched"], rb_n=F.RBAC["total"],
        unauth=len(F.RBAC["unauthenticated_statuses"]),
        flips=F.TAMPER["ciphertext_bitflip"]["trials"], flips_ok=F.TAMPER["ciphertext_bitflip"]["detected"],
        classes=len(t), classes_caught=len(caught),
        caught_n=sum(v["detected"] for v in caught.values()), caught_t=sum(v["trials"] for v in caught.values()),
        trunc_t=t["truncate_tail"]["trials"], trunc_d=t["truncate_tail"]["detected"],
        entries=F.TAMPER["audit_entries_available"],
        conc_n=F.CONC["4_workers"]["requests"], conc_fail=F.CONC["4_workers"]["failure_at"], conc_chk=F.CONC["4_workers"]["checked"],
        aes25=F.AES["26214400"]["encrypt"]["median"], dec25=F.AES["26214400"]["decrypt"]["median"], sha25=F.AES["26214400"]["sha256"]["median"],
        keygen=F.CRY["rsa_keygen"]["median"], pbk=F.CRY["pbkdf2_120k"]["median"], unwrap=F.CRY["rsa_unwrap"]["median"],
        up1=e2e["1048576"]["encrypted_up"]["median"], pup1=e2e["1048576"]["plain_up"]["median"],
        up10=e2e["10485760"]["encrypted_up"]["median"], pup10=e2e["10485760"]["plain_up"]["median"],
        dn10=e2e["10485760"]["encrypted_down"]["median"], pdn10=e2e["10485760"]["plain_down"]["median"],
        p95_up10=e2e["10485760"]["encrypted_up"]["p95"],
        login=F.API["login_ms"]["median"], health=F.API["health_ms"]["median"], me=F.API["me_ms"]["median"],
        api_up25=F.API["upload_ms"]["26212352"]["median"], api_dn25=F.API["download_ms"]["26212352"]["median"],
        share=F.API["share_ms"], revoke=F.API["revoke_ms"],
        v5000=F.SCALE["5000"]["verify_ms_median"], v1000=F.SCALE["1000"]["verify_ms_median"],
        audit_w=M_AUDIT_W(),
        cpu=F.ENV["cpu"], ram=F.ENV["ram_gb"], py=F.ENV["python"],
        loc_b=F.LOC["backend_py"]["lines"], loc_f=F.LOC["frontend_src"]["lines"], loc_t=F.LOC["tests_py"]["lines"],
    )


def M_AUDIT_W():
    return F.M["audit_write_ms"]["median"]


# ---------------------------------------------------------------------------- novelty and contributions
def novelty_blocks():
    v = _v()
    ba = __import__("scripts.docs.lit", fromlist=["BASE_ANALYSIS"]).BASE_ANALYSIS
    return [
        H2("What the base paper contributes"),
        P(f"The declared base paper {C('base')} is a scheme for sharing electronic health records through a semi-trusted cloud: ciphertext-policy attribute-based encryption {C('cpabe')} over both user and data attributes, "
          f"ClinicalBERT {C('clinbert')} to derive the data attributes from clinical notes, several key-generation centres to avoid key escrow, and a private Hyperledger Fabric ledger {C('fabric')} that holds attribute public keys and policies. "
          "Its evaluation is a calculation: the total encryption and decryption cost is built from operation counts and the measured time of each primitive on an HPE server and a Raspberry Pi 3 B+, "
          "and no end-to-end system, dataset or extraction accuracy is reported. It is a different system from the one built here, so the comparison below is one of ideas and of method, not of numbers."),
        H2("What CipherVault adopts from it"),
        B(*ba["adopts"]),
        H2("What is new in CipherVault"),
        P("CipherVault does not propose a new cryptographic primitive. AES-GCM, RSA-OAEP, PBKDF2, bcrypt and JSON Web Tokens are standard, and each is used as specified. What is new is the integration and the evaluation:"),
        B("**A deployable, general-purpose encrypted file store.** The base paper addresses health records through a calculation; CipherVault is a runnable application with upload, download, replace, delete, sharing, role changes, revocation and a user-visible audit trail, "
          f"served by a FastAPI back end of {v['loc_b']:,} lines and a React front end of {v['loc_f']:,} lines.",
          f"**Browser-side hybrid encryption with per-recipient re-wrapping.** Each file is encrypted in the browser with a fresh AES-256-GCM key; that key is wrapped with RSA-2048-OAEP for the owner and, at share time, re-wrapped locally for every recipient, "
          "so the server never holds a file key or a private key in usable form. Replacing a file's content re-encrypts under the existing key so every share keeps working.",
          "**Role enforcement on ciphertext.** The three roles Owner, Editor and Viewer are checked on the server for every request, while the server only ever stores ciphertext; the access decision and the cryptographic access are separate layers that must both agree.",
          "**A hash-chained audit log with a verification screen.** Every sensitive action, including each denied access, is written to a SHA-256 chain that any signed-in user can re-verify from the interface, which stands in for the base paper's ledger at the scale of one application.",
          f"**Measured, not calculated, overhead.** Cost was measured in Chrome and over loopback on one machine, per primitive and end to end against a plain transfer of the same file (for example a 10 MiB encrypted upload at a median of {F.ms(v['up10'])} ms against {F.ms(v['pup10'])} ms plain), "
          "so the reader sees what the user sees rather than a sum of primitive costs.",
          f"**A tamper study that finds its own weaknesses.** Nine classes of audit-log tampering were tried over {v['entries']} real entries: {v['classes_caught']} classes were caught in all {v['caught_t']:,} trials, tail truncation was caught in {v['trunc_d']} of {v['trunc_t']}, "
          f"a rewrite that recomputes the later hashes is not detected, and {v['conc_n']} concurrent failed logins forked the chain. Reporting these limits is part of the contribution."),
        H2("What is standard"),
        P(f"Galois/Counter Mode {C('gcm')} on AES {C('aes')}, SHA-256 {C('sha')}, RSA-OAEP {C('oaep')}, PBKDF2 {C('pbkdf2')}, {C('sp800132')}, bcrypt {C('bcrypt')}, JSON Web Tokens {C('jwt')} and the Web Cryptography API {C('webcrypto')} "
          f"are used as published. The three-role model follows the user-role-permission structure of role-based access control {C('rbac96')}, {C('rbac01')}, and the hash chain is the familiar linked-log idea {C('audit99')}. "
          "The design pattern of an untrusted storage server with client-held keys is older still " + C('sirius', 'plutus', 'tahoe') + "."),
        H2("What the base paper and the closest related paper have that CipherVault does not"),
        B("**No attribute-based encryption, no ClinicalBERT, no multiple key-generation centres and no blockchain.** The base paper's fine-grained, policy-in-ciphertext access and its absence of key escrow are not reproduced; "
          "CipherVault uses three roles and a server-side check, which is simpler to administer and far cheaper, and which cannot express policies over data content. " + ba["comparability"],
          f"**Features reported by the IJEDR architecture {C('ijedr')} that are absent here.** That paper reports TOTP multi-factor sign-in, ECDSA-signed log entries, 4 MB chunking, PBKDF2 with 310,000 iterations (CipherVault uses {F.PBKDF2_ITER:,}) and an S3 and Vault back end. "
          f"CipherVault has none of these: it encrypts the whole file in memory under a {F.UPLOAD_LIMIT_MB} MB cap, has no second factor and keeps ciphertext on the local file system.",
          f"**Different headline numbers, different experiments.** The IJEDR paper reports +320 ms for a 10 MB upload, 98.6% access-control accuracy over 900 attempts by 50 users and 100% detection of 50 tamper events. CipherVault's matching figures are a measured "
          f"{F.ms(v['up10'] - v['pup10'])} ms difference between medians for a 10 MiB upload on a shared desktop, {v['rb_ok']} of {v['rb_n']} role-matrix cells correct (an exhaustive check, not a user study) and {v['caught_n']:,} of {v['caught_t']:,} edits caught in eight classes with a ninth class missed entirely. "
          "These are not the same experiments and are not ranked against each other."),
    ]


def contribution_blocks():
    v = _v()
    return [
        P("The contributions of the project, stated at the strength the evidence supports, are:"),
        N("**CipherVault, a working encrypted file store**: browser-side AES-256-GCM encryption, RSA-2048-OAEP key wrapping per recipient, PBKDF2-protected private keys, Owner / Editor / Viewer roles enforced by a FastAPI service with "
          f"24 routes and four database tables, bcrypt and JWT authentication and a React interface (landing, sign-in, dashboard, files, file detail, audit and security pages), with {v['loc_b']:,} lines of back-end code, {v['loc_f']:,} lines of front-end code and {v['loc_t']} lines of tests.",
          f"**A measurement of the cost of client-side encryption**: AES-256-GCM, SHA-256, RSA key generation, wrapping and unwrapping and PBKDF2 timed in Chrome from 1 KiB to 25 MiB, and complete upload and download pipelines compared with a plain transfer of the same file "
          f"(medians {F.ms(v['up10'])} against {F.ms(v['pup10'])} ms for a 10 MiB upload and {F.ms(v['dn10'])} against {F.ms(v['pdn10'])} ms for the download, with run-to-run spread of up to about three times on a shared machine).",
          f"**An exhaustive check of the access-control rules**: four principals against nine operations ({v['rb_ok']} of {v['rb_n']} cells as expected), unauthenticated requests ({v['unauth']} of {v['unauth']} rejected) and four kinds of forged token (all rejected), run against the live API.",
          f"**An integrity and tamper study**: {v['flips_ok']:,} of {v['flips']:,} single-bit changes to stored ciphertext rejected by AES-GCM, a wrong key rejected, and nine classes of audit-log tampering tried, with the two undetected cases and the concurrency fault reported.",
          "**Defects and limits documented, not hidden**: tail truncation and consistent rewrite of the audit chain, a forked chain under concurrent writers, a global audit list visible to every signed-in user, no re-keying on revocation, and the same password serving for sign-in and for unlocking the private key, each with the evidence and a proposed fix.",
          f"**A tested, reproducible artefact**: {F.PYTEST_PASSED} passing automated tests, an {F.E2E_TOTAL}-check API end-to-end run, an {F.UI_TOTAL}-step browser walk, a {F.EVAL_TOTAL}-check evaluation script, a metrics script that regenerates every number in the documents, "
          "a screenshot script that drives the real interface, and a facts file from which the documents are built."),
    ]


# ---------------------------------------------------------------------------- scope and limitations
def scope_blocks():
    v = _v()
    return [
        P("The scope follows the six batch objectives and what could be measured on one desktop. It is stated first as what the product and its measurements cover, then as what they leave out, so that a reader does not mistake an experiment for a product feature."),
        H2("In scope"),
        B("**Accounts and sessions:** registration with a name, e-mail address and a password of at least 8 characters; bcrypt-hashed passwords; JWT bearer sessions of 120 minutes; a throttle of 20 login attempts per 300 seconds for one address and e-mail.",
          f"**Key management in the browser:** an RSA-2048 key pair generated at registration; the private key encrypted with an AES-256-GCM key derived by PBKDF2-HMAC-SHA-256 ({F.PBKDF2_ITER:,} iterations, 16-byte salt) and stored as a bundle on the server; the decrypted key held only in memory of the open tab.",
          f"**Files:** encryption in the browser with a fresh 256-bit key and a 12-byte random IV, upload of ciphertext, IV, wrapped key and the SHA-256 of the plaintext, download with local decryption and hash comparison, replace-content, delete, up to {F.UPLOAD_LIMIT_MB} MB per file.",
          "**Sharing and roles:** share by e-mail or user id as Viewer or Editor with a key re-wrapped in the browser for the recipient; change role; revoke; per-file permission list; Owner / Editor / Viewer rules enforced on the server.",
          "**Audit:** a SHA-256 hash-chained event log for registration, login and logout, upload, download, update, delete, share, role change, revocation, denied access and chain verification; a verification route and screen.",
          "**Interface and support:** landing page, dashboard, file list, file detail, shared-with-me, audit log, security profile and vault unlock screens; dark and light themes; demo accounts with synthetic data; a REST API of 24 routes; automated tests and measurement and screenshot scripts.",
          "**Deployment:** one-command local run with SQLite; a Docker composition that selects PostgreSQL through `DATABASE_URL`."),
        H2("Out of scope"),
        B("Attribute-based or policy-in-ciphertext access control, blockchain ledgers and any health-record specific processing, as in the base paper.",
          "Multi-factor authentication, password recovery or key escrow: losing the password loses the private key and with it every file.",
          "Re-encryption of existing files when access is revoked, and recall of keys or ciphertext a recipient has already downloaded.",
          "Chunked or streaming encryption of files larger than 25 MB, deduplication, versioning and file-name encryption.",
          "Cloud object storage (S3-compatible), hardware security modules or a key-management service; ciphertext stays on the local file system.",
          "A signed or externally anchored audit log, and administrative roles; the global role column exists but is not used for decisions.",
          "Penetration testing, formal verification and a usability study."),
        P("The table below sets the scope against the six batch objectives and the storage statement of the abstract, separating what the product does, what was measured and what was not done."),
        TAB("Scope against the batch objectives", ["Objective", "In the product", "Measured", "Not done"],
            [["1 Registration and authentication", "bcrypt cost 12, JWT HS256, 20 attempts / 300 s throttle", f"Login median {F.ms(v['login'])} ms; forged, expired, wrong-secret and alg=none tokens all rejected", "MFA, lockout across restarts"],
             ["2 Encrypt every file before storage", "AES-256-GCM in the browser; server stores ciphertext only", f"AES-GCM 25 MiB median {F.ms(v['aes25'])} ms; {v['flips_ok']:,} of {v['flips']:,} bit flips rejected", "Files above 25 MB, chunking"],
             ["3 RBAC and ownership", "Owner / Editor / Viewer checked per request", f"{v['rb_ok']} of {v['rb_n']} role-matrix cells as expected", "Roles beyond three; admin role"],
             ["4 Integrity on download", "AES-GCM tag plus SHA-256 of the plaintext", "Wrong key and altered ciphertext rejected", "Signed hashes"],
             ["5 Structured audit logs", "Hash chain, 12 event types observed, verification screen", f"{v['classes_caught']} of {v['classes']} tamper classes caught; verification of 5,000 entries {F.ms(v['v5000'])} ms", "Tail-truncation detection; concurrency safety"],
             ["6 Evaluate overhead, access and integrity", "scripts/measure_metrics.py and tests", f"{F.PYTEST_PASSED} pytest, {F.E2E_PASSED} API and {F.UI_PASSED} UI checks", "Multi-user load, user study"]],
            widths=[1.5, 1.8, 1.9, 1.4], align=["l", "l", "l", "l"], size=9),
    ]


def assumption_blocks():
    v = _v()
    return [
        B("The browser is the trusted endpoint: its Web Crypto implementation is correct and the device is not compromised. Endpoint security is outside the system.",
          "The server delivers the unmodified JavaScript of the application; a hostile server could ship altered code, which no part of the design prevents.",
          "A user chooses a password strong enough to resist guessing against the PBKDF2-protected key bundle, which the server stores.",
          "Public keys held by the server belong to the person named: no out-of-band verification of a recipient's key is performed, so the server could in principle substitute one.",
          "The audit log has a single writer at a time and the database is not edited by anyone able to recompute the chain.",
          f"The measurements on one {v['cpu']} desktop with {v['ram']} GB of memory, Chrome and Python {v['py']} are indicative of a small local deployment; the machine also ran other jobs, so timings carry noise.",
          "The five demo files and the generated measurement files are fictional; no real personal or confidential data were stored.",
          "One user session per browser tab and a handful of users: the application was designed and measured for a single organisation, not for public scale."),
    ]


def limitation_blocks():
    v = _v()
    return [
        H2("Cryptographic design"),
        B("**Revocation is not recall.** Revoking a share deletes the recipient's wrapped key on the server and stops further downloads (a download after revoke returned HTTP 403), but a recipient who already holds the file key or the plaintext keeps it. The file is not re-keyed.",
          "**An editor's update reuses the file key.** The new content is encrypted under the existing key with a fresh random 96-bit IV; the collision bound of GCM applies to very many updates, and the server cannot check that the new ciphertext and IV match.",
          "**The server serves the code that does the cryptography.** A compromised or malicious server could deliver JavaScript that leaks keys; this is the trust problem of deployed browser-based end-to-end encryption " + C('mega') + ", and no content-security or integrity pinning is implemented.",
          "**One password plays two roles.** The browser sends the password to the sign-in route and uses the same password to derive the key that unlocks the stored private-key bundle. The server only keeps a bcrypt hash, but it sees the password at every sign-in, so a hostile server could attempt to open the bundle.",
          f"**Weaker key derivation than the closest related paper.** PBKDF2 uses {F.PBKDF2_ITER:,} iterations against 310,000 reported by the IJEDR paper {C('ijedr')}; no memory-hard function is used.",
          "**Password loss means data loss.** No recovery or escrow exists; this is stated to the user but is a real cost.",
          "**Public keys are trusted as served.** No key fingerprint check between users exists.",
          "**The plaintext hash is stored in clear.** The SHA-256 of each file sits beside the ciphertext, so a server-side reader holding a guess of a file's exact contents can confirm the guess."),
        H2("Audit log"),
        B(f"**Tail truncation is not detected.** Removing the newest entries left a chain that still verifies ({v['trunc_d']} of {v['trunc_t']} detected), because the verifier only checks internal consistency.",
          "**A consistent rewrite is not detected.** Anyone able to edit the database can alter an entry and recompute every later hash; the chain has no secret key and no external anchor.",
          f"**Concurrent writers fork the chain.** The last hash is read and the new row committed without a lock; {v['conc_n']} concurrent failed logins on four workers left a chain that no longer verifies (first bad entry {v['conc_fail']:,} of {v['conc_chk']:,}). The single-writer assumption is not enforced.",
          "**The global event list is visible to every signed-in user** through `GET /api/audit`, including other users' e-mail addresses and file identifiers."),
        H2("Product"),
        B(f"**Whole-file, in-memory encryption.** Files up to {F.UPLOAD_LIMIT_MB} MB only; larger uploads are refused with HTTP 413 and there is no streaming or chunking.",
          "**Metadata in clear.** File name, size, MIME type, owner and timestamps are stored unencrypted so that listing works.",
          "**Session and throttle.** The JWT lives in `sessionStorage` and is exposed to script injection in the page; the login throttle is in memory and resets on restart; no refresh or server-side logout revocation of a token exists.",
          "**SQLite by default.** The abstract names PostgreSQL; it is supported through `DATABASE_URL` and the Docker composition, but the PostgreSQL path was not run in this work.",
          "**Single-node local storage.** Ciphertext is on the local file system and the application has no replication or backup."),
        H2("Evaluation and process"),
        B(f"**One shared machine.** All timings come from one {v['cpu']} desktop with {v['ram']} GB while other programs were running; run-to-run spread reached about three times at 10 MiB, so differences of a few milliseconds in the encrypted-against-plain comparison are inside the noise.",
          "**Browser timer resolution.** Chrome's clock steps in 0.1 ms, so the 1 KiB and 64 KiB operations were timed in batches of 200 and are averages.",
          "**Exhaustive, not statistical, access checks.** The role matrix proves the implemented rules for one file and four principals; it is not a user study and does not include concurrent edits.",
          "**Synthetic data and no user study.** No real users, no usability test and no independent security audit were carried out; the evaluation script's own browser-labelled timings are Python timings and were superseded by the Chrome measurements."),
        H2("How the limits affect the reading of the results"),
        P("The access-control and integrity results are the most dependable part of the work because they are exhaustive over the implemented operations and use a deterministic pass or fail. "
          "The timing results are indicative of a small local deployment, not benchmarks. The audit results show what a plain hash chain can and cannot promise: it detects edits, deletions, swaps and insertions, it does not detect removal of the tail or a full rewrite, and it needs a writer lock and an external anchor before it can be called tamper-evident in a hostile setting."),
    ]


def not_measured_blocks():
    return [
        P("The following were not measured, so no document claims anything about them. Each is either outside what the product does or beyond what one desktop and a short project could test."),
        B("Behaviour under many simultaneous users: only one concurrency test (100 failed logins on four workers) was run, and it exposed the audit fault.",
          f"Files larger than {F.UPLOAD_LIMIT_MB} MB and memory use of whole-file encryption near the cap.",
          "Firefox, Safari, mobile browsers beyond a 360 px layout check, and older browsers without the Web Crypto features used.",
          "The PostgreSQL path and the Docker image build; only SQLite on Windows was exercised.",
          "A screen-reader accessibility audit; keyboard use and reduced-motion support were provided but not assessed by users.",
          "Usability for real users, perceived waiting time and error recovery.",
          "Security by an independent party: no penetration test, no code audit and no side-channel analysis.",
          "Long-term storage behaviour: backup, restore, disk-full and crash recovery.",
          "Network conditions other than loopback: all API timings exclude real network latency."),
        P("None of these is hidden in a headline number. The statements of the abstract about cloud storage and professional key management are treated as future scope, not results."),
    ]


# ---------------------------------------------------------------------------- code walk-throughs
def walkthrough_blocks():
    up = jsfn("frontend/src/lib/vault.js", "uploadFile")
    enc = jsfn("frontend/src/lib/vaultCrypto.js", "encryptFile") + "\n\n" + jsfn("frontend/src/lib/vaultCrypto.js", "wrapFileKey")
    validate = between("backend/app/api/files.py", "data = await ciphertext.read()", "Invalid SHA-256 digest")
    down = jsfn("frontend/src/lib/vault.js", "fetchAndDecrypt")
    share_c = jsfn("frontend/src/lib/vault.js", "shareWith")
    share_s = between("backend/app/api/sharing.py", "try:", "wrapped_fek must be base64")
    perm = "\n\n".join(fn("backend/app/services/permission_service.py", n) for n in ("get_effective_role", "can_write", "can_delete", "can_share"))
    audit = "\n\n".join([fn("backend/app/services/audit_service.py", "_hash_event"), fn("backend/app/services/audit_service.py", "verify_chain")])
    rec = between("backend/app/services/audit_service.py", "last = db.query(AuditLog)", "db.refresh(entry)")
    sec = fn("backend/app/core/security.py", "hash_password") + "\n\n" + fn("backend/app/core/security.py", "create_access_token") + "\n\n" + fn("backend/app/core/security.py", "decode_access_token")
    login = fn("backend/app/api/auth.py", "login")
    return [
        H2("Browser-side encryption and key wrapping (`vault.js`, `vaultCrypto.js`)"),
        P("Upload is the one place where plaintext exists, and it exists only in the browser. The file is read into memory, its SHA-256 is computed, a fresh 256-bit AES-GCM key (the file encryption key, FEK) is generated, "
          "the file is encrypted with a new random 12-byte IV, and the FEK is wrapped with the owner's RSA-2048 public key using OAEP. Only the ciphertext, the IV, the wrapped key and the hash are placed in the multipart form; "
          "the unwrapped key is never sent. AES-GCM appends a 16-byte authentication tag, which is the whole of the 16-byte size overhead measured in Chapter 8."),
        CODE(up, 7.5),
        CODE(enc, 7.5),
        H2("Server-side validation of an upload (`files.py`)"),
        P("The server cannot read the content, so it validates what it can: that the body is not empty, that it is within the size limit (HTTP 413), that the file name and declared size are sane, "
          "that the IV is valid base64 and decodes to exactly 12 bytes, that the wrapped key is valid base64 and that the plaintext hash has the shape of a SHA-256 digest. "
          "It then stores the object under a random 32-hex-character name, so the original name never touches the file system. These checks catch malformed requests; they cannot tell a genuine ciphertext from random bytes, which is why integrity is verified by the client on download."),
        CODE(validate, 7.5),
        H2("Download, decryption and integrity verification (`vault.js`)"),
        P("The download route returns ciphertext with the IV, the caller's own wrapped key and the stored hash in response headers. The browser unwraps the FEK with the private key held in memory, decrypts, and fails if the AES-GCM tag does not authenticate; "
          "it then recomputes SHA-256 of the plaintext and refuses to save the file on a mismatch. The two checks are independent: the tag protects the ciphertext, the hash binds the result to what the owner uploaded."),
        CODE(down, 7.5),
        H2("Sharing with a re-wrapped key (`vault.js`, `sharing.py`)"),
        P("To share, the owner's browser looks up the recipient, fetches the recipient's public key, unwraps its own copy of the FEK, and wraps it again for the recipient. The server receives only the new 256-byte wrapped value and stores it with the role. "
          "The server checks the length (an RSA-2048 OAEP output is 256 bytes), that the caller owns the file, that the target is a different registered user and that no permission exists yet."),
        CODE(share_c, 7.5),
        CODE(share_s, 7.5),
        H2("Role decisions (`permission_service.py`)"),
        P("Every file route calls `get_effective_role` and then one predicate. The role is owner when the user id matches the file's owner, otherwise the role stored in the permission row, otherwise none. "
          "Read is allowed to all three roles, write to owner and editor, and delete and share only to the owner. A denied request writes an `unauthorized_access` event before the 403 is returned. "
          "Keeping the rules in four short functions made the exhaustive 36-cell matrix test possible."),
        CODE(perm, 7.5),
        H2("The hash-chained audit log (`audit_service.py`)"),
        P("Each event stores the previous entry's hash and its own hash, which is the SHA-256 of the previous hash, the timestamp, user, file, action, success flag and details joined by a vertical bar. The first entry uses the constant `GENESIS`. "
          "`verify_chain` walks the table in id order, recomputes every hash and checks that each `previous_hash` equals the previous entry's `current_hash`. "
          "The code also shows both weaknesses reported in Chapter 8: `record_event` reads the last row and commits without a lock, so concurrent writers can both extend the same predecessor, and the verifier has nothing to compare the final hash against, so entries removed from the end leave a valid chain."),
        CODE(audit, 7.5),
        CODE(rec, 7.5),
        H2("Passwords and tokens (`security.py`, `auth.py`)"),
        P("Passwords are hashed with bcrypt at cost 12 and are never stored or logged; tokens are HS256 JWTs with the user id as subject and a 120-minute expiry, and any decoding error is treated as an invalid token. "
          "The login route applies the in-memory throttle first, answers every failure with the same message so that it does not reveal which addresses exist, and records a `login_failure` or `login_success` event. "
          "The same function receives the plaintext password that the browser later uses to unlock the private key, which is the double role of the password noted in the limitations."),
        CODE(sec, 7.5),
        CODE(login, 7.5),
    ]


def decision_blocks():
    v = _v()
    return [
        P("The main implementation decisions, the reason for each and the cost each brought are listed in the table below."),
        TAB("Implementation decisions and their reasons", ["Decision", "Reason", "Cost or what the measurements showed"],
            [["Encrypt in the browser, not on the server", "The server and its backups must never hold plaintext or usable keys", f"Server is trusted only for availability and role checks; but it serves the JavaScript. AES-GCM of 25 MiB takes a median {F.ms(v['aes25'])} ms"],
             ["AES-256-GCM for files", "Confidentiality and integrity in one standard operation, implemented natively by the browser", "16-byte tag overhead; random 96-bit IVs must not repeat under one key"],
             ["A fresh random key per file, wrapped per user", "Sharing needs no file re-encryption and one user's key leaks no other file", f"Wrapping costs {F.ms(F.CRY['rsa_wrap']['median'])} ms and unwrapping {F.ms(v['unwrap'])} ms; revocation cannot recall a key already given"],
             ["RSA-2048-OAEP rather than attribute-based encryption", "Three roles do not need policy-in-ciphertext; wrapping is cheap and supported by Web Crypto", f"Key generation median {F.ms(v['keygen'])} ms once per account; no policies over content"],
             ["Private key encrypted with a PBKDF2-derived key and stored on the server", "A user can sign in on any device without carrying a key file", f"PBKDF2 median {F.ms(v['pbk'])} ms at {F.PBKDF2_ITER:,} iterations; same password signs in and unlocks; offline guessing is possible if the bundle leaks"],
             ["bcrypt cost 12 and JWT", "Standard, slow-by-design password hashing and stateless sessions", f"Login median {F.ms(v['login'])} ms dominates the light calls (health {F.ms(v['health'])} ms); tokens cannot be revoked before expiry"],
             ["Server-side RBAC in four small functions", "One place for the decision; easy to test exhaustively", f"{v['rb_ok']} of {v['rb_n']} matrix cells as expected; global role column unused"],
             ["SHA-256 of the plaintext stored beside the ciphertext", "A second, independent integrity check after decryption", "Hash in clear metadata lets a server-side reader confirm a guessed file"],
             ["Hash-chained audit log in the application database", "Tamper evidence without a blockchain, readable by the interface", f"Verification of 5,000 entries takes {F.ms(v['v5000'])} ms; truncation, rewrite and concurrent writers are not covered"],
             ["Ciphertext on the file system under random names, metadata in SQL", "Keeps large objects out of the database and the storage layer swappable", "No replication; stored name unrelated to the content"],
             ["Whole-file encryption with a 25 MB cap", "Simplest correct use of Web Crypto, which has no streaming GCM", f"Upload of 25 MiB through the API median {F.ms(v['api_up25'])} ms; larger files refused"],
             ["SQLite default, PostgreSQL by configuration", "One-click local run for demonstration", "PostgreSQL path untested"]],
            widths=[1.7, 2.3, 2.6], align=["l", "l", "l"], size=9),
        P("Three decisions deserve a longer note. The first is to put the cryptography in the browser. It is the only design in which a stolen database, a curious administrator and a network observer all see ciphertext, and it shifts the trust to the code the server delivers; "
          "the cost is the whole class of limitations around key custody, recovery and a server that serves the code. "
          "The second is the single password. It keeps the interface simple, since signing in also unlocks the vault, but it gives the server a chance to see the secret that protects the key bundle; separating an authentication secret from a key-derivation secret is the first design change a production version should make. "
          "The third is the plain hash chain: it is cheap, visible in the interface and good enough to catch accidental and naive tampering, and the study shows precisely which attacks it does not stop."),
    ]


# ---------------------------------------------------------------------------- conclusion
def _lessons():
    v = _v()
    return [
        f"**Encryption in the browser costs little.** AES-256-GCM encrypts 25 MiB in a median {F.ms(v['aes25'])} ms and decrypts it in {F.ms(v['dec25'])} ms; for a 10 MiB file the whole encrypted upload takes a median {F.ms(v['up10'])} ms against {F.ms(v['pup10'])} ms for a plain upload "
        f"(p95 {F.ms(v['p95_up10'])} ms), a difference that is within the run-to-run spread of the shared machine. Key generation, once per account, takes {F.ms(v['keygen'])} ms.",
        f"**The access rules held in every checked case.** All {v['rb_n']} cells of the role matrix behaved as intended, unauthenticated requests ({v['unauth']} of {v['unauth']}) and four kinds of forged token were refused, and a download after revocation returned HTTP 403. This is exhaustive over the implemented operations, not a user study.",
        f"**Integrity is enforced twice.** All {v['flips_ok']:,} of {v['flips']:,} single-bit changes to stored ciphertext were rejected by the AES-GCM tag, and a wrong key failed to decrypt; the browser additionally refuses to save a file whose SHA-256 does not match.",
        f"**The audit chain catches edits but not removal or rewriting.** Eight of nine tamper classes were caught in all {v['caught_t']:,} trials, tail truncation in {v['trunc_d']} of {v['trunc_t']}, and a rewrite that recomputes later hashes was not detected. "
        f"{v['conc_n']} concurrent failed logins forked the chain (first bad entry {v['conc_fail']:,} of {v['conc_chk']:,}). A writer lock and an external anchor are required.",
        f"**Costs sit in the slow-by-design steps.** A sign-in takes a median {F.ms(v['login'])} ms because of bcrypt and unlocking the vault {F.ms(v['pbk'])} ms for PBKDF2, while an authenticated `me` call takes {F.ms(v['me'])} ms; verifying 5,000 audit entries takes {F.ms(v['v5000'])} ms and grows linearly.",
        "**The trust boundary is the delivered code and the password.** The server never sees plaintext or a usable key in normal operation, but it serves the JavaScript that does the cryptography and receives the password that protects the key bundle; revocation cannot recall what a recipient already holds.",
    ]


def _objective_table():
    v = _v()
    return TAB("Objectives against outcomes", ["Objective", "Outcome", "Evidence"],
               [["1 Registration and authentication with hashed credentials and JWT sessions", "Achieved", f"bcrypt cost 12, HS256 tokens with 120-minute expiry; login median {F.ms(v['login'])} ms; forged, expired, wrong-secret and alg=none tokens all rejected"],
                ["2 Encrypt every file with AES-256-GCM before it reaches storage", "Achieved", f"Encryption in the browser; the stored object is ciphertext; {v['flips_ok']:,} of {v['flips']:,} bit flips rejected; limited to {F.UPLOAD_LIMIT_MB} MB per file"],
                ["3 Role-based access with ownership checks", "Achieved", f"{v['rb_ok']} of {v['rb_n']} role-matrix cells as expected; revocation stops downloads (403) but does not recall keys"],
                ["4 Integrity verification on download", "Achieved", "AES-GCM tag plus SHA-256 of the plaintext; a wrong key or altered ciphertext is rejected"],
                ["5 Audit logs of uploads, downloads, deletes and denials", "Achieved with defects", f"All four event kinds logged in a hash chain with a verification screen; tail truncation ({v['trunc_d']} of {v['trunc_t']}) and concurrent writers are not handled"],
                ["6 Evaluate overhead, access-control correctness and integrity", "Achieved within limits", f"Chrome and API measurements, exhaustive role matrix and tamper study; one shared machine, no user study; {F.PYTEST_PASSED} pytest, {F.E2E_PASSED} API and {F.UI_PASSED} UI checks passed"]],
               widths=[2.3, 1.1, 3.2], align=["l", "l", "l"], size=9.5)


def conclusion_blocks():
    v = _v()
    return [
        H2("Summary"),
        P("CipherVault is a working secure file store in which the browser encrypts every file before upload, the server stores only ciphertext and enforces Owner, Editor and Viewer roles, "
          f"and every sensitive action is written to a hash-chained audit log. It was built with FastAPI, SQLAlchemy, React and the Web Crypto API, and measured on one {v['cpu']} desktop. "
          "The honest outcome is positive on confidentiality, integrity and access control, and mixed on the audit trail, whose limits were found by the project's own tamper study."),
        H2("Objectives against outcomes"),
        _objective_table(),
        H2("Key findings"),
        N(*_lessons()),
        P("The abstract's statement that the system can later be extended to cloud storage and professional key management is a statement of future scope; it is not demonstrated here. "
          "The same holds for PostgreSQL, which is supported by configuration but was not exercised."),
        H2("Closing remark"),
        P("The value of the project is a runnable, measured design and a precise list of what to repair. With a writer lock and an external anchor for the audit chain, a separate secret for key derivation, re-keying on revocation and "
          "chunked encryption for large files, the same code would be a sound base for a small organisation's confidential document store."),
    ]


def chapter9_blocks():
    v = _v()
    body = [
        H2("Summary"),
        P("CipherVault was built to store sensitive files so that neither the storage server nor a stolen database can read them, so that only authorised users can reach them, so that tampering is noticed and so that every access can be reconstructed afterwards. "
          "At registration the browser generates an RSA-2048 key pair and protects the private key with a key derived from the password. For each upload it computes the SHA-256 of the file, "
          "encrypts it with a fresh AES-256-GCM key, wraps that key for the owner and sends only ciphertext, IV, wrapped key and hash. "
          "A FastAPI service with 24 routes authenticates users with bcrypt and JWT, enforces the Owner, Editor and Viewer roles on every request, stores the ciphertext under a random name and records each sensitive action in a SHA-256 hash chain. "
          "Sharing re-wraps the file key in the owner's browser for each recipient; revoking deletes that wrapped key."),
        P(f"The system was measured rather than trained: there is no machine-learning model and no dataset in it. Primitive and end-to-end timings were taken in Chrome and over loopback, the role rules were checked across {v['rb_n']} cells, "
          f"{v['flips']:,} bit flips and nine kinds of audit tampering were tried, and {F.PYTEST_PASSED} automated tests, {F.E2E_PASSED} API checks and {F.UI_PASSED} browser steps pass. The screenshots in this report were taken from the running application with demo data."),
        H2("Objectives achieved"),
        _objective_table(),
        P("Objectives 1 to 4 were met; objective 5 was met with two audit defects, and objective 6 within the limits of one shared machine and no user study."),
        H2("Key findings"),
        N(*_lessons()),
        *_fig_conclusion(),
        P("A further finding concerns method. Some of the most useful results came from trying to break the system: the role matrix confirmed the rules, but the tamper study and a concurrency run exposed faults that the passing unit tests did not, "
          "and the evaluation script's browser-labelled timings turned out to be Python timings, which is why the Chrome measurements replaced them."),
        H2("Practical applications"),
        B("**A confidential document store for a small organisation or a student team.** One command starts it locally; files stay encrypted at rest and on the server, and the audit screen shows who did what.",
          "**A teaching and reference implementation.** The measured costs of each primitive, the role matrix and the tamper study show what hybrid client-side encryption, role checks and a hash chain do and do not provide.",
          "**A test bed for hardening.** The scripts rerun every number, so each fix listed in Chapter 10 can be checked against the same experiments.",
          "**Sharing with accountability.** Per-recipient wrapped keys let an owner grant and withdraw access to a file without re-uploading it."),
        H2("Known limitations"),
        P("Revocation does not recall what a recipient already holds, the audit chain does not detect tail truncation or a consistent rewrite and can fork under concurrent writers, the global audit list is visible to every signed-in user, "
          "the server delivers the code that does the cryptography and receives the password that protects the key bundle, files are limited to 25 MB and encrypted whole, and the timings come from one shared machine with no user study. Chapter 8 and the limitations document give the full list."),
    ]
    if F.REPORT:
        body = _ch9_trim(body)
    return [H1("CHAPTER 9: CONCLUSION")] + renum(body, "9")


def _fig_conclusion():
    return _fig("f06_tamper_detection.png", "Detection rate of each audit-log tamper class and of ciphertext bit flips.", 5.4)


def _ch9_trim(body):
    """Report variant: no figure, no method paragraph, the four practical applications cut to two."""
    out = []
    for b in body:
        if b[0] == "fig":
            continue
        if b[0] == "p" and b[1].startswith(("A further finding concerns method", "The system was measured rather than trained")):
            continue
        if b[0] == "b" and b[1][0].startswith("**A confidential document store"):
            b = ("b", [b[1][0], b[1][1]])
        out.append(b)
    return out


# ---------------------------------------------------------------------------- future scope
def _roadmap():
    return TAB("Roadmap", ["Stage", "Work", "Done when"],
               [["1. Repair what was measured", "Writer lock and an externally anchored or HMAC-signed chain head; restrict `GET /api/audit` to own events; separate the sign-in secret from the key-derivation secret; PBKDF2 at 310,000 iterations or Argon2id",
                 "The 200-trial truncation test and the 100-login concurrency test both report a valid, detecting chain"],
                ["2. Close the design gaps", "Re-key on revoke; chunked streaming encryption beyond 25 MB; MFA; content-security policy and subresource integrity; out-of-band public-key fingerprints", "A revoked user's saved key no longer opens new content; a 200 MB file uploads"],
                ["3. Scale and deploy", "S3-compatible object storage, a key-management service, PostgreSQL in continuous integration, a queue for audit writes", "The Docker composition passes the same suite on PostgreSQL"],
                ["4. Evaluate with people", "A usability study and an independent security review", "Task success rates and review findings are in the report"]],
               widths=[1.5, 3.2, 1.9], align=["l", "l", "l"], size=9.5)


def future_blocks():
    return [
        H2("Repair the weaknesses found"),
        B("**Make the audit log tamper-evident.** Take a lock around reading the last hash and writing the new row (or a single writer queue), sign each entry or the chain head with a server-held HMAC key, and publish the head to a separate place so that truncation and consistent rewriting become detectable "
          + C('audit99', 'tamper09') + ". Rerun the 199-trial truncation test and the 100-login concurrency test.",
          "**Restrict the audit list.** Return only the caller's own events from `GET /api/audit`, and let the owner of a file see that file's events.",
          "**Separate the two secrets.** Derive an authentication value in the browser (or use an augmented password protocol) so the server never receives the password that unlocks the key bundle.",
          f"**Strengthen key derivation.** Raise PBKDF2 to at least the 310,000 iterations used by the IJEDR paper {C('ijedr')}, or switch to a memory-hard function such as Argon2id."),
        H2("Close the design gaps"),
        B("**Re-key on revoke.** Generate a new file key, re-encrypt the file and re-wrap for the remaining users, so a revoked user's saved key no longer opens new content.",
          "**Chunked, streaming encryption** with per-chunk authentication, so that files above 25 MB can be handled without holding them in memory.",
          "**Multi-factor sign-in** (TOTP), as in the closest related paper, and account recovery by an optional recovery key.",
          "**Key transparency.** Show a fingerprint of a recipient's public key and let users compare it out of band, so a substituted key is noticed.",
          "**Content-security policy and subresource integrity** to narrow the problem of a server that serves the cryptographic code " + C('mega') + "."),
        H2("Scale and deploy"),
        B("S3-compatible object storage behind the existing storage module, and a key-management service or hardware security module for server-side secrets such as the JWT signing key.",
          "PostgreSQL in continuous integration, so the path that the abstract names is tested on every change.",
          "Measurement under many simultaneous users, with the audit writes moved to a queue."),
        H2("Evaluate with people"),
        B("A usability study of the unlock, share and revoke flows, and an independent penetration test and code review.",
          "A comparison with an attribute-based design on the same files, using the same measured, end-to-end method rather than calculated primitive costs " + C('base', 'cpabe') + "."),
        P("The order matters: the repairs in the first group are small and testable, and they should be done before new features, because every later stage builds on an audit trail and a key hierarchy that can be trusted."),
        _roadmap(),
    ]


def chapter10_blocks():
    body = [
        H2("Improvements to the existing system"),
        P("Every improvement below answers a defect that Chapter 8 measured, so each has a test it must pass."),
        B("**Fix the audit chain.** Add a lock or single-writer queue around `record_event`, sign the chain head with an HMAC key kept outside the database and publish it elsewhere. A test: the 100-concurrent-login run must leave a valid chain, and the 199-trial tail-truncation test must detect every trial.",
          "**Limit what the audit list reveals.** `GET /api/audit` should return a user's own events and let owners read their files' histories. A test: a viewer must not see another user's e-mail address in the list.",
          "**Split the password's two roles.** Derive a separate authentication value in the browser so that the server never sees the secret that unlocks the key bundle. A test: the sign-in request must not contain the key-derivation password.",
          f"**Raise key-derivation cost.** Move from {F.PBKDF2_ITER:,} PBKDF2 iterations to at least 310,000 or to Argon2id; measure the unlock time again (now a median {F.ms(_v()['pbk'])} ms).",
          "**Re-key on revocation** so that revoking a user also protects later content."),
        P("Two of these repairs change numbers in earlier chapters: the tamper study would report all nine classes caught, and the unlock time would rise, which is the real cost of stronger key derivation."),
        H2("Additional features"),
        P("The features below follow limits recorded in this work and the features of the closest related paper."),
        B("**Chunked encryption** with per-chunk authentication and resumable uploads for files above 25 MB.",
          "**Multi-factor authentication and account recovery** by an optional recovery key, so that a forgotten password need not destroy files.",
          "**Key fingerprints and key transparency** to defend against a substituted public key.",
          "**File versions and encrypted file names** to reduce the metadata kept in clear.",
          "**An administrator role** for account management that still cannot read file contents."),
        H2("Scalability and deployment"),
        P(f"CipherVault was built and measured for one organisation on one machine. The server reads the whole upload into memory, serialises audit writes by assumption and keeps its login throttle in a process dictionary; that is enough for the measured workloads (25 MB uploads in a median {F.ms(_v()['api_up25'])} ms) and not for a public service."),
        B("Move ciphertext to S3-compatible object storage behind the storage module and keep metadata in PostgreSQL, with the PostgreSQL path tested in continuous integration.",
          "Move audit writes to a queue with a single consumer and add a shared throttle (for example in Redis) so limits survive restarts and several workers.",
          "Keep the JWT signing key and any server-side secrets in a key-management service, and set the application's secrets through the environment rather than the defaults in the configuration file.",
          "Add monitoring of failed logins and audit verification as a scheduled job."),
        P("Deployment also needs a decision about trust: a hosted service would have to publish and pin its client code so users can check that the JavaScript is the audited build."),
        H2("Further research"),
        P("The open questions are about what the audit trail and the key hierarchy can promise, and the measurement scripts are ready to answer them."),
        B("How much does an externally anchored chain add to the cost of an audit write (now a median " + F.ms(_v()["audit_w"]) + " ms) and to verification time?",
          "Can revocation with lazy re-encryption give the benefit of re-keying without re-uploading every file?",
          "How do users understand the unlock, share and revoke flows, and where do they make unsafe choices?",
          "What does an attribute-based design cost end to end in a general file store, measured with the same method as here, compared with the calculated costs of the base paper " + C('base') + "?"),
        H2("Risks and dependencies"),
        B("**Browser support.** The design depends on Web Crypto features of current browsers; only Chrome was measured.",
          "**Library drift.** Updates to the cryptography, JWT and bcrypt libraries should be tested against the same suite.",
          "**Operational secrets.** The default JWT secret in the configuration is a placeholder and must be replaced in any deployment."),
        P("The order of work matters: the repairs in the first section are small and testable, and they should be done before any new feature, because every later stage builds on an audit trail and key hierarchy that can be trusted."),
        _roadmap(),
    ]
    if F.REPORT:
        body = _ch10_trim(body)
    return [H1("CHAPTER 10: FUTURE SCOPE")] + renum(body, "10")


def _ch10_trim(body):
    """Report variant: no roadmap table, no risks section, two lead paragraphs and the sixth and later bullets of each list cut."""
    out, skip = [], False
    for b in body:
        if b[0] == "h2":
            skip = b[1].startswith("Risks")
        if skip or b[0] == "tab":
            continue
        if b[0] == "p" and b[1].startswith(("Every improvement below", "The order of work")):
            continue
        if b[0] == "b" and len(b[1]) > 5:
            b = ("b", b[1][:5])
        out.append(b)
    return out
