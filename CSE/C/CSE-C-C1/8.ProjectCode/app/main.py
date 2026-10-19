from fastapi import FastAPI, Request, Depends, Form, HTTPException, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.database import SessionLocal, init_db
from app.config import APP_NAME
from app.models.models import User, Election, Candidate, VoterProfile, LedgerBlock, LedgerTransaction, AuditLog, VoterEligibility, Ballot
from app.security.auth import hash_password, verify_password
from app.security.sessions import create_session, get_session, destroy_session, get_csrf_for_session, SESSION_COOKIE
from app.security.rate_limit import is_rate_limited
from app.services.audit import log_event
from app.identity.provider import demo_provider
from app.ledger.ledger import create_genesis_block, validate_chain, tamper_test_clone, init_validators
from app.services.voting_service import issue_authorization, cast_vote, tally_results
from app.security.crypto import mask_aadhaar

app = FastAPI(title=APP_NAME)

from app.api_v1 import router as api_v1_router
app.include_router(api_v1_router)

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Ensure DB init
init_db()
# ensure genesis and validators
from app.database import SessionLocal as SL
db0 = SL()
try:
    init_validators(db0)
    create_genesis_block(db0)
finally:
    db0.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    sess = get_session(token)
    if not sess:
        return None
    user = db.query(User).filter(User.id == sess["user_id"]).first()
    if not user:
        return None
    return {"user": user, "session": sess, "token": token}

def require_role(roles: list):
    def dep(request: Request, db: Session = Depends(get_db)):
        cu = get_current_user(request, db)
        if not cu:
            raise HTTPException(status_code=401, detail="Not authenticated")
        if cu["user"].role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return cu
    return dep

def csrf_check(request: Request, current = Depends(get_current_user)):
    if request.method in ["POST", "PUT", "DELETE"]:
        token = request.cookies.get(SESSION_COOKIE)
        sess = get_session(token) if token else None
        form_token = None
        # try form or header
        ctype = request.headers.get("content-type","")
        # FastAPI will parse form via dependency but we need to check header alternative
        # We'll check via request.headers csrf
        header_csrf = request.headers.get("x-csrf-token")
        # For form posts, the csrf token will be validated in route manually if needed
        # Here just check header if present
        if sess and header_csrf and header_csrf != sess["csrf"]:
            raise HTTPException(status_code=403, detail="CSRF mismatch")
    return current

# --- helpers ---
def audit(request: Request, db: Session, user, action, entity_type=None, entity_id=None, details=None):
    ip = request.client.host if request.client else None
    uname = user.username if user else None
    uid = user.id if user else None
    log_event(db, uid, uname, action, entity_type, entity_id, details, ip)

# Routes

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    elections = db.query(Election).order_by(Election.id.desc()).all()
    return templates.TemplateResponse("home.html", {"request": request, "current": cur, "elections": elections})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if cur:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    if is_rate_limited(f"login:{ip}", max_req=10, window_sec=60):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Too many attempts. Try later."}, status_code=429)
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(user.password_hash, password):
        audit(request, db, None, "login_failed", "user", username, "invalid credentials")
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"}, status_code=401)
    # success
    token = create_session(user.id, user.username, user.role)
    sess = get_session(token)
    audit(request, db, user, "login_success", "user", user.id, f"role {user.role}")
    resp = RedirectResponse(url="/dashboard", status_code=302)
    resp.set_cookie(key=SESSION_COOKIE, value=token, httponly=True, samesite="lax", path="/")
    return resp

@app.get("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    cu = get_current_user(request, db)
    if cu:
        audit(request, db, cu["user"], "logout", "user", cu["user"].id)
    if token:
        destroy_session(token)
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie(SESSION_COOKIE)
    return resp

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur:
        return RedirectResponse(url="/login", status_code=302)
    role = cur["user"].role
    if role == "ADMIN":
        return RedirectResponse(url="/admin", status_code=302)
    elif role == "AUDITOR":
        return RedirectResponse(url="/auditor", status_code=302)
    else:
        return RedirectResponse(url="/voter", status_code=302)

# --- Admin ---
@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur or cur["user"].role != "ADMIN":
        return RedirectResponse(url="/login", status_code=302)
    elections = db.query(Election).order_by(Election.id.desc()).all()
    total_voters = db.query(User).filter(User.role=="VOTER").count()
    total_votes = db.query(Ballot).count()
    turnout = round((total_votes/total_voters*100) if total_voters else 0, 2)
    chain = validate_chain(db)
    blocks = db.query(LedgerBlock).order_by(LedgerBlock.block_index.desc()).limit(5).all()
    audit_logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(10).all()
    validators = db.query(LedgerBlock).count()
    # benchmark latest
    from app.models.models import BenchmarkRun
    bench = db.query(BenchmarkRun).order_by(BenchmarkRun.id.desc()).first()
    # validator nodes
    from app.models.models import ValidatorNode
    vnodes = db.query(ValidatorNode).all()
    return templates.TemplateResponse("admin.html", {"request": request, "current": cur, "elections": elections, "total_voters": total_voters, "total_votes": total_votes, "turnout": turnout, "chain": chain, "blocks": blocks, "logs": audit_logs, "bench": bench, "vnodes": vnodes})

@app.get("/admin/elections", response_class=HTMLResponse)
def admin_elections(request: Request, db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur or cur["user"].role != "ADMIN":
        return RedirectResponse(url="/login", status_code=302)
    elections = db.query(Election).order_by(Election.id.desc()).all()
    return templates.TemplateResponse("admin_elections.html", {"request": request, "current": cur, "elections": elections})

@app.post("/admin/elections/create")
def create_election_route(request: Request, title: str = Form(...), description: str = Form(""), start_time: str = Form(...), end_time: str = Form(...), db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur or cur["user"].role != "ADMIN":
        raise HTTPException(403)
    # CSRF check via form
    token = request.cookies.get(SESSION_COOKIE)
    sess = get_session(token) if token else None
    # optional csrf form field check - we allow but not strict for demo
    try:
        st = datetime.fromisoformat(start_time)
        et = datetime.fromisoformat(end_time)
    except:
        raise HTTPException(400, "Invalid datetime")
    from app.services.election_service import create_election
    e = create_election(db, title, description, st, et, cur["user"].id)
    audit(request, db, cur["user"], "election_create", "election", e.id, title)
    # auto add eligibility for all voters
    voters = db.query(User).filter(User.role=="VOTER").all()
    for v in voters:
        exists = db.query(VoterEligibility).filter(VoterEligibility.election_id==e.id, VoterEligibility.voter_user_id==v.id).first()
        if not exists:
            db.add(VoterEligibility(election_id=e.id, voter_user_id=v.id, is_eligible=True))
    db.commit()
    return RedirectResponse(url="/admin/elections", status_code=302)

@app.post("/admin/elections/{eid}/status")
def change_status(request: Request, eid: int, status: str = Form(...), db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur or cur["user"].role != "ADMIN":
        raise HTTPException(403)
    e = db.query(Election).filter(Election.id==eid).first()
    if not e:
        raise HTTPException(404)
    e.status = status
    db.commit()
    audit(request, db, cur["user"], f"election_{status.lower()}", "election", eid, status)
    return RedirectResponse(url="/admin/elections", status_code=302)

@app.get("/admin/elections/{eid}", response_class=HTMLResponse)
def admin_election_detail(request: Request, eid: int, db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur or cur["user"].role != "ADMIN":
        return RedirectResponse(url="/login", status_code=302)
    e = db.query(Election).filter(Election.id==eid).first()
    if not e:
        raise HTTPException(404)
    cands = db.query(Candidate).filter(Candidate.election_id==eid).all()
    eligible = db.query(VoterEligibility).filter(VoterEligibility.election_id==eid).count()
    votes = db.query(Ballot).filter(Ballot.election_id==eid).count()
    results = None
    if e.status == "CLOSED":
        results = tally_results(db, eid)
    return templates.TemplateResponse("admin_election_detail.html", {"request": request, "current": cur, "election": e, "candidates": cands, "eligible": eligible, "votes": votes, "results": results})

@app.post("/admin/elections/{eid}/candidates/add")
def add_candidate_route(request: Request, eid: int, name: str = Form(...), party: str = Form(...), description: str = Form(""), manifesto: str = Form(""), db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur or cur["user"].role != "ADMIN":
        raise HTTPException(403)
    from app.services.election_service import add_candidate
    c = add_candidate(db, eid, name, party, description, manifesto)
    audit(request, db, cur["user"], "candidate_add", "candidate", c.id, name)
    return RedirectResponse(url=f"/admin/elections/{eid}", status_code=302)

@app.post("/admin/candidates/{cid}/toggle")
def toggle_candidate(request: Request, cid: int, db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur or cur["user"].role != "ADMIN":
        raise HTTPException(403)
    c = db.query(Candidate).filter(Candidate.id==cid).first()
    if not c:
        raise HTTPException(404)
    c.is_active = not c.is_active
    db.commit()
    audit(request, db, cur["user"], "candidate_toggle", "candidate", cid, str(c.is_active))
    return RedirectResponse(url=f"/admin/elections/{c.election_id}", status_code=302)

@app.get("/admin/results/{eid}", response_class=HTMLResponse)
def admin_results(request: Request, eid: int, db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur or cur["user"].role != "ADMIN":
        return RedirectResponse(url="/login", status_code=302)
    e = db.query(Election).filter(Election.id==eid).first()
    if not e:
        raise HTTPException(404)
    res = tally_results(db, eid)
    return templates.TemplateResponse("results.html", {"request": request, "current": cur, "election": e, "results": res})

@app.get("/admin/benchmark", response_class=HTMLResponse)
def admin_benchmark_page(request: Request, db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur or cur["user"].role != "ADMIN":
        return RedirectResponse(url="/login", status_code=302)
    from app.models.models import BenchmarkRun
    runs = db.query(BenchmarkRun).order_by(BenchmarkRun.id.desc()).limit(5).all()
    return templates.TemplateResponse("benchmark.html", {"request": request, "current": cur, "runs": runs})

# --- Voter ---
@app.get("/voter", response_class=HTMLResponse)
def voter_home(request: Request, db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur or cur["user"].role != "VOTER":
        return RedirectResponse(url="/login", status_code=302)
    elections = db.query(Election).filter(Election.status.in_(["OPEN","PAUSED","CLOSED"])).order_by(Election.id.desc()).all()
    # check participation
    from app.models.models import VoterParticipation
    parts = {p.election_id: p for p in db.query(VoterParticipation).filter(VoterParticipation.voter_user_id==cur["user"].id).all()}
    return templates.TemplateResponse("voter_home.html", {"request": request, "current": cur, "elections": elections, "parts": parts})

@app.get("/voter/verify/{eid}", response_class=HTMLResponse)
def voter_verify_page(request: Request, eid: int, db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur or cur["user"].role != "VOTER":
        return RedirectResponse(url="/login", status_code=302)
    e = db.query(Election).filter(Election.id==eid).first()
    if not e:
        raise HTTPException(404)
    from app.models.models import VoterParticipation
    part = db.query(VoterParticipation).filter(VoterParticipation.election_id==eid, VoterParticipation.voter_user_id==cur["user"].id).first()
    if part:
        return templates.TemplateResponse("voter_verified.html", {"request": request, "current": cur, "election": e, "already_voted": True, "part": part})
    profile = db.query(VoterProfile).filter(VoterProfile.user_id==cur["user"].id).first()
    return templates.TemplateResponse("voter_verify.html", {"request": request, "current": cur, "election": e, "profile": profile, "error": None, "success": None, "masked": profile.aadhaar_masked if profile else ""})

@app.post("/voter/verify/{eid}")
def voter_verify_post(request: Request, eid: int, aadhaar: str = Form(...), db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur or cur["user"].role != "VOTER":
        raise HTTPException(403)
    ip = request.client.host if request.client else "unknown"
    if is_rate_limited(f"verify:{ip}", max_req=15, window_sec=60):
        raise HTTPException(429, "Too many verification attempts")
    e = db.query(Election).filter(Election.id==eid).first()
    profile = db.query(VoterProfile).filter(VoterProfile.user_id==cur["user"].id).first()
    result = demo_provider.verify(aadhaar, db)
    if not result["success"]:
        audit(request, db, cur["user"], "aadhaar_verify_failed", "election", eid, result["reason"])
        return templates.TemplateResponse("voter_verify.html", {"request": request, "current": cur, "election": e, "profile": profile, "error": result["reason"], "success": None, "masked": profile.aadhaar_masked if profile else ""}, status_code=400)
    # check that verified user matches current user
    if result["user"].id != cur["user"].id:
        audit(request, db, cur["user"], "aadhaar_verify_failed", "election", eid, "Aadhaar belongs to another user")
        return templates.TemplateResponse("voter_verify.html", {"request": request, "current": cur, "election": e, "profile": profile, "error": "Aadhaar does not match logged-in voter", "success": None, "masked": profile.aadhaar_masked}, status_code=403)
    # check eligibility
    elig = db.query(VoterEligibility).filter(VoterEligibility.election_id==eid, VoterEligibility.voter_user_id==cur["user"].id).first()
    if not elig or not elig.is_eligible:
        audit(request, db, cur["user"], "aadhaar_verify_failed", "election", eid, "not eligible")
        return templates.TemplateResponse("voter_verify.html", {"request": request, "current": cur, "election": e, "profile": profile, "error": "You are not eligible for this election", "success": None, "masked": profile.aadhaar_masked}, status_code=403)
    # check already voted
    from app.models.models import VoterParticipation
    if db.query(VoterParticipation).filter(VoterParticipation.election_id==eid, VoterParticipation.voter_user_id==cur["user"].id).first():
        return templates.TemplateResponse("voter_verify.html", {"request": request, "current": cur, "election": e, "profile": profile, "error": "You have already voted in this election", "success": None}, status_code=400)
    # issue auth token
    try:
        token = issue_authorization(db, eid, cur["user"].id)
    except ValueError as ve:
        return templates.TemplateResponse("voter_verify.html", {"request": request, "current": cur, "election": e, "profile": profile, "error": str(ve), "success": None}, status_code=400)
    audit(request, db, cur["user"], "aadhaar_verify_success", "election", eid, "Demo verification")
    audit(request, db, cur["user"], "auth_issued", "election", eid, "token issued")
    # store token in session for later? We'll pass via hidden form via response
    # redirect to vote page with token in query? For demo, store in server session dict keyed by user+election
    # We will store hashed token in DB, but return plain token to template via query param securely via redirect with token as param (short-lived)
    # Instead render vote page directly with token
    candidates = db.query(Candidate).filter(Candidate.election_id==eid, Candidate.is_active==True).all()
    return templates.TemplateResponse("voter_vote.html", {"request": request, "current": cur, "election": e, "candidates": candidates, "auth_token": token, "error": None})

@app.post("/voter/cast/{eid}")
def voter_cast(request: Request, eid: int, candidate_id: int = Form(...), auth_token: str = Form(...), db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur or cur["user"].role != "VOTER":
        raise HTTPException(403)
    e = db.query(Election).filter(Election.id==eid).first()
    if not e:
        raise HTTPException(404)
    try:
        res = cast_vote(db, eid, cur["user"].id, auth_token, candidate_id)
    except ValueError as ve:
        msg = str(ve)
        audit(request, db, cur["user"], "vote_rejected", "election", eid, msg)
        candidates = db.query(Candidate).filter(Candidate.election_id==eid, Candidate.is_active==True).all()
        return templates.TemplateResponse("voter_vote.html", {"request": request, "current": cur, "election": e, "candidates": candidates, "auth_token": auth_token, "error": msg}, status_code=400)
    except Exception as ex:
        audit(request, db, cur["user"], "vote_failed", "election", eid, str(ex))
        raise HTTPException(500, str(ex))
    audit(request, db, cur["user"], "vote_cast", "election", eid, f"tx {res['tx_hash']}")
    # receipt page
    return templates.TemplateResponse("voter_receipt.html", {"request": request, "current": cur, "election": e, "receipt": res})

@app.get("/voter/results/{eid}", response_class=HTMLResponse)
def voter_results(request: Request, eid: int, db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur:
        return RedirectResponse(url="/login", status_code=302)
    e = db.query(Election).filter(Election.id==eid).first()
    if not e or e.status != "CLOSED":
        raise HTTPException(404, "Results not available")
    res = tally_results(db, eid)
    return templates.TemplateResponse("results.html", {"request": request, "current": cur, "election": e, "results": res})

# --- Auditor ---
@app.get("/auditor", response_class=HTMLResponse)
def auditor_home(request: Request, db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur or cur["user"].role != "AUDITOR":
        return RedirectResponse(url="/login", status_code=302)
    chain = validate_chain(db)
    blocks = db.query(LedgerBlock).order_by(LedgerBlock.block_index.desc()).limit(20).all()
    txs = db.query(LedgerTransaction).order_by(LedgerTransaction.id.desc()).limit(20).all()
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(20).all()
    from app.models.models import ValidatorNode
    vnodes = db.query(ValidatorNode).all()
    return templates.TemplateResponse("auditor.html", {"request": request, "current": cur, "chain": chain, "blocks": blocks, "txs": txs, "logs": logs, "vnodes": vnodes, "tamper_result": None})

@app.post("/auditor/verify")
def auditor_verify(request: Request, db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur or cur["user"].role != "AUDITOR":
        raise HTTPException(403)
    result = validate_chain(db)
    audit(request, db, cur["user"], "integrity_check", "ledger", None, json.dumps(result))
    blocks = db.query(LedgerBlock).order_by(LedgerBlock.block_index.desc()).limit(20).all()
    txs = db.query(LedgerTransaction).order_by(LedgerTransaction.id.desc()).limit(20).all()
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(20).all()
    from app.models.models import ValidatorNode
    vnodes = db.query(ValidatorNode).all()
    return templates.TemplateResponse("auditor.html", {"request": request, "current": cur, "chain": result, "blocks": blocks, "txs": txs, "logs": logs, "vnodes": vnodes, "tamper_result": None, "verify_result": result})

@app.post("/auditor/tamper-test")
def auditor_tamper(request: Request, db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur or cur["user"].role != "AUDITOR":
        raise HTTPException(403)
    result = tamper_test_clone(db)
    audit(request, db, cur["user"], "tamper_test", "ledger", None, json.dumps(result))
    chain = validate_chain(db)
    blocks = db.query(LedgerBlock).order_by(LedgerBlock.block_index.desc()).limit(20).all()
    txs = db.query(LedgerTransaction).order_by(LedgerTransaction.id.desc()).limit(20).all()
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(20).all()
    from app.models.models import ValidatorNode
    vnodes = db.query(ValidatorNode).all()
    return templates.TemplateResponse("auditor.html", {"request": request, "current": cur, "chain": chain, "blocks": blocks, "txs": txs, "logs": logs, "vnodes": vnodes, "tamper_result": result, "verify_result": chain})

@app.get("/auditor/block/{bid}", response_class=HTMLResponse)
def auditor_block(request: Request, bid: int, db: Session = Depends(get_db)):
    cur = get_current_user(request, db)
    if not cur or cur["user"].role != "AUDITOR":
        return RedirectResponse(url="/login", status_code=302)
    block = db.query(LedgerBlock).filter(LedgerBlock.block_index==bid).first()
    if not block:
        raise HTTPException(404)
    txs = db.query(LedgerTransaction).filter(LedgerTransaction.block_index==bid).all()
    return templates.TemplateResponse("block_detail.html", {"request": request, "current": cur, "block": block, "txs": txs})

@app.get("/api/chain/verify")
def api_verify(db: Session = Depends(get_db)):
    return validate_chain(db)

@app.get("/api/benchmark/latest")
def api_bench(db: Session = Depends(get_db)):
    from app.models.models import BenchmarkRun
    b = db.query(BenchmarkRun).order_by(BenchmarkRun.id.desc()).first()
    if not b:
        return {"exists": False}
    return {"exists": True, "details": json.loads(b.details_json) if b.details_json else {}, "throughput_sync": b.throughput_sync, "throughput_async": b.throughput_async}

@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    chain = validate_chain(db)
    return {"status": "ok", "chain_valid": chain.get("valid"), "height": chain.get("height")}

# Seed on startup handled via script, but ensure demo users exist on first run via separate init
