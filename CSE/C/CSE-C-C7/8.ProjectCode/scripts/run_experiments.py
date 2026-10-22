"""
Extra measurements for the documentation set. Everything is written to experiments/*.json;
nothing is typed in by hand later.

    python scripts/run_experiments.py            # run from 8.ProjectCode with the project .venv

1. seed_study     - the shipped training pipeline re-run for 6 data/split seeds (artifacts are NOT overwritten)
2. ceiling        - same pipeline, but with the hidden assessment score added as a feature (upper bound on what
                    the label noise allows)
3. recsys_eval    - 10 hand-written learner personas, expected categories fixed BEFORE ranking: precision@k and
                    MRR for popularity, content-only and the hybrid ranker; leave-one-component-out ablation
4. feedback_loop  - cold-start vs after-interaction ranking for one persona (does behaviour change the ranking?)
5. action_scores  - how much the suggested action and the success probability vary across learners
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
EXP = os.path.join(ROOT, "experiments")
os.makedirs(EXP, exist_ok=True)

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, f1_score, accuracy_score, brier_score_loss
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

import train_pipeline as tp  # noqa: E402  (module import creates folders only; train_eval() is never called)


def dump(name, obj):
    with open(os.path.join(EXP, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    print("wrote", name)


# ------------------------------------------------------------------ 1 + 2: seed study and ceiling
def fit_eval(df, features, seed):
    tr, va, te = tp.split_learners(df)
    Xtr, ytr = tr[features].values, tr["success"].values
    Xva, yva = va[features].values, va["success"].values
    Xte, yte = te[features].values, te["success"].values
    sc = StandardScaler().fit(Xtr)
    A, V, T = sc.transform(Xtr), sc.transform(Xva), sc.transform(Xte)
    models = {
        "logistic_regression": LogisticRegression(max_iter=1000),
        "random_forest": RandomForestClassifier(n_estimators=200, random_state=seed, n_jobs=-1),
        "xgboost": XGBClassifier(n_estimators=300, max_depth=5, learning_rate=0.05, subsample=0.9, colsample_bytree=0.9,
                                 eval_metric="logloss", random_state=seed, n_jobs=-1),
    }
    out = {}
    for k, m in models.items():
        m.fit(A, ytr)
        pv = m.predict_proba(V)[:, 1]
        p = m.predict_proba(T)[:, 1]
        pred = (p >= 0.5).astype(int)
        out[k] = {"val_auc": float(roc_auc_score(yva, pv)), "test_auc": float(roc_auc_score(yte, p)), "accuracy": float(accuracy_score(yte, pred)),
                  "f1": float(f1_score(yte, pred, zero_division=0)), "brier": float(brier_score_loss(yte, p))}
    sel = max(out, key=lambda k: out[k]["val_auc"])
    return out, sel, {"train": int(len(tr)), "val": int(len(va)), "test": int(len(te)),
                      "train_learners": int(tr.learner_id.nunique()), "test_learners": int(te.learner_id.nunique()),
                      "positive_rate_test": float(te["success"].mean())}


def seed_study():
    runs = []
    for seed in (42, 1, 2, 3, 4, 5):
        t0 = time.time()
        tp.rng = np.random.RandomState(seed)
        tp.SEED = seed
        df, _ = tp.acquire_data()
        res, sel, sizes = fit_eval(df, tp.FEATURES, seed)
        runs.append({"seed": seed, "selected": sel, "models": res, "sizes": sizes, "seconds": round(time.time() - t0, 1)})
        print("seed", seed, sel, {k: round(v["test_auc"], 4) for k, v in res.items()})
    summary = {}
    for k in runs[0]["models"]:
        for met in ("test_auc", "f1", "accuracy", "brier"):
            v = np.array([r["models"][k][met] for r in runs])
            summary.setdefault(k, {})[met] = {"mean": float(v.mean()), "std": float(v.std(ddof=1)), "min": float(v.min()), "max": float(v.max())}
    sel_counts = {}
    for r in runs:
        sel_counts[r["selected"]] = sel_counts.get(r["selected"], 0) + 1
    dump("seed_study.json", {"seeds": [r["seed"] for r in runs], "runs": runs, "summary": summary, "selected_counts": sel_counts,
                             "note": "seed 42 is the shipped configuration; the other five re-draw the synthetic data and the learner split"})

    # ceiling: add the (hidden) assessment score
    tp.rng = np.random.RandomState(42)
    tp.SEED = 42
    df, _ = tp.acquire_data()
    res, sel, _ = fit_eval(df, tp.FEATURES + ["assess_score"], 42)
    base, _, _ = fit_eval(df, tp.FEATURES, 42)
    dump("ceiling.json", {"with_assess_score": res, "shipped_features": base,
                          "note": "assess_score drives the synthetic label but is not an observable feature in the app; this is an upper bound on the label noise"})
    # label balance and per-feature signal
    corr = {f: float(np.corrcoef(df[f], df["success"])[0, 1]) for f in tp.FEATURES}
    dump("data_profile.json", {"rows": int(len(df)), "learners": int(df.learner_id.nunique()), "weeks": 12, "success_rate": float(df["success"].mean()),
                               "action_counts": df["action"].value_counts().to_dict(), "corr_with_success": corr})


# ------------------------------------------------------------------ 3: recommender evaluation
PERSONAS = [
    # name, skill, interests, topics, goals, preferences, relevant categories (fixed before any ranking was run)
    ("Python beginner", "Beginner", "python, programming, coding", "Python", "learn programming", "hands-on", {"Programming"}),
    ("Aspiring data scientist", "Beginner", "data science, statistics, machine learning", "Data Science, Machine Learning", "get a data job", "projects", {"Data Science", "Maths"}),
    ("Frontend web developer", "Beginner", "html, css, javascript, web", "Web Development", "build websites", "hands-on", {"Web Development", "Design"}),
    ("Backend / API developer", "Intermediate", "fastapi, backend, databases, python", "Web Development, Databases", "build backend apis", "hands-on", {"Web Development", "Programming", "Data Science"}),
    ("Cloud and DevOps learner", "Intermediate", "cloud, docker, deployment, git", "Cloud", "deploy applications", "labs", {"Engineering"}),
    ("Security awareness", "Beginner", "security, privacy, safety", "Security", "stay safe online", "short courses", {"Engineering"}),
    ("Business analyst", "Beginner", "business, excel, finance, analysis", "Business, Spreadsheets", "become a business analyst", "practical", {"Business", "Maths"}),
    ("Designer", "Beginner", "design, ui, ux", "Design", "design user interfaces", "visual", {"Design", "Web Development"}),
    ("Exam preparation", "Beginner", "study skills, quizzes, productivity, motivation", "Study Skills", "study better", "short", {"Study Skills"}),
    ("Communication skills", "Beginner", "speaking, presentation, writing, communication", "Communication", "speak confidently", "practice", {"Communication"}),
]
WEIGHTS = {"content": 0.30, "skill": 0.15, "topic": 0.15, "success": 0.12, "behaviour": 0.10, "goal": 0.08, "rating": 0.05, "engagement": 0.05}


def prec(ranked_ids, rel_ids, k):
    return sum(1 for i in ranked_ids[:k] if i in rel_ids) / k


def mrr(ranked_ids, rel_ids):
    for r, i in enumerate(ranked_ids, 1):
        if i in rel_ids:
            return 1.0 / r
    return 0.0


def components(profile, courses, rec, eng):
    """Re-derive every term of the hybrid score (mirrors app.recommender.rank_courses)."""
    from app.recommender import content_scores, skill_compat, topic_interest_score
    sims = content_scores(profile, courses)
    rows = []
    goals = [g.strip().lower() for g in (profile.get("goals", "").split(",") if profile.get("goals") else []) if g.strip()]
    for i, c in enumerate(courses):
        ra = rec["by_id"][c["id"]]
        goal = 0.7 if any(g in (c["title"] + c["description"] + c["tags"]).lower() for g in goals) else 0.4
        rating = max(0, min(1, (float(c["rating"]) - 3.5) / 1.5))
        rows.append({"id": c["id"], "content": float(sims[i]), "skill": skill_compat(profile["skill_level"], c["skill_level"]),
                     "topic": topic_interest_score(profile, c), "success": ra["success_prob"], "behaviour": 0.5 + ra["behavior"],
                     "goal": goal, "rating": rating, "engagement": eng["score"]})
    return rows


def recsys_eval():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database import Base
    import app.models  # noqa: F401
    from app.recommender import rank_courses, load_ml_bundle, content_scores

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    courses = json.load(open(os.path.join(ROOT, "data", "catalog", "courses.json"), encoding="utf-8"))
    cat = {c["id"]: c["category"] for c in courses}
    bundle = load_ml_bundle()
    per, agg = [], {}
    variants = {"popularity (rating only)": None, "content-only (TF-IDF)": None, "hybrid (shipped)": None}
    abl = {k: [] for k in ["full"] + list(WEIGHTS)}
    for uid, (name, skill, interests, topics, goals, prefs, rel_cats) in enumerate(PERSONAS, 1):
        profile = {"interests": interests, "preferred_topics": topics, "goals": goals, "course_preferences": prefs,
                   "education": "Bachelor's Degree", "skill_level": skill, "weekly_hours": 6.0}
        ranked, ctx = rank_courses(profile, courses, db, uid, bundle, top_n=len(courses))
        rel = {c["id"] for c in courses if c["category"] in rel_cats}
        hy = [r["course"]["id"] for r in ranked]
        pop = [c["id"] for c in sorted(courses, key=lambda c: (-float(c["rating"]), c["id"]))]
        sims = content_scores(profile, courses)
        co = [courses[i]["id"] for i in np.argsort(-sims, kind="stable")]
        row = {"persona": name, "skill": skill, "relevant_categories": sorted(rel_cats), "relevant_courses": len(rel), "top3_hybrid": hy[:3]}
        for label, order in (("popularity (rating only)", pop), ("content-only (TF-IDF)", co), ("hybrid (shipped)", hy)):
            row[label] = {"p@1": prec(order, rel, 1), "p@3": prec(order, rel, 3), "p@5": prec(order, rel, 5), "mrr": mrr(order, rel)}
            for m, v in row[label].items():
                agg.setdefault(label, {}).setdefault(m, []).append(v)
        # ablation: drop one term at a time, renormalise nothing (weights are absolute in the shipped formula)
        by_id = {r["course"]["id"]: r for r in ranked}
        comp = components(profile, courses, {"by_id": by_id}, ctx["engagement"])
        full = {r["id"]: sum(WEIGHTS[k] * r[k] for k in WEIGHTS) for r in comp}
        top_full = sorted(full, key=lambda i: -full[i])
        # reproduces the shipped order (up to the +-0 rounding of 4 decimals)
        assert top_full[:3] == hy[:3] or abs(full[top_full[0]] - full[hy[0]]) < 1e-3, (name, top_full[:3], hy[:3])
        abl["full"].append({"p@3": prec(top_full, rel, 3), "p@5": prec(top_full, rel, 5), "mrr": mrr(top_full, rel)})
        for drop in WEIGHTS:
            sc = {r["id"]: sum(w * r[k] for k, w in WEIGHTS.items() if k != drop) for r in comp}
            order = sorted(sc, key=lambda i: -sc[i])
            abl[drop].append({"p@3": prec(order, rel, 3), "p@5": prec(order, rel, 5), "mrr": mrr(order, rel),
                              "top3_overlap_with_full": len(set(order[:3]) & set(top_full[:3])) / 3})
        per.append(row)
    summary = {k: {m: float(np.mean(v)) for m, v in d.items()} for k, d in agg.items()}
    ablation = {}
    for k, rows in abl.items():
        ablation[k] = {m: float(np.mean([r[m] for r in rows])) for m in rows[0]}
    dump("recsys_eval.json", {"personas": len(PERSONAS), "catalog_size": len(courses), "per_persona": per, "summary": summary, "ablation_drop_one_term": ablation,
                              "weights": WEIGHTS,
                              "note": "10 author-written personas; relevance = the course category is in the persona's expected set (fixed before ranking). A sanity check, not a user study."})
    print(json.dumps(summary, indent=1))
    print(json.dumps(ablation, indent=1))
    return courses, bundle, db


# ------------------------------------------------------------------ 4 + 5: feedback loop, action scores
def feedback_and_actions(courses, bundle, db):
    from app.models import Interaction
    from app.recommender import rank_courses, engagement_level, learner_state_vector, predict_success, uplift_scores

    profile = {"interests": "python, data science, machine learning", "preferred_topics": "Machine Learning, Data Analysis", "goals": "get a data job, build portfolio",
               "course_preferences": "hands-on labs, short videos", "education": "Bachelor's Degree", "skill_level": "Beginner", "weekly_hours": 6.0}
    uid = 900
    r0, c0 = rank_courses(profile, courses, db, uid, bundle, top_n=len(courses))
    base = {r["course"]["id"]: (i + 1, r["score"]) for i, r in enumerate(r0)}
    top3 = [r["course"]["id"] for r in r0[:3]]
    events = [(top3[0], "start"), (top3[0], "quiz"), (top3[0], "quiz"), (top3[0], "complete"), (top3[1], "view"), (top3[2], "dismiss")]
    for cid, ev in events:
        db.add(Interaction(user_id=uid, course_id=cid, event_type=ev, value=1.0))
    db.commit()
    r1, c1 = rank_courses(profile, courses, db, uid, bundle, top_n=len(courses))
    after = {r["course"]["id"]: (i + 1, r["score"]) for i, r in enumerate(r1)}
    moved = {cid: {"rank_before": base[cid][0], "rank_after": after[cid][0], "score_before": base[cid][1], "score_after": after[cid][1]} for cid in top3}
    dump("feedback_loop.json", {"events": [list(e) for e in events], "top3_before": top3, "top3_after": [r["course"]["id"] for r in r1[:3]],
                                "tracked": moved, "p_success_before": c0["p_success"], "p_success_after": c1["p_success"],
                                "engagement_before": c0["engagement"], "engagement_after": c1["engagement"],
                                "best_action_before": max(c0["uplift"], key=c0["uplift"].get), "best_action_after": max(c1["uplift"], key=c1["uplift"].get),
                                "uplift_before": c0["uplift"], "uplift_after": c1["uplift"]})

    # action scores / success probability across a grid of learner states
    from collections import Counter
    acts, probs, rows = Counter(), [], []
    for skill in ("Beginner", "Intermediate", "Advanced"):
        for hrs in (2, 6, 12):
            for (tot, quiz, forum, comp) in ((0, 0, 0, 0), (5, 1, 0, 0), (15, 3, 1, 1), (40, 8, 4, 3), (80, 15, 8, 5)):
                eng_score = min(1.0, 0.25 + min(tot, 200) * 0.04 + quiz * 0.03 + comp * 0.08) if tot else 0.25
                eng = {"total": tot, "quizzes": quiz, "forums": forum, "completes": comp, "score": eng_score}
                st = learner_state_vector({"weekly_hours": hrs, "skill_level": skill}, eng)
                p, _ = predict_success(bundle, st)
                u = uplift_scores(bundle, st)
                best = max(u, key=u.get)
                acts[best] += 1
                probs.append(p)
                rows.append({"skill": skill, "hours": hrs, "interactions": tot, "p_success": round(p, 4), "best_action": best, "benefit": u[best]})
    dump("action_scores.json", {"grid_states": len(rows), "best_action_counts": dict(acts), "p_success_min": float(min(probs)), "p_success_max": float(max(probs)),
                                "p_success_mean": float(np.mean(probs)), "rows": rows})
    print("actions", dict(acts), "p range", min(probs), max(probs))


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else "all"
    if only in ("all", "seeds"):
        seed_study()
    if only in ("all", "recsys"):
        courses, bundle, db = recsys_eval()
        feedback_and_actions(courses, bundle, db)
