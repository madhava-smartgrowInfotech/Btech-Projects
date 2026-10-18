from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_service
from app.models.schemas import ExperimentRequest
from app.services.simulation_service import SimulationService
from app.simulation.experiment import ARMS

router = APIRouter(prefix="/api", tags=["metrics"])


def _series(rows):
    out = []
    for r in rows:
        g = r["grid"]
        t = g.get("totals", {})
        out.append({"step": r["step"], "time": r["time"], "price": r["price"], **t, "counts": r["counts"],
                    "violations_without_shield": r["violations_without_shield"], "violations_executed": r["violations_executed"],
                    "lines": {l["name"]: l["loading_percent"] for l in g.get("lines", [])},
                    "buses": {b["name"]: b["vm_pu"] for b in g.get("buses", []) if b["vn_kv"] < 1.0},
                    "nodes": {n["node_id"]: {k: n[k] for k in ("soc", "load_kw", "pv_kw", "battery_kw", "exchange_kw", "voltage_pu")}
                              for n in g.get("nodes", [])}})
    return out


@router.get("/health")
def health(svc: SimulationService = Depends(get_service)):
    s = svc.settings
    try:
        import pandapower
        pp_version = getattr(pandapower, "__version__", "unknown")
    except Exception:
        pp_version = None
    return {"status": "ok", "app_env": s.app_env, "llm_provider": s.llm_provider, "llm_configured": s.llm_configured,
            "pandapower": pp_version, "ws_clients": svc.hub.count}


@router.get("/metrics")
def metrics(svc: SimulationService = Depends(get_service)):
    eng = svc.ensure_engine()
    return {"run_id": eng.run_id, "status": svc.status()["status"], "summary": eng.summary or eng._summarise(),
            "series": _series(eng.rows)}


@router.get("/events")
def events(type: str | None = None, run_id: str | None = None, limit: int = 200, svc: SimulationService = Depends(get_service)):
    eng = svc.ensure_engine()
    if run_id and run_id != eng.run_id:
        return {"run_id": run_id, "events": svc.store.list_events(run_id, type, limit)}
    evs = [e for e in eng.event_log if not type or e["type"] == type]
    return {"run_id": eng.run_id, "events": list(reversed(evs))[:limit]}


@router.get("/runs")
def runs(svc: SimulationService = Depends(get_service)):
    return svc.store.list_runs(50)


@router.get("/runs/{run_id}")
def run_detail(run_id: str, svc: SimulationService = Depends(get_service)):
    r = svc.store.get_run(run_id)
    if r is None:
        raise HTTPException(404, "unknown run")
    return r


@router.get("/runs/{run_id}/steps")
def run_steps(run_id: str, svc: SimulationService = Depends(get_service)):
    if svc.store.get_run(run_id) is None:
        raise HTTPException(404, "unknown run")
    return _series(svc.store.get_steps(run_id))


@router.post("/experiments/run")
async def experiment_run(req: ExperimentRequest, svc: SimulationService = Depends(get_service)):
    if req.arms and any(a not in ARMS for a in req.arms):
        raise HTTPException(422, f"unknown arm; valid: {list(ARMS)}")
    return await svc.start_experiment(req)


@router.get("/experiments")
def experiments(svc: SimulationService = Depends(get_service)):
    return {"jobs": list(svc.jobs.values()), "stored": svc.store.list_experiments(), "arms": {k: v["label"] for k, v in ARMS.items()}}


@router.get("/experiments/{exp_id}")
def experiment_detail(exp_id: str, svc: SimulationService = Depends(get_service)):
    r = svc.store.get_experiment(exp_id)
    if r is None:
        job = svc.jobs.get(exp_id)
        if job:
            return job
        raise HTTPException(404, "unknown experiment")
    return r
