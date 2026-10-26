"""16.Final_PPT.pptx: 28 slides. Built from D:\\abstracts\\Templates\\Final_PPT.pptx (banner, rule, title and footer chrome inherited)."""

import os

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE

from . import facts as F
from . import pptkit as K
from .lit import (BASE_PAPER_POINTS, EXISTING_SYSTEM, EXPECTED_OUTCOMES, GAPS, LIT_TABLE, OBJECTIVES, PROBLEM_STATEMENT, PROPOSED_APPROACH,
                  SUPPORT_EVIDENCE)
from .refs import REFS

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


def ftile(slide, x, y, w, h, value, label, color=K.FBLUE, vsize=26):
    K.box(slide, x, y, w, h, fill=K.FHEAD, line=None, radius=0.05)
    K.box(slide, x, y, 0.08, h, fill=color, line=None, shape=MSO_SHAPE.RECTANGLE)
    K.text(slide, x + 0.2, y + 0.06, w - 0.3, h * 0.55, value, size=vsize, color=K.FNAVY, bold=True, anchor="m", font=FONT)
    K.text(slide, x + 0.2, y + h * 0.58, w - 0.3, h * 0.4, label, size=12, color=K.DARK, font=FONT)


def clean_ref(i):
    return REFS[i - 1].replace("*", "").replace("  ", " ")


def build(out_path):
    prs = Presentation(TEMPLATE)
    S = list(prs.slides)
    assert len(S) == 28, len(S)
    cp = prs.core_properties
    cp.title = f"{F.TITLE} - Final Review"
    cp.author = f"Batch {F.BATCH_NO}, Dept. of CSE, TKRCET"
    cp.comments = ""
    cp.subject = F.PRODUCT
    cp.keywords = "secure e-voting, Aadhaar verification, blockchain ledger, AES-GCM, Ed25519, audit"
    notes = {}

    sy = F.BENCH_SYNC
    bb = F.BENCH_BATCH
    lat = F.LAT
    st = F.STAGE
    mt = F.MICRO
    vh = F.VALIDATE_BY_HEIGHT
    idle = F.IDLE_RUNS
    idle_mean = (min(r["sync"]["mean_ms"] for r in idle), max(r["sync"]["mean_ms"] for r in idle))
    idle_thr = (min(r["sync"]["throughput"] for r in idle), max(r["sync"]["throughput"] for r in idle))
    batch_means = [sy["mean_ms"]] + [v["mean_ms"] for v in bb.values()]
    n_det, n_all, n_strict = F.N_TAMPER_PRODUCT, F.N_TAMPER, F.N_TAMPER_STRICT

    # footers on every slide except the title
    for sl in S:
        for sh in sl.shapes:
            if sh.top == TOP_FOOT and sh.has_text_frame and "Final Review" in sh.text_frame.text:
                K.replace_text(sh, f"Dept. of CSE  |  Batch {F.BATCH_NO}  |  Final Review")

    # ---- 1 title
    s = S[0]
    for sh in s.shapes:
        if sh.name == "Text 1":
            K.replace_text(sh, F.FULL_TITLE, 24)
        elif sh.name == "Text 2":
            K.replace_text(sh, f"Final Review  ·  {F.PRODUCT}")
        elif sh.name == "Text 3":
            K.replace_text(sh, f"Team Details : Batch {F.BATCH_NO}")
        elif sh.name == "Text 4":
            K.replace_text(sh, "\n".join(f"{r_}   {n_}" for n_, r_ in F.STUDENTS))
        elif sh.name == "Text 5":
            K.replace_text(sh, f"Under the Esteemed Guidance of\n{F.GUIDE}\n{F.GUIDE_DESIGNATION}, Department of CSE")
        elif sh.name == "Text 6":
            K.replace_text(sh, f"DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING  ·  {F.COLLEGE_SHORT}  ·  Academic Year {F.YEAR}")
    notes[1] = "Introduce the team and the project: AegisBallot, a local e-voting application with Aadhaar-style verification, encrypted ballots and an auditable ledger."

    # ---- 2 table of contents
    s = S[1]
    set_title(s, "Table of Contents")
    for sh in s.shapes:
        if sh.name == "Text 4":
            K.replace_text(sh, "Abstract\nBase Paper & Literature Survey\nResearch Gap, Problem Statement & Objectives\nProposed System & Architecture\nMethodology & Identity Verification\nBallot, Token & Ledger Design\nInteraction, Database & Implementation\nResults: Benchmark, Tamper Matrix, Parameters\nPerformance & Testing\nComparison with Base Paper\nOutput Screens\nConclusion, Future Scope & References", 17)
    notes[2] = "The agenda follows the report: problem, design, method, results, comparison, screens, conclusion."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract")
    wipe(s)
    ftext(s, 0.55, 1.85, 12.2, 5.0, [
        ("Manual polling is slow and error-prone; conventional e-voting keeps ballots in a database an administrator could alter, and without identity binding duplicate votes cannot be excluded reliably.", {"bullet": True, "space_after": 9}),
        ("AegisBallot: a voter verifies a synthetic Aadhaar number (12 digits, Verhoeff checksum, salted-hash registry), receives a 10-minute single-use token, casts an AES-256-GCM encrypted ballot, and the Ed25519-signed transaction is committed to a hash-chained ledger by 2 of 3 validators.", {"bullet": True, "space_after": 9}),
        (f"Admin, voter and auditor roles on FastAPI + React; {F.PYTEST_PASSED} of {F.PYTEST_TOTAL} tests and {F.MATRIX_PASSED} of {F.MATRIX_TOTAL} HTTP security checks pass.", {"bullet": True, "space_after": 9}),
        (f"Benchmark of {F.N_VOTERS_BENCH:,} synthetic voters: 1000 of 1000 votes succeed; mean {sy['mean_ms']:.1f} ms per vote on a shared PC ({idle_mean[0]:.0f}-{idle_mean[1]:.0f} ms on an idle PC); a full voter journey over HTTP takes {lat['end_to_end']['mean_ms']:.0f} ms.", {"bullet": True, "space_after": 9}),
        (f"The product's integrity check catches {n_det} of {n_all} tamper cases; a stricter audit written for the study catches {n_strict} of {n_all}.", {"bullet": True, "space_after": 9}),
        ("Not done: real UIDAI link, networked validators, TLS, concurrent-vote tests, a user study.", {"bullet": True}),
    ], size=16)
    notes[3] = "Read the problem, then the system in one breath. Give each number with its protocol and end on the honest limits."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base Paper")
    wipe(s)
    ftext(s, 0.55, 1.85, 12.2, 0.8, F.BASE_PAPER, size=13, color=K.FNAVY)
    rows = [["Aspect", "Base paper: Blockchain-enhanced electoral integrity - a robust model for secure digital voting in Oman"],
            ["Method", "Four tiers: MySQL + Ethereum nodes (Geth test chain, Nethereum) + C# web tier + client devices. Smart contracts register voters and candidates, cast and count votes; biometric authentication blocks duplicates (simulation)"],
            ["Data", "1000 synthetic voters (synthetic SSNs, names, addresses); voter registration and vote-casting transactions"],
            ["Reported results", "Synchronous and asynchronous batches of 10, 20, 30, 50; about 2 s per registration and 3-4 s per vote (read by eye from its Figures 6 and 9; no tabulated values)"],
            ["Security", "Discusses Sybil, 51%, smart-contract and DoS threats; proposes PBFT among approved validators; no attack experiments"],
            ["Stated limits", "Layer-1 throughput (Ethereum about 119 tx/s as quoted), synthetic data, no pilot, public-trust studies needed"]]
    ftable(s, 0.55, 2.7, [2.0, 10.2], rows, size=13, row_h=0.66)
    notes[4] = "Shaikh et al., F1000Research 2025. We keep the idea of a ledger-backed vote and add national-ID-style identity, an admin and auditor workflow, and a tamper study; we do not use Ethereum."

    # ---- 5 literature survey
    s = S[4]
    set_title(s, "Literature Survey")
    wipe(s)
    rows = [["Work", "Year", "Approach", "Data / finding / limitation"]]
    for r in LIT_TABLE:
        rows.append([r[0].replace(" (base paper)", " (base)"), r[1], r[2], r[3]])
    ftable(s, 0.55, 1.8, [2.3, 0.7, 4.9, 4.3], rows, size=10, row_h=0.55, align=["l", "c", "l", "l"])
    notes[5] = "Representative blockchain-voting work. Entries whose full text could not be read are used only for what their abstracts say."

    # ---- 6 research gap
    s = S[5]
    set_title(s, "Research Gap")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.9, [(g, {"bullet": True, "space_after": 16}) for g in GAPS], size=20)
    notes[6] = "Six gaps from the survey. We address identity, administration and audit directly and measure what the ledger check does and does not catch."

    # ---- 7 problem statement
    s = S[6]
    set_title(s, "Problem Statement")
    wipe(s)
    fbox(s, 0.55, 1.9, 12.2, 2.3)
    ftext(s, 0.85, 1.95, 11.6, 2.2, PROBLEM_STATEMENT, size=17, anchor="m", bullets=True)
    for i, (t, b_) in enumerate([("Input", "Login, a 12-digit Aadhaar number and a candidate choice from an eligible voter"), ("Output", "An encrypted ballot on a hash-chained ledger, a receipt, a tally and an auditable trail"), ("Record", "Audit log of every action; chain, blocks and benchmarks open to the auditor")]):
        x = 0.55 + i * 4.1
        fbox(s, x, 4.5, 3.9, 1.7, fill=K.FZEBRA)
        ftext(s, x + 0.2, 4.6, 3.5, 0.4, t, size=17, color=K.FNAVY, bold=True)
        ftext(s, x + 0.2, 5.1, 3.5, 1.0, b_, size=15)
    notes[7] = "The statement has three parts: verify identity, record the ballot immutably, and keep the result checkable."

    # ---- 8 objectives
    s = S[7]
    set_title(s, "Objectives")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.9, [(f"{i}.  {o}", {"space_after": 12}) for i, o in enumerate(OBJECTIVES, 1)], size=20)
    notes[8] = "The six objectives of the proposal. The conclusion states the real status of each; objective 6 (TLS) was not met."

    # ---- 9 proposed system
    s = S[8]
    set_title(s, "Proposed System")
    wipe(s)
    K.flow(s, 0.55, 1.95, 12.2, 1.1, [("Sign in", K.FNAVY), ("Verify Aadhaar", K.FBLUE), ("One-time token", K.GREEN), ("Encrypt + sign", K.ORANGE), ("Ledger block", K.PURPLE), ("Receipt + audit", K.FNAVY)], size=14, gap=0.3, font=FONT)
    ftext(s, 0.55, 3.35, 12.2, 3.5, [(p, {"bullet": True, "space_after": 10}) for p in PROPOSED_APPROACH] + [
        ("A local demonstration: no UIDAI call, no public chain; the interface labels it a demo verification environment.", {"bullet": True})], size=17)
    notes[9] = "The proposed system as one line of boxes and the five design rules behind it."

    # ---- 10 architecture
    s = S[9]
    set_title(s, "System Architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.55, 1.8, 8.4, 5.1)
    ftext(s, 9.2, 2.0, 3.6, 4.8, [
        (f"Web app: React + Vite on port {F.WEB_PORT}", {"bullet": True, "space_after": 8}),
        (f"API: FastAPI on port {F.API_PORT}, 21 JSON routes", {"bullet": True, "space_after": 8}),
        ("Services: identity, voting, crypto, audit, ledger", {"bullet": True, "space_after": 8}),
        (f"Storage: SQLite, {F.N_TABLES} tables, plus key files in data/", {"bullet": True, "space_after": 8}),
        ("Everything runs on one machine; nothing is sent to an outside service", {"bullet": True}),
    ], size=15)
    notes[10] = "Tiers and storage; the ledger is a module inside the application, not a separate network."

    # ---- 11 methodology
    s = S[10]
    set_title(s, "Methodology")
    wipe(s)
    K.flow(s, 0.55, 1.9, 12.2, 1.2, [("Login", K.FNAVY), ("Aadhaar check", K.FBLUE), ("Token", K.GREEN), ("Encrypt", K.ORANGE), ("Sign + propose", K.PURPLE), ("2-of-3 commit", K.FBLUE), ("Audit", K.FNAVY)], size=13, gap=0.2, font=FONT)
    ftext(s, 0.55, 3.4, 12.2, 3.4, [
        ("One vote per voter is enforced four ways: eligibility row, unique participation row, single-use token, and ledger nonce / transaction-hash uniqueness.", {"bullet": True, "space_after": 9}),
        ("Identity and ballot are separated: the ballot row has no voter id; the token is stored only as a SHA-256 hash.", {"bullet": True, "space_after": 9}),
        ("Controls: Argon2id passwords, server-side session, CSRF header, role checks, rate limits (10 logins and 15 verifications per minute per IP), audit log.", {"bullet": True, "space_after": 9}),
        (f"Evaluation: {F.PYTEST_TOTAL} unit tests, {F.MATRIX_TOTAL} HTTP checks, a {n_all}-case tamper study, a {F.N_VOTERS_BENCH:,}-voter benchmark and latency measurements.", {"bullet": True, "space_after": 9}),
        ("Every number comes from scripts/run_experiments.py, the product's own benchmark or the test run.", {"bullet": True}),
    ], size=16)
    notes[11] = "Workflow, the four-layer one-vote rule and how the system was evaluated."

    # ---- 12 identity verification
    s = S[11]
    set_title(s, "Identity Verification: Verhoeff Check and Registry")
    wipe(s)
    ftile(s, 0.55, 1.9, 2.9, 1.05, "0", "external datasets: all identities are synthetic", K.FBLUE, 26)
    ftile(s, 0.55, 3.1, 2.9, 1.05, "20", "seeded voters (voter1-20) + admin + auditor", K.GREEN, 26)
    ftile(s, 0.55, 4.3, 2.9, 1.05, f"{mt['verhoeff_validate']['mean_ms'] + mt['aadhaar_salted_sha256']['mean_ms']:.3f} ms", "Verhoeff check + salted hash per Aadhaar", K.ORANGE, 22)
    ftext(s, 3.7, 1.85, 5.3, 4.9, [
        ("Steps: strip spaces and dashes; exactly 12 digits; Verhoeff checksum (dihedral-group check over the digits); SHA-256 of salt + pepper + number looked up in voter_profiles.", {"bullet": True, "space_after": 8}),
        ("The number must belong to the signed-in account (403 otherwise), the voter must be eligible and not yet have voted.", {"bullet": True, "space_after": 8}),
        ("Only a salted hash and a masked form (XXXX-XXXX-1234) are stored.", {"bullet": True, "space_after": 8}),
        ("Provider interface: DemoAadhaarProvider can be replaced by a real adapter. UIDAI is not contacted; numbers are generated with a valid check digit.", {"bullet": True, "italic": True}),
    ], size=14)
    rows = [["Component", "Choice"], ["Passwords", "Argon2id"], ["Ballot", "AES-256-GCM, 12-byte nonce"], ["Signatures", "Ed25519 (system + 3 validators)"], ["Hashing", "SHA-256 chain"], ["Quorum", "2 of 3 validators"]]
    ftable(s, 9.2, 1.9, [1.35, 2.25], rows, size=11, row_h=0.62, first_bold=True)
    notes[12] = "Be frank: the registry is synthetic and local. The Verhoeff check catches typing errors, not forged numbers."

    # ---- 13 ballot, token and ledger design
    s = S[12]
    set_title(s, "Ballot, Token & Ledger Design")
    wipe(s)
    K.picture(s, F.diag("10_flowchart_cast_vote.png"), 0.55, 1.8, 5.6, 5.1)
    ftext(s, 6.4, 1.95, 6.4, 4.9, [
        ("Token: 256-bit random, only its SHA-256 stored, valid 10 minutes, one per voter and election.", {"bullet": True, "space_after": 10}),
        ("Ballot: candidate id encrypted with AES-256-GCM; transaction hash = SHA-256 of the canonical JSON; Ed25519 signature.", {"bullet": True, "space_after": 10}),
        ("Block: index, timestamp, previous hash, flat hash of the sorted transaction hashes, block hash, validator signatures; one transaction per block.", {"bullet": True, "space_after": 10}),
        ("Validators: three Ed25519 keys held in the same process; each re-checks schema, nonce and hash uniqueness; two approvals commit.", {"bullet": True, "space_after": 10}),
        ("This simulates a permissioned ledger on one machine; it is not Ethereum and not distributed.", {"bullet": True, "italic": True}),
    ], size=15)
    notes[13] = "The core algorithm: cast_vote followed by propose_block. Say plainly that the validators are simulated on one server."

    # ---- 14 user-system interaction
    s = S[13]
    set_title(s, "User – System Interaction")
    wipe(s)
    K.picture(s, F.diag("07_sequence_vote.png"), 0.55, 1.8, 6.3, 5.1)
    K.picture(s, F.diag("08_use_case.png"), 7.0, 1.8, 5.8, 5.1)
    notes[14] = "Sequence of verification and casting, and the use cases of voter, administrator and auditor."

    # ---- 15 database design
    s = S[14]
    set_title(s, "Database Design")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.55, 1.8, 6.4, 5.0)
    rows = [["Table", "Role"], ["users, voter_profiles", "accounts; salted Aadhaar hash"], ["elections, candidates", "election set-up"], ["voter_eligibility", "who may vote, unique per pair"],
            ["voting_authorizations", "hashed single-use tokens"], ["ballots", "ciphertext, no voter id"], ["voter_participation", "voter + ballot id, unique per pair"], ["ledger_blocks / _transactions", "the chain"],
            ["validator_nodes, audit_logs", "public keys; action log"]]
    ftable(s, 7.2, 1.9, [2.5, 3.1], rows, size=11, row_h=0.46)
    ftext(s, 7.2, 6.15, 5.6, 0.7, "voter_participation joins a voter to a ballot id, so ballot secrecy is partial (stated as a limitation).", size=12, color=K.FNAVY, italic=True)
    notes[15] = "Thirteen tables in SQLite. The unique constraints are what the database itself uses to refuse a second vote."

    # ---- 16 implementation highlights
    s = S[15]
    set_title(s, "Implementation Highlights")
    wipe(s)
    for i, (v, l, c) in enumerate([("21", "JSON API routes", K.FBLUE), (f"{F.PYTEST_TOTAL} + {F.MATRIX_TOTAL}", "unit tests + HTTP checks", K.GREEN), ("12", "React pages (3 role consoles)", K.ORANGE), ("5,281", "lines of frontend TypeScript", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.9, 2.9, 1.1, v, l, c, 28)
    ftext(s, 0.55, 3.3, 12.2, 3.5, [
        ("Backend: FastAPI + SQLAlchemy 2 (about 2,091 lines); React 18, TanStack Query, Tailwind 4 frontend; one run.bat starts both servers.", {"bullet": True, "space_after": 9}),
        ("Input checks: Pydantic models, Aadhaar format and checksum, election window and status, candidate must belong to the election.", {"bullet": True, "space_after": 9}),
        ("Auditor tools: integrity check, block explorer, tamper demonstration on a cloned ledger, audit log viewer; admin benchmark page.", {"bullet": True, "space_after": 9}),
        ("Known gaps: sessions and rate limits are in memory, no TLS or Secure cookie flag, keys stored as files in data/.", {"bullet": True}),
    ], size=17)
    notes[16] = "Highlights and the configuration gaps that a real deployment would have to close."

    # ---- 17 results: benchmark
    s = S[16]
    set_title(s, "Results – Benchmark of 1,000 Synthetic Voters")
    wipe(s)
    for i, (v, l, c) in enumerate([("1000 / 1000", "votes succeeded, 0 failures", K.FBLUE), (f"{sy['mean_ms']:.1f} ms", "mean per vote (shared PC)", K.GREEN),
                                   (f"{sy['throughput']:.1f} ops/s", "synchronous throughput", K.ORANGE), (f"{idle_mean[0]:.0f}-{idle_mean[1]:.0f} ms", f"mean per vote on idle PC ({idle_thr[0]:.0f}-{idle_thr[1]:.0f} ops/s)", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.85, 2.9, 1.1, v, l, c, 24)
    K.picture(s, F.fig("f01_benchmark_1000.png"), 0.55, 3.1, 7.4, 3.05)
    K.picture(s, F.fig("f02_benchmark_runs.png"), 8.1, 3.1, 4.7, 2.1)
    ftext(s, 8.1, 5.3, 4.7, 1.1, f"Median {sy['median_ms']:.1f} ms, p95 {sy['p95_ms']:.1f} ms, max {sy['max_ms']:.0f} ms. The PC was shared with other jobs; earlier idle runs (50, 200, 500 voters) were about 60 ops/s.", size=12)
    ftext(s, 0.55, 6.3, 12.2, 0.6, "'Batches' of 10, 20, 30 run sequentially in the benchmark code, so differences between them are machine noise, not an effect of batching.", size=12, color=K.FNAVY, italic=True)
    notes[17] = "The base paper used 1000 synthetic voters too. Stress that the batch bars differ only by load on the PC: the code is sequential."

    # ---- 18 tamper matrix
    s = S[17]
    set_title(s, "Tamper-Detection Matrix (13 cases)")
    wipe(s)
    K.picture(s, F.fig("f06_tamper_matrix.png"), 0.55, 1.85, 6.6, 4.4)
    ftext(s, 7.4, 1.9, 5.4, 4.9, [
        (f"Product check (validate_chain): {n_det} of {n_all} cases detected; stricter audit written for the study: {n_strict} of {n_all}.", {"bullet": True, "space_after": 9}),
        ("Missed by the product: edited ledger payload, edited ballots table (the tally source, tally changes), edit with all hashes recomputed, forged validator signatures, dropped tip block.", {"bullet": True, "space_after": 9}),
        ("The stricter audit verifies signatures, recomputes transaction hashes and cross-checks ballots against the ledger.", {"bullet": True, "space_after": 9}),
        ("Keys sit on the same server, so a writer of the files could forge signatures too.", {"bullet": True, "italic": True}),
    ], size=14)
    ftext(s, 0.55, 6.3, 6.6, 0.6, "Each case was applied inside a transaction and rolled back; chain of 361 blocks.", size=12, color=K.FNAVY, italic=True)
    notes[18] = "This replaces the confusion matrix: it shows which tampering is detected. It is the most important finding of the evaluation."

    # ---- 19 parameter analysis
    s = S[18]
    set_title(s, "Parameter Analysis – Chain Height, Batch Size, Primitives")
    wipe(s)
    K.picture(s, F.fig("f03_validate_chain_growth.png"), 0.55, 1.8, 5.9, 3.5)
    K.picture(s, F.fig("f05_micro_timings.png"), 6.6, 1.8, 6.2, 3.5)
    h_lo, h_hi = vh["25"], vh["300"]
    ftext(s, 0.55, 5.45, 12.2, 1.5, [
        (f"validate_chain grows linearly: {h_lo['median_ms']:.0f} ms at {h_lo['height_blocks']} blocks, {h_hi['median_ms']:.0f} ms at {h_hi['height_blocks']} blocks (about {h_hi['median_ms'] / h_hi['height_blocks']:.1f} ms per block).", {"bullet": True, "space_after": 6}),
        (f"Batch size 10 / 20 / 30: {bb['10']['throughput']:.1f} / {bb['20']['throughput']:.1f} / {bb['30']['throughput']:.1f} ops/s on the loaded PC; batches run sequentially, so this is noise.", {"bullet": True, "space_after": 6}),
        (f"Primitives: AES-GCM {mt['aes256gcm_encrypt']['mean_ms']:.3f} ms, Ed25519 sign {mt['ed25519_sign']['mean_ms']:.2f} ms, Argon2id verify {mt['argon2id_verify']['mean_ms']:.0f} ms: password hashing dominates login, not the ballot cryptography.", {"bullet": True}),
    ], size=13)
    notes[19] = "Parameter analysis for a systems project: how cost changes with chain length and which primitive dominates. Batch size has no real effect."

    # ---- 20 performance & testing
    s = S[19]
    set_title(s, "Performance & Testing")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{lat['login']['mean_ms']:.0f} ms", "login over HTTP (Argon2id)", K.FBLUE), (f"{lat['verify']['mean_ms']:.0f} ms", "Aadhaar verification", K.GREEN),
                                   (f"{lat['cast']['mean_ms']:.0f} ms", "cast ballot (block commit)", K.ORANGE), (f"{lat['end_to_end']['mean_ms']:.0f} ms", "whole voter journey (27 voters)", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.85, 2.9, 1.15, v, l, c, 26)
    rows = [["Test layer", "What it covers", "Result"],
            ["Unit tests (pytest)", "Aadhaar format and checksum, duplicate vote, RBAC, tamper, nonce replay, token expiry, identity separation, audit log", f"{F.PYTEST_PASSED} of {F.PYTEST_TOTAL} passed in {F.PYTEST_SECONDS:.1f} s"],
            ["HTTP matrix", "401 / 403 / 400 / 404 / 429 paths: RBAC, CSRF, wrong or forged Aadhaar, replay, rate limit, injection-style login", f"{F.MATRIX_PASSED} of {F.MATRIX_TOTAL} as expected"],
            ["Per-vote stages (in-process)", "authorise, encrypt + sign, propose block, persist", f"{st['authorise']:.1f} + {st['encrypt_sign_hash']:.1f} + {st['propose_block']:.1f} + {st['persist']:.1f} ms"],
            ["Not tested", "concurrent voters, penetration test, user study, TLS, real UIDAI", "gap"]]
    ftable(s, 0.55, 3.2, [2.6, 6.6, 3.0], rows, size=12, row_h=0.62)
    ftext(s, 0.55, 6.4, 12.2, 0.55, "Intel Core i5-12500, 15.7 GB, Windows 11; the PC was shared with other jobs. Tests ran against scratch databases, never the demo database.", size=12, color=K.FNAVY, italic=True)
    notes[20] = "Everything passed, but the tests did not cover concurrency or a penetration test; say so."

    # ---- 21 comparison with the base paper
    s = S[20]
    set_title(s, "Comparison with Base Paper (context only – different chain and scope)")
    wipe(s)
    rows = [["Aspect", "Base paper [1]", "AegisBallot"],
            ["Ledger", "Ethereum (Geth test chain), smart contracts, Nethereum", "Local permissioned ledger, 3 in-process validators, 2-of-3, SQLite"],
            ["Identity", "Biometric authentication (simulated)", "Aadhaar-style 12 digits, Verhoeff + salted-hash registry (synthetic)"],
            ["Stack / hardware", "C# .NET Core 7, MySQL; i7-12700, 16 GB, Windows 10", "Python FastAPI, React, SQLite; i5-12500, 15.7 GB, shared PC"],
            ["Test data", "1000 synthetic voters; batches 10, 20, 30, 50", f"{F.N_VOTERS_BENCH:,} synthetic voters; sequential batches 10, 20, 30"],
            ["Time per transaction", "about 2 s registration, 3-4 s vote (read by eye from Figs 6, 9)", f"cast {min(batch_means):.0f}-{max(batch_means):.0f} ms in-process (loaded PC), {lat['cast']['mean_ms']:.0f} ms over HTTP"],
            ["Security evaluation", "Threat discussion; no attack experiments", f"{F.MATRIX_TOTAL} HTTP checks + {n_all}-case tamper study; not decentralised"]]
    ftable(s, 0.55, 1.85, [2.0, 4.8, 5.4], rows, size=12, row_h=0.64)
    ftext(s, 0.55, 6.4, 12.2, 0.6, "Different chain, hardware, definition of a transaction and guarantees: the times are an order of magnitude only. No superiority over the base paper is claimed; a local ledger does not offer its decentralisation.", size=12, color=K.FNAVY, italic=True)
    notes[21] = "State plainly that a single-machine ledger is not comparable with an Ethereum test chain; the millisecond numbers show only that the local design is light."

    # ---- 22-24 output screens
    s = S[21]
    set_title(s, "Output – Voter Flow: Aadhaar Verification and Receipt")
    wipe(s)
    K.picture(s, F.shot("17_voter_aadhaar_verification.png"), 0.55, 1.85, 6.0, 4.2, border=True)
    K.picture(s, F.shot("19_voter_receipt.png"), 6.8, 1.85, 6.0, 4.2, border=True)
    ftext(s, 0.55, 6.2, 12.2, 0.7, "Left: the voter enters a 12-digit number against the masked Aadhaar of the account; a token is issued for ten minutes. Right: after the vote the receipt shows ballot id, transaction hash, block number and block hash, never the choice.", size=12, color=K.FNAVY)
    notes[22] = "Real screenshots of the running app with 200 voters, 8 elections and 212 ballots in the database."
    s = S[22]
    set_title(s, "Output – Administrator Dashboard and Results")
    wipe(s)
    K.picture(s, F.shot("10_admin_dashboard.png"), 0.55, 1.85, 6.0, 4.2, border=True)
    K.picture(s, F.shot("14_results.png"), 6.8, 1.85, 6.0, 4.2, border=True)
    ftext(s, 0.55, 6.2, 12.2, 0.7, "Left: dashboard with voters, votes cast, ledger height, validators and turnout per election. Right: results of a closed election, counted from the 8 decrypted ballots.", size=12, color=K.FNAVY)
    notes[23] = "The tally is read from the ballots table; the tamper study shows the ledger check does not cover that table."
    s = S[23]
    set_title(s, "Output – Auditor Ledger View and Block Detail")
    wipe(s)
    K.picture(s, F.shot("21_auditor_dashboard.png"), 0.55, 1.85, 6.0, 4.2, border=True)
    K.picture(s, F.shot("22_auditor_block_detail.png"), 6.8, 1.85, 6.0, 4.2, border=True)
    ftext(s, 0.55, 6.2, 12.2, 0.7, "Left: chain integrity, validators, integrity check and tamper demonstration. Right: one block with previous hash, Merkle root, block hash and the three validator signatures.", size=12, color=K.FNAVY)
    notes[24] = "The auditor can recompute the chain and inspect every block; the tamper demonstration works on a cloned ledger."

    # ---- 25 conclusion
    s = S[24]
    set_title(s, "Conclusion")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 5.0, [
        (f"**Delivered:** a working local e-voting platform from Aadhaar verification to encrypted ballot, ledger block, receipt, results and auditor view; {F.PYTEST_PASSED} of {F.PYTEST_TOTAL} tests and {F.MATRIX_PASSED} of {F.MATRIX_TOTAL} HTTP checks pass.", {"bullet": True, "space_after": 9}),
        (f"**Measured:** {sy['mean_ms']:.1f} ms mean per vote at {F.N_VOTERS_BENCH:,} voters (shared PC), {lat['end_to_end']['mean_ms']:.0f} ms per voter journey over HTTP; the integrity check detects {n_det} of {n_all} tamper cases.", {"bullet": True, "space_after": 9}),
        ("**Objectives:** objective 2 achieved; 1, 3, 4, 5 and 6 achieved in part or with caveats (identity on a synthetic registry, 7 of 13 tamper cases caught, windows not enforced, TLS not configured).", {"bullet": True, "space_after": 9}),
        ("**Limits:** synthetic registry, single-machine ledger, partial ballot secrecy, no TLS, no concurrency test, no user study.", {"bullet": True, "space_after": 9}),
        ("**Position:** a local demonstration, not a national-election system.", {"bullet": True}),
    ], size=19)
    notes[25] = "Be explicit about which objectives were met and what was never measured."

    # ---- 26 future scope
    s = S[25]
    set_title(s, "Future Scope")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 5.0, [
        ("Make validate_chain verify validator signatures, recompute transaction hashes and cross-check the ballots table; use a real Merkle tree.", {"bullet": True, "space_after": 10}),
        ("Separate voter and ballot records so ballots are unlinkable; per-election keys; threshold or homomorphic tallying.", {"bullet": True, "space_after": 10}),
        ("TLS with Secure cookies, persistent sessions, shared rate limiting; OTP or biometric second factor; a real identity-provider adapter.", {"bullet": True, "space_after": 10}),
        ("Validators on separate machines with a network consensus (e.g. PBFT or Raft); PostgreSQL; concurrent-vote and load testing.", {"bullet": True, "space_after": 10}),
        ("Penetration test, usability and accessibility study with real users, and a Layer-2 comparison with the base paper's approach.", {"bullet": True}),
    ], size=20)
    notes[26] = "Concrete next steps, ordered by value: close the audit gaps first."

    # ---- 27 references
    s = S[26]
    set_title(s, "References")
    wipe(s)
    ids = [1, 2, 4, 6, 7, 8, 10, 15, 16, 18, 20, 21, 22, 23]
    ftext(s, 0.55, 1.8, 6.0, 5.1, [(f"[{n}] {clean_ref(n)}", {"space_after": 5}) for n in ids[:7]], size=11)
    ftext(s, 6.8, 1.8, 6.0, 5.1, [(f"[{n}] {clean_ref(n)}" if False else f"[{n}] {clean_ref(n)}", {"space_after": 5}) for n in ids[7:]], size=11)
    notes[27] = "Selected references with their report numbers; the complete numbered list is in the report."

    # ---- 28 thank you
    for sh in S[27].shapes:
        if sh.name == "Text 2":
            K.replace_text(sh, "Questions & Suggestions")
    notes[28] = "Invite questions."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes.get(i, ""))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, "AegisBallot")
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "16.Final_PPT.pptx")))
