"""Chapter 8: Results and output screens. Every number is read from facts.py (experiments/voting/*.json, docs/metrics/tests.json);
the sample receipt values were read once, read-only, from the development database that the screenshots were taken from."""

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, PAIR, TAB
from .refs import CITE as R

SH = F.shot
LT = F.LAT
S = F.BENCH_SYNC


def _c(x, d=1):
    return f"{x:,.{d}f}"


def _cap(name, text):
    return (SH(name), text)


# --------------------------------------------------------------------------- 8.1
def _setup():
    e = F.ENV
    return [
        H2("8.1 Experimental Set-up and Data"),
        P("This chapter reports what the finished application did when it was run. AegisBallot has no trained model and no external dataset, so the usual accuracy table does not exist; the evidence is of four kinds: "
          "what the screens show, how fast the system is, whether its controls hold, and whether tampering is detected."),
        TAB("What was measured and on what", ["Item", "Content", "Source and status"],
            [["Output screens", "23 screenshots, 22 at 1440 x 900 pixels and one at phone width", "Captured by `scripts/capture_screens.py` from the running app (Chrome via Playwright)"],
             ["Screen data", "200 registered voters, 8 elections, 212 ballots, 213 blocks, 3 validators", "The development database after seeding, the benchmark runs, the smoke test and the screenshot walk; all identities synthetic"],
             ["Unit tests", f"{F.PYTEST_TOTAL} pytest tests", "`tests/test_aegis.py`, scratch database"],
             ["HTTP checks", f"{F.MATRIX_TOTAL} security and functional checks", "`scripts/run_experiments.py` part D, live uvicorn, scratch database"],
             ["Tamper study", f"{F.N_TAMPER} kinds of tampering on a {F.TAMPER.get('chain_height')}-block chain", "Part C of the same harness, rolled back after each case"],
             ["Benchmarks", f"{F.N_VOTERS_BENCH} synthetic voters; five earlier idle-PC runs of 50 to 500 voters", "The product's `run_benchmark`; `benchmark_results/`"]],
            widths=[1.3, 2.6, 2.6], align=["l", "l", "l"], size=9.5),
        P(f"All timings come from one PC (Intel Core i5-12500, 15.7 GB, Windows 11 Pro, Python {e.get('python', '3.11.9')}) that was shared with other jobs, so absolute latencies are upper bounds and vary between runs by up to a factor of two. "
          "The screens, tests and measurements use no real personal data: voters, Aadhaar numbers and names are generated, and the Aadhaar registry is a local table of salted hashes. Statistical significance tests were not applied; "
          "the quantities are deterministic checks (pass or fail) and timings whose spread is shown by the mean, median and 95th percentile."),
    ]


# --------------------------------------------------------------------------- 8.2
def _screens():
    return [
        H2("8.2 Output Screens"),
        P("All 23 screens of the application are shown, grouped by who sees them. They were captured from the running React interface (port 5401) against the FastAPI server (port 8401) holding the data listed above, "
          "after real sign-ins, real elections and real votes; no screen is a mock-up. The counters grow by one between the early and the late screens (211 ballots and 212 blocks on the landing page and the dashboard, 212 ballots and 213 blocks on the auditor page) "
          "because the voter walk-through of screens 17 to 19 casts one more ballot. The purple-and-dark theme is the default; screens 05 to 08 repeat the landing page in the light theme."),
        H3("8.2.1 Public pages and sign-in"),
        PAIR([_cap("01_landing_dark.png", "Landing page (dark theme): the headline, a \"demonstration environment - synthetic identities only\" badge, and a live-ledger card listing the latest blocks (209 to 211) with their \"2/3 signed\" status and \"chain valid\"."),
              _cap("02_landing_dark_stats_and_features.png", "Landing page, live figures: 8 elections, 211 ballots recorded, 212 blocks, 3 validator nodes, read from `/api/public/overview`, and the three feature cards (encrypted ballots, ledger integrity, independent audit).")], 2.8),
        PAIR([_cap("03_landing_dark_how_it_works.png", "Landing page, \"How it works\": the four steps (verify who you are, one-time authorisation, encrypted ballot, ledger receipt), with step 1 expanded. The capture caught the header over the section title."),
              _cap("04_landing_dark_elections.png", "Landing page, \"What is on the ballot\": all eight elections with their status and window, including the closed Community Welfare Board 2026 and the smoke-test election.")], 2.8),
        PAIR([_cap("05_landing_light.png", "Landing page in the light theme (toggle in the header)."),
              _cap("06_landing_light_stats_and_features.png", "Light theme: live figures and feature cards.")], 2.8),
        PAIR([_cap("07_landing_light_how_it_works.png", "Light theme: the four-step explanation."),
              _cap("08_landing_light_elections.png", "Light theme: the election list.")], 2.8),
        PAIR([_cap("09_login.png", "Sign-in page: username and password, the demonstration badge and quick-fill buttons for the admin, voter and auditor demo accounts; voters are voter1 to voter20.")], 2.8),
        H3("8.2.2 Administrator screens"),
        PAIR([_cap("10_admin_dashboard.png", "Administrator dashboard: 200 registered voters, 211 votes cast across 8 elections, ledger height 212 with a \"ledger healthy\" badge, a turnout-by-election bar chart (a tooltip shows 0 of 20 for Campus Council) and the three validators, all active, quorum 2 of 3."),
              _cap("11_admin_elections.png", "Elections list: each card shows status, window, votes against eligible voters and a progress bar, with Open, Pause, Close, Results and Manage controls. The benchmark elections show 50 of 50 voted.")], 2.8),
        PAIR([_cap("12_admin_create_election.png", "\"Create an election\" dialog: title, description, start and end. A new election starts as a draft and every registered voter is made eligible automatically."),
              _cap("13_admin_election_detail.png", "Election detail for the Screenshot Demo Election: 200 eligible voters, 2 votes, 1.0 % turnout, the three candidates with party and manifesto, and Add candidate and Deactivate controls.")], 2.8),
        PAIR([_cap("14_results.png", "Results of the closed Community Welfare Board 2026: 8 ballots decrypted for the count, a vote-share chart and a ranked table (3, 3 and 2 votes; the first two marked \"tied for lead\")."),
              _cap("15_admin_benchmarks.png", "Performance benchmarks: the stored run of 50 voters (62.2 operations per second synchronous, 61.7 batched, mean latency 16.1 ms), throughput and latency charts and the list of recent runs.")], 2.8),
        PAIR([_cap("23_mobile_admin_dashboard.png", "The administrator dashboard at phone width (390 x 844): the layout collapses to one column with a bottom navigation bar.")], 2.8),
        H3("8.2.3 Voter screens"),
        PAIR([_cap("16_voter_elections.png", "Voter home (voter3, shown as Aditya Verma): open elections with \"Verify and vote\", a closed election with \"View results\" and, where the voter has already voted, a \"Vote confirmed\" box with the receipt id."),
              _cap("17_voter_aadhaar_verification.png", "Step 1 of 3, Aadhaar verification: the masked number on file, the 12-digit entry field and the note that only a salted hash is kept.")], 2.8),
        PAIR([_cap("18_voter_candidate_selection.png", "Step 2 of 3: identity verified, a ten-minute countdown for the one-time authorisation, three candidate cards with one selected and a \"Confirm and submit vote\" bar that warns that the choice is encrypted and cannot be changed."),
              _cap("19_voter_receipt.png", "Step 3 of 3, receipt: ballot receipt id, transaction hash, block number 212 and block hash, with the statement that two of three validators signed the block and that the receipt does not reveal the candidate.")], 2.8),
        PAIR([_cap("20_voter_elections_after_vote.png", "Voter home after voting: the Screenshot Demo Election now shows \"Vote confirmed\" with the receipt id and \"Your ballot is sealed; results appear when the election closes\".")], 2.8),
        H3("8.2.4 Auditor screens"),
        PAIR([_cap("21_auditor_dashboard.png", "Auditor ledger audit: 213 blocks and the tip hash, \"Verified just now: all 213 blocks are consistent\", the result of the tamper-detection demo on a clone, the validator list and tabs for blocks, transactions and the audit log."),
              _cap("22_auditor_block_detail.png", "Block detail (block 1): index, timestamp, number of transactions, previous hash, Merkle root, block hash and the three validator signatures (3 of 3 signed, quorum 2), with previous and next navigation.")], 2.8),
        P("Reading the screens together, the interface covers the three roles end to end. It also contains one visible limitation that the next sections explain: screen 21 labels its demonstration \"safe: it uses a cloned copy\", and the message \"Tampering detected on the clone\" comes from a simulated change (Section 7.6)."),
    ]


# --------------------------------------------------------------------------- 8.3
def _perf():
    lat_rows = [[nm, _c(LT[k]["mean_ms"]), _c(LT[k]["median_ms"]), _c(LT[k]["p95_ms"])] for k, nm in
                (("login", "Login"), ("verify", "Aadhaar verification"), ("cast", "Cast a ballot"), ("end_to_end", "Whole journey"))]
    lo = min(d["sync"]["mean_ms"] for d in F.IDLE_RUNS)
    hi = max(d["sync"]["mean_ms"] for d in F.IDLE_RUNS)
    vh = F.VALIDATE_BY_HEIGHT
    last = list(vh.values())[-1]
    return [
        H2("8.3 System Performance Results"),
        P("Since there is no classifier to score, \"model performance\" here means how quickly the system does its work. The table below gives the headline results; the full tables and charts are in Chapter 7."),
        TAB("Headline performance results", ["Quantity", "Result", "Conditions"],
            [["Votes completed in the 1000-voter benchmark", f"1000 of 1000 in every mode, 0 failures", "In-process, scratch database"],
             ["Mean time per vote, synchronous", f"{_c(S['mean_ms'])} ms (median {_c(S['median_ms'])}, p95 {_c(S['p95_ms'])})", "Shared PC"],
             ["Throughput, synchronous", f"{_c(S['throughput'])} votes per second", "Shared PC"],
             ["Mean time per vote on an idle PC", f"{_c(lo)} to {_c(hi)} ms (about 60 votes per second)", "Five earlier runs, 50-500 voters"],
             ["Whole voter journey over HTTP", f"{_c(LT['end_to_end']['mean_ms'], 0)} ms mean, p95 {_c(LT['end_to_end']['p95_ms'], 0)} ms", "27 voters, 127.0.0.1"],
             ["Of which login (Argon2id)", f"{_c(LT['login']['mean_ms'], 0)} ms mean", "Same run"],
             ["Cast a ballot over HTTP", f"{_c(LT['cast']['mean_ms'], 0)} ms mean", "Same run"],
             ["Integrity check of 301 blocks", f"{_c(last['median_ms'], 0)} ms median, linear in chain length", "In-process, median of 5"],
             ["Cryptography of one vote (AES-GCM, SHA-256, Ed25519 sign)", f"{_c(F.MICRO['aes256gcm_encrypt']['mean_ms'] + F.MICRO['sha256_tx_payload']['mean_ms'] + F.MICRO['ed25519_sign']['mean_ms'], 2)} ms", "Micro-timing means"]],
            widths=[2.6, 2.3, 1.6], align=["l", "l", "l"], size=9.5),
        P(f"Three results stand out. First, the work a vote does with cryptography is negligible; the cost of {_c(F.STAGE['propose_block'] + F.STAGE['authorise'] + F.STAGE['persist'], 0)} ms of the vote is database work. "
          f"Second, login is the slowest step by design, {_c(LT['login']['mean_ms'], 0)} ms against {_c(LT['verify']['mean_ms'], 0)} ms for the Aadhaar check and {_c(LT['cast']['mean_ms'], 0)} ms for the cast. "
          "Third, the benchmark's batch sizes make no difference because the batches are sequential, and the throughput of the 1000-voter run is about one third of the idle-machine figure because the PC was busy."),
        FIG(F.fig("f07_http_latency.png"), "Latency of login, Aadhaar verification, cast and the whole voter journey through HTTP (27 voters).", 5.3),
    ]


# --------------------------------------------------------------------------- 8.4
def _security_results():
    return [
        H2("8.4 Security and Integrity Results"),
        P(f"The unit tests passed ({F.PYTEST_PASSED} of {F.PYTEST_TOTAL}) and every one of the {F.MATRIX_TOTAL} HTTP checks returned the status it should: unauthenticated and wrongly-roled requests were refused (401, 403), a request without the CSRF header was refused, "
          "short, mis-checksummed, unregistered and foreign Aadhaar numbers were refused (400, 403), forged and replayed tokens were refused, a voter could not see a running tally (404), and the eleventh login attempt in a minute was throttled (429)."),
        P(f"The tamper study gave the mixed result that matters most for a voting system. Of {F.N_TAMPER} kinds of tampering applied to a stored chain, the product's integrity check detected **{F.N_TAMPER_PRODUCT}** and missed **{F.N_TAMPER - F.N_TAMPER_PRODUCT}**. "
          f"A stricter audit that also verifies validator signatures, recomputes transaction hashes and compares the ballots table with the ledger detected all {F.N_TAMPER_STRICT}. The figure below shows the cases."),
        FIG(F.fig("f06_tamper_matrix.png"), f"Result of the tamper study: {F.N_TAMPER_PRODUCT} of {F.N_TAMPER} cases are detected by the product's check, all by the stricter audit.", 5.3),
        P("The detected cases are the ones a hash chain is built for: a changed block hash, previous hash, Merkle root, timestamp or transaction hash, a deleted transaction, a deleted middle block. "
          "The missed cases are the ones that need signatures or a link between the ledger and the table the tally reads: an edited ciphertext (in the ledger or in the ballots table), a deleted newest block, forged validator signatures, and an edit followed by a full re-hash from that block to the tip. "
          "Two of the missed cases (edited ballots table, and ballots plus ledger edited together with all hashes recomputed) change the result of the election while the auditor's page keeps reporting a healthy chain."),
    ]


# --------------------------------------------------------------------------- 8.5
def _compare():
    return [
        H2("8.5 Comparison with the Base Paper"),
        P(f"The base paper [{R['base']}] proposes and simulates an Ethereum-based model for Oman; the closest related proposal that names Aadhaar is [{R['newera']}], which reports no performance or tamper evaluation. "
          "The comparison below is of design and of orders of magnitude only. **The two evaluations differ in chain, hardware, language, definition of a transaction and security guarantees, so the numbers must not be read as a head-to-head benchmark.**"),
        TAB("AegisBallot against the base paper", ["Aspect", "Base paper (Oman model)", "AegisBallot"],
            [["Ledger", "Ethereum nodes (Geth test chain via Nethereum) with smart contracts; Layer-1 public-chain technology", "Local hash-chained ledger in SQLite; three validator keys in one process; no smart contracts, not Ethereum"],
             ["Decentralisation", "Distributed nodes each holding a copy of the chain", "None: one server, one database; the quorum of 2 of 3 simulates approval"],
             ["Voter authentication", "Biometric authentication in the simulation; National-ID data in the synthetic population", "Password (Argon2id) plus Aadhaar number checked by Verhoeff checksum and a salted-hash registry; synthetic registry, no UIDAI"],
             ["Application stack", "C# / .NET Core 7 clients and web tier, MySQL, Ethereum", "Python FastAPI, SQLAlchemy and SQLite, React"],
             ["Administration", "Administrators register officers, voters and candidates and deploy contracts", "Admin console for elections, candidates, status; auditor console; audit log"],
             ["Workload", "1000 synthetic voters; registration and voting transactions", f"{F.N_VOTERS_BENCH} synthetic voters, vote only (registration is not a transaction here)"],
             ["Hardware", "Intel i7-12700, 12 cores, 16 GB, Windows 10", "Intel i5-12500, 6 cores / 12 threads, 15.7 GB, Windows 11; shared with other jobs"],
             ["Synchronous time per transaction", "About 2000 ms (registration) and 4000 ms (voting), read from Figure 6", f"Vote {_c(S['mean_ms'])} ms on the loaded PC, about 16-17 ms idle; cast over HTTP {_c(LT['cast']['mean_ms'], 0)} ms"],
             ["Asynchronous batches", "Batches of 10, 20, 30 and 50 submitted concurrently; about 2000 ms and 3000 ms per transaction for a batch of 10 (Figure 9)", "Batches of 10, 20 and 30 processed one after another; no concurrency"],
             ["Tamper evaluation", "Qualitative; threats listed (Sybil, 51 %, contract bugs, DoS)", f"13 cases applied; product check detects {F.N_TAMPER_PRODUCT}, stricter audit {F.N_TAMPER_STRICT}"],
             ["Reported limits", "Layer-1 throughput (about 119 tx/s for Ethereum, as the paper quotes), synthetic data, no pilot", "Single machine, no TLS, partial ballot secrecy, no concurrency test, synthetic data"]],
            widths=[1.3, 2.6, 2.6], align=["l", "l", "l"], size=9),
        P("The base paper's times were read by eye from its Figures 6 and 9, which are charts without tabulated values, so they are approximate (about 2000 ms for a registration, 3000 to 4000 ms for a vote). "
          f"AegisBallot's vote takes tens of milliseconds, one to two orders of magnitude less. This is no evidence that the design is better. A transaction on a test blockchain waits for block production and confirmation across nodes, whereas AegisBallot's block is committed by a function call that "
          "asks three in-process validators to sign. The speed is what a single trusted server buys; the price is that the ledger offers no protection against whoever controls that server, which the tamper study makes concrete."),
        FIG(F.fig("f08_base_paper_comparison.png"), "Per-transaction time on a logarithmic scale: base paper (approximate, read from its figures) and AegisBallot (measured). Order of magnitude only.", 5.3),
        P("Where AegisBallot goes beyond the base paper is in workflow and verification, not in distribution: it adds the Aadhaar-style identity check with a checksum and a hashed registry, a complete administrator, voter and auditor workflow with a receipt, an audit log, "
          "rate limiting and CSRF protection, and it measures what its own integrity check can and cannot detect. The base paper adds, and AegisBallot lacks, a real distributed chain, smart-contract enforcement and an analysis of public-chain attack classes."),
    ]


# --------------------------------------------------------------------------- 8.6
def _samples():
    ballot = "blt_241450f4567e2c6aee2822667acec620"
    tx = "ddb6ea28446897169940d823fa9612520ac85bbbf27cb97c41a8fe08bf665d5a"
    blk = "ee0d0a3c07e112adcd4cb87ec06f78177e6a829f8dc6ae98505bdb2ff7df6faf"
    prev = "4b1687a46a717830a1fd430c80512f50668de3641464844094c629f260561454"
    ver = F.HTTP.get("auditor_verify_result", {})
    return [
        H2("8.6 Sample Inputs and Outputs"),
        P("The samples below are real. The receipt is the one on screen 19: its values were read from the development database (read-only) and match the screenshot; the other samples come from the scratch runs of Chapter 7."),
        H3("8.6.1 A successful vote"),
        P("Step 1, Aadhaar verification (voter signed in, session cookie and CSRF header sent):"),
        CODE("POST /api/voter/elections/7/verify\n{ \"aadhaar\": \"<12 digits of the signed-in voter>\" }\n\n200 OK\n{ \"auth_token\": \"<256-bit URL-safe token, shown once>\",\n  \"expires_in\": 600,\n  \"candidates\": [ { \"id\": ..., \"name\": \"Aarohi Sen\", \"party\": \"People's Unity Front\", ... }, ... ] }", 8.5),
        P("Step 2, the cast and the receipt (screen 19; the election is the Screenshot Demo Election, number 7):"),
        CODE("POST /api/voter/elections/7/cast\n{ \"candidate_id\": <id of the chosen candidate>, \"auth_token\": \"<token from step 1>\" }\n\n200 OK\n{ \"election\": { \"id\": 7, \"title\": \"Screenshot Demo Election\", \"status\": \"OPEN\", ... },\n  \"receipt\": {\n    \"ballot_id\":   \"" + ballot + "\",\n    \"tx_hash\":     \"" + tx + "\",\n    \"block_index\": 212,\n    \"block_hash\":  \"" + blk + "\" } }", 8.0),
        P("The ledger record behind that receipt (auditor screens and `ledger_transactions`) holds the same ballot id, the transaction hash, the encrypted payload `CuhkuG5Z0hLtdWtW5Z0AppaDGQSroY9siOpHcZPR` (a 12-byte nonce followed by the AES-256-GCM ciphertext of the candidate id and its tag, base64-encoded), "
          f"a 16-byte random nonce, the Ed25519 signature of the system key and, in `ledger_blocks`, the previous hash `{prev[:16]}...`, a Merkle root, the block hash and the signatures of validators 1, 2 and 3. "
          "Neither the receipt nor the ledger names the candidate or the voter."),
        H3("8.6.2 Refusals"),
        TAB("Sample refused requests and what the application answers", ["Request", "Status", "Message or effect"],
            [["Aadhaar of 11 digits", "400", "Invalid Aadhaar format: must be 12 digits"],
             ["12 digits, last digit changed", "400", "Invalid Aadhaar checksum (Verhoeff)"],
             ["Valid checksum, not in registry", "400", "Aadhaar not found in voter registry"],
             ["Another voter's registered number", "403", "Aadhaar does not match logged-in voter"],
             ["Second cast with the used token", "400", "Authorization token already used (audit entry vote_rejected)"],
             ["Cast after the token's ten minutes", "400", "Authorization token expired"],
             ["Cast in a paused election", "400", "Election is not open for voting"],
             ["Voter asks for results of an open election", "404", "Results are published when the election is closed"],
             ["POST without X-CSRF-Token", "403", "CSRF token missing or invalid"],
             ["Eleventh login attempt within a minute", "429", "Too many attempts. Try again in a minute."]],
            widths=[2.6, 0.7, 3.2], align=["l", "c", "l"], size=9.5),
        H3("8.6.3 The auditor's check"),
        CODE("POST /api/auditor/verify            (scratch chain of " + str(ver.get("height")) + " blocks)\n\n200 OK\n{ \"valid\": " + str(ver.get("valid")).lower() + ", \"height\": " + str(ver.get("height")) + ",\n  \"last_hash\": \"" + str(ver.get("last_hash")) + "\" }\n\n(after tampering, the same call returns, for example)\n{ \"valid\": false, \"first_invalid\": <block index>, \"field\": \"merkle_root\" | \"block_hash\" | \"previous_hash\", \"expected\": \"...\", \"actual\": \"...\" }", 8.0),
        P("The development database also keeps the trace of the smoke test run on 19 October 2026 in its audit log: a verification refused because the Aadhaar belonged to another voter, a verification accepted, a token issued, a cast with an invalid token rejected, a valid cast accepted and a replay with the used token rejected - the same sequence as checks 12, 15, 13, 17 and 18 of Chapter 7."),
    ]


# --------------------------------------------------------------------------- 8.7
def _analysis():
    return [
        H2("8.7 Success and Failure Analysis"),
        H3("8.7.1 What worked"),
        B("**One vote per voter** was enforced by four independent layers (eligibility, a unique participation row, a single-use token, and the ledger's nonce check). Every attempt in the tests to vote twice failed, at the service level and over HTTP.",
          "**Identity binding** worked as designed against the synthetic registry: format, checksum, registration and ownership of the number are all checked, and a voter cannot verify with someone else's number.",
          f"**Ballots were encrypted and receipts did not reveal choices.** The ledger and the ballots table hold only ciphertext and a random ballot id.",
          f"**The workflow was complete.** An administrator created an election, a voter was verified, voted and obtained a receipt, the seeded election Community Welfare Board 2026 was closed and its results page counts eight decrypted ballots, and an auditor verified 213 blocks (screens 10 to 22).",
          f"**Basic hardening held:** {F.MATRIX_PASSED} of {F.MATRIX_TOTAL} HTTP checks matched expectation, including roles, CSRF, validation, replay and the login limiter.",
          "**The system is fast enough for its purpose** as a local demonstration: tens of milliseconds per vote and about a fifth of a second for a whole voter journey."),
        H3("8.7.2 What failed or fell short"),
        N(f"**The integrity check misses {F.N_TAMPER - F.N_TAMPER_PRODUCT} of {F.N_TAMPER} tampering cases.** The cases that matter most for an election are among them: the `ballots` table, from which the tally is computed, is not covered by the ledger check, and signatures and transaction hashes are never re-verified. "
          "An administrator with database access could change the result and the auditor's page would still show \"ledger healthy\".",
          "**The tamper-detection demonstration is simulated.** The clone test overwrites a hash in memory and reports detection; it is not an independent verification (Section 7.6).",
          "**Ballot secrecy is partial.** `voter_participation` stores the voter id with the ballot id, so anyone who can read the database can find a voter's ballot, and with the single AES key in `data/secrets.json` can decrypt it. "
          "The README describes a per-election key; the code (`app/config.py`) creates one key for all elections.",
          "**The administrator can read a running tally** of an open election (HTTP check 22). The voter is refused, but an election official can see partial results before the poll closes.",
          "**The polling window is not enforced.** Start and end times are shown but never compared with the clock; a vote is accepted whenever the status is OPEN.",
          "**The login limiter keys on the client address**, so a polling station behind one address would be limited to ten sign-ins a minute, and it is lost on every restart because it is held in memory; sessions are in memory too.",
          "**No TLS and no `Secure` cookie flag**, although the abstract lists TLS. Password hashing is Argon2id, not the bcrypt named in the abstract (a stronger choice, but a difference).",
          "**The benchmark's \"asynchronous\" batches are sequential**, and concurrent voting was never tested; two simultaneous votes compete for the same next block index.",
          "**Weak assertions in three unit tests** (Section 7.2) mean the green result of the pytest run overstates what is verified."),
        H3("8.7.3 Why the failures matter, and what they do not mean"),
        P("The failures cluster in one place: the gap between the ledger and the data the application actually trusts. A hash chain protects the records inside it; it does not protect the table next to it. Nothing here shows that the cryptographic primitives are wrong - SHA-256, AES-GCM and Ed25519 were used through standard libraries and behaved correctly in every test - "
          "or that the one-vote rule can be bypassed through the interface. What the study shows is that \"immutable\" is a property of a verified chain, and the delivered verification is incomplete."),
    ]


# --------------------------------------------------------------------------- 8.8
def _limits():
    return [
        H2("8.8 Limitations of the Results"),
        B("All identities, Aadhaar numbers and elections are synthetic; the results say nothing about real electoral rolls, UIDAI services or real voters' behaviour.",
          "The ledger is a single-machine simulation of a permissioned chain; no result applies to a distributed deployment, to network faults or to Byzantine validators.",
          "Timings come from one shared PC; they show orders of magnitude and relative cost, not guaranteed performance.",
          "No concurrency, load or penetration testing was done, and no user study.",
          "The stricter audit that detected all 13 cases is a research script, not part of the product.",
          "Numbers taken from the base paper's figures are approximate readings."),
    ]


# --------------------------------------------------------------------------- 8.9
def _objectives():
    return [
        H2("8.9 Objectives Versus Outcomes"),
        P("The six objectives are those of the batch's objectives document. Each is judged against the evidence of Chapters 7 and 8, and the verdicts are deliberately conservative."),
        TAB("Objectives and outcomes", ["No.", "Objective", "Outcome", "Evidence and caveat"],
            [["1", "Voter registration and authentication with Aadhaar-based identity verification", "Partly achieved",
              "Password sign-in and the Aadhaar check (format, Verhoeff, registry, ownership) work and are tested. Registration is not a user function (voters are seeded), and the registry is synthetic; UIDAI is not contacted."],
             ["2", "One-voter-one-vote through identity binding and duplicate checks", "Achieved",
              "Four layers; unit tests 5, 6 and 11; HTTP checks 12, 18 and 19; database uniqueness constraints on three tables."],
             ["3", "Record each ballot immutably using blockchain and cryptographic hashing", "Partly achieved",
              f"Each ballot is a signed transaction in a hash-chained, validator-signed block. Edits to hashes and links are detected ({F.N_TAMPER_PRODUCT} of {F.N_TAMPER} cases), but the tally source is not covered, signatures are not verified by the audit, and the chain is not distributed."],
             ["4", "Administration portal for elections, candidates and polling windows", "Mostly achieved",
              "Elections, candidates and status are managed through the interface (screens 11-13). Windows are stored and displayed but not enforced."],
             ["5", "Results automatically when the poll closes, with a chronological audit trail", "Achieved, with caveats",
              "Closing is an administrator action; once CLOSED the tally is computed on request and published to signed-in roles (screens 14, 20). The audit log records actions in time order. The administrator can also see a live tally."],
             ["6", "RBAC, input validation and TLS; evaluate integrity and performance", "Partly achieved",
              f"RBAC, CSRF, validation, rate limiting achieved ({F.MATRIX_PASSED} of {F.MATRIX_TOTAL} checks). TLS **not achieved**. Integrity and performance evaluated with the limits stated here."]],
            widths=[0.4, 2.0, 1.0, 3.1], align=["c", "l", "l", "l"], size=9),
        P("In summary, the platform delivers the voting workflow and the one-vote guarantee convincingly, delivers the ledger as a tamper-evident record for the part of the data it covers, and is honest about the rest: the pieces that remain are listed again as future work in Chapter 10."),
    ]


def blocks():
    return ([H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS")] + _setup() + _screens() + _perf() + _security_results() + _compare() + _samples() + _analysis() + _limits() + _objectives())
