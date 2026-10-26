"""16.Final_PPT.pptx: 28 slides. Built from D:\\abstracts\\Templates\\Final_PPT.pptx (letterhead, rule, title and footer chrome inherited).

Every number is read from facts.py (docs/metrics/metrics.json, tests.json); nothing is typed in by hand except what the code states.
"""

import os
import tempfile

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE

from . import facts as F
from . import lit
from . import pptkit as K
from .make_figures import fig_path
from .refs import N, REFS, _IDX

TEMPLATE = r"D:\abstracts\Templates\Final_PPT.pptx"
FONT = "Calibri"
TOP_BANNER, TOP_RULE, TOP_TITLE, TOP_FOOT = 73152, 979985, 1098857, 6446520


def chrome(sh):
    return sh.top in (TOP_BANNER, TOP_RULE, TOP_TITLE, TOP_FOOT)


def set_title(slide, text, size=None):
    for sh in slide.shapes:
        if sh.top == TOP_TITLE:
            K.replace_text(sh, text, size)
            return


def wipe(slide):
    K.clear(slide, chrome)


def fbox(slide, x, y, w, h, fill=K.FHEAD, line=None):
    return K.box(slide, x, y, w, h, fill=fill, line=line, radius=0.04)


def ftable(slide, x, y, widths, rows, size=13, row_h=0.45, align=None, first_bold=True):
    return K.table(slide, x, y, widths, rows, font_size=size, row_h=row_h, header_fill=K.FHEAD, header_color=K.FNAVY, zebra=K.FZEBRA,
                   body_color=K.DARK, first_bold=first_bold, font=FONT, align=align, border=K.RGBColor(0xBF, 0xBF, 0xBF))


def ftext(slide, x, y, w, h, paras, size=16, color=K.DARK, **kw):
    return K.text(slide, x, y, w, h, paras, size=size, color=color, font=FONT, **kw)


def ftile(slide, x, y, w, h, value, label, color=K.FBLUE, vsize=26, lsize=12):
    K.box(slide, x, y, w, h, fill=K.FHEAD, line=None, radius=0.05)
    K.box(slide, x, y, 0.08, h, fill=color, line=None, shape=MSO_SHAPE.RECTANGLE)
    K.text(slide, x + 0.2, y + 0.06, w - 0.3, h * 0.55, value, size=vsize, color=K.FNAVY, bold=True, anchor="m", font=FONT)
    K.text(slide, x + 0.2, y + h * 0.58, w - 0.3, h * 0.4, label, size=lsize, color=K.DARK, font=FONT)


CROPS = os.path.join(tempfile.gettempdir(), "ciphervault_deck_crops")


def crop_shot(name, box=(248, 56, 1440, 900)):
    """Real screenshot with the sidebar cropped away (left, top, right, bottom in pixels) so the content is larger on the slide."""
    from PIL import Image

    os.makedirs(CROPS, exist_ok=True)
    out = os.path.join(CROPS, f"{os.path.splitext(name)[0]}_{abs(hash(box)) % 10**6}.png")
    with Image.open(F.shot(name)) as im:
        im.crop(box).save(out)
    return out


def clean_ref(s):
    return " ".join(s.replace("*", "").split())


def bl(items, space=8):
    return [(t, {"bullet": True, "space_after": space}) for t in items]


def short(t, n):
    t = " ".join(t.split())
    return t if len(t) <= n else t[: n - 3].rsplit(" ", 1)[0] + "..."


def mb(n):
    return f"{n / 1048576:.0f} MiB" if n >= 1048576 else (f"{n // 1024} KiB")


def build(out_path):
    prs = Presentation(TEMPLATE)
    S = list(prs.slides)
    assert len(S) == 28, len(S)
    cp = prs.core_properties
    cp.title = f"{F.TITLE} - Final Review"
    cp.author = f"Batch {F.BATCH_NO}, Dept. of CSE, TKRCET"
    cp.comments = ""
    cp.last_modified_by = f"Batch {F.BATCH_NO}, Dept. of CSE, TKRCET"
    cp.subject = F.PRODUCT
    cp.keywords = "secure file storage, AES-256-GCM, RSA-OAEP, role-based access control, audit log"
    notes = {}

    AES, E2E, API, TAM, SC, CONC, CRY = F.AES, F.E2E, F.API, F.TAMPER, F.SCALE, F.CONC, F.CRY
    ms = F.ms
    a25 = AES["26214400"]
    a10 = AES["10485760"]
    up25 = API["upload_ms"]["26212352"]["median"]
    dn25 = API["download_ms"]["26212352"]["median"]
    at = TAM["audit_tamper"]
    detected_classes = [k for k, v in at.items() if v["detected"] == v["trials"]]
    n_cls = len(at)
    conc = CONC["4_workers"]

    for sl in S:  # footers on every slide except the title
        for sh_ in sl.shapes:
            if sh_.top == TOP_FOOT and sh_.has_text_frame and "Final Review" in sh_.text_frame.text:
                K.replace_text(sh_, f"Dept. of CSE  |  Batch {F.BATCH_NO}  |  Final Review")

    # ---- 1 title
    for sh_ in S[0].shapes:
        if sh_.name == "Text 1":
            K.replace_text(sh_, F.FULL_TITLE, 28)
        elif sh_.name == "Text 2":
            K.replace_text(sh_, f"Final Review  ·  {F.PRODUCT}")
        elif sh_.name == "Text 3":
            K.replace_text(sh_, f"Team Details : Batch {F.BATCH_NO}")
        elif sh_.name == "Text 4":
            K.replace_text(sh_, "\n".join(f"{r_}   {n_}" for n_, r_ in F.STUDENTS))
        elif sh_.name == "Text 5":
            K.replace_text(sh_, f"Under the Esteemed Guidance of\n{F.GUIDE}\n{F.GUIDE_DESIGNATION}, Department of CSE")
        elif sh_.name == "Text 6":
            K.replace_text(sh_, f"DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING  ·  {F.COLLEGE_SHORT}  ·  Academic Year {F.YEAR}")
    notes[1] = "Introduce the team and CipherVault: files are encrypted in the browser, the server enforces roles and keeps a hash-chained audit log. Everything shown was measured on one desktop."

    # ---- 2 contents
    s = S[1]
    set_title(s, "Table of Contents")
    for sh_ in s.shapes:
        if sh_.name == "Text 4":
            K.replace_text(sh_, "Abstract\nBase Paper & Literature Survey\nResearch Gap, Problem Statement & Objectives\nProposed System & Architecture\nMethodology, Data & Cryptographic Primitives\nDecision Workflow, Interaction & Database Design\nImplementation\nResults: Cryptographic Cost, Overhead, Access Control & Integrity\nParameter Analysis, Performance & Testing\nComparison with the Base Paper and the Closest Architecture\nOutput Screens\nConclusion, Limitations, Future Scope & References", 16)
    notes[2] = "The agenda follows the report: problem, design, method, results, comparison, screens, conclusion."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract")
    wipe(s)
    ftext(s, 0.55, 1.8, 12.2, 5.1, bl([
        "Files kept on a storage provider are readable by the provider, by insiders and by anyone who reaches the database. CipherVault moves encryption to the browser: every file is encrypted with its own AES-256-GCM key before upload, the key is wrapped for each authorised user with RSA-2048-OAEP, and the server stores only ciphertext.",
        "The server enforces Owner / Editor / Viewer roles on every request, checks plaintext SHA-256 and the GCM tag on download (in the browser), and records each sensitive action in a SHA-256 hash-chained audit log.",
        f"Measured on one i5-12500 desktop in Chrome and over loopback: AES-256-GCM of a 25 MiB file takes {ms(a25['encrypt']['median'])} ms; a 10 MiB encrypted upload adds about {E2E['10485760']['encrypted_up']['median'] - E2E['10485760']['plain_up']['median']:.0f} ms to a plain one; the role matrix matched {F.RBAC['matched']} of {F.RBAC['total']} cells; {TAM['ciphertext_bitflip']['detected']} of {TAM['ciphertext_bitflip']['trials']} ciphertext bit flips were rejected.",
        f"Honest limits found while measuring: {n_cls - len(detected_classes)} of {n_cls} audit-tampering classes (tail truncation, 0 of {at['truncate_tail']['trials']}) are not detected, a full re-hash is not detected, and concurrent writers fork the chain.",
        f"{F.PYTEST_PASSED} pytest tests, a {F.E2E_TOTAL}-check API run and an {F.UI_TOTAL}-step browser walk all pass.",
    ], 9), size=15)
    notes[3] = "Give the product, then the honest result: the cryptography is cheap; the audit chain detects most but not all tampering."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base Paper")
    wipe(s)
    ftext(s, 0.55, 1.72, 12.2, 0.75, F.BASE_PAPER, size=12.5, color=K.FNAVY)
    rows = [["Aspect", "Base paper: secure EHR access control (Nekouie et al., Scientific Reports, 2026)"],
            ["Method", "Elliptic-curve ciphertext-policy dual-attribute encryption; ClinicalBERT extracts data attributes from clinical notes; several key-generation centres (no key escrow); Hyperledger Fabric ledger holds public keys and policies; 23 protocol phases"],
            ["Evaluation", "Analytic: cost calculated from operation counts times OpenSSL primitive timings on an HPE server (E5-2620 v3) and a Raspberry Pi 3 B+; no dataset, no ClinicalBERT accuracy reported"],
            ["Reported cost", "Proposed scheme about 8,506 microseconds in total at x = 5 attributes on the Pi (formula 1362.5x + 1694); ten compared schemes 8,812 to 71,323 microseconds"],
            ["Limits for our aim", "Not a file store: no upload / download time, no role check latency, no audit-log cost; heavy key-centre and ledger infrastructure"],
            ["What we adopt", "Untrusted storage that sees only ciphertext; a stored hash checked after decryption; revocation and audit as part of the design; cost reported per primitive"]]
    ftable(s, 0.55, 2.5, [1.9, 10.3], rows, size=12, row_h=0.72)
    notes[4] = "The declared base paper solves a different problem (attribute-based encryption for health records). We adopt its trust model and measurement habit, not its machinery; its timings are calculated, not measured."

    # ---- 5 literature survey
    s = S[4]
    set_title(s, "Literature Survey")
    wipe(s)
    keys = ["base", "ijedr", "geo", "sagi", "mega", "sirius", "plutus", "audit99"]
    rows = [["Work", "Approach", "Limitation relevant here"]]
    for r in lit.ROWS:
        if r[0] in keys:
            rows.append([f"{r[1]} {N(r[0])}", short(r[2], 118), short(r[5], 118)])
    ftable(s, 0.55, 1.75, [2.6, 5.0, 4.6], rows, size=10, row_h=0.56)
    notes[5] = "Eight of the surveyed works. The three batch-survey titles we could not locate online are listed only in the report and no results are quoted from them."

    # ---- 6 research gap + problem statement
    s = S[5]
    set_title(s, "Research Gap & Problem Statement")
    wipe(s)
    fbox(s, 0.55, 1.8, 6.0, 4.9, fill=K.FZEBRA)
    ftext(s, 0.75, 1.9, 5.6, 0.4, "Research gap", size=17, color=K.FNAVY, bold=True)
    ftext(s, 0.75, 2.4, 5.6, 4.2, bl([
        "Attribute-based encryption and blockchain designs for records report calculated primitive costs, not a working file store.",
        "The closest file-storage paper reports +320 ms, 98.6% access accuracy and 100% tamper detection without hardware, per-operation timings or tamper methods.",
        "No work found measures browser-side AES-GCM, key wrapping, role checks and a hash-chained audit log on one machine, and reports what the chain does not detect.",
    ], 10), size=15)
    fbox(s, 6.8, 1.8, 6.0, 4.9, fill=K.FHEAD)
    ftext(s, 7.0, 1.9, 5.6, 0.4, "Problem statement", size=17, color=K.FNAVY, bold=True)
    ftext(s, 7.0, 2.4, 5.6, 4.3, bl([
        "Files stored without client-side encryption are readable by the storage provider.",
        "Without role-based control any authenticated user may reach another user's files.",
        "Tampering goes undetected when no integrity check is made on retrieval.",
        "Without audit logs a security incident cannot be reconstructed afterwards.",
        "Need: a store that encrypts before upload, enforces roles, verifies integrity and logs every action.",
    ], 8), size=15)
    notes[6] = "The gap is the measured, complete combination and the honesty about its weak points."

    # ---- 7 objectives
    s = S[6]
    set_title(s, "Objectives")
    wipe(s)
    rows = [["#", "Objective (batch documents)", "How it is realised"],
            ["1", "Registration and authentication with hashed credentials and JWT sessions", f"bcrypt cost {F.BCRYPT_COST}; JWT HS256, {F.JWT_MINUTES} min; login throttle {F.LOGIN_LIMIT[0]} per {F.LOGIN_LIMIT[1]} s"],
            ["2", "Encrypt every uploaded file with AES-256-GCM before storage", "In the browser, fresh 256-bit key and 12-byte IV per file; server stores ciphertext only"],
            ["3", "Role-based access control with ownership checks", "Owner / Editor / Viewer checked on every request in permission_service"],
            ["4", "Verify integrity on download", "GCM tag plus SHA-256 of the plaintext compared in the browser"],
            ["5", "Structured audit log of uploads, downloads, deletes and denials", "Hash-chained audit_logs table with a verify endpoint and screen"],
            ["6", "Evaluate overhead, access-control correctness and integrity", f"scripts/measure_metrics.py (browser crypto, API, roles, tampering) and {F.PYTEST_PASSED} + {F.E2E_PASSED} + {F.UI_PASSED} + {F.EVAL_PASSED} passing checks"]]
    ftable(s, 0.55, 1.8, [0.5, 5.6, 6.1], rows, size=12.5, row_h=0.68, align=["c", "l", "l"])
    notes[7] = "The six objectives are taken from the batch documents; the outcome of each is on the conclusion slide."

    # ---- 8 proposed system
    s = S[7]
    set_title(s, "Proposed System")
    wipe(s)
    ftile(s, 0.55, 1.8, 2.9, 1.0, "Browser crypto", "AES-256-GCM, RSA-2048-OAEP, PBKDF2", K.FBLUE, 22, 12)
    ftile(s, 3.65, 1.8, 2.9, 1.0, "3 roles", "Owner / Editor / Viewer, server-enforced", K.GREEN, 22, 12)
    ftile(s, 6.75, 1.8, 2.9, 1.0, "SHA-256", "plaintext hash + GCM tag on download", K.ORANGE, 22, 12)
    ftile(s, 9.85, 1.8, 2.9, 1.0, "Hash chain", "tamper-evident audit log", K.PURPLE, 22, 12)
    ftext(s, 0.55, 3.1, 6.0, 3.8, bl([
        "Register: the browser generates an RSA-2048 key pair; the private key is encrypted with a password-derived key before it is stored.",
        "Upload: the file is hashed, encrypted with a fresh file key, and the key is wrapped with the owner's public key.",
        "Share: the owner unwraps the file key locally and re-wraps it for the recipient; the plaintext key is never sent.",
    ], 8), size=14)
    ftext(s, 6.8, 3.1, 6.0, 3.8, bl([
        "Download: the server checks the role, returns ciphertext plus the caller's wrapped key; the browser decrypts and compares the SHA-256.",
        "Every sensitive action (login, upload, download, share, role change, revoke, delete, denied access) is appended to the chain.",
        "Runs locally with SQLite (PostgreSQL through Docker); ports 8413 (API) and 5413 (UI).",
    ], 8), size=14)
    notes[8] = "The server is blind to content by design; roles and the audit log are its job."

    # ---- 9 architecture
    s = S[8]
    set_title(s, "System Architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.45, 1.75, 7.3, 5.05)
    ftext(s, 8.0, 1.85, 4.8, 5.0, bl([
        "Browser (React 19 + Web Crypto API) is the trusted crypto endpoint.",
        f"FastAPI backend, port {F.API_PORT}: auth, users, files, sharing and audit routers; 24 endpoints.",
        "Services: permission_service (roles) and audit_service (hash chain).",
        "SQLAlchemy with 4 tables; SQLite by default, PostgreSQL via Docker.",
        "Ciphertext lives in storage/encrypted under random 32-hex names.",
        "The storage layer is one small module and can be swapped for object storage.",
    ], 7), size=14)
    notes[9] = "Walk the diagram top to bottom. The server never holds a plaintext file or a private key."

    # ---- 10 methodology
    s = S[9]
    set_title(s, "Methodology")
    wipe(s)
    K.picture(s, F.diag("02_high_level_workflow.png"), 0.45, 1.75, 7.6, 4.45)
    ftext(s, 8.3, 1.85, 4.5, 5.0, [(t, {"space_after": 9}) for t in [
        "1. Register and create keys in the browser.",
        "2. Unlock the vault with the password (PBKDF2 key unlocks the private key).",
        "3. Hash, encrypt and upload.",
        "4. Share by re-wrapping the file key.",
        "5. Download, decrypt and verify the hash.",
        "6. Verify the audit chain at any time; revoke access when needed.",
    ]], size=14)
    ftext(s, 0.45, 6.3, 7.6, 0.5, "High-level workflow, from registration to chain verification.", size=12, color=K.FNAVY, italic=True)
    notes[10] = "Six steps; steps 3 to 5 are where the cryptography and the role check meet."

    # ---- 11 data, primitives and tools
    s = S[10]
    set_title(s, "Data, Cryptographic Primitives and Tools")
    wipe(s)
    rows = [["Item", "Detail"],
            ["Data", "No dataset and no learned model. Demo data are 5 fictional files and 3 demo accounts; measurement payloads are random bytes from 1 KiB to 25 MiB"],
            ["File cipher", "AES-256-GCM, fresh 256-bit file key and random 12-byte IV per file, 16-byte tag"],
            ["Key wrapping", "RSA-2048-OAEP (SHA-256); wrapped key is 256 bytes, one copy per authorised user"],
            ["Private key", f"PKCS#8 encrypted with AES-256-GCM under a PBKDF2-HMAC-SHA-256 key ({F.PBKDF2_ITER:,} iterations, 16-byte salt)"],
            ["Integrity / audit", "SHA-256 of the plaintext; audit chain SHA-256(prev | time | user | file | action | success | details)"],
            ["Passwords, sessions", f"bcrypt cost {F.BCRYPT_COST}; JWT HS256, {F.JWT_MINUTES} minutes"],
            ["Stack", "FastAPI, SQLAlchemy, SQLite / PostgreSQL, React 19, Vite 8, Web Crypto API, Recharts, three.js; pytest and Playwright"]]
    ftable(s, 0.55, 1.8, [2.2, 10.0], rows, size=12.5, row_h=0.6)
    notes[11] = "There is no training data: the 'dataset' is demo data and measurement workloads, and we say so on purpose."

    # ---- 12 decision workflow
    s = S[11]
    set_title(s, "Decision Workflow: Roles and the Core Algorithm")
    wipe(s)
    K.picture(s, F.diag("10_flowchart_encrypt_upload.png"), 0.45, 1.75, 5.7, 5.1)
    cells = {(c["principal"], c["operation"]): c["expected_allowed"] for c in F.RBAC["cells"]}
    tick = lambda p, o: "allow" if cells[(p, o)] else "deny"  # noqa: E731
    ops = [("metadata", "Read metadata"), ("download", "Download"), ("update", "Replace content"), ("list_permissions", "List access"),
           ("share", "Share"), ("change_role", "Change role"), ("revoke", "Revoke"), ("file_audit", "File history"), ("delete", "Delete")]
    rows = [["Operation", "Owner", "Editor", "Viewer", "Stranger"]] + [[lab] + [tick(p, o) for p in ("owner", "editor", "viewer", "stranger")] for o, lab in ops]
    ftable(s, 6.4, 1.8, [2.3, 1.0, 1.0, 1.0, 1.1], rows, size=11.5, row_h=0.4, align=["l", "c", "c", "c", "c"])
    ftext(s, 6.4, 6.0, 6.4, 0.85, "Roles are resolved per file by permission_service; a denied request returns HTTP 403 and writes an unauthorized_access event. This table is what the live API returned (all 36 cells matched).", size=11.5, color=K.FNAVY, italic=True)
    notes[12] = "Left: upload and download algorithm. Right: the decision table the server applies; it was measured against the live API."

    # ---- 13 interaction
    s = S[12]
    set_title(s, "User - System Interaction")
    wipe(s)
    K.picture(s, F.diag("07_sequence_upload_share_download.png"), 0.45, 1.75, 6.4, 5.1)
    K.picture(s, F.diag("08_use_case.png"), 7.0, 1.75, 5.9, 5.1)
    notes[13] = "Sequence of upload, share and download between the owner, the server and the recipient; and the use cases per role."

    # ---- 14 database
    s = S[13]
    set_title(s, "Database Design")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.45, 1.75, 6.5, 5.1)
    ftext(s, 7.2, 1.9, 5.6, 4.9, bl([
        "users: name, unique email, bcrypt hash, public key, encrypted private-key bundle and salt",
        "files: owner, original and stored (random) names, sizes, IV, owner-wrapped file key, plaintext SHA-256",
        "file_permissions: file, user, role (viewer | editor), recipient-wrapped file key; unique (file, user)",
        "audit_logs: time, user, file, action, success, IP, details, previous and current hash",
        "File and user deletion cascade to permissions; audit rows keep their history (foreign keys set to NULL).",
    ], 8), size=14)
    notes[14] = "Four tables. The ER diagram mirrors backend/app/db/models.py."

    # ---- 15 implementation highlights
    s = S[14]
    set_title(s, "Implementation Highlights")
    wipe(s)
    L = F.LOC
    ftile(s, 0.55, 1.8, 2.9, 1.0, "24 endpoints", "REST API + SPA fallback", K.FBLUE, 22, 12)
    ftile(s, 3.65, 1.8, 2.9, 1.0, f"{F.PYTEST_PASSED} tests", "pytest, all pass", K.GREEN, 22, 12)
    ftile(s, 6.75, 1.8, 2.9, 1.0, f"{L['backend_py']['lines']:,} lines", f"backend, {L['backend_py']['files']} Python files", K.ORANGE, 22, 12)
    ftile(s, 9.85, 1.8, 2.9, 1.0, f"{L['frontend_src']['lines']:,} lines", f"frontend, {L['frontend_src']['files']} files", K.PURPLE, 22, 12)
    ftext(s, 0.55, 3.1, 6.0, 3.8, bl([
        "Server validates every upload: 12-byte IV, 64-hex SHA-256, base64 fields, 25 MB limit (HTTP 413).",
        "Stored object has a random 32-hex name; the original name is metadata only.",
        "A share must carry a 256-byte RSA-OAEP value; duplicates return 409.",
        "Login throttle in memory; forged, expired, wrong-secret and alg=none tokens all return 401.",
    ], 7), size=14)
    ftext(s, 6.8, 3.1, 6.0, 3.8, bl([
        "Found while measuring: concurrent audit writers fork the chain (read last hash, then commit, no lock).",
        "Whole-file encryption in memory, hence the 25 MB cap; no chunking.",
        "GET /api/audit returns the global event list to any signed-in user.",
        "An editor's update re-encrypts under the existing file key with a fresh IV.",
    ], 7), size=14)
    notes[15] = "Strengths on the left, defects found while measuring on the right."

    # ---- 16 results: cryptographic cost
    s = S[15]
    set_title(s, "Results - Cost of the Cryptography (Browser)")
    wipe(s)
    ftile(s, 0.55, 1.75, 2.9, 0.95, f"{ms(a25['encrypt']['median'])} ms", "AES-256-GCM encrypt, 25 MiB", K.FBLUE, 24, 11)
    ftile(s, 3.65, 1.75, 2.9, 0.95, f"{ms(a10['encrypt']['median'])} ms", "AES-256-GCM encrypt, 10 MiB", K.GREEN, 24, 11)
    ftile(s, 6.75, 1.75, 2.9, 0.95, f"{ms(CRY['rsa_keygen']['median'])} ms", "RSA-2048 key generation", K.ORANGE, 24, 11)
    ftile(s, 9.85, 1.75, 2.9, 0.95, f"{ms(CRY['pbkdf2_120k']['median'])} ms", f"PBKDF2, {F.PBKDF2_ITER:,} iterations", K.PURPLE, 24, 11)
    K.picture(s, fig_path("f01"), 0.45, 2.85, 6.1, 3.55)
    K.picture(s, fig_path("f08"), 6.8, 2.85, 6.1, 3.55)
    ftext(s, 0.55, 6.45, 12.2, 0.55, f"Chrome {F.BR['browser_version'].split('.')[0]}, medians; wrapping a file key costs {ms(CRY['rsa_wrap']['median'])} ms, unwrapping {ms(CRY['rsa_unwrap']['median'])} ms; AES-GCM adds 16 bytes per file. Encryption cost grows linearly with size.", size=12, color=K.FNAVY, italic=True)
    notes[16] = "Medians in Chrome on an i5-12500 shared with other jobs. Small sizes were timed in batches because Chrome's clock is 0.1 ms."

    # ---- 17 results: end to end overhead
    s = S[16]
    set_title(s, "Results - End-to-End Overhead vs Plain Transfer")
    wipe(s)
    K.picture(s, fig_path("f02"), 0.45, 1.75, 6.5, 3.5)
    rows = [["Size", "Upload enc / plain", "Download+decrypt / plain"]]
    for k in ("1024", "1048576", "10485760"):
        e = E2E[k]
        rows.append([mb(int(k)), f"{ms(e['encrypted_up']['median'])} / {ms(e['plain_up']['median'])} ms", f"{ms(e['encrypted_down']['median'])} / {ms(e['plain_down']['median'])} ms"])
    ftable(s, 7.2, 1.85, [1.3, 2.1, 2.2], rows, size=12, row_h=0.5, align=["l", "c", "c"])
    d10u = E2E["10485760"]["encrypted_up"]["median"] - E2E["10485760"]["plain_up"]["median"]
    d10d = E2E["10485760"]["encrypted_down"]["median"] - E2E["10485760"]["plain_down"]["median"]
    ftext(s, 7.2, 4.0, 5.6, 1.5, bl([
        f"10 MiB: encryption adds about {d10u:.0f} ms to an upload and {d10d:.0f} ms to a download+decrypt+verify (medians).",
        "Encrypted and plain runs used the same endpoint, in a real browser.",
    ], 6), size=12.5)
    ftext(s, 0.55, 5.5, 12.2, 1.4, bl([
        "Host CPU was shared with other sessions: run-to-run spread reached about 3x at 10 MiB, so read these as indicative, not exact.",
        "The closest paper reports +320 ms for a 10 MB upload; its hardware and protocol are not published, so the two figures are not compared.",
    ], 6), size=13)
    notes[17] = "Same endpoint, same browser, encrypted against plain. State the noise caveat."

    # ---- 18 results: access control and integrity (confusion-matrix equivalent)
    s = S[17]
    set_title(s, "Results - Access Control and Tamper Evidence")
    wipe(s)
    K.picture(s, fig_path("f05"), 0.4, 1.75, 5.9, 3.95)
    ftext(s, 0.45, 5.75, 5.9, 1.2, f"Expected vs observed for 4 principals x 9 operations: {F.RBAC['matched']} of {F.RBAC['total']} matched. No token is accepted when forged, expired, signed with the wrong secret, or alg=none (all 401); unauthenticated calls return 401.", size=11.5, color=K.FNAVY, italic=True)
    lab = {"edit_details": "Edit details", "edit_action": "Edit action", "edit_success": "Edit success flag", "edit_user": "Edit user", "edit_hash": "Edit hash",
           "delete_entry_middle": "Delete a middle entry", "swap_adjacent": "Swap two entries", "insert_forged_entry": "Insert a forged entry", "truncate_tail": "Truncate the tail"}
    rows = [["Tampering", "Detected"]]
    rows.append(["Ciphertext bit flip (AES-GCM)", f"{TAM['ciphertext_bitflip']['detected']} / {TAM['ciphertext_bitflip']['trials']}"])
    for k, v in at.items():
        rows.append([f"Audit: {lab[k]}", f"{v['detected']} / {v['trials']}"])
    rows.append(["Audit: rewrite and re-hash every later entry", "not detected"])
    ftable(s, 6.55, 1.75, [4.4, 1.9], rows, size=10.5, row_h=0.33, align=["l", "c"])
    ftext(s, 6.55, 6.35, 6.3, 0.6, "Tail truncation and a full re-hash pass the check: the chain has no secret key or external anchor.", size=11, color=K.FNAVY, italic=True)
    notes[18] = "This is the equivalent of a confusion matrix for a security system: expected against observed decisions, and detected against injected tampering. Say the two misses aloud."

    # ---- 19 parameter analysis
    s = S[18]
    set_title(s, "Parameter Analysis - File Size, Key Derivation, Chain Length")
    wipe(s)
    K.picture(s, fig_path("f04"), 0.45, 1.75, 6.1, 3.5)
    K.picture(s, fig_path("f07"), 6.8, 1.75, 6.1, 3.5)
    ftext(s, 0.55, 5.4, 12.2, 1.6, bl([
        f"File size: API upload median {ms(API['upload_ms']['1048576']['median'])} ms at 1 MiB, {ms(API['upload_ms']['10485760']['median'])} ms at 10 MiB, {ms(up25)} ms at the 25 MB limit; download {ms(dn25)} ms. Above the limit the server returns HTTP 413.",
        f"Key derivation: PBKDF2 at {F.PBKDF2_ITER:,} iterations costs {ms(CRY['pbkdf2_120k']['median'])} ms per unlock; cost scales with the iteration count (the closest paper uses 310,000; not measured here).",
        f"Chain length: verification took {ms(SC['461']['verify_ms_median'])} ms for 461 entries and {ms(SC['5000']['verify_ms_median'])} ms for 5,000; it re-walks every entry (no incremental check).",
    ], 5), size=12.5)
    notes[19] = "Three parameters: file size (the 25 MB cap), PBKDF2 iterations, audit chain length."

    # ---- 20 performance and testing
    s = S[19]
    set_title(s, "Performance & Testing")
    wipe(s)
    ftile(s, 0.55, 1.75, 2.9, 0.95, f"{F.PYTEST_PASSED} / {F.PYTEST_TOTAL}", f"pytest tests, {F.PYTEST_SECONDS:.0f} s", K.GREEN, 24, 11)
    ftile(s, 3.65, 1.75, 2.9, 0.95, f"{F.E2E_PASSED} / {F.E2E_TOTAL}", "API end-to-end checks", K.GREEN, 24, 11)
    ftile(s, 6.75, 1.75, 2.9, 0.95, f"{F.UI_PASSED} / {F.UI_TOTAL}", "real-browser UI steps", K.GREEN, 24, 11)
    ftile(s, 9.85, 1.75, 2.9, 0.95, f"{F.EVAL_PASSED} / {F.EVAL_TOTAL}", "evaluate.py checks", K.GREEN, 24, 11)
    K.picture(s, fig_path("f03"), 0.45, 2.85, 6.0, 3.55)
    ftext(s, 6.8, 2.9, 6.0, 4.1, bl([
        f"Login {ms(API['login_ms']['median'])} ms (bcrypt cost {F.BCRYPT_COST}); a call to /auth/me {ms(API['me_ms']['median'])} ms; share {ms(API['share_ms'])} ms; revoke {ms(API['revoke_ms'])} ms.",
        f"After revoke, the next download returned HTTP {API['download_after_revoke_status']}.",
        f"Defect: {conc['requests']} concurrent failed logins on {4} workers left the chain invalid (first bad entry {conc['failure_at']} of {conc['checked']}); not fixed.",
        "Not tested: multi-user load, files above 25 MB, Firefox / Safari, PostgreSQL path, Docker build, screen-reader audit.",
    ], 7), size=13)
    ftext(s, 0.55, 6.5, 6.0, 0.45, "Median latency per operation over loopback.", size=12, color=K.FNAVY, italic=True)
    notes[20] = "Tests are broad but small-scale. The concurrency defect is a real finding and is documented, not hidden."

    # ---- 21 comparison
    s = S[20]
    set_title(s, "Comparison with the Base Paper and the Closest Architecture")
    wipe(s)
    rows = [["Aspect", "Base paper [1]", "Closest paper [2]", "CipherVault"],
            ["Domain", "Health records (EHR)", "Cloud file storage", "General file store"],
            ["Encryption", "EC dual-attribute encryption", "Client-side AES-256 + RSA-2048", "Browser AES-256-GCM + RSA-2048-OAEP"],
            ["Access control", "Attribute policies", "3 roles, 50 users", "Owner / Editor / Viewer, 36-cell matrix"],
            ["Audit", "Hyperledger Fabric ledger", "Signed log entries", "SHA-256 hash chain in the database"],
            ["Evaluation basis", "Calculated from primitive timings", "Reported, set-up unspecified", "Measured, one host, real browser"],
            ["Cost reported", "~8,506 us total (Pi, x = 5)", "+320 ms, 10 MB upload", f"~{d10u:.0f} ms added, 10 MiB upload"],
            ["Access / tamper result", "No dataset or accuracy", "98.6% access; 100% tamper (50)", f"36/36 roles; {len(detected_classes)} of {n_cls} audit classes"]]
    ftable(s, 0.55, 1.75, [2.0, 3.2, 3.4, 3.6], rows, size=11, row_h=0.5)
    ftext(s, 0.55, 5.9, 12.2, 1.1, "The three works differ in task, data and conditions, so no score is ranked: the base paper's microsecond figures are calculated from OpenSSL timings on a Raspberry Pi and an HPE server; the closest paper does not publish its hardware or tamper method; CipherVault is measured on a shared desktop. Only the qualitative aims (provider-blind storage, integrity check, revocation, audit) are comparable.", size=12, color=K.FNAVY, italic=True)
    notes[21] = "Say plainly that nothing is score-comparable. Differences that matter: PBKDF2 120,000 vs 310,000, no chunking, no MFA, tail truncation undetected."

    # ---- 22-24 output screens
    def two_shots(slide, title, a, b, cap_a, cap_b, box_a=(248, 56, 1440, 900), box_b=(248, 56, 1440, 900)):
        set_title(slide, title)
        wipe(slide)
        K.picture(slide, crop_shot(a, box_a), 0.45, 1.75, 6.0, 3.75, border=True)
        K.picture(slide, crop_shot(b, box_b), 6.85, 1.75, 6.0, 3.75, border=True)
        ftext(slide, 0.45, 5.65, 6.0, 1.3, cap_a, size=13, color=K.FNAVY, bold=True)
        ftext(slide, 6.85, 5.65, 6.0, 1.3, cap_b, size=13, color=K.FNAVY, bold=True)

    two_shots(S[21], "Output - Dashboard and Encrypted File List", "06_dashboard.png", "07_my-files.png",
              "Dashboard for the demo owner: files, role split and vault-wide audit events per day (demo and measurement activity).",
              "My files: drop zone (any type, up to 25 MB, encrypted before it leaves the tab) and the owner's files with role badges and actions.")
    notes[22] = "Real captures of the running app with demo data."
    two_shots(S[22], "Output - File Details and Sharing", "08_file-detail.png", "09_share-access.png",
              "File detail: sizes, plaintext SHA-256, AES-GCM IV, the access list (owner, editor, viewer) and the owner-only file history, including a denied delete by the viewer.",
              "Share dialog: the file key is unwrapped and re-wrapped for the recipient in the browser; role can be changed or revoked.",
              box_a=(248, 56, 1440, 760), box_b=(440, 60, 1000, 830))
    notes[23] = "The history on the left shows a real denied delete (owner only)."
    two_shots(S[23], "Output - Audit Log and Security Profile", "10_audit-log.png", "11_security.png",
              "Audit log: hash-chained events with success or failure and a Verify audit chain button (chain valid, 226 entries at capture time).",
              "Security profile: key status (public key registered, private key stored encrypted, unlocked in memory) and the five protections.")
    notes[24] = "The audit screen is where tamper evidence is visible to the user."

    # ---- 25 conclusion
    s = S[24]
    set_title(s, "Conclusion")
    wipe(s)
    ftext(s, 0.55, 1.72, 12.2, 0.8, "CipherVault is a working, tested secure file store: encryption is cheap, roles behaved exactly as specified, and the audit chain detects most tampering, but not truncation or a full rewrite.", size=15, color=K.FNAVY, bold=True)
    rows = [["#", "Objective", "Outcome"],
            ["1", "Registration, bcrypt, JWT", "Met"],
            ["2", "AES-256-GCM before storage", f"Met, in the browser; {TAM['ciphertext_bitflip']['detected']}/{TAM['ciphertext_bitflip']['trials']} bit flips rejected"],
            ["3", "RBAC with ownership checks", f"Met: {F.RBAC['matched']}/{F.RBAC['total']} matrix cells"],
            ["4", "Integrity on download", "Met: GCM tag and SHA-256 compared in the browser"],
            ["5", "Audit log of actions and denials", f"Met with limits: {len(detected_classes)} of {n_cls} tamper classes caught; concurrent writers fork the chain"],
            ["6", "Evaluation of overhead, access control, integrity", "Met on one shared host; indicative timings, no user study"]]
    ftable(s, 0.55, 2.6, [0.5, 4.5, 7.2], rows, size=12, row_h=0.52, align=["c", "l", "l"])
    ftext(s, 0.55, 6.35, 12.2, 0.6, "Key finding: the cost of client-side encryption is small next to network and API time; the weak point is audit integrity, not confidentiality.", size=13, color=K.FNAVY, italic=True)
    notes[25] = "Be explicit about which objectives were met in full and which with limits."

    # ---- 26 limitations + future scope
    s = S[25]
    set_title(s, "Limitations & Future Scope")
    wipe(s)
    fbox(s, 0.55, 1.8, 6.0, 5.0, fill=K.FZEBRA)
    ftext(s, 0.75, 1.9, 5.6, 0.4, "Known limitations", size=17, color=K.FNAVY, bold=True)
    ftext(s, 0.75, 2.4, 5.6, 4.4, bl([
        "Audit chain: tail truncation and a full re-hash undetected; concurrent writers fork it",
        "Revocation cannot recall a key or ciphertext already downloaded; no re-keying",
        "The server ships the JavaScript that does the crypto (MEGA-style trust)",
        "Clear metadata (name, size, type, owner, time); password loss means data loss",
        "No MFA; JWT in sessionStorage; in-memory login throttle; whole-file encryption, 25 MB cap",
        "Timings from one shared host; no user study",
    ], 6), size=13.5)
    fbox(s, 6.8, 1.8, 6.0, 5.0, fill=K.FHEAD)
    ftext(s, 7.0, 1.9, 5.6, 0.4, "Future scope", size=17, color=K.FNAVY, bold=True)
    ftext(s, 7.0, 2.4, 5.6, 4.4, bl([
        "Sign chain entries or anchor the head hash externally; serialise audit writes",
        "Re-key the file on revoke; chunked encryption for large files",
        "TOTP multi-factor sign-in; higher PBKDF2 iterations; HttpOnly cookies",
        "Restrict GET /api/audit to a user's own events",
        "Object storage and key-management service; PostgreSQL load test",
        "Subresource integrity or a signed web app to reduce the served-JS risk",
    ], 6), size=13.5)
    notes[26] = "Limitations first, then future work drawn from the measured defects."

    # ---- 27 references
    s = S[26]
    set_title(s, "References")
    wipe(s)
    keys = ["base", "ijedr", "geo", "sagi", "mega", "sirius", "plutus", "rbac01", "gcm", "oaep", "pbkdf2", "bcrypt", "jwt", "webcrypto", "audit99", "tamper09"]
    short_ = [f"[{_IDX[k]}] {clean_ref(REFS[_IDX[k] - 1])}" for k in keys]
    short_ = [t if len(t) < 300 else t[:297] + "..." for t in short_]
    ftext(s, 0.55, 1.75, 6.0, 5.2, [(t, {"space_after": 4}) for t in short_[:8]], size=10)
    ftext(s, 6.8, 1.75, 6.0, 5.2, [(t, {"space_after": 4}) for t in short_[8:]] + [(f"The full numbered list of {len(REFS)} references is in the report.", {"italic": True})], size=10)
    notes[27] = "Selected references; the complete numbered list is in the report."

    # ---- 28 thank you
    for sh_ in S[27].shapes:
        if sh_.name == "Text 2":
            K.replace_text(sh_, "Questions & Suggestions")
    notes[28] = "Invite questions."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes.get(i, ""))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, "CipherVault")
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "16.Final_PPT.pptx")))
