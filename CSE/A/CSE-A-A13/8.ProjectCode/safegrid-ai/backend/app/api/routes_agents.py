from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_service
from app.models.schemas import DecisionRequest
from app.services.simulation_service import SimulationService

router = APIRouter(prefix="/api/agents", tags=["agents"])


def _latest(eng, agent_id: str):
    for row in reversed(eng.rows):
        for a in row["agents"]:
            if a["agent_id"] == agent_id:
                return {"step": row["step"], "time": row["time"], **a}
    return None


@router.get("")
def list_agents(svc: SimulationService = Depends(get_service)):
    eng = svc.ensure_engine()
    snap = eng.preview()
    nodes = {n["agent_id"]: n for n in snap.get("nodes", [])}
    out = []
    for aid, agent in eng.manager.agents.items():
        latest = _latest(eng, aid)
        n = nodes.get(aid, {})
        out.append({"agent_id": aid, "node_id": agent.node_id, "role": agent.role, "label": n.get("label"),
                    "soc": n.get("soc"), "voltage_pu": n.get("voltage_pu"), "exchange_kw": n.get("exchange_kw"),
                    "provider": eng.provider.describe(), "latest": latest})
    return out


@router.get("/{agent_id}")
def agent_detail(agent_id: str, limit: int = 40, svc: SimulationService = Depends(get_service)):
    eng = svc.ensure_engine()
    if agent_id not in eng.manager.agents:
        raise HTTPException(404, f"unknown agent '{agent_id}'")
    hist = []
    for row in eng.rows[-limit:]:
        for a in row["agents"]:
            if a["agent_id"] == agent_id:
                hist.append({"step": row["step"], "time": row["time"], **a})
    return {"agent_id": agent_id, "node_id": eng.manager.agents[agent_id].node_id, "role": eng.manager.agents[agent_id].role,
            "provider": eng.provider.describe(), "history": hist, "latest": hist[-1] if hist else None}


@router.post("/{agent_id}/decision")
async def agent_decision(agent_id: str, body: DecisionRequest | None = None, svc: SimulationService = Depends(get_service)):
    """Dry run. Without a body: get the agent's current proposal and validate it. With `action`: validate an
    operator-crafted proposal. Nothing is applied to the simulation."""
    eng = svc.ensure_engine()
    action = body.action if body else None
    if action is not None and action.agent_id != agent_id:
        raise HTTPException(422, "action.agent_id must match the agent in the URL")
    try:
        return await eng.dry_run(agent_id, action)
    except KeyError:
        raise HTTPException(404, f"unknown agent '{agent_id}'")
