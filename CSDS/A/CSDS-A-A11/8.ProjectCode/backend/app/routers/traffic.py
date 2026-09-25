"""Traffic control centre endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..recommender.traffic_manager import traffic_manager
from ..schemas import LoadTestIn, LoadTestOut, TrafficSnapshot

router = APIRouter(prefix="/traffic", tags=["traffic"])


@router.get("/live", response_model=TrafficSnapshot)
def live():
    snapshot = traffic_manager.state.snapshot()
    snapshot["active_test"] = traffic_manager.current_test()
    return snapshot


@router.post("/load-test", response_model=LoadTestOut)
def load_test(payload: LoadTestIn):
    try:
        test_id = traffic_manager.start_load_test(payload.profile, payload.duration_s)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return LoadTestOut(
        ok=True,
        test_id=test_id,
        profile=payload.profile,
        duration_s=payload.duration_s,
    )


@router.get("/history")
def history(limit: int = 120):
    """Recent snapshots, so a chart can render before the socket has data."""
    return traffic_manager.history[-max(1, min(600, limit)):]
