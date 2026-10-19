from sqlalchemy.orm import Session
from datetime import datetime
from app.models.models import Election, Candidate, VoterProfile, VoterEligibility, User
from app.models.models import ElectionStatus

def create_election(db: Session, title, description, start_time, end_time, created_by):
    e = Election(title=title, description=description, start_time=start_time, end_time=end_time, status=ElectionStatus.DRAFT.value, created_by=created_by)
    db.add(e)
    db.commit()
    db.refresh(e)
    return e

def update_election_status(db: Session, election_id: int, status: str):
    e = db.query(Election).filter(Election.id == election_id).first()
    if e:
        e.status = status
        db.commit()
        db.refresh(e)
    return e

def add_candidate(db: Session, election_id: int, name, party, description, manifesto):
    c = Candidate(election_id=election_id, name=name, party=party, description=description, manifesto=manifesto)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c
