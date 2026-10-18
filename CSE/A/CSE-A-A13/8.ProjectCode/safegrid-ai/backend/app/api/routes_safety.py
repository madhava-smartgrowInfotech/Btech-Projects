from fastapi import APIRouter, Depends

from app.api.deps import get_service
from app.safety.events import verify_chain
from app.services.simulation_service import SimulationService

router = APIRouter(prefix="/api/safety", tags=["safety"])


@router.get("/events")
def safety_events(status: str | None = None, run_id: str | None = None, limit: int = 200,
                  svc: SimulationService = Depends(get_service)):
    """Hash-chained safety events for the current run (or a stored run via run_id)."""
    eng = svc.ensure_engine()
    if run_id and run_id != eng.run_id:
        return {"run_id": run_id, "chain_valid": None, "events": svc.store.list_safety_events(run_id, status, limit)}
    evs = [e.to_dict() for e in eng.safety_events if not status or e.payload.get("status") == status]
    return {"run_id": eng.run_id, "chain_valid": verify_chain(eng.safety_events), "total": len(eng.safety_events),
            "events": list(reversed(evs))[:limit]}


@router.get("/constraints")
def constraints(svc: SimulationService = Depends(get_service)):
    return svc.ensure_engine().cfg.to_dict()
