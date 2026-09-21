"""Financial goal CRUD + progress calculations."""
from __future__ import annotations

from datetime import date
from sqlalchemy import and_

from database.database import get_session
from database.models import FinancialGoal
from utils.helpers import pct


def add_goal(user_id: int, goal_name: str, target_amount: float,
             current_amount: float, target_date: date) -> int:
    if target_amount <= 0:
        raise ValueError("target_amount must be greater than zero")
    with get_session() as session:
        goal = FinancialGoal(
            user_id=user_id, goal_name=goal_name.strip(), target_amount=target_amount,
            current_amount=max(0.0, current_amount), target_date=target_date, status="active",
        )
        session.add(goal)
        session.flush()
        return goal.id


def update_goal_progress(user_id: int, goal_id: int, current_amount: float) -> bool:
    with get_session() as session:
        goal = session.query(FinancialGoal).filter(
            and_(FinancialGoal.id == goal_id, FinancialGoal.user_id == user_id)
        ).first()
        if not goal:
            return False
        goal.current_amount = max(0.0, current_amount)
        if goal.current_amount >= goal.target_amount:
            goal.status = "completed"
        return True


def delete_goal(user_id: int, goal_id: int) -> bool:
    with get_session() as session:
        goal = session.query(FinancialGoal).filter(
            and_(FinancialGoal.id == goal_id, FinancialGoal.user_id == user_id)
        ).first()
        if not goal:
            return False
        session.delete(goal)
        return True


def get_goals(user_id: int) -> list[dict]:
    with get_session() as session:
        goals = session.query(FinancialGoal).filter(FinancialGoal.user_id == user_id).all()
        result = []
        for g in goals:
            months_left = max(1, _months_between(date.today(), g.target_date))
            remaining = max(0.0, g.target_amount - g.current_amount)
            required_monthly = round(remaining / months_left, 2) if months_left else remaining
            result.append({
                "id": g.id, "goal_name": g.goal_name, "target_amount": g.target_amount,
                "current_amount": g.current_amount, "target_date": g.target_date,
                "status": g.status, "percent_complete": pct(g.current_amount, g.target_amount),
                "required_monthly_savings": required_monthly,
            })
        return result


def _months_between(d1: date, d2: date) -> int:
    return (d2.year - d1.year) * 12 + (d2.month - d1.month)
