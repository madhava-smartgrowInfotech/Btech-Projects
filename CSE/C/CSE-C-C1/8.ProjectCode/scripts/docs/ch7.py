"""Chapter 7: System Testing. Every number is read from facts.py (experiments/voting/*.json, docs/metrics/tests.json)."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R

G = F.GROWTH
ST = F.STAGE
LT = F.LAT


def _c(x, d=1):
    return f"{x:,.{d}f}"


def _idle_range():
    tp = [d["sync"]["throughput"] for d in F.IDLE_RUNS]
    mean = [d["sync"]["mean_ms"] for d in F.IDLE_RUNS]
    return min(tp), max(tp), min(mean), max(mean)


# --------------------------------------------------------------------------- 7.1
def _strategy():
    lo_tp, hi_tp, lo_ms, hi_ms = _idle_range()
    e = F.ENV
    return [
        H2("7.1 Testing Strategy and Environment"),
        P("AegisBallot contains no learned model, so there is no accuracy or F1 to report. What can be tested is whether the rules of an election are enforced, whether the ledger exposes tampering, "
          "whether the access controls hold, and how fast the platform is. The strategy therefore has six levels, each answering a different question and each backed by a script or test file that is part of the repository."),
        TAB("Levels of testing and the artefact behind each", ["Level", "Question it answers", "Artefact", "Section"],
            [["Unit", "Does each rule work when called directly (hashing, checksum, token, vote, encryption)?", f"`tests/test_aegis.py`, {F.PYTEST_TOTAL} pytest tests", "7.2"],
             ["Integration over HTTP", "Do the JSON routes return the right status for good and bad requests?", f"`scripts/run_experiments.py`, part D, {F.MATRIX_TOTAL} checks against a live uvicorn server", "7.3"],
             ["Functional", "Does each required function of the abstract and objectives work end to end?", "pytest, HTTP checks, the seeded demonstration and the screenshot walk-through", "7.4"],
             ["Security", "Do roles, CSRF, rate limits, replay and identity checks hold?", "HTTP checks 1-14, 16, 18-19 and 25, plus unit tests", "7.5"],
             ["Tamper detection", "Which edits to stored data does the auditor's check expose?", f"13-case study in `scripts/run_experiments.py`, part C", "7.6"],
             ["Performance", "How long does a vote, a login and an audit take, and how does that grow?", f"`app.benchmarks.run_benchmark` ({F.N_VOTERS_BENCH} voters) and parts A, B and D of the harness", "7.8"]],
            widths=[1.1, 2.4, 2.3, 0.6], align=["l", "l", "l", "c"], size=9.5),
        P(f"**Environment.** Every run used one PC: an Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB of memory, Windows 11 Pro, Python {e.get('python', '3.11.9')}, FastAPI {e.get('libs', {}).get('fastapi', '')}, "
          f"SQLAlchemy {e.get('libs', {}).get('sqlalchemy', '')}, cryptography {e.get('libs', {}).get('cryptography', '')} and argon2-cffi {e.get('libs', {}).get('argon2-cffi', '')}. "
          "The PC was shared with other running jobs, so about a third of the processor was already busy when the measurements began. Latency figures are therefore upper-ish bounds and they move from run to run; "
          f"the earlier runs kept in `benchmark_results/` were made on an idle machine and give {_c(lo_ms)} to {_c(hi_ms)} ms per vote against the {_c(F.BENCH_SYNC['mean_ms'])} ms of the {F.N_VOTERS_BENCH}-voter run reported below."),
        P("**Scratch databases.** The pytest fixture calls `Base.metadata.drop_all` on whatever database `DATABASE_URL` names. To protect the development database that holds the data shown in the screenshots, "
          "every test and experiment in this chapter was run with `DATABASE_URL` pointing at a scratch SQLite file, and the experiment harness builds its own users, elections and chains there. "
          "The HTTP checks start a separate uvicorn process on port 18401 against another scratch file, so the product's ports 8401 and 5401 were not used."),
    ]


# --------------------------------------------------------------------------- 7.2
UNIT_ROWS = [
    ("test_password_hashing", "Argon2id hash differs from the password; correct password verifies, wrong one does not"),
    ("test_verhoeff_valid", "A generated Aadhaar number has 12 digits and a valid Verhoeff checksum (its negative assertion is weak, see below)"),
    ("test_invalid_checksum_rejection", "`DemoAadhaarProvider.verify` refuses 123456789012 with a checksum, format or not-found reason"),
    ("test_unknown_voter_rejection", "A checksum-valid number that is not in the registry fails with \"not found\""),
    ("test_ineligible_voter_rejection", "`issue_authorization` raises for a voter with no eligibility row"),
    ("test_duplicate_vote_rejection", "After one vote, a second authorisation and a replay of the old token both raise"),
    ("test_unauthorized_admin_route", "A voter session requesting the legacy `/admin` page is redirected or refused (accepts 302, 307, 401 or 403)"),
    ("test_unauthorized_auditor_route", "An admin session requesting `/auditor` is redirected or refused"),
    ("test_tampered_block_detection", "A valid chain passes; `tamper_test_clone` reports detection; overwriting a real block hash makes `validate_chain` fail"),
    ("test_invalid_previous_hash_rejection", "Overwriting a block's `previous_hash` makes `validate_chain` fail (field accepted: previous_hash or block_hash)"),
    ("test_duplicate_transaction_rejection", "`propose_block` with a reused nonce and transaction hash raises a \"duplicate\" error"),
    ("test_malformed_input_rejection", "Empty username and password on the login form give 400, 401 or 422"),
    ("test_expired_authorization_rejection", "A token whose expiry is moved five minutes into the past is refused as expired"),
    ("test_ballot_identity_separation", "The ledger transaction text contains neither the Aadhaar number nor the voter's name; `ballots` has no voter column"),
    ("test_audit_logging", "A failed login adds a row to `audit_logs`"),
    ("test_election_status_enforcement", "Casting in a PAUSED election raises \"not open\""),
    ("test_encryption_roundtrip", "AES-256-GCM decrypt(encrypt(\"42\")) returns \"42\""),
]


def _unit():
    rows = [[str(i), f"`{n}`", d, "Pass"] for i, (n, d) in enumerate(UNIT_ROWS, 1)]
    return [
        H2("7.2 Unit Tests"),
        P(f"The repository's test file holds {F.PYTEST_TOTAL} pytest tests. They were run with Python 3.11.9 and pytest 9.1.1 on a scratch database: **{F.PYTEST_PASSED} passed, {F.PYTEST_TOTAL - F.PYTEST_PASSED} failed, in {F.PYTEST_SECONDS} s**. "
          "The table below lists what each test checks."),
        TAB("The 17 pytest tests and their result", ["No.", "Test", "What it checks", "Result"], rows, widths=[0.4, 2.2, 3.2, 0.6], align=["c", "l", "l", "c"], size=9),
        P("Reading the tests critically gives four observations that bear on how much weight the green result deserves."),
        B("Most tests call the service layer (`issue_authorization`, `cast_vote`, `propose_block`, `validate_chain`) directly or use the legacy HTML routes; the JSON API that the React interface uses is exercised only by the HTTP checks of Section 7.3.",
          "The assertion in `test_verhoeff_valid` that should show a corrupted number is rejected is satisfied trivially (`not validate_verhoeff(\"123456789012\") or validate_verhoeff(a)`), and the corrupted number it builds is never used. The checksum itself is tested properly by the HTTP checks 10 and 11 of Section 7.3, which send a number whose last digit was changed.",
          "The two role tests accept several status codes (a redirect, 401 or 403), and the previous-hash test accepts either of two failing fields, so they show that access is not granted and that tampering is noticed, not exactly how.",
          "`test_tampered_block_detection` calls `tamper_test_clone` as well as editing the real database; the former only simulates the change in memory (Section 7.6), but the real edit that follows it does make `validate_chain` fail."),
    ]


# --------------------------------------------------------------------------- 7.3
def _http():
    rows = []
    for i, m in enumerate(F.MATRIX, 1):
        res = "Pass" if m["pass"] else "FAIL"
        rows.append([str(i), m["test"], str(m["expected"]), str(m["got"]), res])
    seq = F.HTTP.get("login_rate_limit_status_sequence", [])
    first429 = seq.index(429) + 1 if 429 in seq else None
    return [
        H2("7.3 Integration Tests over HTTP"),
        P(f"The integration tests drive a real uvicorn process through its JSON API, as the React interface does: one client per user, cookies kept, the CSRF token read from the login reply and sent as `X-CSRF-Token` on every POST. "
          f"The server and its database were created for the run (an election with three candidates, an administrator, an auditor, 28 voters with synthetic Verhoeff-valid Aadhaar numbers). "
          f"{F.MATRIX_PASSED} of the {F.MATRIX_TOTAL} checks returned the expected status (table below)."),
        TAB("HTTP security and functional checks: expected and observed status", ["No.", "Check", "Expected", "Got", "Result"], rows, widths=[0.4, 3.5, 0.8, 0.7, 0.7], align=["c", "l", "c", "c", "c"], size=9),
        P(f"Check 25 needs a remark. The login limiter allows ten attempts per minute from one address and it counted the four successful logins made just before the check, so the first rejection arrived on the {first429}th request of the burst "
          f"(status sequence {', '.join(str(x) for x in seq)}), not on the eleventh. The rule works; the check's wording \"11th\" is loose. Check 22 passes by design: the administrator can read a running tally of an election that is still open, "
          "a property that the success and failure analysis in Chapter 8 returns to as a limitation."),
    ]


# --------------------------------------------------------------------------- 7.4
def _functional():
    return [
        H2("7.4 Functional Tests"),
        P("Functional testing asks whether each function promised by the abstract and the objectives can be performed. The table below sets each function against the evidence collected and states where the evidence is thin."),
        TAB("Functions, evidence and outcome", ["Function", "Evidence", "Outcome"],
            [["Authenticate with a password", "Unit test 1; HTTP: login for 28 voters, an administrator and an auditor; empty body 422; injection-style name 401", "Works"],
             ["Verify identity with Aadhaar", "Unit tests 3-4; HTTP checks 9-12 and 15: short number, bad checksum, unknown number, another voter's number, own number", "Works against the synthetic registry; no real UIDAI service exists in the product"],
             ["One voter, one vote", "Unit tests 5-6; HTTP checks 18-19 (replay, second verification); database constraints UNIQUE(election, voter) on three tables", "Works; four layers each refuse a second vote"],
             ["Cast an encrypted ballot and obtain a receipt", "Unit tests 14 and 17; HTTP check 17; 28 receipts from the HTTP run; screenshots 17-19", "Works"],
             ["Immutable record in a ledger", "Unit tests 9-11; Section 7.6", "Partly: hash links are checked, signatures and the tally source are not"],
             ["Administer elections and candidates", "HTTP checks 20-21; screenshots 11-13; the screenshot run created an election and candidates through the interface", "Works; no test edits a candidate beyond activate and deactivate"],
             ["Results when the poll closes", "Check 14 (404 while open for a voter); screenshots 14 and 20; the seeded closed election tallies 8 ballots", "Works"],
             ["Chronological audit trail", "Unit test 15; the development database holds audit rows for login, verification, vote, status and integrity actions", "Works"],
             ["Voter registration", "No self-registration route exists in `api_v1.py`; voters are created by the seed script or the benchmark", "Not provided as a user function"],
             ["Polling window", "Start and end times are stored and shown; a search of the code finds no comparison of them with the clock when a vote is cast, only the status OPEN", "Not enforced automatically; the administrator opens and closes the poll"]],
            widths=[1.6, 3.4, 1.5], align=["l", "l", "l"], size=9),
        P("Besides the pytest and HTTP evidence, the repository holds `scripts/smoke_test.py`, a standard-library script that needs both servers running: it creates a \"Smoke Test\" election, casts a ballot with a seeded voter, closes the election and checks the ledger. "
          "It was run by the interface build on 19 October 2026; its election and one ballot are visible in the development database and in screenshot 04. It was not re-run for this report, and no pass count from it is quoted."),
    ]


# --------------------------------------------------------------------------- 7.5
def _security():
    ck = F.HTTP.get("cookie_header", {}).get("Set-Cookie", "")
    flags = ck.split(";", 1)[1].strip() if ";" in ck else ""
    return [
        H2("7.5 Security Tests"),
        P("The security-relevant checks of Section 7.3 are grouped below by the property they test."),
        TAB("Security properties and the checks that cover them", ["Property", "Checks", "Observation"],
            [["Authentication required", "1, 2", "Anonymous calls to an admin and a voter route return 401"],
             ["Role-based access control", "5, 6, 7", "A voter session receives 403 from the admin and auditor routes and cannot change an election's status"],
             ["Cross-site request forgery", "8", "A POST without the `X-CSRF-Token` header is refused with 403 even with a valid session cookie"],
             ["Injection-style input", "3", "The username `admin' OR '1'='1` returns 401, not an error; queries are built by SQLAlchemy with bound parameters"],
             ["Input validation", "4, 9, 10, 16, 20, 21", "Empty body 422; Aadhaar of 11 digits 400; wrong checksum 400; unknown candidate 400; unknown status 400; end before start 400"],
             ["Identity binding", "11, 12", "A checksum-valid number that is not registered fails with 400; another voter's registered number fails with 403"],
             ["Replay and duplicates", "13, 18, 19", "A forged token fails; a used token fails; a second verification after voting fails; unit test 6 adds the same at service level"],
             ["Brute-force limit", "25", "After ten login attempts in a minute the server answers 429; the same limiter guards verification at fifteen per minute"],
             ["Audit of failures", "unit test 15", "Failed logins, failed verifications and rejected votes each write an audit row"]],
            widths=[1.7, 1.0, 3.8], align=["l", "c", "l"], size=9),
        P(f"Three weaknesses were also confirmed by observation and are reported here so that the green checks are not over-read."),
        B(f"**No Secure flag and no TLS.** The session cookie is issued as `{flags}`. It is HttpOnly and SameSite=lax, but there is no `Secure` attribute because the application is served over plain HTTP; the abstract's TLS requirement is not met by the shipped configuration.",
          f"**Per-address rate limit.** The limiter keys on the client's IP address and lives in memory. Ten voters signing in within a minute from one address, such as a polling station behind one NAT gateway, would lock out the eleventh; "
          "conversely an attacker with many addresses is not slowed.",
          f"**Voter and ballot are linkable in the database.** After the HTTP run, {F.HTTP.get('db_linkable_voter_ballot_rows')} of {F.HTTP.get('db_ballots')} ballots could be joined to a voter through `voter_participation` (voter id and ballot id are stored together). "
          "The unit test of identity separation passes because it looks only at the ledger transaction and the ballots table, which indeed carry no identity; the third table undoes the separation for anyone who can read the database."),
    ]


# --------------------------------------------------------------------------- 7.6
def _tamper():
    rows = []
    for c in F.TAMPER_CASES:
        pc = f"Detected ({c['validate_chain_field']})" if c["validate_chain_detects"] else "**Missed**"
        sa = f"Detected ({c['strict_audit_stage']})" if c["strict_audit_detects"] else "Missed"
        tc = {None: "-", True: "Yes", False: "No"}[c["tally_changed"]]
        rows.append([c["case"].split(" ")[0], c["description"], pc, sa, tc])
    t = F.TAMPER
    return [
        H2("7.6 Tamper-Detection Tests"),
        P(f"The central claim of the project is that an edit to a recorded vote does not go unnoticed. To test it, a scratch chain of {t['chain_height']} blocks ({t['chain_height'] - 1} votes) was built through the real voting service. "
          "Thirteen kinds of tampering were then applied one at a time inside a database transaction, checked, and rolled back. Two checks were applied to each: the product's own `validate_chain` (the function behind the auditor's \"Verify ledger integrity\" button "
          "and `/api/chain/verify`), and a stricter audit written only for this study, in `scripts/run_experiments.py`. The stricter audit additionally verifies the three validators' Ed25519 signatures on each block hash, recomputes every transaction hash from its fields, "
          "verifies the system signature on each transaction, and compares the `ballots` table with the ledger. **The stricter audit is not part of the product.**"),
        TAB("Tamper cases and whether each check detects them", ["Case", "Tampering applied", "Product check", "Stricter audit", "Tally changed"], rows,
            widths=[0.5, 2.7, 1.3, 1.5, 0.6], align=["c", "l", "l", "l", "c"], size=8.5),
        P(f"The baseline chain passes both checks. The product check detects **{F.N_TAMPER_PRODUCT} of {F.N_TAMPER}** cases; the stricter audit detects all {F.N_TAMPER_STRICT}. The seven detected cases are all edits to a hash, a root, a timestamp, a link or a row that the check recomputes. "
          "The six missed cases share a cause: `validate_chain` recomputes the Merkle root, the block hash and the link to the previous block from the stored values, but it never verifies a signature, never recomputes a transaction hash from the transaction's own fields, "
          "and never looks at the `ballots` table, from which the final tally is computed."),
        B("**T6, T7.** Replacing the ciphertext in a ledger transaction, or in the `ballots` row that the tally reads, is invisible to the product check. In T7 the tally changes (last column of the table) while the auditor's page still reports a healthy chain.",
          "**T10.** Removing the newest block leaves a shorter but internally consistent chain. The stricter audit finds it only because a ballot then refers to a transaction that is no longer in the ledger.",
          "**T11-T13.** Forged signatures, or an attacker who edits a ballot and recomputes every hash from that block to the tip, pass the product check. Only signature verification exposes them, and only so long as the attacker does not also hold the validators' private keys, "
          "which sit in `data/validators.json` on the same server. The study therefore bounds what the quorum of three provides: it is a simulation of distributed approval, not distributed trust."),
        P(f"Cost: on the {t['chain_height']}-block chain the product check took {_c(t['validate_chain_ms_median'])} ms and the stricter audit {_c(t['strict_audit_ms_median'])} ms, about five times the product check because it verifies about four signatures per block and recomputes every transaction hash. "
          "A second finding concerns the auditor's \"tamper-detection demo\" button. `tamper_test_clone` does not run `validate_chain` on a modified copy; it overwrites a hash in a list in memory and returns a detection result from a hash-link comparison. "
          "It demonstrates the principle but is not an independent test, and the \"Tampering detected on the clone\" message in screenshot 21 should be read in that light."),
    ]


# --------------------------------------------------------------------------- 7.7
def _edge():
    return [
        H2("7.7 Validation and Edge Cases"),
        P("Edge cases were chosen at the boundaries of each rule. The HTTP checks and the unit tests cover the following; items marked (code only) were read from the source and not separately tested."),
        B("**Identity input:** 11 digits; 12 digits with a changed check digit; 12 valid digits not in the registry; another voter's valid number; Aadhaar numbers typed with spaces or hyphens (the provider strips them before checking; code only).",
          "**Token lifecycle:** forged token; token already used; token whose expiry has passed (unit test 13); a second issue while one is pending (refused as \"already issued and pending\"; code only); a second verification after voting.",
          "**Election state:** casting in a PAUSED election (unit test 16); results of an OPEN election requested by a voter (404) and by the administrator (200); a closed election's results readable by every signed-in role.",
          "**Administrator input:** unknown status; end before start; empty title or candidate name (rejected by the request models' length limits; code only).",
          "**Ledger:** duplicate nonce and duplicate transaction hash (unit test 11); an altered `previous_hash` (unit test 10)."),
        P("Two boundaries were not exercised. The polling window is not compared with the clock (Section 7.4), so there is no test of a vote cast after the stated end time, and the behaviour of the quorum when one validator rejects a block cannot be reached from the product: "
          "all three validators run the same checks in the same process, so they approve or reject together."),
    ]


# --------------------------------------------------------------------------- 7.8
def _perf():
    s = F.BENCH_SYNC
    brs = F.BENCH_BATCH
    lo_tp, hi_tp, lo_ms, hi_ms = _idle_range()
    rows = [["Synchronous", _c(s["total_duration"]), _c(s["throughput"]), _c(s["mean_ms"]), _c(s["median_ms"]), _c(s["p95_ms"]), _c(s["max_ms"])]]
    for k, v in brs.items():
        rows.append([f"\"Batched\", size {k}", _c(v["total_duration"]), _c(v["throughput"]), _c(v["mean_ms"]), _c(v["median_ms"]), _c(v["p95_ms"]), _c(v["max_ms"])])
    idle = [[str(d["voters_count"]), _c(d["sync"]["throughput"]), _c(d["sync"]["mean_ms"], 2),
             f"{d['async_batches']['10']['throughput']:.1f} / {d['async_batches']['20']['throughput']:.1f} / {d['async_batches']['30']['throughput']:.1f}"] for d in F.IDLE_RUNS]
    vh = F.VALIDATE_BY_HEIGHT
    grow_rows = [[k, str(v["height_blocks"]), _c(v["median_ms"])] for k, v in vh.items()]
    names = {"sha256_tx_payload": "SHA-256 of a transaction", "aes256gcm_encrypt": "AES-256-GCM encrypt", "aes256gcm_decrypt": "AES-256-GCM decrypt", "ed25519_sign": "Ed25519 sign",
             "ed25519_verify": "Ed25519 verify", "verhoeff_validate": "Verhoeff check of 12 digits", "aadhaar_salted_sha256": "Aadhaar salted SHA-256", "argon2id_hash": "Argon2id hash (password)", "argon2id_verify": "Argon2id verify (login)"}
    mt = [[names[k], f"{v['n']:,}", f"{v['mean_ms']:.4g}", f"{v['p95_ms']:.4g}"] for k, v in F.MICRO.items()]
    fa, f1_, l1 = G["per_vote_all"], G["per_vote_first_100"], G["per_vote_last_100"]
    http_rows = [[nm, _c(LT[k]["mean_ms"]), _c(LT[k]["median_ms"]), _c(LT[k]["p95_ms"]), _c(LT[k]["max_ms"])] for k, nm in
                 (("login", "Login (Argon2id verify)"), ("verify", "Aadhaar verification"), ("cast", "Cast (encrypt, sign, block, commit)"), ("end_to_end", "Whole voter journey"))]
    tot = ST["authorise"] + ST["encrypt_sign_hash"] + ST["propose_block"] + ST["persist"]
    return [
        H2("7.8 Performance Tests"),
        H3("7.8.1 The product's own benchmark with 1000 voters"),
        P(f"The benchmark shipped with the product (`python -m app.benchmarks.run_benchmark --voters {F.N_VOTERS_BENCH}`) generates synthetic voters with Argon2-hashed passwords and Verhoeff-valid Aadhaar numbers, then times a vote as authorisation plus cast "
          "(encryption, signature, three-validator block, database commit), called in-process with no HTTP. It was run on a scratch database; all 1000 votes succeeded in every mode and none failed. The 1000-voter size was chosen because the base paper also used 1000 synthetic voters."),
        TAB("Benchmark of 1000 voters (shared PC)", ["Mode", "Total s", "Votes/s", "Mean ms", "Median ms", "p95 ms", "Max ms"], rows, widths=[1.6, 0.8, 0.8, 0.8, 0.9, 0.8, 0.8], align=["l", "r", "r", "r", "r", "r", "r"], size=9.5),
        P("**The batched rows are not concurrent.** In `run_benchmark.py` each batch is processed by a loop in one thread; the code comment itself says that asynchrony is simulated. The per-vote latency of a batch is the batch's duration divided by its size. "
          "The differences between batch sizes in the table (22.5, 37.5 and 22.3 votes per second) therefore reflect only what else the PC was doing at the time, not an effect of batching. This differs from the base paper, whose asynchronous batches really were submitted in parallel to a chain."),
        FIG(F.fig("f01_benchmark_1000.png"), "Throughput and per-vote latency of the 1000-voter benchmark in synchronous mode and in the three sequential batch sizes.", 5.9),
        H3("7.8.2 The same code on an idle machine"),
        P(f"Five runs with 50, 200 and 500 voters, committed with the product on 8 September 2026, were made on an idle PC. They give {_c(lo_ms, 2)} to {_c(hi_ms, 2)} ms per vote, about {_c(lo_tp, 0)} to {_c(hi_tp, 0)} votes per second, "
          f"almost constant across voter counts and batch sizes. The 1000-voter run above, made while other jobs were running, was about {s['mean_ms'] / ((lo_ms + hi_ms) / 2):.1f} times slower on average. Both are reported because neither alone is the \"true\" speed: the first is the best case of the code, the second a realistic shared machine."),
        TAB("Earlier benchmark runs on an idle PC (8 September 2026)", ["Voters", "Sync votes/s", "Sync mean ms", "Batches 10 / 20 / 30, votes/s"], idle, widths=[1.0, 1.4, 1.4, 2.7], align=["c", "r", "r", "c"], size=9.5),
    ] + ([] if F.REPORT else [
        FIG(F.fig("f02_benchmark_runs.png"), "Synchronous throughput of the five idle-PC runs and the 1000-voter run on a loaded PC.", 5.5),
    ]) + [
        H3("7.8.3 Growth along the chain"),
        P(f"Two measurements show how cost grows as the chain lengthens. First, 300 votes were cast one after another on a growing chain: mean {_c(fa['mean_ms'])} ms, median {_c(fa['median_ms'])} ms, p95 {_c(fa['p95_ms'])} ms; "
          f"the first hundred votes averaged {_c(f1_['mean_ms'])} ms and the last hundred {_c(l1['mean_ms'])} ms, so the cost of a vote did not grow visibly over 300 blocks (it needs only the last block and two indexed uniqueness look-ups). "
          "Second, the time of `validate_chain` was taken at five chain lengths (median of five calls):"),
        TAB("validate_chain time against chain length", ["Votes cast", "Blocks", "Median ms"], grow_rows, widths=[1.4, 1.4, 1.4], align=["c", "c", "r"], size=10),
        P("The check is linear in the number of blocks, about 0.5 ms per block, because it queries each block's transactions separately. At this rate a chain of 100,000 blocks would take close to a minute to verify; "
          "this extrapolation is arithmetic from the linear trend, not a measurement."),
        FIG(F.fig("f03_validate_chain_growth.png"), "Time of the integrity check against chain length.", 4.8),
    ] + ([] if F.REPORT else [
        FIG(F.fig("f09_vote_cost_growth.png"), "Per-vote cost for the first hundred, all three hundred and the last hundred votes of a growing chain.", 4.8),
    ]) + [
        H3("7.8.4 Where a vote spends its time"),
        P(f"One vote was split into four stages and timed on 60 further votes (mean milliseconds): authorisation {_c(ST['authorise'], 2)}, encryption, hashing and signing {_c(ST['encrypt_sign_hash'], 2)}, "
          f"`propose_block` with the three validators {_c(ST['propose_block'], 2)}, and persisting the ballot, token and participation row {_c(ST['persist'], 2)}; the sum is {_c(tot, 2)} ms. "
          "The cryptography is under one millisecond; the time goes to database round trips, which is why a vote costs about as much as a handful of SQLite queries."),
        FIG(F.fig("f04_vote_stage_breakdown.png"), "Mean time of the four stages of a vote.", 4.8),
        H3("7.8.5 Cost of the primitives"),
        TAB("Micro-timings of the cryptographic and identity primitives", ["Operation", "Calls timed", "Mean ms", "p95 ms"], mt, widths=[2.8, 1.1, 1.1, 1.1], align=["l", "r", "r", "r"], size=9.5),
        P("Password hashing with Argon2id costs about 80 ms per call, several hundred times the cost of all the cryptography of a vote taken together (AES-GCM, SHA-256 and Ed25519 signing add up to " + _c(F.MICRO["aes256gcm_encrypt"]["mean_ms"] + F.MICRO["sha256_tx_payload"]["mean_ms"] + F.MICRO["ed25519_sign"]["mean_ms"], 2) + " ms). "
          "That is deliberate - slowness is the purpose of a password hash [" + str(R['argon2']) + "] - and it explains why login dominates the HTTP times below. The Verhoeff check and the salted lookup hash cost microseconds."),
        FIG(F.fig("f05_micro_timings.png"), "Cost of each primitive on a logarithmic scale.", 5.6),
        H3("7.8.6 Latency through HTTP"),
        P(f"Twenty-seven voters each signed in, verified an Aadhaar number and cast a vote through uvicorn on 127.0.0.1, nine per minute because of the login limiter. A complete journey took {_c(LT['end_to_end']['mean_ms'], 0)} ms on average "
          f"(p95 {_c(LT['end_to_end']['p95_ms'], 0)} ms); {_c(LT['login']['mean_ms'], 0)} ms of it is the login. The auditor's integrity check through the API took {F.HTTP.get('auditor_verify_ms')} ms on a {F.HTTP.get('auditor_verify_result', {}).get('height')}-block chain."),
        TAB("Latency of the voter journey over HTTP (27 voters, milliseconds)", ["Step", "Mean", "Median", "p95", "Max"], http_rows, widths=[2.8, 0.9, 0.9, 0.9, 0.9], align=["l", "r", "r", "r", "r"], size=9.5),
        P("The times are for a single client on the same machine as the server, so they include no network delay and no queueing. They say nothing about how the system behaves when many voters arrive together."),
    ]


# --------------------------------------------------------------------------- 7.9 - 7.11
def _tail():
    return [
        H2("7.9 User Acceptance"),
        P("No user study was carried out. No election official, auditor or voter outside the project team used the application, no usability questionnaire was administered, and no accessibility audit was made. "
          "What exists is a scripted walk-through: `scripts/capture_screens.py` drives a browser through every screen with real data (sign in as each role, create an election, add candidates, verify an Aadhaar number, vote, read the receipt, verify the ledger) and "
          "fails if the browser console shows an error or an API call returns an unexpected 4xx or 5xx. The 23 screenshots of Chapter 8 are its output. A walk-through shows that the screens work in sequence; it is not evidence that voters find them clear."),
        H2("7.10 Limits of the Testing Done"),
        B("**Concurrency was not tested.** Only one vote is in flight at a time in every test and benchmark. A block takes `last block index + 1` and the index is unique in the database, so two simultaneous votes would race and one could fail; no test shows how the product behaves.",
          "**The \"asynchronous\" benchmark is sequential**, so no throughput under parallel load exists, and the base paper's parallel batches have no counterpart here.",
          "**The machine was shared.** Absolute latencies vary by a factor of two between runs on the same code; relative statements (cryptography is negligible, Argon2id dominates, validation is linear) are robust, absolute ones are not.",
          "**Scale.** The 1000-voter benchmark built a chain of about 4,000 blocks, but validation time was measured only up to 301 blocks; larger sizes are extrapolations.",
          "**No penetration test, fuzzing or code audit** was performed. The security checks are the ones in Section 7.3.",
          "**The stricter audit is not in the product.** It shows what a better check would catch; it does not mean the delivered product catches it.",
          "**Synthetic identities only.** No real Aadhaar number, registry or UIDAI interface was involved, so nothing here validates real-world identity assurance.",
          f"**Smoke test not re-run** for this report; the pytest and HTTP results are fresh, the smoke test is cited only for its existence."),
        H2("7.11 Summary of Testing"),
        TAB("Summary of results", ["Level", "Result"],
            [["Unit tests", f"{F.PYTEST_PASSED} of {F.PYTEST_TOTAL} passed ({F.PYTEST_SECONDS} s), with some weak assertions noted"],
             ["HTTP checks", f"{F.MATRIX_PASSED} of {F.MATRIX_TOTAL} returned the expected status"],
             ["Tamper study", f"Product check detects {F.N_TAMPER_PRODUCT} of {F.N_TAMPER} cases; stricter audit {F.N_TAMPER_STRICT} of {F.N_TAMPER}"],
             ["Benchmark, 1000 voters", f"1000 of 1000 votes succeeded; mean {_c(F.BENCH_SYNC['mean_ms'])} ms per vote on a loaded PC, about 16-17 ms on an idle PC"],
             ["HTTP journey", f"{_c(LT['end_to_end']['mean_ms'], 0)} ms mean for login, verification and cast"],
             ["Not provided", "Concurrency tests, user study, penetration test, TLS, real identity service"]],
            widths=[1.8, 4.7], align=["l", "l"], size=10),
    ]


def blocks():
    return ([H1("CHAPTER 7: SYSTEM TESTING")] + _strategy() + _unit() + _http() + _functional() + _security() + _tamper() + _edge() + _perf() + _tail())
