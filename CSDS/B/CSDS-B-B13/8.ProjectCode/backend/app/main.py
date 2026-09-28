"""APISentry backend entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import init_db
from .routes import auth_routes, catalog_routes, scan_routes, target_routes
from .seed import seed

app = FastAPI(title="APISentry API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{settings.frontend_port}",
                   f"http://127.0.0.1:{settings.frontend_port}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(target_routes.router)
app.include_router(scan_routes.router)
app.include_router(catalog_routes.router)


@app.on_event("startup")
def _startup():
    init_db()
    seed()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "APISentry"}
