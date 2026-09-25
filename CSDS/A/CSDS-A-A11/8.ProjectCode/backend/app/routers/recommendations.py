"""Recommendation surface and its explainability endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..recommender.explain import explain as build_explanation
from ..recommender.orchestrator import orchestrator
from ..schemas import ExplainOut, RecommendationsOut

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=RecommendationsOut)
def get_recommendations(
    user_id: str | None = None,
    session_id: str | None = None,
    context: str = Query("home", pattern="^(home|product|cart|search)$"),
    product_id: int | None = None,
    q: str | None = None,
    limit: int = Query(12, ge=1, le=48),
):
    if not orchestrator.ready:
        raise HTTPException(status_code=503, detail="Recommendation engine is still warming up")
    if context == "product" and product_id is None:
        raise HTTPException(status_code=400, detail="context=product requires product_id")
    if product_id is not None and product_id not in orchestrator.index_by_id:
        raise HTTPException(status_code=404, detail=f"No product with id {product_id}")

    return orchestrator.recommend(
        user_id=user_id,
        session_id=session_id,
        context=context,
        product_id=product_id,
        query=q,
        limit=limit,
    )


@router.get("/{rec_id}/explain", response_model=ExplainOut)
def explain_recommendation(rec_id: str):
    payload = build_explanation(orchestrator, rec_id)
    if payload is None:
        raise HTTPException(
            status_code=404,
            detail=f"Recommendation '{rec_id}' is no longer in the impression store",
        )
    return payload
