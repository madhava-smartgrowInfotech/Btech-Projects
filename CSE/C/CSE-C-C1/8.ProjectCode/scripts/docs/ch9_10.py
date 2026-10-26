"""Novelty, contributions, scope, limitations, walk-throughs, decisions, conclusion (Chapter 9) and future scope (Chapter 10) of AegisBallot.

Every number is read from facts.py (experiments/voting/*.json, docs/metrics/tests.json); every statement about behaviour was checked against the code in app/.
"""

import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB, renum
from .refs import CITE as R


def src(rel, start=None, end=None):
    """Lines start..end (1-based, inclusive) of a source file of 8.ProjectCode, for code listings."""
    lines = open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    return "\n".join(lines[(start or 1) - 1:end or len(lines)]).rstrip("\n")


def c(*keys):
    """Citation string such as [1], [6] from CITE keys."""
    return "[" + ", ".join(str(R[k]) for k in keys) + "]"


def _v():
    """Frequently quoted measured values."""
    s = F.BENCH_SYNC
    idle = [d["sync"]["throughput"] for d in F.IDLE_RUNS]
    idle_ms = [d["sync"]["mean_ms"] for d in F.IDLE_RUNS]
    lat = F.LAT
    vh = F.VALIDATE_BY_HEIGHT
    top = list(vh.values())[-1] if vh else {"height_blocks": 0, "median_ms": 0}
    return {
        "sync_ms": f"{s['mean_ms']:.1f}", "sync_ops": f"{s['throughput']:.1f}", "sync_p95": f"{s['p95_ms']:.0f}",
        "idle_lo": f"{min(idle):.1f}", "idle_hi": f"{max(idle):.1f}", "idle_ms_lo": f"{min(idle_ms):.1f}", "idle_ms_hi": f"{max(idle_ms):.1f}",
        "login": f"{lat['login']['mean_ms']:.0f}", "verify": f"{lat['verify']['mean_ms']:.0f}", "cast": f"{lat['cast']['mean_ms']:.0f}",
        "e2e": f"{lat['end_to_end']['mean_ms']:.0f}", "e2e_p95": f"{lat['end_to_end']['p95_ms']:.0f}",
        "vc_h": top["height_blocks"], "vc_ms": f"{top['median_ms']:.0f}",
        "sa_ms": f"{F.TAMPER.get('strict_audit_ms_median', 0):.0f}", "sa_h": F.TAMPER.get("chain_height"),
        "vc_361": f"{F.TAMPER.get('validate_chain_ms_median', 0):.0f}",
        "propose": f"{F.STAGE['propose_block']:.1f}", "auth": f"{F.STAGE['authorise']:.1f}", "persist": f"{F.STAGE['persist']:.1f}", "crypto": f"{F.STAGE['encrypt_sign_hash']:.2f}",
        "argon_v": f"{F.MICRO['argon2id_verify']['mean_ms']:.0f}", "argon_h": f"{F.MICRO['argon2id_hash']['mean_ms']:.0f}",
        "ed_sign": f"{F.MICRO['ed25519_sign']['mean_ms']:.2f}", "ed_ver": f"{F.MICRO['ed25519_verify']['mean_ms']:.2f}",
        "np": F.N_TAMPER_PRODUCT, "nt": F.N_TAMPER, "ns": F.N_TAMPER_STRICT,
        "pt": F.PYTEST_TOTAL, "pp": F.PYTEST_PASSED, "mp": F.MATRIX_PASSED, "mt": F.MATRIX_TOTAL,
    }


# ------------------------------------------------------------------ document 9: novelty and contributions
def novelty_blocks():
    v = _v()
    base = c("base")
    return [
        P(f"{F.PRODUCT} does not introduce a new cryptographic primitive or a new consensus protocol, and we do not claim one. Its building blocks (SHA-256, AES-256-GCM, Ed25519, Argon2id, the Verhoeff checksum, "
          "a hash-chained ledger, quorum approval) are standard and well studied. What is new is the combination in one small, runnable system, the way identity is separated from the ballot, "
          "the auditor tooling, and above all the habit of measuring the integrity check itself: the project tests what its own ledger validation can and cannot detect and reports the result. "
          "This section sets the work against the base paper first and then separates what is new from what is not."),
        H2("2.1 Difference from the base paper"),
        P(f"The base paper {base} proposes a four-tier model for Oman: a MySQL tier, an Ethereum tier (Geth test chain) whose smart contracts register voters and candidates, cast and count votes, "
          "a C# web-application tier, and client devices. Voters are authenticated by biometrics in a simulation, and the evaluation times voter-registration and vote-casting transactions for 1000 synthetic voters, "
          "synchronously and in asynchronous batches. The paper's own conclusion calls for pilots, a Layer-2 study and a threat model."),
        TAB("AegisBallot compared with the base paper", ["Aspect", "Base paper (Oman model)", "AegisBallot"],
            [["Ledger", "Ethereum test chain (Geth), smart contracts in C# / Nethereum", "Local permissioned ledger in Python: SHA-256 hash chain, 3 validators, quorum 2 of 3, Ed25519 block signatures"],
             ["Identity", "Biometric authentication (simulated), National ID in synthetic data", "Aadhaar-style number: 12 digits, Verhoeff checksum, salted-hash registry, number must match the signed-in voter"],
             ["Ballot privacy", "Votes recorded through contracts; wallets for anonymity", "Choice encrypted with AES-256-GCM; one-time token separates the identity step from the ballot; voter-ballot link still stored (see limitations)"],
             ["Workflow", "Administrator registers voters and candidates and deploys contracts; voters cast", "Admin, voter and auditor consoles: elections, candidates, status, tokens, receipts, results, audit log"],
             ["Audit tool", "Auditors named as actors; no audit tool evaluated", "Integrity check, block explorer, tamper demonstration, audit log viewer; tamper study of the check itself"],
             ["Evaluation", "1000 synthetic voters, sync and batches of 10 to 50; ~2 s registration and ~3-4 s vote per transaction (read from figures)",
              f"1000 synthetic voters, sync and batches of 10, 20, 30; {v['sync_ms']} ms per vote in-process on a shared PC; {F.N_TAMPER}-case tamper study; {v['pt']} tests; {v['mt']}-check HTTP matrix"],
             ["Hardware / stack", "Core i7-12700, 16 GB, Windows 10; C# .NET 7", f"Core i5-12500, 15.7 GB, Windows 11; Python {F.ENV.get('python', '3.11')}, FastAPI, SQLite"]],
            widths=[1.0, 2.5, 3.0], align=["l", "l", "l"], size=9.5),
        P("The two evaluations answer different questions and the numbers must not be compared as if they did. The base paper times a transaction that is mined or validated by an Ethereum node and returns a confirmation; "
          "AegisBallot times a function call inside one process in which three validators are three key objects, with no network between them. A shorter time here is therefore not evidence that this design is better, "
          "only that a single-machine simulation is cheaper than a real chain, which is expected."),
        H2("2.2 What is new in this work"),
        N("**National-identity-style verification in the loop.** The batch asks for Aadhaar verification, which the base paper does not provide. The identity provider is an interface with a demonstration adapter "
          "that checks format, the Verhoeff checksum and a salted-hash registry, and requires the number to belong to the signed-in account; a real adapter could replace it.",
        "**Identity separated from the ballot by a one-time token.** The token is random, stored only as a hash, expires in ten minutes and is unique per election and voter; the ballot table carries no voter column.",
        "**A complete three-role workflow.** Administrator, voter and auditor consoles on a React front end over a JSON API with CSRF protection, role checks, rate limiting and an audit log.",
        "**An auditor toolset.** Chain verification, a block explorer showing validator signatures, a tamper demonstration and the audit trail.",
        f"**A measured tamper study of the ledger check.** Thirteen kinds of tampering were applied to a {F.TAMPER.get('chain_height')}-block chain. The product's `validate_chain` detects {v['np']} of {v['nt']}; "
          f"a stricter audit that also verifies validator signatures, recomputes transaction hashes and cross-checks the ballot table detects {v['ns']} of {v['nt']}. The study is the main evidence that the ledger is "
          "tamper-evident for some edits and not for others, and it points to concrete fixes.",
        "**Honest performance reporting.** The project's own benchmark was found to run its \"asynchronous\" batches sequentially; this is stated rather than reported as a concurrency result."),
        H2("2.3 What is standard and was reused"),
        B("SHA-256 hashing and canonical JSON serialisation for transaction and block hashes " + c("sha2") + ".",
          "AES-256-GCM authenticated encryption for the ballot " + c("gcm") + ".",
          "Ed25519 signatures for transactions and for validator approvals " + c("eddsa") + ".",
          "Argon2id password hashing " + c("argon2", "argon2rfc") + " and the Verhoeff decimal checksum " + c("verhoeff") + ".",
          "A hash-linked chain of blocks and quorum approval, as in permissioned ledgers " + c("fabric", "pbft") + "; the 'Merkle root' is a flat hash, not a tree " + c("merkle") + ".",
          "FastAPI, SQLAlchemy, React, Vite and Tailwind as the application stack " + c("fastapi", "sqlalchemy", "react") + "."),
        P("In short, the contribution is an integrated, tested and honestly measured prototype, not a new scheme. Where the prototype falls short of what the word blockchain suggests, Section 3 and Chapter 9 say so."),
    ]


def contribution_blocks():
    v = _v()
    return [
        P("The work makes the following contributions."),
        N("A working local e-voting platform in which a voter proves identity with a Verhoeff-checked, salted-hash Aadhaar number, receives a single-use ten-minute token and casts one encrypted ballot per election.",
          "A one-voter-one-vote guarantee enforced in four independent layers (eligibility, unique participation row, single-use token, ledger nonce and hash uniqueness), tested by automated tests and by an HTTP replay check.",
          "A local permissioned ledger with SHA-256 chaining, three Ed25519-signing validators and a two-of-three commit rule, with a receipt (ballot id, transaction hash, block number, block hash) for every vote.",
          "Administrator, voter and auditor consoles with CSRF protection, role-based access control, rate limiting and a chronological audit log.",
          f"A measured evaluation: {v['pt']} automated tests passed, {v['mp']} of {v['mt']} HTTP security and functional checks behaved as expected, 1000 synthetic voters voted without failure "
          f"(mean {v['sync_ms']} ms per vote on a shared PC), and a full voter journey over HTTP took {v['e2e']} ms on average.",
          f"A tamper-detection study showing that the product's integrity check catches {v['np']} of {v['nt']} tampering cases and a stricter signature-aware audit catches all {v['ns']}, with the concrete gaps listed.",
          "A candid account of what the prototype is not: a single-machine simulation without TLS, UIDAI access or full ballot unlinkability, and a benchmark whose batch mode is sequential."),
    ]


# ------------------------------------------------------------------ document 10: scope and limitations
def scope_blocks():
    return [
        H2("1.1 In scope"),
        B("Registration-style provisioning of voters by a seed script, with a synthetic Aadhaar registry of salted hashes and masked display (`XXXX-XXXX-` plus the last four digits).",
          "Voter authentication with Argon2id passwords, server-side sessions and an `HttpOnly` cookie; identity verification by format, Verhoeff checksum, registry lookup and ownership of the number.",
          "Election management by the administrator: create an election with a start and end time, add or deactivate candidates, move the status between DRAFT, OPEN, PAUSED and CLOSED, and read turnout and tallies.",
          "One-time authorisation tokens, AES-256-GCM encrypted ballots, signed transactions, a three-validator ledger with two-of-three approval, and a receipt.",
          "Results of a closed election, available to every signed-in role; a chain integrity check, block explorer, tamper demonstration and audit-log viewer for the auditor.",
          "Role-based access control, CSRF header, per-IP rate limits (10 logins and 15 verifications per minute), input validation, and an in-built benchmark."),
        H2("1.2 Out of scope"),
        B("Contacting UIDAI or any real identity service, OTP or biometric factors, and handling of real personal data.",
          "A distributed network of validator machines, a real consensus protocol, smart contracts, a public blockchain, cryptocurrency or gas.",
          "National-scale elections, constituency and ward structures, ranked or multi-seat ballots, postal or proxy voting, and legal compliance with an election commission's rules.",
          "End-to-end verifiable cryptography (zero-knowledge proofs, homomorphic tallying, mix-nets) and coercion-resistance.",
          "TLS termination, high-availability deployment, backup and disaster recovery, and a mobile application.",
          "A self-service voter registration screen: voters are provisioned by the seed script or the benchmark, not through the interface."),
        H2("1.3 Deployment context"),
        P("AegisBallot is a local demonstration. It binds to 127.0.0.1 (backend port 8401, front end port 5401), keeps its state in one SQLite file and three key files in `data/`, and is suited to a classroom, a laboratory "
          "demonstration or an informal association election run by one trusted operator. It is not a system on which a public election should depend, and the later sections explain why."),
        H2("1.4 Users and what each may do"),
        TAB("Roles and permissions", ["Role", "May do", "May not do"],
            [["Administrator", "Create elections, add or deactivate candidates, open, pause and close an election, read turnout, the live tally of any election and the benchmark page", "Cast a ballot; read the auditor console (HTTP 403)"],
             ["Voter", "List open, paused and closed elections, verify identity, cast one ballot per election, see the receipt, read results once an election is closed", "Read the administrator or auditor routes (HTTP 403); read the tally of an open election (HTTP 404)"],
             ["Auditor", "Run the integrity check and the tamper demonstration, browse blocks, transactions, validators and the audit log, read results of closed elections", "Change elections or cast ballots"]],
            widths=[1.2, 3.1, 2.2], align=["l", "l", "l"], size=10),
        H2("1.5 Technology boundaries"),
        P("The back end is Python 3.11 with FastAPI, SQLAlchemy 2 and SQLite; the front end is React 18 with Vite, TypeScript and Tailwind CSS. Cryptography comes from the `cryptography` and `argon2-cffi` libraries rather than from code written for the project. "
          "The original server-rendered Jinja pages were kept beside the new JSON layer, so the system has two user interfaces over the same services; the documents describe and illustrate the React interface only. "
          "The batch abstract mentions a Java back end and bcrypt as possibilities; the implementation uses Python and Argon2id instead, and this difference is stated wherever it matters."),
    ]


def assumption_blocks():
    return [
        P("The following assumptions underlie the design and every result in this report."),
        B("The operator of the server is honest and controls the machine; the validators run on the same host, so the quorum protects against bugs and casual edits, not against an operator with file access.",
          "Voters are provisioned with an Aadhaar number that is already in the registry; the synthetic numbers carry a valid Verhoeff check digit and are not real identifiers.",
          "Clients reach the server over a trusted local connection; TLS would be added by a reverse proxy in any shared deployment.",
          "One administrator account is trusted to manage elections; the auditor is a distinct, read-mostly role.",
          "The clock of the server is correct, because token expiry and block timestamps use the server's UTC time.",
          "SQLite with one writer is sufficient for the expected load of a small election.",
          "The encryption key, the three validator keys and the system signing key are generated on first start and are never committed to source control; whoever holds them is trusted.",
          "Each voter uses one account and one browser session at a time; shared accounts and shared devices are not considered.",
          "The test and benchmark data are synthetic, so results describe the software and not the behaviour of a real electorate."),
        P("If any assumption fails the consequences are stated in the limitations: an operator with file access can alter results undetected by the present check, a wrong clock changes token expiry, and a shared IP address shares the rate limit."),
    ]


def limitation_blocks():
    v = _v()
    return [
        P("The limitations below are grouped by the area they affect. Each was either read from the code or demonstrated by a measurement, and none is hypothetical."),
        H2("3.1 Identity"),
        B("The identity check is a local, synthetic registry. It does not contact UIDAI, and there is no biometric or OTP factor; possession of the number and the account password is enough.",
          "The Verhoeff checksum catches typing errors, not forged numbers: any 12-digit string with a valid check digit passes the format step, and only the registry lookup separates real from unknown numbers.",
          "Voters cannot register themselves; the API has no registration route."),
        H2("3.2 Ledger"),
        B("The ledger is a single-process simulation. The three validator private keys sit in `data/validators.json` on the same server, so anyone who can write that file can also forge approvals; the quorum is not distributed trust.",
          "Each block holds one transaction, so the chain has one block per vote; the 'Merkle root' is a hash of the sorted transaction hashes, so there are no inclusion proofs.",
          "`propose_block` skips the transaction signature check if a transaction has no public key, and validators do not independently re-verify the voter's token or eligibility.",
          f"`validate_chain` recomputes the Merkle root, the block hash and the previous-hash links but does not verify validator signatures, does not recompute a transaction hash from its fields and does not look at the ballots table. In the tamper study it missed {v['nt'] - v['np']} of {v['nt']} cases (tamper matrix below)."),
        FIG(F.fig("f06_tamper_matrix.png"), "Tamper study: the product check misses edits to the tally table, ledger payloads, signatures and the newest block; the stricter audit catches all of them.", 5.6),
        B("The auditor's 'tamper test' button does not validate a modified copy: it overwrites a hash in memory and reports detection from a link comparison. It illustrates the idea; the unit test that edits the real database is the independent check."),
        H2("3.3 Privacy and secrecy"),
        B("The table `voter_participation` stores the voter id next to the ballot id, so an operator with the database and the encryption key can link a voter to a choice. The ballot is anonymous only in the sense that the ballots table has no voter column.",
          "All ballots are encrypted under one AES key held by the server (the README speaks of a per-election key; the code generates one key), and the tally decrypts every ballot with it.",
          "The administrator can read a live tally of an open election; the HTTP check confirmed status 200 for that request, whereas a voter receives 404."),
        H2("3.4 Security configuration"),
        B("No TLS is configured. The session cookie is `HttpOnly` and `SameSite=lax` but has no `Secure` flag, because the app is served over plain HTTP. The batch objective names TLS; it was not achieved.",
          "Sessions and rate-limit counters are in memory and are lost on restart; the limit of 10 logins per minute is per IP address, so voters behind one shared address would share it.",
          "Secrets (`data/secrets.json`, validator and system keys) are plain files; the default `SECRET_KEY` is a development string unless overridden.",
          "Election windows are stored, but `cast_vote` checks the status flag only, not the clock, so voting is controlled by the administrator's status change."),
        H2("3.5 Testing"),
        B(f"The {v['pt']} unit tests and the {v['mt']}-check HTTP matrix cover the paths we thought of; there was no penetration test, fuzzing, static analysis or independent review.",
          "Concurrent voting was not tested. Block creation reads the last block and writes the next index, so two simultaneous requests could race on the unique block index; the code has no lock.",
          "No usability or accessibility study with real voters was done."),
        H2("3.6 Performance"),
        B(f"The benchmark's \"asynchronous\" batches run sequentially, so the three batch sizes measure the same thing; the throughput differences ({F.BENCH_BATCH['10']['throughput']:.1f}, {F.BENCH_BATCH['20']['throughput']:.1f} and {F.BENCH_BATCH['30']['throughput']:.1f} ops/s) are machine noise.",
          f"Timings were taken on a shared PC: the same code ran at {v['idle_lo']} to {v['idle_hi']} ops/s on an idle machine and {v['sync_ops']} ops/s during the 1000-voter run.",
          f"`validate_chain` is linear in chain length ({v['vc_ms']} ms at {v['vc_h']} blocks) and the stricter audit is slower ({v['sa_ms']} ms at {v['sa_h']} blocks), so a national chain would need indexing and batching."),
        H2("3.7 Gaps against the batch abstract and the base paper"),
        P("The batch abstract promises authentication, verification, election management, vote storage and automatic results; these exist. It also lists password hashing, role-based access control, input validation, audit logging and TLS as security techniques; "
          "all but TLS exist, and the abstract's bcrypt was replaced by Argon2id. The base paper's central feature, decentralised verification by Ethereum nodes, has no counterpart in this prototype: "
          "the validators are loop iterations in one process. The base paper's biometric authentication is replaced by a number check, which proves less about the person. "
          f"The prototype therefore implements the application layers of the base paper's four-tier model (storage, web application, client) and a faithful miniature of its ledger rules, but not the distribution that gives a blockchain its trust property {c('base')}."),
        P("Two smaller defects were found while reading the code and are reported rather than hidden: the README speaks of a per-election encryption key whereas the code uses one key for all elections, and the benchmark documentation calls the batch mode asynchronous whereas the code processes batches in sequence. "
          "Neither affects the correctness of a vote, but both would mislead a reader who relied on the description."),
    ]


def not_measured_blocks():
    return [
        P("Several things a reader might expect were not measured. We list them so that no result is read as covering them."),
        B("**Concurrency.** No test submitted votes from parallel clients; the sequential benchmark and the one-at-a-time HTTP run say nothing about contention on the ledger.",
          "**Large scale.** The largest run had 1000 voters and the largest chain 361 blocks in the study and about 4000 blocks in the 1000-voter benchmark database; nothing was run at the scale of a state election.",
          "**Network behaviour.** All traffic was to 127.0.0.1; latency over a real network, packet loss and TLS handshake cost are unknown.",
          "**Memory and disk.** CPU time was recorded; resident memory, database growth per vote and disk use were not.",
          "**Real identity data.** No test used a real Aadhaar number or UIDAI response, which would be unlawful and unnecessary for a prototype.",
          "**Human factors.** No voter or administrator was observed using the interface, so error rates and satisfaction are unknown.",
          "**Base-paper replication.** The Oman model was not rebuilt; its per-transaction times were read by eye from Figures 6 and 9 and are quoted only as an order of magnitude.",
          "**Security assurance.** No penetration test, code audit or formal analysis was performed beyond the automated checks listed in Chapter 7."),
        P("The reasons are mostly practical. The work was done on one shared student PC with no second machine, no access to a real identity service and no real voters; "
          "a concurrency test needs a multi-threaded server and a database that supports it, and a usability study needs participants and ethical approval. "
          "None of these omissions changes the numbers that were measured, but each limits what they can be taken to mean."),
    ]


# ------------------------------------------------------------------ document 12: key code walk-throughs and decisions
def walkthrough_blocks():
    return [
        P("This section reads the five functions that carry the system's behaviour. The listings are copied unchanged from the repository; line comments are the authors' own."),
        H2("3.1 Identity verification: DemoAadhaarProvider.verify"),
        CODE(src("app/identity/provider.py", 18, 37), 8.5),
        P("The function strips spaces and hyphens, insists on exactly twelve digits, runs the Verhoeff checksum, hashes the number with a salt and the server pepper and looks the hash up in `voter_profiles`. "
          "It returns a dictionary rather than raising, so the API route can turn each failure reason into the HTTP 400 that was exercised in the matrix. The class implements `IdentityVerificationProvider`, an abstract interface with the same signature, which is the seam where a real adapter would be plugged in. "
          "Note what is not here: the function does not know which voter is signed in; the route compares `result['user'].id` with the session user and returns 403 on a mismatch."),
        H2("3.2 Token issue: issue_authorization"),
        CODE(src("app/services/voting_service.py", 35, 64), 8.5),
        P("Three guards run before a token exists: the voter must have an eligibility row marked eligible, must have no participation row, and must not hold a still-valid unused authorisation. "
          "The token is `secrets.token_urlsafe(32)`, 256 bits of randomness; only its SHA-256 hash is stored, so a database leak does not reveal usable tokens. The expiry is ten minutes, and a unique constraint on (election, voter) means a second token cannot be inserted while the first row exists."),
        H2("3.3 Casting: cast_vote"),
        CODE(src("app/services/voting_service.py", 86, 116), 8.5),
        P("After the election, candidate and token checks, the function generates a random ballot id and nonce, encrypts the candidate id with AES-256-GCM, builds the transaction from five fields, hashes its canonical JSON, signs the hash with the system Ed25519 key and calls `propose_block`. "
          "Only when the block is committed does it write the ballot row, mark the token used and add the participation row, all in one commit; if the ledger raises, nothing was stored and the token is still usable. The block commit inside `propose_block` and the ballot commit here are two separate commits, so a crash between them would leave a block without a ballot. "
          f"In the stage measurements the encryption, hashing and signing together take {_v()['crypto']} ms, which is why the cost of a vote is dominated by database work and block proposal."),
        H2("3.4 Committing: propose_block"),
        CODE(src("app/ledger/ledger.py", 143, 148) + "\n    ...\n" + src("app/ledger/ledger.py", 191, 214), 8.5),
        P("The block hash is computed first, from the next index, the timestamp, the previous block's hash, the flat Merkle root and the sorted transaction hashes. In the elided part each of the three validators re-checks the schema, the uniqueness of the nonce and of the transaction hash and, when a public key is present, the transaction signature. "
          "A validator that finds no fault signs the block hash with its Ed25519 key. If fewer than two approve, a `ValueError` is raised and nothing is committed; otherwise the block is stored with the approvals as JSON. "
          "Because the validators are three loop iterations in one process, the quorum rule is correctly implemented but is not an agreement between separate machines."),
        H2("3.5 Auditing: validate_chain"),
        CODE(src("app/ledger/ledger.py", 231, 252), 8.5),
        P("For every block the function recomputes the Merkle root from the stored transactions, recomputes the block hash from the stored fields, and compares the previous hash with the preceding block. The first mismatch is returned with the field name and the block index, which is what the auditor page displays. "
          "The listing also shows the limits found in the tamper study: nothing here reads `validator_signatures`, recomputes a `tx_hash` from the transaction fields or looks at the `ballots` table, and a chain with its newest blocks removed is still internally consistent."),
    ]


def decision_blocks():
    v = _v()
    return [
        P("The table lists the main implementation decisions, the reason for each and the alternative that was not taken. Several decisions were made for the sake of a runnable, locally testable prototype and are revisited in Chapter 10."),
        TAB("Implementation decisions and their reasons", ["Decision", "Reason", "Alternative not taken"],
            [["Local permissioned ledger in Python instead of Ethereum", "Runs on one PC without a node, gas or test network; keeps the demonstration reproducible; the batch asks for hashing and immutability, not a public chain", "Geth or Ganache with Solidity contracts, as in the base paper"],
             ["Three validators with quorum 2 of 3", "Shows the commit rule and signed approvals at small cost; mirrors the idea of permissioned consensus " + c("pbft", "fabric"), "A single signer, or a real network of nodes"],
             ["One transaction per block", "Gives every vote its own block number for the receipt and simplifies ordering", "Batching several ballots per block, which would raise throughput"],
             ["SHA-256 hash chain with canonical JSON", "Deterministic bytes make hashes reproducible by an auditor " + c("sha2"), "Pickle or ad-hoc string concatenation"],
             ["Flat hash instead of a Merkle tree", "Simpler code for one-transaction blocks", "Binary Merkle tree with inclusion proofs " + c("merkle")],
             ["AES-256-GCM for the choice, single server key", "Authenticated encryption with a random 12-byte nonce " + c("gcm") + "; one key keeps tallying simple", "Per-election keys, threshold or homomorphic encryption"],
             ["Ed25519 signatures", f"Fast ({v['ed_sign']} ms to sign, {v['ed_ver']} ms to verify) and small " + c("eddsa"), "RSA or ECDSA"],
             ["Argon2id for passwords", f"Memory-hard; about {v['argon_v']} ms per verification on this PC " + c("argon2"), "bcrypt (named in the batch abstract)"],
             ["Verhoeff checksum before the registry lookup", "Rejects mistyped numbers cheaply and without a database query " + c("verhoeff"), "Format check only"],
             ["Salted and peppered hash of the Aadhaar number", "The registry never stores the plain number; the display uses a masked form", "Plain text or an unsalted hash"],
             ["Single-use token with a hashed copy and ten-minute expiry", "Separates identity checking from ballot casting and defeats replay", "Reusing the session as the voting credential"],
             ["Unique constraints in the database", "The database itself refuses a second participation or token row, even if application code is bypassed", "Application-level checks only"],
             ["Server-side sessions, CSRF header and per-IP rate limit", "Simple and testable for a single process " + c("asvs"), "JWT stored in the browser; Redis-backed limits"],
             ["FastAPI JSON layer beside the original Jinja pages", "The React front end needed JSON; the existing routes and tests stayed untouched", "Rewriting the HTML routes"],
             ["SQLite", "Zero configuration for a local demonstration", "PostgreSQL, which would allow real concurrency"]],
            widths=[1.9, 2.7, 1.9], align=["l", "l", "l"], size=9.5),
        P("Two decisions deserve a closer word. Counting the tally from the `ballots` table rather than from the ledger was convenient, but it is the reason why edits to that table are not detected by the ledger check; "
          "the tamper study turned a design shortcut into a measured finding. Storing the voter id beside the ballot id in the participation table made the one-vote constraint trivial to enforce, at the price of weaker unlinkability."),
        P("Several decisions favour testability over strength. Keeping validators in one process made the quorum code easy to unit-test (a tampered block, a duplicate nonce and a bad previous hash all have tests) and made the benchmark reproducible; "
          "it also means the quorum protects nothing against the host. Writing the JSON layer beside the HTML routes rather than replacing them kept the existing test suite valid while the new interface was built. "
          "In each case the cheaper choice was taken knowingly and its cost is recorded in the limitations and the future scope."),
    ]


# ------------------------------------------------------------------ conclusion (Chapter 9, document 15)
def _conclusion():
    v = _v()
    base = c("base")
    return [
        H2("Summary of the work"),
        P(f"This project set out to build a secure voting system in which an Aadhaar-based identity check binds one ballot to one voter and a blockchain-style ledger makes the record tamper-evident and independently checkable. "
          f"The result is {F.PRODUCT}, a local web application with an administrator, voter and auditor console on a FastAPI and React stack. A voter signs in, enters an Aadhaar number that is validated by format, Verhoeff checksum and a salted-hash registry, "
          "receives a single-use ten-minute token, and casts one ballot that is encrypted with AES-256-GCM, signed with Ed25519 and committed as a block approved by two of three validators. The voter keeps a receipt, the administrator sees turnout and results, and the auditor can recompute the chain and read the audit log."),
        P("The system was built, run and measured. It is a demonstration on one machine: the registry is synthetic, the validators are in-process keys, and TLS is not configured. We make no claim that it is ready for a public election."),
        H2("Objectives achieved"),
        TAB("Objectives against outcomes", ["No.", "Objective (from the batch)", "Status", "Evidence"],
            [["1", "Voter registration and authentication with Aadhaar-based identity verification", "Partly achieved (registration is provisioning only)",
              "Argon2id login; verification by 12 digits, Verhoeff checksum, registry and ownership (matrix checks 9-12). Synthetic registry, no UIDAI; no self-registration screen"],
             ["2", "One voter, one vote through identity binding and duplicate checks", "Achieved", f"Four layers; duplicate-vote and replay checks returned 400; {v['pp']} of {v['pt']} tests passed"],
             ["3", "Record each ballot immutably with blockchain and cryptographic hashing", "Partly achieved",
              f"Hash-chained, signed blocks; the product check detects {v['np']} of {v['nt']} tamper cases and misses edits to the tally table, re-hashed chains, forged signatures and tip removal"],
             ["4", "Admin portal for elections, candidates and polling windows", "Mostly achieved", "Create, add, deactivate, open, pause, close; windows are stored but voting is governed by the status flag, not the clock"],
             ["5", "Results on close with a complete chronological audit trail", "Achieved, with caveats", "Tally published when the status is CLOSED (manual close, no scheduler); audit log records login, verification, cast, election changes, integrity checks"],
             ["6", "RBAC, input validation and TLS; evaluate integrity and performance", "Partly achieved (TLS not achieved)",
              f"RBAC and validation: {v['mp']} of {v['mt']} checks as expected; TLS not configured; integrity and performance evaluated (Chapter 8)"]],
            widths=[0.4, 2.2, 1.3, 2.6], align=["c", "l", "l", "l"], size=9.5),
        H2("Key findings"),
        B(f"**Cost of a vote.** On an idle machine one vote took {v['idle_ms_lo']} to {v['idle_ms_hi']} ms (about {v['idle_lo']} to {v['idle_hi']} votes per second); in the 1000-voter run on a shared PC the mean was {v['sync_ms']} ms with all 1000 votes succeeding. "
          f"Block proposal ({v['propose']} ms), token authorisation ({v['auth']} ms) and persistence ({v['persist']} ms) dominate; the cryptography of the vote takes {v['crypto']} ms.",
          f"**Whole journey.** Over HTTP a voter's login, verification and cast took {v['e2e']} ms on average ({v['e2e_p95']} ms at the 95th percentile), of which login with Argon2id was {v['login']} ms, verification {v['verify']} ms and casting {v['cast']} ms.",
          f"**Integrity check scales linearly.** `validate_chain` took {v['vc_ms']} ms at {v['vc_h']} blocks; a stricter audit that verifies signatures took {v['sa_ms']} ms on {v['sa_h']} blocks.",
          f"**The ledger check has gaps.** {v['np']} of {v['nt']} tamper cases were detected; {v['nt'] - v['np']} were missed, including an attacker who edits a ballot and recomputes every hash. {v['ns']} of {v['nt']} were detected once validator signatures, transaction hashes and the ballots table were checked.",
          "**Batch size had no effect.** The benchmark's batches are sequential, so the differences between them are noise."),
        P(f"Against the base paper {base}, the comparison is qualitative. It reports roughly two seconds for a registration and three to four seconds for a vote on an Ethereum test chain with a C# client, read from its figures; "
          f"{F.PRODUCT} takes a few tens of milliseconds in-process because it has no network or mining step. The base paper's argument for decentralised verification is exactly what a single-machine simulation cannot show, and the conclusion of that paper, that pilots and threat modelling are needed, applies equally here."),
        P(f"The security checks gave a consistent picture. All {v['mt']} HTTP checks behaved as designed: anonymous requests received 401, a voter on an administrator or auditor route received 403, a missing CSRF header 403, a malformed or checksum-invalid Aadhaar number 400, "
          "another voter's valid number 403, a forged or replayed token 400, and the eleventh login attempt inside a minute 429. The automated test suite covers the same ground from inside the application, including expiry of a token and the separation of identity from the ballot. "
          "What the checks could not show is whether an operator with access to the machine can alter the outcome; the tamper study addresses that question and its answer is the most useful result of the project."),
        H2("Practical applications"),
        B("Classroom and laboratory demonstration of identity-bound, hash-chained voting and of auditor tooling.",
          "A starting point for small association or campus council elections run by a trusted operator, after TLS, persistent sessions and the audit fixes in Chapter 10.",
          "A test bed for e-governance research: the identity provider interface, the ledger and the tamper study can be reused to compare other designs.",
          "It is not a candidate for a national or state election, which would need a real identity service, distributed validators, formal review and legal approval."),
        H2("Known limitations"),
        P("The limitations listed earlier in this report stand: synthetic identity, simulated distribution of trust, partial ballot secrecy, an integrity check that does not cover signatures or the tally table, no TLS, and untested concurrency. "
          "The most important lesson of the project is that a ledger is only as trustworthy as the check that reads it, and that the check must be tested as carefully as the ledger."),
    ]


def conclusion_blocks():
    return _conclusion()


# ------------------------------------------------------------------ future scope (Chapter 10, document 15)
def _future():
    ratio = round(F.TAMPER.get("strict_audit_ms_median", 0) / max(F.TAMPER.get("validate_chain_ms_median", 1), 1))
    return [
        H2("Improvements to the present design"),
        P("The tamper study and the code review identify fixes that are small and would close the largest gaps."),
        N(f"Extend `validate_chain` to verify each validator signature against the stored public keys, recompute every transaction hash from its fields, verify the transaction signature, and cross-check the `ballots` table against the ledger. The stricter audit in `scripts/run_experiments.py` already does this and detected all {F.N_TAMPER} cases, at about {ratio} times the cost of the present check.",
          "Compute a real binary Merkle tree so that a voter can check inclusion of their ballot from a short proof.",
          "Use a key per election, keep it out of the application database, and decrypt only when the election is closed; hide the live tally from the administrator.",
          "Split the voter-to-ballot link: record participation without the ballot id, or use blind-signature or mix-based schemes " + c("chaum") + ", so that the database alone does not reveal a choice.",
          "Serve the application over TLS behind a reverse proxy, set the `Secure` flag on the cookie, and replace the development secrets.",
          "Make sessions persistent and rate limits shared (for example in a database or Redis) and key them by account as well as by IP address.",
          "Enforce the election window by the clock as well as the status flag, and close elections automatically."),
        H2("Additional features"),
        B("A second identity factor: OTP to a registered phone or a biometric match, as proposed in the Aadhaar-based work " + c("newera") + " and the base paper.",
          "A real identity adapter for an official sandbox, behind the existing `IdentityVerificationProvider` interface, with consent and data-protection handling in line with the Aadhaar Act " + c("aadhaar_act") + ".",
          "Cryptographic verifiability: zero-knowledge proofs or homomorphic tallying, as surveyed " + c("aswini", "ohize") + ", so that the result can be checked without trusting the decrypting party.",
          "A public receipt-verification page where a voter pastes the ballot id and sees the block and its hashes.",
          "Voter self-registration with approval by the administrator, and multi-election and constituency support."),
        H2("Scalability and deployment"),
        B("Run the three validators as separate services on separate hosts, exchange proposals and signatures over the network, and adopt a tested protocol such as PBFT or Raft " + c("pbft") + " in place of the in-process loop.",
          "Replace SQLite with PostgreSQL, add a lock or a serialisable transaction around block creation, and then run a real concurrent load test (the present benchmark is sequential).",
          "Batch several ballots per block and add database indexes so that validation does not issue queries per block.",
          "Package the application in containers with the secrets supplied from outside the image, and add monitoring of chain height and validation time.",
          "Compare the throughput of the revised design with the figures in the base paper on the same hardware, including a Layer-2 comparison as the base paper proposes."),
        TAB("Suggested order of work", ["Step", "Change", "Effort", "Closes"],
            [["1", "Signature-aware, ballot-cross-checking audit in `validate_chain`", "Small: logic already prototyped in the experiment script", "Tamper cases T6, T7, T10-T13"],
             ["2", "TLS proxy, `Secure` cookie, non-default secrets", "Small", "Plain-HTTP session exposure"],
             ["3", "Lock or serialisable transaction around block creation; concurrent load test", "Medium", "Untested concurrency and the unique block-index race"],
             ["4", "Per-election keys; hide the live tally; split voter and ballot ids", "Medium", "Operator linking of voter to choice"],
             ["5", "Real Merkle tree with inclusion proofs; receipt-check page", "Medium", "Voter-side verification"],
             ["6", "Separate validator services with a tested consensus protocol", "Large", "Single-host trust"],
             ["7", "Official identity sandbox adapter, OTP or biometric factor", "Large; needs approval", "Synthetic registry"]],
            widths=[0.5, 2.8, 1.7, 1.5], align=["c", "l", "l", "l"], size=9.5),
        P("The order puts the cheap, high-value corrections first. The first step alone would raise the detection result of the study from the present figure to all thirteen cases without a change of architecture; the later steps change what the system is and should follow only once the earlier ones are measured."),
        H2("Further research"),
        B("Formal modelling of the voting protocol and its privacy and verifiability properties, in the manner of analyses of deployed systems " + c("estonia", "helios", "voatz") + ".",
          "A penetration test and a threat model that includes insider and operator attacks on the key files.",
          "A usability and accessibility study with real voters and polling staff, including voters who cannot use the web interface.",
          "A study of coercion-resistance and receipt-freeness: the present receipt proves that a ballot exists but not what it contains, which is intended, and this property should be argued formally.",
          "A longitudinal measurement of chain growth, storage and audit time over many elections."),
    ]


def future_blocks():
    return _future()


def chapter9_blocks():
    return [H1("CHAPTER 9: CONCLUSION")] + renum(_conclusion(), "9")


def chapter10_blocks():
    return [H1("CHAPTER 10: FUTURE SCOPE")] + renum(_future(), "10")
