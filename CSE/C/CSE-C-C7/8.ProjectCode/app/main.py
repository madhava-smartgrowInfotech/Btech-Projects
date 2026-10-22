from pathlib import Path
import json
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import init_db, get_db, SessionLocal
from app.models import Course
from app.api_routes import router as api_router
from app.config import settings

BASE = Path(__file__).resolve().parent
app = FastAPI(title="LearnPathIQ")
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE / "templates"))

init_db()

def seed_courses():
    db = SessionLocal()
    try:
        if db.query(Course).count() == 0:
            cj = Path(__file__).resolve().parent.parent / "data" / "catalog" / "courses.json"
            if not cj.exists():
                # inline minimal seed
                data = []
            else:
                data = json.loads(cj.read_text())
            for c in data:
                db.add(Course(**{k: c.get(k) for k in ["id","title","category","topic","skill_level","description","duration_hours","difficulty","prerequisites","outcomes","tags","resource_type","rating"]}))
            db.commit()
    finally:
        db.close()

seed_courses()
app.include_router(api_router)

PAGES = ["index","register","login","onboarding","dashboard","recommendations","course","path","activity","insights","analytics"]

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

for pg in ["register","login","onboarding","dashboard","recommendations","path","activity","insights","analytics"]:
    def make_handler(pg=pg):
        def h(request: Request):
            return templates.TemplateResponse(request, f"{pg}.html", {"request": request})
        return h
    app.get(f"/{pg}", response_class=HTMLResponse)(make_handler(pg))

@app.get("/course/{course_id}", response_class=HTMLResponse)
def course_page(course_id: str, request: Request):
    return templates.TemplateResponse(request, "course.html", {"request": request, "course_id": course_id})
