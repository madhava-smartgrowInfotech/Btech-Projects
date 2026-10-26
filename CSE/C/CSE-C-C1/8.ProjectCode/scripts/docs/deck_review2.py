"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx."""

import os
import re

from pptx import Presentation

from . import facts as F
from . import pptkit as K
from .deck_review1 import agenda, prepare, set_title, thank_you, title_slide, wipe

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"


def crop(name, box, tag):
    """Crop a real screenshot to the part that matters (written to the temp folder, source untouched)."""
    import tempfile
    from PIL import Image
    out = os.path.join(tempfile.gettempdir(), f"c1_deck_{tag}.png")
    with Image.open(F.shot(name)) as im:
        im.crop(box).save(out)
    return out


def n_routes():
    src = open(os.path.join(F.CODE, "app", "api_v1.py"), encoding="utf-8").read()
    return len(re.findall(r'@router\.(?:get|post)\(', src))


def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}
    Bs, Lt, MI = F.BENCH_SYNC, F.LAT, F.MICRO
    NR = n_routes()
    C = [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE]
    idle_lo = min(d["sync"]["mean_ms"] for d in F.IDLE_RUNS)
    idle_hi = max(d["sync"]["mean_ms"] for d in F.IDLE_RUNS)
    lib = F.ENV.get("libs", {})

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: Aadhaar-verified, encrypted, hash-chained voting with an auditor view",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = "This review shows how AegisBallot is designed and built: the data, the cryptography and ledger design, what is implemented, the first measured results and the open items."

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and data"), ("03", "Preprocessing and cryptographic design"), ("04", "System configuration and decision logic"),
               ("05", "Data flow, database and UML"), ("06", "Technology stack"), ("07", "Implementation progress and results"),
               ("08", "Output screens and testing"), ("09", "Challenges and next steps")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Manual polling is slow and error-prone. A database ballot box can be edited without trace, and without identity binding duplicate or ineligible votes cannot be excluded reliably. Observers cannot recompute the result.", K.ORANGE, "!"),
        ("Proposed system", "AegisBallot verifies a 12-digit Aadhaar number, issues a single-use token, encrypts the choice, commits it to a 3-validator hash-chained ledger and lets an auditor recompute the chain.", K.BLUE, "i"),
        ("Base paper link", "Shaikh et al. time a blockchain voting model on an Ethereum test chain with biometric authentication. AegisBallot keeps a registry plus ledger idea but uses an Aadhaar-style check and a local ledger. Results are not directly comparable.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, 4.9, t, b_, col, gl, body_size=18)
    notes[3] = "One-minute recap of Review 1: the integrity and identity problem, our approach, and how the base paper relates (shared goal, different chain, identity method and scope)."

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.5, 1.2, 7.4, 5.75)
    K.text(s, 8.1, 1.5, 4.6, 5.3, [
        ("**Four tiers**", {"space_after": 8}),
        (f"Presentation: React 18 and Vite SPA (port {F.WEB_PORT}); public, voter, admin and auditor pages.", {"bullet": True}),
        (f"Application: FastAPI (port {F.API_PORT}), {NR} JSON routes under /api, session cookie, CSRF header, RBAC, rate limits.", {"bullet": True}),
        ("Services: identity provider, voting service, crypto, audit log and the ledger module.", {"bullet": True}),
        ("Data: SQLite, 13 tables, plus key files in data/. Nothing is sent to an external service.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[4] = "The JSON routes are in app/api_v1.py; the original Jinja pages in app/main.py still work. The services are separate modules so each can be tested alone."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: end-to-end workflow")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.2, [("Sign in", K.NAVY), ("Verify Aadhaar", K.BLUE), ("One-time token", K.BLUE), ("Encrypt + sign", K.ORANGE),
                                      ("Validators sign block", K.PURPLE), ("Receipt", K.GREEN), ("Audit chain", K.NAVY)], size=13, gap=0.22)
    for i, (t, b_) in enumerate([("One vote, four layers", "Eligibility row, UNIQUE participation per (election, voter), single-use token, and a ledger check that nonce and transaction hash are new. Any one of them stops a second ballot."),
                                 ("Identity apart from ballot", "The ballots table has no voter column and the token is stored only as a hash. Honest gap: voter_participation still stores voter id with ballot id, so secrecy is partial."),
                                 ("Measured, not typed", "scripts/run_experiments.py and the product's own benchmark write every reported number to JSON; documents read them from there.")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 3.1, 3.85, 3.6)
        K.text(s, x + 0.25, 3.25, 3.4, 0.5, t, size=19, color=K.INK, bold=True)
        K.text(s, x + 0.25, 3.9, 3.4, 2.7, b_, size=18, color=K.TXT)
    notes[5] = "The three design principles: layered one-vote enforcement, separation of identity from the ballot (with the honest gap stated), and numbers that come from scripts."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Data used: no external dataset")
    wipe(s)
    for i, (v, l, c) in enumerate([("0", "external datasets (no ML model)", K.BLUE), ("20", "seeded demo voters, Verhoeff-valid synthetic Aadhaar", K.GREEN),
                                   (f"{F.N_VOTERS_BENCH:,}", "synthetic voters per benchmark run", K.ORANGE), ("200 / 212", "voters / ballots in the demo database", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Data", "Source", "Size", "Note"],
            ["Voter registry", "app/seed.py, generate_valid_aadhaar()", "20 voters + admin + auditor", "salted SHA-256 hash and masked number stored"],
            ["Elections", "app/seed.py", "2 elections, 4 and 3 candidates", "8 seeded votes in the closed one"],
            ["Benchmark voters", "app.benchmarks.run_benchmark", f"{F.N_VOTERS_BENCH:,} per run", "Argon2id-hashed passwords, generated"],
            ["Demo database", "seed + benchmarks + smoke test", "200 voters, 8 elections, 213 blocks", "used for the screenshots"]]
    K.table(s, 0.6, 3.0, [2.2, 3.6, 3.2, 3.13], rows, font_size=13, row_h=0.62, first_bold=True)
    K.text(s, 0.6, 6.25, 12.13, 0.7, "All identities are generated; no real personal data and no UIDAI service are involved. Names in the seed file are common given names combined arbitrarily.", size=13, color=K.TXT, italic=True)
    notes[6] = "Be frank: there is no dataset in the machine-learning sense. The 'data' is a synthetic identity registry and generated benchmark voters. Accuracy and F1 do not apply to this project."

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Preprocessing: input validation and Aadhaar normalisation")
    wipe(s)
    K.flow(s, 0.6, 1.4, 12.13, 1.1, [("Strip spaces / hyphens", K.BLUE), ("12 digits?", K.BLUE), ("Verhoeff checksum", K.GREEN), ("Salted SHA-256", K.GREEN), ("Registry lookup", K.ORANGE),
                                      ("Own account? eligible? not voted?", K.PURPLE)], size=12, gap=0.25)
    K.card(s, 0.6, 2.85, 5.95, 3.95, "Verhoeff check digit", "The last digit of an Aadhaar number is a check digit of the Verhoeff dihedral-group scheme. It catches every single-digit error and adjacent transposition before any database work. Cost: "
           + f"{MI['verhoeff_validate']['mean_ms'] * 1000:.1f} microseconds per number.", K.BLUE, "V", body_size=18)
    K.card(s, 6.78, 2.85, 5.95, 3.95, "Hashed, never stored", "The registry stores sha256(salt + pepper + number) and a masked form (XXXX-XXXX-last four). The voter sees only the masked number. "
           "Failed attempts are audited and limited to 15 per minute per IP.", K.GREEN, "H", body_size=18)
    notes[7] = "Validation is cheap and happens first. Rejections at any stage return HTTP 400 or 403 and an audit entry. The registry is a synthetic local table; a real UIDAI adapter could replace the provider through the interface."

    # ---- 8 models -> cryptographic design
    s = S[7]
    set_title(s, "Cryptographic and ledger design (no ML model)")
    wipe(s)
    rows = [["Component", "Configuration", "Role"],
            ["Passwords", "Argon2id (argon2-cffi defaults)", "login verification"],
            ["Aadhaar lookup", "salted and peppered SHA-256 + Verhoeff", "registry membership"],
            ["Ballot secrecy", "AES-256-GCM, 12-byte random nonce, one election key", "encrypts the candidate id"],
            ["Signatures", "Ed25519: one system key for transactions, three validator keys for blocks", "authenticity of tx and block"],
            ["Ledger", "SHA-256 hash chain, flat Merkle root, quorum 2 of 3 validators", "tamper evidence"]]
    K.table(s, 0.6, 1.5, [2.4, 6.3, 3.43], rows, font_size=14, row_h=0.72, first_bold=True)
    K.tile(s, 0.6, 5.95, 3.8, 1.0, "3 validators", "in-process Ed25519 keys on one server", K.BLUE, vsize=22)
    K.tile(s, 4.7, 5.95, 3.8, 1.0, "2 of 3", "approvals commit a block", K.GREEN, vsize=22)
    K.tile(s, 8.8, 5.95, 3.93, 1.0, "1 tx / block", "one vote per block", K.ORANGE, vsize=22)
    notes[8] = ("A local permissioned-ledger simulation. The three validators are keys in data/validators.json on the same machine, so the quorum demonstrates the rule but gives no distributed trust. "
                "The 'Merkle root' is a flat hash of the sorted transaction hashes, not a tree.")

    # ---- 9 training -> system configuration
    s = S[8]
    set_title(s, "System configuration (no training step)")
    wipe(s)
    rows = [["Setting", "Value"],
            ["One-time token", "secrets.token_urlsafe(32); stored as SHA-256; expires after 10 minutes; one per election and voter"],
            ["Rate limits", "10 logins and 15 verifications per 60 s per client IP (in memory)"],
            ["Session", "server-side store, cookie aegis_session HttpOnly, SameSite=lax; CSRF token in X-CSRF-Token on every POST; no Secure flag (plain HTTP)"],
            ["Ledger", "3 validators, quorum 2, one transaction per block, genesis block at index 0"],
            ["Machine", f"{F.ENV.get('python', '')} on Windows 11, Intel i5-12500 (6 cores, 12 threads), 15.7 GB RAM; PC shared with other jobs"]]
    K.table(s, 0.6, 1.3, [2.4, 9.73], rows, font_size=13, row_h=0.5, first_bold=True)
    K.picture(s, F.fig("f05_micro_timings.png"), 0.6, 4.55, 7.0, 2.5)
    K.text(s, 7.9, 4.85, 4.8, 2.0, f"Argon2id hash {MI['argon2id_hash']['mean_ms']:.0f} ms and verify {MI['argon2id_verify']['mean_ms']:.0f} ms dominate; AES-GCM, SHA-256 and Ed25519 sign cost under 0.2 ms each. The cryptography of a vote is not the bottleneck.", size=14, color=K.INK)
    notes[9] = "These are the fixed parameters read from the code. Micro-timings are means over thousands of calls on the shared PC (script run_experiments.py)."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: casting and auditing")
    wipe(s)
    K.picture(s, F.diag("10_flowchart_cast_vote.png"), 0.5, 1.2, 5.6, 5.75)
    K.text(s, 6.4, 1.5, 6.3, 5.3, [
        ("**cast_vote.** Election OPEN and candidate active; token hash matches, unused, not expired; no participation row. Then encrypt, hash, sign.", {"bullet": True, "space_after": 9}),
        ("**propose_block.** Each validator checks schema, new nonce, new transaction hash and signature, then signs the block hash. At least 2 of 3 approve, or a ValueError rejects the block and the token stays unused.", {"bullet": True, "space_after": 9}),
        ("**validate_chain.** Recomputes the Merkle root, block hash and previous-hash link of every block; returns the first failing field.", {"bullet": True, "space_after": 9}),
        ("**Not covered.** Validator signatures, transaction hashes against their fields, the ballots table and a dropped tip block (see testing).", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[10] = "Left: the casting flowchart. Right: the three functions in app/services/voting_service.py and app/ledger/ledger.py. The last bullet is a finding from our own tamper study, shown later."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, F.diag("04_dfd_level1.png"), 0.5, 1.3, 6.5, 5.6)
    rows = [["Module", "Role"], ["identity/provider, verhoeff", "Aadhaar checks"], ["services/voting_service", "token, cast, tally"], ["ledger/ledger", "blocks, quorum, validate"],
            ["security/crypto, auth", "AES, Ed25519, Argon2id"], ["security/sessions, rate_limit", "cookie session, throttling"], ["services/audit", "audit log"],
            ["api_v1", f"{NR} JSON routes"], ["benchmarks/run_benchmark", "latency and throughput"]]
    K.table(s, 7.2, 1.4, [2.9, 2.63], rows, font_size=12, row_h=0.52)
    notes[11] = "Level-1 data flow: the login and Aadhaar check produce a token, the casting process hands a signed transaction to the ledger, and the auditor and tally processes read the stores."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database design and UML")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.5, 1.3, 6.0, 5.0)
    K.picture(s, F.diag("06_uml_class.png"), 6.7, 1.3, 6.1, 5.65)
    K.text(s, 0.6, 6.35, 5.9, 0.7, "13 tables. UNIQUE(election, voter) on eligibility, authorisation and participation lets the database refuse a second vote.", size=12, color=K.TXT, italic=True)
    notes[12] = "Left: ER diagram of the 13 tables. Right: the models as classes with the voting and ledger modules. Ballots carry no voter column; voter_participation is the only voter-to-ballot link."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    rows = [["Layer", "Technology"],
            ["Backend", f"Python {F.ENV.get('python', '3.11')}, FastAPI {lib.get('fastapi', '')}, Uvicorn, Pydantic, SQLAlchemy {lib.get('sqlalchemy', '')}, SQLite"],
            ["Cryptography", f"cryptography {lib.get('cryptography', '')} (AES-GCM, Ed25519), argon2-cffi {lib.get('argon2-cffi', '')} (Argon2id), hashlib SHA-256"],
            ["Reports", "reportlab (PDF generation), Jinja2 (original pages)"],
            ["Front end", "React 18.3, Vite 8, TypeScript 5.9, Tailwind CSS 4, Radix UI, TanStack Query 5, React Router 7, Recharts 3, Framer Motion, GSAP"],
            ["Testing", "pytest (17 tests), FastAPI TestClient, httpx, an HTTP matrix in run_experiments.py, Playwright for screenshots"],
            ["Run", f"run.bat creates the virtual environment, seeds the database and starts both servers (ports {F.API_PORT} and {F.WEB_PORT})"]]
    K.table(s, 0.6, 1.5, [2.4, 9.73], rows, font_size=14, row_h=0.7, first_bold=True)
    notes[13] = f"Everything is open source. The versions are those measured: Python {F.ENV.get('python', '')}, FastAPI {lib.get('fastapi', '')}, SQLAlchemy {lib.get('sqlalchemy', '')}."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Identity check (format, Verhoeff, registry, own id)", "Done", f"25 of 25 HTTP checks incl. identity cases"],
            ["Token, encrypted ballot, one-vote layers", "Done", "duplicate / replay / expired cases rejected"],
            ["Ledger: blocks, 3 validators, quorum, validate_chain", "Done, gaps", f"{F.N_TAMPER_PRODUCT} of {F.N_TAMPER} tamper cases detected"],
            ["Admin, voter and auditor consoles", "Done", f"{NR} JSON routes; 23 screenshots"],
            ["Audit log, rate limiting, CSRF, RBAC", "Done", "401 / 403 / 429 verified"],
            ["TLS / Secure cookies", "Not done", "plain HTTP, no Secure flag"],
            ["Real UIDAI integration, distributed validators", "Not done", "synthetic registry; one-machine ledger"]]
    K.table(s, 0.6, 1.4, [5.2, 1.7, 5.23], rows, font_size=13, row_h=0.62)
    notes[14] = "State of the code base. The honest gaps: TLS, a real identity provider, distributed validators, and signature checks inside validate_chain."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{Bs['successes']:,} / {F.N_VOTERS_BENCH:,}", "votes succeeded in the benchmark, 0 failures", K.BLUE),
                                   (f"{Bs['mean_ms']:.0f} ms", f"mean per vote on the shared PC ({idle_lo:.0f}-{idle_hi:.0f} ms idle)", K.GREEN),
                                   (f"{Lt['end_to_end']['mean_ms']:.0f} ms", "whole voter journey over HTTP (mean, 27 voters)", K.ORANGE),
                                   (f"{F.N_TAMPER_PRODUCT} of {F.N_TAMPER}", "tamper cases caught by validate_chain", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    K.picture(s, F.fig("f01_benchmark_1000.png"), 0.5, 2.9, 7.1, 3.2)
    K.picture(s, F.fig("f07_http_latency.png"), 7.8, 2.9, 4.9, 3.2)
    K.text(s, 0.6, 6.15, 12.13, 0.85, "The 'async' batches in the benchmark run sequentially, so batch sizes differ only by noise; the base paper's 2-4 s per transaction (read from its charts) is on another chain and machine, so only the order of magnitude is comparable.", size=12, color=K.TXT, italic=True)
    notes[15] = (f"Benchmark: {F.N_VOTERS_BENCH} synthetic voters, all votes succeeded; mean {Bs['mean_ms']:.1f} ms, p95 {Bs['p95_ms']:.1f} ms on a shared PC; earlier idle-PC runs gave {idle_lo:.1f} to {idle_hi:.1f} ms. "
                 f"HTTP journey login + verify + cast averaged {Lt['end_to_end']['mean_ms']:.0f} ms, dominated by Argon2id login ({Lt['login']['mean_ms']:.0f} ms).")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    shots = [("17_voter_aadhaar_verification.png", "1  Aadhaar check: masked number, format, Verhoeff, registry"), ("19_voter_receipt.png", "2  Receipt: ballot id, transaction hash, block number"),
             ("21_auditor_dashboard.png", "3  Auditor: chain integrity check and tamper demo")]
    for i, (f_, cap) in enumerate(shots):
        x = 0.6 + i * 4.14
        K.picture(s, crop(f_, (240, 50, 1440, 900), f"r2s{i}"), x, 1.3, 3.95, 2.95, border=True)
        K.text(s, x, 4.3, 3.95, 0.55, cap, size=12, color=K.TXT, align="c", italic=True)
    K.text(s, 0.6, 5.1, 12.13, 1.8, [
        ("Real captures of the running React application (1440 x 900) against the demo database: 200 voters, 8 elections, 212 ballots, 213 blocks.", {"bullet": True}),
        ("The voter flow is three steps: verify identity, choose a candidate, keep the receipt. The same receipt values appear in the auditor's block view.", {"bullet": True}),
        ("The banner 'Demo verification environment - synthetic data only' is shown on every voter page.", {"bullet": True}),
    ], size=15, color=K.INK, space_after=6)
    notes[16] = "Real screenshots of the running React application with the demo database (200 voters, 8 elections, 212 ballots, 213 blocks): identity check, receipt and the auditor console. More screens follow in the final deck."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.PYTEST_PASSED} / {F.PYTEST_TOTAL}", "pytest tests passed", K.GREEN), (f"{F.MATRIX_PASSED} / {F.MATRIX_TOTAL}", "HTTP security and functional checks", K.BLUE),
                                   ("HTTP 429", "login throttled after 10 attempts per 60 s", K.ORANGE), (f"{F.N_TAMPER_STRICT} / {F.N_TAMPER}", "tamper cases caught by a stricter audit", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Observation", "Action"],
            ["validate_chain misses edits to the ballots table (the tally source), edits with all hashes recomputed, forged signatures and a dropped tip block", "Documented; stricter audit built for the study only; fix listed as next step"],
            ["The 'tamper test' button simulates detection on an in-memory copy", "Stated plainly; the unit test tampers the real database"],
            ["Admin can read a live tally of an open election; voter_participation links voter to ballot", "Listed as privacy limitations"]]
    K.table(s, 0.6, 3.0, [6.8, 5.33], rows, font_size=14, row_h=0.92)
    notes[17] = "Tests ran on scratch databases so the demo data stayed untouched. The tamper study applied 13 kinds of edit to a 361-block chain and rolled each back."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "Corrective action"],
            ["No access to UIDAI; real Aadhaar data must not be used", "Synthetic registry with valid Verhoeff check digits behind an interface that a real adapter can replace"],
            ["Keeping identity apart from the ballot", "Token hashed at rest, ballots table without voter id; remaining link in voter_participation measured and disclosed"],
            ["Ledger checks weaker than the claim 'immutable'", "Tamper study run; gaps reported; stricter audit prototyped in the experiment script"],
            ["Benchmark noise on a shared PC", f"Idle runs ({idle_lo:.0f}-{idle_hi:.0f} ms) and loaded run ({Bs['mean_ms']:.0f} ms) both reported"],
            ["Base paper's setting differs (Ethereum, biometrics, C#)", "Only order-of-magnitude comparison, differences stated"]]
    K.table(s, 0.6, 1.5, [5.0, 7.13], rows, font_size=15, row_h=0.9)
    notes[18] = "Each challenge was met by a concrete design choice or by measuring it and saying so in the report."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Harden the audit", "Verify validator signatures, recompute transaction hashes and cross-check ballots against the ledger inside validate_chain.", K.BLUE, "1"),
        ("Improve privacy", "Per-election keys, break the voter-to-ballot link, and keep tallies sealed until the election closes.", K.GREEN, "2"),
        ("Secure transport", "TLS with Secure cookies, persistent sessions and a shared rate-limit store.", K.ORANGE, "3"),
        ("Evaluate further", "Concurrent voting test, real multi-node validators, penetration test and a small usability study.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.09, 1.6, 2.85, 4.6, t, b_, col, gl, body_size=18)
    notes[19] = "Plan to the final review. The first two items address the gaps found by our own tamper study and design review."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Likely questions: is the Aadhaar check real (no, synthetic registry); is it decentralised (no, three validators on one machine); can the administrator change a vote (some edits are detected, some are not; see the tamper study)."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
