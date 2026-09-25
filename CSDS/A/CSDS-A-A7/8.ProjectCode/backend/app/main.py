from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import config
from .db import Base, SessionLocal, engine
from .routes import auth as auth_routes
from .routes import guardians, risk, routes_plan, sos, evidence, track, ai, ws
from .seed import seed_district_risk

Base.metadata.create_all(bind=engine)

with SessionLocal() as _db:
    seed_district_risk(_db)

app = FastAPI(title="SHEGUARD API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(guardians.router)
app.include_router(risk.router)
app.include_router(routes_plan.router)
app.include_router(sos.router)
app.include_router(evidence.router)
app.include_router(track.router)
app.include_router(ai.router)
app.include_router(ws.router)

app.mount("/evidence-files", StaticFiles(directory=str(config.EVIDENCE_DIR)), name="evidence-files")


@app.get("/api/health")
def health():
    return {"status": "ok"}
