"""Draw the AegisBallot design diagrams into docs/diagrams/ (PNG, 150 dpi, matplotlib only).

Every box and arrow mirrors the code: app/api_v1.py (JSON API), app/main.py (legacy HTML routes), app/services/voting_service.py,
app/ledger/ledger.py, app/identity/, app/security/ and app/models/models.py (13 tables).

    python scripts/docs_build/make_diagrams.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dgm_lib import *  # noqa: E402,F401,F403
from matplotlib.patches import Circle, Rectangle  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------------------------------
def system_architecture():
    fig, ax = canvas(10, 8.6, 100, 86)
    panel(ax, 2, 68, 96, 17, "Presentation tier - React 18 + Vite SPA (port 5401), Vite proxy /api -> backend", PALE_BLUE, BLUE)
    box(ax, 17, 74, 26, 10, "Public pages\nLanding - Login\nResults (closed elections)", BLUE, fs=7.6)
    box(ax, 44, 74, 24, 10, "Role consoles\nAdmin - Voter - Auditor\nReact Router 7 guards", BLUE, fs=7.6)
    box(ax, 68, 74, 22, 10, "lib/api.ts, queries.ts\nAxios + TanStack Query\nX-CSRF-Token header", BLUE, fs=7.2)
    box(ax, 89, 74, 17, 10, "UI kit\nTailwind 4, Radix\nRecharts, light/dark", BLUE, fs=7.2)

    panel(ax, 2, 47, 96, 19, "Application tier - FastAPI (port 8401): app/api_v1.py (JSON) + app/main.py (legacy Jinja pages)", PALE_TEAL, TEAL)
    box(ax, 15, 54, 24, 11, "Auth + guards\n/api/auth/login|me|logout\nsession cookie, CSRF,\nRBAC, rate limit", TEAL, fs=7.0)
    box(ax, 41, 54, 24, 11, "Admin API\nelections, candidates,\nstatus, benchmarks,\nresults", TEAL, fs=7.2)
    box(ax, 67, 54, 24, 11, "Voter API\nverify Aadhaar -> token\ncast ballot -> receipt\nelections list", TEAL, fs=7.2)
    box(ax, 89, 54, 17, 11, "Auditor API\nverify chain\ntamper test\nblocks, logs", TEAL, fs=7.2)

    panel(ax, 2, 20, 96, 25, "Service tier - voting_service, election_service, audit, identity provider, security, ledger", PALE_ORANGE, ORANGE)
    box(ax, 15, 33, 25, 11, "Identity\nDemoAadhaarProvider\n12 digits - Verhoeff -\nsalted-hash lookup", ORANGE, fs=7.0)
    box(ax, 42, 33, 25, 11, "Voting service\nissue_authorization\nverify_authorization\ncast_vote, tally_results", ORANGE, fs=7.0)
    box(ax, 69, 33, 25, 11, "Crypto\nArgon2id - AES-256-GCM\nSHA-256 - Ed25519\nsecrets, hash_token", ORANGE, fs=7.0)
    box(ax, 90, 33, 15, 11, "Audit log\nlog_event()", ORANGE, fs=7.2)
    box(ax, 50, 24.5, 86, 5.5, "Local permissioned ledger (ledger.py): propose_block -> 3 validators, quorum 2 of 3, Ed25519 block signatures -> validate_chain", NAVY, fs=7.4)

    panel(ax, 2, 1.5, 96, 16.5, "Data tier - SQLite (SQLAlchemy 2) + key files in data/ - nothing leaves the machine", LIGHT, "#B7C3D3")
    store(ax, 17, 8, 28, 9, "users, voter_profiles, elections,\ncandidates, voter_eligibility", fs=7.0)
    store(ax, 45, 8, 24, 9, "voting_authorizations, ballots,\nvoter_participation", fs=7.0)
    store(ax, 71, 8, 24, 9, "ledger_blocks, ledger_transactions,\nvalidator_nodes", fs=7.0)
    store(ax, 91, 8, 14, 9, "audit_logs\nbenchmark_runs", fs=6.8)

    arrow(ax, (50, 68), (50, 66), "HTTP + JSON (cookie session)", lo=(19, 0), fs=7.2, color=NAVY)
    arrow(ax, (50, 47), (50, 45), "Python calls", lo=(8, 0), fs=7.2, color=NAVY)
    arrow(ax, (50, 20), (50, 17.2), "SQLAlchemy sessions", lo=(11, 0), fs=7.2, color=NAVY)
    save(fig, OUT / "01_system_architecture.png")


# --------------------------------------------------------------------------------------------------
def high_level_workflow():
    fig, ax = canvas(10, 6.2, 100, 62)
    ax.text(50, 59.2, "Election life cycle and one vote, end to end", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    top = [("Admin creates\nelection", "title, window,\ncandidates", BLUE), ("Open election", "status OPEN;\nall voters eligible", BLUE),
           ("Voter signs in", "Argon2id check,\nsession + CSRF", TEAL), ("Verify Aadhaar", "format, Verhoeff,\nregistry, own id", TEAL),
           ("One-time token", "256-bit, hashed,\n10 min, single use", TEAL)]
    xs = [10 + i * 20 for i in range(5)]
    for x, (t, d, c) in zip(xs, top):
        box(ax, x, 46, 17, 13, f"{t}\n{d}", c, fs=7.6)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 8.7, 46), (b - 8.7, 46), color=NAVY)
    bot = [("Close election", "admin sets CLOSED;\nresults published", ORANGE), ("Auditor checks", "validate_chain,\nblocks, audit log", PURPLE),
           ("Receipt", "ballot id, tx hash,\nblock no., block hash", NAVY), ("Block committed", "3 validators sign,\n2 of 3 needed", PURPLE),
           ("Cast ballot", "choice encrypted\nAES-256-GCM, tx signed", ORANGE)]
    bx = [10 + i * 20 for i in range(5)]
    for x, (t, d, c) in zip(bx, bot):
        box(ax, x, 18, 17, 13, f"{t}\n{d}", c, fs=7.6)
    for a, b in zip(bx[:-1], bx[1:]):
        arrow(ax, (b - 8.7, 18), (a + 8.7, 18), color=NAVY)
    arrow(ax, (xs[-1], 39.5), (bx[-1], 24.5), color=NAVY)
    ax.text(50, 4.5, "Rejected at any step (bad Aadhaar, wrong voter, used or expired token, closed election, replay) -> HTTP 400/403 and an audit-log entry",
            ha="center", fontsize=7.6, color=GREY, style="italic")
    save(fig, OUT / "02_high_level_workflow.png")


# --------------------------------------------------------------------------------------------------
def dfd0():
    fig, ax = canvas(10, 6.4, 100, 64)
    circle(ax, 50, 32, 12.5, "AegisBallot\n(voting platform)", NAVY, fs=10)
    box(ax, 11, 54, 16, 8, "Voter", WHITE, tc=INK, ec=BLUE, fs=9, bold=True)
    box(ax, 11, 32, 16, 8, "Election\nadministrator", WHITE, tc=INK, ec=BLUE, fs=8.5, bold=True)
    box(ax, 11, 10, 16, 8, "Auditor", WHITE, tc=INK, ec=BLUE, fs=9, bold=True)
    box(ax, 89, 50, 18, 9, "Voter registry\n(synthetic Aadhaar)", WHITE, tc=INK, ec=TEAL, fs=7.8, bold=True)
    box(ax, 89, 14, 18, 9, "Ledger, ballots\nand audit store", WHITE, tc=INK, ec=TEAL, fs=7.8, bold=True)
    # voter
    arrow(ax, (19, 56), (41, 40), "", lo=(0, 0), color=NAVY)
    ax.text(21, 54, "login, Aadhaar number,\ncandidate choice", fontsize=7.0, color=NAVY, ha="left", va="top")
    arrow(ax, (40.5, 36.5), (19, 52.5), "", color=ORANGE)
    ax.text(38, 47.5, "receipt, results", fontsize=7.0, color=ORANGE, ha="right")
    # admin
    arrow(ax, (19, 34), (37.5, 34), "", color=NAVY)
    ax.text(28, 35.4, "elections, candidates,\nstatus changes", fontsize=7.0, color=NAVY, ha="center", va="bottom")
    arrow(ax, (37.5, 30), (19, 30), "", color=ORANGE)
    ax.text(28, 28.6, "turnout, tallies", fontsize=7.0, color=ORANGE, ha="center", va="top")
    # auditor
    arrow(ax, (19, 12), (41, 24.5), "", color=NAVY)
    ax.text(21, 6.2, "integrity check,\ntamper-test request", fontsize=7.0, color=NAVY, ha="left", va="center")
    arrow(ax, (40.5, 27.5), (19, 8.5), "", color=ORANGE)
    ax.text(38, 17.5, "chain status, blocks,\naudit log", fontsize=7.0, color=ORANGE, ha="right", va="center")
    # stores
    arrow(ax, (80, 48), (60.5, 38.5), "", color=TEAL)
    ax.text(75, 47, "registry lookup\n(hashed Aadhaar)", fontsize=7.0, color=TEAL, ha="center")
    arrow(ax, (60.5, 26), (80, 16.5), "", color=TEAL)
    ax.text(70, 14.5, "blocks, ballots, log entries", fontsize=7.0, color=TEAL, ha="center")
    ax.text(50, 1.6, "Context diagram (level 0). No external service is contacted; the 'registry' is a local table.", ha="center", fontsize=8, color=GREY, style="italic")
    save(fig, OUT / "03_dfd_level0.png")


def dfd1():
    fig, ax = canvas(10, 7.2, 100, 72)
    box(ax, 7, 56, 12, 7, "Voter", WHITE, tc=INK, ec=BLUE, fs=9, bold=True)
    box(ax, 7, 34, 12, 7, "Admin", WHITE, tc=INK, ec=BLUE, fs=9, bold=True)
    box(ax, 7, 12, 12, 7, "Auditor", WHITE, tc=INK, ec=BLUE, fs=9, bold=True)
    circle(ax, 26, 56, 6.6, "1.0\nAuthenticate", BLUE, fs=7.2)
    circle(ax, 46, 56, 6.6, "2.0\nVerify\nidentity", TEAL, fs=7.2)
    circle(ax, 66, 56, 6.6, "3.0\nIssue\nauthorization", TEAL, fs=7.2)
    circle(ax, 66, 34, 6.6, "4.0\nCast and\nencrypt", ORANGE, fs=7.2)
    circle(ax, 46, 34, 6.6, "5.0\nPropose and\ncommit block", ORANGE, fs=7.2)
    circle(ax, 26, 34, 6.6, "6.0\nManage\nelections", BLUE, fs=7.2)
    circle(ax, 46, 12, 6.6, "7.0\nAudit and\nverify chain", PURPLE, fs=7.2)
    circle(ax, 88, 12, 6.6, "8.0\nTally and\npublish", PURPLE, fs=7.2)
    store(ax, 46, 68, 22, 5.5, "D1 users + registry", fs=6.8)
    store(ax, 78, 68, 16, 5.5, "D2 tokens", fs=7.0)
    store(ax, 88, 34, 18, 7, "D3 ballots +\nparticipation", fs=6.8)
    store(ax, 66, 12, 14, 6.5, "D4 ledger", fs=7.0)
    store(ax, 26, 21.5, 18, 6, "D6 elections", fs=6.8)
    arrow(ax, (13, 56), (19.4, 56), "credentials", lo=(0, 2.3), fs=6.8, color=NAVY)
    arrow(ax, (32.6, 56), (39.4, 56), "session", lo=(0, 2.3), fs=6.8, color=NAVY)
    arrow(ax, (52.6, 56), (59.4, 56), "verified", lo=(0, 2.3), fs=6.8, color=NAVY)
    arrow(ax, (46, 65), (46, 62.8), "", color=TEAL)
    arrow(ax, (70, 62.4), (74, 65.2), "", color=TEAL)
    arrow(ax, (66, 49.4), (66, 40.6), "token + choice", lo=(8, 0), fs=6.8, color=NAVY)
    arrow(ax, (59.4, 34), (52.6, 34), "signed tx", lo=(0, 2.3), fs=6.8, color=NAVY)
    arrow(ax, (72.6, 34), (79, 34), "ballot", lo=(0, 2.3), fs=6.8, color=TEAL)
    arrow(ax, (50.5, 29), (62, 14.5), "block, hashes", lo=(5, 2.5), fs=6.8, color=TEAL)
    arrow(ax, (59, 12), (52.6, 12), "read", lo=(0, 2.3), fs=6.8, color=TEAL)
    arrow(ax, (88, 27.5), (88, 18.6), "ballots", lo=(5, 0), fs=6.8, color=TEAL)
    arrow(ax, (13, 34), (19.4, 34), "settings", lo=(0, 2.3), fs=6.8, color=NAVY)
    arrow(ax, (26, 27.4), (26, 24.6), "", color=TEAL)
    arrow(ax, (13, 12), (39.4, 12), "verify / tamper request", lo=(0, 2.3), fs=6.8, color=NAVY)
    arrow(ax, (39.4, 9.6), (13, 9.6), "chain status, blocks, audit log", lo=(0, -2.4), fs=6.8, color=ORANGE)
    ax.text(88, 2.2, "results to every\nsigned-in role", ha="center", fontsize=6.8, color=ORANGE)
    ax.text(50, 3.0, "Notes: every process appends to the audit log (table audit_logs, not drawn); the receipt returns from 4.0 to the voter;\nprocess 6.0 also creates the eligibility rows read by 3.0 and 4.0.",
            fontsize=7.0, ha="center", color=GREY, style="italic")
    save(fig, OUT / "04_dfd_level1.png")


def dfd2():
    fig, ax = canvas(10, 6.6, 100, 66)
    ax.text(50, 63, "DFD level 2 - process 4.0 and 5.0 expanded (voting_service.cast_vote, ledger.propose_block)", ha="center", fontsize=9.4, color=NAVY, fontweight="bold")
    circle(ax, 11, 48, 6.4, "4.1\nCheck election\nand candidate", BLUE, fs=6.2)
    circle(ax, 31, 48, 6.4, "4.2\nVerify token\n(hash, unused,\nnot expired)", BLUE, fs=5.8)
    circle(ax, 51, 48, 6.4, "4.3\nNo prior\nparticipation", BLUE, fs=6.2)
    circle(ax, 71, 48, 6.4, "4.4\nEncrypt choice\nAES-256-GCM", ORANGE, fs=6.0)
    circle(ax, 91, 48, 6.4, "4.5\nHash + sign\ntransaction", ORANGE, fs=6.2)
    circle(ax, 91, 24, 6.4, "5.1\nSchema, nonce,\ntx_hash unique", TEAL, fs=5.8)
    circle(ax, 71, 24, 6.4, "5.2\nEach validator\nchecks + signs", TEAL, fs=6.0)
    circle(ax, 51, 24, 6.4, "5.3\nQuorum\n>= 2 of 3?", TEAL, fs=6.2)
    circle(ax, 31, 24, 6.4, "5.4\nCommit block\n+ transactions", TEAL, fs=6.0)
    circle(ax, 11, 24, 6.4, "4.6\nSave ballot,\nmark token used,\nparticipation", ORANGE, fs=5.6)
    store(ax, 22, 58.5, 22, 4.5, "D6 elections, candidates", fs=6.6)
    store(ax, 50, 58.5, 18, 4.5, "D2 tokens", fs=6.6)
    store(ax, 78, 58.5, 22, 4.5, "D3 participation", fs=6.6)
    store(ax, 71, 8, 22, 6, "D4 ledger (blocks, txs)", fs=6.6)
    store(ax, 31, 8, 22, 6, "D3 ballots", fs=6.8)
    for a, b in ((17.4, 24.6), (37.4, 44.6), (57.4, 64.6), (77.4, 84.6)):
        arrow(ax, (a, 48), (b, 48), color=NAVY)
    arrow(ax, (91, 41.6), (91, 30.4), "signed tx", lo=(5.5, 0), fs=6.4, color=NAVY)
    for a, b in ((84.6, 77.4), (64.6, 57.4), (44.6, 37.4)):
        arrow(ax, (a, 24), (b, 24), color=NAVY)
    arrow(ax, (24.6, 24), (17.4, 24), "block no.,\nhash", lo=(0, 3.4), fs=6.2, color=TEAL)
    arrow(ax, (20, 56), (12, 54.4), "", color=TEAL, ls="--")
    arrow(ax, (48, 56), (32, 54.4), "", color=TEAL, ls="--")
    arrow(ax, (74, 56), (52, 54.4), "", color=TEAL, ls="--")
    arrow(ax, (31, 17.6), (31, 11), "", color=TEAL)
    arrow(ax, (11, 17.6), (22, 9.5), "ballot row", lo=(-4, -1.5), fs=6.2, color=TEAL)
    arrow(ax, (31, 17.6), (66, 10.5), "", color=TEAL, ls="--")
    arrow(ax, (71, 17.6), (71, 11), "", color=TEAL)
    ax.text(50, 36, "Rejections at 4.1 - 4.3 or 5.1 / 5.3 stop the flow, write an audit entry and return HTTP 400 - nothing is stored", ha="center", fontsize=7.2, color=ORANGE, style="italic")
    save(fig, OUT / "05_dfd_level2.png")


# --------------------------------------------------------------------------------------------------
def uml_class_diagram():
    fig, ax = canvas(10, 10.4, 100, 104)
    def cls(x, y, w, name, attrs, hdr, meth=(), stereo=None):
        return uml_class(ax, x, y, w, name, list(attrs), list(meth), hdr=hdr, fs=6.8, stereotype=stereo)
    # row 1
    user = cls(1, 102, 22, "User", ["id, username", "password_hash", "role ADMIN|VOTER|AUDITOR", "display_name, email"], NAVY)
    vp = cls(26, 102, 24, "VoterProfile", ["user_id (unique)", "full_name", "aadhaar_hash (unique)", "aadhaar_masked", "is_verified"], NAVY)
    el = cls(53, 102, 22, "Election", ["id, title, description", "start_time, end_time", "status DRAFT|OPEN|", "       PAUSED|CLOSED"], BLUE)
    ca = cls(78, 102, 21, "Candidate", ["election_id", "name, party", "manifesto", "is_active"], BLUE)
    # row 2
    ve = cls(1, 76, 22, "VoterEligibility", ["election_id", "voter_user_id", "is_eligible", "UNIQUE(election,voter)"], TEAL)
    va = cls(26, 76, 24, "VotingAuthorization", ["election_id, voter_user_id", "token_hash (unique)", "is_used, expires_at", "UNIQUE(election,voter)"], TEAL)
    ba = cls(53, 76, 22, "Ballot", ["ballot_id (unique)", "encrypted_choice", "nonce (unique)", "tx_hash, block_index", "(no voter id)"], ORANGE)
    vpar = cls(78, 76, 21, "VoterParticipation", ["election_id", "voter_user_id", "ballot_id", "UNIQUE(election,voter)"], ORANGE)
    # row 3
    vn = cls(1, 50, 22, "ValidatorNode", ["node_id (unique)", "public_key (Ed25519)", "is_active"], PURPLE)
    lb = cls(26, 50, 24, "LedgerBlock", ["block_index (unique)", "timestamp", "previous_hash", "merkle_root, block_hash", "validator_signatures", "transaction_count"], PURPLE)
    lt = cls(53, 50, 22, "LedgerTransaction", ["tx_hash (unique)", "block_index -> block", "election_id, ballot_id", "encrypted_payload", "nonce (unique)", "signature"], PURPLE)
    al = cls(78, 50, 21, "AuditLog", ["timestamp", "actor_user_id, username", "action, entity", "details, ip_address"], GREY)
    # row 4: modules
    cls(1, 24, 30, "VotingService (module)", [], NAVY, ["issue_authorization()", "verify_authorization()", "cast_vote()", "tally_results()"], "service")
    cls(35, 24, 30, "Ledger (module)", [], PURPLE, ["init_validators(), genesis", "propose_block()", "validate_chain()", "tamper_test_clone()"], "service")
    cls(69, 24, 30, "IdentityVerificationProvider", [], TEAL, ["verify(aadhaar, db)  {abstract}", "DemoAadhaarProvider", "Verhoeff.validate()"], "interface")
    ar = dict(color=NAVY, lw=1.1, style="-")
    arrow(ax, (23, 96), (26, 96), "1..1", fs=6.4, lo=(0, 1.4), **ar)
    arrow(ax, (75, 96), (78, 96), "1..*", fs=6.4, lo=(0, 1.4), **ar)
    arrow(ax, (12, user[1]), (12, 76), "1..*", fs=6.4, lo=(3, 0), **ar)
    arrow(ax, (20, user[1]), (31, 76), "1..*", fs=6.4, lo=(-2, 0), **ar)
    arrow(ax, (64, el[1]), (64, 76), "1..*", fs=6.4, lo=(3, 0), **ar)
    arrow(ax, (72, el[1]), (85, 76), "1..*", fs=6.4, lo=(2, 0), **ar)
    arrow(ax, (23, 44), (26, 44), "signs", fs=6.2, lo=(0, 1.5), **ar)
    arrow(ax, (50, 44), (53, 44), "1..*", fs=6.4, lo=(0, 1.5), **ar)
    arrow(ax, (64, ba[1]), (64, 50), "same ballot_id", fs=6.2, lo=(7, 0), color=GREY, lw=0.9, style="-", ls="--")
    ax.text(1, 3.8, "Lines are foreign-key or logical associations. Ballot has no voter column: the voter-to-ballot link exists only in VoterParticipation.", fontsize=6.9, color=GREY)
    ax.text(1, 1.2, "Class diagram of 12 of the 13 SQLAlchemy models (BenchmarkRun omitted) plus the service modules and the identity-provider interface that operate on them.", fontsize=6.9, color=GREY)
    save(fig, OUT / "06_uml_class.png")


def sequence_diagram():
    fig, ax = canvas(10, 8.6, 100, 86)
    ax.text(50, 83.5, "Sequence: Aadhaar verification and casting one ballot (React -> /api/voter/...)", ha="center", fontsize=9.8, color=NAVY, fontweight="bold")
    actors = [("Voter\n(browser)", 7, BLUE), ("FastAPI\napi_v1", 24, TEAL), ("Identity\nprovider", 41, TEAL), ("Voting\nservice", 58, ORANGE), ("Ledger\n(3 validators)", 75, PURPLE), ("SQLite", 92, GREY)]
    for n, x, c in actors:
        box(ax, x, 77, 14, 6.5, n, c, fs=7.2)
        ax.plot([x, x], [73.5, 3], color="#B7C3D3", lw=1.2, ls="--", zorder=1)
    X = {n: x for n, x, _ in actors}
    steps = [
        ("Voter\n(browser)", "FastAPI\napi_v1", 70, "POST /verify {aadhaar} + cookie + CSRF", 0),
        ("FastAPI\napi_v1", "Identity\nprovider", 66, "verify(): 12 digits, Verhoeff", 0),
        ("Identity\nprovider", "SQLite", 62.2, "lookup salted SHA-256 hash", 0),
        ("FastAPI\napi_v1", "Voting\nservice", 58.4, "own id? eligible? not voted? issue token", 0),
        ("Voting\nservice", "SQLite", 54.6, "store SHA-256(token), expires +10 min", 0),
        ("FastAPI\napi_v1", "Voter\n(browser)", 50.8, "200 {auth_token, candidates}", 2),
        ("Voter\n(browser)", "FastAPI\napi_v1", 46.8, "POST /cast {candidate_id, token}", 0),
        ("FastAPI\napi_v1", "Voting\nservice", 43, "cast_vote(): election OPEN, token valid", 0),
        ("Voting\nservice", "Voting\nservice", 39.2, "AES-GCM encrypt; tx_hash; Ed25519 sign", 1),
        ("Voting\nservice", "Ledger\n(3 validators)", 35.2, "propose_block([tx])", 0),
        ("Ledger\n(3 validators)", "SQLite", 31.2, "nonce / tx_hash unique? write block", 0),
        ("Ledger\n(3 validators)", "Voting\nservice", 27.2, "block (hash, index), 2+ signatures", 2),
        ("Voting\nservice", "SQLite", 23.2, "ballot, token used, participation; commit", 0),
        ("FastAPI\napi_v1", "SQLite", 19.2, "audit_logs: vote_cast", 0),
        ("FastAPI\napi_v1", "Voter\n(browser)", 15.2, "200 receipt {ballot_id, tx_hash, block}", 2),
    ]
    for a, b, y, label, kind in steps:
        xa, xb = X[a], X[b]
        if kind == 1:
            ax.add_patch(Rectangle((xa - 1.2, y - 2), 2.4, 4, fc=PALE_ORANGE, ec=ORANGE, zorder=2))
            ax.text(xa + 2.5, y, label, fontsize=6.9, va="center", color=INK)
        else:
            arrow(ax, (xa, y), (xb, y), label, color=NAVY if kind == 0 else ORANGE, ls="-" if kind == 0 else "--", lo=(0, 1.8), fs=6.6, bg=True)
    ax.text(50, 7.5, "Any failed check raises HTTP 400/403, writes vote_rejected / aadhaar_verify_failed to the audit log and stores nothing.", ha="center", fontsize=7.4, color=GREY, style="italic")
    save(fig, OUT / "07_sequence_vote.png")


def use_case():
    fig, ax = canvas(10, 7.4, 100, 74)
    ax.add_patch(Rectangle((24, 4), 54, 68, fc="#F7F9FC", ec=NAVY, lw=1.4, zorder=1))
    ax.text(51, 69.2, "AegisBallot", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    ucs = [("Sign in / sign out", 64, "all"), ("Verify Aadhaar identity", 58, "v"), ("Cast an encrypted ballot", 52, "v"), ("View receipt and election history", 46, "v"),
           ("Create and configure election", 40, "a"), ("Add / deactivate candidates", 34, "a"), ("Open, pause, close election", 28, "a"),
           ("View results and benchmarks", 22, "a"), ("Verify chain integrity, browse blocks", 16, "u"), ("Run tamper demo, read audit log", 10, "u")]
    for t, y, _ in ucs:
        ellipse(ax, 51, y, 38, 4.8, t, fs=7.6)
    for (nm, x, y, c) in (("Voter", 10, 52, BLUE), ("Administrator", 10, 24, TEAL), ("Auditor", 91, 14, PURPLE)):
        ax.add_patch(Circle((x, y + 6), 2.2, fc="white", ec=c, lw=1.6, zorder=3))
        ax.plot([x, x], [y + 3.8, y - 2], color=c, lw=1.6, zorder=3)
        ax.plot([x - 3, x + 3], [y + 1.5, y + 1.5], color=c, lw=1.6, zorder=3)
        ax.plot([x, x - 2.5], [y - 2, y - 7], color=c, lw=1.6, zorder=3)
        ax.plot([x, x + 2.5], [y - 2, y - 7], color=c, lw=1.6, zorder=3)
        ax.text(x, y - 9.5, nm, ha="center", fontsize=8.5, color=c, fontweight="bold")
    for t, y, w in ucs:
        if w in ("v", "all"):
            arrow(ax, (14, 55), (32, y), color=BLUE, lw=0.8, style="-")
        if w in ("a", "all"):
            arrow(ax, (14, 27), (32, y), color=TEAL, lw=0.8, style="-")
        if w in ("u", "all"):
            arrow(ax, (87, 17), (70, y), color=PURPLE, lw=0.8, style="-")
    ax.text(51, 1.6, "'Cast an encrypted ballot' includes 'Verify Aadhaar identity'; results of a CLOSED election are readable by every signed-in role.", fontsize=7.2, ha="center", color=GREY)
    save(fig, OUT / "08_use_case.png")


def er_diagram():
    fig, ax = canvas(10, 9.2, 100, 92)
    ax.text(50, 89.5, "Entity-relationship diagram - the 13 tables of data/aegisballot.db", ha="center", fontsize=9.6, color=NAVY, fontweight="bold")
    def ent(x, y, w, name, attrs, c):
        return uml_class(ax, x, y, w, name, attrs, [], hdr=c, fs=6.6)
    users = ent(1, 86, 23, "users", ["PK id", "username (unique)", "password_hash", "role", "display_name, email"], NAVY)
    vprof = ent(27, 86, 23, "voter_profiles", ["PK id", "FK user_id (unique)", "aadhaar_hash (unique)", "aadhaar_masked", "full_name, dob, address"], NAVY)
    elec = ent(53, 86, 22, "elections", ["PK id", "title, description", "start_time, end_time", "status", "FK created_by"], BLUE)
    cand = ent(78, 86, 21, "candidates", ["PK id", "FK election_id", "name, party", "manifesto, is_active"], BLUE)
    veli = ent(1, 58, 23, "voter_eligibility", ["PK id", "FK election_id", "FK voter_user_id", "is_eligible", "UQ(election, voter)"], TEAL)
    vaut = ent(27, 58, 23, "voting_authorizations", ["PK id", "FK election_id", "FK voter_user_id", "token_hash (unique)", "is_used, expires_at", "UQ(election, voter)"], TEAL)
    ball = ent(53, 58, 22, "ballots", ["PK id", "FK election_id", "ballot_id (unique)", "encrypted_choice", "nonce (unique)", "tx_hash, block_index"], ORANGE)
    vpar = ent(78, 58, 21, "voter_participation", ["PK id", "FK election_id", "FK voter_user_id", "ballot_id", "UQ(election, voter)"], ORANGE)
    lbl = ent(1, 30, 23, "ledger_blocks", ["PK id", "block_index (unique)", "timestamp", "previous_hash", "merkle_root", "block_hash (unique)"], PURPLE)
    ltx = ent(27, 30, 23, "ledger_transactions", ["PK id", "tx_hash (unique)", "FK block_index", "FK election_id", "ballot_id, nonce (uq)", "encrypted_payload", "signature"], PURPLE)
    vnod = ent(53, 30, 22, "validator_nodes", ["PK id", "node_id (unique)", "public_key", "is_active"], PURPLE)
    alog = ent(78, 30, 21, "audit_logs", ["PK id", "timestamp", "FK actor_user_id", "action, entity_type", "details, ip_address"], GREY)
    ar = dict(color=NAVY, lw=1.1, style="-")
    arrow(ax, (24, 80), (27, 80), "1 : 1", fs=6.4, lo=(0, 1.3), **ar)
    arrow(ax, (75, 80), (78, 80), "1 : n", fs=6.4, lo=(0, 1.3), **ar)
    arrow(ax, (12, users[1]), (12, 58), "1 : n", fs=6.4, lo=(3, 0), **ar)
    arrow(ax, (20, users[1]), (31, 58), "1 : n", fs=6.4, lo=(-2, 0), **ar)
    arrow(ax, (64, elec[1]), (64, 58), "1 : n", fs=6.4, lo=(3, 0), **ar)
    arrow(ax, (72, elec[1]), (85, 58), "1 : n", fs=6.4, lo=(2, 0), **ar)
    arrow(ax, (24, 22), (27, 22), "1 : n", fs=6.4, lo=(0, 1.4), **ar)
    arrow(ax, (64, ball[1]), (64, 30), "same ballot_id", fs=6.2, lo=(7, 0), color=GREY, lw=0.9, style="-", ls="--")
    ax.text(50, 2.6, "benchmark_runs (the 13th table: id, timestamp, total_ops, sync/async duration and throughput, mean and p95 latency, details_json) stands alone.\n"
            "Only voter_participation joins a voter to a ballot id; ballots carries no voter column. voter_eligibility, voting_authorizations and\nvoter_participation each also reference users and elections (FK election_id, FK voter_user_id).",
            ha="center", fontsize=6.9, color=GREY)
    save(fig, OUT / "09_er_diagram.png")


def flowchart():
    fig, ax = canvas(10, 9.4, 100, 94)
    ax.text(50, 91.5, "Core algorithm - casting a ballot (cast_vote + propose_block)", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    box(ax, 40, 86, 44, 5, "Input: election id, voter id, one-time token, candidate id", NAVY, fs=7.6)
    diamond(ax, 40, 77.5, 46, 8.5, "Election OPEN and candidate active\nin this election?", fs=7.4)
    diamond(ax, 40, 66.5, 46, 8.5, "Token hash matches, unused,\nnot expired?", fs=7.4)
    diamond(ax, 40, 55.5, 46, 8.5, "No participation row for\nthis (election, voter)?", fs=7.4)
    box(ax, 40, 45.5, 46, 6.2, "ciphertext = nonce || AES-256-GCM(key, candidate id);  ballot_id, nonce random", TEAL, fs=7.0)
    box(ax, 40, 37, 46, 6.2, "tx_hash = SHA-256(canonical JSON of tx);  signature = Ed25519(system key, tx_hash)", TEAL, fs=7.0)
    diamond(ax, 40, 27, 46, 8.5, "Block valid for each validator?\n(schema, new nonce, new tx_hash, signature)", fs=7.0)
    diamond(ax, 40, 16.5, 46, 8.5, "At least 2 of 3 validators\napprove?", fs=7.4)
    box(ax, 40, 6.5, 46, 6.2, "Commit block; save ballot; mark token used;\nadd participation row", ORANGE, fs=7.0)
    box(ax, 86, 77.5, 22, 7, "Reject: HTTP 400\n+ audit entry\n(nothing stored)", PALE_ORANGE, tc=INK, ec=ORANGE, fs=7.0)
    box(ax, 86, 20, 22, 8, "ValueError:\nblock rejected;\nno ballot, token stays unused", PALE_ORANGE, tc=INK, ec=ORANGE, fs=6.8)
    box(ax, 86, 6.5, 22, 6, "Receipt: ballot id,\ntx hash, block no., hash", NAVY, fs=6.8)
    for y1, y2 in ((83.5, 81.8), (73.2, 70.8), (62.2, 59.8), (51.7, 48.6), (42.4, 40.1), (33, 31.3), (22.7, 20.8), (12.2, 9.6)):
        arrow(ax, (40, y1), (40, y2), color=NAVY)
    for y in (77.5, 66.5, 55.5):
        arrow(ax, (63, y), (75, 77.5 if y == 77.5 else 74), color=ORANGE, lw=1.1)
    ax.text(64, 79, "no", fontsize=7.2, color=ORANGE)
    arrow(ax, (63, 27), (75, 22), color=ORANGE)
    arrow(ax, (63, 16.5), (75, 18.5), color=ORANGE)
    ax.text(63.5, 28.4, "no", fontsize=7.2, color=ORANGE)
    ax.text(63.5, 18, "no", fontsize=7.2, color=ORANGE)
    arrow(ax, (63, 6.5), (75, 6.5), color=NAVY)
    ax.text(41.5, 71.6, "yes", fontsize=7.2, color=TEAL)
    save(fig, OUT / "10_flowchart_cast_vote.png")


def validate_flowchart():
    fig, ax = canvas(10, 7.0, 100, 70)
    ax.text(50, 67.2, "Audit algorithm - validate_chain() (what the auditor's 'Verify ledger integrity' runs)", ha="center", fontsize=9.6, color=NAVY, fontweight="bold")
    box(ax, 30, 60, 44, 5, "Load all blocks ordered by block_index", NAVY, fs=7.6)
    box(ax, 30, 51.5, 44, 5, "For block b: collect its transaction hashes", BLUE, fs=7.6)
    diamond(ax, 30, 41, 44, 9, "SHA-256(sorted tx hashes)\n== b.merkle_root ?", fs=7.4)
    diamond(ax, 30, 29, 44, 9, "block hash recomputed from\nindex, time, previous, merkle, txs == b.block_hash ?", fs=6.6)
    diamond(ax, 30, 17, 44, 9, "b.previous_hash ==\nprevious block's hash ?", fs=7.4)
    box(ax, 30, 6, 44, 5, "Next block;  after the last: valid = true, height, last hash", TEAL, fs=7.4)
    box(ax, 80, 41, 30, 8, "valid = false\nfield = merkle_root,\nfirst_invalid = b.block_index", PALE_ORANGE, tc=INK, ec=ORANGE, fs=7.0)
    box(ax, 80, 29, 30, 8, "valid = false\nfield = block_hash", PALE_ORANGE, tc=INK, ec=ORANGE, fs=7.0)
    box(ax, 80, 17, 30, 8, "valid = false\nfield = previous_hash", PALE_ORANGE, tc=INK, ec=ORANGE, fs=7.0)
    for y1, y2 in ((57.5, 54), (49, 45.6), (36.5, 33.6), (24.5, 21.6), (12.5, 8.6)):
        arrow(ax, (30, y1), (30, y2), color=NAVY)
    for y in (41, 29, 17):
        arrow(ax, (52, y), (65, y), color=ORANGE)
        ax.text(55, y + 1.6, "no", fontsize=7.2, color=ORANGE)
    ax.text(31.5, 36.2, "yes", fontsize=7.0, color=TEAL)
    ax.text(31.5, 24.2, "yes", fontsize=7.0, color=TEAL)
    ax.text(31.5, 12.2, "yes", fontsize=7.0, color=TEAL)
    ax.add_patch(Rectangle((60, 2), 38, 9.5, fc="white", ec="#B7C3D3", zorder=1))
    ax.text(79, 6.8, "Not checked by this function: validator signatures,\ntransaction hash vs its fields, ballots table vs ledger,\nblocks dropped from the tip.", ha="center", va="center", fontsize=6.8, color=ORANGE)
    save(fig, OUT / "11_flowchart_validate_chain.png")


def ledger_structure():
    fig, ax = canvas(10, 5.4, 100, 54)
    ax.text(50, 51.5, "Ledger structure - blocks linked by previous_hash, each holding one signed transaction", ha="center", fontsize=9.6, color=NAVY, fontweight="bold")
    for i, (x, label) in enumerate(((17, "Block 0 (genesis)"), (50, "Block n"), (83, "Block n+1"))):
        ax.add_patch(Rectangle((x - 14, 14), 28, 31, fc=PALE_PURPLE, ec=PURPLE, lw=1.4, zorder=1))
        ax.text(x, 43, label, ha="center", fontsize=8.6, color=PURPLE, fontweight="bold")
        rows = ["block_index, timestamp", "previous_hash", "merkle_root", "block_hash", "signatures: v1, v2, v3"] if i else ["index 0, no transactions", "previous_hash = 64 zeros", "merkle_root = SHA-256('')", "block_hash", "signatures: v1, v2, v3"]
        for j, r in enumerate(rows):
            ax.text(x - 12.5, 39 - j * 3.9, r, fontsize=6.9, color=INK, family="DejaVu Sans Mono")
        if i:
            box(ax, x, 18.5, 24, 6.5, "tx: tx_hash, ballot_id,\nencrypted_payload, nonce,\ntimestamp, signature", ORANGE, fs=6.2)
    arrow(ax, (36, 33), (3 + 28, 33), "", color=NAVY, lw=1.0)
    arrow(ax, (69, 33), (64, 33), "", color=NAVY, lw=1.0)
    ax.text(50, 9, "block_hash = SHA-256( canonical JSON { block_index, timestamp, previous_hash, merkle_root, sorted tx hashes } )", ha="center", fontsize=7.6, color=INK)
    ax.text(50, 4.8, "merkle_root = SHA-256( concatenation of the sorted transaction hashes )   - a flat hash, not a binary Merkle tree", ha="center", fontsize=7.6, color=INK)
    ax.text(50, 1.2, "Commit rule: at least 2 of the 3 validators must verify the block and sign its block_hash with Ed25519.", ha="center", fontsize=7.6, color=GREY, style="italic")
    save(fig, OUT / "12_ledger_structure.png")


if __name__ == "__main__":
    for fn in (system_architecture, high_level_workflow, dfd0, dfd1, dfd2, uml_class_diagram, sequence_diagram, use_case, er_diagram, flowchart, validate_flowchart, ledger_structure):
        fn()
