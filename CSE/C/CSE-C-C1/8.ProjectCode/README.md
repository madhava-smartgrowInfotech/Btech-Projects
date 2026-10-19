# AegisBallot — Secure Local Electronic Voting Platform

**AegisBallot** is a polished local web application demonstrating a complete secure electronic voting workflow: voter registration, synthetic Aadhaar verification, one-time authorization, encrypted ballots, blockchain-backed ledger with quorum validation, one-vote enforcement, result tallying, and independent auditability.

> This is a functional local demonstration. It is not a production national-election system, does not contact UIDAI, and does not use public blockchain infrastructure.

## Key Features
- **Election management:** Admin creates elections, adds/edits candidates, opens/pauses/closes elections, views turnout and results.
- **Synthetic identity:** Demo Aadhaar provider validates 12-digit format, Verhoeff checksum, and registry membership; stores salted hash, shows masked value.
- **One-time authorization:** Random single-use token (hashed at rest, 10-minute expiry) separates identity from ballot.
- **Encrypted ballots:** AES-256-GCM per-election key, never exposed to voters, never in source control.
- **Local permissioned ledger:** SHA-256 chained blocks, Merkle root, 3 validators, 2/3 quorum, Ed25519 signatures, previous-hash linking, immutable append.
- **One-vote enforcement:** DB unique constraint + auth token + app check + ledger nonce uniqueness.
- **Auditor view:** Chain explorer, block details, chain-integrity verification (recomputes hashes), tamper demo (cloned ledger), audit log viewer.
- **Performance:** Real benchmark (1,000 voters default, batch sizes 10/20/30) with mean/median/p95/throughput measured via `time.perf_counter()`.

## Architecture
```
app/
  main.py          FastAPI + Jinja2 + static
  config.py        Secrets, election key, DB URL
  database.py      SQLAlchemy + SQLite
  models/          Users, elections, candidates, ledger, ballots, audit
  security/        Argon2, AES-GCM, sessions, rate-limit, CSRF
  identity/        Verhoeff + DemoAadhaarProvider adapter
  ledger/          Block creation, quorum, chain validation, tamper demo
  services/        Election & voting logic, audit logging
  benchmarks/      Synthetic population + sync/async timing
  templates/       Light theme, responsive, status badges
  static/css/      Commercial-style UI
```

## Security Model
- **Authentication:** Argon2id, server-side sessions, secure cookies, RBAC (ADMIN/VOTER/AUDITOR), server-side authorization.
- **Aadhaar handling:** Hashed with pepper (`SECRET_KEY`) + salt; masked display; Verhoeff validation; no raw storage beyond demo lookup.
- **Ballot privacy:** Identity DB → one-time token → anonymous ballot ID → encrypted choice → ledger transaction (ballot_id, election_id, encrypted_payload, nonce, timestamp, signature).
- **Ledger:** SHA-256, deterministic serialization, validator signatures, quorum 2/3, tamper detection, replay prevention via nonce/tx_hash uniqueness.

## Local Blockchain Design
- Genesis block + sequential blocks (index, timestamp, previous_hash, merkle_root, block_hash, validator_signatures, tx list).
- Three validators with Ed25519 keypairs stored in `data/validators.json`.
- Application creates transaction → primary proposes block → replicas validate schema, previous hash, signature, uniqueness → 2/3 approvals → commit → replicas sync.
- Described accurately as *local permissioned ledger simulation* (not Ethereum/Hyperledger/mainnet).

## Identity-Verification Design
- Interface `IdentityVerificationProvider` + `DemoAadhaarProvider`.
- Checks: 12-digit, Verhoeff, exists in `voter_profiles`, eligible, not already voted.
- Clearly labeled “Demo verification environment” in UI and code.

## Privacy Model
Strict separation of identity/eligibility, authorization token, anonymous ballot, ledger transaction, and tally. Voter receipt contains ballot ID, tx hash, block number, timestamp — never the candidate choice on the audit page.

## Benchmark Methodology
`python -m app.benchmarks.run_benchmark --voters 1000`
- Generates synthetic voters (Argon2-hashed passwords, Verhoeff Aadhaar).
- Measures voter registration, synchronous vote submission, batched/async submission (batches 10/20/30).
- Reports total ops, successes/fails, total duration, mean/median/p95/min/max/stdev latency, throughput.
- Saves JSON to `benchmark_results/` and displays latest on admin dashboard.

## Testing
- `pytest` suite covering: Aadhaar format, checksum, unknown/ineligible voters, duplicate vote, RBAC, tampered block, previous-hash, duplicate transaction, malformed input, expired token, identity separation, password hashing, audit logging, election status.
- Run: `pip install -r requirements-dev.txt && python -m pytest -v`

## Run Instructions
See **HOW_TO_RUN.md** for Prerequisites, Method A (double-click `run.bat`), Method B (Docker), Method C (manual), and Troubleshooting. Server binds to **127.0.0.1:8000**, browser at **http://localhost:8000**.

## Limitations & Extension Points
- Local demo: single SQLite DB, in-memory sessions, local validator keys. No real decentralization across Internet nodes.
- No live UIDAI, no public chain, no cryptocurrency.
- Extension: replace `DemoAadhaarProvider` with a real identity adapter; swap ledger layer for a real permissioned chain; add email/SMS notifications; add external audit exports.

## Product Identity
Consistently branded **AegisBallot** throughout UI, docs, package metadata, and configuration. No academic-project wording.
