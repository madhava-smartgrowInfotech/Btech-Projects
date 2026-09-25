"""Digital twin simulation lab endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import SimulationRun
from ..recommender.digital_twin import run_simulation
from ..recommender.orchestrator import orchestrator
from ..schemas import DeployOut, SimulateIn, SimulateOut, SimulationHistoryRow

router = APIRouter(prefix="/simulate", tags=["simulate"])


@router.post("", response_model=SimulateOut)
def simulate(payload: SimulateIn, db: Session = Depends(get_db)):
    """Run the proposed blend against the live one across the whole population.

    Defined as a sync handler so FastAPI runs the compute on a worker thread and
    the traffic loop keeps ticking while a long run is in flight.
    """
    if not orchestrator.ready:
        raise HTTPException(status_code=503, detail="Recommendation engine is still warming up")

    return run_simulation(
        db,
        orchestrator,
        name=payload.name,
        candidate_weights=payload.weights.model_dump(),
        population_size=payload.population_size or 200,
        rounds=payload.rounds or 5,
    )


@router.get("/history", response_model=list[SimulationHistoryRow])
def history(limit: int = Query(20, ge=1, le=200), db: Session = Depends(get_db)):
    rows = (
        db.execute(select(SimulationRun).order_by(SimulationRun.created_at.desc()).limit(limit))
        .scalars()
        .all()
    )
    return [
        SimulationHistoryRow(
            run_id=r.run_id,
            name=r.name,
            weights=r.weights,
            verdict=r.verdict,
            lift=r.lift,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/{run_id}", response_model=SimulateOut)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.get(SimulationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"No simulation run '{run_id}'")
    return run.payload


@router.post("/{run_id}/deploy", response_model=DeployOut)
def deploy(run_id: str, db: Session = Depends(get_db)):
    run = db.get(SimulationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"No simulation run '{run_id}'")

    live = orchestrator.set_weights(db, run.weights, trigger_action="digital_twin_deploy")
    return DeployOut(ok=True, live_weights=live)
