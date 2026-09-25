from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import BACKEND_PORT, gemini_configured
from .db import init_db
from .routes import auth, contracts, eval as eval_routes

app = FastAPI(title="ClauseGuard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(contracts.router)
app.include_router(eval_routes.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "gemini_configured": gemini_configured(), "port": BACKEND_PORT}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=BACKEND_PORT, reload=True)
