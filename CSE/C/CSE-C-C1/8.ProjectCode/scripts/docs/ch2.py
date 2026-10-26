"""Chapter 2: Literature Survey."""

from . import facts as F
from . import lit
from .blocks import B, H1, H2, H3, P, TAB
from .refs import CITE as R


def blocks():
    base, newera, dao = R["base"], R["newera"], R["dao"]
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        P("This chapter reviews the work on which AegisBallot builds. It first gives an overview of the survey, then analyses the base paper in depth, groups the related work by theme, "
          "summarises the datasets and algorithms that the literature and the project use, weighs strengths against limitations and closes with the research gap. Every statement about a "
          "paper is limited to what the team read: the three papers kept in the batch folder were read in full, the other items were confirmed online and are used only for what their abstracts state."),

        H2("2.1 Overview"),
        P(f"The batch literature survey lists five papers: the base paper [{base}], a study of an electronic voting system powered by blockchain [{R['ray']}], a decentralised-trust framework "
          f"[{R['krishan']}], a review of trust and security challenges [{R['aswini']}] and a decentralised application on the Vexanium blockchain [{R['vexanium']}]. The team added two "
          f"papers that were already in the batch folder, an Aadhaar-based proposal [{newera}] and a study of voting between decentralised autonomous organisations [{dao}], and further reviews and analyses "
          f"of deployed systems [{R['jafar']}], [{R['ohize']}], [{R['estonia']}], [{R['helios']}], [{R['voatz']}]."),
        P("Taken together, the work falls into four groups: proposals that bind a voter's identity to a blockchain ballot, frameworks and applications that demonstrate a design, reviews that "
          "collect the open problems, and security analyses of systems that were actually used in elections. The literature agrees on the promise of blockchain voting, which is a record that "
          "cannot be altered silently, and on its difficulties, which are privacy, speed, identity and trust in the operator. It rarely reports a test of the integrity check itself."),

        H2("2.2 Base Paper Analysis"),
        P(f"The base paper is \"{lit.BASE_PAPER_TITLE}\" by Shaikh, Adhikari, Nazir, Shah, Baig and Al Shihi, published in F1000Research in 2025 (article 223, version 3 of September 2025) [{base}]. "
          "The journal publishes openly refereed articles; the third version carries a peer-review status of two reviewers approving, one approving with reservations and one not approving. The version "
          "analysed here is the revised one that added a discussion of Ethereum scalability and of Layer-2 rollups."),
        H3("2.2.1 Problem and approach"),
        P("The paper studies Oman's electronic voting, which was used in the 2019 Majlis Al-Shura elections, and argues that blockchain can strengthen integrity, transparency and trust. It proposes a "
          "simplified model, prototypes it and measures how long registration and voting transactions take. The research design is quantitative and experimental: open-source software is run with synthetic "
          "population data that contain national identity numbers and basic demographic fields."),
        H3("2.2.2 Architecture"),
        P("The model has four tiers. Tier 1 stores data in MySQL and on the blockchain ledger. Tier 2 is the Ethereum network on which smart contracts register voters, officers and candidates, record a vote cast "
          "by a registered voter and answer queries about registration and vote counts. Tier 3 is a web application written in C# that lets administrators register campaign officers, voters and candidates and "
          "deploy the contracts. Tier 4 consists of client devices and crypto wallets; in the experiments, .NET Core 7 programs simulate them. The actors are election administrators, voters, auditors, "
          "Ethereum nodes and smart-contract developers. The pseudocode of the contract (its Algorithm 1) keeps maps of owner, voters and candidates and offers procedures for candidate registration, voter registration, "
          "casting a vote and counting."),
        H3("2.2.3 Experiment"),
        P("The experiment ran on a Geth test chain accessed through the Nethereum library on a machine with an Intel Core i7-12700 processor, 16 GB of memory and Windows 10 Enterprise. Communication used HTTP "
          "for simplicity. One thousand synthetic voters, each with a synthetic social security number, name, address, phone number and e-mail address, were loaded into SQL Server, and a client produced "
          "one thousand registration and one thousand voting transactions. Each was run synchronously, one after another, and asynchronously in batches of 10, 20, 30 and 50 transactions."),
        H3("2.2.4 Reported results"),
        P("The paper presents its timings only as charts. Reading Figure 6 by eye, a synchronous registration transaction takes roughly 2,000 ms and a voting transaction roughly 4,000 ms; Figure 9, the average per "
          "transaction in asynchronous batches of ten, shows about 2,000 ms for registration and about 3,000 ms for voting. These are approximations made by the team, not figures quoted in the text, and they are "
          "used in this report only as an order of magnitude. The text states qualitatively that the model processed the simulated load with minimal delay, that recorded votes could not be altered by outside "
          "parties and that biometric authentication blocked duplicate votes; the biometric step is part of the narrative and the simulation, but it is not specified in the contract pseudocode."),
        P("The discussion also quotes a theoretical Ethereum throughput of 119.1 transactions per second against 65,000 for Solana, 2,516 for Tron, 1,137 for Stellar, 2,222 for BNB Chain and 714.1 for Polygon, "
          "and reviews Layer-2 rollups and zero-knowledge proofs as remedies. Threats such as Sybil attacks, 51 percent attacks, smart-contract vulnerabilities and denial of service are discussed with "
          "mitigations (staking, practical Byzantine fault tolerance among approved validators, auditing, rate limiting), but none of them is tested."),
        H3("2.2.5 Strengths and limitations of the base paper"),
        B("Strength: a complete tiered design with an administrator, voter and auditor view, and a performance experiment of the same size (1,000 voters) that AegisBallot repeats.",
          "Strength: it states its own boundary clearly in the revised version, separating what the experiment supports from speculation about public trust and network readiness.",
          "Limitation: all data are synthetic and the system is a simulation; the authors themselves call for a pilot with real data and adversarial stress tests.",
          "Limitation: the identity layer is described through biometrics and the Omani national identity card, so it does not address Aadhaar, and no identity-verification step is measured.",
          "Limitation: security is argued, not measured; no test shows what happens when a stored record is altered.",
          "Limitation: Layer-1 Ethereum throughput and cost limit national-scale use, as the paper concedes. A reviewer of the paper also noted that the algorithms lack a complexity analysis such as gas cost and that the synthetic data lack real-world validation."),
        H3("2.2.6 What AegisBallot takes from the base paper"),
        P("AegisBallot keeps the actor model (administrator, voter, auditor), the separation of a web tier from a ledger tier, the use of synthetic voters and the performance experiment with one thousand voters, "
          "batch sizes of 10, 20 and 30 and synchronous and batched modes. It replaces Ethereum and C# with a local permissioned ledger written in Python, replaces biometric authentication with a "
          "Verhoeff-checked Aadhaar number and a one-time token, and adds what the paper leaves untested: a tamper study, an HTTP security matrix and the cost of the identity step."),

        H2("2.3 Related Work"),
        H3("2.3.1 Identity-bound blockchain voting"),
        P(f"Chouhan and Sharma [{newera}] propose a blockchain voting system with layered identity verification. The voter's Aadhaar card or driving licence is hashed with BLAKE2b-512, a fingerprint "
          "is reduced to minutiae and hashed with SHA-256, and a picture-rotation pattern is hashed in the same way; the three hashes are concatenated and hashed again into a unified identity, and the vote record is "
          "the SHA-256 hash of that identity joined with the choice. The record is stored on an election-specific chain. The paper presents a Visual Studio and SQL Server implementation and example blocks, and its hash "
          "analysis reports an avalanche effect well below the desired 50 percent. It is the closest published idea to AegisBallot, because it uses Aadhaar in a voting chain, but it reports no throughput, "
          "no latency and no tamper test."),
        P(f"The base paper [{base}] authenticates by biometrics against the Omani national identity infrastructure; together with the paper above, it shows that binding a ballot to a national identity "
          "is a recurring design goal and that the strength of the binding is rarely evaluated."),
        H3("2.3.2 Frameworks and applications"),
        P(f"Krishan, Raj and Raj [{R['krishan']}] describe, in a short preprint, a design that runs self-executing smart contracts on a permissioned distributed ledger, uses cryptographic hashing "
          "to keep voters anonymous while allowing public verification of the tally, and claims better resistance to denial-of-service attacks and unauthorised changes than legacy systems; they acknowledge "
          "scalability as an open problem and suggest an optimised consensus mechanism. The team read the abstract only, so the claims are the authors' own. "
          f"Bramasto, Savitri and Djuwitaningrum [{R['vexanium']}] build an e-voting decentralised application on the Vexanium blockchain with PHP 8.2, Apache and PostgreSQL and report that it passed black-box testing; "
          "they note that only smart contracts were created, not the default Ricardian contracts, and list blockchain-level hardening (reentrancy protection, a better source of randomness for nonces, protection against "
          f"front-running) as future work. Hjalmarsson et al. [{R['hjalmarsson']}] propose a blockchain-based voting system on a permissioned blockchain. Ray, Ojha and Rhmann [{R['ray']}] study a blockchain-powered "
          "electronic voting system; only the abstract's framing of election integrity as central to public confidence was available to the team."),
        P(f"The paper on DAO-to-DAO voting [{dao}] belongs to a different setting: it identifies, on Ethereum, how decentralised organisations vote in each other's decisions (metagovernance) and builds a network "
          "of 61 organisations with 72 relationships. It is relevant to this project only as a reminder that transparent on-chain voting can still hide who effectively decides."),
        H3("2.3.3 Reviews and surveys"),
        P(f"Jafar, Ab Aziz and Shukur [{R['jafar']}] review blockchain voting in the journal Sensors and find that privacy protection and transaction speed are the issues raised most often and that proposals "
          f"need improvement before they suit elections. Ohize et al. [{R['ohize']}] survey architectures, trends and solutions and name cybersecurity risk, resource intensity and infrastructure as the main obstacles to scalability "
          f"and reliability. Aswini [{R['aswini']}] reviews trust and security challenges; the abstract lists malware, server compromise, insider threats and limited verifiability as the main vulnerabilities, "
          "suggests hybrid designs that combine zero-knowledge proofs, homomorphic encryption and sharding, and argues that legitimacy also needs institutional frameworks, accessibility measures and regular technical audits. "
          f"Kshetri and Voas [{R['kshetri']}] discuss the promise and the challenges of blockchain-enabled voting for practitioners."),
        H3("2.3.4 Deployed systems and security analyses"),
        P(f"Springall et al. [{R['estonia']}] analysed Estonia's internet voting system, the best-known national deployment based on a national identity card, and found concrete attack paths. Adida [{R['helios']}] "
          f"introduced Helios, a web-based voting system in which anyone can audit the election, a goal shared by the auditor role of AegisBallot. Specter, Koppel and Weitzner [{R['voatz']}] analysed Voatz, a mobile "
          "voting application used in United States federal elections, and showed that its weaknesses lay in the application and its servers, not in the blockchain it advertised. These analyses are the reason the "
          "project tests the surrounding application (authentication, authorisation, replay, rate limiting) and not only the ledger."),
        H3("2.3.5 Foundations"),
        P(f"The ledger uses ideas from several foundational works: hash-chained blocks [{R['bitcoin']}], Merkle's use of hash trees [{R['merkle']}], permissioned blockchains [{R['fabric']}], Byzantine fault-tolerant "
          f"agreement among known replicas [{R['pbft']}] and, for ballot secrecy, Chaum's work on untraceable communication [{R['chaum']}], which also shows what a mix network would add beyond this prototype."),
        TAB("Comparison of the surveyed work",
            ["Work", "Year", "Approach", "Result / limitation"],
            lit.LIT_TABLE, widths=[1.55, 0.45, 2.3, 2.0], align=["l", "c", "l", "l"], size=9),

        H2("2.4 Datasets and Algorithms Used"),
        P("None of the surveyed voting systems uses a public dataset in the machine-learning sense. The experiments are run with synthetic populations: the base paper loads one thousand synthetic voters with fictitious "
          f"social security numbers [{base}], the Aadhaar proposal uses sample identity data in its demonstration [{newera}], and AegisBallot generates synthetic voters with Verhoeff-valid Aadhaar numbers. This is "
          "appropriate for a prototype, because real identity data must not be used, but it means that no result says anything about real voters."),
        TAB("Algorithms and mechanisms used in the literature and in AegisBallot",
            ["Purpose", "Literature", "AegisBallot"],
            [["Identity number check", "Hash of identity card or number (BLAKE2b-512); biometric hash", f"12 digits and Verhoeff checksum [{R['verhoeff']}], salted-peppered SHA-256 lookup, masked display"],
             ["Password protection", "Not described in the surveyed abstracts", f"Argon2id [{R['argon2']}], [{R['argon2rfc']}]"],
             ["Ballot confidentiality", "Hashing of identity with choice; encryption not detailed", f"AES-256-GCM [{R['gcm']}] with a random 96-bit nonce"],
             ["Transaction authenticity", "Wallet signatures on Ethereum", f"Ed25519 signature [{R['eddsa']}] by a system key"],
             ["Chain integrity", "Hash-linked blocks on Ethereum or a permissioned ledger", f"SHA-256 [{R['sha2']}] block hash over the previous hash; flat hash of sorted transaction hashes as Merkle root"],
             ["Agreement", "Ethereum consensus; PBFT among approved validators is discussed", f"Two-of-three approval by three validators that each sign the block hash (simulated on one server)"],
             ["Web security", "HTTP in the experiments; threats discussed", f"Server-side sessions, CSRF header, role checks, rate limits, audit log (topics that web-security guidance such as [{R['asvs']}] lists)"]],
            widths=[1.3, 2.4, 2.6], align=["l", "l", "l"], size=9.5),

        P(f"A word on consensus is needed because the surveyed systems differ most there. A public chain such as Ethereum lets anonymous participants agree on the next block, which gives strong resistance to a "
          f"single dishonest operator but limits speed and adds fees; the base paper quotes 119.1 transactions per second for it and proposes Layer-2 rollups and zero-knowledge proofs as remedies [{base}]. "
          f"A permissioned chain restricts block production to approved validators, which is faster and easier to govern but moves the trust to whoever selects the validators; practical Byzantine fault tolerance "
          f"[{R['pbft']}] is the classical protocol for agreement among such known replicas and tolerates a minority of faulty ones. AegisBallot sits at the simple end of this range: three validators and a quorum of "
          f"two, in the manner of a Byzantine quorum, but all three run inside one process, so the project demonstrates the commit rule and not the fault tolerance."),
        P(f"The surveyed work also says little about how the voter's identity and the voter's choice are kept apart. The base paper relies on wallets and on the anonymity of addresses [{base}]; the Aadhaar "
          f"proposal hashes the identity together with the choice [{newera}]; the review of trust challenges names zero-knowledge proofs and homomorphic encryption as ways to keep both secrecy and verifiability "
          f"[{R['aswini']}]. None of these is implemented in AegisBallot, which separates identity from ballot only through a one-time token and a ballot table without a voter column, and which "
          "therefore falls short of the strongest forms of secrecy, as Chapter 9 states."),

        H2("2.5 Strengths and Limitations of the Existing Work"),
        P("The strengths of the literature are a convincing case that an append-only, hash-linked record makes silent alteration detectable, a growing set of working prototypes, and, in the security analyses, "
          "a realistic view of how deployed systems fail. The limitations are consistent across the group:"),
        B("Evaluation is mostly qualitative or limited to the time of a transaction; tests that alter stored data and ask whether the system notices are almost absent.",
          "Prototypes use synthetic data and simulated networks, and several use HTTP without transport protection.",
          "Identity is handled through biometrics, wallets or hashes of cards; combination with an Indian national identity check and an administrator workflow is rare.",
          "Public-chain designs inherit the speed and cost of the chain (the base paper quotes 119.1 transactions per second for Ethereum), and permissioned designs are rarely reported with measurements.",
          "Ballot secrecy and verifiability pull in different directions; most prototypes state a goal without showing where the identity-to-ballot link is stored."),

        H2("2.6 Research Gap"),
        P("The batch survey states the gap as: the surveyed work establishes blockchain models for electoral integrity, but it does not combine such a ledger with national identity verification and a full "
          "election administration workflow in one deployable system. The team refines this into five points that the project addresses:"),
        TAB("Research gap and the response in AegisBallot",
            ["Gap in the literature", "Response in this project"],
            [["Ledger models without a national-identity step", "Verhoeff-checked Aadhaar number, salted hash, match with the logged-in voter, single-use token"],
             ["Administration workflow only simulated", "Admin console with election life cycle, candidates, turnout, results and benchmarks"],
             ["Performance reported per transaction on a test chain", f"Per-vote cost of the whole platform, {F.N_VOTERS_BENCH}-voter benchmark, stage breakdown and HTTP latency"],
             ["Integrity claimed but not tested", f"Tamper study of {F.N_TAMPER} modifications; result: {F.N_TAMPER_PRODUCT} detected by the product check, {F.N_TAMPER_STRICT} by a stricter audit"],
             ["Limits of the prototype seldom stated", "Explicit list of what is simulated: validators, registry, secrecy, TLS, concurrency"]],
            widths=[3.1, 3.2], align=["l", "l"], size=10),
        P("The remaining chapters show how far the prototype closes each gap and where it does not."),
    ]
