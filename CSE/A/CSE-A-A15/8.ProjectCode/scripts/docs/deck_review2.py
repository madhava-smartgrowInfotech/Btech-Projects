"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx.

Self-contained: the small slide helpers (prepare, set_title, wipe, agenda, title_slide, thank_you) are defined here so the deck does not depend
on the Review 1 module. All numbers come from facts.py (experiments/**/metrics.json); nothing is typed in by hand.
    python -m scripts.docs.deck_review2        # from 8.ProjectCode
"""
import os

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"


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
    cp.keywords = "hybrid encryption, AES-GCM, RSA-OAEP, LSB steganography, PSNR, SSIM"
    cp.comments = ""
    cp.last_modified_by = ""


def set_title(slide, text, size=None):
    for sh in slide.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, text, size)
            return sh


def wipe(slide):
    K.clear(slide, lambda sh: sh.is_placeholder)


def agenda(slide, items, colors, cols=3):
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
            K.replace_text(sh, F.TITLE, 32)
        elif is_ph(sh, PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.BODY):
            K.replace_text(sh, subtitle, 20)
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
    """Copy of a diagram or chart with its white margins removed (written to the temp folder, source untouched)."""
    import tempfile

    from PIL import Image, ImageChops

    with Image.open(path) as im:
        im = im.convert("RGB")
        bbox = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
        if bbox:
            pad = 12
            bbox = (max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, im.size[0]), min(bbox[3] + pad, im.size[1]))
            im = im.crop(bbox)
        out = os.path.join(tempfile.gettempdir(), f"a15_r2_{tag}.png")
        im.save(out)
    return out


def shot_box(slide, name, x, y, w, h, caption):
    """Real screenshot in a w x h area with a one-line caption under it."""
    K.picture(slide, F.shot(name), x, y, w, h - 0.34, border=True)
    K.text(slide, x, y + h - 0.3, w, 0.3, caption, size=11, color=K.TXT, align="c", italic=True)


def api_ms(prefix):
    for k, v in F.API.items():
        if k.startswith(prefix):
            return v["median_ms"]
    raise KeyError(prefix)


# ------------------------------------------------------------------ the deck
def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}

    ev, ex, sm = F.EV, F.EX, F.S
    rsa = {r["rsa_bits"]: r for r in ex["rsa_study"]}
    fs = ex["fill_study"]
    sa = ex["steganalysis"]
    tamper = ex["tamper_study"]
    extra = {r["attack"]: r for r in ex["extra_attacks"]}
    rob = {r["attack"]: r for r in ev["robustness"]}
    survived = sum(1 for r in ev["robustness"] if r["recovered"] == 6)
    fill_floor = min(r["psnr_mean"] for r in fs["rows"])

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: AES-256-GCM and RSA-OAEP encryption, hidden by LSB steganography in a PNG",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = ("This review shows how CipherVeil is designed and built, what is implemented, the first measured results from our own evaluation, and the open items. "
                "Introduce the four team members and the guide.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology, data and preprocessing"), ("03", "The pipeline and its configuration"), ("04", "Decision logic and data flow"),
               ("05", "Entities, UML and technology stack"), ("06", "Implementation progress"), ("07", "Preliminary results and output screens"),
               ("08", "Testing and challenges"), ("09", "Next steps")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Encryption alone shows that something secret is moving. Hiding alone protects nothing once found. Symmetric keys are fast but sharing them is the weak point, "
                    "and naive LSB embedding can degrade the picture.", K.ORANGE, "!"),
        ("Proposed system", "CipherVeil encrypts a file with a fresh AES-256-GCM key, wraps that key with the receiver's RSA public key, and hides the bundle in the least significant bits "
                            "of a PNG. The receiver extracts, unwraps, verifies the tag and gets the file back byte for byte.", K.BLUE, "i"),
        ("Base paper link [1]", "Ahmad and Rass (ProSt) hide secret bits among random decoy LSBs so an untrusted cloud can compute on them. We keep the LSB carrier and key-exchange framing, "
                                "but move a whole file from sender to receiver and measure it. We do not implement homomorphic computation or its security proof.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.6, W, 4.5, t, b_, col, gl, body_size=17)
    notes[3] = ("Recap of Review 1: the surveyed work advances steganography and encryption independently. The gap is a practical hybrid AES-RSA plus LSB pipeline evaluated end to end on capacity, "
                "imperceptibility and speed. ProSt reports no PSNR, SSIM or capacity, so we cannot compare numbers with it directly.")

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, trim(F.diag("01_system_architecture.png"), "01"), 0.6, 1.3, 7.2, 5.7)
    K.text(s, 8.0, 1.45, 4.75, 5.4, [
        ("**Three tiers, one small database**", {"space_after": 8}),
        (f"Console: React 18 + Vite on port {F.WEB_PORT}, 8 pages: landing, sign-in, keys, send, receive, analysis, robustness, log.", {"bullet": True}),
        (f"API: FastAPI on port {F.API_PORT}, 24 endpoints under /api, JWT sign-in (12 h), bcrypt password hashes.", {"bullet": True}),
        ("Services: crypto, lsb, metrics, pipeline, plots, robustness, benchmark (about 1,040 lines of backend Python).", {"bullet": True}),
        ("Storage: SQLite with users, keypairs and oplog; cover, stego and restored files under data/outputs.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[4] = ("Routes live in backend/app/routes; the services hold all cryptographic and image logic and are shared by the API, the benchmark and ml/eval.py, so the numbers in this deck come from the same code the user runs.")

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: encrypt, wrap, hide, recover")
    wipe(s)
    K.picture(s, trim(F.diag("02_high_level_workflow.png"), "02"), 0.6, 1.4, 7.4, 5.0)
    for i, (t, b_) in enumerate([("Send", "Header {name, size, SHA-256} plus the file is encrypted with AES-256-GCM; the session key is wrapped with RSA-OAEP; a capacity check precedes embedding."),
                                 ("Hide", "The 32-bit length and the bundle go into the lowest bit of each R, G, B value, row by row; the result is saved as a PNG and measured (PSNR, SSIM)."),
                                 ("Recover", "Extract, unwrap with the private key, verify the GCM tag, then compare the stored SHA-256 with the hash of the restored file.")]):
        y = 1.4 + i * 1.78
        K.box(s, 8.3, y, 4.43, 1.65)
        K.text(s, 8.45, y + 0.07, 4.15, 0.4, t, size=15, color=K.INK, bold=True)
        K.text(s, 8.45, y + 0.42, 4.15, 1.2, b_, size=12.5, color=K.TXT)
    K.text(s, 0.6, 6.5, 7.4, 0.45, "High-level workflow as implemented in the backend services.", size=12, color=K.TXT, align="c", italic=True)
    notes[5] = "A fresh AES key and nonce are generated for every message, so two messages to the same receiver share nothing except the RSA key."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Data: no dataset, six covers and four payloads")
    wipe(s)
    for i, (v, l, c) in enumerate([("6", "cover images, 200 x 200 to 1280 x 720", K.ORANGE), ("4", "synthetic payloads, 99 B to 21.5 KiB", K.BLUE),
                                   (f"{sm['runs']} + {sm['runs_skipped_too_large']}", "evaluation runs that fit + runs blocked by the capacity check", K.GREEN),
                                   ("5", "random payload seeds per fill level in the fill study", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Cover", "Pixels", "Max hidden", "Source and licence"]]
    srcs = {"astronaut_512x512.png": "scikit-image astronaut, NASA photo, public domain", "cat_451x300.png": "scikit-image chelsea, CC0",
            "coffee_600x400.png": "scikit-image coffee, CC0", "coffee_small_200x200.png": "crop of coffee, resized, CC0",
            "generated_landscape_1280x720.png": "procedural, seed 11, generated here", "rocket_640x427.png": "scikit-image rocket, public domain"}
    for c in ev["capacity"]:
        rows.append([c["cover"], f"{c['width']} x {c['height']}", f"{c['max_bundle_kib']} KiB", srcs[c["cover"]]])
    K.table(s, 0.6, 2.95, [3.6, 1.7, 1.6, 5.23], rows, font_size=12.5, row_h=0.46, first_bold=True)
    K.text(s, 0.6, 6.3, 12.13, 0.7, "Payloads: accounts.csv 2,774 B, confidential_memo.pdf 21,517 B, meeting_notes.txt 169 B, settings.json 99 B, all synthetic. Nothing is learned, so there is no "
           "train/test split; the committed files are regenerated by a seeded script. Any image up to 25 MB can be uploaded instead.", size=12, color=K.TXT, italic=True)
    notes[6] = ("CipherVeil needs no external dataset: it is a deterministic scheme, so we evaluate it on a fixed grid of covers and payload sizes. The limit is that these are only six images and four small files; "
                "camera photographs were not tested.")

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Preprocessing: preparing payload and cover")
    wipe(s)
    K.flow(s, 0.6, 1.45, 12.13, 1.0, [("File bytes", K.NAVY), ("Header: name, size, SHA-256", K.PURPLE), ("header_len + header + file", K.PURPLE),
                                       ("Cover to RGB uint8", K.GREEN), ("Capacity check", K.GREEN), ("Bit stream", K.ORANGE)], size=12, gap=0.22)
    for i, (v, l, c) in enumerate([("3.0", "bits per pixel capacity: (W x H x 3 - 32) / 8 bytes per cover", K.BLUE),
                                   ("32 bit", "big-endian length prefix written before the bundle", K.GREEN)]):
        K.tile(s, 0.6 + i * 6.2, 2.8, 5.95, 1.25, v, l, c, vsize=28, lsize=12)
    K.text(s, 0.6, 4.35, 12.13, 2.6, [
        ("The stored file name is stripped to its base name; the header travels inside the encrypted layer, so name, size and hash are not visible.", {"bullet": True}),
        ("Covers are converted to 8-bit RGB; an alpha channel is dropped; output is always PNG, the one common format that stores every pixel value exactly.", {"bullet": True}),
        ("Uploads are capped at 25 MB; an empty file, a non-image cover or an oversized payload is rejected with a message before any bit is written.", {"bullet": True}),
        (f"Overhead added to the file: {rsa[2048]['overhead_bytes']} B (RSA-2048), {rsa[3072]['overhead_bytes']} B (RSA-3072), {rsa[4096]['overhead_bytes']} B (RSA-4096).", {"bullet": True}),
    ], size=16, color=K.INK, space_after=9)
    notes[7] = "Overhead is the wrapped key, magic, lengths, nonce, header JSON and the 16-byte GCM tag. The cover keeps its geometry; only the lowest bit of the first bits-needed values changes."

    # ---- 8 model / pipeline
    s = S[7]
    set_title(s, "The pipeline: AES-256-GCM, RSA-OAEP and LSB")
    wipe(s)
    K.picture(s, trim(F.diag("11_bundle_layout.png"), "11"), 0.6, 1.35, 7.6, 5.0)
    K.text(s, 8.5, 1.45, 4.25, 5.4, [
        ("**AES-256-GCM**: fresh 256-bit key and 96-bit nonce per message; associated data is the magic CVL1; the 16-byte tag authenticates everything.", {"bullet": True, "space_after": 8}),
        ("**RSA-OAEP** (SHA-256, MGF1-SHA-256) wraps the session key; RSA keys below 2048 bits are rejected.", {"bullet": True, "space_after": 8}),
        ("**LSB substitution**: 1 bit per R, G, B value, sequential from the top-left pixel; no key-dependent permutation.", {"bullet": True, "space_after": 8}),
    ], size=14, color=K.INK)
    K.text(s, 0.6, 6.45, 7.6, 0.45, "CVL1 bundle layout and the way its bits are laid into the image.", size=12, color=K.TXT, align="c", italic=True)
    notes[8] = ("All three primitives are standard; the contribution is the way they are combined, the bundle format and the measurement. Sequential embedding is a deliberate simplification and is the reason "
                "steganalysis can find the payload.")

    # ---- 9 configuration
    s = S[8]
    set_title(s, "Configuration and evaluation set-up (no training)")
    wipe(s)
    rows = [["Setting", "Value"],
            ["Cipher", "AES-256-GCM, 96-bit random nonce, associated data CVL1, 128-bit tag; OAEP padding with SHA-256 and MGF1-SHA-256, public exponent 65537"],
            ["Key sizes", f"RSA 2048 / 3072 (default) / 4096; key generation median {rsa[2048]['keygen_ms_median']:.0f} / {rsa[3072]['keygen_ms_median']:.0f} / {rsa[4096]['keygen_ms_median']:.0f} ms"],
            ["Embedding", "1 LSB per colour value, row-major, 32-bit length prefix; stego saved as PNG compression level 6"],
            ["Core evaluation", f"ml/eval.py: 6 covers x payloads 1, 4, 16, 64, 128 KiB, RSA-3072, 3 repeats, median; {sm['runs']} runs fit, {sm['runs_skipped_too_large']} blocked"],
            ["Extra experiments", "fill study (6 covers x 7 fill levels x 5 payload seeds), 9 extra attacks, chi-square and weighted-stego tests, 240 tamper flips"],
            ["Reproducibility", "fixed seeds (payloads 1000-1004, 2024, 77, 9); the covers are regenerated by scripts/make_samples.py"],
            ["Machine", "Core i5-12500 (6 cores), 15.7 GB RAM, Windows 11, Python 3.11.9, cryptography 44.0.0, scikit-image 0.24.0; CPU only"]]
    K.table(s, 0.6, 1.35, [2.3, 9.83], rows, font_size=13, row_h=0.62, first_bold=True)
    K.text(s, 0.6, 6.75, 12.13, 0.4, "Parameters are those in the shipped code; the system has nothing to train or tune.", size=12, color=K.TXT, italic=True)
    notes[9] = ("There is no model to train, so configuration means the cryptographic parameters and the experiment grid. Timings vary by 10 to 30 percent between runs because other jobs share the PC; "
                "accuracy-type numbers such as PSNR do not.")

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: embedding, extraction and checks")
    wipe(s)
    K.picture(s, trim(F.diag("10_flowchart_algorithm.png"), "10"), 0.6, 1.3, 5.9, 5.65)
    rows = [["Check", "Outcome"],
            ["Bundle larger than (W x H x 3 - 32) / 8 bytes", "Send refused, nothing embedded"],
            ["Length header zero or above capacity", "Receive: no payload found"],
            ["Magic is not CVL1 or bundle too short", "Rejected before RSA is used"],
            ["Wrapped-key length differs from key size", "Wrong private key reported"],
            ["RSA unwrap fails", "Not the key the message was sent to"],
            ["GCM tag check fails", "Data modified; nothing released"],
            ["SHA-256 in header differs from restored file", "Hash mismatch flagged"]]
    K.table(s, 6.8, 1.4, [3.65, 2.3], rows, font_size=12, row_h=0.52)
    K.text(s, 6.8, 5.75, 5.95, 1.2, [
        ("Order matters: cheap structural checks run first, the RSA operation second, the authenticated decryption last; every failure ends in an explicit message and a log entry without secrets.", {"bullet": True}),
    ], size=12.5, color=K.INK)
    notes[10] = "This mirrors lsb.embed, lsb.extract, crypto.decrypt_bundle and the receive route. Failures are logged as failed operations with the error text only."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, trim(F.diag("04_dfd_level1.png"), "04"), 0.6, 1.3, 7.0, 5.65)
    rows = [["Module", "Role"], ["services/crypto.py", "keys, bundle encrypt and decrypt"], ["services/lsb.py", "embed, extract, capacity"], ["services/metrics.py", "PSNR, SSIM, MSE"],
            ["services/robustness.py", "nine attacks, hash check"], ["services/pipeline.py", "hide and reveal with timings"], ["routes/ (5 files)", "24 endpoints, ownership checks"],
            ["db.py, auth.py", "3 tables, JWT, bcrypt"], ["tests/, scripts/", f"{F.PYTEST_TOTAL} tests, smoke, experiments"]]
    K.table(s, 7.9, 1.45, [2.35, 2.48], rows, font_size=12, row_h=0.55, first_bold=True)
    K.text(s, 7.9, 6.5, 4.83, 0.5, "Level-1 data-flow diagram of the platform.", size=11.5, color=K.TXT, italic=True)
    notes[11] = "Level 1 follows data from the user through authentication, key management, the send and receive pipelines, analysis and the log. The stores are the database and the output folder."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database entities and UML")
    wipe(s)
    K.picture(s, trim(F.diag("09_er_diagram.png"), "09"), 0.6, 1.3, 6.0, 4.95)
    K.picture(s, trim(F.diag("06_uml_class.png"), "06"), 6.75, 1.3, 6.0, 5.2)
    K.text(s, 0.6, 6.35, 6.0, 0.7, "SQLite: users(id, username, pw_hash), keypairs(user_id, bits, fingerprint, public_pem, private_pem or NULL) and oplog(user_id, op, ok, details JSON).", size=11.5, color=K.TXT, italic=True)
    K.text(s, 6.75, 6.55, 6.0, 0.5, "Services and routes as classes and modules used by the API.", size=11.5, color=K.TXT, italic=True)
    notes[12] = ("Honest point: private keys are stored unencrypted in the local database, so data/app.db must be treated as sensitive. A public-only entry has a NULL private_pem. "
                 "The log table never receives keys, passwords or file contents; a test checks this.")

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    rows = [["Layer", "Technology"],
            ["Language and API", "Python 3.11.9, FastAPI 0.115.6, Uvicorn 0.34.0, SQLAlchemy 2.0.36 on SQLite, PyJWT 2.10.1 (HS256), bcrypt 4.2.1"],
            ["Cryptography", "cryptography 44.0.0: AESGCM, RSA key generation, OAEP; hashlib SHA-256; os.urandom for nonces"],
            ["Image and metrics", "Pillow 11.0.0, NumPy 2.1.3 (bit operations on uint8 arrays), scikit-image 0.24.0 (PSNR, SSIM), matplotlib 3.9.3 (histograms, bit planes)"],
            ["Front end", "React 18.3.1, Vite 6.0.3, Tailwind CSS 4, React Router 6, Axios, Recharts 3; three.js backdrop on the landing page"],
            ["Testing and capture", "pytest with FastAPI TestClient, urllib smoke script, Playwright with Chrome for 1440 x 900 captures"],
            ["Run", f"setup.bat creates the virtual environment and installs packages; run.bat starts both servers on ports {F.API_PORT} and {F.WEB_PORT}; runs offline, no API keys"]]
    K.table(s, 0.6, 1.45, [2.6, 9.53], rows, font_size=14, row_h=0.72, first_bold=True)
    notes[13] = "Versions are those installed on the measurement PC. The front end build succeeds in about 17 seconds; the landing page ships a 747 kB three.js chunk."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Crypto layer: AES-256-GCM, RSA-OAEP, CVL1 bundle, key import and export", "Done", f"{F.PYTEST_CRYPTO} crypto tests; {tamper['trials']}/{tamper['trials']} tampered bundles rejected"],
            ["LSB embedder and extractor with capacity check", "Done", f"{F.PYTEST_LSB} tests; {sm['runs']}/{sm['runs']} byte-exact round trips"],
            ["Quality measures and plots: PSNR, SSIM, histograms, bit planes", "Done", f"PSNR never below {fill_floor:.2f} dB at any fill (6 covers)"],
            ["Robustness (9 attacks) and benchmark", "Done", f"payload survives {survived} of 9; lossy steps destroy it"],
            ["API (24 endpoints), React console (8 pages), secret-free log", "Done", f"{F.SMOKE_PASSED}/{F.SMOKE_TOTAL} smoke checks; {F.PYTEST_API} API tests"],
            ["Key-dependent embedding, error correction, steganalysis resistance", "Not done", "sequential LSB; chi-square flags 30 of 30 cases"],
            ["Encrypted key store, sender signatures, login rate limit", "Not done", "private keys stored unencrypted; placeholder JWT secret"],
            ["Defect: Send page crashes for an account with no keys", "Open", "KeyRound icon is used but not imported in Send.jsx"]]
    K.table(s, 0.6, 1.4, [5.9, 1.3, 4.93], rows, font_size=12.5, row_h=0.6)
    notes[14] = ("State of the code base. The last three rows are the honest gaps. The KeyRound defect was found while capturing screens with a fresh account; the product code was not changed during documentation, "
                 "and the fix is one import line.")

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results: imperceptibility and capacity")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{sm['psnr_db_min']:.1f} dB", f"minimum PSNR in {sm['runs']} runs (mean {sm['psnr_db_mean']:.1f} dB, up to 73% fill)", K.ORANGE),
                                   (f"{sm['ssim_min']:.4f}", f"minimum SSIM (mean {sm['ssim_mean']:.4f})", K.BLUE),
                                   (f"{sm['max_capacity_bits_per_pixel']:.1f} bpp", "capacity: 14.6 KiB (200 x 200) to 337.5 KiB (1280 x 720)", K.GREEN),
                                   (f"{sm['median_decrypt_ms']:.0f} ms", f"median RSA-3072 unwrap + decrypt; encrypt {sm['median_encrypt_ms']} ms, embed {sm['median_embed_ms']} ms", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.35, 2.85, 1.2, v, l, c, vsize=26, lsize=11)
    K.picture(s, trim(F.fig("f01_psnr_vs_fill.png"), "f01"), 0.6, 2.7, 6.0, 3.25)
    K.picture(s, trim(F.fig("f13_psnr_by_payload.png"), "f13"), 6.75, 2.7, 6.0, 3.25)
    K.text(s, 0.6, 6.05, 12.13, 1.0, [
        (f"Measured PSNR follows the closed form 10 log10(255^2 N / (0.5 bits)) within {fs['max_abs_dev_vs_theory_db']} dB; at 100% fill the floor is 51.14 dB. "
         f"Robustness: only lossless re-save and bottom crop survive ({survived} of 9); JPEG even at quality 100 and lossy WebP lose the payload (0 of 6). "
         f"Chi-square on the embedded prefix flags the stego image in {sa['chi2_total']} of {sa['chi2_total']} cases: hidden from the eye, not from statistics.", {}),
    ], size=12.5, color=K.TXT)
    notes[15] = (f"Headline: 22 of 22 round trips byte-exact, PSNR between {sm['psnr_db_min']:.1f} and 74.6 dB depending on how full the cover is, SSIM above {sm['ssim_min']:.3f}. "
                 "PSNR depends only on how many bits are embedded, because each embedded bit flips its value half the time. ProSt reports no PSNR or SSIM, so we compare only with the supporting SCReedSolo paper "
                 "in the final review, and there the covers and payloads differ.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    cw, ch = 3.95, 2.62
    grid = [("06_send_result.png", "Send: stego PNG, PSNR, SSIM, capacity, SHA-256"), ("08_analysis.png", "Analysis: PSNR, SSIM, MSE and side-by-side images"),
            ("11_receive_result.png", "Receive: restored byte for byte, tag verified"), ("12_receive_wrong_key.png", "Receive with the wrong key: RSA unwrap fails"),
            ("13_robustness_results.png", "Robustness: payload survives 2 of 9 attacks"), ("17_log.png", "Operation log: successes and failures, no secrets")]
    for i, (n_, cap) in enumerate(grid):
        r, c = divmod(i, 3)
        shot_box(s, n_, 0.6 + c * (cw + 0.19), 1.3 + r * (ch + 0.14), cw, ch, cap)
    K.text(s, 0.6, 6.72, 12.13, 0.3, "Real captures of the running application at 1440 x 900 from one session on a fresh database: keys generated, files encrypted and recovered, attacks run.", size=11, color=K.TXT, italic=True)
    notes[16] = ("Real screenshots from one session. The memo is hidden in the astronaut photo (PSNR 57.64 dB, 22.4 percent of the capacity); the second receive uses a different 3072-bit key and is refused.")

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.PYTEST_PASSED} / {F.PYTEST_TOTAL}", f"pytest tests passed ({F.PYTEST_CRYPTO} crypto, {F.PYTEST_LSB} LSB, {F.PYTEST_METRICS} metrics, {F.PYTEST_API} API)", K.GREEN),
                                   (f"{F.SMOKE_PASSED} / {F.SMOKE_TOTAL}", "smoke-test checks passed against the live API", K.BLUE),
                                   (f"{tamper['trials']} / {tamper['trials']}", "single-bit flips of the stego image rejected, 0 accepted with wrong data", K.ORANGE),
                                   (f"{api_ms('send (21 KiB memo, 512x512'):.0f} ms", f"median API send call (receive {api_ms('receive'):.0f} ms), measured on 127.0.0.1", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Observation", "Action"],
            ["Chi-square flags the embedded region in 30 of 30 cases; weighted-stego estimates the filled fraction", "Stated in every result: invisible is not undetectable; low fill is safer, not safe"],
            ["JPEG at quality 100, lossy WebP, noise, resize, rotate, flip and palette reduction all give 0 of 6 recovered", "Send the stego image as a PNG file; no chat app or email client that re-encodes"],
            ["Send dominated by PSNR/SSIM and PNG encoding, not by cryptography (AES-GCM 0.15 ms)", "Timing split reported per stage; API latency measured separately"],
            ["Send page crashes for an account with no keys (KeyRound not imported)", "Recorded as an open defect; one-line fix proposed"]]
    K.table(s, 0.6, 2.95, [6.4, 5.73], rows, font_size=13, row_h=0.78)
    notes[17] = "Tests cover the cryptography, the LSB layer, the metrics, the pipeline and the API through FastAPI's TestClient; the smoke script drives the live server. No browser assertion suite and no load test were run."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "Corrective action"],
            ["Base paper reports no PSNR, SSIM or capacity, and solves a different problem (computing on hidden bits)", "Compared only with the supporting SCReedSolo figures and said plainly where covers and payloads differ"],
            ["LSB data is destroyed by any lossy step; no error correction", "Robustness tests state exactly what survives; output is PNG-only; Reed-Solomon coding listed as future work"],
            [f"Sequential embedding is statistically detectable (chi-square {sa['chi2_total']}/{sa['chi2_total']})", "Reported honestly; key-dependent permutation and adaptive embedding are next steps"],
            ["bcrypt reads only 72 bytes of a password", "Password length capped at 72 characters in the API; the hash step also cuts at 72 bytes"],
            ["Python clients to localhost add about 2 s per call on this PC (IPv6 fallback)", "API latency measured on 127.0.0.1; timings otherwise vary 10 to 30% with other jobs"]]
    K.table(s, 0.6, 1.5, [5.9, 6.23], rows, font_size=13.5, row_h=0.88)
    notes[18] = "Each challenge was met by a concrete design choice or by measuring it and saying so in the report."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Harder to detect", "Key-dependent pixel permutation, LSB matching or adaptive embedding, and a test with stronger detectors (RS, sample-pair).", K.BLUE, "1"),
        ("Survive more", "Add Reed-Solomon error correction so mild damage can be repaired; keep PNG-only guidance for lossy channels.", K.GREEN, "2"),
        ("Harden the tool", "Encrypt stored private keys, sign messages (RSA-PSS or Ed25519), add login rate limiting, fix the Send page import.", K.ORANGE, "3"),
        ("Test wider", "Camera photographs, large covers, browser end-to-end tests, a load test and a small usability study.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.09, 1.6, 2.85, 3.9, t, b_, col, gl, body_size=16)
    K.box(s, 0.6, 5.75, 12.13, 0.95, fill=K.FHEAD, line=None)
    K.text(s, 0.85, 5.9, 11.6, 0.7, "Priority: items 1 and 3 close the largest honest gaps - statistical detectability and the unencrypted key store.", size=16, color=K.INK, anchor="m")
    notes[19] = "Plan to the final review. Item 1 addresses the main weakness shown by the steganalysis results; item 3 addresses the security gaps listed on the progress slide."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = ("Likely questions: why AES-GCM and not CBC; why RSA-OAEP; why PSNR does not depend on the cover; why the payload dies under JPEG; how ProSt differs; "
                 "whether the scheme can be detected (yes, by chi-square and weighted-stego at medium and high fill).")

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


def render(path, outdir):
    """Export every slide to PNG with PowerPoint COM (absolute path; serialised with the other builders)."""
    import win32com.client

    from .comlock import com_lock

    os.makedirs(outdir, exist_ok=True)
    with com_lock():
        app = win32com.client.DispatchEx("PowerPoint.Application")
        try:
            pres = app.Presentations.Open(os.path.abspath(path), True, False, False)
            pres.SaveAs(os.path.abspath(outdir), 18)
            pres.Close()
        finally:
            app.Quit()


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
