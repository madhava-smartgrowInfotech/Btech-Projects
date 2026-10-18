from fastapi import APIRouter, Depends

from app.api.deps import get_service
from app.services.simulation_service import SimulationService

router = APIRouter(prefix="/api/grid", tags=["grid"])


@router.get("/state")
def grid_state(svc: SimulationService = Depends(get_service)):
    """Latest power-flow snapshot: buses, lines, transformer, nodes, totals."""
    eng = svc.ensure_engine()
    snap = eng.preview()
    return {"run_id": eng.run_id, "step": eng.step_index, "time": eng.timeline[min(eng.step_index, eng.n_steps - 1)].label, **snap}


@router.get("/topology")
def grid_topology(svc: SimulationService = Depends(get_service)):
    return svc.ensure_engine().sim.topology()
