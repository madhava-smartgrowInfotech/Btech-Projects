import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.models.models import User, VoterProfile, Election, Candidate, VoterEligibility, ValidatorNode
from app.security.auth import hash_password
from app.security.crypto import hash_aadhaar, mask_aadhaar
from app.identity.verhoeff import generate_valid_aadhaar
from app.ledger.ledger import init_validators, create_genesis_block

DEMO_USERS = [
    ("admin", "Admin@123", "ADMIN", "Aegis Administrator"),
    ("auditor", "Audit@123", "AUDITOR", "Aegis Auditor"),
]

VOTER_NAMES = [
    "Aarav Sharma", "Vivaan Patel", "Aditya Verma", "Vihaan Singh", "Arjun Kumar",
    "Sai Reddy", "Reyansh Gupta", "Ayaan Khan", "Krishna Nair", "Ishaan Mehta",
    "Saanvi Desai", "Ananya Rao", "Diya Joshi", "Pari Kapoor", "Aadhya Iyer",
    "Navya Menon", "Myra Bhatt", "Sara Kulkarni", "Ira Pillai", "Kiara Shah",
]

CANDIDATES_POOL = [
    ("Aarohi Sen", "People's Unity Front", "Focus on education and healthcare access for all.", "Universal education, affordable healthcare, community development."),
    ("Rohan Deshmukh", "National Progress Alliance", "Driving innovation and sustainable growth.", "Green energy, startup ecosystem, infrastructure modernization."),
    ("Meera Krishnan", "Civic Harmony Collective", "Inclusive governance and social equity.", "Social welfare, gender equality, participatory governance."),
    ("Vikram Bhatia", "Future Vision Party", "Transparent administration and digital governance.", "E-governance, anti-corruption, youth employment."),
]

def seed():
    init_db()
    db: Session = SessionLocal()
    try:
        # check if already seeded
        existing_admin = db.query(User).filter(User.username=="admin").first()
        if existing_admin:
            print("Already seeded, skipping")
            return

        # create demo admin/auditor
        for uname, pwd, role, dname in DEMO_USERS:
            u = User(username=uname, password_hash=hash_password(pwd), role=role, display_name=dname, email=f"{uname}@aegisballot.local")
            db.add(u)
        db.commit()

        # create voters
        voters = []
        for idx, name in enumerate(VOTER_NAMES):
            uname = f"voter{idx+1}"
            pwd = f"Voter@{idx+1:02d}pass"
            u = User(username=uname, password_hash=hash_password(pwd), role="VOTER", display_name=name, email=f"{uname}@example.local")
            db.add(u)
            db.flush()
            aadhaar = generate_valid_aadhaar()
            # ensure not duplicate (hash uniqueness)
            vp = VoterProfile(user_id=u.id, full_name=name, aadhaar_hash=hash_aadhaar(aadhaar), aadhaar_masked=mask_aadhaar(aadhaar), dob="1995-01-01", address=f"Demo Address {idx+1}, Demo City")
            db.add(vp)
            # store plain for demo display? We'll create a file synthetic_identities.json for demo credentials
            voters.append((uname, pwd, aadhaar, name))
            # keep association
        db.commit()

        # save synthetic identities for HOW_TO_RUN
        import json, pathlib
        pathlib.Path("data/synthetic_identities.json").write_text(json.dumps([{"username": u, "password": p, "aadhaar": a, "name": n, "masked": mask_aadhaar(a)} for u,p,a,n in voters], indent=2))

        # create elections - e2 initially OPEN to allow seeding votes, then close after
        now = datetime.utcnow()
        e1 = Election(title="Campus Council Election 2026", description="Annual campus council election to elect student representatives.", start_time=now - timedelta(days=1), end_time=now + timedelta(days=7), status="OPEN", created_by=1)
        e2 = Election(title="Community Welfare Board 2026", description="Election for community welfare board members.", start_time=now - timedelta(days=2), end_time=now - timedelta(hours=1), status="OPEN", created_by=1)
        db.add_all([e1,e2])
        db.commit()
        db.refresh(e1)
        db.refresh(e2)

        # candidates for e1
        for name, party, desc, mani in CANDIDATES_POOL:
            c = Candidate(election_id=e1.id, name=name, party=party, description=desc, manifesto=mani, is_active=True)
            db.add(c)
        # candidates for e2 (fewer)
        for name, party, desc, mani in CANDIDATES_POOL[:3]:
            c = Candidate(election_id=e2.id, name=name, party=party, description=desc, manifesto=mani, is_active=True)
            db.add(c)
        db.commit()

        # eligibility: all voters eligible for both
        all_voters = db.query(User).filter(User.role=="VOTER").all()
        for e in [e1, e2]:
            for v in all_voters:
                db.add(VoterEligibility(election_id=e.id, voter_user_id=v.id, is_eligible=True))
        db.commit()

        init_validators(db)
        create_genesis_block(db)

        # create some votes for e2 to demonstrate results (8 votes)
        from app.services.voting_service import issue_authorization, cast_vote
        from app.models.models import Candidate as CandModel
        e2_cands = db.query(CandModel).filter(CandModel.election_id==e2.id).all()
        for i, v in enumerate(all_voters[:8]):
            try:
                tok = issue_authorization(db, e2.id, v.id)
                chosen = e2_cands[i % len(e2_cands)].id
                cast_vote(db, e2.id, v.id, tok, chosen)
            except Exception as ex:
                print(f"seed vote failed {v.username}: {ex}")
        # close e2 after seeding
        e2.status = "CLOSED"
        db.commit()

        print("Seeding complete")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
