"""
SQLAlchemy ORM models for FINJARVIS.

Every user-owned table carries a `user_id` foreign key so that queries can
(and must) be scoped per-user at the service layer. This is the core of the
app's data-isolation guarantee: no query in services/ should ever fetch rows
for a table like Transaction without filtering by user_id.
"""
from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey, Boolean, Text
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    currency = Column(String(8), default="INR")
    monthly_income = Column(Float, default=0.0)
    risk_profile = Column(String(20), default="Moderate")  # Conservative/Moderate/Aggressive
    savings_target = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("FinancialGoal", back_populates="user", cascade="all, delete-orphan")
    investments = relationship("Investment", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, default=date.today)
    description = Column(String(255), nullable=False)
    category = Column(String(80), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(10), nullable=False)  # "income" | "expense"
    payment_method = Column(String(50), default="Other")
    notes = Column(Text, default="")

    user = relationship("User", back_populates="transactions")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category = Column(String(80), nullable=False)
    budget_amount = Column(Float, nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)

    user = relationship("User", back_populates="budgets")


class FinancialGoal(Base):
    __tablename__ = "financial_goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    goal_name = Column(String(120), nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    target_date = Column(Date, nullable=False)
    status = Column(String(20), default="active")  # active/completed/abandoned

    user = relationship("User", back_populates="goals")


class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    asset_name = Column(String(120), nullable=False)
    symbol = Column(String(20), default="")
    asset_type = Column(String(30), nullable=False)  # Stock/Mutual Fund/ETF/Gold/FD/Other
    quantity = Column(Float, nullable=False)
    purchase_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    purchase_date = Column(Date, nullable=False)

    user = relationship("User", back_populates="investments")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message = Column(String(255), nullable=False)
    notification_type = Column(String(30), default="info")  # info/warning/danger/success
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

    user = relationship("User", back_populates="notifications")
