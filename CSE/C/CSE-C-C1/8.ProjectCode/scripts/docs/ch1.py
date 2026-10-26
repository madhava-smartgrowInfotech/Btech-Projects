"""Chapter 1: Introduction."""

from . import facts as F
from .blocks import B, H1, H2, N, P, TAB
from .refs import CITE as R


def _bench_idle():
    """Throughput range of the five earlier idle-PC synchronous runs (2026-09-08)."""
    t = [d["sync"]["throughput"] for d in F.IDLE_RUNS]
    m = [d["sync"]["mean_ms"] for d in F.IDLE_RUNS]
    return min(t), max(t), min(m), max(m)


def blocks():
    lo_t, hi_t, lo_m, hi_m = _bench_idle()
    s = F.BENCH_SYNC
    e2e = F.LAT["end_to_end"]["mean_ms"]
    base, newera, jafar, estonia, voatz = R["base"], R["newera"], R["jafar"], R["estonia"], R["voatz"]
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        P(f"This chapter introduces the domain of the project, the motivation for building {F.PRODUCT}, the problem it addresses, the objectives set for it, the scope that was "
          "actually delivered, the contributions, and the limitations and assumptions that govern every result reported later. It closes with a map of the rest of the report."),

        H2("1.1 Domain and Background"),
        P("An election is a procedure by which a population chooses its representatives, and its value rests on public confidence that each eligible person voted at most once, that no vote was "
          "altered after it was cast, and that the published result follows from the votes. Traditional polling achieves this with physical infrastructure: voter lists, polling booths, paper ballots "
          "or electronic voting machines, and a manual or semi-automated count. These processes are slow, they need large numbers of staff, and they concentrate trust in the people who run the booth "
          f"and the count. The base paper of this project lists the same weaknesses for conventional systems: security and manipulation concerns, a lack of transparency, limited accessibility, high cost "
          f"and slow counting [{base}]."),
        P("Digital voting removes some of these weaknesses and introduces others. A web application can accept a vote from any connected device and tally it in seconds, but a conventional implementation "
          "stores the ballots in a database whose administrator can edit or delete rows without leaving a visible trace. Two further questions then decide whether the system can be trusted: who is "
          "allowed to vote, and how an outsider can check the outcome. The first is a question of identity; the second is a question of auditability."),
        P("Blockchain technology offers a way to address the second question. A blockchain is a list of records, called blocks, in which each block contains the cryptographic hash of the previous block, "
          f"so that changing an old record changes every later hash and is therefore detectable [{R['bitcoin']}], [{R['merkle']}]. When the blocks are produced by a small, known set of validators rather "
          f"than by anonymous miners the ledger is called permissioned [{R['fabric']}], and agreement among the validators can follow a Byzantine fault-tolerant protocol [{R['pbft']}]. Blockchain "
          f"voting proposals are numerous, and surveys agree that privacy protection and transaction speed are the most frequently reported difficulties [{jafar}]."),
        P("India's national identity number, Aadhaar, is a 12-digit number whose last digit is a check digit computed with the Verhoeff algorithm "
          f"[{R['verhoeff']}]. The number is issued under the Aadhaar Act of 2016 [{R['aadhaar_act']}] and is widely used to bind a person to a record. A voting system for Indian users that "
          "wants to enforce one voter, one vote needs to tie each ballot to a verified identity without letting the ballot reveal the person who cast it. This project, AegisBallot, examines that "
          "combination in a working local prototype: Aadhaar-style identity verification in front of an encrypted, hash-chained, validator-signed ledger, with an administrator console and an "
          "auditor console around it."),
        P("Three terms are used throughout the report. A *ballot* is the encrypted record of one voter's choice. A *block* is a ledger entry that holds one signed transaction and the hash of the block "
          "before it. An *audit* is the recomputation of hashes by a person who does not control the system, which in AegisBallot is the auditor role."),

        H2("1.2 Motivation"),
        P("Three observations motivated the project. First, identity and ledger are usually studied separately. The Oman model that serves as the base paper authenticates voters with biometric "
          f"technology and records votes through Ethereum smart contracts, but its administration workflow is simulated by client programs and it is not tied to an Indian national identity [{base}]. "
          f"The Aadhaar-based proposal in the batch folder describes hashing of identity documents and a chain of vote records but reports no performance or tamper tests [{newera}]. A system that "
          "joins identity, ledger, administration and audit in one deployable application is the gap named in the batch literature survey."),
        P("Second, the security claims of voting software are only as strong as the checks that can be run against them. Real deployments have been found to contain weaknesses that an analysis "
          f"of the running system exposed: the Estonian internet voting system was analysed in use and attack paths were found [{estonia}], and the Voatz mobile voting application, which was marketed with "
          f"blockchain, was shown to have exploitable weaknesses outside the blockchain itself [{voatz}]. The team therefore decided that the project should not only claim integrity but "
          "also measure which kinds of tampering its own integrity check detects, and report the cases it does not."),
        P("Third, a student-built system can be run, inspected and measured in full on one ordinary computer, which allows every number in this report to come from a run the reader can repeat. "
          "The whole platform, from the database to the validators, starts with one script and needs no network service or cryptocurrency."),

        H2("1.3 Problem Statement"),
        P("The batch problem statement lists four weaknesses of the present situation. The team restates them as the problem that the project addresses:"),
        B("Manual voting is slow, needs heavy physical infrastructure and delays the declaration of results.",
          "Conventional digital voting stores ballots in a database that an administrator could alter.",
          "Without binding a ballot to a verified identity, duplicate or ineligible voting cannot be prevented reliably.",
          "Voters and observers have no way to verify independently that the result was not manipulated."),
        P("The need that follows from these weaknesses is a voting platform that verifies identity, records every ballot so that later alteration is detectable, and gives an auditor "
          "the means to recompute the result and the chain."),

        H2("1.4 Need of the Project"),
        P("The need is both practical and methodological. Practically, an election authority that wants an electronic channel needs a design in which no single operator can change a vote unnoticed, "
          "in which a voter can obtain proof that the vote was recorded, and in which the same voter cannot vote twice. Methodologically, a project that claims such properties needs an evaluation that "
          "tests them: functional tests of the rules, a test of what the integrity check detects, and measurements of the cost of the added safeguards. The base paper concentrates on the time taken by "
          f"registration and voting transactions on a test chain [{base}]; AegisBallot adds the identity and administration layers and also tests the audit mechanism."),
        P("It is equally important to state what the project does not provide. It does not contact the Unique Identification Authority of India, it does not run a distributed network of validators, "
          "and it is not a system for a national election. It is an academic prototype whose purpose is to show the design, to measure it honestly and to record where its protection ends."),

        H2("1.5 Objectives"),
        P("The batch fixed six objectives. The table below lists each of them with the feature of AegisBallot that addresses it and the evidence collected in the later chapters."),
        TAB("Objectives of the project and how each was addressed",
            ["No.", "Objective (batch document 6)", "Feature of AegisBallot", "Evidence"],
            [["1", "Voter registration and authentication with Aadhaar-based identity verification",
              "Argon2id login; Aadhaar check of 12 digits, Verhoeff checksum, salted-hash registry lookup and match with the signed-in account", "Chapter 7: HTTP checks on format, checksum, unknown and foreign numbers"],
             ["2", "One-voter-one-vote through identity binding and duplicate checks",
              "Eligibility row, single-use token, unique participation row and ledger nonce check", "Chapter 7: replay and second-verify checks; unit test for duplicate vote"],
             ["3", "Immutable recording of each ballot using blockchain and cryptographic hashing",
              "AES-256-GCM ballot, Ed25519-signed transaction, SHA-256 hash-chained block approved by 2 of 3 validators", f"Chapter 8: tamper study, {F.N_TAMPER_PRODUCT} of {F.N_TAMPER} cases detected by the product check"],
             ["4", "Administration portal for elections, candidates and polling windows",
              "Admin console: create, open, pause, close elections; add and deactivate candidates", "Chapter 8: output screens"],
             ["5", "Automatic results at close with a chronological audit trail",
              "Tally from decrypted ballots after CLOSED; audit_logs table and auditor view", "Chapter 8: results and auditor screens"],
             ["6", "RBAC, input validation and TLS; evaluate integrity and performance",
              "Three roles, CSRF token, rate limits, schema validation; benchmark and timing study; TLS not configured", f"Chapter 7 and 8: {F.MATRIX_PASSED} of {F.MATRIX_TOTAL} security checks, benchmark of {F.N_VOTERS_BENCH} voters"]],
            widths=[0.4, 1.9, 2.3, 1.7], align=["c", "l", "l", "l"], size=9.5),
        P("Objective 6 is only partly met. Role-based access control, input validation and rate limiting are implemented and tested, and the integrity and performance evaluations were carried out, "
          "but Transport Layer Security is not part of the shipped configuration: the application runs over plain HTTP on the local machine."),

        H2("1.6 Scope"),
        P("The delivered scope has four parts. The identity part covers registration of synthetic voters with a salted, peppered hash of the Aadhaar number, the Verhoeff checksum, a registry lookup behind an "
          "interface (`IdentityVerificationProvider`) that a real adapter could replace, and the rule that the verified number must belong to the signed-in voter. The ballot part covers the one-time authorisation token, "
          "AES-256-GCM encryption of the choice, the Ed25519-signed transaction and the receipt. The ledger part covers a genesis block, one block per vote, three validators with a quorum of two, "
          "hash chaining, a chain validation function and an auditor tamper demonstration. The administration part covers elections with a status life cycle (draft, open, paused, closed), candidates, "
          "turnout, tallies, an audit log and a benchmark page."),
        P(f"The platform is a web application with a FastAPI backend on port {F.API_PORT}, a SQLite database of {F.N_TABLES} tables and a React interface on port {F.WEB_PORT}. "
          "Out of scope are connection to UIDAI or any biometric or one-time-password factor, a distributed network of validators, public blockchains and smart contracts, ballot "
          "anonymisation techniques such as mix-nets or homomorphic tallying, mobile applications, accessibility certification and any use in a real election."),

        H2("1.7 Contributions"),
        P("The team makes the following contributions. They are stated at the level at which they were verified."),
        N("An end-to-end prototype that joins Verhoeff-checked, hashed Aadhaar verification, single-use authorisation tokens, encrypted Ed25519-signed ballots and a hash-chained ledger with three-validator quorum, behind three role consoles.",
          "A four-layer enforcement of one voter, one vote (eligibility, unique participation row, single-use token, ledger nonce and transaction-hash uniqueness) that is checked by automated tests and by HTTP attacks.",
          f"A measurement of cost: a benchmark of {F.N_VOTERS_BENCH} synthetic voters in the same style as the base paper, component timings, a stage breakdown of one vote, the growth of integrity-check time with chain length and the end-to-end latency over HTTP.",
          f"A tamper study of {F.N_TAMPER} kinds of modification that shows which ones the product's `validate_chain` detects ({F.N_TAMPER_PRODUCT}) and which a stricter signature-aware audit would also catch ({F.N_TAMPER_STRICT}).",
          "An explicit list of the properties the prototype does not have, so that a reader can tell a demonstration from a deployable system."),

        H2("1.8 Limitations and Assumptions"),
        P("The principal limitations are stated here so that the reader meets them before the results. Each is treated in detail in Chapters 7 to 9."),
        B("The identity check uses a locally generated synthetic registry; UIDAI is not contacted and no second factor is used.",
          "The ledger is a simulation of a permissioned chain on one machine. The three validator keys are files on the same server, there are no network messages between validators, and the 'Merkle root' is a flat hash of the sorted transaction hashes.",
          "Ballot secrecy is partial: the participation table stores the voter id with the ballot id, one server-held key encrypts every ballot, and the administrator can read a live tally of an open election.",
          "The integrity check does not verify validator signatures or recompute transaction hashes, and it does not cover the ballots table from which the tally is read.",
          "TLS is not configured, the session cookie lacks the Secure flag, sessions and rate-limit counters live in memory.",
          "The 'asynchronous' benchmark batches run one after another, so no concurrency result exists; concurrent voting was not tested.",
          "All measurements were taken on one shared personal computer, so absolute times vary between runs."),
        P(f"The assumptions are that the server and its key files are controlled by the election authority, that the voters' devices and browsers are not compromised, and that the synthetic data stand in for real voters "
          f"without affecting the measured behaviour. The benchmark comparisons with the base paper are therefore indicative only. On an idle machine the earlier committed runs processed {lo_t:.0f} to {hi_t:.0f} votes per second "
          f"({lo_m:.1f} to {hi_m:.1f} ms per vote), while the 1000-voter run of this documentation, taken while other jobs used the processor, reached {s['throughput']:.1f} votes per second ({s['mean_ms']:.1f} ms per vote)."),

        H2("1.9 Organisation of the Report"),
        P("The report has ten chapters followed by references and three appendices."),
        B("Chapter 1 (this chapter) introduces the domain, motivation, problem, objectives, scope, contributions and limitations.",
          "Chapter 2 surveys the literature: the base paper in depth, related work grouped by theme, the techniques used and the research gap.",
          "Chapter 3 examines technical, economic, operational and schedule feasibility.",
          "Chapter 4 analyses the existing and proposed systems and states the functional and non-functional requirements, the hardware and software and the user roles.",
          "Chapter 5 presents the system design: architecture, workflow, data flow diagrams, UML diagrams, database, modules and user interface.",
          "Chapter 6 describes the methodology and implementation: the vote protocol, cryptographic choices, the ledger, application and API design, security and error handling, and installation.",
          "Chapter 7 reports the testing: unit, integration, functional, security, validation, performance and the limits of the testing done.",
          "Chapter 8 presents the output screens, the measured results, the comparison with the base paper and the objectives against outcomes.",
          "Chapter 9 concludes, and Chapter 10 gives the future scope.",
          "The references follow in IEEE style; Appendix A lists important code, Appendix B the installation and user guide and Appendix C additional screens."),
        P(f"Within the report, measured values are quoted from the experiment files of the project (`experiments/voting/metrics.json`, the benchmark file and the pytest record). As an example, a "
          f"complete voter journey over HTTP, from login to receipt, averaged {e2e:.0f} ms in the final run. Where a value was not measured, the report says so."),
    ]
