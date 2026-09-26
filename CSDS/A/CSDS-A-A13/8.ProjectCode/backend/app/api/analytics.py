from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.core.deps import DB, AdminUser
from app.core.errors import AppError, NotFound
from app.ml.profile import benchmark_metrics, engine_profile, experiment_dir, hall_budget
from app.services import analytics
from app.services.plans import get_plan

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", summary="Workspace-wide figures for the dashboard")
def overview(db: DB, _: AdminUser) -> dict:
    return analytics.overview(db)


@router.get("/plans/{plan_id}", summary="Utilisation, department mix and the roll-order comparison for one plan")
def plan_figures(plan_id: int, db: DB, _: AdminUser) -> dict:
    return analytics.plan_analytics(db, get_plan(db, plan_id))


@router.get("/engine", summary="Seating engine benchmark results (ml/benchmark.py)")
def engine(_: AdminUser) -> dict:
    metrics = benchmark_metrics()
    profile = engine_profile()
    return {
        "profile": {**profile, "hall_budget_in_use": hall_budget()},
        "available": metrics is not None,
        "metrics": metrics,
        "plots": [f"/api/analytics/engine/plots/{name}" for name in (metrics or {}).get("plots", [])],
    }


@router.get("/engine/plots/{name}", summary="A benchmark chart (PNG)")
def engine_plot(name: str, _: AdminUser) -> FileResponse:
    metrics = benchmark_metrics()
    folder = experiment_dir()
    if not metrics or folder is None or name not in metrics.get("plots", []):
        raise NotFound("Chart")
    path = folder / name
    if not path.is_file():
        raise AppError("This chart file is missing from the experiment folder.", 404)
    return FileResponse(path, media_type="image/png")
