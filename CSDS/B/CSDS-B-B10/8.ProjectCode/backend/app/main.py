import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import router as auth_router, seed_demo_user
from .db import init_db
from .routes import bench, lab, live, studio

app = FastAPI(title="SkyCipher API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{os.getenv('FRONTEND_PORT', '5210')}",
                   f"http://127.0.0.1:{os.getenv('FRONTEND_PORT', '5210')}"],
    allow_methods=["*"], allow_headers=["*"], allow_credentials=True,
)

for r in (auth_router, studio.router, lab.router, bench.router, live.router):
    app.include_router(r)


@app.on_event("startup")
def startup():
    init_db()
    seed_demo_user()


@app.get("/api/health")
def health():
    return {"status": "ok"}
