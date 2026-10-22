"""Create the demo account and a few real consultations (run through the actual RAG pipeline)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal, init_db  # noqa: E402
from app.demo import DEMO_EMAIL, DEMO_PASSWORD, ensure_demo_user  # noqa: E402
from app.models import Consultation  # noqa: E402

SAMPLES = [
    "I have high fever, headache and body pain since two days",
    "Persistent dry cough, sore throat and runny nose",
    "Itchy red eyes with watery discharge in the morning",
    "I have severe chest pain and difficulty breathing",
    "Frequent urination, excessive thirst and tiredness",
]

def main():
    init_db()
    uid = ensure_demo_user()
    db = SessionLocal()
    try:
        if db.query(Consultation).filter(Consultation.user_id == uid).count():
            print(f"Demo account {DEMO_EMAIL} already has consultations - nothing to seed.")
            return
        from app.rag.pipeline import get_pipeline
        pipe = get_pipeline()
        for q in SAMPLES:
            r = pipe.answer(q)
            db.add(Consultation(
                user_id=uid, symptom_query=q, generated_response=r["answer"], top_condition=r["top_condition"],
                retrieved_evidence=json.dumps(r["evidence"]), retrieval_score=float(r["retrieval_score"]),
                safety_flag=r["safety_flag"],
            ))
        db.commit()
        print(f"Seeded {len(SAMPLES)} consultations for {DEMO_EMAIL} (password: {DEMO_PASSWORD}).")
    finally:
        db.close()

if __name__ == "__main__":
    main()
