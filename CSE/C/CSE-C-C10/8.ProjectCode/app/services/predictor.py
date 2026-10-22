"""Prediction + deterministic explanations."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.config import ALPHA, DEFAULT_K
from app.ml.embeddings import embed_texts
from app.ml.retrieval import fuse, retrieve_similar


def build_input_row(payload: dict) -> pd.DataFrame:
    row = {
        "age_first_funding_year": float(payload.get("age_first_funding_year", 1.5)),
        "age_last_funding_year": float(payload.get("age_last_funding_year", 2.5)),
        "age_first_milestone_year": float(payload.get("age_first_milestone_year", 1.0)),
        "age_last_milestone_year": float(payload.get("age_last_milestone_year", 2.0)),
        "relationships": float(payload.get("relationships", 4)),
        "funding_rounds": float(payload.get("funding_rounds", 2)),
        "funding_total_usd": float(payload.get("funding_total_usd", 1000000)),
        "milestones": float(payload.get("milestones", 2)),
        "avg_participants": float(payload.get("avg_participants", 3.0)),
        "has_VC": int(bool(payload.get("has_VC", False))),
        "has_angel": int(bool(payload.get("has_angel", False))),
        "has_roundA": int(bool(payload.get("has_roundA", False))),
        "has_roundB": int(bool(payload.get("has_roundB", False))),
        "has_roundC": int(bool(payload.get("has_roundC", False))),
        "has_roundD": int(bool(payload.get("has_roundD", False))),
        "is_top500": int(bool(payload.get("is_top500", False))),
        "state": str(payload.get("state", "CA")),
        "industry_type": str(payload.get("industry_type", "Software")),
        "description": str(payload.get("description", "")),
    }
    row["log_funding_total_usd"] = float(np.log1p(max(0.0, row["funding_total_usd"])))
    return pd.DataFrame([row])


def predict_one(payload: dict, state: dict, k: int = DEFAULT_K) -> dict:
    model = state["model"]
    pre = state["pre"]
    train_fused = state["train_fused"]
    train_df = state["train_df"]
    meta = state["metadata"]
    k = int(max(1, min(int(k or DEFAULT_K), len(train_df))))

    inp = build_input_row(payload)
    S = pre.transform(inp)
    T, backend = embed_texts([inp.iloc[0]["description"] or f"{inp.iloc[0]['industry_type']} startup"])
    F = fuse(S, T, ALPHA)

    proba = None
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(F)[0]
        pred = int(np.argmax(proba))
        conf = float(np.max(proba))
    else:
        pred = int(model.predict(F)[0])
        conf = 0.5
        proba = np.array([1 - conf, conf]) if pred == 1 else np.array([conf, 1 - conf])

    similar = retrieve_similar(F[0], train_fused, train_df, k=k)
    sim_records = []
    for _, r in similar.iterrows():
        sim_records.append({
            "similarity": round(float(r["similarity"]), 4),
            "outcome": str(r.get("outcome", "SUCCESS" if r.get("label") == 1 else "FAILURE")),
            "industry": str(r.get("industry_type", "")),
            "state": str(r.get("state", "")),
            "funding_total_usd": float(r.get("funding_total_usd", 0) or 0),
            "funding_rounds": float(r.get("funding_rounds", 0) or 0),
            "relationships": float(r.get("relationships", 0) or 0),
            "milestones": float(r.get("milestones", 0) or 0),
            "description": str(r.get("description", ""))[:280],
        })
    n_s = sum(1 for s in sim_records if s["outcome"] == "SUCCESS")
    n_f = len(sim_records) - n_s

    # deterministic explanation from feature importance / coefficients + retrieval
    bullets = []
    try:
        fnames = meta.get("feature_names_structured", [])
        svals = np.asarray(S[0]).ravel()
        if hasattr(model, "feature_importances_"):
            imp = np.asarray(model.feature_importances_, dtype=float)[: len(svals)]
            order = np.argsort(-imp)[:5]
            for i in order:
                name = fnames[int(i)] if int(i) < len(fnames) else f"feature_{i}"
                bullets.append(f"{name}: value {svals[int(i)]:.2f} (scaled), importance {imp[int(i)]:.3f}")
        elif hasattr(model, "coef_"):
            coef = np.asarray(model.coef_).ravel()[: len(svals)]
            order = np.argsort(-np.abs(coef))[:5]
            for i in order:
                name = fnames[int(i)] if int(i) < len(fnames) else f"feature_{i}"
                direction = "supports SUCCESS" if coef[int(i)] * svals[int(i)] > 0 else "supports FAILURE"
                bullets.append(f"{name}: value {svals[int(i)]:.2f} (scaled), weight {coef[int(i)]:.3f} — {direction}")
    except Exception:
        pass
    bullets.append(f"Retrieved {len(sim_records)} comparable historical startups ({n_s} SUCCESS / {n_f} FAILURE); "
                   f"top similarity {sim_records[0]['similarity']:.3f}." if sim_records else "No comparable records.")
    avg_sim_s = float(np.mean([s["similarity"] for s in sim_records if s["outcome"] == "SUCCESS"])) if n_s else 0.0
    avg_sim_f = float(np.mean([s["similarity"] for s in sim_records if s["outcome"] == "FAILURE"])) if n_f else 0.0
    bullets.append(f"Average similarity to SUCCESS cases: {avg_sim_s:.3f}; to FAILURE cases: {avg_sim_f:.3f}.")

    risk = "Lower risk" if (pred == 1 and conf >= 0.7) else ("Moderate risk" if conf >= 0.55 else "Higher uncertainty")
    return {
        "outcome": "SUCCESS" if pred == 1 else "FAILURE",
        "probability_success": float(proba[1] if len(proba) > 1 else conf),
        "probability_failure": float(proba[0] if len(proba) > 1 else 1 - conf),
        "confidence": conf,
        "model": meta.get("best_model", "model"),
        "risk": risk,
        "similar": sim_records,
        "similar_counts": {"SUCCESS": n_s, "FAILURE": n_f},
        "explanation": bullets,
        "embedding_backend": backend,
        "k": k,
    }
