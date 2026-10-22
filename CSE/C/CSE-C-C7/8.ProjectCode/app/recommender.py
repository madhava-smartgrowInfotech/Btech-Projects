import json, joblib
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings

SKILL_ORDER = {"Beginner": 0, "Intermediate": 1, "Advanced": 2, "All levels": 1}

def skill_compat(learner_skill: str, course_skill: str) -> float:
    ls = SKILL_ORDER.get(learner_skill, 1)
    cs = SKILL_ORDER.get(course_skill, 1)
    d = abs(ls - cs)
    return {0: 1.0, 1: 0.6, 2: 0.3}.get(d, 0.3)

def course_text(c: Dict[str, Any]) -> str:
    return " ".join([str(c.get("title","")), str(c.get("description","")), str(c.get("topic","")),
                     str(c.get("category","")), str(c.get("tags","")), str(c.get("skill_level",""))])

def profile_text(p: Dict[str, Any]) -> str:
    return " ".join([str(p.get("interests","")), str(p.get("preferred_topics","")),
                     str(p.get("goals","")), str(p.get("course_preferences","")),
                     str(p.get("education","")), str(p.get("skill_level",""))])

def content_scores(profile: Dict[str, Any], courses: List[Dict[str, Any]]):
    docs = [profile_text(profile)] + [course_text(c) for c in courses]
    vec = TfidfVectorizer(stop_words="english", max_features=2000)
    X = vec.fit_transform(docs)
    sims = cosine_similarity(X[0:1], X[1:]).flatten()
    return sims

def topic_interest_score(profile: Dict[str, Any], course: Dict[str, Any]) -> float:
    blob = (profile.get("interests","") + " " + profile.get("preferred_topics","") + " " + profile.get("goals","")).lower()
    ct = (course.get("topic","") + " " + course.get("category","") + " " + course.get("tags","") + " " + course.get("title","")).lower()
    keys = [w.strip() for w in blob.replace(",", " ").split() if len(w.strip()) > 2]
    if not keys:
        return 0.5
    hit = sum(1 for k in set(keys) if k in ct)
    return min(1.0, hit / max(3, len(set(keys)) * 0.5))

def behavioral_boost(user_id: int, course_id: str, db) -> float:
    from app.models import Interaction
    rows = db.query(Interaction).filter(Interaction.user_id == user_id).all()
    if not rows:
        return 0.0
    w = {"view": 0.05, "open": 0.06, "start": 0.12, "content": 0.10, "quiz": 0.14, "forum": 0.10, "save": 0.08, "complete": 0.20, "dismiss": -0.25}
    s = 0.0
    for r in rows:
        if r.course_id == course_id:
            s += w.get(r.event_type, 0.03) * (r.value or 1.0)
    return max(-0.3, min(0.35, s))

def engagement_level(db, user_id: int) -> Dict[str, Any]:
    from app.models import Interaction
    from datetime import datetime, timedelta
    rows = db.query(Interaction).filter(Interaction.user_id == user_id).order_by(Interaction.created_at.desc()).limit(200).all()
    total = len(rows)
    recent = sum(1 for r in rows if r.event_type in ("view","open","start","content","quiz","forum"))
    quizzes = sum(1 for r in rows if r.event_type == "quiz")
    forums = sum(1 for r in rows if r.event_type == "forum")
    completes = sum(1 for r in rows if r.event_type == "complete")
    if total == 0:
        return {"label": "Getting started", "score": 0.25, "total": 0, "quizzes": 0, "forums": 0, "completes": 0}
    score = min(1.0, 0.25 + recent * 0.04 + quizzes * 0.03 + completes * 0.08)
    label = "Getting started" if score < 0.4 else ("Steady learner" if score < 0.7 else "Highly engaged")
    if any(r.event_type == "dismiss" for r in rows[:5]) and score < 0.45:
        label = "Needs a nudge"
    return {"label": label, "score": round(float(score),3), "total": total, "quizzes": quizzes, "forums": forums, "completes": completes}

def load_ml_bundle():
    mdir = Path(settings.models_dir)
    bundle = {}
    for k, f in [("scaler","scaler.joblib"),("model","xgb_model.joblib"),("features","feature_cols.joblib"),("uplift","uplift.joblib"),("opecfg","ope.joblib")]:
        p = mdir / f
        if p.exists():
            try:
                bundle[k] = joblib.load(p)
            except Exception:
                bundle[k] = None
    # tfidf catalog matrix
    tp = mdir / "tfidf.joblib"
    if tp.exists():
        try:
            bundle["tfidf"] = joblib.load(tp)
        except Exception:
            bundle["tfidf"] = None
    return bundle

def learner_state_vector(profile: Dict[str, Any], eng: Dict[str, Any]) -> Dict[str, float]:
    return {
        "cum_clicks": float(eng.get("total", 0)),
        "recent_clicks": float(min(eng.get("total",0), 20)),
        "quiz_count": float(eng.get("quizzes", 0)),
        "forum_count": float(eng.get("forums", 0)),
        "completions": float(eng.get("completes", 0)),
        "engagement": float(eng.get("score", 0.25)),
        "weekly_hours": float(profile.get("weekly_hours", 5.0) or 5.0),
        "skill_code": float(SKILL_ORDER.get(profile.get("skill_level","Beginner"), 0)),
    }

def predict_success(bundle, state: Dict[str, float]):
    try:
        feats = bundle.get("features") or ["cum_clicks","recent_clicks","quiz_count","forum_count","completions","engagement","weekly_hours","skill_code"]
        X = np.array([[state.get(f, 0.0) for f in feats]], dtype=float)
        scaler = bundle.get("scaler")
        if scaler is not None:
            X = scaler.transform(X)
        model = bundle.get("model")
        if model is None:
            return 0.55, {"note": "baseline"}
        p = float(model.predict_proba(X)[0][1])
        imp = {}
        try:
            if hasattr(model, "feature_importances_"):
                fi = model.feature_importances_
                imp = {f: round(float(v),4) for f, v in zip(feats, fi)}
        except Exception:
            pass
        return p, imp
    except Exception:
        return 0.55, {}

def uplift_scores(bundle, state: Dict[str, float]):
    actions = ["quiz","content","forum","homepage","continue_course"]
    up = bundle.get("uplift") if bundle else None
    feats = bundle.get("features") if bundle else None
    out = {}
    try:
        if up and feats:
            X = np.array([[state.get(f, 0.0) for f in feats]], dtype=float)
            scaler = bundle.get("scaler")
            if scaler is not None:
                Xs = scaler.transform(X)
            else:
                Xs = X
            for a in actions:
                if a in up and isinstance(up[a], dict) and up[a].get("t1") is not None:
                    p1 = float(up[a]["t1"].predict_proba(Xs)[0][1])
                    p0 = float(up[a]["t0"].predict_proba(Xs)[0][1])
                    out[a] = round(p1 - p0, 4)
                else:
                    out[a] = 0.0
        else:
            # predictive fallback ranking: heuristic from state
            out = {
                "quiz": round(0.02 + 0.05 * (1 - state.get("engagement", .5)) + 0.01 * min(state.get("quiz_count",0),5), 4),
                "content": round(0.03 + 0.03 * (1 - state.get("engagement", .5)), 4),
                "forum": round(0.015 + 0.02 * (1 - min(state.get("forum_count",0)/5,1)), 4),
                "homepage": round(0.01, 4),
                "continue_course": round(0.04 + 0.04 * state.get("engagement", .5), 4),
            }
    except Exception:
        out = {a: 0.0 for a in actions}
    return out

ACTION_LABEL = {
    "quiz": "Complete a quiz",
    "content": "Review learning content",
    "forum": "Engage with discussion",
    "homepage": "Visit course resources",
    "continue_course": "Continue your learning path",
}

def rank_courses(profile, courses, db, user_id, bundle, top_n=8):
    sims = content_scores(profile, courses)
    eng = engagement_level(db, user_id)
    state = learner_state_vector(profile, eng)
    p_success, feat_imp = predict_success(bundle, state)
    upl = uplift_scores(bundle, state)
    ranked = []
    for i, c in enumerate(courses):
        cs = float(sims[i]) if len(sims) > i else 0.0
        sk = skill_compat(profile.get("skill_level","Beginner"), c.get("skill_level","Beginner"))
        ti = topic_interest_score(profile, c)
        beh = behavioral_boost(user_id, c.get("id",""), db)
        goal = 0.7 if any(g.strip().lower() in (c.get("title","")+c.get("description","")+c.get("tags","")).lower() for g in (profile.get("goals","").split(",") if profile.get("goals") else []) if g.strip()) else 0.4
        rating_f = (float(c.get("rating", 4.5)) - 3.5) / 1.5
        rating_f = max(0, min(1, rating_f))
        score = 0.30*cs + 0.15*sk + 0.15*ti + 0.12*p_success + 0.10*(0.5+beh) + 0.08*goal + 0.05*rating_f + 0.05*eng["score"]
        score = round(float(max(0, min(1, score))), 4)
        reasons = []
        if cs > 0.08: reasons.append(f"Matches your interests ({', '.join((c.get('tags','').split(',')[:2]))})")
        elif ti > 0.3: reasons.append(f"Aligned with your topic preferences in {c.get('topic','')}")
        else: reasons.append(f"Broadens your {c.get('category','')} knowledge")
        if sk >= 0.9: reasons.append("Fits your current skill level")
        elif sk < 0.6: reasons.append("Stretches you slightly beyond your level" if SKILL_ORDER.get(c.get('skill_level','Beginner'),0) > SKILL_ORDER.get(profile.get('skill_level','Beginner'),0) else "A comfortable refresher for your level")
        if beh > 0.05: reasons.append("You have engaged with similar material before")
        if p_success > 0.6: reasons.append(f"High estimated completion likelihood ({p_success:.0%})")
        best_act = max(upl, key=lambda k: upl[k]) if upl else "continue_course"
        est_benefit = round(float(upl.get(best_act, 0.0)), 4)
        ranked.append({"course": c, "score": score, "content_sim": round(float(cs),4),
                        "skill_compat": round(float(sk),3), "topic_fit": round(float(ti),3),
                        "success_prob": round(float(p_success),4), "behavior": round(float(beh),4),
                        "est_benefit": est_benefit, "suggested_action": best_act,
                        "suggested_action_label": ACTION_LABEL.get(best_act, best_act),
                        "explanation": "; ".join(reasons[:3])})
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:top_n], {"engagement": eng, "p_success": round(float(p_success),4), "feat_imp": feat_imp, "uplift": upl, "state": state}
