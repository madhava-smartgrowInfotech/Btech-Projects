import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .routes import auth, network, ops, quality


def warm_up():
    """Load models and run the twin once so the first user request is fast."""
    from .services import anomaly, imbalance, quality

    try:
        quality.predict(quality.samples()[0]["values"])
        anomaly.flagged_meters()
        imbalance.analyse()
    except Exception as e:  # noqa: BLE001
        print(f"warm-up skipped: {e}")


@asynccontextmanager
async def lifespan(app):
    init_db()
    threading.Thread(target=warm_up, daemon=True).start()
    yield


app = FastAPI(title="AquaVision API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5214", "http://127.0.0.1:5214"],
                   allow_methods=["*"], allow_headers=["*"])
for r in (auth, quality, network, ops):
    app.include_router(r.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "AquaVision"}
