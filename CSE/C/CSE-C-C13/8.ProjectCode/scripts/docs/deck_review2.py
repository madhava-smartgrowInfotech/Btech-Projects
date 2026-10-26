"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\Abstracts\\Templates\\Review_2_PPT.pptx.

Self-contained: the small slide helpers are defined here. Every number comes from facts.py (docs/metrics/*.json) or is counted from the code.
    python -m scripts.docs.deck_review2        # from 8.ProjectCode
"""
import os
import tempfile

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"
OUT = os.path.join(F.BATCH, "13.Review_2_PPT.pptx")


# ------------------------------------------------------------------ helpers
def is_ph(sh, *types):
    return sh.is_placeholder and sh.placeholder_format.type in types


def prepare(prs, review_label):
    for lay in prs.slide_layouts:
        for sh in lay.shapes:
            if sh.has_text_frame and LAYOUT_FOOTER_OLD in sh.text_frame.text:
                K.replace_text(sh, f"{F.PRODUCT}  ·  {review_label}")
    cp = prs.core_properties
    cp.title = f"{F.FULL_TITLE}: {review_label}"
    cp.subject = f"Batch {F.BATCH_NO} ({F.SECTION})"
    cp.author = ", ".join(n for n, _ in F.STUDENTS)
    cp.keywords = "secure file storage, AES-256-GCM, RSA-OAEP, role-based access control, audit log"
    cp.comments = ""
    cp.last_modified_by = ""


def set_title(slide, text, size=None):
    for sh in slide.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, text, size)
            return sh


def wipe(slide):
    K.clear(slide, lambda sh: sh.is_placeholder)


def agenda(slide, items, colors, cols=4):
    n = len(items)
    rows = (n + cols - 1) // cols
    gx, gy = 0.29, 0.3
    w = (12.13 - gx * (cols - 1)) / cols
    h = min(1.45, (5.3 - gy * (rows - 1)) / rows)
    x0, y0 = 0.6, 1.55
    for i, (n_, label) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = x0 + c * (w + gx), y0 + r * (h + gy)
        K.box(slide, x, y, w, h)
        K.text(slide, x + 0.25, y + 0.14, 1.0, 0.5, n_, size=26, color=colors[i % len(colors)], bold=True, font="Cambria")
        K.text(slide, x + 0.25, y + 0.72, w - 0.5, 0.65, label, size=16, color=K.INK, bold=True)


def title_slide(s, subtitle, label):
    for sh in s.shapes:
        nm = sh.name
        if is_ph(sh, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, F.TITLE, 28)
        elif is_ph(sh, PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.BODY):
            K.replace_text(sh, subtitle, 18)
        elif nm == "review label":
            K.replace_text(sh, label)
        elif nm == "team":
            K.replace_text(sh, "\n".join(f"{n_}  {r_}" for n_, r_ in F.STUDENTS))
        elif nm == "Text 6":
            K.replace_text(sh, f"{F.GUIDE}, {F.GUIDE_DESIGNATION}")
        elif nm == "Text 7":
            K.replace_text(sh, f"{F.DEPT}\n{F.COLLEGE_SHORT}  ·  Batch {F.BATCH_NO} ({F.SECTION})  ·  {F.YEAR}")


def thank_you(s):
    for sh in s.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
            K.replace_text(sh, "Thank you")
        elif is_ph(sh, PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.SUBTITLE):
            K.replace_text(sh, "Questions and suggestions are welcome.")


def trim(path, tag):
    """Copy of a diagram with its white margins removed (written to the temp folder, source untouched)."""
    from PIL import Image, ImageChops

    with Image.open(path) as im:
        im = im.convert("RGB")
        bbox = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
        if bbox:
            pad = 12
            bbox = (max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, im.size[0]), min(bbox[3] + pad, im.size[1]))
            im = im.crop(bbox)
        out = os.path.join(tempfile.gettempdir(), f"ciphervault_r2_{tag}.png")
        im.save(out)
    return out


def clean_png(path, tag):
    """Re-encode a PNG so that no compressed byte run happens to spell a banned word (the package check scans raw bytes)."""
    import re

    from PIL import Image

    banned = re.compile(rb"(?<![a-z])(mcnn|pheme|snopes)(?![a-z])")
    with Image.open(path) as im:
        im = im.convert("RGB")
        for level in (9, 6, 7, 5, 4, 3):
            out = os.path.join(tempfile.gettempdir(), f"ciphervault_r2_{tag}.png")
            im.save(out, compress_level=level)
            with open(out, "rb") as f:
                if not banned.search(f.read().lower()):
                    return out
    return out


def shot_box(slide, name, x, y, w, h, caption):
    K.picture(slide, clean_png(F.shot(name), "shot_" + os.path.splitext(name)[0]), x, y, w, h - 0.5, border=True)
    K.text(slide, x, y + h - 0.45, w, 0.45, caption, size=11, color=K.TXT, align="c", italic=True)


def lines_of(*rels):
    """Total line count of the given files (paths relative to 8.ProjectCode)."""
    n = 0
    for rel in rels:
        with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
            n += sum(1 for _ in f)
    return n


def med(d):
    return d["median"]


# ------------------------------------------------------------------ the deck
def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}

    sizes = [1024, 65536, 1048576, 10485760, 26214400]
    size_lbl = {1024: "1 KiB", 65536: "64 KiB", 1048576: "1 MiB", 10485760: "10 MiB", 26214400: "25 MiB"}
    aes = {n: F.AES[str(n)] for n in sizes}
    e2e = {n: F.E2E[str(n)] for n in (1024, 1048576, 10485760)}
    api = F.API
    up = {n: api["upload_ms"][str(n)] for n in (1024, 65536, 1048576, 10485760, 26212352)}
    dn = {n: api["download_ms"][str(n)] for n in (1024, 65536, 1048576, 10485760, 26212352)}
    tam = F.TAMPER["audit_tamper"]
    n_classes = len(tam)
    n_detected = sum(1 for v in tam.values() if v["detected"] == v["trials"])
    conc = F.CONC["4_workers"]
    mb10 = 10485760
    up_over = e2e[mb10]["encrypted_up"]["median"] - e2e[mb10]["plain_up"]["median"]
    up_over_pct = up_over / e2e[mb10]["plain_up"]["median"]
    dn_over = e2e[mb10]["encrypted_down"]["median"] - e2e[mb10]["plain_down"]["median"]

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: files are encrypted in the browser with AES-256-GCM, keys are wrapped with RSA-OAEP, "
                "and access is enforced by Owner, Editor and Viewer roles with a hash-chained audit log",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = ("This review shows how CipherVault is designed and built, what is implemented, the first measured results and the open items. "
                "Introduce the four team members and the guide.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and data"), ("03", "Client-side processing and crypto design"), ("04", "Configuration and decision logic"),
               ("05", "Data flow, modules, UML"), ("06", "Technology stack"), ("07", "Implementation progress"), ("08", "Preliminary results"),
               ("09", "Output screens"), ("10", "Testing"), ("11", "Challenges"), ("12", "Next steps")],
           [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Files kept on a server are readable by the provider, its administrators and anyone holding a database backup. Without roles any signed-in user may reach another user's files, tampering goes unnoticed, and an incident cannot be reconstructed.", K.ORANGE, "!"),
        ("Proposed system", "CipherVault encrypts every file in the browser with AES-256-GCM, wraps the file key for each recipient with RSA-2048-OAEP, enforces Owner, Editor and Viewer roles on the server, checks SHA-256 on every download and records each action in a hash-chained audit log.", K.BLUE, "i"),
        ("Base paper link", "Nekouie et al. secure health-record access with attribute-based encryption, a blockchain ledger and an LLM attribute extractor. We adopt only the motivation (fine-grained access control, a tamper-evident record of access) and the idea of costing each primitive. Techniques and hardware differ, so numbers are not compared.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.6, W, 5.0, t, b_, col, gl, body_size=15.5)
    notes[3] = ("Recap of Review 1. The base paper's timings are calculated from OpenSSL primitive costs on a server and a Raspberry Pi, not measured end to end, "
                "so we report our own measurements and compare design choices only. The closest architecture is Sowmiya et al. (IJEDR, 2026).")

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, trim(F.diag("01_system_architecture.png"), "01"), 0.6, 1.3, 7.7, 5.7)
    K.text(s, 8.55, 1.45, 4.2, 5.4, [
        ("**The browser is the crypto endpoint**", {"space_after": 8}),
        (f"App: React 19 + Vite; Web Crypto API; port {F.WEB_PORT} in development, or served by the API.", {"bullet": True}),
        (f"API: FastAPI on port {F.API_PORT}; 24 endpoints in five routers (auth, users, files, sharing, audit).", {"bullet": True}),
        ("Server holds ciphertext, IVs, wrapped keys, hashes, public keys and the audit log, never plaintext or private keys.", {"bullet": True}),
        ("Storage: SQLite by default (PostgreSQL through Docker), ciphertext as files under random names.", {"bullet": True}),
    ], size=14.5, color=K.INK)
    notes[4] = "Routes live in backend/app/api; permission_service and audit_service hold the RBAC rules and the hash chain. The server never decrypts anything."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: encrypt, store, share, verify")
    wipe(s)
    K.picture(s, trim(F.diag("02_high_level_workflow.png"), "02"), 0.5, 1.4, 7.9, 5.0)
    for i, (t, b_) in enumerate([("Register and unlock", "The browser makes an RSA-2048 key pair; the private key is encrypted with a key derived from the password (PBKDF2) before it is stored. Unlocking decrypts it in memory only."),
                                 ("Encrypt, upload, share", "A fresh AES key encrypts the file; the key is wrapped with the owner's public key. Sharing re-wraps the key for the recipient, so the server never sees it."),
                                 ("Download and verify", "RBAC is checked, the wrapped key is unwrapped, AES-GCM decrypts, SHA-256 is compared. Every step writes a hash-chained audit entry.")]):
        y = 1.4 + i * 1.78
        K.box(s, 8.55, y, 4.18, 1.65)
        K.text(s, 8.68, y + 0.07, 3.9, 0.4, t, size=15, color=K.INK, bold=True)
        K.text(s, 8.68, y + 0.42, 3.9, 1.2, b_, size=12, color=K.TXT)
    K.text(s, 0.5, 6.5, 7.9, 0.45, "High-level workflow as implemented in the application.", size=12, color=K.TXT, align="c", italic=True)
    notes[5] = "Revoking access deletes the recipient's wrapped key on the server; it cannot recall a key or ciphertext that was already downloaded."

    # ---- 6 data
    s = S[5]
    set_title(s, "Data: demo vault and measurement workloads")
    wipe(s)
    for i, (v, l, c) in enumerate([("0", "ML datasets: nothing is trained or classified", K.ORANGE),
                                   ("5", "fictional demo files, 3 demo accounts", K.BLUE),
                                   ("36", "RBAC cells tested: 4 principals x 9 operations", K.GREEN),
                                   (f"{F.TAMPER['audit_entries_available']}", "audit entries used in the tamper study", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Workload", "What it is", "Size and repetitions"],
            ["Demo vault", "Fictional files created by the in-app demo login for owner, editor and viewer accounts (example.com addresses); used for screenshots", "5 files, 706 B of plaintext in total"],
            ["Crypto size sweep", "Random bytes encrypted, decrypted and hashed with Web Crypto in Chrome " + F.BR["browser_version"].split(".")[0],
             "1 KiB, 64 KiB, 1 MiB, 10 MiB, 25 MiB; " + ", ".join(str(aes[n]["encrypt"]["n"]) for n in sizes) + " runs"],
            ["Encrypted vs plain transfer", "The same endpoint used with and without browser encryption", "1 KiB, 1 MiB, 10 MiB; " + ", ".join(str(e2e[n]["encrypted_up"]["n"]) for n in e2e) + " runs"],
            ["Access control and tamper", "Exhaustive RBAC matrix; 2,000 ciphertext bit flips; nine audit-log tamper classes of about 200 trials each", "one file, four principals; one audit chain"],
            ["Limits", "Synthetic data only, no user study; the host CPU was shared with other jobs, so timings are indicative", "single machine, loopback"]]
    K.table(s, 0.6, 2.95, [2.2, 6.2, 3.73], rows, font_size=12, row_h=0.66, first_bold=True)
    notes[6] = ("This is security software, so there is no training data. The demo accounts and files are fictional, and the numbers come from workloads we generated: "
                "random bytes of fixed sizes and scripted attacks on the audit log.")

    # ---- 7 client-side processing
    s = S[6]
    set_title(s, "Client-side processing before upload")
    wipe(s)
    K.flow(s, 0.6, 1.45, 12.13, 1.0, [("Read file", K.NAVY), ("SHA-256 of plaintext", K.PURPLE), ("Random 256-bit key + 12-byte IV", K.PURPLE),
                                       ("AES-256-GCM encrypt", K.GREEN), ("Wrap key (RSA-OAEP)", K.GREEN), ("Upload multipart", K.ORANGE)], size=11.5, gap=0.22)
    for i, (v, l, c) in enumerate([("16 B", "authentication tag added by AES-GCM: ciphertext is 16 bytes longer than the file", K.ORANGE),
                                   (f"{F.CRY['rsa_wrapped_bytes']} B", "wrapped file key: one RSA-2048-OAEP block, per recipient", K.BLUE)]):
        K.tile(s, 0.6 + i * 6.2, 2.8, 5.95, 1.25, v, l, c, vsize=28, lsize=11.5)
    K.text(s, 0.6, 4.3, 12.13, 2.7, [
        (f"Registration: the browser generates the RSA-2048 key pair (median {F.ms(F.CRY['rsa_keygen']['median'])} ms) and encrypts the private key with PBKDF2 ({F.PBKDF2_ITER:,} iterations, median {F.ms(F.CRY['pbkdf2_120k']['median'])} ms).", {"bullet": True}),
        ("The server validates what it can without seeing plaintext: IV decodes to 12 bytes, SHA-256 is 64 hex characters, wrapped key is base64 (256 bytes when sharing), file name at most 512 characters.", {"bullet": True}),
        (f"Uploads above {F.UPLOAD_LIMIT_MB} MB are refused with HTTP 413 (measured); the whole file is encrypted in memory, so there is no chunking yet.", {"bullet": True}),
        ("The ciphertext is stored under a random 32-hex name; the original file name stays in the database as clear metadata.", {"bullet": True}),
    ], size=15, color=K.INK, space_after=9)
    notes[7] = "These are the steps in frontend/src/lib/vaultCrypto.js and vault.js. Nothing leaves the browser before step six except the encrypted bytes and the wrapped key."

    # ---- 8 crypto design
    s = S[7]
    set_title(s, "Cryptographic design (no ML model)")
    wipe(s)
    K.picture(s, trim(F.diag("11_key_hierarchy.png"), "11"), 0.6, 1.35, 7.6, 5.0)
    K.text(s, 8.5, 1.45, 4.25, 5.4, [
        ("**File key**: a random AES-256-GCM key per file; a new random 12-byte IV for each encryption.", {"bullet": True, "space_after": 7}),
        ("**Key wrapping**: RSA-2048-OAEP with SHA-256, one wrapped copy per recipient, stored in file_permissions.", {"bullet": True, "space_after": 7}),
        ("**Private key**: exported as PKCS#8 and encrypted with an AES-256-GCM key derived from the password by PBKDF2-HMAC-SHA-256.", {"bullet": True, "space_after": 7}),
        ("**Passwords** are separate: bcrypt on the server, never used as a key.", {"bullet": True, "space_after": 7}),
        ("All primitives come from the browser's Web Crypto API; none is written by hand.", {"bullet": True, "italic": True, "color": K.TXT}),
    ], size=13, color=K.INK)
    K.text(s, 0.6, 6.45, 7.6, 0.45, "Key hierarchy: password, private key, file key, ciphertext.", size=12, color=K.TXT, align="c", italic=True)
    notes[8] = "Hybrid encryption was chosen because RSA is too slow and too small for files, while AES-GCM gives confidentiality and integrity in one pass."

    # ---- 9 configuration
    s = S[8]
    set_title(s, "System and cryptographic configuration")
    wipe(s)
    rows = [["Setting", "Value"],
            ["File cipher", "AES-256-GCM, random 12-byte IV, 16-byte tag; whole file in memory; at most " + str(F.UPLOAD_LIMIT_MB) + " MB"],
            ["Key wrap", "RSA-2048-OAEP with SHA-256, exponent 65537, 256-byte wrapped key"],
            ["Private-key protection", f"PBKDF2-HMAC-SHA-256, {F.PBKDF2_ITER:,} iterations, 16-byte salt, AES-256-GCM"],
            ["Passwords and sessions", f"bcrypt cost {F.BCRYPT_COST}, at least 8 characters; JWT HS256, {F.JWT_MINUTES} minutes; login throttle {F.LOGIN_LIMIT[0]} attempts per {F.LOGIN_LIMIT[1]} s per IP and email (in memory)"],
            ["Integrity and audit", "SHA-256 of the plaintext stored and checked on download; audit hash = SHA-256 of previous hash, time, user, file, action, success, details"],
            ["Storage", "SQLite by default, PostgreSQL via Docker; ciphertext under storage/encrypted with random 32-hex names"],
            ["Measuring machine", f"{F.ENV['cpu'].replace('12th Gen Intel Core ', 'Intel ')}, {F.ENV['ram_gb']} GB RAM, Windows 11, Python {F.ENV['python']}, Chrome {F.BR['browser_version']}, loopback 127.0.0.1"]]
    K.table(s, 0.6, 1.45, [2.5, 9.63], rows, font_size=13, row_h=0.68, first_bold=True)
    notes[9] = "The same configuration applies to every measurement. The project's iteration count (120,000) is lower than the 310,000 reported by the IJEDR paper; this is listed as a limitation."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: RBAC rules and the audit chain")
    wipe(s)
    rbac_rows = [["Role", "Read", "Update", "Share / role / revoke", "Delete, file audit"],
                 ["Owner", "yes", "yes", "yes", "yes"], ["Editor", "yes", "yes", "no", "no"],
                 ["Viewer", "yes", "no", "no", "no"], ["Stranger", "no", "no", "no", "no"]]
    K.table(s, 0.6, 1.4, [1.0, 0.7, 0.85, 1.65, 1.4], rbac_rows, font_size=12, row_h=0.46, first_bold=True, align=["l", "c", "c", "c", "c"], header_size=11)
    K.text(s, 0.6, 3.85, 5.6, 3.1, [
        (f"The role is computed per request from ownership and the file_permissions row; denied requests return 403 and write an unauthorized_access entry.", {"bullet": True, "space_after": 6}),
        (f"Measured: all {F.RBAC['matched']} of {F.RBAC['total']} cells matched the rules; unauthenticated, forged, expired, wrong-secret and alg=none tokens all returned 401.", {"bullet": True, "space_after": 6}),
        (f"Audit chain: {n_detected} of {n_classes} tamper classes are always caught; deleting the last entries is not (0 of {tam['truncate_tail']['trials']}).", {"bullet": True, "space_after": 6}),
    ], size=13.5, color=K.INK)
    K.picture(s, trim(F.diag("12_audit_hash_chain.png"), "12"), 6.5, 1.35, 6.23, 4.55)
    K.text(s, 6.5, 6.0, 6.23, 0.9, "Audit entries are linked by SHA-256. The verifier checks internal consistency only: there is no secret key or external anchor.", size=11.5, color=K.TXT, align="c", italic=True)
    notes[10] = ("The rules are in permission_service.py (four small functions). The chain code is audit_service.py. A full rewrite that recomputes every later hash is also not detected, "
                 "and concurrent writers can fork the chain; both are open items.")

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, trim(F.diag("04_dfd_level1.png"), "04"), 0.6, 1.3, 6.4, 5.2)
    K.text(s, 0.6, 6.55, 6.4, 0.4, "DFD level 1: the processes and the data stores.", size=12, color=K.TXT, align="c", italic=True)
    B = "backend/app/"
    mods = [["Module", "Lines", "Role"],
            ["api/files.py", lines_of(B + "api/files.py"), "upload, download, update, delete"],
            ["api/sharing.py", lines_of(B + "api/sharing.py"), "share, role change, revoke"],
            ["api/auth.py + users.py", lines_of(B + "api/auth.py", B + "api/users.py"), "accounts, keys, directory"],
            ["api/audit.py", lines_of(B + "api/audit.py"), "history, chain verify"],
            ["services/ (2 files)", lines_of(B + "services/audit_service.py", B + "services/permission_service.py"), "hash chain, RBAC rules"],
            ["db/models.py", lines_of(B + "db/models.py"), "4 tables"],
            ["core/ + api/deps.py", lines_of(B + "core/security.py", B + "core/config.py", B + "api/deps.py"), "bcrypt, JWT, settings"],
            ["lib/vaultCrypto.js", lines_of("frontend/src/lib/vaultCrypto.js"), "browser cryptography"]]
    K.table(s, 7.25, 1.45, [2.2, 0.7, 2.58], mods, font_size=11, row_h=0.5, first_bold=True, align=["l", "r", "l"])
    notes[11] = (f"Counted from the files: the backend is {F.LOC['backend_py']['lines']:,} lines in {F.LOC['backend_py']['files']} files, the frontend source {F.LOC['frontend_src']['lines']:,} lines in {F.LOC['frontend_src']['files']} files. "
                 "Each route validates, checks the role, performs the change and writes an audit entry.")

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database design and UML")
    wipe(s)
    K.picture(s, trim(F.diag("06_uml_class.png"), "06"), 0.6, 1.3, 6.0, 4.9)
    K.text(s, 0.6, 6.25, 6.0, 0.8, "UML class diagram. **users** own many **files**; **file_permissions** links a user to a file with a role and that user's wrapped key (unique per file and user).", size=11.5, color=K.TXT, align="c", italic=True)
    K.picture(s, trim(F.diag("09_er_diagram.png"), "09"), 6.8, 1.3, 5.93, 4.9)
    K.text(s, 6.8, 6.25, 5.93, 0.8, "Entity-relationship diagram. **audit_logs** keeps previous_hash and current_hash per event; its user and file links are nullable, so entries survive deletion.", size=11.5, color=K.TXT, align="c", italic=True)
    notes[12] = "SQLAlchemy 2.0 declarative models. Deleting a file removes its permissions by cascade and its ciphertext object in the route; the audit entry stays."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    stack = [("Python 3.11+", "FastAPI, uvicorn, pydantic; REST under /api", K.BLUE), ("SQLAlchemy 2.0", "SQLite by default, PostgreSQL via psycopg", K.ORANGE),
             ("PyJWT + bcrypt", "session tokens and password hashing (cost 12)", K.GREEN), ("Web Crypto API", "AES-GCM, RSA-OAEP, PBKDF2, SHA-256 in the browser", K.PURPLE),
             ("React 19 + Vite 8", "single-page app, React Router 7", K.BLUE), ("Recharts + three.js", "dashboard charts and landing hero; Framer Motion, GSAP", K.ORANGE),
             ("pytest + httpx", f"{F.PYTEST_TOTAL} backend tests; Playwright for the UI walk", K.GREEN), ("Docker Compose", "PostgreSQL deployment option and run.bat for one-click local use", K.PURPLE)]
    for i, (t, b_, col) in enumerate(stack):
        r, c = divmod(i, 4)
        x, y = 0.6 + c * 3.09, 1.5 + r * 2.5
        K.box(s, x, y, 2.85, 2.25)
        K.circle(s, x + 0.22, y + 0.22, 0.5, col, str(i + 1), 16)
        K.text(s, x + 0.22, y + 0.9, 2.45, 0.45, t, size=15, color=K.INK, bold=True)
        K.text(s, x + 0.22, y + 1.35, 2.45, 0.85, b_, size=12.5, color=K.TXT)
    K.text(s, 0.6, 6.6, 12.13, 0.4, "Everything runs locally on one machine; no cloud service or external key manager is used yet.", size=13, color=K.TXT, italic=True)
    notes[13] = "requirements.txt gives minimum versions; the frontend versions are those in package.json."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Registration, login, JWT sessions", "Done", f"bcrypt cost {F.BCRYPT_COST}; forged, expired and alg=none tokens all rejected (401)"],
            ["Client-side encryption and key wrapping", "Done", f"AES-256-GCM + RSA-2048-OAEP; {F.TAMPER['ciphertext_bitflip']['detected']:,} of {F.TAMPER['ciphertext_bitflip']['trials']:,} bit flips detected"],
            ["RBAC and sharing", "Done", f"{F.RBAC['matched']} of {F.RBAC['total']} access-matrix cells as expected; revoked user gets 403"],
            ["Integrity check and audit log", "Done, with gaps", f"{n_detected} of {n_classes} tamper classes caught; tail truncation and concurrent writers are not handled"],
            ["React interface", "Done", "landing, dashboard, files, file detail, sharing, audit log, security, 360 px layout"],
            ["MFA, chunked upload, key rotation, KMS", "Not implemented", "named as future work; not in the code"],
            ["Tests", "Done", f"pytest {F.PYTEST_PASSED}/{F.PYTEST_TOTAL}; API walk {F.E2E_PASSED}/{F.E2E_TOTAL}; browser walk {F.UI_PASSED}/{F.UI_TOTAL}"]]
    K.table(s, 0.6, 1.45, [4.2, 1.9, 6.03], rows, font_size=12.5, row_h=0.66, first_bold=True)
    notes[14] = "All six objectives of Review 1 have an implementation; the gaps are in the audit log and in features beyond the original scope."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results")
    wipe(s)
    K.bar_chart(s, 0.6, 1.3, 6.9, 3.5, ["1 KiB up", "1 MiB up", "10 MiB up", "1 KiB down", "1 MiB down", "10 MiB down"],
                [("Encrypted (median ms)", [round(e2e[n][k]["median"], 1) for k in ("encrypted_up", "encrypted_down") for n in e2e]),
                 ("Plain (median ms)", [round(e2e[n][k]["median"], 1) for k in ("plain_up", "plain_down") for n in e2e])],
                colors=[K.NAVY, K.GREEN], number_format="0", font_size=9, max_value=260, label_size=8)
    # the chart categories above are ordered up(1 KiB, 1 MiB, 10 MiB) then down(...)
    K.text(s, 0.6, 4.8, 6.9, 0.35, "Browser end to end, encrypted vs plain transfer on the same endpoint (loopback).", size=11, color=K.TXT, align="c", italic=True)
    rrows = [["Measurement", "Result"],
             ["AES-GCM encrypt, 10 MiB", f"{F.ms(aes[mb10]['encrypt']['median'])} ms median"],
             ["AES-GCM encrypt, 25 MiB", f"{F.ms(aes[26214400]['encrypt']['median'])} ms median"],
             ["RSA-2048 wrap / unwrap", f"{F.ms(F.CRY['rsa_wrap']['median'])} / {F.ms(F.CRY['rsa_unwrap']['median'])} ms"],
             ["Login (bcrypt cost 12)", f"{F.ms(api['login_ms']['median'])} ms median"],
             ["RBAC matrix", f"{F.RBAC['matched']} of {F.RBAC['total']} cells correct"],
             ["Ciphertext bit flips", f"{F.TAMPER['ciphertext_bitflip']['detected']:,} of {F.TAMPER['ciphertext_bitflip']['trials']:,} caught"]]
    K.table(s, 7.75, 1.4, [2.6, 2.38], rrows, font_size=11.5, row_h=0.5, first_bold=True, align=["l", "r"], header_size=11)
    K.text(s, 0.6, 5.25, 12.13, 1.8, [
        (f"Cost of encryption is small: for a 10 MiB file the encrypted upload takes {up_over:.0f} ms more than a plain one ({F.pct(up_over_pct, 0)}) and the verified download {dn_over:.0f} ms more; AES itself takes about {F.ms(aes[mb10]['encrypt']['median'])} ms.", {"bullet": True}),
        (f"The audit chain verifies in {F.ms(F.SCALE['5000']['verify_ms_median'])} ms for 5,000 entries, but it does not catch deleted tail entries (0 of {tam['truncate_tail']['trials']}) or a full re-hash.", {"bullet": True}),
        (f"100 concurrent failed logins broke the chain (first bad entry {conc['failure_at']}): the audit writer assumes one writer at a time. Reported, not yet fixed.", {"bullet": True}),
    ], size=13, color=K.INK, space_after=5)
    notes[15] = ("Results are reported as measured, including the negative ones. The host was shared with other jobs, so run-to-run spread reached about three times at 10 MiB; "
                 "treat the numbers as indicative. The base paper's costs are calculated on other hardware and are not comparable.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    shot_box(s, "06_dashboard.png", 0.6, 1.4, 3.95, 2.85, "Dashboard: files, roles, security events")
    shot_box(s, "07_my-files.png", 4.69, 1.4, 3.95, 2.85, "My files: ciphertext sizes and roles")
    shot_box(s, "09_share-access.png", 8.78, 1.4, 3.95, 2.85, "Sharing: grant Editor or Viewer access")
    shot_box(s, "10_audit-log.png", 0.6, 4.35, 3.95, 2.7, "Audit log with chain verification")
    shot_box(s, "11_security.png", 4.69, 4.35, 3.95, 2.7, "Security profile: keys and crypto settings")
    shot_box(s, "13_shared-with-me.png", 8.78, 4.35, 3.95, 2.7, "Viewer account: files shared with me")
    notes[16] = "All screens are captures of the running application with the fictional demo data. More screens follow in the final presentation."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.PYTEST_PASSED} / {F.PYTEST_TOTAL}", f"pytest tests pass in about {F.PYTEST_SECONDS:.0f} s", K.GREEN),
                                   (f"{F.E2E_PASSED} / {F.E2E_TOTAL}", "API end-to-end checks pass", K.BLUE),
                                   (f"{F.UI_PASSED} / {F.UI_TOTAL}", "real-browser UI walk steps pass", K.ORANGE),
                                   (f"{F.EVAL_PASSED} / {F.EVAL_TOTAL}", "checks in the evaluation script pass", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Operation (n calls)", "Median ms", "p95 ms"],
            [f"Health check ({api['health_ms']['n']})", F.ms(api["health_ms"]["median"]), F.ms(api["health_ms"]["p95"])],
            [f"GET /api/auth/me ({api['me_ms']['n']})", F.ms(api["me_ms"]["median"]), F.ms(api["me_ms"]["p95"])],
            [f"Login, bcrypt cost 12 ({api['login_ms']['n']})", F.ms(api["login_ms"]["median"]), F.ms(api["login_ms"]["p95"])],
            [f"List 65 files ({api['list_files_ms']['n']})", F.ms(api["list_files_ms"]["median"]), F.ms(api["list_files_ms"]["p95"])],
            [f"Upload 1 MiB ({up[1048576]['n']})", F.ms(up[1048576]["median"]), F.ms(up[1048576]["p95"])],
            [f"Download 1 MiB ({dn[1048576]['n']})", F.ms(dn[1048576]["median"]), F.ms(dn[1048576]["p95"])]]
    K.table(s, 0.6, 3.0, [4.2, 1.1, 1.1], rows, font_size=12.5, row_h=0.55, first_bold=True, align=["l", "r", "r"])
    K.text(s, 7.3, 3.0, 5.45, 4.0, [
        ("**What the tests cover**: registration and login, encrypted upload and download, owner, editor, viewer and stranger access, share, role change, revoke, the audit chain and the crypto round trip.", {"bullet": True, "space_after": 7}),
        ("**What they do not cover**: more than a few users at once, files above 25 MB, Firefox and Safari, PostgreSQL, a Docker build, screen readers.", {"bullet": True, "space_after": 7}),
        ("**Not done**: user study, load test, independent security audit.", {"bullet": True, "space_after": 7}),
        ("Timings are from one machine with 127.0.0.1 as host.", {"bullet": True, "italic": True, "color": K.TXT}),
    ], size=13.5, color=K.INK)
    notes[17] = "The study that found the audit-log weaknesses is a script that edits the database directly and then calls the verifier; it is in scripts/measure_metrics.py."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "What we found", "Action"],
            ["Audit log trust", f"Deleting the last entries goes unnoticed (0 of {tam['truncate_tail']['trials']}); a full re-hash is not detected", "Plan an HMAC key or an external anchor for the latest hash"],
            ["Concurrent writers", f"{conc['requests']} parallel failed logins left the chain invalid (first bad entry {conc['failure_at']})", "Serialise the read-then-write of the last hash"],
            ["Revocation", "Deleting the wrapped key cannot recall a key or file already downloaded", "Document it; re-key on revoke is future work"],
            ["Who sees the audit log", "GET /api/audit lists the global event history to any signed-in user", "Restrict to the user's own events and owned files"],
            ["Trust in the web app", "The server serves the JavaScript that does the encryption", "State it as a limit; signed builds are future work"],
            ["Measuring honestly", "Chrome's timer has 0.1 ms steps and the CPU was shared", "Timed batches of 200 operations; reported spread"]]
    K.table(s, 0.6, 1.4, [2.5, 5.2, 4.43], rows, font_size=13, row_h=0.78, first_bold=True)
    notes[18] = "Each challenge is a measured finding, not a guess; the evidence is in docs/REPORT_FACTS.md and the metrics file."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Fix and re-measure", "Lock the audit writer, add a keyed or anchored chain head, restrict the global audit list, then repeat the tamper and concurrency studies with the same scripts.", K.ORANGE, "1"),
        ("Close the gaps", "Chunked streaming above 25 MB, MFA, key rotation and re-keying on revoke, a PostgreSQL run, and a key-management service for the JWT secret.", K.BLUE, "2"),
        ("Deliver", "Finish the final report and the IEEE paper from the measured results, rehearse the demo, and keep every number tied to the metrics files.", K.GREEN, "3"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.6, W, 3.9, t, b_, col, gl, body_size=16.5)
    notes[19] = "The open items are the ones identified by the measurements, in priority order."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Close the review and invite questions."

    for i, t in notes.items():
        K.set_notes(S[i - 1], t)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


def main():
    build(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
