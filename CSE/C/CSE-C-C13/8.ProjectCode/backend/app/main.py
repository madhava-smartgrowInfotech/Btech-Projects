"""CipherVault backend: FastAPI app serving the REST API and the frontend."""

from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api import audit, auth, files, sharing, users
from backend.app.core.config import get_settings
from backend.app.db.database import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="CipherVault", version="1.0.0",
              description="Secure file storage with client-side AES-256-GCM encryption.",
              lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8413", "http://127.0.0.1:8413",
                   "http://localhost:5413", "http://127.0.0.1:5413"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-CipherVault-IV", "X-CipherVault-Wrapped-FEK", "X-CipherVault-SHA256",
                    "X-CipherVault-Filename", "X-CipherVault-MIME"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(files.router)
app.include_router(sharing.router)
app.include_router(audit.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/api/config")
def public_config():
    return {"app": settings.APP_NAME, "max_upload_mb": settings.MAX_UPLOAD_MB}


# ---- Frontend (served by the backend so one-click local deployment works) ----
APP_DIR = Path(__file__).resolve().parent            # backend/app/
BACKEND_DIR = APP_DIR.parent                           # backend/
PROJECT_ROOT = BACKEND_DIR.parent                      # CipherVault/
# Built Vite app (run `npm run build` in frontend/). In development the Vite server on :5413 is used instead.
FRONTEND_DIR = PROJECT_ROOT / "frontend" / "dist"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index), media_type="text/html")
    return {"app": "CipherVault", "docs": "/docs"}


@app.get("/{path:path}", include_in_schema=False)
def spa_fallback(path: str):
    # Let API + docs + static pass through; everything else serves the SPA.
    if path.startswith(("api/", "docs", "openapi.json", "redoc", "static/")):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
    index = FRONTEND_DIR / "index.html"
    candidate = FRONTEND_DIR / path
    if path and candidate.is_file():
        return FileResponse(str(candidate))
    if index.exists():
        return FileResponse(str(index), media_type="text/html")
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Not found")
