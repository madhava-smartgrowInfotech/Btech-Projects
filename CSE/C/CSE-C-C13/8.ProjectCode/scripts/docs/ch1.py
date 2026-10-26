"""Chapter 1: Introduction."""

from . import facts as F
from .blocks import B, H1, H2, N, P, TAB
from .refs import N as C


def trim(blocks, drop=(), drop_sections=(), replace=None, table_rows=None):
    """Report-mode trimming helper (shared by the other chapter modules). drop: block-text prefixes to remove; drop_sections: heading
    prefixes whose whole section is removed; replace: {prefix: block}; table_rows: {caption prefix: keep(row)}."""
    replace = replace or {}
    table_rows = table_rows or {}
    out, skip_level = [], None
    for b in blocks:
        if b[0] in ("h1", "h2", "h3"):
            lvl = int(b[0][1])
            if skip_level is not None and lvl <= skip_level:
                skip_level = None
            if skip_level is None and any(b[1].startswith(x) for x in drop_sections):
                skip_level = lvl
        if skip_level is not None:
            continue
        v = b[1]
        k = v[0] if isinstance(v, list) and v else (v if isinstance(v, str) else "")
        if any(k.startswith(x) for x in drop):
            continue
        hit = next((x for x in replace if k.startswith(x)), None)
        if hit:
            if replace[hit] is not None:
                out.append(replace[hit])
            continue
        if b[0] == "tab":
            cap = next((x for x in table_rows if b[1].startswith(x)), None)
            if cap:
                b = ("tab", b[1], b[2], [r for r in b[3] if table_rows[cap](r)], b[4], b[5], b[6])
        out.append(b)
    return out


def blocks():
    lo = F.LOC
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        H2("1.1 Introduction to the Project Domain"),
        P("Organisations and individuals now keep contracts, medical letters, board papers and source archives on storage they do not run themselves: a cloud drive, a departmental file server, a shared "
          "folder behind a web portal. The storage provider, its administrators, anyone who obtains a database backup and an attacker who reaches the server are all, in practice, able to read what is stored "
          "if the files are held as plaintext. The domain of this project is therefore cybersecurity applied to file storage, and in particular three techniques that are usually studied separately: "
          "cryptography that protects the content, access control that decides who may do what, and audit logging that lets an incident be reconstructed afterwards."),
        P(f"The project, named CipherVault, is a working web application that combines the three. Every file is encrypted in the user's browser with AES-256-GCM before it is uploaded, "
          "so the server stores ciphertext only. A role model with three levels (Owner, Editor, Viewer) is enforced by the server on every request, and every security-relevant event is written to an audit log whose "
          f"entries are linked by SHA-256 hashes so that editing the history can be detected. The design follows the client-side encryption pattern described in recent file-storage work {C('ijedr')} and in older "
          f"research on storage over untrusted servers {C('sirius')}, {C('plutus')}, but it is built as a complete, runnable and measured system rather than as a design sketch."),
        H2("1.2 Background and Motivation"),
        P("Three developments make the problem practical. First, browsers now provide a standard cryptographic interface, the Web Cryptography API "
          f"{C('webcrypto')}, which performs AES, RSA, PBKDF2 and SHA-256 natively and fast, so a web page can encrypt a file without any plug-in or native code. Second, authenticated encryption modes such as "
          f"Galois/Counter Mode {C('gcm')} give confidentiality and integrity in a single operation, which removes a class of mistakes that came from combining a cipher with a separate checksum. "
          f"Third, hybrid encryption, in which a random symmetric key encrypts the file and a public-key scheme such as RSA-OAEP {C('oaep')} wraps that key for each authorised reader, makes it possible to share an encrypted file "
          "without re-encrypting it or revealing a key to the server."),
        P(f"Deployed systems show that the idea is easy to state and hard to get right. The analysis of the MEGA service {C('mega')} found that weaknesses in the way keys were handled allowed an attacker to recover users' keys and files "
          "even though the service was advertised as end-to-end encrypted. Access control has its own history: role-based models "
          f"{C('rbac96')}, {C('rbac01')} are well understood, yet in a file store the role check must also be tied to key distribution, because a role that is revoked on the server is meaningless if the reader already holds "
          "the file key. Finally, the audit trail is often the weakest part: a log that an administrator can edit proves nothing, and the literature on tamper-evident logging "
          f"{C('audit99')}, {C('tamper09')} exists precisely because plain log files are not trustworthy evidence."),
        P(f"The declared base paper of this batch {C('base')} addresses a neighbouring problem. It protects electronic health records with attribute-based encryption, extracts data attributes from clinical notes with a language model and "
          "stores keys and policies on a permissioned blockchain. Its motivation, that the cloud must not be trusted with readable records and that every access must be policy-controlled and accountable, is the motivation of this project. "
          "Its machinery is considerably heavier than a general file store needs, and its evaluation is a calculation from primitive timings rather than a measurement of a running system "
          "(Section 2.2). The project therefore keeps the motivation and replaces the machinery with a simpler design that can be built, run and measured by a small team."),
        H2("1.3 Problem Statement"),
        P("The batch documents state the problem in four sentences, which this report adopts without change in meaning:"),
        B("Files stored without client-side encryption are readable by the storage provider.",
          "Without role-based control, any authenticated user may reach another user's files.",
          "Tampering goes undetected when no integrity check is performed on retrieval.",
          "Without audit logs, a security incident cannot be reconstructed afterwards."),
        P("Stated as one problem: design, implement and evaluate a file-storage system in which the server never holds readable content, each user can reach only the files and operations that their role allows, "
          "any modification of stored content is detected when the file is retrieved, and every security-sensitive action leaves a record whose alteration can be detected."),
        H2("1.4 Need for the Proposed System"),
        P("General-purpose file-sharing tools protect data in transit and, at best, encrypt it at rest with a key that the provider holds. Under that model the provider, a malicious insider or an attacker who "
          "obtains a backup can read every file, so the protection is only as strong as the provider's own security. Research prototypes that encrypt on the client exist, but they are typically file-system "
          "clients rather than web applications, or they report headline results without the hardware, timings and methods needed to judge them (Section 2.10). "
          "A student-scale, openly inspectable system that joins client-side encryption, per-recipient key wrapping, server-enforced roles, hash-based integrity checking and a verifiable audit log, "
          "and then reports what each layer costs and where it falls short, is a useful reference for anyone deciding how far such a design can be trusted."),
        P("There is a second, practical need. A security claim is worth little unless it is tested. The system is therefore accompanied by a measurement programme (Chapter 7 and Chapter 8): "
          "the cost of every cryptographic operation in a real browser, the end-to-end cost of an encrypted transfer against a plain one, an exhaustive role-by-operation check against the live API, "
          "and tampering experiments against the stored ciphertext and the audit log."),
        H2("1.5 Project Objectives"),
        P("The six objectives set at the start of the project (6.OBJECTIVES&PROBLEM STATEMENT.docx) are:"),
        N("Implement user registration and authentication with securely hashed credentials and JWT sessions.",
          "Encrypt every uploaded file using AES-256-GCM before it reaches storage.",
          "Implement role-based access control together with file-ownership verification.",
          "Verify file integrity on download using cryptographic hashing.",
          "Maintain structured audit logs of every upload, download, delete and access denial.",
          "Evaluate encryption overhead, access-control correctness and integrity verification."),
        P("Objective 2 is met by moving the encryption to the browser, so that the data are encrypted before they leave the user's machine rather than only before they reach the storage directory; "
          "this is a stronger reading of the objective and is explained in Chapter 6. Whether each objective was achieved is assessed against the measurements in Chapter 8 (objectives versus outcomes) and summarised in Chapter 9."),
        TAB("Objectives and where each is realised and assessed", ["No.", "Objective (short form)", "Realised in", "Assessed in"],
            [["1", "Registration, bcrypt hashing, JWT sessions", "backend/app/api/auth.py, core/security.py", "Chapters 7, 8"],
             ["2", "AES-256-GCM encryption before storage", "frontend/src/lib/vaultCrypto.js, vault.js", "Chapters 7, 8"],
             ["3", "Role-based access and ownership checks", "services/permission_service.py, api/files.py, api/sharing.py", "Chapters 7, 8"],
             ["4", "Integrity check on download (AES-GCM tag and SHA-256)", "vault.js download path, files.py headers", "Chapter 8"],
             ["5", "Structured audit log of all sensitive events", "services/audit_service.py, api/audit.py", "Chapter 8"],
             ["6", "Evaluation of overhead, access control, integrity", "scripts/measure_metrics.py, scripts/smoke_test.py, tests/", "Chapters 7 and 8"]],
            widths=[0.4, 2.4, 2.3, 1.2], align=["c", "l", "l", "l"], size=9.5),
        H2("1.6 Scope of the Project"),
        P(f"The system is a single-institution web application with a FastAPI back end (port {F.API_PORT}) and a React front end (port {F.WEB_PORT}). It covers registration and sign-in; creation of an RSA-2048 key pair "
          "in the browser at registration; encrypted upload, download, replacement and deletion of files up to "
          f"{F.UPLOAD_LIMIT_MB} MB; sharing of a file with another registered user as Viewer or Editor, changing that role and revoking it; "
          "an audit log with a verification function; a dashboard, file-detail view and security page; and one-click demo accounts with synthetic data. "
          f"The back end exposes 24 endpoints over four database tables, and the whole application is about {lo['backend_py']['lines']:,} lines of Python and {lo['frontend_src']['lines']:,} lines of front-end source."),
        P("The following are outside the scope: multi-factor authentication, key escrow or recovery, chunked or streamed encryption of very large files, a hardware security module or external key-management service, "
          "anonymous or public links, organisation-wide administrators, mobile applications, and any claim of protection against a compromised user device or a malicious server that ships altered JavaScript. "
          "These boundaries are listed again, with their consequences, in the Scope and Limitations document and in Chapter 10."),
        H2("1.7 Project Contributions"),
        N("A complete, runnable secure file-storage application in which encryption, key wrapping, role checks and audit logging are implemented end to end and run on a standard laptop with no cloud account.",
          "A key design in which a random 256-bit file key is wrapped separately for each recipient and the owner's private key is stored on the server only after being encrypted under a password-derived key, "
          "so the server never holds a key that can decrypt a file.",
          "A server-side Owner / Editor / Viewer model whose behaviour was verified exhaustively on the live API: four principals against nine operations, 36 of 36 cells as expected, "
          "together with rejection of unauthenticated and forged tokens.",
          "A hash-chained audit log with a verification endpoint and an interface that shows the verdict, together with a tamper study that states what the chain detects (eight of nine tampering classes) and, equally plainly, "
          "what it does not (tail truncation, and a rewrite that recomputes every later hash).",
          "A measurement study on one machine: per-operation browser crypto timings, end-to-end encrypted and plain transfer times for files from 1 KiB to 10 MiB, API latencies up to the 25 MB limit, "
          "and a discovered defect (concurrent writers fork the audit chain) that is documented rather than hidden."),
        P(f"Against the base paper {C('base')} the contribution is the move from a calculated cost model for attribute-based encryption to a measured, general-purpose file store; "
          f"against the closest architecture paper {C('ijedr')} it is the publication of hardware, per-operation timings, the tampering methods and their failures, which that paper does not give."),
        H2("1.8 Limitations and Assumptions"),
        P("The principal limitations are stated here so that no later chapter has to retract them. The audit chain is an unsigned hash chain: it cannot detect removal of the newest entries "
          f"(0 of {F.TAMPER['audit_tamper']['truncate_tail']['trials']} truncation trials were detected) or a rewrite by someone who recomputes every later hash, and the audit writer is not safe under concurrent writers "
          "(a burst of 100 concurrent failed logins left the chain invalid). Revoking a reader removes the wrapped key stored on the server but cannot recall a key or ciphertext that the reader has already downloaded, "
          "and the file key is not rotated on revoke. The server delivers the JavaScript that performs the encryption, so a compromised server could deliver malicious code; "
          "file names, sizes, types, owners and timestamps are stored in the clear; a forgotten password means unrecoverable data; there is no multi-factor sign-in; "
          "the session token is kept in sessionStorage; and files are encrypted whole in memory, which is why the upload size is capped."),
        P("The assumptions are that the user's browser and device are not compromised, that the server operator is honest-but-curious rather than actively malicious at the moment code is served, that the Web Cryptography "
          "implementation of the browser is correct, that users choose passwords of at least eight characters, and that the deployment is a single instance behind a trusted network or TLS terminator. "
          f"All measurements were made on one desktop computer ({F.ENV['cpu']}, {F.ENV['ram_gb']} GB, Windows, Chrome) that was also used by other jobs at the time, so timings are indicative and the run-to-run spread reached about three times at 10 MB."),
        H2("1.9 Organization of the Report"),
        P("Chapter 2 surveys the literature, analyses the base paper and states the research gap. Chapter 3 assesses the technical, economic, operational and schedule feasibility of the project. "
          "Chapter 4 describes the existing and proposed systems and lists the functional and non-functional requirements, the hardware and software, and the user roles. "
          "Chapter 5 presents the design: architecture, workflow, data-flow diagrams, UML diagrams, database design, modules and user interface. "
          "Chapter 6 gives the methodology and implementation: the cryptographic pipeline, its mathematical formulation, the application and API, security handling, and how to install and run the system. "
          "Chapter 7 reports testing at unit, integration, functional, security, edge-case and performance level, and the limits of that testing. "
          "Chapter 8 presents the results and every output screen, compares the work with the base paper and the closest related paper, and measures the objectives against the outcomes. "
          "Chapter 9 concludes and Chapter 10 describes future scope. The references follow, and three appendices give the important code, the installation and user guide, and additional screens."),
    ]
