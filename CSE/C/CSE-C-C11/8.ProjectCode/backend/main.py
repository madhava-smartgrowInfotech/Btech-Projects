"""FINJARVIS web API.

A thin FastAPI layer over the project's existing service functions (services/, ml/, auth/, utils/).
No business logic lives here: every route validates input, calls the same function the Streamlit
pages call, and shapes the result as JSON. Run from the project root:

    python -m uvicorn backend.main:app --port 8411
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import os
import sys
import time
from contextlib import asynccontextmanager
import datetime as dt
from datetime import date, timedelta
from types import SimpleNamespace
from typing import Any, Literal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(ROOT, ".env"))

import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError

import database.database as db_module
from database.models import Base, Notification, User

# Optional: point the app at another SQLite file (tests, screenshots) without touching database/.
_db_override = os.getenv("FINJARVIS_DB", "").strip()
if _db_override:
    _engine = create_engine(f"sqlite:///{_db_override}", connect_args={"check_same_thread": False})
    db_module.engine = _engine
    db_module.SessionLocal.configure(bind=_engine)

from auth.authentication import login as auth_login, signup as auth_signup
from database.database import get_session, init_db
from ml.expense_classifier import learn_from_correction, predict_category
from ml.financial_health import calculate_financial_health
from ml.spending_prediction import check_budget_overrun_risk, predict_category_spending, predict_next_month_expense
from services import report_service
from services.ai_service import DISCLAIMER, answer_question, generate_insights
from services.analytics_service import (
    analytics_overview, monthly_trend, spending_by_category, summary_metrics, transactions_dataframe,
)
from services.budget_service import check_and_raise_alerts, delete_budget, get_budget_status, set_budget
from services.data_import_service import clean_and_prepare, commit_import, load_and_validate
from services.goal_service import add_goal, delete_goal, get_goals, update_goal_progress
from services.investment_service import (
    ASSET_TYPES, add_investment, delete_investment, get_investments, portfolio_summary, refresh_price,
)
from services.transaction_service import (
    DEFAULT_CATEGORIES, add_transaction, delete_transaction, get_all_categories, get_transactions, update_transaction,
)
from utils.helpers import current_month_year, month_name
from utils.validators import is_valid_email, is_valid_amount

from backend import demo_seed

SECRET = (os.getenv("APP_SECRET_KEY") or "finjarvis-dev-secret").encode()
TOKEN_TTL = 7 * 24 * 3600
PAYMENT_METHODS = ["UPI", "Card", "Cash", "Bank Transfer", "Other"]
CURRENCIES = ["INR", "USD", "EUR", "GBP"]
RISK_PROFILES = ["Conservative", "Moderate", "Aggressive"]
GOAL_PRESETS = ["New Laptop", "Education", "Emergency Fund", "Vacation", "Car", "House", "Other"]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    try:
        demo_seed.ensure_demo_user()
    except Exception as exc:  # the API must still start if seeding fails
        print(f"[finjarvis] demo account was not seeded: {exc}")
    yield


app = FastAPI(title="FINJARVIS API", version="1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:5411", "http://127.0.0.1:5411"],
    allow_methods=["*"], allow_headers=["*"], allow_credentials=False,
)


# ----------------------------------------------------------------------------- helpers
def clean(obj: Any) -> Any:
    """Make service output JSON-safe: numpy scalars -> python, NaN -> None, DataFrames -> records."""
    if isinstance(obj, pd.DataFrame):
        return clean(obj.to_dict(orient="records"))
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, np.generic):
        obj = obj.item()
    if isinstance(obj, float) and (obj != obj or obj in (float("inf"), float("-inf"))):
        return None
    if isinstance(obj, (pd.Timestamp,)):
        return obj.date().isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    return obj


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def make_token(user_id: int) -> str:
    payload = _b64(json.dumps({"uid": user_id, "exp": int(time.time()) + TOKEN_TTL}).encode())
    sig = _b64(hmac.new(SECRET, payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{sig}"


def read_token(token: str) -> int | None:
    try:
        payload, sig = token.split(".", 1)
        good = _b64(hmac.new(SECRET, payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, good):
            return None
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        return int(data["uid"]) if data["exp"] > time.time() else None
    except Exception:
        return None


def user_dict(u: Any) -> dict:
    return {
        "id": u.id, "name": u.name, "email": u.email, "username": u.username, "currency": u.currency or "INR",
        "monthly_income": float(u.monthly_income or 0), "risk_profile": u.risk_profile or "Moderate",
        "savings_target": float(u.savings_target or 0),
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


def current_user(authorization: str | None = Header(default=None)) -> SimpleNamespace:
    token = (authorization or "").removeprefix("Bearer ").strip()
    uid = read_token(token) if token else None
    if uid is None:
        raise HTTPException(401, "Your session has expired. Please log in again.")
    with get_session() as session:
        u = session.query(User).filter(User.id == uid).first()
        if not u:
            raise HTTPException(401, "This account no longer exists. Please log in again.")
        return SimpleNamespace(**user_dict(u))


def parse_date(value: str | None, name: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(422, f"'{name}' must be a date like 2026-10-31.")


def bad_request(exc: Exception) -> HTTPException:
    return HTTPException(400, str(exc))


class NamedBytes(io.BytesIO):
    """BytesIO with a .name, which load_and_validate uses to tell CSV from Excel."""

    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name


# ----------------------------------------------------------------------------- schemas
class SignupIn(BaseModel):
    name: str
    email: str
    username: str
    password: str
    confirm_password: str


class LoginIn(BaseModel):
    identifier: str
    password: str


class ProfileIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str
    monthly_income: float = Field(ge=0)
    currency: Literal["INR", "USD", "EUR", "GBP"] = "INR"
    risk_profile: Literal["Conservative", "Moderate", "Aggressive"] = "Moderate"
    savings_target: float = Field(ge=0)


class TransactionIn(BaseModel):
    date: dt.date
    description: str
    amount: float
    transaction_type: Literal["income", "expense"]
    category: str | None = None  # None / "Auto-detect" -> classifier
    payment_method: str = "Other"
    notes: str = ""


class TransactionPatch(BaseModel):
    description: str | None = None
    amount: float | None = None
    category: str | None = None
    date: dt.date | None = None
    transaction_type: Literal["income", "expense"] | None = None
    payment_method: str | None = None
    notes: str | None = None


class PredictIn(BaseModel):
    description: str


class BudgetIn(BaseModel):
    category: str
    budget_amount: float
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2100)


class GoalIn(BaseModel):
    goal_name: str
    target_amount: float
    current_amount: float = 0
    target_date: dt.date


class GoalProgressIn(BaseModel):
    current_amount: float = Field(ge=0)


class InvestmentIn(BaseModel):
    asset_name: str
    symbol: str = ""
    asset_type: str
    quantity: float
    purchase_price: float
    current_price: float = 0
    purchase_date: dt.date


class AskIn(BaseModel):
    question: str


# ----------------------------------------------------------------------------- health + auth
@app.get("/api/health")
def health():
    return {"status": "ok", "ai_llm_enabled": bool(os.getenv("AI_API_KEY", "").strip())}


@app.get("/api/public/showcase")
def showcase():
    """Landing-page numbers, computed from the fictional demo account (no login needed)."""
    with get_session() as session:
        u = session.query(User).filter(User.username == demo_seed.DEMO_USERNAME).first()
        demo = SimpleNamespace(**user_dict(u)) if u else None
    if demo is None:
        raise HTTPException(404, "The demo account has not been created yet.")
    data = dashboard(demo)
    question = "Where am I spending the most money?"
    data["assistant"] = {"question": question, **answer_question(question, demo.id, demo.monthly_income)}
    return data


@app.post("/api/auth/signup", status_code=201)
def signup(body: SignupIn):
    result = auth_signup(body.name, body.email, body.username, body.password, body.confirm_password)
    if not result.success:
        raise HTTPException(409 if "already exists" in result.message else 400, result.message)
    return {"message": result.message, "user_id": result.user_id}


@app.post("/api/auth/login")
def login(body: LoginIn):
    result = auth_login(body.identifier, body.password)
    if not result.success:
        raise HTTPException(401, result.message)
    with get_session() as session:
        u = session.query(User).filter(User.id == result.user_id).first()
        return {"token": make_token(u.id), "user": user_dict(u)}


@app.get("/api/auth/me")
def me(user=Depends(current_user)):
    return vars(user)


@app.get("/api/meta")
def meta(user=Depends(current_user)):
    """Static choices the forms need, plus this user's categories."""
    return {
        "categories": get_all_categories(user.id), "default_categories": DEFAULT_CATEGORIES,
        "payment_methods": PAYMENT_METHODS, "asset_types": ASSET_TYPES, "currencies": CURRENCIES,
        "risk_profiles": RISK_PROFILES, "goal_presets": GOAL_PRESETS,
    }


# ----------------------------------------------------------------------------- profile
@app.put("/api/profile")
def update_profile(body: ProfileIn, user=Depends(current_user)):
    email = body.email.strip().lower()
    if not is_valid_email(email):
        raise HTTPException(400, "Please enter a valid email address.")
    try:
        with get_session() as session:
            u = session.query(User).filter(User.id == user.id).first()
            u.name = body.name.strip()
            u.email = email
            u.monthly_income = body.monthly_income
            u.currency = body.currency
            u.risk_profile = body.risk_profile
            u.savings_target = body.savings_target
            session.flush()
            return user_dict(u)
    except IntegrityError:
        raise HTTPException(409, "Another account already uses this email address.")


@app.post("/api/profile/demo-data")
def load_demo(user=Depends(current_user)):
    counts = demo_seed.load_demo(user.id)
    return {"message": "Demo data loaded.", **counts}


# ----------------------------------------------------------------------------- dashboard
def _health(user, metrics, budget_status, holdings, goals) -> dict:
    return calculate_financial_health(
        monthly_income=metrics["monthly_income"], monthly_expenses=metrics["monthly_expenses"],
        savings_rate=metrics["savings_rate"], total_balance=metrics["total_balance"],
        budget_status=budget_status, holdings=holdings, goals=goals,
    )


@app.get("/api/dashboard")
def dashboard(user=Depends(current_user)):
    month, year = current_month_year()
    metrics = summary_metrics(user.id, month, year, user.monthly_income)
    budget_status = get_budget_status(user.id, month, year)
    port = portfolio_summary(user.id)
    goals = get_goals(user.id)
    check_and_raise_alerts(user.id, month, year)

    avg_budget = (sum(b["percent_used"] for b in budget_status) / len(budget_status)) if budget_status else 0
    by_cat = spending_by_category(user.id)
    trend = monthly_trend(user.id)
    return clean({
        "month": month, "year": year, "month_name": month_name(month),
        "metrics": {**metrics, "avg_budget_usage": avg_budget},
        "health": _health(user, metrics, budget_status, port["holdings"], goals),
        "alerts": [b for b in budget_status if b["percent_used"] >= 75],
        "charts": {
            "category_spend": by_cat, "trend": trend,
            "allocation": [{"name": h["asset_name"], "value": h["current_value"]} for h in port["holdings"]],
            "budget_vs_actual": [{"category": b["category"], "budget": b["budget_amount"], "actual": b["actual_spent"]}
                                 for b in budget_status],
            "goals": [{"name": g["goal_name"], "percent": g["percent_complete"]} for g in goals],
        },
        "counts": {"budgets": len(budget_status), "goals": len(goals), "holdings": len(port["holdings"])},
    })


# ----------------------------------------------------------------------------- transactions
@app.get("/api/transactions")
def list_transactions(
    start: str | None = None, end: str | None = None, category: str | None = None,
    type: str | None = Query(default=None), q: str | None = None,
    sort: Literal["date", "amount", "category"] = "date", order: Literal["asc", "desc"] = "desc",
    user=Depends(current_user),
):
    rows = get_transactions(user.id, start_date=parse_date(start, "start"), end_date=parse_date(end, "end"),
                            category=category, transaction_type=type)
    if q and q.strip():
        needle = q.strip().lower()
        rows = [r for r in rows if needle in r["description"].lower()]
    rows.sort(key=lambda r: r[sort], reverse=(order == "desc"))
    income = sum(r["amount"] for r in rows if r["transaction_type"] == "income")
    expense = sum(r["amount"] for r in rows if r["transaction_type"] == "expense")
    return clean({"items": rows, "total": len(rows), "income": income, "expense": expense})


@app.post("/api/transactions/predict-category")
def predict(body: PredictIn, user=Depends(current_user)):
    return {"category": predict_category(body.description)}


@app.post("/api/transactions", status_code=201)
def create_transaction(body: TransactionIn, user=Depends(current_user)):
    if not body.description.strip():
        raise HTTPException(400, "Please enter a description.")
    if not is_valid_amount(body.amount):
        raise HTTPException(400, "Please enter a valid amount greater than zero.")

    chosen = (body.category or "").strip()
    auto = chosen in ("", "Auto-detect")
    predicted = predict_category(body.description)
    if auto:
        category = predicted
    else:
        category = chosen
        if predicted != category:  # a manual pick that differs from the model is a correction to learn from
            history = [(t["description"], t["category"]) for t in get_transactions(user.id)]
            try:
                learn_from_correction(body.description, category, history)
            except Exception:
                pass  # learning is best-effort, never blocks adding the transaction
    try:
        txn_id = add_transaction(user.id, body.date, body.description, category, body.amount,
                                 body.transaction_type, body.payment_method, body.notes)
    except ValueError as exc:
        raise bad_request(exc)
    return {"id": txn_id, "category": category, "auto_categorised": auto}


@app.put("/api/transactions/{txn_id}")
def edit_transaction(txn_id: int, body: TransactionPatch, user=Depends(current_user)):
    fields = body.model_dump(exclude_none=True)
    if "description" in fields:
        fields["description"] = fields["description"].strip()
        if not fields["description"]:
            raise HTTPException(400, "Description cannot be empty.")
    if "amount" in fields and not is_valid_amount(fields["amount"]):
        raise HTTPException(400, "Amount must be greater than zero.")
    if "category" in fields and not fields["category"].strip():
        raise HTTPException(400, "Category cannot be empty.")
    if not update_transaction(user.id, txn_id, **fields):
        raise HTTPException(404, "That transaction was not found.")
    return {"ok": True}


@app.delete("/api/transactions/{txn_id}")
def remove_transaction(txn_id: int, user=Depends(current_user)):
    if not delete_transaction(user.id, txn_id):
        raise HTTPException(404, "That transaction was not found.")
    return {"ok": True}


async def _read_import(file: UploadFile):
    data = await file.read()
    if not data:
        raise HTTPException(400, "The file is empty.")
    df, errors = load_and_validate(NamedBytes(data, file.filename or "upload.csv"))
    if errors or df is None:
        raise HTTPException(400, " ".join(errors) or "Could not read the file.")
    cleaned, warnings = clean_and_prepare(df)
    return cleaned, warnings


@app.post("/api/transactions/import/preview")
async def import_preview(file: UploadFile = File(...), user=Depends(current_user)):
    cleaned, warnings = await _read_import(file)
    return clean({"rows": cleaned, "valid": len(cleaned), "warnings": warnings})


@app.post("/api/transactions/import/commit")
async def import_commit(file: UploadFile = File(...), user=Depends(current_user)):
    cleaned, _ = await _read_import(file)
    if cleaned.empty:
        raise HTTPException(400, "No valid rows found to import.")
    return {"imported": commit_import(user.id, cleaned)}


# ----------------------------------------------------------------------------- analytics
@app.get("/api/analytics")
def analytics(
    start: str | None = None, end: str | None = None,
    type: Literal["All", "income", "expense"] = "All", user=Depends(current_user),
):
    end_d = parse_date(end, "end") or date.today()
    start_d = parse_date(start, "start") or end_d - timedelta(days=90)
    if start_d > end_d:
        raise HTTPException(400, "'From' must be on or before 'To'.")

    overview = analytics_overview(user.id, start_d, end_d)
    df = transactions_dataframe(user.id, start_d, end_d)

    # category breakdown honours the Type filter (the Streamlit page showed the filter but ignored it);
    # "All" means spending, as on the original page, so income categories do not swamp the chart
    sub = df[df.transaction_type == ("income" if type == "income" else "expense")]
    if sub.empty:
        by_cat = []
    else:
        by_cat = sub.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
    split = [] if df.empty else df.groupby("transaction_type", as_index=False)["amount"].sum()

    df_all = transactions_dataframe(user.id)
    prediction = predict_next_month_expense(df_all)
    cat_pred: dict = {"available": False, "message": prediction.get("message", "")}
    risks: list = []
    if prediction["available"]:
        cat_pred = predict_category_spending(df_all)
        if cat_pred["available"]:
            month, year = current_month_year()
            risks = check_budget_overrun_risk(cat_pred["predictions"], get_budget_status(user.id, month, year))

    return clean({
        "range": {"start": start_d, "end": end_d}, "type": type, "overview": overview,
        "category_distribution": by_cat, "income_expense_split": split, "trend": monthly_trend(user.id),
        "prediction": prediction, "category_prediction": cat_pred, "overrun_risks": risks,
    })


# ----------------------------------------------------------------------------- budgets
@app.get("/api/budgets")
def list_budgets(month: int | None = Query(default=None, ge=1, le=12), year: int | None = Query(default=None, ge=2000, le=2100),
                 user=Depends(current_user)):
    cm, cy = current_month_year()
    month, year = month or cm, year or cy
    return clean({"month": month, "year": year, "month_name": month_name(month),
                  "items": get_budget_status(user.id, month, year)})


@app.post("/api/budgets", status_code=201)
def save_budget(body: BudgetIn, user=Depends(current_user)):
    try:
        return {"id": set_budget(user.id, body.category.strip(), body.budget_amount, body.month, body.year)}
    except ValueError as exc:
        raise bad_request(exc)


@app.delete("/api/budgets/{budget_id}")
def remove_budget(budget_id: int, user=Depends(current_user)):
    if not delete_budget(user.id, budget_id):
        raise HTTPException(404, "That budget was not found.")
    return {"ok": True}


# ----------------------------------------------------------------------------- goals
@app.get("/api/goals")
def list_goals(user=Depends(current_user)):
    return clean({"items": get_goals(user.id)})


@app.post("/api/goals", status_code=201)
def create_goal(body: GoalIn, user=Depends(current_user)):
    if not body.goal_name.strip():
        raise HTTPException(400, "Please provide a goal name.")
    try:
        return {"id": add_goal(user.id, body.goal_name, body.target_amount, body.current_amount, body.target_date)}
    except ValueError as exc:
        raise bad_request(exc)


@app.put("/api/goals/{goal_id}")
def update_goal(goal_id: int, body: GoalProgressIn, user=Depends(current_user)):
    if not update_goal_progress(user.id, goal_id, body.current_amount):
        raise HTTPException(404, "That goal was not found.")
    return {"ok": True}


@app.delete("/api/goals/{goal_id}")
def remove_goal(goal_id: int, user=Depends(current_user)):
    if not delete_goal(user.id, goal_id):
        raise HTTPException(404, "That goal was not found.")
    return {"ok": True}


# ----------------------------------------------------------------------------- investments
@app.get("/api/investments")
def list_investments(user=Depends(current_user)):
    return clean(portfolio_summary(user.id))


@app.post("/api/investments", status_code=201)
def create_investment(body: InvestmentIn, user=Depends(current_user)):
    if not body.asset_name.strip():
        raise HTTPException(400, "Please enter an asset name.")
    try:
        return {"id": add_investment(user.id, body.asset_name, body.symbol, body.asset_type, body.quantity,
                                     body.purchase_price, body.current_price, body.purchase_date)}
    except ValueError as exc:
        raise bad_request(exc)


@app.post("/api/investments/{investment_id}/refresh")
def refresh_investment(investment_id: int, user=Depends(current_user)):
    ok, message = refresh_price(user.id, investment_id)
    return {"success": ok, "message": message}


@app.delete("/api/investments/{investment_id}")
def remove_investment(investment_id: int, user=Depends(current_user)):
    if not delete_investment(user.id, investment_id):
        raise HTTPException(404, "That investment was not found.")
    return {"ok": True}


# ----------------------------------------------------------------------------- assistant
@app.get("/api/assistant/insights")
def insights(user=Depends(current_user)):
    return {"insights": generate_insights(user.id, user.monthly_income), "disclaimer": DISCLAIMER,
            "llm_enabled": bool(os.getenv("AI_API_KEY", "").strip())}


@app.post("/api/assistant/ask")
def ask(body: AskIn, user=Depends(current_user)):
    return clean(answer_question(body.question, user.id, user.monthly_income))


# ----------------------------------------------------------------------------- reports
@app.get("/api/reports/{kind}")
def report(kind: Literal["pdf", "excel", "csv"], month: int | None = Query(default=None, ge=1, le=12),
           year: int | None = Query(default=None, ge=2000, le=2100), user=Depends(current_user)):
    cm, cy = current_month_year()
    month, year = month or cm, year or cy
    try:
        if kind == "pdf":
            path = report_service.generate_pdf_report(user.id, month, year, user.monthly_income, user.name)
            media, name = "application/pdf", f"finjarvis_report_{year}_{month:02d}.pdf"
        elif kind == "excel":
            path = report_service.generate_excel_report(user.id, month, year, user.monthly_income)
            media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            name = f"finjarvis_report_{year}_{month:02d}.xlsx"
        else:
            if not get_transactions(user.id):
                raise HTTPException(400, "There are no transactions to export yet.")
            path = report_service.generate_csv_report(user.id)
            media, name = "text/csv", "finjarvis_transactions.csv"
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, f"Could not generate the {kind.upper()} report: {exc}")
    return FileResponse(path, media_type=media, filename=name)


# ----------------------------------------------------------------------------- notifications
def _notes(user_id: int) -> list[dict]:
    with get_session() as session:
        rows = session.query(Notification).filter(Notification.user_id == user_id) \
            .order_by(Notification.created_at.desc(), Notification.id.desc()).all()
        return [{"id": n.id, "message": n.message, "type": n.notification_type,
                 "created_at": n.created_at.isoformat() if n.created_at else None, "is_read": bool(n.is_read)}
                for n in rows]


@app.get("/api/notifications")
def notifications(user=Depends(current_user)):
    month, year = current_month_year()
    check_and_raise_alerts(user.id, month, year)
    items = _notes(user.id)
    return {"items": items, "unread": sum(1 for n in items if not n["is_read"])}


@app.post("/api/notifications/read-all")
def read_all(user=Depends(current_user)):
    with get_session() as session:
        session.query(Notification).filter(Notification.user_id == user.id).update({"is_read": True})
    return {"ok": True}
