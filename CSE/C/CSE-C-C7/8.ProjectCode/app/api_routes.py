import json
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Profile, Course, Interaction, RecommendationLog, AuthToken
from app.schemas import RegisterIn, LoginIn, ProfileIn, InteractionIn
from app.security import hash_password, verify_password, new_token
from app.recommender import rank_courses, engagement_level, learner_state_vector, predict_success, uplift_scores, ACTION_LABEL, load_ml_bundle
from app.config import settings

router = APIRouter()
_bundle = None
def bundle():
    global _bundle
    if _bundle is None:
        _bundle = load_ml_bundle()
    return _bundle

def get_current_user(request: Request, db: Session):
    tok = request.cookies.get("lpq_token") or request.headers.get("X-Token", "")
    if not tok and "authorization" in [k.lower() for k in request.headers.keys()]:
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            tok = auth[7:]
    if not tok:
        return None
    at = db.query(AuthToken).filter(AuthToken.token == tok).first()
    if not at:
        return None
    return db.query(User).filter(User.id == at.user_id).first()

def require_user(request: Request, db: Session = Depends(get_db)):
    u = get_current_user(request, db)
    if not u:
        raise HTTPException(401, "Please sign in")
    return u

def profile_dict(p):
    if not p: return {"education":"","skill_level":"Beginner","interests":"","preferred_topics":"","learning_style":"Self-paced","goals":"","course_preferences":"","weekly_hours":5.0,"age_band":"25-34","gender":"Prefer not to say"}
    return {"education":p.education or "","skill_level":p.skill_level or "Beginner","interests":p.interests or "","preferred_topics":p.preferred_topics or "","learning_style":p.learning_style or "Self-paced","goals":p.goals or "","course_preferences":p.course_preferences or "","weekly_hours":p.weekly_hours or 5.0,"age_band":p.age_band or "25-34","gender":p.gender or "Prefer not to say"}

def course_dict(c):
    return {"id":c.id,"title":c.title,"category":c.category,"topic":c.topic,"skill_level":c.skill_level,"description":c.description,"duration_hours":c.duration_hours,"difficulty":c.difficulty,"prerequisites":c.prerequisites,"outcomes":c.outcomes,"tags":c.tags,"resource_type":c.resource_type,"rating":c.rating}

@router.post("/api/auth/register")
def register(body: RegisterIn, response: Response, db: Session = Depends(get_db)):
    if body.password != body.confirm_password:
        raise HTTPException(400, "Passwords do not match")
    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(400, "Email already registered")
    u = User(name=body.name.strip(), email=body.email.lower().strip(), password_hash=hash_password(body.password))
    db.add(u); db.commit(); db.refresh(u)
    db.add(Profile(user_id=u.id)); db.commit()
    t = new_token(); db.add(AuthToken(user_id=u.id, token=t)); db.commit()
    response.set_cookie("lpq_token", t, httponly=True, samesite="lax", max_age=72*3600)
    return {"ok": True, "token": t, "user": {"id": u.id, "name": u.name, "email": u.email}}

@router.post("/api/auth/login")
def login(body: LoginIn, response: Response, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == body.email.lower()).first()
    if not u or not verify_password(body.password, u.password_hash):
        raise HTTPException(401, "Invalid email or password")
    t = new_token(); db.add(AuthToken(user_id=u.id, token=t)); db.commit()
    response.set_cookie("lpq_token", t, httponly=True, samesite="lax", max_age=72*3600)
    return {"ok": True, "token": t, "user": {"id": u.id, "name": u.name, "email": u.email}}

@router.post("/api/auth/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    tok = request.cookies.get("lpq_token", "")
    if tok:
        db.query(AuthToken).filter(AuthToken.token == tok).delete(); db.commit()
    response.delete_cookie("lpq_token")
    return {"ok": True}

@router.get("/api/me")
def me(request: Request, db: Session = Depends(get_db)):
    u = get_current_user(request, db)
    if not u: return {"user": None}
    return {"user": {"id": u.id, "name": u.name, "email": u.email}}

@router.get("/api/profile")
def get_profile(request: Request, db: Session = Depends(get_db)):
    u = require_user(request, db)
    p = db.query(Profile).filter(Profile.user_id == u.id).first()
    return profile_dict(p)

@router.put("/api/profile")
def put_profile(body: ProfileIn, request: Request, db: Session = Depends(get_db)):
    u = require_user(request, db)
    p = db.query(Profile).filter(Profile.user_id == u.id).first()
    if not p:
        p = Profile(user_id=u.id); db.add(p)
    for k in ["education","skill_level","interests","preferred_topics","learning_style","goals","course_preferences","weekly_hours","age_band","gender"]:
        setattr(p, k, getattr(body, k))
    p.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "profile": profile_dict(p)}

@router.get("/api/courses")
def list_courses(q: str = "", category: str = "", level: str = "", db: Session = Depends(get_db)):
    rows = db.query(Course).all()
    out = [course_dict(c) for c in rows]
    if q:
        ql = q.lower()
        out = [c for c in out if ql in (c["title"]+c["description"]+c["tags"]+c["topic"]+c["category"]).lower()]
    if category: out = [c for c in out if c["category"] == category]
    if level: out = [c for c in out if c["skill_level"] == level]
    return {"courses": out, "count": len(out)}

@router.get("/api/courses/{course_id}")
def course_detail(course_id: str, request: Request, db: Session = Depends(get_db)):
    c = db.query(Course).filter(Course.id == course_id).first()
    if not c: raise HTTPException(404, "Course not found")
    d = course_dict(c)
    u = get_current_user(request, db)
    expl = "Popular across learners."
    if u:
        p = profile_dict(db.query(Profile).filter(Profile.user_id == u.id).first())
        courses = [course_dict(x) for x in db.query(Course).all()]
        ranked, _ = rank_courses(p, courses, db, u.id, bundle(), top_n=50)
        for r in ranked:
            if r["course"]["id"] == course_id:
                expl = r["explanation"]; d.update({"match_score": r["score"], "success_prob": r["success_prob"], "est_benefit": r["est_benefit"], "suggested_action": r["suggested_action_label"]})
                break
    d["explanation"] = expl
    return d

@router.get("/api/recommendations")
def recommendations(request: Request, top_n: int = 8, db: Session = Depends(get_db)):
    u = require_user(request, db)
    p = profile_dict(db.query(Profile).filter(Profile.user_id == u.id).first())
    courses = [course_dict(x) for x in db.query(Course).all()]
    ranked, ctx = rank_courses(p, courses, db, u.id, bundle(), top_n=top_n)
    for r in ranked:
        db.add(RecommendationLog(user_id=u.id, course_id=r["course"]["id"], score=r["score"], explanation=r["explanation"]))
    db.commit()
    return {"recommendations": ranked, "engagement": ctx["engagement"], "success_probability": ctx["p_success"], "uplift": ctx["uplift"], "feature_contrib": ctx["feat_imp"]}

@router.post("/api/recommendations/refresh")
def refresh_rec(request: Request, db: Session = Depends(get_db)):
    global _bundle
    _bundle = load_ml_bundle()
    return recommendations(request, top_n=8, db=db)

@router.post("/api/interactions")
def record_interaction(body: InteractionIn, request: Request, db: Session = Depends(get_db)):
    u = require_user(request, db)
    allowed = {"view","open","start","quiz","content","forum","complete","dismiss","save"}
    if body.event_type not in allowed:
        raise HTTPException(400, f"event_type must be one of {sorted(allowed)}")
    db.add(Interaction(user_id=u.id, course_id=body.course_id or "", event_type=body.event_type, value=body.value))
    db.commit()
    return {"ok": True}

@router.get("/api/activity")
def activity(request: Request, limit: int = 30, db: Session = Depends(get_db)):
    u = require_user(request, db)
    rows = db.query(Interaction).filter(Interaction.user_id == u.id).order_by(Interaction.created_at.desc()).limit(limit).all()
    return {"events": [{"course_id": r.course_id, "event_type": r.event_type, "value": r.value, "at": r.created_at.isoformat()} for r in rows]}

@router.get("/api/history")
def history(request: Request, db: Session = Depends(get_db)):
    u = require_user(request, db)
    rows = db.query(RecommendationLog).filter(RecommendationLog.user_id == u.id).order_by(RecommendationLog.created_at.desc()).limit(40).all()
    return {"history": [{"course_id": r.course_id, "score": r.score, "explanation": r.explanation, "at": r.created_at.isoformat()} for r in rows]}

@router.get("/api/learning-path")
def learning_path(request: Request, db: Session = Depends(get_db)):
    u = require_user(request, db)
    p = profile_dict(db.query(Profile).filter(Profile.user_id == u.id).first())
    courses = [course_dict(x) for x in db.query(Course).all()]
    ranked, ctx = rank_courses(p, courses, db, u.id, bundle(), top_n=12)
    # order: beginner-friendly first then by score -> staged path
    order = {"Beginner": 0, "All levels": 0, "Intermediate": 1, "Advanced": 2}
    path = sorted(ranked, key=lambda r: (order.get(r["course"]["skill_level"], 1), -r["score"]))[:6]
    steps = []
    for i, r in enumerate(path, 1):
        steps.append({"step": i, "course": r["course"], "score": r["score"], "why": r["explanation"],
                      "action": r["suggested_action_label"], "est_benefit": r["est_benefit"]})
    best_act = max(ctx["uplift"], key=lambda k: ctx["uplift"][k]) if ctx.get("uplift") else "continue_course"
    return {"steps": steps, "engagement": ctx["engagement"], "next_action": ACTION_LABEL.get(best_act, best_act), "next_action_key": best_act}

@router.get("/api/insights")
def insights(request: Request, db: Session = Depends(get_db)):
    u = require_user(request, db)
    p = profile_dict(db.query(Profile).filter(Profile.user_id == u.id).first())
    eng = engagement_level(db, u.id)
    state = learner_state_vector(p, eng)
    ps, contrib = predict_success(bundle(), state)
    upl = uplift_scores(bundle(), state)
    rows = db.query(Interaction).filter(Interaction.user_id == u.id).all()
    by_type = {}
    for r in rows: by_type[r.event_type] = by_type.get(r.event_type, 0) + 1
    strengths, attention = [], []
    if by_type.get("quiz", 0) >= 3: strengths.append("Consistent quiz practice")
    if by_type.get("complete", 0) >= 1: strengths.append("Course completion momentum")
    if by_type.get("forum", 0) >= 2: strengths.append("Active peer discussion")
    if not strengths: strengths.append("Fresh start — every expert was once a beginner")
    if by_type.get("quiz", 0) < 2: attention.append("Try a short quiz to lock in knowledge")
    if by_type.get("forum", 0) < 1: attention.append("Join one discussion to deepen understanding")
    if eng["score"] < 0.4: attention.append("Short daily reviews will rebuild momentum")
    best = max(upl, key=lambda k: upl[k]) if upl else "continue_course"
    trend = [{"label": f"Event {i+1}", "count": 1} for i in range(min(len(rows), 20))]
    return {"engagement": eng, "success_probability": round(float(ps),4), "risk": round(float(1-ps),4),
            "contributing_features": contrib, "uplift": upl, "recommended_action": ACTION_LABEL.get(best, best),
            "recommended_action_key": best, "strengths": strengths, "attention": attention,
            "by_type": by_type, "state": state}

@router.get("/api/metrics")
def metrics():
    p = Path(settings.artifacts_dir) / "metrics" / "model_metrics.json"
    if not p.exists():
        raise HTTPException(503, "Model artifacts not ready. Run: python scripts/train_pipeline.py")
    return json.loads(p.read_text())

@router.get("/api/fairness")
def fairness():
    p = Path(settings.artifacts_dir) / "metrics" / "model_metrics.json"
    if not p.exists():
        raise HTTPException(503, "Model artifacts not ready.")
    m = json.loads(p.read_text())
    return {"fairness": m.get("fairness", {}), "note": "Audit only: transparent reporting, not a claim of perfect fairness."}

@router.get("/api/health")
def health():
    p = Path(settings.artifacts_dir) / "metrics" / "model_metrics.json"
    return {"ok": True, "models_ready": p.exists(), "app": "LearnPathIQ"}
