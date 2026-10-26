"""Builds 19.IEEE_Paper.docx (two-column, 6 pages) for AegisBallot from facts.py (metrics JSON), the diagrams and the screenshots.

    python -m scripts.docs.build_paper            # from 8.ProjectCode, system python
"""

import os
import sys

from PIL import Image

from . import facts as F
from .paper import Paper

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "docs_build"))

f1 = F.f1


def make_figures():
    """Compact, column-width figures for the paper (true font sizes at 3.45 in), written to docs/figures/paper_*.png."""
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib.patches import Rectangle
    from dgm_lib import (BLUE, GREY, INK, LIGHT, NAVY, ORANGE, PALE_BLUE, PALE_ORANGE, PALE_PURPLE, PALE_TEAL, PURPLE, TEAL, arrow, box, canvas, panel)

    out = {}
    os.makedirs(F.FIGS, exist_ok=True)

    # ---- Fig. 1 architecture
    fig, ax = canvas(3.45, 3.35, 100, 97)
    tiers = [
        (74, "React 18 + Vite single-page app (port 5401)", PALE_BLUE, BLUE, ["Landing, login,\nresults", "Voter - admin -\nauditor consoles", "Axios + TanStack\nQuery, CSRF header"]),
        (50, "FastAPI application (port 8401): /api JSON routes", PALE_TEAL, TEAL, ["Auth, RBAC,\nrate limit", "Admin API\nelections, results", "Voter API\nverify, cast", "Auditor API\nverify, blocks"]),
        (26, "Services", PALE_ORANGE, ORANGE, ["Identity:\nVerhoeff +\nsalted hash", "Voting\nservice", "Crypto: Argon2id\nAES-GCM, Ed25519", "Ledger: 3 validators,\nquorum 2 of 3"]),
    ]
    for y, title, pc, ec, items in tiers:
        panel(ax, 1, y, 98, 21.5, title, pc, ec, fs=5.6, tc=NAVY)
        n = len(items)
        w = 96 / n - 2
        for i, t in enumerate(items):
            box(ax, 1 + 48 / n * 2 * (i + 0.5) + 0.0, y + 8.2, w, 12.5 - 3.8, t, ec, fs=5.0, r=1.0)
    panel(ax, 1, 1.5, 98, 20.5, "Data: SQLite (SQLAlchemy 2), 13 tables, and key files", LIGHT, "#B7C3D3", fs=5.6, tc=NAVY)
    for i, t in enumerate(("users, profiles,\nelections,\ncandidates", "tokens, ballots,\nparticipation", "ledger blocks,\ntransactions,\nvalidators", "audit_logs,\nbenchmarks")):
        box(ax, 12.5 + i * 25, 9.5, 21.5, 11.0, t, "white", tc=INK, ec=TEAL, fs=4.6, r=0.8)
    for y in (95.5, 71.5, 47.5):
        pass
    p = os.path.join(F.FIGS, "paper_fig1_architecture.png")
    fig.savefig(p, dpi=300, facecolor="white")
    out["arch"] = p

    # ---- Fig. 2 main flow (serpentine)
    import matplotlib.pyplot as plt
    fig, ax = canvas(3.45, 3.5, 100, 101.4)
    left = [("1 Sign in", "Argon2id verify, session\ncookie, CSRF token", BLUE), ("2 Aadhaar check", "12 digits, Verhoeff, salted-\nhash lookup, own account", TEAL),
            ("3 One-time token", "256-bit, SHA-256 stored,\n10 min, single use", TEAL), ("4 Choose candidate", "election OPEN, no earlier\nparticipation row", ORANGE),
            ("5 Encrypt and sign", "AES-256-GCM choice, SHA-256\ntx hash, Ed25519 signature", ORANGE)]
    right = [("6 Propose block", "3 validators check schema,\nnonce, tx hash, signature", PURPLE), ("7 Quorum", "at least 2 of 3 sign\nthe block hash", PURPLE),
             ("8 Commit", "block, ballot, token used,\nparticipation (one commit)", NAVY), ("9 Receipt", "ballot id, tx hash,\nblock number and hash", NAVY),
             ("10 Audit", "validate_chain recomputes\nMerkle root, hashes, links", GREY)]
    ys = [88, 70, 52, 34, 16]
    for (t, d, c), y in zip(left, ys):
        box(ax, 25, y, 45, 14, f"{t}\n{d}", c, fs=5.0, r=1.2)
    for (t, d, c), y in zip(right, ys[::-1]):
        box(ax, 75, y, 45, 14, f"{t}\n{d}", c, fs=5.0, r=1.2)
    for a, b in zip(ys[:-1], ys[1:]):
        arrow(ax, (25, a - 7.2), (25, b + 7.2), color=NAVY, lw=1.0)
    for a, b in zip(ys[::-1][:-1], ys[::-1][1:]):
        arrow(ax, (75, a + 7.2), (75, b - 7.2), color=NAVY, lw=1.0)
    arrow(ax, (47.8, 16), (52.2, 16), color=NAVY, lw=1.0)
    ax.text(50, 2.2, "Any failed check: HTTP 400/403, audit-log entry, nothing stored", ha="center", fontsize=5.2, color=GREY, style="italic")
    p = os.path.join(F.FIGS, "paper_fig2_flow.png")
    fig.savefig(p, dpi=300, facecolor="white")
    out["flow"] = p

    # ---- Fig. 3 results chart: (a) cost of each step, (b) tamper matrix
    labels = ["T1 block hash replaced", "T2 previous hash replaced", "T3 Merkle root replaced", "T4 block timestamp edited", "T5 tx hash replaced",
              "T6 ledger payload swapped", "T7 ballots table edited", "T8 transaction deleted", "T9 middle block deleted", "T10 tip block deleted",
              "T11 validator signatures forged", "T12 payload edited, chain re-hashed", "T13 ballots+ledger edited, re-hashed"]
    cases = F.TAMPER_CASES
    st_, lt_ = F.STAGE, F.LAT
    fig = plt.figure(figsize=(3.45, 3.75))
    gs = fig.add_gridspec(2, 1, height_ratios=[0.9, 1.8], hspace=0.5)
    ax0 = fig.add_subplot(gs[0])
    names = ["token issue", "encrypt + sign", "block commit", "persist", "HTTP verify", "HTTP cast", "HTTP login"]
    vals = [st_["authorise"], st_["encrypt_sign_hash"], st_["propose_block"], st_["persist"], lt_["verify"]["mean_ms"], lt_["cast"]["mean_ms"], lt_["login"]["mean_ms"]]
    cols = ["#2B6CB0", "#14907F", "#6B5BD2", "#D9772F", "#8795A8", "#8795A8", "#8795A8"]
    bars = ax0.barh(names[::-1], vals[::-1], color=cols[::-1], height=0.65)
    for b, v in zip(bars, vals[::-1]):
        ax0.text(v + 1.5, b.get_y() + b.get_height() / 2, f"{v:.1f}", va="center", fontsize=5.4)
    ax0.set_xlim(0, max(vals) * 1.18)
    ax0.tick_params(labelsize=5.6, length=2)
    ax0.set_xlabel("mean ms (first four: in-process; last three: HTTP)", fontsize=5.6, labelpad=1)
    ax0.set_title("(a) Where a vote spends its time", fontsize=6.4, pad=2)
    ax0.spines[["top", "right"]].set_visible(False)
    ax = fig.add_subplot(gs[1])
    ax.set_xlim(0, 2)
    ax.set_ylim(0, len(cases))
    ax.invert_yaxis()
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([0.5, 1.5])
    ax.set_xticklabels(["validate_chain()", "stricter audit"], fontsize=5.8)
    ax.xaxis.tick_top()
    ax.set_yticks([i + 0.5 for i in range(len(cases))])
    ax.set_yticklabels(labels, fontsize=5.4)
    ax.tick_params(length=0, pad=2)
    ax.set_title("(b) Tamper study, 13 cases", fontsize=6.4, pad=14)
    for i, c in enumerate(cases):
        for j, key in enumerate(("validate_chain_detects", "strict_audit_detects")):
            ok = c[key]
            ax.add_patch(Rectangle((j + 0.04, i + 0.1), 0.92, 0.8, color="#14907F" if ok else "#C0392B"))
            ax.text(j + 0.5, i + 0.5, "detected" if ok else "MISSED", ha="center", va="center", color="white", fontsize=5.2, fontweight="bold")
    fig.subplots_adjust(left=0.47, right=0.97, top=0.95, bottom=0.03)
    p = os.path.join(F.FIGS, "paper_fig3_results.png")
    fig.savefig(p, dpi=300, facecolor="white")
    plt.close("all")
    out["tamper"] = p

    # ---- Fig. 4 and 5 screens (crops of real screenshots)
    s19 = Image.open(F.shot("19_voter_receipt.png")).convert("RGB")
    p = os.path.join(F.FIGS, "paper_screen_receipt.png")
    from PIL import ImageDraw
    bgc = s19.getpixel((1000, 790))
    ImageDraw.Draw(s19).rectangle((1040, 805, 1195, 870), fill=bgc)
    s19.crop((505, 300, 1195, 870)).save(p)
    out["receipt"] = p
    s21 = Image.open(F.shot("21_auditor_dashboard.png")).convert("RGB")
    p = os.path.join(F.FIGS, "paper_screen_auditor.png")
    s21.crop((285, 225, 1410, 665)).save(p)
    out["auditor"] = p
    return out


def build(path):
    P = Paper()
    figs = make_figures()
    s, bt = F.BENCH_SYNC, F.BENCH_BATCH
    g, st, lat, mic = F.GROWTH, F.STAGE, F.LAT, F.MICRO
    vh = F.VALIDATE_BY_HEIGHT
    tam = F.TAMPER
    idle = F.IDLE_RUNS
    idle_lo = min(d["sync"]["throughput"] for d in idle)
    idle_hi = max(d["sync"]["throughput"] for d in idle)
    idle_ms_lo = min(d["sync"]["mean_ms"] for d in idle)
    idle_ms_hi = max(d["sync"]["mean_ms"] for d in idle)

    authors = [[n, f"Roll No. {r}", "Dept. of Computer Science and Engineering", "TKR College of Engineering & Technology", "[CITY], India", "[email]"] for n, r in F.STUDENTS]
    authors.append([F.GUIDE, f"{F.GUIDE_DESIGNATION}, project guide", "Dept. of Computer Science and Engineering", "TKR College of Engineering & Technology", "[CITY], India", "[email]"])
    P.title_block("AegisBallot: Aadhaar-Verified Electronic Voting on an Auditable Hash-Chained Ledger", authors)
    P.begin_two_columns()

    P.abstract(
        "Electronic voting must ensure that each eligible person votes once, that no recorded ballot is altered, and that the result can be checked. This paper presents AegisBallot, a local web application "
        "that binds a ballot to a voter through an Aadhaar-style check (12 digits, Verhoeff checksum, salted-hash registry lookup on synthetic data), issues a single-use token, encrypts the choice with AES-256-GCM "
        "and commits it as an Ed25519-signed block approved by two of three validators on a hash-chained ledger. Administrator, voter and auditor consoles are served by FastAPI and React. "
        f"All {F.PYTEST_TOTAL} automated tests and {F.MATRIX_PASSED} of {F.MATRIX_TOTAL} HTTP security checks passed. A benchmark of {F.N_VOTERS_BENCH} synthetic voters completed every vote, at {f1(s['mean_ms'])} ms per vote "
        f"on a loaded PC and about 16-17 ms on an idle one, and a whole voter journey over HTTP took {f1(lat['end_to_end']['mean_ms'])} ms. A tamper study found that the ledger's own integrity check detects "
        f"{F.N_TAMPER_PRODUCT} of {F.N_TAMPER} kinds of tampering and misses edits to the tally table and re-hashed edits, which a stricter audit catches. The ledger is a single-machine simulation, ballot secrecy is partial and TLS is absent.",
        ["Aadhaar verification", "audit logging", "blockchain", "electronic voting", "election integrity", "hash chain", "role-based access control"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Elections depend on public confidence that every vote is counted exactly once and cannot be altered {r:4}. Manual polling costs queues, staff and counting time, while a conventional electronic system keeps "
           "ballots in a database that an administrator could edit without trace. Blockchain offers an append-only record in which each block commits to its predecessor by a hash {r:16}, and identity binding, "
           "such as the Aadhaar number in India {r:27}, offers a way to enforce one voter, one vote. Deployed internet voting has nevertheless been broken in practice, as analyses of Estonia's system {r:10} and of the Voatz "
           "mobile application {r:12} show, so a design must be judged by what an attacker with database access can still do, not only by its description.")
    P.para("The base paper {r:1} prototypes a four-tier Ethereum voting model for Oman with biometric voter authentication and measures registration and voting transactions on a Geth test chain. "
           "Proposals that combine Aadhaar-style identity with a ledger {r:2} report a concept and a few blocks but no performance or tamper evaluation. The gap this work addresses is a deployable system that joins "
           "identity verification, a ledger, an administration workflow and an auditor, and that is measured, including where it fails. The contributions are:")
    P.para("(1) AegisBallot, a working admin/voter/auditor platform with Verhoeff-checked Aadhaar verification, single-use tokens, AES-256-GCM ballots and a three-validator, quorum-of-two ledger. "
           "(2) Four independent layers that block a second vote. (3) Measurements of vote latency and throughput for 1000 synthetic voters, of ledger-check cost against chain length, and of end-to-end HTTP latency. "
           "(4) A thirteen-case tamper study that shows what the ledger check detects and, equally, what it misses. Section II surveys the literature, Section III gives the method, Section IV the results and Section V concludes.", indent=0.2)
    P.sub("A", "System Hardware")
    P.para("All measurements ran on one desktop PC: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, no GPU, Windows 11 Pro. The machine was shared with other jobs, so about one third of the CPU was busy "
           "when the benchmark started; absolute latencies are therefore upper-ish bounds and vary between runs.")
    P.sub("B", "Software Requirements")
    e = F.ENV["libs"]
    P.para(f"Python {F.ENV['python']}; FastAPI {e['fastapi']} with SQLite through SQLAlchemy {e['sqlalchemy']}; cryptography {e['cryptography']} (AES-GCM, Ed25519, SHA-256); argon2-cffi {e['argon2-cffi']} (Argon2id {{r:23}}); "
           "React 18.3, React Router 7, TanStack Query 5, Tailwind CSS 4 and Recharts 3 built with Vite 8 on Node 24; pytest 9.1. No component contacts an external service.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para("**Base paper.** Shaikh et al. {r:1} describe four tiers: MySQL and Ethereum nodes for storage, a smart-contract tier, a C# web tier for administrators and client applications on devices that hold crypto wallets. "
           "The contract registers voters and candidates, accepts one vote per registered voter and returns counts. Using synthetic national-ID records for 1000 voters and a Geth test chain on an i7-12700 with 16 GB, "
           "the authors time registration and voting transactions run synchronously and asynchronously in batches of 10, 20, 30 and 50. Read from their Fig. 6 and Fig. 9, a registration takes about 2 s and a voting transaction "
           "about 3-4 s (the paper gives charts, not tables). They conclude that blockchain improves integrity and call for pilots, a public-trust study and Layer-2 scaling, noting Ethereum's theoretical 119.1 tx/s. "
           "Its limits are synthetic data, no real-world pilot, a public-chain setting with per-transaction delay, and no administration or audit tooling beyond monitoring.")
    P.para("**Identity-bound voting.** Chouhan and Sharma {r:2} hash an Aadhaar number or driving licence with BLAKE2b-512, add a fingerprint hash and a picture-rotation pattern, combine them with SHA-256 and record the vote "
           "hash in a chain; they show example blocks and an avalanche test whose result they find below the desired 50 %. Krishan et al. {r:5} propose a permissioned ledger with smart contracts and hashing for anonymity, "
           "and acknowledge scalability as open. Bramasto et al. {r:7} build a decentralized application on the Vexanium blockchain that passed black-box tests but implements only smart contracts.")
    P.para("**Reviews and analyses.** Jafar et al. {r:8} find privacy protection and transaction speed to be the most frequently raised issues; Ohize et al. {r:9} survey architectures and name cybersecurity risk, "
           "resource intensity and infrastructure needs as obstacles; Aswini {r:6} lists malware, server compromise, insiders and limited verifiability and points to hybrid designs with zero-knowledge proofs, "
           "homomorphic encryption and sharding; Ray et al. {r:4} study blockchain-powered voting. Real systems were examined by Springall et al. {r:10} (Estonia), Specter et al. {r:12} (Voatz) and, with open audit, "
           "Adida's Helios {r:11}. Lloyd et al. {r:3} show that on-chain voting can still hide who decides, through metagovernance among DAOs.")
    P.table("Representative related work", ["Work", "Approach", "Data", "Reported result", "Limitation"], [
        ["{r:1}", "Ethereum, Geth, C#, biometrics", "1000 synthetic voters", "~2 s reg., ~3-4 s vote (read from charts)", "No pilot; public-chain delay"],
        ["{r:2}", "Aadhaar hash + biometrics, hash chain", "Example blocks", "Avalanche test < 50 %", "No throughput or tamper test"],
        ["{r:5}", "Permissioned ledger, contracts", "None reported", "Qualitative claims", "Scalability open"],
        ["{r:7}", "DApp on Vexanium", "Black-box test", "Tests passed", "Contracts only"],
        ["{r:10}", "Analysis of Estonian i-voting", "Live system", "Attack paths found", "Not a blockchain design"],
        ["{r:12}", "Analysis of Voatz app", "Live app", "Weaknesses found", "Mobile app, closed"],
        ["{r:8}", "Review of blockchain voting", "Published proposals", "Privacy, speed most cited", "No implementation"],
        ["{r:6}", "Review of trust and security", "Literature", "Malware, insiders, verifiability", "No implementation"],
        ["{r:11}", "Open-audit web voting (Helios)", "Deployed system", "Ballot audit by voters", "No ledger, no national ID"],
    ], [0.3, 0.85, 0.6, 0.8, 0.85], size=6.2, align=["c", "l", "l", "l", "l"])
    P.para("**Lessons for the design.** Three points follow from the survey. First, identity binding needs a registry that can be checked without exposing the identifier, which argues for hashing with a secret "
           "and a checksum before any lookup. Second, the cost the base paper reports per transaction comes largely from a public-chain setting; a permissioned ledger with a small validator set removes mining and gas "
           "but also removes decentralisation, so the claim must be limited to local, auditable integrity. Third, deployed systems {r:10}, {r:12} failed in the surrounding software and keys rather than in the hash chain, "
           "so the evaluation here attacks the database, the key files and the checks themselves, not only the chain format.")
    P.para("**Consensus and cost.** Public chains such as Ethereum {r:16} settle transactions by network-wide consensus, which gives public verifiability at a cost the base paper quantifies in seconds per transaction "
           "and in a theoretical 119.1 tx/s; permissioned platforms and Byzantine-fault-tolerant protocols {r:18} trade openness for speed by limiting who validates. AegisBallot goes one step further and puts all validators "
           "on one machine, which is why its results are reported as an integrity and workflow study rather than as a decentralisation result.")
    P.para("**Gap.** The surveyed blockchain designs establish integrity models, but none combines national-ID-style identity, a complete election workflow and an auditor in one deployable system, and none reports "
           "what its integrity check would miss when an attacker can write to the database. That is the gap AegisBallot measures.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.para("**Architecture.** Fig. 1 shows the tiers. A React single-page application calls FastAPI routes under /api with a session cookie and an X-CSRF-Token header; services implement identity, voting, "
           "cryptography and the ledger; one SQLite database holds thirteen tables, and three key files (election key, validator keys, system key) live in data/. Roles are administrator, voter and auditor.")
    P.figure(figs["arch"], "AegisBallot architecture: React tier, FastAPI tier, service tier with the local ledger, and SQLite storage.")
    P.para("**Data.** There is no external dataset. The seed script creates one administrator, one auditor, twenty voters with generated Aadhaar-format numbers whose last digit is a valid Verhoeff check digit, "
           "two elections, a genesis block and three validators with Ed25519 key pairs; the benchmark generates further synthetic voters with Argon2id-hashed passwords. No real personal data is used anywhere.")
    P.para("**Identity.** The submitted number must have 12 digits and satisfy the Verhoeff dihedral-group check {r:25} (a checksum of the digits, c = d(c, p(i mod 8, n_i)) folded over the digits from the right, valid when c = 0). "
           "It is then hashed as SHA-256(salt || pepper || number) and looked up in the registry of synthetic voters; only the hash and a masked form are stored. The match must belong to the signed-in account and the voter "
           "must be eligible and not yet recorded as voted. The registry is a local synthetic table; UIDAI is not contacted and no OTP or biometric is used.")
    P.para("**Token and ballot.** A successful check issues a 256-bit random token whose SHA-256 is stored with a ten-minute expiry; it can be used once. The candidate id is encrypted as nonce || AES-256-GCM(K, id) "
           "{r:21} with a 12-byte random nonce and one server-held key. The transaction hash is")
    P.eq("h_tx = SHA-256(canonical JSON{election, ballot id, ciphertext, nonce, time}),")
    P.para("signed with Ed25519 {r:22}. A second vote is blocked at four places: the eligibility row, a unique (election, voter) participation row, the single-use token and the uniqueness of the ledger nonce and h_tx.", indent=0)
    P.para("**Ledger.** Each vote becomes one block. With the sorted transaction hashes T, the code computes")
    P.eq("M = SHA-256(concat(sort(T))),   h_b = SHA-256(canonical JSON{index, time, h_prev, M, sort(T)}).")
    P.para("M is a flat hash, not a binary Merkle tree {r:19}, so no inclusion proofs exist. Each of three validators checks the transaction schema, a new nonce, a new h_tx and the signature, and signs h_b with Ed25519; "
           "the block is committed when at least two approve, a quorum rule in the spirit of Byzantine-fault-tolerant protocols {r:18} but without any network messaging: all three validator keys are held in-process on one server. "
           "Fig. 2 gives the flow. The auditor's validate_chain recomputes M, h_b and the previous-hash link of every block.")
    P.figure(figs["flow"], "Main flow of one vote, from sign-in to receipt and audit.")
    P.para("**Casting procedure.** In pseudocode the vote path is: (a) reject unless the election is OPEN and the candidate is active in it; (b) hash the presented token and reject if it is unknown, used or expired; "
           "(c) reject if a participation row exists; (d) encrypt, hash and sign; (e) call propose_block, which raises an error unless two validators approve; (f) in one commit store the ballot, mark the token used and "
           "add the participation row. Because steps (a)-(c) precede any write and step (f) is a single database transaction, a rejected request leaves no partial state, and a failed block leaves the token usable.")
    P.para("**Implementation.** The React application has twelve page components (landing, login, results, not-found, four administrator pages, two voter pages and two auditor pages) and talks to 21 JSON routes grouped by role; "
           "the original Jinja routes and three helper endpoints remain. The administrator creates an election and every registered voter becomes eligible automatically; closing an election publishes its results to all signed-in roles. "
           "About 2,100 non-blank lines of Python implement the backend and 5,300 lines of TypeScript the interface.")
    P.para("**Privacy design.** The ballots table carries a random ballot id, the ciphertext and the nonce but no voter column, and the tally decrypts ballots only to count them. The intended separation is "
           "identity (registry), authorisation (token), anonymous ballot and ledger transaction. In the code, however, the participation table that enforces one vote stores the voter id next to the ballot id, so "
           "anyone holding the database and the single AES key can link a voter to a choice; secrecy rests on access control, not on cryptography.")
    P.para("**Threat model.** The design defends against a voter who tries to vote twice or as someone else, a client that replays or forges tokens and requests, and a casual reader of the ledger. It does not defend against "
           "an administrator or intruder with write access to the database and the key files, against denial of service, or against network eavesdropping, since traffic is plain HTTP on localhost.")
    P.para("**Security services.** Passwords use Argon2id; sessions are server-side with an HttpOnly, SameSite=lax cookie and no Secure flag; unsafe methods need the CSRF header; logins are limited to 10 per minute and "
           "verifications to 15 per minute per client IP; and every login, verification, cast, status change and audit action writes an audit-log row. The Jinja pages of the original build remain but the React app uses the JSON API.")
    P.para("**Evaluation protocol.** (i) pytest on a scratch database; (ii) an HTTP matrix of 25 security and functional checks against a live server; (iii) the product's own benchmark with 1000 synthetic voters, "
           "synchronous and in batches of 10, 20 and 30 (the code processes batches sequentially, so they are not concurrent); (iv) 300 further votes on a growing chain with timing of validate_chain and of each stage; "
           "(v) 27 voters through HTTP; and (vi) thirteen tampering cases applied inside a rolled-back transaction, each judged by validate_chain and by a stricter audit written for the study that also verifies validator and "
           "transaction signatures, recomputes transaction hashes and cross-checks the ballots table with the ledger.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.para(f"**Test conditions.** One shared PC (Section I-A), in-process timings unless stated, synthetic identities only. The system contains no learned model, so accuracy and F1 do not apply; the evidence is functional "
           f"correctness, tamper detection and latency. Results are single runs; repeated runs differed by the machine load, which is shown below rather than hidden.")
    P.table("Measured results", ["Measurement", "Setting", "Result"], [
        ["Unit tests", "pytest, scratch DB", f"{F.PYTEST_PASSED} of {F.PYTEST_TOTAL} passed ({F.PYTEST_SECONDS} s)"],
        ["HTTP checks", "RBAC, CSRF, replay, Verhoeff, 429", f"{F.MATRIX_PASSED} of {F.MATRIX_TOTAL} as expected"],
        ["Benchmark, sync", f"{F.N_VOTERS_BENCH} voters, loaded PC", f"{f1(s['throughput'])} votes/s; mean {f1(s['mean_ms'])}, median {f1(s['median_ms'])}, p95 {f1(s['p95_ms'])} ms; {s['successes']}/{F.N_VOTERS_BENCH} ok"],
        ["Benchmark, batches", "10 / 20 / 30 (sequential)", f"{f1(bt['10']['throughput'])} / {f1(bt['20']['throughput'])} / {f1(bt['30']['throughput'])} votes/s"],
        ["Benchmark, idle PC", "50-500 voters, Sept. runs", f"{f1(idle_lo)}-{f1(idle_hi)} votes/s; {f1(idle_ms_lo)}-{f1(idle_ms_hi)} ms"],
        ["Stage cost per vote", "mean of 60 votes (ms)", f"token {f1(st['authorise'])}; crypto {st['encrypt_sign_hash']:.2f}; block {f1(st['propose_block'])}; persist {f1(st['persist'])}"],
        ["validate_chain", "26 / 101 / 301 blocks", f"{f1(vh['25']['median_ms'])} / {f1(vh['100']['median_ms'])} / {f1(vh['300']['median_ms'])} ms"],
        ["HTTP, per voter", "27 voters, 127.0.0.1", f"login {f1(lat['login']['mean_ms'])}; verify {f1(lat['verify']['mean_ms'])}; cast {f1(lat['cast']['mean_ms'])}; total {f1(lat['end_to_end']['mean_ms'])} ms"],
        ["Tamper detection", f"{F.N_TAMPER} cases, {tam['chain_height']} blocks", f"validate_chain {F.N_TAMPER_PRODUCT}; stricter audit {F.N_TAMPER_STRICT}"],
    ], [0.9, 1.15, 1.35], size=6.2, align=["l", "l", "l"])
    P.para(f"**Functional and security results.** All {F.PYTEST_TOTAL} tests passed, covering the Verhoeff check, unknown and ineligible voters, duplicate votes, role routes, tampered blocks, duplicate transactions, "
           f"expired tokens, identity separation, audit logging and the encryption round trip. In the live matrix, unauthenticated calls returned 401, role violations 403, a missing CSRF header 403, a bad checksum, "
           f"an unregistered number, a forged token and a replayed token 400, another voter's valid Aadhaar number 403, and the eleventh login attempt within a minute 429; an injection-style user name was rejected with 401.")
    P.para(f"**Performance.** On an idle machine one vote cost 16-17 ms (about 60 votes/s). In the 1000-voter run on the loaded machine the mean was {f1(s['mean_ms'])} ms, with a {f1(s['max_ms'])} ms maximum, and the "
           f"three \"batch\" runs ranged from {f1(min(v['throughput'] for v in bt.values()))} to {f1(max(v['throughput'] for v in bt.values()))} votes/s; since the batches are sequential this spread is machine noise, not an effect of batching. "
           f"Of a vote's {f1(sum(st.values()))} ms, the cryptography is {st['encrypt_sign_hash']:.2f} ms; the rest is database work and the three validators' checks ({mic['ed25519_verify']['mean_ms']:.2f} ms per Ed25519 verification, "
           f"{mic['argon2id_verify']['mean_ms']:.0f} ms per Argon2id verification, which dominates the {f1(lat['login']['mean_ms'])} ms login). Per-vote cost did not grow measurably over 300 votes (first 100 votes {f1(g['per_vote_first_100']['mean_ms'])} ms, "
           f"last 100 {f1(g['per_vote_last_100']['mean_ms'])} ms), but validate_chain grows linearly, about 0.5 ms per block ({f1(vh['300']['median_ms'])} ms at 301 blocks), because each block issues its own queries.")
    P.para(f"**Run-to-run variation.** The same code gave {f1(idle_lo)}-{f1(idle_hi)} votes/s on five runs in September on an idle machine (50 to 500 voters, mean {f1(idle_ms_lo)}-{f1(idle_ms_hi)} ms per vote), "
           f"against {f1(s['throughput'])} votes/s in the 1000-voter run while other jobs used the CPU. The maximum single-vote latency of {f1(s['max_ms'])} ms in that run is most likely a scheduling stall on the shared PC rather than a property of the ledger. "
           "These numbers therefore bound the cost of a vote rather than predict it for another machine; in all three measured runs the block commit was the largest stage of a vote and the cryptography the smallest.")
    P.para("**Tamper study.** Fig. 3(b) lists the thirteen cases. validate_chain caught replaced block hashes, previous hashes, Merkle roots, timestamps and transaction hashes, deleted transactions and a deleted middle block. "
           f"It missed six: a swapped ledger payload, an edited ballots table (which changes the tally, since results are read from that table), removal of the newest block, forged validator signatures, and both re-hashed edits (T12, T13). "
           f"The stricter audit detected all {F.N_TAMPER}, at {tam['strict_audit_ms_median'] / 1000:.2f} s on {tam['chain_height']} blocks against {f1(vh['300']['median_ms'])} ms for the product check on 301. "
           "Because the validator keys sit on the same disk, an attacker who also reads data/validators.json could forge the signatures the stricter audit relies on.")
    P.figure(figs["tamper"], "Results chart. (a) Mean cost of the stages of one vote and of the HTTP steps. (b) Tamper study: which of thirteen cases are detected by the product's validate_chain() and by a stricter signature and cross-table audit.")
    P.para("**What the study means.** The ledger format itself behaves as designed: any change to a block that leaves its neighbours alone is found, and the first bad block is named. The weakness is in what the check "
           "covers. It reads transaction hashes as stored instead of recomputing them from the transaction fields, never looks at the validator signatures that make the quorum meaningful, and does not compare the "
           "table the tally reads with the ledger. A stricter audit that adds these three steps costs roughly four times as much per block (about 2.2 ms against 0.5 ms), which is acceptable for an offline audit but not for every page view; "
           "the product runs the cheap check on the public overview, the administrator dashboard and the auditor page. Even the stricter audit assumes the validator keys were not copied, which the single-machine design cannot promise.")
    P.para("**Reproducibility.** Every number above comes from scripts in the repository (run_experiments.py, the product's run_benchmark, pytest), run against scratch databases so the demonstration data was untouched; "
           "the JSON outputs are stored with the code. The HTTP figures exclude the browser and the Vite proxy, and the in-process figures exclude the network entirely.")
    P.para("**Output screens.** Fig. 4 shows the receipt after a vote: ballot id, transaction hash, block number and block hash, taken from the running application with 200 synthetic voters and 213 blocks. "
           "Fig. 5 shows the auditor's console: the chain verified from genesis, the three validators with the two-of-three rule, and the tamper demonstration, which only compares a hash in a cloned copy and does not re-run the integrity check.")
    P.figure(figs["receipt"], "Output screen: voter receipt after a recorded vote (block #212).")
    P.figure(figs["auditor"], "Output screen: auditor console with chain integrity, validators and the tamper-detection demonstration.")
    P.para("**Objectives against outcomes.** Identity verification with a checksum and registry: met on a synthetic registry, with no registration function. One voter one vote: met, tested by duplicate-vote, replay and wrong-identity cases. Immutable recording: "
           "met only in the weak sense that edits to blocks are detected when they leave the neighbours alone; the six missed cases show it is not tamper-proof against a database writer. Administration portal: met for elections and candidates, while polling windows are stored but not enforced. "
           "Results with a chronological audit trail: met. RBAC and input validation: met; TLS: not met; integrity and performance evaluation: done, with the limits stated in this section.")
    P.para("**Comparison with the base paper.** The base paper's per-transaction times (about 2 s registration, 3-4 s voting, read from its charts) were measured on a Geth test chain with C# clients, biometric "
           f"authentication and a different i7-12700 machine; AegisBallot's mean in-process vote took {f1(s['mean_ms'])} ms on a loaded PC and {f1(lat['cast']['mean_ms'])} ms for the cast call over HTTP. These are orders of magnitude apart, "
           "but they are not comparable: a local simulated ledger without network consensus, mining or gas does far less work, and gives none of the decentralisation or public verifiability that a public chain provides. "
           "The datasets also differ (both synthetic, 1000 voters in the benchmark) and the definitions differ (the base paper times registration and vote separately, here a vote includes token issue).")
    P.para("**Failure cases and limits.** (1) The integrity check misses six of thirteen tamper cases. (2) Ballot secrecy is partial: the participation table stores voter and ballot ids together, one AES key protects all ciphertext, "
           "and an administrator can read a live tally of an open election. (3) The cookie has no Secure flag and no TLS is configured, although the batch objectives call for TLS. (4) The login limiter is per IP, so users behind one address share 10 logins a minute. "
           "(5) Concurrent voting, a penetration test and a user study were not carried out. (6) The registry is synthetic; real Aadhaar integration is out of scope and its legal limits {r:27} apply.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion and Future Scope")
    P.para(f"AegisBallot meets the batch objectives of Aadhaar-style verification, one voter one vote, an immutable-by-design ledger, an administration portal, results with an audit trail and RBAC, and it measures its own integrity and performance; "
           f"the objective of TLS is not met. Its key finding is that a hash-chained ledger is only as trustworthy as the check run over it: the shipped check detects {F.N_TAMPER_PRODUCT} of {F.N_TAMPER} tamper cases while a stricter audit detects all. "
           "Limits are the single-machine ledger, partial secrecy, synthetic identities and a shared test PC. Future work is to verify signatures, transaction hashes and the ballots table in the product, use a true Merkle tree and "
           "per-election keys, separate voter and ballot records, add TLS, a second factor and network validators with a real consensus protocol {r:18}, and run concurrent-load, penetration and usability tests.")

    P.references()
    return P.save(path)


if __name__ == "__main__":
    out = os.path.join(F.BATCH, "19.IEEE_Paper.docx")
    print("wrote", build(out))
