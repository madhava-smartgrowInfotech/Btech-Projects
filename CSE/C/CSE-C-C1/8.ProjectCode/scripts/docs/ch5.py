"""Chapter 5: System Design. Also used (without its H1) by 12.DESIGN &IMPLEMENTATION.docx.

Every statement was checked against app/ (api_v1.py, main.py, services/, ledger/, identity/, security/, models/) and frontend/src.
"""

from . import facts as F
from .blocks import B, EQ, FIG, H1, H2, H3, N, P, PAIR, TAB
from .diagram_index import DIAGRAMS
from .refs import CITE as R

_D = {k: (t, f, c, p) for k, t, f, c, p in DIAGRAMS}


def dfig(key, width=5.6, max_h=6.6):
    """Real diagram from diagram_index, width limited so that its height stays below max_h inches."""
    _, f, cap, _ = _D[key]
    path = F.diag(f)
    return FIG(path, cap, F.shot_w(path, width, max_h))


def pshot(name, caption):
    return (F.shot(name), caption)


def blocks():
    return (intro() + architecture() + workflow() + dataflow() + uml() + database() + modules() + algorithms() + ui_design() + decisions())


# =====================================================================================================================
def intro():
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter turns the requirements of Chapter 4 into a design. It gives the architecture, the workflow of an election and of one vote, the data flow diagrams at three levels, the UML diagrams, "
          "the database design with the way identity and ballot are kept apart, the module design, the algorithms in flow-chart form and the user-interface design. Every diagram was drawn from the code of "
          f"`8.ProjectCode` (the JSON routes in `app/api_v1.py`, the services, the ledger and the thirteen SQLAlchemy models), and all twelve diagrams are listed again with longer explanations in the "
          "block-diagram document."),
    ]


# =====================================================================================================================
def architecture():
    return [
        H2("5.1 Design Goals and Architecture"),
        P("Six goals shaped the design. **Integrity**: once a ballot has been accepted it must not be changeable without the change being detectable. **One voter, one vote**: the rule must hold even if a "
          "single layer of the application is bypassed. **Separation of identity and ballot**: the record that proves a person voted should not be the record that shows what was chosen. "
          "**Auditability**: an independent party must be able to recompute the state of the ledger. **Local operation and simplicity**: one launcher, one configuration file, one database file, no external "
          "service, so that the system can be demonstrated on any laptop. **Role separation**: the administrator who runs the election, the voter who takes part and the auditor who checks it are different accounts with different rights."),
        P(f"The architecture has four tiers, shown in the figure below. The presentation tier is a React 18 single-page application served by Vite on port {F.WEB_PORT}; it holds the public pages and the three "
          f"role consoles and talks to the backend through an Axios client that forwards `/api` to port {F.API_PORT}. The application tier is FastAPI: `app/api_v1.py` provides the JSON routes used by the React app, "
          "and `app/main.py` keeps the original server-rendered Jinja pages, which still work but are no longer the main interface. The service tier contains the identity provider, the voting service, the "
          "cryptographic helpers, the audit logger and the ledger module with its three validators. The data tier is a single SQLite database, `data/aegisballot.db`, with thirteen tables, plus three small key files "
          "in `data/` (`secrets.json`, `validators.json`, `system_key.json`)."),
        dfig("arch"),
        P(f"The base paper [{R['base']}] uses a four-tier model as well: MySQL and an Ethereum ledger for storage, Ethereum nodes running smart contracts, a C# web-application tier and client devices. "
          "AegisBallot keeps the same separation of concerns but replaces the public-chain tier with a local permissioned ledger, which is the main design departure. The table maps the two designs."),
        TAB("Tiers of the base paper's model and of AegisBallot", ["Tier", "Base paper (Oman model)", "AegisBallot"],
            [["Storage", "MySQL for credentials and voter data; Ethereum ledger for votes", "One SQLite database; the ledger is two tables in the same database"],
             ["Ledger / consensus", "Ethereum nodes execute smart contracts on a Geth test chain", "Three in-process validators with Ed25519 keys; a block needs 2 of 3 approvals"],
             ["Business logic", "C# web application", "FastAPI services (`voting_service`, `election_service`, `audit`, identity provider)"],
             ["Client", ".NET Core 7 simulators; crypto wallets in the proposal", "React 18 browser application with cookie session and CSRF header"],
             ["Identity", "Biometric authentication (simulated)", "Aadhaar number checked for format, Verhoeff checksum and registry membership (synthetic registry)"]],
            widths=[1.1, 2.6, 2.7], size=10, align=["l", "l", "l"]),
    ]


# =====================================================================================================================
def workflow():
    return [
        H2("5.2 High-Level Workflow"),
        P("The life cycle of an election has two parts. In the administration part the administrator creates the election with its title, description and polling window, adds candidates, and sets the status to "
          "OPEN. Creating an election also creates a `voter_eligibility` row for every registered voter. In the voting part each voter passes the identity check, receives a token, casts one ballot and keeps a receipt. "
          "When the administrator sets the status to CLOSED the tally is published and the auditor can check the chain."),
        dfig("flow", 5.8, 4.2),
        N("**Sign in.** The voter sends a username and password. The password is verified against an Argon2id hash; a server-side session and a CSRF token are created; an audit entry is written.",
          "**Verify identity.** The voter types the 12-digit Aadhaar number. The provider removes spaces and hyphens, requires twelve digits, checks the Verhoeff checksum and looks up the salted hash. "
          "The number must belong to the signed-in account, the voter must be eligible and must not have voted.",
          "**Receive a token.** A 256-bit random token is generated; only its SHA-256 hash is stored, with an expiry of ten minutes; the plain token is returned once to the browser.",
          "**Cast.** The browser sends the candidate id and the token. The service checks the election is OPEN, the candidate is active in that election, the token is valid and unused, and that no participation row exists.",
          "**Commit.** The choice is encrypted with AES-256-GCM, the transaction is hashed and signed, and three validators check and sign the block; two approvals commit it. The ballot row, the used token and the participation row are saved in one commit.",
          "**Receive a receipt.** The voter gets the ballot id, transaction hash, block number and block hash. Any failure returns HTTP 400 or 403, writes an audit entry and stores nothing.",
          "**Close and audit.** After closing, the tally is computed from the `ballots` table and published; the auditor recomputes the chain with `validate_chain`, browses blocks and reads the audit log."),
    ]


# =====================================================================================================================
def dataflow():
    return [
        H2("5.3 Data Flow Diagrams"),
        H3("5.3.1 Level 0: context diagram"),
        P("At level 0 AegisBallot is a single process with three human actors and two stores. The voter supplies credentials, an Aadhaar number and a choice and receives a receipt and the published results. "
          "The administrator supplies election, candidate and status changes and receives turnout and tallies. The auditor supplies integrity-check requests and receives chain status, blocks and the audit log. "
          "The only data sources are the voter registry (a table of hashed synthetic Aadhaar numbers) and the store of ledger, ballots and log entries."),
        dfig("dfd0", 5.6, 4.0),
        H3("5.3.2 Level 1"),
        P("Level 1 divides the platform into eight processes. The table lists what each process does and which stores it reads and writes."),
        TAB("Processes and data stores of the level-1 diagram", ["Process", "Function (code)", "Reads", "Writes"],
            [["1.0 Authenticate", "`POST /api/auth/login`: Argon2id verify, session, CSRF token, rate limit", "D1 users", "session store (memory), D5 audit"],
             ["2.0 Verify identity", "`DemoAadhaarProvider.verify`: digits, Verhoeff, registry lookup", "D1 users and registry", "D5 audit"],
             ["3.0 Issue authorization", "`issue_authorization`: eligibility, not voted, one pending token", "D6 elections, D3", "D2 tokens"],
             ["4.0 Cast and encrypt", "`cast_vote`: checks, AES-GCM, tx hash, signature", "D2, D3, D6", "D3 ballots and participation"],
             ["5.0 Propose and commit block", "`propose_block`: validator checks, quorum, commit", "D4 ledger", "D4 ledger"],
             ["6.0 Manage elections", "admin routes: create, status, candidates", "D6", "D6, eligibility rows"],
             ["7.0 Audit and verify chain", "`validate_chain`, `tamper_test_clone`, block browser", "D4, D5", "D5 audit"],
             ["8.0 Tally and publish", "`tally_results`: decrypt and count", "D3, D6", "-"]],
            widths=[1.35, 2.45, 1.3, 1.3], size=9.5, align=["l", "l", "l", "l"]),
        dfig("dfd1", 5.8, 4.4),
        H3("5.3.3 Level 2: casting a ballot"),
        P("Level 2 expands processes 4.0 and 5.0, the heart of the system. The three guard checks (election and candidate, token, no prior participation) come before any cryptography; the encryption and "
          "signing steps produce a transaction; and the ledger steps (schema and uniqueness, validator checks, quorum, commit) decide whether it becomes a block. Only after the block is committed does 4.6 save the ballot, "
          "mark the token used and add the participation row, all in one database commit, so that a rejected block leaves no trace."),
        dfig("dfd2", 5.8, 4.2),
    ]


# =====================================================================================================================
def uml():
    return [
        H2("5.4 UML Diagrams"),
        H3("5.4.1 Class diagram"),
        P("The classes of the diagram are the SQLAlchemy models in `app/models/models.py`, together with the two service modules and the identity-provider interface. `User` has at most one `VoterProfile`. "
          "`Election` owns `Candidate` rows. `VoterEligibility`, `VotingAuthorization` and `VoterParticipation` are each unique on the pair (election, voter), which is what lets the database refuse a second vote independently of the "
          "application code. `Ballot` has no voter column. `LedgerBlock` and `LedgerTransaction` are linked by block index, `ValidatorNode` stores the three public keys, and `AuditLog` records actions. "
          "`IdentityVerificationProvider` is an abstract class with one method, `verify`; `DemoAadhaarProvider` implements it with the local registry, so a real adapter could be substituted without touching the routes."),
        dfig("uml", 5.8, 5.4),
        H3("5.4.2 Use-case diagram"),
        P("There are three actors. The table lists their use cases and the API group that serves each."),
        TAB("Use cases by actor", ["Actor", "Use cases", "Served by"],
            [["Voter", "Sign in and out; verify Aadhaar identity; cast one encrypted ballot; see receipt and election history; read results of closed elections", "`/api/auth/*`, `/api/voter/*`, `/api/elections/{id}/results`"],
             ["Administrator", "Create and configure elections; add and deactivate candidates; open, pause and close elections; read results of any election; read benchmark runs", "`/api/admin/*`, `/api/elections/{id}/results`"],
             ["Auditor", "Verify chain integrity; browse blocks and their validator signatures; run the tamper demonstration; read the audit log", "`/api/auditor/*`"]],
            widths=[1.1, 3.6, 1.7], size=10, align=["l", "l", "l"]),
        dfig("uc", 5.0, 4.6),
        H3("5.4.3 Sequence diagram"),
        P("The sequence diagram follows the two calls that matter, `verify` and `cast`. The verify call touches the identity provider and the token store; the cast call goes through the voting service to the "
          "ledger and then writes four kinds of rows (block, ballot, token, participation) and the audit entry. The second call returns the receipt. Two details are worth noticing: the token returned by the first call is the "
          "only copy of the secret (the database holds only its hash), and the ledger call happens before the ballot row exists, so a failed quorum aborts the whole cast."),
        dfig("seq", 5.6, 5.8),
    ]


# =====================================================================================================================
def database():
    return [
        H2("5.5 Database Design"),
        P("The database has thirteen tables, created by `Base.metadata.create_all` at start-up. The entity-relationship diagram shows the tables with their keys; the tables that follow list the columns. "
          "Types are those of the SQLAlchemy models; `UQ` means a unique constraint."),
        dfig("er", 5.8, 5.8),
        H3("5.5.1 People, elections and eligibility"),
        TAB("Tables for users, elections and eligibility", ["Table", "Columns", "Keys and constraints"],
            [["users", "id, username, password_hash (Argon2id), role (ADMIN, VOTER, AUDITOR), display_name, email, created_at", "PK id; username unique"],
             ["voter_profiles", "id, user_id, full_name, aadhaar_hash, aadhaar_masked, dob, address, is_verified", "PK id; FK user_id (unique, one profile per user); aadhaar_hash unique"],
             ["elections", "id, title, description, start_time, end_time, status (DRAFT, OPEN, PAUSED, CLOSED), created_by, created_at", "PK id; FK created_by"],
             ["candidates", "id, election_id, name, party, description, manifesto, is_active, created_at", "PK id; FK election_id (cascade)"],
             ["voter_eligibility", "id, election_id, voter_user_id, is_eligible", "UQ (election_id, voter_user_id)"]],
            widths=[1.3, 3.3, 1.8], size=9.5, align=["l", "l", "l"]),
        H3("5.5.2 Authorization, ballots and participation"),
        TAB("Tables that implement one voter, one vote", ["Table", "Columns", "Keys and constraints"],
            [["voting_authorizations", "id, election_id, voter_user_id, token_hash, is_used, expires_at, created_at", "UQ token_hash; UQ (election_id, voter_user_id)"],
             ["ballots", "id, election_id, ballot_id (`blt_` + 32 hex), encrypted_choice, nonce, tx_hash, block_index, created_at - no voter column", "UQ ballot_id; UQ nonce"],
             ["voter_participation", "id, election_id, voter_user_id, ballot_id, created_at", "UQ (election_id, voter_user_id)"]],
            widths=[1.5, 3.3, 1.6], size=9.5, align=["l", "l", "l"]),
        H3("5.5.3 Ledger, validators, audit and benchmarks"),
        TAB("Tables of the ledger and the audit trail", ["Table", "Columns", "Keys and constraints"],
            [["ledger_blocks", "id, block_index, timestamp, previous_hash, merkle_root, block_hash, validator_signatures (JSON text), transaction_count, created_at", "UQ block_index; UQ block_hash"],
             ["ledger_transactions", "id, tx_hash, block_index, election_id, ballot_id, encrypted_payload, nonce, timestamp, signature", "UQ tx_hash; UQ nonce; FK block_index; index on election_id"],
             ["validator_nodes", "id, node_id, public_key, is_active", "UQ node_id"],
             ["audit_logs", "id, timestamp, actor_user_id, actor_username, action, entity_type, entity_id, details, ip_address", "PK id; FK actor_user_id"],
             ["benchmark_runs", "id, timestamp, total_ops, sync_duration, async_duration, throughput_sync, throughput_async, mean_latency_ms, p95_latency_ms, details_json", "PK id"]],
            widths=[1.5, 3.3, 1.6], size=9.5, align=["l", "l", "l"]),
        H3("5.5.4 Separation of identity and ballot"),
        P("The design intends the person and the ballot to live in different places. The `ballots` table carries an anonymous ballot id (`blt_` followed by 32 random hex digits), the ciphertext, a random nonce, "
          "the transaction hash and the block index, but no user id. The `ledger_transactions` table repeats the ballot id and the ciphertext. The record that a given user has voted is a separate row in "
          "`voter_participation`, which exists to enforce the uniqueness rule. Three layers are visible to the voter: the account (`users`), the Aadhaar number (stored only as a salted hash plus a masked form "
          "`XXXX-XXXX-1234`) and the one-time token (stored only as a hash)."),
        P("The separation is **partial**, and the report says so plainly. `voter_participation` stores the voter id and the ballot id in the same row, so anyone with read access to the database can join a voter to a "
          "ballot id; the ballot ciphertext is under one AES key that the server holds, so a party with the database and `data/secrets.json` can then decrypt the choice. The measurement run after the HTTP test found "
          f"{F.HTTP.get('db_linkable_voter_ballot_rows', 'n')} of {F.HTTP.get('db_ballots', 'n')} ballots joinable to a voter in this way. The README describes a per-election key, but `app/config.py` generates a single key. "
          "What the design does give is that the receipt page, the ledger and the auditor interface never show a choice, and that the ordinary application code has no query that returns a voter together with a choice. "
          f"A blind-signature or mix-network design in the line of Chaum [{R['chaum']}] would be needed for unlinkability against the operator; it is listed under future scope."),
    ]


# =====================================================================================================================
def modules():
    return [
        H2("5.6 Module Design"),
        P("The code is organised as small packages with one responsibility each. The table lists them with their sizes in non-blank lines of Python or TypeScript, counted from the source tree."),
        TAB("Modules of AegisBallot", ["Module (path)", "Responsibility"],
            [["`app/main.py`", "Creates the FastAPI app, mounts the JSON router and the static files, initialises the database, validators and genesis block, and keeps the legacy HTML routes"],
             ["`app/api_v1.py`", "21 JSON routes in four groups (auth, admin, voter, auditor) with Pydantic input models, CSRF and role dependencies"],
             ["`app/identity/`", "`verhoeff.py` (checksum and generator) and `provider.py` (`IdentityVerificationProvider`, `DemoAadhaarProvider`)"],
             ["`app/services/`", "`voting_service.py` (authorization, cast, tally), `election_service.py` (create, status, candidate), `audit.py` (`log_event`)"],
             ["`app/ledger/ledger.py`", "validators, genesis, Merkle root, block hash, `propose_block`, `validate_chain`, `tamper_test_clone`"],
             ["`app/security/`", "Argon2id hashing, AES-GCM and Ed25519 helpers, session store, in-memory rate limiter"],
             ["`app/models/models.py`", "The thirteen SQLAlchemy models"],
             ["`app/benchmarks/run_benchmark.py`", "Synthetic voters, synchronous and batched voting, latency statistics, JSON and database output"],
             ["`app/seed.py`", "Demo data: admin, auditor, 20 voters with synthetic Aadhaar numbers, two elections, eight seeded votes"],
             ["`frontend/src`", "React pages, UI kit, API client, query hooks, theme and auth context"]],
            widths=[2.0, 4.4], size=9.5, align=["l", "l"]),
        H3("5.6.1 Identity module"),
        P("`DemoAadhaarProvider.verify` implements three checks in order: the cleaned string must have exactly twelve digits; the Verhoeff checksum must hold; and the salted SHA-256 of the number must exist in "
          "`voter_profiles`. It returns the profile and the user, and the route then confirms that the user is the logged-in voter. The class is explicitly labelled a demonstration provider in code and in the interface: it "
          "does not contact UIDAI and holds only synthetic numbers generated by `generate_valid_aadhaar`. The Aadhaar Act, 2016 [" + str(R['aadhaar_act']) + "] governs real use; a production adapter would implement the same interface "
          "against an authorised service."),
        H3("5.6.2 Voting service"),
        P("`issue_authorization` checks eligibility and prior participation, refuses a second pending token, creates a 256-bit URL-safe token and stores its hash with a ten-minute expiry. `verify_authorization` re-hashes the presented "
          "token and checks existence, use and expiry. `cast_vote` runs the guard checks, encrypts, signs, calls the ledger and then persists the rows. `tally_results` decrypts every ballot of an election and counts "
          "the choices; the result is sorted by votes."),
        H3("5.6.3 Ledger module"),
        P("Three validator key pairs are created on first use and written to `data/validators.json`; the public keys are in `validator_nodes`. `propose_block` loads the last block, builds the next index, computes the Merkle "
          "root and block hash, lets each validator check the block, collects the signatures of those that approve and commits the block if at least two did. `validate_chain` recomputes the Merkle root, the block hash and "
          "the previous-hash link of every block. `tamper_test_clone` simulates a changed hash on a copy held in memory."),
        dfig("ledger", 5.6, 3.6),
        H3("5.6.4 Security and audit modules"),
        P(f"`security/auth.py` wraps Argon2id from argon2-cffi [{R['argon2']}]. `crypto.py` provides SHA-256, canonical JSON, AES-256-GCM, Ed25519 and the Aadhaar salted hash. `sessions.py` keeps sessions in a dictionary in memory, each with "
          "a CSRF token. `rate_limit.py` is a sliding window of timestamps per key. `audit.log_event` writes one `audit_logs` row with actor, action, entity, details and client address; the API calls it for login success and "
          "failure, logout, verification success and failure, token issue, vote cast, vote rejected, election and candidate changes, integrity checks and tamper tests."),
        H3("5.6.5 Benchmark module"),
        P(f"`run_benchmark` creates synthetic voters (Argon2-hashed passwords, Verhoeff-valid Aadhaar numbers), runs a synchronous series and three batched series (batch sizes 10, 20 and 30), computes the mean, median, 95th "
          f"percentile, minimum, maximum and standard deviation per series and the throughput, writes `benchmark_results/*.json` and stores a `benchmark_runs` row that the administrator's page displays. "
          "The batched series process each batch one vote after another in a single thread; they model the batch structure of the base paper but are not concurrent, and the results chapter treats them accordingly."),
        H3("5.6.6 Front-end pages"),
        TAB("Pages of the React application (`frontend/src/App.tsx`)", ["Route", "Role", "Content"],
            [["`/`", "public", "Landing: live counts from `/api/public/overview`, how it works, elections on the ballot"],
             ["`/login`", "public", "Sign-in with quick-fill demo accounts"],
             ["`/app/admin`, `/app/admin/elections`, `/app/admin/elections/:id`, `/app/admin/benchmarks`", "ADMIN", "Dashboard with KPIs, validators and turnout chart; election list and creation; election detail with candidates and results; benchmark charts"],
             ["`/app/voter`, `/app/voter/:id/verify`", "VOTER", "Election list; the three-step vote flow (verify, choose, receipt)"],
             ["`/app/auditor`, `/app/auditor/blocks/:index`", "AUDITOR", "Chain integrity, validators, blocks, transactions, audit log; block detail with signatures"],
             ["`/app/results/:id`", "ADMIN, VOTER", "Vote-share chart and ranked table of one election"]],
            widths=[2.4, 0.9, 3.1], size=9.5, align=["l", "c", "l"]),
        P("A `Protected` wrapper redirects unauthenticated visitors to the login page and sends a signed-in user whose role does not match to the home page of their own role. This is a convenience only: every route is "
          "protected again on the server by the role dependencies, and the server is the only authority."),
    ]


# =====================================================================================================================
def algorithms():
    return [
        H2("5.7 Algorithm Design"),
        P("Two algorithms carry the design. The first is the casting algorithm, which decides whether a ballot is accepted; the second is the audit algorithm, which decides whether the recorded chain is still consistent. "
          "Their mathematics is given in Chapter 6; the flow charts show the control flow."),
        dfig("flow_cast", 5.4, 6.0),
        P("The casting flow has three guard decisions before any cryptography is done. Failing one returns HTTP 400 and an audit entry and stores nothing. Two further decisions are taken by the validators: whether the block is "
          "valid for each of them, and whether at least two approve. If the quorum fails a `ValueError` is raised, the route answers with 400 and the token stays unused, so the voter may retry within the ten minutes."),
        dfig("flow_audit", 5.2, 4.6),
        P("The audit flow is deliberately simple: it uses only information in the ledger tables, so any holder of a copy can repeat it. The chart also shows its limits, which the tamper study of Chapter 8 measures: "
          "signatures and transaction hashes are not re-verified, and the ballots table is not compared with the ledger."),
    ]


# =====================================================================================================================
def ui_design():
    return [
        H2("5.8 User-Interface Design"),
        P("The interface is a single-page application with a dark and a light theme. The design follows five rules: one task per screen (the vote flow has three visible steps: verify identity, choose a candidate, receive the receipt); "
          "the state of the system is always visible (ledger height and health on the dashboards and on the landing page); destructive or irreversible actions ask for confirmation (the vote asks the voter to confirm the selection; "
          "closing an election is a separate button); every failure is shown as a toast with the server's message; and the notice \"Demo verification environment - synthetic identities only\" is shown wherever Aadhaar is entered."),
    ] + ([] if F.REPORT else [
        PAIR([pshot("01_landing_dark.png", "Landing page: live counts from the running ledger and the entry to the sign-in."),
              pshot("09_login.png", "Sign-in page with quick-fill demo accounts for the three roles.")], 2.8),
        PAIR([pshot("10_admin_dashboard.png", "Administrator dashboard: voters, votes, ledger height, turnout per election and the three validators."),
              pshot("17_voter_aadhaar_verification.png", "Voter flow, step 1: the masked Aadhaar of the account and the field for the 12-digit number.")], 2.8),
        PAIR([pshot("18_voter_candidate_selection.png", "Voter flow, step 2: identity verified, ten-minute countdown, candidate cards and confirmation."),
              pshot("19_voter_receipt.png", "Voter flow, step 3: receipt with ballot id, transaction hash and block number.")], 2.8),
        PAIR([pshot("21_auditor_dashboard.png", "Auditor console: chain integrity, validators, blocks, transactions and the audit log."),
              pshot("22_auditor_block_detail.png", "Block detail with previous hash, Merkle root, block hash and validator signatures.")], 2.8),
    ]) + [
        P("Accessibility and layout choices are modest and honest: colour is never the only carrier of status (badges carry words), forms use labelled fields, and the layout was checked at 1440 by 900 pixels and "
          "at a 390 by 844 pixel phone width (the mobile administrator dashboard is shown in Appendix C). No formal accessibility audit or usability test with real voters was done."),
    ]


# =====================================================================================================================
def decisions():
    return [
        H2("5.9 Design Decisions and Their Reasons"),
        TAB("Principal design decisions", ["Decision", "Alternatives considered", "Reason"],
            [["Local permissioned ledger, three in-process validators, quorum 2 of 3", "Public Ethereum chain as in the base paper; a real PBFT network",
              f"Runs on one laptop with no wallet or fees; Ethereum is quoted by the base paper at about 119.1 tx/s [{R['base']}]; PBFT [{R['pbft']}] needs a network of nodes that the project could not provide. The cost is that the trust is simulated"],
             ["One transaction per block", "Batching many votes in a block", "Simple receipts (each voter gets a block number) and simple recovery; the cost is a longer chain and linear validation time"],
             ["Aadhaar checked locally with Verhoeff and a salted-hash registry", "Calling UIDAI; storing the number", f"UIDAI is not available to a student project; the Verhoeff check [{R['verhoeff']}] catches mistyped numbers; storing only a hash avoids keeping the number"],
             ["Token between identity and ballot", "Sending the Aadhaar number with the ballot", "The cast call carries a token, not an identity, and the token is stored only as a hash"],
             ["Four overlapping one-vote rules", "A single check in code", "Unique constraints in the database hold even if the application logic is bypassed"],
             ["AES-256-GCM for the choice", "Plain candidate id; per-voter keys; homomorphic encryption", f"Authenticated encryption [{R['gcm']}] hides choices from the ledger and the auditor view at low cost; a single key is the simplification"],
             ["Ed25519 signatures", "RSA; HMAC", f"Small, fast signatures [{R['eddsa']}]; {F.MICRO['ed25519_sign']['mean_ms']:.2f} ms to sign in the micro-benchmark"],
             ["Argon2id for passwords", "bcrypt as in the batch abstract", f"Memory-hard, current guidance [{R['argon2rfc']}]; one verification costs about {F.MICRO['argon2id_verify']['mean_ms']:.0f} ms, which dominates the HTTP latency"],
             ["React single-page app over a JSON API", "Server-rendered Jinja pages only", "Role consoles with live data and charts; the Jinja pages remain as a fallback"],
             ["SQLite", "A client-server database", "No installation; adequate for a demonstration; concurrent writers were not tested"]],
            widths=[1.8, 1.7, 2.9], size=9, align=["l", "l", "l"]),
    ]
