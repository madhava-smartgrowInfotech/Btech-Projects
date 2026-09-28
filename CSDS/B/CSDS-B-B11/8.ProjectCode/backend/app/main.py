from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from .auth import hash_password
from .config import DEMO_EMAIL, DEMO_PASSWORD, FRONTEND_PORT, GEMINI_API_KEY, MODEL_PATH
from .db import Profile, SessionLocal, TargetHistory, User, WeightLog, init_db
from .routes import auth, foods, logs, plans, profile, progress, recipes
from .services.foods import food_db
from .services.targets import compute_targets

# Sample account so the product can be tried immediately (clearly labelled as sample data).
DEMO_PROFILE = dict(age=28, gender="female", height_cm=164, weight_kg=66, activity="moderate", diet_type="vegetarian",
                    cuisine="both", allergies=["peanut"], conditions=[], goal="lose")


def ensure_demo_user():
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == DEMO_EMAIL)):
            return
        u = User(email=DEMO_EMAIL, name="Sample User", password_hash=hash_password(DEMO_PASSWORD))
        db.add(u)
        db.flush()
        now = datetime.utcnow()
        db.add(Profile(user_id=u.id, adaptive_adjust=0.0, last_recalc_at=now, **DEMO_PROFILE))
        t = compute_targets(DEMO_PROFILE)
        db.add(TargetHistory(user_id=u.id, as_of=date.today(), kcal=t["kcal"], weight_kg=DEMO_PROFILE["weight_kg"],
                             reason="Initial target from your profile (sample account)."))
        db.add(WeightLog(user_id=u.id, date=date.today(), weight_kg=DEMO_PROFILE["weight_kg"], created_at=now - timedelta(seconds=1)))
        db.commit()


@asynccontextmanager
async def lifespan(_app):
    init_db()
    food_db()  # load the food database and swap model once
    ensure_demo_user()
    yield


app = FastAPI(title="NutriSense API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[f"http://localhost:{FRONTEND_PORT}", f"http://127.0.0.1:{FRONTEND_PORT}"],
                   allow_methods=["*"], allow_headers=["*"])
for r in (auth, profile, plans, recipes, foods, logs, progress):
    app.include_router(r.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "foods": len(food_db().foods), "swap_model": MODEL_PATH.exists(),
            "gemini_configured": bool(GEMINI_API_KEY)}
