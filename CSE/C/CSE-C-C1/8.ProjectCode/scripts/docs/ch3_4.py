"""Chapters 3 and 4: Feasibility Study; System Requirements and Analysis."""

from . import facts as F
from . import lit
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def _validate_ms(key):
    return F.VALIDATE_BY_HEIGHT.get(key, {}).get("median_ms")


def chapter3():
    lat = F.LAT
    st = F.STAGE
    v300 = F.VALIDATE_BY_HEIGHT.get("300", {})
    arg_h = F.MICRO.get("argon2id_hash", {}).get("mean_ms", 0)
    ed_s = F.MICRO.get("ed25519_sign", {}).get("mean_ms", 0)
    aes_e = F.MICRO.get("aes256gcm_encrypt", {}).get("mean_ms", 0)
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P("A feasibility study asks whether the proposed system can be built and used with the resources at hand. This chapter examines the technical, economic, operational and schedule feasibility "
          "of AegisBallot and ends with its advantages and constraints. The assessments rely on what was actually built and measured, not on projections."),

        H2("3.1 Technical Feasibility"),
        P("The technical question is whether the security mechanisms that the batch objectives require can be implemented with freely available components on an ordinary computer, and whether their cost "
          "leaves the system usable. The team answered it by building the platform and measuring it."),
        H3("3.1.1 Availability of the required techniques"),
        P(f"Every mechanism has a maintained open-source implementation. Password hashing uses Argon2id from argon2-cffi {F.ENV.get('libs', {}).get('argon2-cffi', '23.1.0')} [{R['argon2']}]. Ballot encryption (AES-256 in Galois/Counter Mode [{R['gcm']}]), "
          f"hashing (SHA-256 [{R['sha2']}]) and signatures (Ed25519 [{R['eddsa']}]) come from the cryptography library {F.ENV.get('libs', {}).get('cryptography', '42.0.7')} and Python's standard hashlib. The Verhoeff checksum "
          f"[{R['verhoeff']}] is a short table-driven function written for the project and checked by a unit test. The backend uses FastAPI {F.ENV.get('libs', {}).get('fastapi', '0.110.0')} [{R['fastapi']}] with SQLAlchemy "
          f"{F.ENV.get('libs', {}).get('sqlalchemy', '2.0.30')} [{R['sqlalchemy']}] and SQLite, and the interface uses React [{R['react']}] with Vite."),
        H3("3.1.2 Cost of the mechanisms"),
        P(f"The measured cost shows that the mechanisms are affordable on one machine. The cryptography of a vote is cheap: an AES-GCM encryption took {aes_e * 1000:.0f} microseconds and an Ed25519 signature {ed_s:.2f} ms on average. "
          f"Password hashing is the dominant cost, at {arg_h:.0f} ms per Argon2id hash with the library defaults, which is intended. The whole in-process cost of a vote, covering authorisation, encryption, a three-validator block and "
          f"the database commit, was {st.get('authorise', 0) + st.get('encrypt_sign_hash', 0) + st.get('propose_block', 0) + st.get('persist', 0):.1f} ms in the stage-breakdown run, and a complete voter journey over HTTP (login, "
          f"Aadhaar verification and cast) averaged {lat['end_to_end']['mean_ms']:.0f} ms. Checking a chain of {v300.get('height_blocks', 301)} blocks took {v300.get('median_ms', 0):.0f} ms."),
        H3("3.1.3 Technical risks"),
        TAB("Technical risks identified during the study",
            ["Risk", "Observation", "Mitigation or status"],
            [["Concurrent writers on SQLite and on the ledger", "One block per vote; the next block index is read from the latest block, and `block_index` is unique", "Not tested under parallel load; single-process demonstration only"],
             ["Key files on the server", "AES key, validator keys and system key are plain files in `data/`", "Acceptable for a prototype; production would need a hardware security module"],
             ["Sessions and rate limits held in memory", "Lost on restart and not shared between processes", "Acceptable for one process; a shared store is future work"],
             ["Integrity check shallower than the claim", "Signatures and transaction hashes are not recomputed by `validate_chain`", "Measured in the tamper study; a stricter audit is described as future scope"],
             ["Identity registry is synthetic", "No contact with UIDAI", "Provider interface allows a real adapter; not feasible within the project"]],
            widths=[1.7, 2.6, 2.0], align=["l", "l", "l"], size=9.5),
        H3("3.1.4 Alternatives considered"),
        P(f"Two alternatives to the local ledger were weighed. A public Ethereum chain, as in the base paper [{R['base']}], needs a node, a contract language and tooling that the team did not have, and the "
          f"paper itself reports transaction times of seconds on a test chain and quotes a theoretical throughput of 119.1 transactions per second for the main network. A framework for permissioned chains "
          f"such as Hyperledger Fabric [{R['fabric']}] needs several services and containers to run even a minimal network, which conflicts with the aim of a one-script installation. "
          "The team therefore wrote a small permissioned ledger on top of the database that the application already uses. This choice makes the project feasible, and it is also the reason why the ledger "
          "must be described as a simulation of a distributed system."),
        P("The conclusion of the technical study is that the design is feasible with the chosen components for a single-machine prototype, and that the open risks concern deployment, not the algorithms."),

        H2("3.2 Economic Feasibility"),
        P("The project was carried out with computers that the team already used, so no hardware or licence was purchased for it. The team does not give a rupee estimate, because none was recorded and an "
          "invented figure would not be reliable; the table below lists the cost items qualitatively."),
        TAB("Cost items of the prototype and of a production deployment",
            ["Item", "In this project", "In a production deployment"],
            [["Software licences", "None; every library is open source (FastAPI, SQLAlchemy, cryptography, argon2-cffi, React, Vite, Tailwind CSS, Recharts)", "None for these components; support contracts optional"],
             ["Development hardware", "Existing personal computers; measurements on one Core i5-12500 PC with 15.7 GB of memory", "Servers sized by a load test that was not done here"],
             ["Cloud or blockchain network fees", "None; the ledger is local and no cryptocurrency is used", "Validator hosting at independent institutions; not costed"],
             ["Identity service", "None; synthetic registry", "Authorised access to Aadhaar authentication would need an arrangement with UIDAI and is not costed here"],
             ["Key management and TLS certificates", "None; keys are files, TLS not configured", "Hardware security modules and certificates; not costed"],
             ["Security assessment", "Self-made tests only", "Independent penetration test and audit; not costed"],
             ["Staff", "Four students and a guide", "Not estimated"]],
            widths=[1.5, 2.7, 2.1], align=["l", "l", "l"], size=9.5),
        P("A second economic consideration is the cost of failure. A voting prototype that is mistaken for a production system could cause harm out of proportion to its development cost, which is why the "
          "interface labels the identity step as a demonstration environment and why this report lists the missing safeguards (transport security, key custody, independent validators) instead of "
          "describing them as future conveniences."),
        P("The economic position is therefore that the prototype costs nothing beyond the team's time, and that the cost of a real deployment is dominated by items outside this project: identity authorisation, "
          "independent validators, key custody and assurance."),

        H2("3.3 Operational Feasibility"),
        P("Operational feasibility asks whether the intended users can operate the system. A voter needs three steps: sign in, enter an Aadhaar number and choose a candidate, after which the receipt is shown. "
          "The screens of Chapter 8 show the flow with a step indicator, a ten-minute countdown for the token, a confirmation dialog and a receipt with copy buttons. The administrator works from a dashboard that "
          "lists elections with turnout and from forms to create elections and candidates. The auditor has one page with the chain status, a button that verifies the ledger, a tamper demonstration and tabs for "
          "blocks, transactions and the audit log."),
        P("For the operator, the installation is one script (`run.bat`) that creates a virtual environment, installs the requirements, seeds demonstration data and starts the backend and the frontend on fixed ports "
          f"({F.API_PORT} and {F.WEB_PORT}). A Docker file is also provided. A restart clears sessions and rate-limit counters, which the operator must expect, and the files in `data/` must be backed up because they "
          "hold the keys without which encrypted ballots cannot be tallied. The demonstration is labelled in the interface as a demo verification environment so that no user mistakes it for an official service."),

        P("Errors are reported in a form that an operator or voter can act on. A rejected verification or vote returns a short message with status 400 or 403 (for example that the checksum is invalid, that the "
          "number does not belong to the signed-in voter, or that the token has expired), a throttled client receives status 429 and a message to try again in a minute, and an unexpected failure while recording "
          "a vote returns a message that nothing was submitted and the vote may be tried again. Each of these events is also written to the audit log, so that an operator can reconstruct what happened."),

        H2("3.4 Schedule Feasibility"),
        P("The work was organised in phases that depend on one another. The project records do not contain a planned calendar, so the table below gives the order of the phases and the date that the files "
          "of the repository carry as evidence; planned start and end dates are left as placeholders."),
        TAB("Phases of the project",
            ["Phase", "Output", "Evidence in the repository", "Planned dates"],
            [["1. Study and design", "Abstract, base paper, literature survey, objectives", "Batch documents 2 to 6", "[DATE]"],
             ["2. Backend", "FastAPI services, models, ledger, identity provider, security", "`app/`; 17 automated tests", "[DATE]"],
             ["3. Benchmarks", "Synthetic voters, synchronous and batched runs", "`benchmark_results/` files dated 8 September 2026", "[DATE]"],
             ["4. Interface", "JSON API layer and React single-page application", "`app/api_v1.py`, `frontend/`; screenshots dated 19 October 2026", "[DATE]"],
             ["5. Measurement and documentation", "Experiment script, figures, decks and report", "`scripts/run_experiments.py`, `docs/`; run of 26 October 2026", "[DATE]"]],
            widths=[1.4, 2.0, 2.2, 0.8], align=["l", "l", "l", "c"], size=9.5),
        P("The sequence shows that the work is realistic for an academic term: the backend and the measurements are separable from the interface, and each phase has a checkable output."),

        H2("3.5 Advantages and Constraints"),
        P("The study yields the following advantages and constraints."),
        B("Advantage: no licence, cloud or network cost, and a one-script installation.",
          "Advantage: the security mechanisms are standard, well-documented primitives, and their cost is small relative to the cost of password hashing.",
          "Advantage: the measured results are repeatable by anyone who runs the experiment script.",
          "Constraint: a single machine, single process and single SQLite file, so no result applies to concurrent or distributed operation.",
          "Constraint: synthetic identities and a local registry, so no result applies to real voters or to UIDAI.",
          "Constraint: partial ballot secrecy and no TLS, which disqualify the prototype from real elections."),
    ]


def chapter4():
    s = F.BENCH_SYNC
    lat = F.LAT
    v100 = F.VALIDATE_BY_HEIGHT.get("100", {}).get("median_ms")
    v300 = F.VALIDATE_BY_HEIGHT.get("300", {}).get("median_ms")
    g = F.GROWTH
    out = [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        P("This chapter describes the systems that voters and election authorities use today, sets the proposed system against them, and states what the proposed system must do and how well. "
          "It then lists the hardware and software, the user roles and the constraints."),

        H2("4.1 Existing System and Its Limitations"),
        P("Three kinds of system exist today. In manual polling, voters are identified at a booth against a printed list, mark paper ballots or press a button on a machine, and officials count the result. "
          "In central-database e-voting, a web application checks a password or one-time code and stores ballots in a database controlled by the operator. In public-chain prototypes, votes are transactions "
          f"on a network such as Ethereum, as in the base paper [{R['base']}]."),
        TAB("Existing approaches and their limitations",
            ["Existing approach", "Typical limitations"],
            [[lit.EXISTING_SYSTEM[0], lit.LIMITATIONS_EXISTING[0]],
             [lit.EXISTING_SYSTEM[1], lit.LIMITATIONS_EXISTING[1]],
             [lit.EXISTING_SYSTEM[3], lit.LIMITATIONS_EXISTING[2]],
             [lit.EXISTING_SYSTEM[2], lit.LIMITATIONS_EXISTING[3]],
             [lit.EXISTING_SYSTEM[4], lit.LIMITATIONS_EXISTING[4]]],
            widths=[3.1, 3.2], align=["l", "l"], size=10),
        P("The limitations common to the three approaches are that the voter cannot check that the vote was recorded, an observer cannot recompute the result, and identity checks are either weak "
          f"(a password) or tied to a particular biometric infrastructure [{R['base']}], [{R['newera']}]. Security analyses of real systems [{R['estonia']}], [{R['voatz']}] add that the surrounding application "
          "is often the weakest part."),

        H2("4.2 Proposed System and Its Advantages"),
        P("AegisBallot is a web application with three roles. The voter authenticates, proves identity with an Aadhaar number, obtains a single-use token and casts one encrypted ballot; the choice is "
          "committed to a hash-chained ledger that three validators sign, and the voter receives a receipt of ballot id, transaction hash, block number and block hash. The administrator manages "
          "elections and candidates and reads results. The auditor recomputes the chain, inspects blocks and the audit log and runs a tamper demonstration."),
    ]
    if not F.REPORT:
        out.append(FIG(F.diag("01_system_architecture.png"), "Architecture of the proposed system.", 5.6))
    else:
        out.append(P("The architecture of the proposed system is drawn in Chapter 5."))
    out += [
        P("The central design idea is to keep four things apart. The voter's *identity* is held in the users and voter-profile tables and is checked once, at verification. The *authorisation* is a random token "
          "whose hash, not the token, is stored, which allows exactly one ballot and expires after ten minutes. The *ballot* is stored under a random ballot id with its ciphertext and carries no voter column. "
          "The *ledger transaction* repeats the ciphertext, the ballot id and a nonce under a signature, and it is what the auditor can check. A record that joins voter and ballot id is kept in a participation "
          "table, because the database needs it to enforce one vote per voter; this is the point at which secrecy is only partial, and it is discussed again in Chapter 9."),
        TAB("Advantages of the proposed system over the existing approaches",
            ["Advantage", "How it is achieved", "Evidence"],
            [["Identity bound to the ballot", "Verhoeff-checked, hashed Aadhaar number that must belong to the signed-in account", "HTTP checks: bad checksum, unknown and foreign numbers rejected"],
             ["One voter, one vote", "Eligibility, unique participation row, single-use token, ledger nonce uniqueness", "Replay and second-verify attempts rejected; unit test for duplicates"],
             ["Tamper evidence", "SHA-256 hash chain, per-block validator signatures, auditor verification", f"{F.N_TAMPER_PRODUCT} of {F.N_TAMPER} tamper cases detected by the product check"],
             ["Ballot confidentiality at rest", "AES-256-GCM per ballot; no voter id in the ballots table", "Unit test for identity separation; limits stated in Chapter 9"],
             ["Accountability", "Audit log of logins, verifications, casts, status changes and checks", "Unit test for audit logging"],
             ["Measured cost", "Benchmark, stage breakdown and HTTP latency", f"{lat['end_to_end']['mean_ms']:.0f} ms mean per complete voter journey"]],
            widths=[1.5, 2.6, 2.2], align=["l", "l", "l"], size=9.5),

        H2("4.3 Functional Requirements"),
        P("The functional requirements were derived from the six batch objectives and are implemented by the JSON routes of `app/api_v1.py` (prefix `/api`). The table below gives each requirement with the route that realises it."),
        TAB("Functional requirements and the routes that implement them",
            ["ID", "Requirement", "Role", "Implemented by"],
            [["FR-1", "Sign in with username and password, sign out, restore the session", "All", "`POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`"],
             ["FR-2", "Show public information: elections, ledger height and validity, votes cast, validators", "Public", "`GET /api/public/overview`"],
             ["FR-3", "Create an election with title, description and polling window; grant eligibility to all voters", "Admin", "`POST /api/admin/elections`"],
             ["FR-4", "Open, pause or close an election; reject any other status", "Admin", "`POST /api/admin/elections/{id}/status`"],
             ["FR-5", "Add a candidate and activate or deactivate it", "Admin", "`POST /api/admin/elections/{id}/candidates`, `POST /api/admin/candidates/{id}/toggle`"],
             ["FR-6", "Show dashboard figures, election list and election detail with turnout", "Admin", "`GET /api/admin/overview`, `/api/admin/elections`, `/api/admin/elections/{id}`"],
             ["FR-7", "Show stored benchmark runs", "Admin", "`GET /api/admin/benchmarks`"],
             ["FR-8", "List the elections a voter can see and whether the voter has voted", "Voter", "`GET /api/voter/elections`, `GET /api/voter/elections/{id}`"],
             ["FR-9", "Verify the Aadhaar number (format, checksum, registry, own identity, eligibility, not yet voted) and issue a ten-minute token", "Voter", "`POST /api/voter/elections/{id}/verify`"],
             ["FR-10", "Cast one encrypted, signed ballot with the token and return a receipt", "Voter", "`POST /api/voter/elections/{id}/cast`"],
             ["FR-11", "Publish the tally of a closed election; let the administrator read any tally", "Admin, all after close", "`GET /api/elections/{id}/results`"],
             ["FR-12", "Verify chain integrity, browse blocks and transactions, show validators", "Auditor", "`GET /api/auditor/overview`, `POST /api/auditor/verify`, `GET /api/auditor/blocks/{index}`"],
             ["FR-13", "Run the tamper demonstration on a copy of the ledger", "Auditor", "`POST /api/auditor/tamper-test`"],
             ["FR-14", "Record every important action with actor, entity, details and address", "System", "`audit_logs` written by `log_event`"]],
            widths=[0.5, 2.5, 0.9, 2.4], align=["c", "l", "c", "l"], size=9),
        P(f"The batch objectives also mention registration of voters. In the prototype, voters are created by the seeding script and by the benchmark generator, and there is no self-registration route; the "
          f"{F.N_TABLES}-table database holds the registry that the verification step queries. This is a deliberate narrowing, recorded in the scope."),

        P("The identity route (FR-9) deserves a precise statement because it carries the main security rule. The checks run in this order, and the first failure ends the request with an audit-log entry:"),
        N("the client address is under the verification rate limit of 15 requests per minute (otherwise status 429);",
          "the election exists;",
          "the number has twelve digits after spaces and hyphens are removed and its Verhoeff checksum is valid (status 400);",
          "the salted hash of the number is present in the voter registry (status 400);",
          "the registered voter is the signed-in voter (status 403);",
          "the voter is eligible for this election (status 403);",
          "the voter has not already voted (status 400) and has no pending unexpired token."),
        P("Only then is a token issued and the active candidates of the election returned."),

        H2("4.4 Non-Functional Requirements"),
        P("The non-functional requirements are stated with the value that was measured, so that each can be judged as met or not met. The measurements were taken on the machine of Section 4.5 while other jobs were using the processor, "
          "so the figures are indicative."),
        TAB("Non-functional requirements and measured values",
            ["Quality", "Requirement", "Measured / observed", "Status"],
            [["Performance", "A vote is recorded without a perceptible delay", f"Mean {s.get('mean_ms', 0):.1f} ms per vote in the {F.N_VOTERS_BENCH}-voter benchmark (16-17 ms on an idle PC); {lat['cast']['mean_ms']:.0f} ms for the cast request over HTTP", "Met"],
             ["Performance", "Whole voter journey under a second", f"{lat['end_to_end']['mean_ms']:.0f} ms mean, {lat['end_to_end']['p95_ms']:.0f} ms p95 over HTTP (27 voters)", "Met"],
             ["Reliability", "No vote lost or duplicated", f"{F.N_VOTERS_BENCH} of {F.N_VOTERS_BENCH} votes succeeded in every benchmark mode; duplicates rejected", "Met for sequential voting; concurrency not tested"],
             ["Scalability", "Integrity check stays practical as the chain grows", f"{v100:.0f} ms at 101 blocks and {v300:.0f} ms at 301 blocks (linear, about 0.5 ms per block)", "Partly: linear, single machine"],
             ["Security", "Roles, CSRF, input validation, rate limiting", f"{F.MATRIX_PASSED} of {F.MATRIX_TOTAL} HTTP checks returned the expected status", "Met"],
             ["Security", "TLS for transport", "Plain HTTP; cookie without Secure flag", "Not met"],
             ["Integrity", "Detect alteration of stored votes", f"{F.N_TAMPER_PRODUCT} of {F.N_TAMPER} tamper cases detected by the product check", "Partly"],
             ["Privacy", "No link between voter and choice", "Participation table stores voter id with ballot id; one key encrypts all ballots", "Partly"],
             ["Usability", "Voter completes the flow unaided", "Three-step flow with step indicator; no user study done", "Not measured"],
             ["Maintainability", "Tests and modular code", f"{F.PYTEST_TOTAL} automated tests, all passing; services separated from routes", "Met"],
             ["Portability", "Runs on a common desktop", "Windows 11 tested; Python and Node are cross-platform; Docker file provided but not run for this report", "Windows only verified"]],
            widths=[1.0, 1.7, 2.7, 0.9], align=["l", "l", "l", "c"], size=9),
        P(f"The cost of the vote also changes little as the chain grows: in a run of {g.get('votes', 300)} votes the mean was {g['per_vote_first_100']['mean_ms']:.1f} ms for the first hundred and "
          f"{g['per_vote_last_100']['mean_ms']:.1f} ms for the last hundred."),

        H2("4.5 Hardware Requirements"),
        TAB("Hardware",
            ["Component", "Used for the measurements", "Minimum suggested"],
            [["Processor", "Intel Core i5-12500, 6 cores / 12 threads, 3.0 GHz", "Any dual-core 64-bit processor; Argon2id and block creation are single-threaded"],
             ["Memory", "15.7 GB", "4 GB (the application itself is small); not measured"],
             ["Storage", "Local SSD; the development database held 213 blocks, 212 ballots and 200 voters", "A few hundred megabytes; not measured"],
             ["Network", "Loopback only", "None for the prototype; browser and server on one machine"],
             ["Display", "1440 x 900 for screenshots; a 390 x 844 capture of the dashboard was also taken", "Any current browser"]],
            widths=[1.2, 2.9, 2.2], align=["l", "l", "l"], size=9.5),
        P("The 'minimum suggested' column is a suggestion of the team, not a measured threshold."),

        H2("4.6 Software Requirements"),
        TAB("Software",
            ["Layer", "Component", "Version"],
            [["Operating system", "Windows 11 Pro", "Build used for the measurements"],
             ["Language", "Python", f"{F.ENV.get('python', '3.11.9')}"],
             ["Web framework", "FastAPI / Uvicorn / Pydantic", f"{F.ENV.get('libs', {}).get('fastapi', '0.110.0')} / 0.29.0 / 2.7.0 (pinned in `requirements.txt`)"],
             ["Persistence", "SQLAlchemy / SQLite", f"{F.ENV.get('libs', {}).get('sqlalchemy', '2.0.30')} / bundled with Python"],
             ["Security", "cryptography / argon2-cffi", f"{F.ENV.get('libs', {}).get('cryptography', '42.0.7')} / {F.ENV.get('libs', {}).get('argon2-cffi', '23.1.0')}"],
             ["Templates and PDF", "Jinja2 / reportlab", "3.1.4 / 4.1.0 (legacy pages, product document)"],
             ["Frontend runtime", "Node.js / npm", "v24.19.0"],
             ["Frontend framework", "React, React Router, TanStack Query, Axios", "^18.3.1, ^7.18.4, ^5.103.2, ^1.20.0 (declared ranges in `package.json`)"],
             ["Styling and charts", "Tailwind CSS, Radix UI, Recharts, Framer Motion", "^4.3.3, ^1.6.7, ^3.10.1, ^14.2.0 (declared ranges)"],
             ["Build tooling", "Vite, TypeScript", "^8.3.0, ~5.9.3"],
             ["Testing", "pytest, httpx, Playwright", f"pytest 9.1.1 used; httpx 0.27.0 and Playwright 1.44.0 pinned in `requirements-dev.txt`"],
             ["Browser", "A current Chromium-based browser", "Used to capture the screenshots"]],
            widths=[1.4, 2.4, 2.5], align=["l", "l", "l"], size=9.5),
        P("The batch abstract names a Java-based backend, bcrypt password hashing and TLS as possible techniques. The delivered system differs on three points: the backend is Python with FastAPI, passwords are "
          "hashed with Argon2id (the variant that RFC 9106 names as the primary choice [" + str(R['argon2rfc']) + "]), and TLS is not part of the shipped configuration. These differences are recorded here and again in the scope document and the conclusion."),

        H2("4.7 User Roles"),
        TAB("User roles and permissions",
            ["Role", "Created by", "Can", "Cannot"],
            [["Voter", "Seeding script or benchmark generator", "List elections, verify own Aadhaar number, cast one ballot per election, read results of closed elections", "Access admin or auditor routes (403), vote twice, use another voter's number"],
             ["Administrator", "Seeding script", "Create elections and candidates, change status, read dashboards, benchmarks and any tally", "Cast a vote through the voter route; its session is of the ADMIN role"],
             ["Auditor", "Seeding script", "Verify the chain, browse blocks, transactions and the audit log, run the tamper demonstration", "Change elections or candidates"],
             ["Anonymous visitor", "-", "Read the public overview and the landing page", "Call any route that needs a session (401)"]],
            widths=[1.1, 1.4, 2.4, 1.4], align=["l", "l", "l", "l"], size=9.5),
    ]
    if not F.REPORT:
        out.append(FIG(F.diag("08_use_case.png"), "Use cases of the three roles.", 5.0))
    else:
        out.append(P("The use cases of the three roles are drawn in Chapter 5."))
    out += [
        P("The demonstration accounts are `admin`, `auditor` and `voter1` to `voter20`; their passwords are given in the installation guide of Appendix B."),

        H2("4.8 Requirement Traceability"),
        P("The table below traces each batch objective to the requirements that realise it and to the chapter that evaluates it, so that an objective with no evidence would be visible."),
        TAB("Traceability of objectives to requirements",
            ["Objective", "Functional requirements", "Non-functional requirements", "Evaluated in"],
            [["1 Identity-based authentication", "FR-1, FR-9", "Security, usability", "Chapters 7 and 8"],
             ["2 One voter, one vote", "FR-9, FR-10", "Reliability, security", "Chapter 7"],
             ["3 Immutable recording", "FR-10, FR-12, FR-13", "Integrity, performance", "Chapter 8 (tamper study)"],
             ["4 Administration portal", "FR-3, FR-4, FR-5, FR-6", "Usability", "Chapter 8 (screens)"],
             ["5 Results and audit trail", "FR-11, FR-14", "Integrity, privacy", "Chapters 8 and 9"],
             ["6 RBAC, validation, TLS, evaluation", "FR-1, FR-7, FR-12", "Security, performance, scalability", "Chapters 7 and 8; TLS not met"]],
            widths=[1.8, 1.6, 1.7, 1.2], align=["l", "l", "l", "l"], size=9.5),

        H2("4.9 Constraints and Assumptions"),
        P("The design was subject to the following constraints."),
        N("The system must run on one ordinary computer, started by one script, with no external service.",
          "Real Aadhaar data and the UIDAI service must not be used; identities are synthetic and the identity provider is replaceable.",
          "Every number in the report must come from a run of the project; a quantity that was not measured is stated as such.",
          "The interface must work on a desktop browser and remain readable on a narrow screen.",
          "The legacy server-rendered pages must continue to work beside the new JSON routes."),
        P("The assumptions are that the server operator is trusted with the key files, that browsers are not compromised, that the synthetic registry represents real voters well enough for the "
          "measurements to be informative, and that elections of a few hundred or thousand voters are the intended size of the demonstration."),
    ]
    return out


def blocks():
    return chapter3() + chapter4()
