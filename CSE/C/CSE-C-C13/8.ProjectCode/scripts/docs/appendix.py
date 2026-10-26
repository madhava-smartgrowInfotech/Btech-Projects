"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""
import ast
import os
import re
import textwrap

from . import facts as F
from .blocks import B, CODE as _CODE, FIG, H1, H2, N, P, PAIR, TAB


# ---------------------------------------------------------------------------- helpers (self-contained: cut from the real source files)
def _read(rel):
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        return f.read()


def fn(rel, name, doc=False):
    """Source of a Python function, a class ('Class') or a method ('Class.method') exactly as it stands
    (docstrings removed unless doc=True), dedented."""
    text = _read(rel)
    lines = text.split("\n")
    tree = ast.parse(text)
    kinds = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    scope = tree.body
    node = None
    for part in name.split("."):
        node = next(n for n in scope if isinstance(n, kinds) and n.name == part)
        scope = node.body
    start = min([d.lineno for d in node.decorator_list] + [node.lineno])
    body = lines[start - 1:node.end_lineno]
    if not doc and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and ast.get_docstring(node):
        d = node.body[0]
        body = lines[start - 1:d.lineno - 1] + lines[d.end_lineno:node.end_lineno]
    return textwrap.dedent("\n".join(body))


def js(rel, header):
    """A JavaScript declaration starting with `header` (a line prefix), with the comment lines directly above it.
    A declaration that opens a block ends at the next line that is just '}'; any other ends before the next blank line."""
    lines = _read(rel).split("\n")
    i = next(k for k, l in enumerate(lines) if l.startswith(header))
    s = i
    while s > 0 and lines[s - 1].lstrip().startswith(("//", "/*", "*")):
        s -= 1
    if lines[i].rstrip().endswith("{"):
        j = next(k for k in range(i, len(lines)) if lines[k] == "}")
    else:
        j = next((k for k in range(i, len(lines)) if not lines[k].strip()), len(lines)) - 1
    return "\n".join(lines[s:j + 1])


def _join(*parts):
    return "\n\n".join(parts)


def _wrap(code, size):
    """Soft-wrap lines that are wider than the page at this font size (continuation lines get four extra spaces)."""
    width = int(790 / size)
    out = []
    for line in code.split(chr(10)):
        if len(line) <= width:
            out.append(line)
            continue
        indent = line[:len(line) - len(line.lstrip())]
        out.extend(textwrap.wrap(line, width, subsequent_indent=indent + "    ", break_long_words=False, break_on_hyphens=False, replace_whitespace=False, drop_whitespace=True) or [line])
    return chr(10).join(out)


def CODE(text, size=8.5):
    return _CODE(_wrap(text, size), size)


# ------------------------------------------------------------------------------ Appendix A
def _intro():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings are cut mechanically from the source files of `8.ProjectCode` as they stood when the measurements were made (Python functions through the `ast` module, JavaScript by declaration), "
          "with Python docstrings removed to save space and over-long lines wrapped to the page width; nothing is retyped. The cryptographic design is explained in Chapter 6, the access rules in Chapter 5 and the audit chain in Chapters 6 and 8."),
    ]


VC = "frontend/src/lib/vaultCrypto.js"
VT = "frontend/src/lib/vault.js"
FILES = "backend/app/api/files.py"
SHARING = "backend/app/api/sharing.py"
PERM = "backend/app/services/permission_service.py"
AUDIT = "backend/app/services/audit_service.py"
SEC = "backend/app/core/security.py"
DEPS = "backend/app/api/deps.py"


def _common():
    return _intro() + [
        H2("A.1 Key derivation and private-key protection (`vaultCrypto.js`)"),
        P("The password never leaves the browser. A 16-byte random salt and PBKDF2-HMAC-SHA-256 with 120,000 iterations give an AES-256-GCM key-encryption key, which seals the exported PKCS#8 private key."),
        CODE(_join(js(VC, "export async function deriveKeyFromPassword"), js(VC, "export async function protectPrivateKey"), js(VC, "export async function restorePrivateKey"),
                   js(VC, "export async function createAccountKeys")), 7.0),
        H2("A.2 File encryption, key wrapping and integrity (`vaultCrypto.js`)"),
        P("A new 256-bit file key and a 12-byte random IV are used for every encryption. The file key is wrapped with the RSA-2048-OAEP (SHA-256) public key of a recipient and unwrapped with the matching private key. "
          "The SHA-256 digest is taken over the plaintext."),
        CODE(_join(js(VC, "export const generateFileEncryptionKey"), js(VC, "export async function encryptFile"), js(VC, "export const decryptFile"), js(VC, "export async function wrapFileKey"),
                   js(VC, "export const unwrapFileKey"), js(VC, "export async function calculateSHA256"), js(VC, "export async function verifySHA256")), 7.0),
        H2("A.3 Upload, download and share flows in the browser (`vault.js`)"),
        CODE(_join(js(VT, "export async function uploadFile"), js(VT, "export async function fetchAndDecrypt"), js(VT, "export async function shareWith")), 7.0),
        H2("A.4 The upload route (`files.py`)"),
        P("The route validates the ciphertext size, the 12-byte IV, the base64 wrapped key and the 64-hex SHA-256, stores the ciphertext under a random 32-hex name, writes the metadata row and appends an audit event. It never sees plaintext."),
        CODE(fn(FILES, "upload"), 6.6),
        H2("A.5 The download route (`files.py`)"),
        CODE(fn(FILES, "download"), 6.8),
        H2("A.6 Role rules (`permission_service.py`)"),
        CODE(_join(fn(PERM, "get_effective_role"), fn(PERM, "can_read"), fn(PERM, "can_write"), fn(PERM, "can_delete"), fn(PERM, "can_share")), 7.2),
        H2("A.7 The share route (`sharing.py`)"),
        CODE(fn(SHARING, "share_file"), 6.8),
        H2("A.8 Hash-chained audit log (`audit_service.py`)"),
        P("Each entry stores the hash of its predecessor and the SHA-256 of a string that joins the previous hash, the timestamp, user, file, action, outcome and details; `verify_chain` recomputes the chain from the first entry."),
        CODE(_join(fn(AUDIT, "_hash_event"), fn(AUDIT, "record_event"), fn(AUDIT, "verify_chain")), 6.8),
        H2("A.9 Passwords, tokens and login throttling (`security.py`, `deps.py`)"),
        CODE(_join(fn(SEC, "hash_password"), fn(SEC, "verify_password"), fn(SEC, "create_access_token"), fn(SEC, "decode_access_token"), fn(DEPS, "check_rate_limit")), 7.0),
    ]


def _report():
    return _intro() + [
        H2("A.1 Key derivation and private-key protection (`vaultCrypto.js`)"),
        CODE(_join(js(VC, "export async function deriveKeyFromPassword"), js(VC, "export async function protectPrivateKey")), 6.8),
        H2("A.2 File encryption, key wrapping and integrity (`vaultCrypto.js`)"),
        CODE(_join(js(VC, "export async function encryptFile"), js(VC, "export async function wrapFileKey"), js(VC, "export const unwrapFileKey"), js(VC, "export async function verifySHA256")), 6.8),
        H2("A.3 Upload and download flows in the browser (`vault.js`)"),
        CODE(_join(js(VT, "export async function uploadFile"), js(VT, "export async function fetchAndDecrypt")), 6.8),
        H2("A.4 The upload route (`files.py`)"),
        CODE(fn(FILES, "upload"), 6.4),
        H2("A.5 Role rules (`permission_service.py`)"),
        CODE(_join(fn(PERM, "get_effective_role"), fn(PERM, "can_read"), fn(PERM, "can_write"), fn(PERM, "can_delete"), fn(PERM, "can_share")), 6.8),
        H2("A.6 Hash-chained audit log (`audit_service.py`)"),
        CODE(_join(fn(AUDIT, "_hash_event"), fn(AUDIT, "record_event"), fn(AUDIT, "verify_chain")), 6.4),
        H2("A.7 Password hashing and tokens (`security.py`)"),
        CODE(_join(fn(SEC, "hash_password"), fn(SEC, "verify_password"), fn(SEC, "create_access_token"), fn(SEC, "decode_access_token")), 6.8),
    ]


def code_blocks():
    return _report() if F.REPORT else _common()


# ------------------------------------------------------------------------------ Appendix B
def guide_blocks():
    n_req = len([l for l in _read("requirements.txt").split("\n") if l.strip() and not l.startswith("#")])
    out = [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        TAB("Requirements", ["Item", "Needed"],
            [["Operating system", "Windows 10/11 for `run.bat` (the measurements were made on Windows 11); the manual commands also work on Linux and macOS"],
             ["Python", f"3.11 or newer on PATH (measured with {F.ENV['python']})"],
             ["Node.js and npm", "Node 20 or newer (React 19 and Vite 8; Node 24 was installed on the measurement machine; the Docker image builds the interface with Node 22)"],
             ["Python packages", f"`requirements.txt`, {n_req} packages with minimum versions: FastAPI, Uvicorn, SQLAlchemy, psycopg, Alembic, Pydantic, pydantic-settings, email-validator, PyJWT, bcrypt, python-multipart, "
                                 "cryptography, python-dotenv, pytest, httpx and fpdf2"],
             ["Browser", "A current Chrome, Edge or Firefox over `http://localhost` (Web Crypto needs a secure context; localhost qualifies). Measurements and screenshots used Chrome 155; Firefox and Safari were not tested"],
             ["Docker (optional)", "Docker Desktop for the PostgreSQL-backed deployment; it was not built or run during this project's documentation work"],
             ["Disk", "About 500 MB free for the packages, the database and the encrypted files"]],
            widths=[1.5, 5.1], align=["l", "l"], size=10),
        H2("B.2 One-click start with run.bat"),
        N("Open the `8.ProjectCode` folder and double-click `run.bat`.",
          "The script checks that Python and Node are on PATH, creates `.venv` if it is missing, installs `requirements.txt`, runs `npm install` in `frontend` on the first run and copies `.env.example` to `.env` if there is no `.env`.",
          f"It starts the API on port {F.API_PORT} (`uvicorn backend.app.main:app`) in one window and the Vite web app on port {F.WEB_PORT} in another, then opens `http://localhost:{F.WEB_PORT}/`. Keep both windows open.",
          "On the sign-in page choose Try the demo (Owner, Editor or Viewer), or open Register and create an account. Interactive API documentation is at `http://localhost:8413/docs`.",
          "To stop the application, close the two windows."),
        H2("B.3 Manual start"),
        CODE("# from 8.ProjectCode\npython -m venv .venv\n.venv\\Scripts\\activate            # Linux/macOS: source .venv/bin/activate\npip install -r requirements.txt\ncopy .env.example .env           # Linux/macOS: cp .env.example .env\n"
             "uvicorn backend.app.main:app --host 127.0.0.1 --port 8413\n\n"
             "# second terminal, from 8.ProjectCode/frontend\nnpm install\nnpm run dev                       # http://localhost:5413\n\n"
             "# single-server alternative: build once, then the API serves the app on port 8413\nnpm run build", 8.2),
        P("Tables are created automatically at start-up (`init_db()`), so there is no migration step. With the default `DATABASE_URL` the metadata is kept in the SQLite file `ciphervault.db` and the ciphertext in `storage/encrypted/`."),
        H2("B.4 Docker (PostgreSQL)"),
        CODE("docker compose build\ndocker compose up          # then open http://localhost:8413\n", 8.5),
        P("`docker-compose.yml` starts a `postgres:16-alpine` database and the application image (a Node 22 stage builds the interface, a Python 3.11 stage runs the API and serves it), publishes port 8413 on `127.0.0.1` only and mounts "
          "`./storage/encrypted`. `run-docker.bat` wraps the same two commands. This path was not built or run for this report (Chapter 7)."),
        H2("B.5 Configuration (`.env`)"),
        TAB("Settings read from .env (defaults in .env.example)", ["Key", "Default", "Meaning"],
            [["APP_PORT, FRONTEND_PORT", "8413, 5413", "API port; web port (the Vite server proxies /api to APP_PORT)"],
             ["DATABASE_URL", "sqlite:///./ciphervault.db", "SQLite file, or a PostgreSQL URL such as postgresql+psycopg://user:password@host:5432/ciphervault"],
             ["JWT_SECRET, JWT_ALGORITHM", "placeholder, HS256", "Signing secret and algorithm of the access tokens; set a long random secret outside local use"],
             ["ACCESS_TOKEN_EXPIRE_MINUTES", "120", "Lifetime of a token"],
             ["STORAGE_DIR", "storage/encrypted", "Directory of the ciphertext files"],
             ["MAX_UPLOAD_MB", "25", "Largest accepted file; larger uploads get HTTP 413"],
             ["LOGIN_MAX_ATTEMPTS, LOGIN_WINDOW_SECONDS", "20, 300", "In-memory login throttle per IP address and e-mail (not in .env.example, settable in .env)"]],
            widths=[2.1, 1.6, 2.9], align=["l", "l", "l"], size=9.5),
        H2("B.6 Using the application"),
        TAB("Demo accounts (fictional, local only)", ["Role", "E-mail", "Password"],
            [["Owner (Olivia Owner)", "owner@example.com", "Demo-Owner-123"], ["Editor (Eddie Editor)", "editor@example.com", "Demo-Editor-123"], ["Viewer (Vera Viewer)", "viewer@example.com", "Demo-Viewer-123"]],
            widths=[2.2, 2.4, 2.0], align=["l", "l", "l"], size=10),
        P("The first click on Try the demo creates the three accounts (the browser generates a real RSA-2048 key pair for each) and fills the owner's vault with five synthetic files, shares two of them, performs an editor update and a denied delete, "
          "so the audit log shows real events. The same accounts can be created from a terminal with `python scripts/seed_demo.py --url http://localhost:8413`."),
        TAB("Pages and what to do on them", ["Page", "What to do", "Result"],
            [["Landing", "Read the summary; choose Create your vault, Try the demo or Sign in", "Public page with the key parameters of the build"],
             ["Sign in / Register", "Register with name, e-mail and a password of at least 8 characters; the key pair is generated in the browser. Sign in with the same password", "Vault unlocked in this tab"],
             ["Dashboard", "Read the counters, the 14-day event chart, the access-by-role chart and recent activity; Upload a file", "Overview of the vault"],
             ["My files", "Drop or choose files (up to 25 MB); search, filter and open a file", "Each file is encrypted before upload; the list shows size and role"],
             ["File details", "Decrypt and download, Share (recipient e-mail and role), change a role, revoke, Replace content, Delete (owner)", "Access list, SHA-256, IV and the owner-only file history"],
             ["Shared with me", "Open or download files other users shared", "Files with your role (Viewer or Editor)"],
             ["Audit log", "Filter events; press Verify audit chain", "Valid or failed result with the number of entries checked"],
             ["Security", "Read the key status; Lock vault now; Sign out", "Private key cleared from memory when locked"]],
            widths=[1.3, 3.3, 2.0], align=["l", "l", "l"], size=9.5),
        P("Reloading the page locks the vault: the decrypted private key lives only in memory, so the password is asked again. If the password is forgotten the files cannot be recovered; there is no recovery key."),
        H2("B.7 API quick reference"),
        CODE("# sign in and keep the token\ncurl -s -X POST http://127.0.0.1:8413/api/auth/login -H \"Content-Type: application/json\" -d '{\"email\":\"owner@example.com\",\"password\":\"Demo-Owner-123\"}'\n\n"
             "curl http://127.0.0.1:8413/api/health\ncurl http://127.0.0.1:8413/api/config\n"
             "curl -H \"Authorization: Bearer <token>\" http://127.0.0.1:8413/api/files\n"
             "curl -H \"Authorization: Bearer <token>\" http://127.0.0.1:8413/api/files/shared\n"
             "curl -H \"Authorization: Bearer <token>\" -o cipher.bin http://127.0.0.1:8413/api/files/1/download\n"
             "curl -H \"Authorization: Bearer <token>\" http://127.0.0.1:8413/api/audit/verify", 7.6),
        P("A download returns ciphertext with the headers `X-CipherVault-IV`, `X-CipherVault-Wrapped-FEK`, `X-CipherVault-SHA256`, `X-CipherVault-Filename` and `X-CipherVault-MIME`; the file can be opened only in the browser, with the owner's, editor's or viewer's private key."),
        H2("B.8 Tests, measurements and screenshots"),
        CODE("pytest -q                              # 21 backend tests, about 13 s\n"
             "python scripts/e2e_check.py --url http://localhost:8413   # API end-to-end checks against a running server\n"
             "python scripts/smoke_test.py           # API end-to-end + a real-browser walk of every screen (needs Playwright)\n"
             "python scripts/evaluate.py             # 17 checks, writes evaluation_results.txt/json\n"
             "python scripts/measure_metrics.py      # browser and API timings, RBAC matrix, tamper studies -> docs/metrics\n"
             "python scripts/capture_screens.py      # 1440 x 900 screenshots -> docs/screenshots\n"
             "python -m scripts.docs.make_report_facts   # docs/REPORT_FACTS.md", 8.0),
        H2("B.9 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Cause and remedy"],
            [["Python or Node not found", "Install Python 3.11+ (tick Add python.exe to PATH) and Node.js LTS, reopen the terminal and run `run.bat` again"],
             ["Port 8413 or 5413 already in use", "Close the other program, or change APP_PORT or FRONTEND_PORT in `.env` and restart"],
             ["Vault locked after a refresh", "By design: the private key is held in memory only. Enter the password in the unlock dialog"],
             ["Decryption failed or Integrity check failed", "AES-GCM authentication or the SHA-256 comparison failed: the ciphertext or the wrapped key does not match. The file is not saved; upload and share it again"],
             ["Registration rejects an e-mail address", "The server validates addresses with `email-validator`, which refuses reserved domains such as `.local` and `.test`; use a normal domain such as example.com"],
             ["Upload refused", "The file is over 25 MB (HTTP 413) or empty; the limit is MAX_UPLOAD_MB"],
             ["Cannot reach the server", "The backend window must be running on port 8413"],
             ["SQLite file corrupt", "Stop the server, delete `ciphervault.db` and restart; local data is reset"],
             ["Windows SmartScreen blocks run.bat", "Choose More info, then Run anyway; the script is plain text and can be inspected first"]],
            widths=[2.3, 4.3], align=["l", "l"], size=9.5),
    ]
    return _guide_trim(out) if F.REPORT else out


def _guide_trim(out):
    """Compact variant for the full report: shorter requirements, no Docker listing, no API quick reference, short troubleshooting."""
    res, skip = [], False
    for b in out:
        if b[0] == "h2":
            skip = b[1].startswith(("B.1", "B.4", "B.7", "B.8"))
            if b[1].startswith("B.1"):
                res.append(("h2", "B.1 Requirements"))
                res.append(("p", f"Python 3.11 or newer ({F.ENV['python']} was used), Node.js 20 or newer, the packages in `requirements.txt`, and a current Chrome, Edge or Firefox over `http://localhost` "
                                 "(Web Crypto needs a secure context). About 500 MB of disk is enough. Docker Desktop is needed only for the PostgreSQL deployment, which was not built or run for this report."))
            if b[1].startswith("B.8"):
                res.append(("h2", "B.7 Tests and measurements"))
                res.append(("code", "pytest -q\npython scripts/smoke_test.py\npython scripts/measure_metrics.py\npython scripts/capture_screens.py", 8.0))
        if skip:
            continue
        if b[0] == "h2" and b[1].startswith("B.5"):
            res.append(b)
            continue
        if b[0] == "h2" and b[1].startswith("B.6"):
            res.append(("h2", "B.5 Using the application"))
            continue
        if b[0] == "h2" and b[1].startswith("B.9"):
            res.append(("h2", "B.8 Troubleshooting"))
            continue
        if b[0] == "tab" and b[1].startswith("Pages and what to do"):
            b = ("tab", b[1], ["Page", "What to do"], [[r[0], r[1]] for r in b[3]], [1.3, 5.3], ["l", "l"], 9.0)
        if b[0] == "tab" and b[1].startswith("Common problems"):
            keep = ("Port 8413", "Vault locked", "Decryption failed", "Registration rejects")
            b = ("tab", b[1], b[2], [r for r in b[3] if r[0].startswith(keep)]) + tuple(b[4:])
        if b[0] == "tab" and b[1].startswith("Settings read from .env"):
            b = ("tab", b[1], b[2], b[3][:6]) + tuple(b[4:])
        res.append(b)
    return res


# ------------------------------------------------------------------------------ Appendix C
def screens_blocks():
    SH = F.shot
    names = ["01_landing-light.png", "01_landing-dark.png", "02_landing-how-it-works-dark.png", "03_landing-features-dark.png", "04_sign-in.png", "05_register.png",
             "13_shared-with-me.png", "14_dashboard-light.png", "15_mobile-dashboard-360.png", "16_mobile-nav-drawer-360.png"]
    missing = [s for s in names if not os.path.exists(SH(s))]
    assert not missing, missing
    out = [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("These captures complement Chapter 8, which shows the dashboard, file list, file details, sharing dialog, audit log, security page and unlock dialog. Here are the public pages, the sign-in and registration screens, "
          "the view of a Viewer, the light theme and the 360-pixel mobile layout. All were taken from the running application with Playwright (Chrome) at 1440 x 900 pixels, or 360 x 740 for the mobile views, "
          "with the fictional demo accounts; nothing is mocked."),
        PAIR([(SH("01_landing-light.png"), "Additional screen: landing page in the light theme."),
              (SH("01_landing-dark.png"), "Additional screen: landing page in the dark theme, with the status badge reading API online.")], 2.95),
        P("The landing page is public. Its headline states the design (files are sealed before they leave the browser), the badges say that the server stores ciphertext only and that keys never leave the device, "
          "and the status badge is filled by a live call to the health endpoint. The rotating wireframe is a three.js scene that is replaced by a static fallback when the user prefers reduced motion or the browser has no WebGL."),
        PAIR([(SH("02_landing-how-it-works-dark.png"), "Additional screen: the How it works section, showing the live pipeline panel."),
              (SH("03_landing-features-dark.png"), "Additional screen: feature cards and the key parameters of the build.")], 2.95),
        P("The pipeline panel names, step by step, what runs in the browser (encrypt and hash, wrap the key), what the server stores (ciphertext) and what the recipient's browser does (unwrap, decrypt, verify). "
          "The strip of parameters (256-bit key, 2,048-bit RSA, 120,000 PBKDF2 iterations, 12-byte IV, 25 MB limit) restates the configuration actually used by this build, and the last card says in plain words that a forgotten password cannot be recovered."),
        PAIR([(SH("04_sign-in.png"), "Additional screen: sign-in with the Try the demo box."),
              (SH("05_register.png"), "Additional screen: registration; the browser generates the RSA-2048 key pair when Create account is pressed.")], 2.95),
        P("The two forms share one panel. The demo box lists the three fictional accounts and signs in with one click; registration asks for a name, an e-mail address and a password of at least eight characters that cannot be recovered, "
          "because the key that protects the private key is derived from it."),
        FIG(SH("13_shared-with-me.png"), "Additional screen: Shared with me, as seen by the demo Viewer, with the role badge of each file.", F.shot_w(SH("13_shared-with-me.png"), 5.4, 3.7)),
        P("The Viewer sees the two files that the owner shared as Viewer, with the owner's address and the time of the last update. Only download and open actions are offered; the delete, share and replace buttons of the owner's file page "
          "are absent, and the server would refuse them anyway (Chapter 8)."),
        FIG(SH("14_dashboard-light.png"), "Additional screen: the dashboard of the demo owner in the light theme.", F.shot_w(SH("14_dashboard-light.png"), 5.4, 3.7)),
        P("The counters show five files owned and none shared with the owner. The event chart plots vault-wide audit events per day for the last 14 days; the chart shows events on a single day, 22 October 2026, "
          "because the demonstration data and the test runs that preceded the capture were all created that day, so it rises as one spike and says nothing about normal usage."),
        PAIR([(SH("15_mobile-dashboard-360.png"), "Additional screen: dashboard at a width of 360 pixels."),
              (SH("16_mobile-nav-drawer-360.png"), "Additional screen: navigation drawer at a width of 360 pixels.")], 2.0),
        P("At 360 pixels the counters stack in two columns and the sidebar becomes a drawer opened from the menu button; the smoke test checks that no page overflows horizontally at 360 and 768 pixels. "
          "The toast in both captures is the notice shown after the one-click demo sign-in."),
    ]
    return _screens_trim(out) if F.REPORT else out


def _screens_trim(out):
    """Compact variant for the full report: shorter explanations, the how-it-works and features pair and the light dashboard dropped."""
    res, drop_next = [], 0
    for b in out:
        if b[0] == "pair" and "02_landing-how-it-works" in b[1][0][0]:
            drop_next = 1          # the pair and its paragraph
            continue
        if b[0] == "fig" and "14_dashboard-light" in b[1]:
            drop_next = 1
            continue
        if drop_next and b[0] == "p":
            drop_next = 0
            continue
        if b[0] == "p" and b[1].startswith("The landing page is public"):
            b = ("p", "The landing page is public. The status badge is filled by a live call to the health endpoint, and the rotating wireframe is a three.js scene replaced by a static fallback for users who prefer reduced motion or lack WebGL.")
        if b[0] == "p" and b[1].startswith("The two forms share"):
            b = ("p", "The demo box signs in with one click; registration needs a password of at least eight characters that cannot be recovered, because the key that protects the private key is derived from it.")
        if b[0] == "p" and b[1].startswith("The Viewer sees"):
            b = ("p", "The Viewer sees the two files shared as Viewer; the delete, share and replace buttons are absent, and the server would refuse them anyway (Chapter 8).")
        res.append(b)
    return res
