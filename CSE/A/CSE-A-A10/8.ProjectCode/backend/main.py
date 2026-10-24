"""FlowSense API - a thin FastAPI layer over the smart_traffic engine.  Run: uvicorn backend.main:app"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:  # on Windows torch must load before scikit-learn / OpenCV or its DLLs fail to initialise
    import torch  # noqa: F401
except Exception:
    pass

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from smart_traffic import vision as V  # noqa: E402
from smart_traffic.sim import APPROACHES, CONTROLLERS, VTYPES  # noqa: E402

from . import auth, config, service as S  # noqa: E402

app = FastAPI(title="FlowSense API", version="1.0.0")
_yolo_ok: bool | None = None


@app.on_event("startup")
def _startup():
    S.start_background()


@app.exception_handler(S.ApiError)
async def _api_error(_: Request, e: S.ApiError):
    return JSONResponse(status_code=e.status, content={"detail": {"message": e.message, "hint": e.hint}})


@app.exception_handler(HTTPException)
async def _http_error(_: Request, e: HTTPException):
    d = e.detail if isinstance(e.detail, dict) else {"message": str(e.detail), "hint": ""}
    return JSONResponse(status_code=e.status_code, content={"detail": d})


@app.exception_handler(RequestValidationError)
async def _validation(_: Request, e: RequestValidationError):
    first = e.errors()[0] if e.errors() else {}
    where = ".".join(str(x) for x in first.get("loc", [])[1:])
    return JSONResponse(status_code=422, content={"detail": {"message": f"Invalid input{' for ' + where if where else ''}: {first.get('msg', '')}",
                                                             "hint": "Check the value and try again."}})


# --------------------------------------------------------------------- public
@app.get("/api/health")
def health():
    global _yolo_ok
    if _yolo_ok is None:
        _yolo_ok = V.yolo_available()
    return dict(ok=True, predictor_ready=S.PRED.ready, predictor_error=S.PRED.error, yolo_available=_yolo_ok, live_clock=S.clock(S.LIVE.sim))


class Login(BaseModel):
    email: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=1, max_length=120)


@app.post("/api/auth/login")
def login(body: Login):
    if not auth.check_credentials(body.email, body.password):
        raise HTTPException(401, detail={"message": "Email or password is incorrect.", "hint": "Use the demo operator account shown on the sign-in page."})
    return dict(token=auth.make_token(body.email.strip().lower(), config.DEMO_NAME), user=dict(name=config.DEMO_NAME, email=body.email.strip().lower()))


@app.get("/api/auth/demo")
def demo_account():
    """Shown on the sign-in page so the demo account is discoverable."""
    return dict(email=config.DEMO_EMAIL, password=config.DEMO_PASSWORD)


@app.get("/api/public/pulse")
def pulse():
    with S.LOCK:
        return S.PREVIEW.pulse()


# ------------------------------------------------------------------ protected
P = [Depends(auth.current_user)]


@app.get("/api/auth/me", dependencies=P)
def me(user: dict = Depends(auth.current_user)):
    return dict(name=user["name"], email=user["sub"])


@app.get("/api/meta", dependencies=P)
def meta():
    return dict(controllers=CONTROLLERS, approaches=list(APPROACHES), grids=list(S.GRIDS), vehicle_types=VTYPES + ["ambulance"],
                version=app.version)


class LiveConfig(BaseModel):
    grid: str | None = None
    controller: str | None = None
    demand: float | None = Field(default=None, ge=0.4, le=2.0)
    emergencies: bool | None = None
    use_ml: bool | None = None


class Step(BaseModel):
    seconds: int = Field(ge=1, le=900)


@app.get("/api/live", dependencies=P)
def live():
    with S.LOCK:
        S.LIVE._attach()
        return S.LIVE.snapshot()


@app.put("/api/live/config", dependencies=P)
def live_config(body: LiveConfig):
    with S.LOCK:
        S.LIVE.configure(**body.model_dump())
        return S.LIVE.snapshot()


@app.post("/api/live/step", dependencies=P)
def live_step(body: Step):
    with S.LOCK:
        S.LIVE.step(body.seconds)
        return S.LIVE.snapshot()


@app.post("/api/live/ambulance", dependencies=P)
def live_ambulance():
    with S.LOCK:
        entry = S.LIVE.ambulance()
        return dict(S.LIVE.snapshot(), entry=entry)


@app.post("/api/live/reset", dependencies=P)
def live_reset():
    with S.LOCK:
        S.LIVE.reset()
        return S.LIVE.snapshot()


class Bench(BaseModel):
    grid: str = "2x2"
    seconds: int = 1800
    demand: float = 1.2
    seeds: int = 3
    start_hour: float = 8.0
    use_ml: bool = True


@app.post("/api/benchmark", dependencies=P)
def benchmark(b: Bench):
    return S.benchmark(b.grid, b.seconds, b.demand, b.seeds, b.start_hour, b.use_ml)


class SweepReq(BaseModel):
    grid: str = "2x2"
    use_ml: bool = True


@app.post("/api/benchmark/sweep", dependencies=P)
def benchmark_sweep(b: SweepReq):
    return S.sweep(b.grid, b.use_ml)


@app.get("/api/vision/synthetic", dependencies=P)
def vision_synthetic(vehicles: int = 9, ambulance: bool = True, flash: str = "A", seed: int = 3):
    return S.vision_synthetic(vehicles, ambulance, flash, seed)


@app.get("/api/vision/sample", dependencies=P)
def vision_sample(conf: float = 0.3):
    return S.vision_sample(conf)


@app.post("/api/vision/analyze", dependencies=P)
def vision_analyze(file: UploadFile = File(...), conf: float = Form(0.3)):
    data = file.file.read(12 * 1024 * 1024 + 1)
    if len(data) > 12 * 1024 * 1024:
        raise S.ApiError(413, "That image is larger than 12 MB.", "Resize or compress the frame and try again.")
    return S.vision_upload(data, conf)


@app.get("/api/prediction", dependencies=P)
def prediction():
    return S.prediction()


@app.get("/api/prediction/live", dependencies=P)
def prediction_live():
    with S.LOCK:
        return S.prediction_live()


@app.post("/api/prediction/simulate", dependencies=P)
def prediction_simulate():
    with S.LOCK:
        S.LIVE.step(180)
        return S.LIVE.snapshot()


@app.get("/api/violations", dependencies=P)
def violations():
    with S.LOCK:
        return S.violations()
