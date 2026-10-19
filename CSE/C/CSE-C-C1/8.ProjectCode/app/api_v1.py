"""Additive JSON API for the React frontend.

Thin wrappers over the same services, models and ledger functions the Jinja routes use.
Nothing here changes existing behaviour; the HTML routes in main.py are untouched.
Auth is the existing aegis_session cookie; mutating calls also need X-CSRF-Token.
"""
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.provider import demo_provider
from app.ledger.ledger import tamper_test_clone, validate_chain
from app.models.models import (
    AuditLog, Ballot, BenchmarkRun, Candidate, Election, LedgerBlock, LedgerTransaction,
    User, ValidatorNode, VoterEligibility, VoterParticipation, VoterProfile,
)
from app.security.auth import verify_password
from app.security.rate_limit import is_rate_limited
from app.security.sessions import SESSION_COOKIE, create_session, destroy_session, get_session
from app.services.audit import log_event
from app.services.election_service import add_candidate, create_election
from app.services.voting_service import cast_vote, issue_authorization, tally_results

router = APIRouter(prefix="/api")

STATUSES = {"DRAFT", "OPEN", "PAUSED", "CLOSED"}


# ---------- helpers ----------
def iso(value):
    return value.isoformat() if isinstance(value, datetime) else value


def current(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    sess = get_session(token) if token else None
    user = db.query(User).filter(User.id == sess["user_id"]).first() if sess else None
    if not user:
        raise HTTPException(401, "Not authenticated")
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        if request.headers.get("x-csrf-token") != sess["csrf"]:
            raise HTTPException(403, "CSRF token missing or invalid")
    return {"user": user, "sess": sess, "token": token}


def role_required(role: str):
    def dep(cu=Depends(current)):
        if cu["user"].role != role:
            raise HTTPException(403, f"{role.title()} access required")
        return cu
    return dep


admin_only = role_required("ADMIN")
voter_only = role_required("VOTER")
auditor_only = role_required("AUDITOR")


def audit(request: Request, db: Session, user, action, entity_type=None, entity_id=None, details=None):
    ip = request.client.host if request.client else None
    log_event(db, user.id if user else None, user.username if user else None, action, entity_type, entity_id, details, ip)


def user_out(u: User):
    return {"id": u.id, "username": u.username, "display_name": u.display_name, "role": u.role, "email": u.email}


def election_out(e: Election):
    return {
        "id": e.id, "title": e.title, "description": e.description, "status": e.status,
        "start_time": iso(e.start_time), "end_time": iso(e.end_time),
    }


def candidate_out(c: Candidate):
    return {
        "id": c.id, "election_id": c.election_id, "name": c.name, "party": c.party,
        "description": c.description, "manifesto": c.manifesto, "is_active": c.is_active,
    }


def block_out(b: LedgerBlock):
    return {
        "block_index": b.block_index, "timestamp": iso(b.timestamp), "previous_hash": b.previous_hash,
        "merkle_root": b.merkle_root, "block_hash": b.block_hash, "transaction_count": b.transaction_count,
    }


def tx_out(t: LedgerTransaction):
    return {
        "tx_hash": t.tx_hash, "block_index": t.block_index, "election_id": t.election_id,
        "ballot_id": t.ballot_id, "encrypted_payload": t.encrypted_payload, "nonce": t.nonce,
        "timestamp": iso(t.timestamp),
    }


def log_out(l: AuditLog):
    return {
        "id": l.id, "timestamp": iso(l.timestamp), "actor": l.actor_username, "action": l.action,
        "entity_type": l.entity_type, "entity_id": l.entity_id, "details": l.details,
    }


def validators_out(db: Session):
    return [{"node_id": v.node_id, "public_key": v.public_key, "is_active": v.is_active} for v in db.query(ValidatorNode).all()]


def bench_out(b: BenchmarkRun):
    return {
        "id": b.id, "timestamp": iso(b.timestamp), "total_ops": b.total_ops, "sync_duration": b.sync_duration,
        "async_duration": b.async_duration, "throughput_sync": b.throughput_sync,
        "throughput_async": b.throughput_async, "mean_latency_ms": b.mean_latency_ms,
        "p95_latency_ms": b.p95_latency_ms, "details": json.loads(b.details_json) if b.details_json else None,
    }


def election_or_404(db: Session, eid: int) -> Election:
    e = db.query(Election).filter(Election.id == eid).first()
    if not e:
        raise HTTPException(404, "Election not found")
    return e


def turnout(votes: int, eligible: int) -> float:
    return round(votes / eligible * 100, 1) if eligible else 0.0


# ---------- auth ----------
class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


@router.post("/auth/login")
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    if is_rate_limited(f"login:{ip}", max_req=10, window_sec=60):
        raise HTTPException(429, "Too many attempts. Try again in a minute.")
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(user.password_hash, body.password):
        audit(request, db, None, "login_failed", "user", body.username, "invalid credentials")
        raise HTTPException(401, "Invalid username or password")
    token = create_session(user.id, user.username, user.role)
    audit(request, db, user, "login_success", "user", user.id, f"role {user.role}")
    response.set_cookie(key=SESSION_COOKIE, value=token, httponly=True, samesite="lax", path="/")
    return {"user": user_out(user), "csrf": get_session(token)["csrf"]}


@router.post("/auth/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    sess = get_session(token) if token else None
    if sess:
        user = db.query(User).filter(User.id == sess["user_id"]).first()
        audit(request, db, user, "logout", "user", sess["user_id"])
        destroy_session(token)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@router.get("/auth/me")
def me(request: Request, db: Session = Depends(get_db)):
    """200 with user=null when signed out, so the browser console stays free of expected 401s."""
    token = request.cookies.get(SESSION_COOKIE)
    sess = get_session(token) if token else None
    user = db.query(User).filter(User.id == sess["user_id"]).first() if sess else None
    if not user:
        return {"user": None, "csrf": None}
    return {"user": user_out(user), "csrf": sess["csrf"]}


# ---------- public ----------
@router.get("/public/overview")
def public_overview(db: Session = Depends(get_db)):
    elections = db.query(Election).order_by(Election.id.desc()).all()
    chain = validate_chain(db)
    return {
        "elections": [election_out(e) for e in elections],
        "ledger": {"valid": chain.get("valid"), "height": chain.get("height")},
        "votes_cast": db.query(Ballot).count(),
        "validators": db.query(ValidatorNode).count(),
    }


# ---------- admin ----------
@router.get("/admin/overview")
def admin_overview(cu=Depends(admin_only), db: Session = Depends(get_db)):
    voters = db.query(User).filter(User.role == "VOTER").count()
    votes = db.query(Ballot).count()
    bench = db.query(BenchmarkRun).order_by(BenchmarkRun.id.desc()).first()
    elections = db.query(Election).order_by(Election.id.desc()).all()
    per_election = []
    for e in elections[:8]:
        eligible = db.query(VoterEligibility).filter(VoterEligibility.election_id == e.id).count()
        cast = db.query(Ballot).filter(Ballot.election_id == e.id).count()
        per_election.append({**election_out(e), "eligible": eligible, "votes": cast, "turnout": turnout(cast, eligible)})
    return {
        "total_voters": voters, "total_votes": votes, "turnout": turnout(votes, voters),
        "election_count": len(elections), "open_count": sum(1 for e in elections if e.status == "OPEN"), "chain": validate_chain(db), "validators": validators_out(db),
        "benchmark": bench_out(bench) if bench else None, "elections": per_election,
        "blocks": [block_out(b) for b in db.query(LedgerBlock).order_by(LedgerBlock.block_index.desc()).limit(5)],
        "audit_logs": [log_out(l) for l in db.query(AuditLog).order_by(AuditLog.id.desc()).limit(10)],
    }


@router.get("/admin/elections")
def admin_elections(cu=Depends(admin_only), db: Session = Depends(get_db)):
    out = []
    for e in db.query(Election).order_by(Election.id.desc()).all():
        eligible = db.query(VoterEligibility).filter(VoterEligibility.election_id == e.id).count()
        cast = db.query(Ballot).filter(Ballot.election_id == e.id).count()
        out.append({
            **election_out(e), "eligible": eligible, "votes": cast, "turnout": turnout(cast, eligible),
            "candidate_count": db.query(Candidate).filter(Candidate.election_id == e.id).count(),
        })
    return {"elections": out}


class ElectionIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    start_time: str
    end_time: str


@router.post("/admin/elections", status_code=201)
def admin_create_election(body: ElectionIn, request: Request, cu=Depends(admin_only), db: Session = Depends(get_db)):
    try:
        st, et = datetime.fromisoformat(body.start_time), datetime.fromisoformat(body.end_time)
    except ValueError:
        raise HTTPException(400, "Invalid date or time")
    if et <= st:
        raise HTTPException(400, "End time must be after start time")
    e = create_election(db, body.title.strip(), body.description, st, et, cu["user"].id)
    audit(request, db, cu["user"], "election_create", "election", e.id, body.title)
    for v in db.query(User).filter(User.role == "VOTER").all():
        exists = db.query(VoterEligibility).filter(VoterEligibility.election_id == e.id, VoterEligibility.voter_user_id == v.id).first()
        if not exists:
            db.add(VoterEligibility(election_id=e.id, voter_user_id=v.id, is_eligible=True))
    db.commit()
    return election_out(e)


@router.get("/admin/elections/{eid}")
def admin_election_detail(eid: int, cu=Depends(admin_only), db: Session = Depends(get_db)):
    e = election_or_404(db, eid)
    eligible = db.query(VoterEligibility).filter(VoterEligibility.election_id == eid).count()
    votes = db.query(Ballot).filter(Ballot.election_id == eid).count()
    cands = db.query(Candidate).filter(Candidate.election_id == eid).order_by(Candidate.id).all()
    return {
        "election": election_out(e), "candidates": [candidate_out(c) for c in cands],
        "eligible": eligible, "votes": votes, "turnout": turnout(votes, eligible),
        "results": tally_results(db, eid) if e.status == "CLOSED" else None,
    }


class StatusIn(BaseModel):
    status: str


@router.post("/admin/elections/{eid}/status")
def admin_set_status(eid: int, body: StatusIn, request: Request, cu=Depends(admin_only), db: Session = Depends(get_db)):
    status = body.status.upper()
    if status not in STATUSES:
        raise HTTPException(400, f"Status must be one of {', '.join(sorted(STATUSES))}")
    e = election_or_404(db, eid)
    e.status = status
    db.commit()
    audit(request, db, cu["user"], f"election_{status.lower()}", "election", eid, status)
    return election_out(e)


class CandidateIn(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    party: str = Field(min_length=1, max_length=128)
    description: str = ""
    manifesto: str = ""


@router.post("/admin/elections/{eid}/candidates", status_code=201)
def admin_add_candidate(eid: int, body: CandidateIn, request: Request, cu=Depends(admin_only), db: Session = Depends(get_db)):
    election_or_404(db, eid)
    c = add_candidate(db, eid, body.name.strip(), body.party.strip(), body.description, body.manifesto)
    audit(request, db, cu["user"], "candidate_add", "candidate", c.id, body.name)
    return candidate_out(c)


@router.post("/admin/candidates/{cid}/toggle")
def admin_toggle_candidate(cid: int, request: Request, cu=Depends(admin_only), db: Session = Depends(get_db)):
    c = db.query(Candidate).filter(Candidate.id == cid).first()
    if not c:
        raise HTTPException(404, "Candidate not found")
    c.is_active = not c.is_active
    db.commit()
    audit(request, db, cu["user"], "candidate_toggle", "candidate", cid, str(c.is_active))
    return candidate_out(c)


@router.get("/admin/benchmarks")
def admin_benchmarks(cu=Depends(admin_only), db: Session = Depends(get_db)):
    runs = db.query(BenchmarkRun).order_by(BenchmarkRun.id.desc()).limit(5).all()
    return {"runs": [bench_out(b) for b in runs]}


# ---------- results (admin: any status, others: closed only) ----------
@router.get("/elections/{eid}/results")
def election_results(eid: int, cu=Depends(current), db: Session = Depends(get_db)):
    e = election_or_404(db, eid)
    if cu["user"].role != "ADMIN" and e.status != "CLOSED":
        raise HTTPException(404, "Results are published when the election is closed")
    return {"election": election_out(e), **tally_results(db, eid)}


# ---------- voter ----------
@router.get("/voter/elections")
def voter_elections(cu=Depends(voter_only), db: Session = Depends(get_db)):
    elections = db.query(Election).filter(Election.status.in_(["OPEN", "PAUSED", "CLOSED"])).order_by(Election.id.desc()).all()
    parts = {p.election_id: p for p in db.query(VoterParticipation).filter(VoterParticipation.voter_user_id == cu["user"].id)}
    return {"elections": [
        {**election_out(e), "voted": e.id in parts, "ballot_id": parts[e.id].ballot_id if e.id in parts else None,
         "candidate_count": db.query(Candidate).filter(Candidate.election_id == e.id, Candidate.is_active == True).count()}  # noqa: E712
        for e in elections
    ]}


@router.get("/voter/elections/{eid}")
def voter_election(eid: int, cu=Depends(voter_only), db: Session = Depends(get_db)):
    e = election_or_404(db, eid)
    part = db.query(VoterParticipation).filter(VoterParticipation.election_id == eid, VoterParticipation.voter_user_id == cu["user"].id).first()
    profile = db.query(VoterProfile).filter(VoterProfile.user_id == cu["user"].id).first()
    return {
        "election": election_out(e), "masked_aadhaar": profile.aadhaar_masked if profile else None,
        "voted": part is not None, "ballot_id": part.ballot_id if part else None,
        "voted_at": iso(part.created_at) if part else None,
    }


class VerifyIn(BaseModel):
    aadhaar: str = Field(min_length=1, max_length=32)


@router.post("/voter/elections/{eid}/verify")
def voter_verify(eid: int, body: VerifyIn, request: Request, cu=Depends(voter_only), db: Session = Depends(get_db)):
    user = cu["user"]
    ip = request.client.host if request.client else "unknown"
    if is_rate_limited(f"verify:{ip}", max_req=15, window_sec=60):
        raise HTTPException(429, "Too many verification attempts. Try again in a minute.")
    election_or_404(db, eid)

    def fail(code, msg):
        audit(request, db, user, "aadhaar_verify_failed", "election", eid, msg)
        raise HTTPException(code, msg)

    result = demo_provider.verify(body.aadhaar, db)
    if not result["success"]:
        fail(400, result["reason"])
    if result["user"].id != user.id:
        fail(403, "Aadhaar does not match logged-in voter")
    elig = db.query(VoterEligibility).filter(VoterEligibility.election_id == eid, VoterEligibility.voter_user_id == user.id).first()
    if not elig or not elig.is_eligible:
        fail(403, "You are not eligible for this election")
    if db.query(VoterParticipation).filter(VoterParticipation.election_id == eid, VoterParticipation.voter_user_id == user.id).first():
        raise HTTPException(400, "You have already voted in this election")
    try:
        token = issue_authorization(db, eid, user.id)
    except ValueError as ve:
        raise HTTPException(400, str(ve))
    audit(request, db, user, "aadhaar_verify_success", "election", eid, "Demo verification")
    audit(request, db, user, "auth_issued", "election", eid, "token issued")
    cands = db.query(Candidate).filter(Candidate.election_id == eid, Candidate.is_active == True).order_by(Candidate.id).all()  # noqa: E712
    return {"auth_token": token, "expires_in": 600, "candidates": [candidate_out(c) for c in cands]}


class CastIn(BaseModel):
    candidate_id: int
    auth_token: str


@router.post("/voter/elections/{eid}/cast")
def voter_cast(eid: int, body: CastIn, request: Request, cu=Depends(voter_only), db: Session = Depends(get_db)):
    user = cu["user"]
    e = election_or_404(db, eid)
    try:
        res = cast_vote(db, eid, user.id, body.auth_token, body.candidate_id)
    except ValueError as ve:
        audit(request, db, user, "vote_rejected", "election", eid, str(ve))
        raise HTTPException(400, str(ve))
    except Exception as ex:
        audit(request, db, user, "vote_failed", "election", eid, str(ex))
        raise HTTPException(500, "Vote could not be recorded. Nothing was submitted; try again.")
    audit(request, db, user, "vote_cast", "election", eid, f"tx {res['tx_hash']}")
    return {"election": election_out(e), "receipt": {k: res[k] for k in ("ballot_id", "tx_hash", "block_index", "block_hash")}}


# ---------- auditor ----------
def auditor_snapshot(db: Session, chain):
    return {
        "chain": chain, "validators": validators_out(db),
        "blocks": [block_out(b) for b in db.query(LedgerBlock).order_by(LedgerBlock.block_index.desc()).limit(20)],
        "transactions": [tx_out(t) for t in db.query(LedgerTransaction).order_by(LedgerTransaction.id.desc()).limit(20)],
        "audit_logs": [log_out(l) for l in db.query(AuditLog).order_by(AuditLog.id.desc()).limit(20)],
    }


@router.get("/auditor/overview")
def auditor_overview(cu=Depends(auditor_only), db: Session = Depends(get_db)):
    return auditor_snapshot(db, validate_chain(db))


@router.post("/auditor/verify")
def auditor_verify(request: Request, cu=Depends(auditor_only), db: Session = Depends(get_db)):
    result = validate_chain(db)
    audit(request, db, cu["user"], "integrity_check", "ledger", None, json.dumps(result))
    return result


@router.post("/auditor/tamper-test")
def auditor_tamper(request: Request, cu=Depends(auditor_only), db: Session = Depends(get_db)):
    result = tamper_test_clone(db)
    audit(request, db, cu["user"], "tamper_test", "ledger", None, json.dumps(result))
    return result


@router.get("/auditor/blocks/{index}")
def auditor_block(index: int, cu=Depends(auditor_only), db: Session = Depends(get_db)):
    b = db.query(LedgerBlock).filter(LedgerBlock.block_index == index).first()
    if not b:
        raise HTTPException(404, "Block not found")
    txs = db.query(LedgerTransaction).filter(LedgerTransaction.block_index == index).all()
    try:
        sigs = json.loads(b.validator_signatures)
    except ValueError:
        sigs = {}
    return {"block": block_out(b), "signatures": sigs, "transactions": [tx_out(t) for t in txs],
            "height": db.query(LedgerBlock).count()}
