"""Literature and framing data for the decks (Review 1, Review 2 and the final deck) and the report.

Every literature fact traces to a PDF or web page read in the documentation run (see refs.REF_NOTES); reference numbers match scripts/docs/refs.py.
"""

from .refs import CITE as R

BASE_PAPER_TITLE = "Blockchain-enhanced electoral integrity: a robust model for secure digital voting systems in Oman"
BASE_PAPER_VENUE = "A. Shaikh, N. Adhikari, A. Nazir, A. S. Shah, S. Baig, H. Al Shihi - F1000Research 14:223 (2025)"

# [work, year, approach, finding / limitation]   (each cell <= 90 characters)
LIT_TABLE = [
    [f"Shaikh et al. [{R['base']}] (base paper)", "2025", "Ethereum (Geth test chain) smart contracts; biometric voter authentication; C# clients",
     "1000 synthetic voters; ~2 s / ~3-4 s per registration / vote tx (read from figures)"],
    [f"Chouhan & Sharma [{R['newera']}]", "2025", "Aadhaar / licence hashed with BLAKE2b-512, fingerprint and picture-rotation factors, hash chain",
     "Concept and demo blocks; no throughput or tamper evaluation"],
    [f"Ray, Ojha & Rhmann [{R['ray']}]", "2024", "Study of a blockchain-powered electronic voting system",
     "Abstract only available; no numbers used here"],
    [f"Krishan, Raj & Raj [{R['krishan']}]", "2026", "Permissioned ledger, smart contracts, hashing for anonymity, real-time tally",
     "Short preprint; scalability acknowledged as open, claims unverified"],
    [f"Aswini [{R['aswini']}]", "2025", "Review of trust and security challenges; hybrid ZKP / homomorphic / sharding designs",
     "Review, no implementation; lists malware, insiders, verifiability as limits"],
    [f"Bramasto et al. [{R['vexanium']}]", "2024", "DApp on the Vexanium blockchain (PHP 8.2, Apache, PostgreSQL)",
     "Black-box tests passed; only smart contracts, no Ricardian contract or hardening"],
    [f"Jafar et al. [{R['jafar']}]", "2021", "Systematic review of blockchain e-voting proposals",
     "Privacy protection and transaction speed are the most reported issues"],
    [f"Springall et al. [{R['estonia']}]", "2014", "Security analysis of Estonia's internet voting in real use",
     "Found real attack paths against a deployed system with national ID"],
]

OBJECTIVES = [
    "Voter registration and authentication with Aadhaar-based identity verification",
    "One voter, one vote: identity binding plus duplicate checks",
    "Record every ballot immutably with blockchain and cryptographic hashing",
    "Admin portal for elections, candidates and polling windows",
    "Results on close with a complete chronological audit trail",
    "RBAC, input validation, TLS; evaluate integrity and performance",
]

PROBLEM_STATEMENT = [
    "Manual voting is slow, needs heavy infrastructure and delays results",
    "Conventional digital voting keeps ballots in a database an administrator could alter",
    "Without identity binding, duplicate or ineligible voting cannot be prevented reliably",
    "Voters and observers cannot independently verify that results were not manipulated",
    "Need: verify identity, record each ballot immutably, produce an auditable result",
]

GAPS = [
    "Surveyed work establishes blockchain models for electoral integrity",
    "Base paper authenticates by biometrics on a test chain; no national-ID check, no admin workflow",
    "Aadhaar-based proposals show concepts but report no performance or tamper tests",
    "Few student-deployable systems join identity, ledger, admin and audit in one app",
    "Ledger checks are rarely tested against edits to the tally source or forged signatures",
    "Ethereum's ~119 tx/s (as quoted by the base paper) limits national-scale use",
]

EXISTING_SYSTEM = [
    "Paper ballots or electronic machines with manual verification and counting",
    "Central-database e-voting: one administrator controls ballots and results",
    "Public-chain prototypes: strong integrity but slow, costly, hard to link to identity",
    "Identity checks by password or OTP alone, with no one-voter-one-vote binding",
    "Audit by trusting the operator rather than recomputing the record",
]

LIMITATIONS_EXISTING = [
    "Queues, human error and slow counting in manual polling",
    "A database ballot box can be edited without trace",
    "Duplicate or ineligible votes are hard to exclude without identity binding",
    "Public chains cost time and fees per transaction (base paper: seconds per tx)",
    "Observers cannot recompute the result themselves",
]

PROPOSED_APPROACH = [
    "Verify Aadhaar locally: 12 digits, Verhoeff checksum, salted-hash registry lookup",
    "Issue a one-time token (hashed, 10 min) that separates identity from the ballot",
    "Encrypt the choice with AES-256-GCM; sign the transaction with Ed25519",
    "Commit each ballot to a hash-chained ledger approved by 2 of 3 validators",
    "Give admin, voter and auditor roles with CSRF, rate limiting and an audit log",
]

EXPECTED_OUTCOMES = [
    "A working web app from login to receipt, results and auditor view",
    "Four independent layers that block a second vote",
    "A ledger whose edits an auditor can detect and locate",
    "Measured latency, throughput and tamper-detection results, gaps stated",
    "A local demonstration, not a national-election system",
]

BASE_PAPER_POINTS = [
    "Four-tier model: MySQL + Ethereum nodes + C# web tier + client devices",
    "Smart contracts register voters and candidates, cast and count votes",
    "Biometric authentication blocks duplicate votes (simulation)",
    "1000 synthetic voters; synchronous vs asynchronous batches of 10, 20, 30, 50",
    "Conclusion: blockchain improves integrity; pilots and public-trust studies needed",
    "Limits: Layer-1 throughput, synthetic data, no real-world pilot",
]

SUPPORT_EVIDENCE = [
    f"Estonia's internet voting was analysed in real use and attack paths were found [{R['estonia']}]",
    f"Voatz, a blockchain-marketed voting app used in U.S. federal elections, had exploitable weaknesses [{R['voatz']}]",
    f"Reviews name privacy protection and transaction speed as the most common blockchain-voting issues [{R['jafar']}]",
    f"Base paper quotes Ethereum at about 119.1 tx/s against 65,000 tx/s for Solana [{R['base']}]",
    f"Aadhaar-hash voter identity has been proposed before, without performance data [{R['newera']}]",
]
