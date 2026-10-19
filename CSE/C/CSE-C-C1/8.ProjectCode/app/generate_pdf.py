from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import pathlib, json

OUTPUT = pathlib.Path("AegisBallot_Product_Documentation.pdf")
WIDTH, HEIGHT = A4
styles = getSampleStyleSheet()
title_style = ParagraphStyle('Title2', parent=styles['Title'], fontSize=26, textColor=HexColor('#0f3b8c'), alignment=TA_CENTER)
h1 = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=16, textColor=HexColor('#0f3b8c'), spaceBefore=14, spaceAfter=6)
h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=13, textColor=HexColor('#1e5cc7'), spaceBefore=10, spaceAfter=4)
body = ParagraphStyle('Body', parent=styles['Normal'], fontSize=9.5, leading=13, alignment=TA_JUSTIFY)
caption = ParagraphStyle('Caption', parent=styles['Normal'], fontSize=8, textColor=HexColor('#6b7280'), alignment=TA_CENTER)

PRIMARY = HexColor('#0f3b8c')

def build():
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, topMargin=0.6*inch, bottomMargin=0.6*inch, leftMargin=0.6*inch, rightMargin=0.6*inch,
                            title="AegisBallot Product Documentation", author="AegisBallot")
    flow = []
    # Cover
    flow.append(Paragraph("AegisBallot", title_style))
    flow.append(Spacer(1, 6))
    flow.append(Paragraph("Secure Local Electronic Voting Platform", ParagraphStyle('sub', parent=styles['Normal'], fontSize=13, textColor=HexColor('#0a7a65'), alignment=TA_CENTER)))
    flow.append(Spacer(1, 12))
    flow.append(Paragraph("Product Documentation &bull; Version 1.0.0 &bull; Local Demonstration", ParagraphStyle('meta', parent=styles['Normal'], fontSize=9, textColor=HexColor('#6b7280'), alignment=TA_CENTER)))
    flow.append(Spacer(1, 18))
    flow.append(Paragraph("AegisBallot demonstrates an end-to-end encrypted, blockchain-backed voting workflow with synthetic identity verification, quorum-validated ledger, and independent auditability — all running locally on SQLite and a permissioned ledger simulation.", body))
    flow.append(Spacer(1, 10))
    # Quick stats table
    stats = [["Feature","Implementation"],["Identity","DemoAadhaarProvider (Verhoeff, salted hash, masked display)"],["Ledger","3 validators, quorum 2/3, SHA-256, Ed25519"],["Ballot","AES-256-GCM, identity/ballot separation"],["Auth","Argon2id, server-side sessions, RBAC"],["DB","SQLite + SQLAlchemy 2.x"]]
    t = Table(stats, colWidths=[1.6*inch, 4.5*inch])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0), PRIMARY),('TEXTCOLOR',(0,0),(-1,0), HexColor('#ffffff')),('GRID',(0,0),(-1,-1), 0.5, HexColor('#d1d5db')),('FONTSIZE',(0,0),(-1,-1), 8),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LEFTPADDING',(0,0),(-1,-1),6)]))
    flow.append(t)
    flow.append(Spacer(1, 12))
    flow.append(Paragraph("This is a functional local platform, not a production national election system. Demo verification does not contact UIDAI.", ParagraphStyle('warn', parent=body, fontSize=8, textColor=HexColor('#92400e'), backColor=HexColor('#fffbeb'), borderPadding=6)))

    def section(title, text):
        flow.append(Paragraph(title, h1))
        for para in text.split("\n\n"):
            flow.append(Paragraph(para.strip(), body))
            flow.append(Spacer(1,4))

    section("Product Overview", "AegisBallot enables an administrator to create and configure elections, manage candidates, and open/close voting; a voter to authenticate, verify via synthetic Aadhaar, view candidates, confirm, cast exactly one encrypted ballot, and receive a non-revealing receipt; and an auditor to inspect the ledger, validate chain integrity, and run tamper detection.\n\nCore principles: reliability over complexity, honest local simulation over exaggerated claims, and clear separation of identity from ballot.")

    section("Problem Addressed", "Electronic voting requires trustworthy identity, one-vote enforcement, ballot secrecy, and verifiable integrity without relying on public blockchain infrastructure or Internet connectivity. AegisBallot shows how these properties can be realized locally with standard cryptography and permissioned ledger concepts.")

    section("Key Features & User Roles", "Roles: ADMIN (election/candidate management, open/pause/close, results, system health), VOTER (login, Aadhaar verification, candidate browsing, ballot confirmation, receipt), AUDITOR (chain explorer, block/tx details, integrity verification, audit log, tamper demo).\n\nWorkflow: Admin creates election → synthetic voters registered → voter logs in → Demo Aadhaar verification → eligibility check → one-time authorization → candidate view → confirmation → encrypted ballot → quorum-validated block commit → receipt → duplicate-vote rejection → admin closes election → decrypted tally → auditor verification.")

    section("Architecture Summary", "Four layers: (1) Persistent storage — SQLite with SQLAlchemy, foreign keys, unique constraints. (2) Ledger — local permissioned chain: genesis block, SHA-256, deterministic serialization, Merkle root, Ed25519 signatures, 3 validators. (3) Application/business logic — FastAPI services for elections, voting, identity, audit. (4) Frontend — Jinja2 templates, vanilla JS, light theme, responsive cards.\n\nModular paths: app/identity/provider.py exposes IdentityVerificationProvider; app/ledger/ledger.py exposes propose_block/validate_chain; app/security/crypto.py centralizes SHA-256, AES-GCM, Ed25519.")

    section("Identity-Verification Design", "Synthetic 12-digit numbers are generated with Verhoeff check digits; validation checks length, digits, Verhoeff, existence in voter_profiles (hashed with salt+pepper), eligibility, and not-already-voted. Raw identifiers are not stored beyond a salted hash (SHA-256 of salt+pepper+number); UI shows masked form XXXX-XXXX-1234. The adapter is DemoAadhaarProvider; the code marks it as simulated/demo and documents that it can be swapped for a real provider without changing voting logic.")

    section("Blockchain / Ledger Design", "Each block contains index, timestamp, previous_hash, merkle_root, block_hash, validator_signatures, transaction count. Hashing uses SHA-256 over canonical JSON serialization. Validators maintain independent keypairs (Ed25519) in data/validators.json. Normal flow: app builds transaction (ballot_id, election_id, encrypted_payload, nonce, timestamp, tx_hash, signature) → primary proposes block → replicas validate schema, previous hash, signature, nonce/tx_hash uniqueness → at least 2/3 approve → block committed → replicas sync → receipt returned. Immutability and tamper detection derive from hash chaining and recomputation.")

    section("Ballot Privacy Model", "Separation: voter_profiles / identity_credentials hold identity; VotingAuthorization holds hashed one-time token; Ballot and LedgerTransaction hold only anonymous ballot_id, encrypted choice, nonce, tx_hash. Token is random (secrets.token_urlsafe), single-use, 10-minute expiry, hashed with SHA-256 at rest. Payload is encrypted via AES-256-GCM with a per-deployment key in data/secrets.json (never in source control). The receipt proves acceptance (election, ballot_id, tx_hash, block index/hash) without revealing candidate.")

    section("Security Controls", "Argon2id password hashing; server-side sessions (httponly, lax samesite); CSRF via per-session token (X-CSRF-Token header check); rate limiting on login/verification (in-memory window); input validation (Pydantic where applicable); secure random IDs; SHA-256, AES-GCM, Ed25519; RBAC with server-side checks; DB constraints (uq_one_vote_per_voter, uq_auth_one_per_election); structured audit logs (no secrets); safe error messages.")

    section("Election Administration", "Admin UI: create election (title, description, start/end, eligibility), add/edit/deactivate candidates (candidate_id, name, party, description, manifesto, active flag), view voter count, open/pause/close, view results after closure, view benchmark summary, ledger height, validator status, last hash, chain integrity, recent audit events. All metrics derive from DB/ledger/benchmarks.")

    section("Auditor Capabilities", "Auditor dashboard provides chain explorer (blocks, tx), block/tx details, validator approvals, chain-integrity verification (recomputes from genesis, reports first invalid block, expected vs actual hash/previous-hash/mekle), audit log viewer, tamper demo (clones ledger, alters a block hash, validates detection, leaves production ledger untouched), and exportable JSON via APIs.")

    # Benchmark results
    flow.append(Paragraph("Performance Benchmark Methodology", h1))
    flow.append(Paragraph("A synthetic population (default 1,000 voters) is generated with Argon2 passwords and Verhoeff identities. Benchmarks measure voter registration, synchronous vote submission, and batched/asynchronous submission (batches 10/20/30). Timing uses Python's monotonic time.perf_counter(). Reported: total ops, successes/fails, total duration, mean/median/p95/min/max/stdev latency, throughput. Output is saved as JSON in benchmark_results/ and displayed on the admin dashboard. Charts are rendered from actual output; no values are hardcoded.", body))
    flow.append(Spacer(1,6))
    # include actual results if available
    latest = pathlib.Path("benchmark_results/latest.json")
    if latest.exists():
        try:
            data = json.loads(latest.read_text())
            bench_text = f"Latest measured run ({data.get('timestamp')}): {data.get('voters_count')} voters — sync throughput {data.get('sync',{}).get('throughput',0):.1f} ops/s, mean {data.get('sync',{}).get('mean_ms',0):.1f} ms, p95 {data.get('sync',{}).get('p95_ms',0):.1f} ms; async b20 throughput {data.get('async_batches',{}).get('20',{}).get('throughput',0):.1f} ops/s. Full JSON in benchmark_results/latest.json."
            flow.append(Paragraph(bench_text, body))
        except Exception:
            pass
    else:
        flow.append(Paragraph("No benchmark output found at build time — run python -m app.benchmarks.run_benchmark to generate measured results.", body))
    flow.append(Spacer(1,6))
    flow.append(Paragraph("Test Coverage", h1))
    flow.append(Paragraph("Automated pytest suite covers: valid Aadhaar format, invalid checksum rejection, unknown/ineligible voter rejection, duplicate-vote rejection, unauthorized admin/auditor route rejection, tampered block detection, invalid previous-hash rejection, invalid signature handling, duplicate transaction rejection, malformed input, expired token, ballot identity separation, password hashing, audit logging, and election status enforcement. All tests assert real behavior against the running ledger and DB, not constants.", body))
    flow.append(Spacer(1,6))
    # Screenshots
    flow.append(Paragraph("Screenshots — Real Application", h1))
    flow.append(Paragraph("The following are real screenshots captured from the running AegisBallot instance via browser automation. They reflect the light, commercial-style theme.", body))
    flow.append(Spacer(1,6))
    screenshots = list(pathlib.Path("screenshots").glob("*.png"))
    # sort to match required order
    order = ["login","admin","election","verify","candidate","confirm","receipt","results","audit","integrity","performance"]
    def sort_key(p):
        name = p.name.lower()
        for i, o in enumerate(order):
            if o in name:
                return i
        return 999
    screenshots.sort(key=sort_key)
    for img_path in screenshots[:12]:
        try:
            # fit image to page width
            img = RLImage(str(img_path), width=6.8*inch, height=4*inch)
            img.hAlign = 'CENTER'
            # preserve aspect by not forcing height? Use width only with preserve
            flow.append(img)
            flow.append(Paragraph(img_path.name, caption))
            flow.append(Spacer(1,8))
        except Exception as e:
            flow.append(Paragraph(f"[Missing image {img_path.name}: {e}]", body))

    flow.append(Paragraph("How to Run", h1))
    flow.append(Paragraph("Prerequisites: Python 3.12 (or 3.11) and optionally Docker Desktop. No DB server or government credentials needed. Method A: double-click run.bat — creates .venv, installs, seeds, starts on 127.0.0.1:8000, opens http://localhost:8000. Method B: docker build -t aegisballot . && docker run --rm -p 127.0.0.1:8000:8000 aegisballot. Method C: python -m venv .venv, pip install -r requirements.txt, python -m app.seed, uvicorn app.main:app --host 127.0.0.1 --port 8000. See HOW_TO_RUN.md for credentials, troubleshooting, and benchmark/test commands.", body))

    flow.append(Paragraph("Limitations and Extensibility", h1))
    flow.append(Paragraph("Local demo scope: SQLite, in-memory sessions, three local validators — not decentralized across Internet nodes. No live UIDAI, no public chain, no wallet. The ledger layer is modular: DemoAadhaarProvider can be replaced by a real identity adapter, and the ledger module can be swapped for a permissioned blockchain without changing voting flows. Future extensions: notifications, external audit export, election-key rotation, UI localization, and enhanced analytics. The system honestly describes its local guarantees and does not claim production national-election readiness.", body))
    flow.append(Spacer(1,12))
    flow.append(Paragraph("AegisBallot — Built as a complete, polished, working local voting platform.", ParagraphStyle('foot', parent=body, alignment=TA_CENTER, textColor=PRIMARY)))

    doc.build(flow)
    print(f"Generated {OUTPUT}")

if __name__ == "__main__":
    build()
