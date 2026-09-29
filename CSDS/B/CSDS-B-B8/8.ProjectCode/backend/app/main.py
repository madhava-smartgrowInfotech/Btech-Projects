import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import hash_password
from .config import DEMO_EMAIL, DEMO_PASSWORD
from .db import SessionLocal, User, init_db
from .routes import alerts, auth, contacts, monitor, reports
from .services.alerts import AlertWatchdog
from .services.monitor import monitor as live_monitor
from .services.settings import get_settings

app = FastAPI(title="CareWatch API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5208", "http://127.0.0.1:5208"],
                   allow_methods=["*"], allow_headers=["*"])
for r in (auth, monitor, alerts, contacts, reports):
    app.include_router(r.router)


@app.on_event("startup")
def startup():
    init_db()
    with SessionLocal() as db:
        if not db.query(User).filter(User.email == DEMO_EMAIL).first():
            db.add(User(name="Demo Caregiver", email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD)))
            db.commit()
    app.state.watchdog = AlertWatchdog()
    if get_settings()["monitor_running"]:  # continuous monitoring survives a restart
        def resume():
            try:
                live_monitor.start()
            except Exception as e:
                print("Could not resume monitoring:", e)
        threading.Thread(target=resume, daemon=True).start()


@app.on_event("shutdown")
def shutdown():
    live_monitor.stop(persist=False)


@app.get("/api/health")
def health():
    return {"status": "ok", "monitoring": live_monitor.running}
