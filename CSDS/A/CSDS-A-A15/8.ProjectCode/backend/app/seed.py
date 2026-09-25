"""Creates a demo login so the dashboard can be explored immediately.

Run:  python -m app.seed
"""
from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.models import User

DEMO_EMAIL = "demo@visionforge.ai"
DEMO_PASSWORD = "demo1234"


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if existing:
            print(f"Demo user already exists: {DEMO_EMAIL}")
            return
        user = User(
            name="Demo Inspector",
            email=DEMO_EMAIL,
            hashed_password=hash_password(DEMO_PASSWORD),
            role="inspector",
        )
        db.add(user)
        db.commit()
        print(f"Created demo user -> email: {DEMO_EMAIL}  password: {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
