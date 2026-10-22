from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

@router.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return templates.TemplateResponse(request, "landing.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {"request": request})

@router.get("/history", response_class=HTMLResponse)
def history_page(request: Request):
    return templates.TemplateResponse(request, "history.html", {"request": request})

@router.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse(request, "about.html", {"request": request})
