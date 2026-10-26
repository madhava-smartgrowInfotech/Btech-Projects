"""Chapter 6: Methodology and Software Implementation.

methodology_blocks() and application_blocks() carry no H1 so that 9.METHODOLOGY... and 12.DESIGN &IMPLEMENTATION... can reuse them;
blocks() is the full chapter. All constants quoted were re-read from app/ (config.py, crypto.py, ledger.py, voting_service.py, api_v1.py).
"""

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def _mt(key, field="mean_ms", fmt="{:.2f}"):
    return fmt.format(F.MICRO[key][field])


# =====================================================================================================================
def methodology_blocks():
    return [
        H2("6.1 Overall Methodology"),
        P("AegisBallot is a systems and security project, not a learning project: no model is trained and no accuracy or F1 value exists. The methodology is therefore an engineering one. "
          "The team took the problem statement and objectives of the batch, derived security requirements from them, chose a small set of well-understood cryptographic primitives, built a backend that enforces the requirements "
          "in several independent layers, put role-based consoles on top, and then evaluated the result with automated tests, a measured tamper study and performance benchmarks. The steps were:"),
        N("**Requirements to controls.** Each objective was turned into a testable control: identity binding became the Aadhaar check and the single-use token; one voter one vote became four overlapping rules; immutability became the hash-chained ledger; the audit trail became the `audit_logs` table and the auditor console.",
          "**Backend first.** The models, services and ledger were written and covered by pytest before any user interface; the original interface was server-rendered Jinja pages.",
          "**Additive JSON layer and React interface.** `app/api_v1.py` was added next to the existing routes without changing them, and the React single-page application was built on it.",
          "**Evaluation.** Seventeen unit and integration tests, an HTTP security matrix, a tamper study that applies thirteen kinds of modification to a real chain, and benchmarks of one thousand synthetic voters were run on one PC (Chapters 7 and 8).",
          "**Honest reporting.** Every limitation found during the evaluation (Sections 6.6 and 6.10 and Chapter 9) is stated in the documents rather than hidden."),
        H2("6.2 Data and Test Data"),
        P("There is no external dataset. A voting system is evaluated on its behaviour, and real voter data would be both unavailable and inappropriate. All identities are synthetic and generated locally, as in the base paper, "
          f"which also used synthetic population data and 1000 synthetic voters [{R['base']}]. The sources of data are:"),
        TAB("Data used by the system and by the evaluation", ["Data", "How it is produced", "Size"],
            [["Demo accounts", "`app/seed.py`: one administrator, one auditor, voters `voter1` to `voter20` with Argon2id password hashes", "22 users"],
             ["Synthetic Aadhaar numbers", "`generate_valid_aadhaar`: first digit 2-9, ten random digits, Verhoeff check digit appended; stored as salted SHA-256 plus a masked form; plain numbers written to `data/synthetic_identities.json` for the demo", "20 in the seed; one per benchmark voter"],
             ["Elections and candidates", "Two seeded elections (four and three candidates); eight seeded votes in the closed one", "2 elections, 7 candidates"],
             ["Benchmark voters", "`run_benchmark`: Argon2-hashed passwords, Verhoeff-valid numbers, eligibility rows", f"{F.N_VOTERS_BENCH} per series"],
             ["Measurement databases", "`scripts/run_experiments.py` builds scratch SQLite files and never touches `data/aegisballot.db`", "up to 361 blocks"]],
            widths=[1.5, 3.7, 1.2], size=9.5, align=["l", "l", "l"]),
        P("The names in the seed file are common Indian given names combined arbitrarily and do not refer to real people. The Aadhaar numbers are random numbers that satisfy the checksum; any resemblance to a real number is coincidental, "
          "and the interface states on every verification screen that the environment is a demonstration."),
        H2("6.3 Input Validation and Normalisation"),
        P("The only transformation applied to inputs is normalisation and validation, the counterpart of preprocessing in a data-driven project. The Aadhaar number is cleaned by removing spaces and hyphens, so that "
          "`1234 5678 9012` and `1234-5678-9012` are treated alike; the result must consist of exactly twelve digits and satisfy the Verhoeff checksum. The Pydantic models of `api_v1.py` bound every text field "
          "(username 1 to 64 characters, password 1 to 256, Aadhaar 1 to 32, election title 1 to 200, candidate name and party 1 to 128); dates are parsed with `datetime.fromisoformat` and an election whose end is not "
          "after its start is rejected; a status must be one of DRAFT, OPEN, PAUSED, CLOSED. Database access goes through SQLAlchemy with bound parameters, which is why the SQL-injection-style username in the security matrix "
          "returns an ordinary 401. Before hashing, structures are serialised canonically: keys sorted and separators `,` and `:` without spaces, so the same transaction always has the same bytes."),
        H2("6.4 Algorithm Choice and Justification"),
        P("Each primitive was chosen to meet one requirement with the least complexity, and each choice has an alternative that was considered and rejected. The table summarises the reasoning; the sections after it give the "
          "formulation."),
        TAB("Algorithms and why they were chosen", ["Requirement", "Chosen", "Alternative", "Reason"],
            [["Catch mistyped identity numbers", f"Verhoeff checksum [{R['verhoeff']}]", "Length check only; Luhn", "Detects all single-digit errors and all adjacent transpositions; the same scheme protects real Aadhaar numbers"],
             ["Find a voter without storing the number", "Salted and peppered SHA-256 lookup", "Store the number; slow hash", "A fixed-length hash allows an indexed unique lookup; the number is never stored. A salted fast hash is weak against brute force of a 12-digit space, which is why only synthetic numbers are used (see 6.6)"],
             ["Store passwords", f"Argon2id [{R['argon2']}], [{R['argon2rfc']}]", "bcrypt (batch abstract); plain SHA-256", f"Memory-hard and the current recommendation; {_mt('argon2id_verify', fmt='{:.0f}')} ms per check on the test PC"],
             ["Separate identity from ballot", "Random 256-bit single-use token, stored hashed", "Session id as ballot key", "A token with expiry and single use makes the cast call independent of the login"],
             ["Hide the choice", f"AES-256-GCM [{R['gcm']}]", "Plain id; CBC", "Authenticated encryption detects modification of the ciphertext; the 12-byte random nonce is stored with it"],
             ["Authenticate transactions and blocks", f"Ed25519 [{R['eddsa']}]", "RSA; HMAC", f"Compact public-key signatures; sign {_mt('ed25519_sign')} ms, verify {_mt('ed25519_verify')} ms"],
             ["Tamper evidence", f"SHA-256 hash chain [{R['sha2']}] with a flat Merkle-style root [{R['merkle']}]", "Merkle tree with proofs", "Simple to implement and to recompute; no inclusion proofs"],
             ["Agreement on a block", "Quorum of 2 of 3 validators", f"PBFT [{R['pbft']}]; Ethereum", "Needs no network; simulates the rule 'more than half of the validators approve'; trust is not actually distributed"]],
            widths=[1.35, 1.45, 1.2, 2.4], size=9, align=["l", "l", "l", "l"]),
        H3("Why a local permissioned ledger"),
        P(f"The base paper builds on Ethereum with smart contracts [{R['base']}] and reports transaction times of about two seconds for registration and three to four seconds for voting on a Geth test chain "
          f"(read from its Figures 6 and 9). It quotes Ethereum's theoretical throughput as 119.1 tx/s against 65,000 tx/s for Solana. A public chain gives strong decentralisation but also fees, wallets, latency and "
          f"no direct link to a national identity; Hyperledger Fabric [{R['fabric']}] gives a permissioned design but needs several containers and an ordering service. For an academic prototype that must run on one laptop and "
          "be explained completely, the project chose to implement the properties it can test - append-only blocks, hash linking, signed approvals, a quorum rule and a recomputing auditor - in about 280 lines of Python. "
          "The consequence, stated throughout the documents, is that all three validators run in one process and keep their keys in one file, so a single operator controls the whole quorum."),
        H3("No learned model"),
        P("No machine-learning model, training procedure or evaluation split exists in this project. Model architecture, hyper-parameters, loss functions and training curves are therefore not applicable; "
          "the corresponding sections of the report template are replaced by the cryptographic and ledger design in this chapter."),
        H2("6.5 Mathematical Formulation"),
        P("This section states exactly what the code computes. Strings are UTF-8 encoded before hashing, and `‖` denotes concatenation."),
        H3("Verhoeff checksum"),
        P("Let `d` be the multiplication table of the dihedral group D5 (a 10 by 10 table), `p` the permutation table with eight rows, and `inv` the inverse table. For a number with digits n(1) (rightmost) to n(L), "
          "the code iterates from the right and keeps a running value c:"),
        EQ("c(0) = 0;   c(i) = d( c(i−1), p( i mod 8, n(i) ) ),   i = 1 … L"),
        P("The number is valid when c(L) = 0. To generate a check digit for an eleven-digit prefix the code uses the shifted index and takes the inverse of the final value:"),
        EQ("c(i) = d( c(i−1), p( (i+1) mod 8, n(i) ) );   check digit = inv( c(11) )"),
        H3("Registry key and masked form"),
        EQ("h = SHA-256( salt ‖ pepper ‖ a )   with salt = “aegisballot-aadhaar-salt-v1”, pepper = SECRET_KEY, a = the 12 digits"),
        P("The registry lookup compares h with `voter_profiles.aadhaar_hash`. The stored display form is `XXXX-XXXX-` followed by the last four digits of a."),
        H3("Authorization token"),
        P("A token t of 256 random bits is produced by `secrets.token_urlsafe(32)`. Only the digest is stored. A presented token t′ is accepted for election e and voter v when all three conditions hold:"),
        EQ("SHA-256(t′) = token_hash(e, v)   ∧   is_used = false   ∧   now ≤ created_at + 10 min"),
        H3("Ballot encryption"),
        P("The plaintext m is the decimal candidate id. With the 256-bit key K, a fresh 12-byte nonce r and no associated data, the stored ciphertext is the base64 encoding of"),
        EQ("c = r ‖ AES-256-GCM_K( r, m )"),
        P("where the GCM output includes the 16-byte authentication tag [" + str(R['gcm']) + "]. Decryption splits the first 12 bytes and fails with an exception if the tag does not verify; the tally skips undecryptable ballots."),
        H3("Transaction, Merkle value and block hash"),
        P("Let `canon(x)` be the JSON serialisation of x with sorted keys and compact separators. A transaction contains the election id, ballot id, ciphertext, a 128-bit random nonce and an ISO timestamp:"),
        EQ("txh = SHA-256( canon( { election_id, ballot_id, encrypted_payload, nonce, timestamp } ) );   sig = Ed25519-Sign( sk_system, txh )"),
        P("The signed message is the hexadecimal text of txh. For a block with transaction hashes sorted in ascending order, h(1) … h(n), the code computes a flat value, not a binary tree:"),
        EQ("M = SHA-256( h(1) ‖ h(2) ‖ … ‖ h(n) )     (M = SHA-256 of the empty string when n = 0)"),
        EQ("H(b) = SHA-256( canon( { block_index, timestamp, previous_hash, merkle_root = M, tx_hashes = [h(1) … h(n)] } ) )"),
        P("The genesis block has index 0, previous hash of sixty-four zeros, no transactions and a hash computed with the same formula."),
        H3("Quorum"),
        P("Each validator v in {1, 2, 3} evaluates the block and returns a Boolean a(v): the schema is complete, the nonce and the transaction hash have not been used before and, when the transaction carries a public key and signature, the "
          "signature verifies. The approving validators sign the block hash:"),
        EQ("s(v) = Ed25519-Sign( sk(v), H(b) ) if a(v);      the block is committed if  Σ a(v) ≥ 2"),
        H3("Chain validity"),
        P("`validate_chain` returns valid when, for every block b(i) with transaction hashes recomputed from the stored transactions,"),
        EQ("M(i) = SHA-256( stored tx hashes )  ∧  H(b(i)) = stored block hash  ∧  previous(b(i)) = H(b(i−1))   for i ≥ 1"),
        H3("Tally and benchmark statistics"),
        P("For candidate k of an election the tally is the number of ballots whose decrypted plaintext equals the candidate id: count(k) = |{ b : Dec_K(c_b) = k }|. For N operations with total wall time T the benchmark reports "
          "throughput N / T, the mean and median of the per-operation times, and the 95th percentile as the element at index ⌊0.95 N⌋ of the sorted times."),
        H2("6.6 Security Design"),
        P(f"The security design follows the controls of the OWASP application security verification standard [{R['asvs']}] that apply to a small web application. The table maps each threat considered to the control that "
          "addresses it and to the test that exercises it."),
        TAB("Threats and controls", ["Threat", "Control in the code", "Evidence"],
            [["Guessing or stealing a password", "Argon2id hashes; login limited to 10 requests per 60 s per client address; failed logins audited", "unit test for hashing; matrix check 25 (429)"],
             ["Using another voter's Aadhaar number", "The number must belong to the signed-in account (HTTP 403)", "matrix check 12"],
             ["Mistyped or invented number", "Twelve-digit, Verhoeff and registry checks (HTTP 400)", "matrix checks 9-11; unit tests"],
             ["Voting twice", "Four layers: eligibility, unique participation, single-use token, unique nonce and transaction hash", "unit tests; matrix checks 18-19"],
             ["Replaying a token", "Token marked used in the same commit as the ballot; expiry after 10 minutes", "matrix check 18; expired-token test"],
             ["Acting beyond one's role", "`role_required` dependencies (HTTP 403)", "matrix checks 5-7; unit tests"],
             ["Cross-site request forgery", "Mutating `/api` calls need the session's `X-CSRF-Token` header; cookie is SameSite=Lax", "matrix check 8"],
             ["Reading the choice from the ledger", "AES-256-GCM ciphertext only; the receipt and auditor pages show no choice", "identity-separation test"],
             ["Changing the ledger", "Hash chain recomputed by the auditor", f"tamper study: {F.N_TAMPER_PRODUCT} of {F.N_TAMPER} cases detected (Chapter 8)"],
             ["Abuse of the verification route", "15 verification attempts per 60 s per client address (HTTP 429)", "code review (`voter_verify`)"]],
            widths=[1.8, 3.0, 1.6], size=9, align=["l", "l", "l"]),
        P("**What the design does not do.** The ledger check does not verify validator signatures or re-derive transaction hashes (Chapter 8 shows which tampering this misses); the three validator keys and the system "
          "key sit in files in `data/` next to the database; the AES key is one key for all elections (the README says per-election; `app/config.py` creates one key and stores it in `data/secrets.json`); "
          "`voter_participation` links a voter to a ballot id; sessions live in process memory and never expire on the server; the rate limiter is per client address, so a polling station behind one address is limited to "
          "ten logins a minute; the cookie has no `Secure` attribute and no TLS is configured, although the batch objectives name TLS; the legacy HTML form routes do not require a CSRF token; the admin can read the tally of "
          "an election that is still open; and the polling window dates are not enforced (Section 6.10). None of these is hidden: each is listed in the limitations chapter and in the future scope."),
    ]


# =====================================================================================================================
def _route_rows():
    return [
        ["POST", "`/api/auth/login`", "public", "Verify credentials, create session and CSRF token, set cookie; 401 bad credentials, 429 throttled"],
        ["POST", "`/api/auth/logout`", "signed in", "Destroy the session, clear the cookie, write audit entry"],
        ["GET", "`/api/auth/me`", "public", "Current user and CSRF token, or `user: null` (200, so the console stays free of expected 401s)"],
        ["GET", "`/api/public/overview`", "public", "Elections, ledger validity and height, ballots cast, validator count (landing page)"],
        ["GET", "`/api/admin/overview`", "ADMIN", "Voters, votes, turnout, chain status, validators, latest benchmark, elections, five blocks, ten log rows"],
        ["GET", "`/api/admin/elections`", "ADMIN", "All elections with eligible, votes, turnout and candidate counts"],
        ["POST", "`/api/admin/elections`", "ADMIN", "Create an election (201); creates eligibility rows for all voters; 400 if end ≤ start"],
        ["GET", "`/api/admin/elections/{eid}`", "ADMIN", "Election, candidates, counts and, if CLOSED, the tally"],
        ["POST", "`/api/admin/elections/{eid}/status`", "ADMIN", "Set DRAFT, OPEN, PAUSED or CLOSED (400 otherwise)"],
        ["POST", "`/api/admin/elections/{eid}/candidates`", "ADMIN", "Add a candidate (201)"],
        ["POST", "`/api/admin/candidates/{cid}/toggle`", "ADMIN", "Activate or deactivate a candidate"],
        ["GET", "`/api/admin/benchmarks`", "ADMIN", "Last five benchmark runs with parsed details"],
        ["GET", "`/api/elections/{eid}/results`", "signed in", "Tally; ADMIN at any time, other roles only when CLOSED (else 404)"],
        ["GET", "`/api/voter/elections`", "VOTER", "Open, paused and closed elections with the voter's own participation"],
        ["GET", "`/api/voter/elections/{eid}`", "VOTER", "Election, masked Aadhaar, voted flag, ballot id"],
        ["POST", "`/api/voter/elections/{eid}/verify`", "VOTER", "Aadhaar checks; returns the one-time token (600 s) and candidates; 400, 403 or 429 on failure"],
        ["POST", "`/api/voter/elections/{eid}/cast`", "VOTER", "Candidate id and token; returns the receipt; 400 on any rejected check, 500 on an unexpected error"],
        ["GET", "`/api/auditor/overview`", "AUDITOR", "Chain status, validators, 20 blocks, 20 transactions, 20 log rows"],
        ["POST", "`/api/auditor/verify`", "AUDITOR", "Run `validate_chain`; audit entry `integrity_check`"],
        ["POST", "`/api/auditor/tamper-test`", "AUDITOR", "Run `tamper_test_clone`; audit entry `tamper_test`"],
        ["GET", "`/api/auditor/blocks/{index}`", "AUDITOR", "One block with parsed signatures and its transactions"],
    ]


def application_blocks():
    return [
        H2("6.7 Application Architecture"),
        P("The backend is a FastAPI application served by uvicorn on 127.0.0.1. On import, `app/main.py` creates the application, mounts the JSON router, calls `init_db` to create missing tables, and then calls `init_validators` and "
          "`create_genesis_block` so that the chain always has a block 0 and three validator keys. Requests are handled by synchronous route functions with a SQLAlchemy session per request (`get_db`). The session store, the "
          "rate limiter and the in-memory validator key table are module-level dictionaries, which keeps the code short and is the reason state is lost on restart (the database survives)."),
        P("The frontend is a Vite project in `frontend/`. `src/lib/api.ts` creates the Axios client, stores the CSRF token returned by login and sends it on every mutating call; `src/lib/queries.ts` wraps each endpoint in a TanStack Query "
          "hook; `src/lib/auth.tsx` holds the user in a context and maps each role to its home route; `src/pages` holds one file per page; `src/components/ui` is a small component kit (cards, tables, badges, dialogs, toasts) "
          "built on Radix primitives and Tailwind CSS. Pages are loaded lazily, and the production build splits the chart, motion and Radix libraries into separate chunks. The Vite development and preview servers proxy `/api` to the backend, "
          "so the browser sees one origin and the session cookie needs no cross-origin settings."),
        P("Configuration comes from `.env` at the project root (`BACKEND_PORT=8401` and `FRONTEND_PORT=5401`, read by `run.bat` and the Vite configuration) and from environment variables read in `app/config.py` (`DATABASE_URL`, `SECRET_KEY`, `SESSION_SECRET`, "
          "`ELECTION_ENCRYPTION_KEY`). The shipped defaults for `SECRET_KEY` and `SESSION_SECRET` are development strings in the source and must be replaced for any real use; the Aadhaar pepper is `SECRET_KEY`."),
        H2("6.8 API Design"),
        P("The JSON API has twenty-one routes in four groups, all under `/api`. Authentication is the `aegis_session` cookie; every route other than the three public ones resolves the session to a user, and every POST requires the "
          "`X-CSRF-Token` header to equal the CSRF token of the session. Errors are JSON of the form `{\"detail\": \"...\"}` with the status codes listed in the next section. The same functions back the legacy HTML pages, so the two interfaces cannot disagree."),
        TAB("Routes of `app/api_v1.py`", ["Method", "Path", "Access", "Purpose"], _route_rows(), widths=[0.55, 2.35, 0.8, 2.7], size=8.5, align=["c", "l", "c", "l"]),
        H2("6.9 Security Handling and Error Handling"),
        P("Authentication state is held in an in-memory dictionary keyed by a 256-bit random token; the cookie is set with `HttpOnly`, `SameSite=lax` and `Path=/`. It has no `Secure` attribute because the application is served over "
          "plain HTTP on localhost, and the server never expires a session by time (only logout or a restart ends it). Passwords are never logged; a failed login writes the attempted username to the audit log, which means a "
          "mistyped password could be recorded if it is entered in the username field - a small privacy gap noted for the future."),
        TAB("HTTP status codes used by the API", ["Status", "Meaning in AegisBallot", "Examples"],
            [["200 / 201", "Success; 201 for created elections and candidates", "login, cast, create election"],
             ["400", "A business rule failed; nothing was stored", "bad Aadhaar format or checksum, not in registry, already voted, invalid token, unknown candidate, election not open, end before start, invalid status"],
             ["401", "No valid session", "any protected route without cookie; wrong username or password"],
             ["403", "Role not allowed, CSRF token missing or wrong, or the Aadhaar belongs to another voter", "voter calling an admin route"],
             ["404", "Resource missing, or results not yet published to a non-admin", "unknown election; results of an OPEN election as a voter"],
             ["422", "Request body failed Pydantic validation", "empty username"],
             ["429", "Rate limit reached", "more than 10 logins or 15 verifications in 60 s from one address"],
             ["500", "Unexpected failure while recording a vote", "message: \"Vote could not be recorded. Nothing was submitted; try again.\""]],
            widths=[0.9, 2.7, 2.8], size=9, align=["c", "l", "l"]),
        P("Failures that follow from business rules are raised as `ValueError` in the services and converted to HTTP 400 in the route; the route also writes the reason to the audit log (`vote_rejected`, `aadhaar_verify_failed`). "
          "If the ledger rejects a block, nothing is written, and the token remains valid until it expires. "
          "The React client converts every error into a toast with the server's message, and a failed request on the landing page shows a clear \"Cannot reach the AegisBallot server\" state."),
        H2("6.10 Implementation Notes and Behaviour Found on Review"),
        P("Writing the documents involved re-reading every route against the objectives of the batch. The review confirmed most behaviour and also produced a short list of facts that a reader of the report should know; "
          "they are repeated in the limitations chapter."),
        B("**Voting windows are not enforced.** An election has `start_time` and `end_time`, and the administrator sets them, but `cast_vote` tests only that the status is OPEN. The status, changed by the administrator, is what "
          "opens and closes voting; the dates are information shown in the interface. The seeded closed election shows the effect: its end time was in the past while its status was still OPEN until the seed script closed it.",
          "**There is no voter-registration route.** Voters, their profiles and their synthetic Aadhaar numbers are created by `app/seed.py` or by the benchmark; the registry is therefore prepared offline, and objective 1 of the batch "
          "(registration and authentication) is met by authentication and verification against that registry, not by a self-service sign-up page.",
          "**Eligibility is created with the election.** `POST /api/admin/elections` inserts an eligibility row for every voter that exists at that moment; a voter added later is not eligible for earlier elections unless a row is added.",
          "**One transaction per block.** `cast_vote` always proposes a block of one transaction. The chain therefore grows by one block per vote, the receipt's block number identifies the vote, and `validate_chain` is linear in the number of votes.",
          "**Validators approve in a fixed order and always agree.** Because the three validators run the same checks on the same database inside one process, a block rejected by one is rejected by all; the quorum matters only if a validator key is missing, in which case the code records the string `missing-priv` as that validator's signature and still counts it as an approval.",
          "**The transaction's public key travels inside the transaction.** The validators verify the Ed25519 signature against the key supplied with the transaction; the system key is not pinned and the key is not stored in `ledger_transactions`. The check proves the transaction was not altered after signing, not that the signer was authorised.",
          "**Times are naive UTC.** Timestamps are produced by `datetime.utcnow()` and serialised without a zone, so the interface shows UTC.",
          "**Concurrency was not tested.** Each block takes the next index from the last block; two simultaneous votes could compute the same index, and the unique constraint on `block_index` would make one of them fail with a 500. The benchmark's \"batched\" series are sequential and do not exercise this."),
        H2("6.11 Installation and Execution"),
        P("The project needs Python 3.11 or 3.12 and Node.js 20 or newer; no database server, wallet or external credentials are required. On Windows, double-clicking `run.bat` creates `.venv`, installs "
          "`requirements.txt`, seeds the database (`python -m app.seed`), installs the front-end packages on the first run, checks that the ports are free, starts uvicorn on 8401 and Vite on 5401, and opens the browser. "
          "The manual method is five commands. Appendix B gives the full instructions, the demonstration accounts and troubleshooting."),
        CODE("python -m venv .venv\n.venv\\Scripts\\activate\npip install -r requirements.txt\npython -m app.seed\nuvicorn app.main:app --host 127.0.0.1 --port 8401\n"
             ":: second window\ncd frontend\nnpm install\nnpm run dev", 9),
        P("To reproduce the measurements: `python -m pytest tests` (17 tests; the fixture drops all tables, so set `DATABASE_URL` to a scratch file first), `python -m app.benchmarks.run_benchmark --voters 1000`, and "
          "`python scripts/run_experiments.py <scratch-directory>` for the growth, tamper and HTTP studies. A smoke test, `python scripts/smoke_test.py`, exercises the API and the main voting flow against running servers."),
    ]


def blocks():
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION"),
            P("This chapter describes how the system was built and evaluated: the methodology, the data, the choice and the mathematics of each algorithm, the security design, the application architecture, the API and the way to install "
              "and run it. Because there is no machine-learning component, the chapter replaces model architecture and training with the cryptographic and ledger design.")] + methodology_blocks() + application_blocks()
