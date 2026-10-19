import secrets
import hashlib
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import VoterEligibility, VotingAuthorization, VoterParticipation, Ballot, Election, Candidate
from app.security.crypto import hash_token, encrypt_ballot, generate_ballot_id, generate_nonce, sha256_hex, canonical_serialize, sign_message
from app.ledger.ledger import propose_block
from app.config import SECRET_KEY

# For transaction signing, generate a system key for voting transactions (ephemeral per server)
import base64
_system_priv_hex = None
_system_pub_hex = None

def get_system_keypair():
    global _system_priv_hex, _system_pub_hex
    if _system_priv_hex:
        return _system_priv_hex, _system_pub_hex
    from app.security.crypto import generate_ed25519_keypair
    import pathlib, json
    p = pathlib.Path("data/system_key.json")
    if p.exists():
        try:
            d = json.loads(p.read_text())
            _system_priv_hex = d["priv"]
            _system_pub_hex = d["pub"]
            return _system_priv_hex, _system_pub_hex
        except:
            pass
    priv, pub = generate_ed25519_keypair()
    p.write_text(json.dumps({"priv": priv, "pub": pub}))
    _system_priv_hex, _system_pub_hex = priv, pub
    return priv, pub

def issue_authorization(db: Session, election_id: int, voter_user_id: int) -> str:
    # check eligibility
    elig = db.query(VoterEligibility).filter(VoterEligibility.election_id==election_id, VoterEligibility.voter_user_id==voter_user_id).first()
    if not elig or not elig.is_eligible:
        raise ValueError("Voter not eligible for this election")
    # check already voted
    part = db.query(VoterParticipation).filter(VoterParticipation.election_id==election_id, VoterParticipation.voter_user_id==voter_user_id).first()
    if part:
        raise ValueError("Voter has already voted in this election")
    # check existing auth not used
    existing = db.query(VotingAuthorization).filter(VotingAuthorization.election_id==election_id, VotingAuthorization.voter_user_id==voter_user_id).first()
    if existing and not existing.is_used:
        # reuse if not expired
        if existing.expires_at > datetime.utcnow():
            raise ValueError("Authorization already issued and pending")
        else:
            db.delete(existing)
            db.commit()
    token = secrets.token_urlsafe(32)
    th = hash_token(token)
    auth = VotingAuthorization(
        election_id=election_id,
        voter_user_id=voter_user_id,
        token_hash=th,
        is_used=False,
        expires_at=datetime.utcnow()+timedelta(minutes=10)
    )
    db.add(auth)
    db.commit()
    return token

def verify_authorization(db: Session, election_id: int, voter_user_id: int, token: str):
    th = hash_token(token)
    auth = db.query(VotingAuthorization).filter(VotingAuthorization.election_id==election_id, VotingAuthorization.voter_user_id==voter_user_id, VotingAuthorization.token_hash==th).first()
    if not auth:
        raise ValueError("Invalid authorization token")
    if auth.is_used:
        raise ValueError("Authorization token already used")
    if auth.expires_at < datetime.utcnow():
        raise ValueError("Authorization token expired")
    return auth

def cast_vote(db: Session, election_id: int, voter_user_id: int, token: str, candidate_id: int) -> dict:
    election = db.query(Election).filter(Election.id==election_id).first()
    if not election:
        raise ValueError("Election not found")
    if election.status != "OPEN":
        raise ValueError("Election is not open for voting")
    cand = db.query(Candidate).filter(Candidate.id==candidate_id, Candidate.election_id==election_id, Candidate.is_active==True).first()
    if not cand:
        raise ValueError("Invalid candidate")
    # verify auth
    auth = verify_authorization(db, election_id, voter_user_id, token)
    # check participation constraint
    exists = db.query(VoterParticipation).filter(VoterParticipation.election_id==election_id, VoterParticipation.voter_user_id==voter_user_id).first()
    if exists:
        raise ValueError("Duplicate vote detected")
    # encrypt ballot
    ballot_id = generate_ballot_id()
    nonce = generate_nonce()
    plaintext = str(candidate_id)
    encrypted = encrypt_ballot(plaintext)
    # transaction hash
    tx_payload = {
        "election_id": election_id,
        "ballot_id": ballot_id,
        "encrypted_payload": encrypted,
        "nonce": nonce,
        "timestamp": datetime.utcnow().isoformat(),
    }
    tx_hash = sha256_hex(canonical_serialize(tx_payload))
    # sign with system key
    priv, pub = get_system_keypair()
    sig = sign_message(priv, tx_hash.encode())
    tx = {
        **tx_payload,
        "tx_hash": tx_hash,
        "signature": sig,
        "pubkey": pub
    }
    # propose block (single tx per block for simplicity, quorum)
    block = propose_block(db, [tx])
    # create ballot record
    ballot = Ballot(
        election_id=election_id,
        ballot_id=ballot_id,
        encrypted_choice=encrypted,
        nonce=nonce,
        tx_hash=tx_hash,
        block_index=block.block_index
    )
    db.add(ballot)
    # mark auth used
    auth.is_used = True
    # add participation
    part = VoterParticipation(election_id=election_id, voter_user_id=voter_user_id, ballot_id=ballot_id)
    db.add(part)
    db.commit()
    return {
        "ballot_id": ballot_id,
        "tx_hash": tx_hash,
        "block_index": block.block_index,
        "block_hash": block.block_hash,
        "encrypted_payload": encrypted
    }

def tally_results(db: Session, election_id: int) -> dict:
    from app.security.crypto import decrypt_ballot
    ballots = db.query(Ballot).filter(Ballot.election_id==election_id).all()
    candidates = db.query(Candidate).filter(Candidate.election_id==election_id).all()
    counts = {c.id: 0 for c in candidates}
    for b in ballots:
        try:
            pt = decrypt_ballot(b.encrypted_choice)
            cid = int(pt)
            if cid in counts:
                counts[cid]+=1
        except Exception:
            continue
    # build result list
    results = []
    for c in candidates:
        results.append({"candidate_id": c.id, "name": c.name, "party": c.party, "votes": counts[c.id]})
    results.sort(key=lambda x: x["votes"], reverse=True)
    total = len(ballots)
    return {"total_votes": total, "results": results}
