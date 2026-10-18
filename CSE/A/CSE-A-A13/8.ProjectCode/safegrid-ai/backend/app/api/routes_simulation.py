from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_service
from app.models.schemas import RunConfig
from app.services.simulation_service import SimulationService
from app.simulation.scenarios import SCENARIO_ORDER, SCENARIOS

router = APIRouter(prefix="/api", tags=["simulation"])


@router.post("/simulation/start")
async def start(config: RunConfig | None = None, resume: bool = False, svc: SimulationService = Depends(get_service)):
    try:
        await svc.start(config, resume=resume)
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    except KeyError as e:
        raise HTTPException(404, f"unknown scenario {e}")
    return svc.status()


@router.post("/simulation/stop")
async def stop(svc: SimulationService = Depends(get_service)):
    return await svc.stop()


@router.post("/simulation/reset")
async def reset(config: RunConfig | None = None, svc: SimulationService = Depends(get_service)):
    try:
        await svc.reset(config)
    except KeyError as e:
        raise HTTPException(404, f"unknown scenario {e}")
    return svc.status()


@router.post("/simulation/step")
async def step(svc: SimulationService = Depends(get_service)):
    try:
        row = await svc.step_once()
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    except IndexError as e:
        raise HTTPException(409, str(e))
    return {"status": svc.status(), "step": row}


@router.get("/simulation/status")
def status(svc: SimulationService = Depends(get_service)):
    return svc.status()


@router.get("/scenarios")
def scenarios():
    return [SCENARIOS[i].to_dict() for i in SCENARIO_ORDER]


@router.post("/scenarios/{scenario_id}/run")
async def run_scenario(scenario_id: str, config: RunConfig | None = None, svc: SimulationService = Depends(get_service)):
    """Run a scenario to completion (no playback delay) and return its summary. The run becomes the current run."""
    try:
        return await svc.run_scenario(scenario_id, config)
    except KeyError:
        raise HTTPException(404, f"unknown scenario '{scenario_id}'")
    except RuntimeError as e:
        raise HTTPException(409, str(e))
