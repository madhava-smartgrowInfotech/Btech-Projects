"""Demo account so the product can be explored without registering."""
from app.auth import hash_password
from app.database import SessionLocal
from app.models import User

DEMO_EMAIL = "demo@carelens.ai"
DEMO_PASSWORD = "Demo@1234"

def ensure_demo_user() -> int:
    """Create the demo user if missing and return its id."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if not user:
            user = User(email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD))
            db.add(user)
            db.commit()
            db.refresh(user)
        return user.id
    finally:
        db.close()
