"""Index of the AegisBallot design diagrams: (key, title, file, caption, explanatory paragraph).

The files are written by scripts/docs_build/make_diagrams.py into docs/diagrams/ and mirror the code in app/ (api_v1.py, main.py,
services/, ledger/, identity/, security/, models/). Used by the block-diagram document and the full report.
"""

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "Four-tier architecture of AegisBallot: React single-page app, FastAPI application, service layer with the local ledger, SQLite storage.",
     "The browser tier is a React 18 and Vite single-page application on port 5401. It has public pages (landing, login, results of closed elections) and three role consoles for the administrator, "
     "the voter and the auditor, guarded by React Router. Every call goes through an Axios client that adds the CSRF token header, and TanStack Query caches the answers. The Vite server proxies /api to the backend.\n"
     "The application tier is FastAPI on port 8401. app/api_v1.py holds the JSON routes used by the React app (authentication, admin, voter and auditor groups); app/main.py keeps the original Jinja pages. "
     "Behind it the service tier holds the identity provider, the voting service, the cryptographic helpers, the audit log and the ledger module with its three validators. "
     "All persistent state is in one SQLite database of 13 tables plus three key files in data/. Nothing is sent to an external service."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "Election life cycle and the path of one vote, from election creation to the auditor's check.",
     "The administrator creates an election with its window and candidates and opens it; every registered voter becomes eligible. A voter signs in, enters an Aadhaar number, and after the checks (format, Verhoeff checksum, "
     "registry lookup, the number must belong to the signed-in account) receives a one-time token that expires in ten minutes. Choosing a candidate encrypts the choice with AES-256-GCM, signs the transaction and "
     "proposes a block to the three validators; two approvals commit it and the voter receives a receipt. When the administrator closes the election the tally is published, and the auditor can recompute the chain at any time. "
     "A failure at any step is answered with HTTP 400 or 403 and an entry in the audit log."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Context diagram (DFD level 0) of AegisBallot with its three user roles and two stores.",
     "At level 0 the platform is one process. The voter sends credentials, an Aadhaar number and a candidate choice and receives a receipt and, later, the results. The administrator sends election, candidate and status changes "
     "and receives turnout and tallies. The auditor sends integrity-check and tamper-test requests and receives the chain status, blocks and the audit log. "
     "The process reads the voter registry (a local table of hashed synthetic Aadhaar numbers) and writes blocks, ballots and log entries. No external agency is contacted."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "DFD level 1: eight processes and six data stores.",
     "Level 1 splits the platform into authentication (1.0), identity verification (2.0), token issue (3.0), casting and encryption (4.0), block proposal and commit (5.0), election management (6.0), "
     "audit and chain verification (7.0) and tally and publication (8.0). Process 2.0 consults the user and registry store D1; 3.0 writes the token store D2; 4.0 writes ballots and participation (D3) and hands a signed transaction "
     "to 5.0, which writes the ledger D4. Process 6.0 maintains the elections store D6, 7.0 reads the ledger and 8.0 reads the ballots. Every process appends to the audit log."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "DFD level 2: processes 4.0 and 5.0 expanded into eleven sub-processes (cast_vote and propose_block).",
     "Process 4.0 checks the election and candidate (4.1), the token (4.2: hash match, unused, not expired) and the absence of a prior participation row (4.3), encrypts the choice (4.4), hashes and signs the transaction (4.5) "
     "and, after the ledger commits, saves the ballot and marks the token used (4.6). Process 5.0 checks the schema and the uniqueness of nonce and transaction hash (5.1), has each validator check and sign the block (5.2), tests the "
     "quorum of two out of three (5.3) and commits the block with its transactions (5.4). A rejection at any point returns HTTP 400 and stores nothing."),
    ("uml", "UML class diagram", "06_uml_class.png",
     "Class diagram of the persistent models with the service modules and the identity-provider interface.",
     "The twelve classes are the SQLAlchemy models. User owns an optional VoterProfile that holds the salted hash and the masked form of the Aadhaar number. Election has Candidates. VoterEligibility, VotingAuthorization and "
     "VoterParticipation each carry a unique constraint on (election, voter), which is how the database itself refuses a second vote. Ballot has no voter column; only VoterParticipation relates a voter to a ballot id. "
     "LedgerBlock, LedgerTransaction and ValidatorNode model the chain, and AuditLog records actions. VotingService and Ledger are modules of functions drawn as classes; IdentityVerificationProvider is an abstract interface "
     "implemented by DemoAadhaarProvider so that a real adapter could replace it."),
    ("seq", "Sequence diagram", "07_sequence_vote.png",
     "Sequence of Aadhaar verification and casting one ballot through the JSON API.",
     "The browser posts the Aadhaar number to the verify route with its session cookie and CSRF header. The route calls the identity provider, which checks the digits and the Verhoeff checksum and looks the salted hash up in the registry; "
     "the voting service then checks that the number belongs to the signed-in voter, that the voter is eligible and has not voted, stores only the SHA-256 of a fresh token and returns the token and the candidate list. "
     "The cast call encrypts the choice, hashes and signs the transaction, asks the ledger for a block, saves the ballot, token and participation rows in one commit, writes the audit entry and returns the receipt."),
    ("uc", "Use-case diagram", "08_use_case.png",
     "Use cases of the voter, the administrator and the auditor.",
     "The voter signs in, verifies identity, casts one encrypted ballot and reviews the receipt and election history. The administrator creates and configures elections, adds or deactivates candidates, opens, pauses and closes "
     "elections and reads results and benchmarks. The auditor verifies chain integrity, browses blocks, runs the tamper demonstration and reads the audit log. Casting a ballot includes identity verification. "
     "Results of a closed election are readable by every signed-in role."),
    ("er", "Entity-relationship diagram", "09_er_diagram.png",
     "Entity-relationship diagram of the thirteen tables.",
     "Users have at most one voter profile. Elections have candidates; eligibility, authorisation and participation rows tie users to elections and are unique per pair. Ballots are keyed by an anonymous ballot id and "
     "carry the ciphertext, nonce, transaction hash and block index, but not the voter. Ledger transactions belong to ledger blocks by block index and repeat the ballot id, which is the logical link between the two stores. "
     "Validator nodes hold the three public keys, audit logs record who did what, and benchmark runs store the measured performance."),
    ("flow_cast", "Flowchart of the core algorithm", "10_flowchart_cast_vote.png",
     "Flowchart of casting a ballot: checks, encryption, signing, quorum and commit.",
     "The core algorithm is cast_vote followed by propose_block. Three checks guard the encryption step: the election must be OPEN and the candidate active, the token must match, be unused and unexpired, and the voter must have "
     "no participation row. The choice is then encrypted, the transaction hashed and signed, and each validator re-checks the block (schema, new nonce, new transaction hash, signature). If at least two of three approve, "
     "the block, ballot, used token and participation row are committed and a receipt is produced; otherwise a ValueError ends the flow and the token stays unused."),
    ("flow_audit", "Flowchart of the audit algorithm", "11_flowchart_validate_chain.png",
     "Flowchart of validate_chain, the function behind the auditor's integrity check.",
     "For every block the function recomputes the flat Merkle root from the stored transaction hashes, recomputes the block hash from the index, timestamp, previous hash, root and transaction hashes, and compares the stored previous "
     "hash with the hash of the block before. The first failure is returned with the field and the block index. The chart also lists what the function does not check - validator signatures, transaction hashes against their fields, "
     "the ballots table against the ledger, and dropped tip blocks - which is the subject of the tamper study in the results chapter."),
    ("ledger", "Ledger structure", "12_ledger_structure.png",
     "Structure of the ledger: blocks linked by previous_hash, each holding one signed transaction.",
     "Block 0 is the genesis block with no transactions and a previous hash of sixty-four zeros. Every later block holds the index, timestamp, previous hash, Merkle root, block hash and the signatures of the approving validators, and "
     "one transaction with its hash, ballot id, encrypted payload, nonce, timestamp and signature. The block hash covers the previous hash, so changing any block changes every hash after it; the commit rule is two approvals out of three."),
]
