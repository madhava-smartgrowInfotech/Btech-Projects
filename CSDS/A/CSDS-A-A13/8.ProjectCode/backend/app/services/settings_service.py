"""Workspace default rules."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import AppSetting
from app.schemas.settings import RulesIn

RULES_KEY = "rules"


def get_rules(db: Session) -> RulesIn:
    row = db.get(AppSetting, RULES_KEY)
    return RulesIn(**(row.value if row else {}))


def save_rules(db: Session, rules: RulesIn) -> RulesIn:
    row = db.get(AppSetting, RULES_KEY)
    if row is None:
        db.add(AppSetting(key=RULES_KEY, value=rules.model_dump()))
    else:
        row.value = rules.model_dump()
    return rules
