"""Measurement harness used for the project documentation (CSE-C-C1, AegisBallot).

Runs entirely against SCRATCH databases (never data/aegisballot.db):
  A. component micro-timings (hash, AES-GCM, Ed25519, Argon2id, Verhoeff)
  B. ledger growth: per-vote cost and validate_chain() time against chain height
  C. tamper study: which kinds of tampering validate_chain() detects, and which a stricter
     signature + cross-table audit (implemented here, NOT in the product) would also detect
  D. HTTP end-to-end latency through uvicorn on 127.0.0.1 and a security/functional matrix

    .venv\\Scripts\\python.exe scripts\\run_experiments.py <scratch-dir> [--skip-http]

Writes experiments/voting/metrics.json.
"""
import json
import os
import pathlib
import platform
import shutil
import statistics
import subprocess
import sys
import time
import http.client
import urllib.parse
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORK = pathlib.Path(sys.argv[1]).resolve()
SKIP_HTTP = "--skip-http" in sys.argv
WORK.mkdir(parents=True, exist_ok=True)
EXP_DB = WORK / "exp.db"
HTTP_DB = WORK / "exp_http.db"
for p in (EXP_DB, HTTP_DB):
    if p.exists():
        p.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{EXP_DB.as_posix()}"
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from app.database import SessionLocal, init_db, engine  # noqa: E402
from app.models.models import (  # noqa: E402
    User, VoterProfile, Election, Candidate, VoterEligibility, LedgerBlock, LedgerTransaction,
    Ballot, ValidatorNode, VoterParticipation,
)
from app.security.auth import hash_password  # noqa: E402
from app.security.crypto import (  # noqa: E402
    hash_aadhaar, mask_aadhaar, encrypt_ballot, decrypt_ballot, sha256_hex, canonical_serialize,
    generate_ed25519_keypair, sign_message, verify_signature,
)
from app.identity.verhoeff import generate_valid_aadhaar, validate_verhoeff  # noqa: E402
from app.ledger.ledger import (  # noqa: E402
    init_validators, create_genesis_block, validate_chain, compute_merkle_root, compute_block_hash,
)
from app.services.voting_service import issue_authorization, cast_vote, tally_results, get_system_keypair  # noqa: E402

OUT = ROOT / "experiments" / "voting"
OUT.mkdir(parents=True, exist_ok=True)
RESULT = {"generated": datetime.utcnow().isoformat() + "Z"}

PW = "Voter@123pass"
PW_HASH = hash_password(PW)  # one Argon2 hash reused for every scratch user (they all share PW)


def stats(vals):
    vals = sorted(vals)
    n = len(vals)
    return {
        "n": n, "mean_ms": round(statistics.mean(vals), 4), "median_ms": round(statistics.median(vals), 4),
        "p95_ms": round(vals[min(n - 1, int(n * 0.95))], 4), "min_ms": round(vals[0], 4),
        "max_ms": round(vals[-1], 4), "stdev_ms": round(statistics.stdev(vals), 4) if n > 1 else 0.0,
    }


def timeit(fn, n):
    out = []
    for _ in range(n):
        s = time.perf_counter()
        fn()
        out.append((time.perf_counter() - s) * 1000)
    return stats(out)


def make_voter(db, idx, tag="v"):
    u = User(username=f"{tag}{idx}", password_hash=PW_HASH, role="VOTER", display_name=f"Voter {idx}", email=f"{tag}{idx}@x.local")
    db.add(u)
    db.flush()
    a = generate_valid_aadhaar()
    db.add(VoterProfile(user_id=u.id, full_name=f"Voter {idx}", aadhaar_hash=hash_aadhaar(a), aadhaar_masked=mask_aadhaar(a)))
    return u, a


def make_election(db, title, ncand=3, status="OPEN"):
    from datetime import timedelta
    now = datetime.utcnow()
    e = Election(title=title, description="exp", start_time=now - timedelta(days=1), end_time=now + timedelta(days=1), status=status)
    db.add(e)
    db.flush()
    cands = []
    for i in range(ncand):
        c = Candidate(election_id=e.id, name=f"Cand {i + 1}", party="P", description="d", manifesto="m")
        db.add(c)
        cands.append(c)
    db.flush()
    return e, cands


# ------------------------------------------------------------------ A. micro timings
def part_a():
    ph = PW_HASH
    from app.security.auth import verify_password
    payload = {"election_id": 1, "ballot_id": "blt_" + "a" * 32, "encrypted_payload": "x" * 60, "nonce": "n" * 32, "timestamp": datetime.utcnow().isoformat()}
    ct = encrypt_ballot("3")
    priv, pub = generate_ed25519_keypair()
    msg = sha256_hex(canonical_serialize(payload)).encode()
    sig = sign_message(priv, msg)
    aad = generate_valid_aadhaar()
    res = {
        "sha256_tx_payload": timeit(lambda: sha256_hex(canonical_serialize(payload)), 5000),
        "aes256gcm_encrypt": timeit(lambda: encrypt_ballot("3"), 5000),
        "aes256gcm_decrypt": timeit(lambda: decrypt_ballot(ct), 5000),
        "ed25519_sign": timeit(lambda: sign_message(priv, msg), 3000),
        "ed25519_verify": timeit(lambda: verify_signature(pub, msg, sig), 3000),
        "verhoeff_validate": timeit(lambda: validate_verhoeff(aad), 20000),
        "aadhaar_salted_sha256": timeit(lambda: hash_aadhaar(aad), 20000),
        "argon2id_hash": timeit(lambda: hash_password(PW), 40),
        "argon2id_verify": timeit(lambda: verify_password(ph, PW), 40),
    }
    RESULT["micro_timings"] = res


# ------------------------------------------------------------------ B. growth + C. tamper
def strict_audit(db):
    """Stricter audit than validate_chain: also checks validator signatures, recomputes tx hashes,
    verifies the system signature on every transaction and cross-checks the ballots table."""
    base = validate_chain(db)
    if not base.get("valid"):
        return {"valid": False, "stage": "validate_chain", "field": base.get("field")}
    pubs = {v.node_id: v.public_key for v in db.query(ValidatorNode).all()}
    sys_pub = get_system_keypair()[1]
    ledger_payload_by_ballot = {}
    for b in db.query(LedgerBlock).order_by(LedgerBlock.block_index).all():
        sigs = json.loads(b.validator_signatures)
        good = sum(1 for nid, s in sigs.items() if nid in pubs and verify_signature(pubs[nid], b.block_hash.encode(), s))
        if good < 2:
            return {"valid": False, "stage": "validator_signatures", "block": b.block_index}
        for t in db.query(LedgerTransaction).filter(LedgerTransaction.block_index == b.block_index).all():
            recomputed = sha256_hex(canonical_serialize({
                "election_id": t.election_id, "ballot_id": t.ballot_id, "encrypted_payload": t.encrypted_payload,
                "nonce": t.nonce, "timestamp": t.timestamp.isoformat()}))
            if recomputed != t.tx_hash:
                return {"valid": False, "stage": "tx_hash_recompute", "block": b.block_index}
            if not verify_signature(sys_pub, t.tx_hash.encode(), t.signature):
                return {"valid": False, "stage": "tx_signature", "block": b.block_index}
            ledger_payload_by_ballot[t.ballot_id] = t.encrypted_payload
    for bl in db.query(Ballot).all():
        if ledger_payload_by_ballot.get(bl.ballot_id) != bl.encrypted_choice:
            return {"valid": False, "stage": "ballots_vs_ledger", "ballot": bl.ballot_id}
    return {"valid": True}


def rehash_from(db, k):
    """Attacker who can write the DB recomputes tx hash / merkle / block hashes from block k to the tip."""
    blocks = db.query(LedgerBlock).order_by(LedgerBlock.block_index).all()
    prev_hash = None
    for b in blocks:
        if b.block_index < k:
            prev_hash = b.block_hash
            continue
        txs = db.query(LedgerTransaction).filter(LedgerTransaction.block_index == b.block_index).all()
        for t in txs:
            t.tx_hash = sha256_hex(canonical_serialize({
                "election_id": t.election_id, "ballot_id": t.ballot_id, "encrypted_payload": t.encrypted_payload,
                "nonce": t.nonce, "timestamp": t.timestamp.isoformat()}))
        hashes = [t.tx_hash for t in txs]
        b.previous_hash = prev_hash
        b.merkle_root = compute_merkle_root(hashes)
        b.block_hash = compute_block_hash(b.block_index, b.timestamp.isoformat(), b.previous_hash, b.merkle_root, hashes)
        prev_hash = b.block_hash
    db.flush()


def part_b_c():
    init_db()
    db = SessionLocal()
    init_validators(db)
    create_genesis_block(db)
    e, cands = make_election(db, "Growth election")
    N = 300
    voters = [make_voter(db, i)[0] for i in range(N)]
    db.flush()
    for v in voters:
        db.add(VoterEligibility(election_id=e.id, voter_user_id=v.id, is_eligible=True))
    db.commit()
    eid = e.id
    cand_ids = [c.id for c in cands]
    per_vote = []
    validate_at = {}
    for i, v in enumerate(voters):
        s = time.perf_counter()
        tok = issue_authorization(db, eid, v.id)
        cast_vote(db, eid, v.id, tok, cand_ids[i % 3])
        per_vote.append((time.perf_counter() - s) * 1000)
        if (i + 1) in (25, 50, 100, 200, 300):
            reps = []
            for _ in range(5):
                s = time.perf_counter()
                r = validate_chain(db)
                reps.append((time.perf_counter() - s) * 1000)
            validate_at[i + 1] = {"height_blocks": r["height"], "valid": r["valid"], "median_ms": round(statistics.median(reps), 2)}
    RESULT["growth"] = {
        "votes": N,
        "per_vote_all": stats(per_vote),
        "per_vote_first_100": stats(per_vote[:100]),
        "per_vote_last_100": stats(per_vote[-100:]),
        "validate_chain_by_height": validate_at,
    }
    # per-stage breakdown of one vote (new voters on same chain)
    from app.ledger.ledger import propose_block
    stage = {"authorise": [], "encrypt_sign_hash": [], "propose_block": [], "persist": []}
    extra = [make_voter(db, 1000 + i, "s")[0] for i in range(60)]
    db.flush()
    for v in extra:
        db.add(VoterEligibility(election_id=eid, voter_user_id=v.id, is_eligible=True))
    db.commit()
    from app.security.crypto import generate_ballot_id, generate_nonce
    priv, pub = get_system_keypair()
    for v in extra:
        t0 = time.perf_counter()
        tok = issue_authorization(db, eid, v.id)
        t1 = time.perf_counter()
        bid, nonce = generate_ballot_id(), generate_nonce()
        enc = encrypt_ballot(str(cand_ids[0]))
        p = {"election_id": eid, "ballot_id": bid, "encrypted_payload": enc, "nonce": nonce, "timestamp": datetime.utcnow().isoformat()}
        th = sha256_hex(canonical_serialize(p))
        sg = sign_message(priv, th.encode())
        t2 = time.perf_counter()
        blk = propose_block(db, [{**p, "tx_hash": th, "signature": sg, "pubkey": pub}])
        t3 = time.perf_counter()
        from app.services.voting_service import verify_authorization
        auth = verify_authorization(db, eid, v.id, tok)
        db.add(Ballot(election_id=eid, ballot_id=bid, encrypted_choice=enc, nonce=nonce, tx_hash=th, block_index=blk.block_index))
        auth.is_used = True
        db.add(VoterParticipation(election_id=eid, voter_user_id=v.id, ballot_id=bid))
        db.commit()
        t4 = time.perf_counter()
        stage["authorise"].append((t1 - t0) * 1000)
        stage["encrypt_sign_hash"].append((t2 - t1) * 1000)
        stage["propose_block"].append((t3 - t2) * 1000)
        stage["persist"].append((t4 - t3) * 1000)
    RESULT["vote_stage_breakdown_ms_mean"] = {k: round(statistics.mean(v), 3) for k, v in stage.items()}

    # ---------------- tamper study (each case rolled back)
    tally0 = tally_results(db, eid)
    height = db.query(LedgerBlock).count()
    k = 120
    cases = []

    def run_case(name, desc, mutate, tally_check=False):
        before = tally0
        mutate()
        db.flush()
        vc = validate_chain(db)
        sa = strict_audit(db)
        tally_after = tally_results(db, eid) if tally_check else None
        db.rollback()
        cases.append({
            "case": name, "description": desc,
            "validate_chain_detects": (not vc.get("valid")), "validate_chain_field": vc.get("field") or vc.get("reason"),
            "first_invalid_block": vc.get("first_invalid"),
            "strict_audit_detects": (not sa.get("valid")), "strict_audit_stage": sa.get("stage"),
            "tally_changed": (tally_after["results"] != before["results"]) if tally_after else None,
        })

    def blk(i):
        return db.query(LedgerBlock).filter(LedgerBlock.block_index == i).first()

    def txs(i):
        return db.query(LedgerTransaction).filter(LedgerTransaction.block_index == i).all()

    def other_choice(ballot):
        cur = int(decrypt_ballot(ballot.encrypted_choice))
        return encrypt_ballot(str(next(c for c in cand_ids if c != cur)))

    run_case("T1 block_hash overwritten", "block_hash of one block replaced", lambda: setattr(blk(k), "block_hash", "f" * 64))
    run_case("T2 previous_hash overwritten", "previous_hash of one block replaced", lambda: setattr(blk(k), "previous_hash", "0" * 64))
    run_case("T3 merkle_root overwritten", "merkle_root of one block replaced", lambda: setattr(blk(k), "merkle_root", "a" * 64))
    run_case("T4 block timestamp edited", "timestamp of one block shifted by one hour",
             lambda: setattr(blk(k), "timestamp", blk(k).timestamp.replace(hour=(blk(k).timestamp.hour + 1) % 24)))
    run_case("T5 tx_hash overwritten", "tx_hash of one ledger transaction replaced", lambda: setattr(txs(k)[0], "tx_hash", "b" * 64))
    run_case("T6 ledger payload swapped (no re-hash)", "encrypted_payload in ledger_transactions replaced by another ciphertext",
             lambda: setattr(txs(k)[0], "encrypted_payload", other_choice(db.query(Ballot).filter(Ballot.ballot_id == txs(k)[0].ballot_id).first())))
    def t7():
        bl = db.query(Ballot).filter(Ballot.block_index == k).first()
        bl.encrypted_choice = other_choice(bl)
    run_case("T7 ballots table edited", "encrypted_choice of one row in ballots replaced by a vote for another candidate (tally source)", t7, True)

    def t8():
        for t in txs(k):
            db.delete(t)
    run_case("T8 transaction row deleted", "transaction removed from a block", t8)

    def t9():
        for t in txs(k):
            db.delete(t)
        db.delete(blk(k))
    run_case("T9 middle block deleted", "a block and its transaction removed from the middle of the chain", t9)

    def t10():
        last = db.query(LedgerBlock).order_by(LedgerBlock.block_index.desc()).first()
        for t in db.query(LedgerTransaction).filter(LedgerTransaction.block_index == last.block_index).all():
            db.delete(t)
        db.delete(last)
    run_case("T10 tip block deleted (truncation)", "newest block and its transaction removed", t10)
    run_case("T11 validator signatures forged", "validator_signatures replaced with random hex",
             lambda: setattr(blk(k), "validator_signatures", json.dumps({"validator-1": "ab" * 64, "validator-2": "cd" * 64, "validator-3": "ef" * 64})))

    def t12():
        t = txs(k)[0]
        t.encrypted_payload = other_choice(db.query(Ballot).filter(Ballot.ballot_id == t.ballot_id).first())
        rehash_from(db, k)
    run_case("T12 payload edited and chain re-hashed", "attacker edits a ballot and recomputes every hash from that block to the tip", t12)

    def t13():
        t = txs(k)[0]
        bl = db.query(Ballot).filter(Ballot.ballot_id == t.ballot_id).first()
        new = other_choice(bl)
        t.encrypted_payload = new
        bl.encrypted_choice = new
        rehash_from(db, k)
    run_case("T13 ballot+ledger edited and chain re-hashed", "both ballots and ledger edited consistently, hashes recomputed (signatures untouched)", t13, True)
    RESULT["tamper_study"] = {"chain_height": height, "target_block": k, "cases": cases,
                              "baseline_validate_chain": validate_chain(db), "baseline_strict_audit": strict_audit(db)}
    # strict audit cost
    reps = []
    for _ in range(3):
        s = time.perf_counter()
        strict_audit(db)
        reps.append((time.perf_counter() - s) * 1000)
    RESULT["tamper_study"]["strict_audit_ms_median"] = round(statistics.median(reps), 1)
    RESULT["tamper_study"]["validate_chain_ms_median"] = RESULT["growth"]["validate_chain_by_height"][300]["median_ms"]
    db.close()


# ------------------------------------------------------------------ D. HTTP
class Client:
    def __init__(self, host="127.0.0.1", port=18401):
        self.host, self.port = host, port
        self.cookie = None
        self.csrf = None
        self.last_headers = {}

    def call(self, method, path, body=None, csrf=True, cookie=True):
        conn = http.client.HTTPConnection(self.host, self.port, timeout=60)
        headers = {}
        data = None
        if body is not None:
            data = json.dumps(body)
            headers["Content-Type"] = "application/json"
        if cookie and self.cookie:
            headers["Cookie"] = self.cookie
        if csrf and self.csrf and method != "GET":
            headers["X-CSRF-Token"] = self.csrf
        s = time.perf_counter()
        conn.request(method, path, data, headers)
        r = conn.getresponse()
        raw = r.read().decode()
        ms = (time.perf_counter() - s) * 1000
        sc = r.getheader("Set-Cookie")
        if sc and "aegis_session" in sc:
            self.cookie = sc.split(";")[0]
            self.last_headers = {"Set-Cookie": sc}
        try:
            js = json.loads(raw)
        except ValueError:
            js = raw
        conn.close()
        return r.status, js, ms


def part_d():
    os.environ["DATABASE_URL"] = f"sqlite:///{HTTP_DB.as_posix()}"
    import sqlalchemy
    from sqlalchemy.orm import sessionmaker
    from app.database import Base
    eng = sqlalchemy.create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    S = sessionmaker(bind=eng)
    db = S()
    # genesis + validators for the HTTP DB (same persisted validator keys as the product)
    import app.ledger.ledger as L
    L.init_validators(db)
    L.create_genesis_block(db)
    for uname, role in (("admin", "ADMIN"), ("auditor", "AUDITOR")):
        db.add(User(username=uname, password_hash=PW_HASH, role=role, display_name=uname, email=f"{uname}@x.local"))
    db.commit()
    e, cands = make_election(db, "HTTP election")
    voters = []
    for i in range(27):
        u, a = make_voter(db, i + 1, "h")
        voters.append((u, a))
    extra_u, extra_a = make_voter(db, 99, "x")  # a registered voter used for cross-identity tests
    db.flush()
    for u, _ in voters + [(extra_u, extra_a)]:
        db.add(VoterEligibility(election_id=e.id, voter_user_id=u.id, is_eligible=True))
    db.commit()
    eid = e.id
    cand_ids = [c.id for c in cands]
    names = [(u.username, a) for u, a in voters]
    xname, xaad = extra_u.username, extra_a
    db.close()
    eng.dispose()

    env = dict(os.environ)
    py = sys.executable
    proc = subprocess.Popen([py, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "18401", "--log-level", "warning"],
                            cwd=str(ROOT), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    res = {}
    try:
        c0 = Client()
        for _ in range(60):
            try:
                st, js, _ = c0.call("GET", "/api/health")
                if st == 200:
                    break
            except OSError:
                time.sleep(0.5)
        res["health"] = js
        lat = {"login": [], "verify": [], "cast": [], "end_to_end": []}
        receipts = []
        t_login_window = []
        for idx, (uname, aad) in enumerate(names):
            if idx and idx % 9 == 0:
                time.sleep(62)  # login rate limit is 10 / 60 s per IP
            cl = Client()
            e2e = time.perf_counter()
            st, js, ms = cl.call("POST", "/api/auth/login", {"username": uname, "password": PW}, csrf=False)
            assert st == 200, (st, js)
            lat["login"].append(ms)
            cl.csrf = js["csrf"]
            st, js, ms = cl.call("POST", f"/api/voter/elections/{eid}/verify", {"aadhaar": aad})
            assert st == 200, (st, js)
            lat["verify"].append(ms)
            tok = js["auth_token"]
            st, js, ms = cl.call("POST", f"/api/voter/elections/{eid}/cast", {"candidate_id": cand_ids[idx % 3], "auth_token": tok})
            assert st == 200, (st, js)
            lat["cast"].append(ms)
            lat["end_to_end"].append((time.perf_counter() - e2e) * 1000)
            receipts.append(js["receipt"])
        res["latency"] = {k: stats(v) for k, v in lat.items()}
        res["voters_through_http"] = len(names)
        res["cookie_header"] = c0.last_headers or cl.last_headers

        # ---- security / functional matrix
        time.sleep(62)
        matrix = []

        def rec(name, expect, got, note=""):
            matrix.append({"test": name, "expected": expect, "got": got, "pass": expect == got, "note": note})

        anon = Client()
        rec("Anonymous GET /api/admin/overview", 401, anon.call("GET", "/api/admin/overview")[0])
        rec("Anonymous POST /api/voter/.../cast", 401, anon.call("POST", f"/api/voter/elections/{eid}/cast", {"candidate_id": 1, "auth_token": "x"})[0])
        rec("SQL-injection style username on login", 401, anon.call("POST", "/api/auth/login", {"username": "admin' OR '1'='1", "password": "x"}, csrf=False)[0])
        rec("Login with empty body fields", 422, anon.call("POST", "/api/auth/login", {"username": "", "password": ""}, csrf=False)[0])

        vcl = Client()
        st, js, _ = vcl.call("POST", "/api/auth/login", {"username": xname, "password": PW}, csrf=False)
        vcl.csrf = js["csrf"]
        rec("Voter GET /api/admin/overview (RBAC)", 403, vcl.call("GET", "/api/admin/overview")[0])
        rec("Voter GET /api/auditor/overview (RBAC)", 403, vcl.call("GET", "/api/auditor/overview")[0])
        rec("Voter POST status change (RBAC)", 403, vcl.call("POST", f"/api/admin/elections/{eid}/status", {"status": "CLOSED"})[0])
        csrf_save = vcl.csrf
        vcl.csrf = None
        rec("Voter POST verify without X-CSRF-Token", 403, vcl.call("POST", f"/api/voter/elections/{eid}/verify", {"aadhaar": xaad}, csrf=False)[0])
        vcl.csrf = csrf_save
        rec("Aadhaar with 11 digits", 400, vcl.call("POST", f"/api/voter/elections/{eid}/verify", {"aadhaar": "12345678901"})[0])
        rec("Aadhaar 12 digits, bad Verhoeff checksum", 400, vcl.call("POST", f"/api/voter/elections/{eid}/verify", {"aadhaar": xaad[:-1] + str((int(xaad[-1]) + 1) % 10)})[0])
        from app.identity.verhoeff import generate_valid_aadhaar as gva
        rec("Valid checksum, not in registry", 400, vcl.call("POST", f"/api/voter/elections/{eid}/verify", {"aadhaar": gva()})[0])
        rec("Another voter's valid Aadhaar", 403, vcl.call("POST", f"/api/voter/elections/{eid}/verify", {"aadhaar": names[0][1]})[0])
        rec("Cast with forged auth token", 400, vcl.call("POST", f"/api/voter/elections/{eid}/cast", {"candidate_id": cand_ids[0], "auth_token": "forged-token-value"})[0])
        rec("Voter reads results of an OPEN election", 404, vcl.call("GET", f"/api/elections/{eid}/results")[0])
        st, js, _ = vcl.call("POST", f"/api/voter/elections/{eid}/verify", {"aadhaar": xaad})
        tok = js["auth_token"]
        rec("Verify with own correct Aadhaar", 200, st)
        rec("Cast with candidate id from nowhere", 400, vcl.call("POST", f"/api/voter/elections/{eid}/cast", {"candidate_id": 999999, "auth_token": tok})[0])
        rec("Valid cast", 200, vcl.call("POST", f"/api/voter/elections/{eid}/cast", {"candidate_id": cand_ids[0], "auth_token": tok})[0])
        rec("Replay of used token (duplicate vote)", 400, vcl.call("POST", f"/api/voter/elections/{eid}/cast", {"candidate_id": cand_ids[0], "auth_token": tok})[0])
        rec("Second verify after voting", 400, vcl.call("POST", f"/api/voter/elections/{eid}/verify", {"aadhaar": xaad})[0])

        acl = Client()
        st, js, _ = acl.call("POST", "/api/auth/login", {"username": "admin", "password": PW}, csrf=False)
        acl.csrf = js["csrf"]
        rec("Admin invalid status value", 400, acl.call("POST", f"/api/admin/elections/{eid}/status", {"status": "NONSENSE"})[0])
        rec("Admin election with end before start", 400, acl.call("POST", "/api/admin/elections", {"title": "x", "description": "", "start_time": "2026-02-02T10:00", "end_time": "2026-02-01T10:00"})[0])
        rec("Admin reads tally of OPEN election", 200, acl.call("GET", f"/api/elections/{eid}/results")[0],
            "admin can see a live tally before the election closes")

        ucl = Client()
        st, js, _ = ucl.call("POST", "/api/auth/login", {"username": "auditor", "password": PW}, csrf=False)
        ucl.csrf = js["csrf"]
        st, js, ms_v = ucl.call("POST", "/api/auditor/verify")
        rec("Auditor integrity check on live chain", 200, st, f"valid={js.get('valid')} height={js.get('height')} in {ms_v:.1f} ms")
        res["auditor_verify_ms"] = round(ms_v, 1)
        res["auditor_verify_result"] = js
        st, js, _ = ucl.call("POST", "/api/auditor/tamper-test")
        rec("Auditor tamper-test on cloned ledger", 200, st, f"detected={js.get('detected')}")

        # rate limit
        got = []
        for i in range(12):
            got.append(Client().call("POST", "/api/auth/login", {"username": "nobody", "password": "bad"}, csrf=False)[0])
        res["login_rate_limit_status_sequence"] = got
        rec("11th failed login inside a minute is throttled", 429, got[10] if len(got) > 10 else None, f"sequence {got}")
        res["matrix"] = matrix
        res["matrix_summary"] = {"total": len(matrix), "passed": sum(1 for m in matrix if m["pass"])}
        res["cookie_header"] = acl.last_headers
    finally:
        proc.terminate()
        try:
            proc.wait(10)
        except Exception:
            proc.kill()

    # post-run DB facts: voter <-> ballot linkability, chain validity
    import sqlite3
    cx = sqlite3.connect(str(HTTP_DB))
    res["db_linkable_voter_ballot_rows"] = cx.execute(
        "select count(*) from voter_participation p join ballots b on b.ballot_id = p.ballot_id").fetchone()[0]
    res["db_ballots"] = cx.execute("select count(*) from ballots").fetchone()[0]
    res["db_blocks"] = cx.execute("select count(*) from ledger_blocks").fetchone()[0]
    res["db_audit_actions"] = dict(cx.execute("select action, count(*) from audit_logs group by action").fetchall())
    cx.close()
    RESULT["http"] = res


def main():
    RESULT["environment"] = {
        "python": sys.version.split()[0], "platform": platform.platform(), "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
    }
    import fastapi, sqlalchemy, cryptography, argon2
    RESULT["environment"]["libs"] = {"fastapi": fastapi.__version__, "sqlalchemy": sqlalchemy.__version__,
                                     "cryptography": cryptography.__version__, "argon2-cffi": argon2.__version__}
    t = time.perf_counter()
    part_a()
    print("A done", round(time.perf_counter() - t, 1), flush=True)
    part_b_c()
    print("B/C done", round(time.perf_counter() - t, 1), flush=True)
    (OUT / "metrics.json").write_text(json.dumps(RESULT, indent=2))
    if SKIP_HTTP:
        old = OUT / "metrics_http_backup.json"
        if old.exists():
            RESULT["http"] = json.loads(old.read_text())
    if not SKIP_HTTP:
        part_d()
        print("D done", round(time.perf_counter() - t, 1), flush=True)
    (OUT / "metrics.json").write_text(json.dumps(RESULT, indent=2))
    print("written", OUT / "metrics.json")


if __name__ == "__main__":
    main()
