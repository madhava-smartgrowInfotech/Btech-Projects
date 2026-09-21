"""
Financial health scoring (0-100) built from weighted, explainable sub-scores.
Every component is computed from the user's actual data — nothing is invented.
"""
from __future__ import annotations

WEIGHTS = {
    "savings_rate": 0.30,
    "expense_ratio": 0.20,
    "budget_adherence": 0.15,
    "emergency_fund": 0.15,
    "investment_diversification": 0.10,
    "goal_progress": 0.10,
}


def _clip(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def score_savings_rate(savings_rate: float) -> float:
    # 20%+ savings rate = full marks; scales linearly below that; negative = 0
    return _clip((savings_rate / 20.0) * 100)


def score_expense_ratio(monthly_income: float, monthly_expenses: float) -> float:
    if monthly_income <= 0:
        return 0.0
    ratio = monthly_expenses / monthly_income
    # ratio <= 0.5 is excellent, ratio >= 1.0 (spending it all or more) is 0
    return _clip((1.0 - ratio) / 0.5 * 100)


def score_budget_adherence(budget_status: list[dict]) -> float:
    if not budget_status:
        return 50.0  # neutral score if no budgets configured yet
    within_budget = sum(1 for b in budget_status if b["percent_used"] <= 100)
    return _clip((within_budget / len(budget_status)) * 100)


def score_emergency_fund(total_balance: float, monthly_expenses: float) -> float:
    if monthly_expenses <= 0:
        return 50.0
    months_covered = total_balance / monthly_expenses
    # 6 months of expenses covered = full marks
    return _clip((months_covered / 6.0) * 100)


def score_investment_diversification(holdings: list[dict]) -> float:
    if not holdings:
        return 0.0
    asset_types = {h["asset_type"] for h in holdings}
    # more distinct asset types = better diversification, cap at 5 types for full marks
    return _clip((len(asset_types) / 5.0) * 100)


def score_goal_progress(goals: list[dict]) -> float:
    if not goals:
        return 50.0  # neutral if no goals set
    avg_progress = sum(g["percent_complete"] for g in goals) / len(goals)
    return _clip(avg_progress)


def calculate_financial_health(
    monthly_income: float, monthly_expenses: float, savings_rate: float,
    total_balance: float, budget_status: list[dict], holdings: list[dict], goals: list[dict],
) -> dict:
    components = {
        "savings_rate": score_savings_rate(savings_rate),
        "expense_ratio": score_expense_ratio(monthly_income, monthly_expenses),
        "budget_adherence": score_budget_adherence(budget_status),
        "emergency_fund": score_emergency_fund(total_balance, monthly_expenses),
        "investment_diversification": score_investment_diversification(holdings),
        "goal_progress": score_goal_progress(goals),
    }
    total = sum(components[k] * WEIGHTS[k] for k in WEIGHTS)
    total = round(_clip(total), 1)

    if total >= 90:
        rating, explanation = "Excellent", "You're managing your finances very effectively."
    elif total >= 75:
        rating, explanation = "Good", "Your finances are in solid shape with room for fine-tuning."
    elif total >= 60:
        rating, explanation = "Fair", "You're on a reasonable track but some areas need attention."
    elif total >= 40:
        rating, explanation = "Needs Improvement", "Several areas of your finances need active attention."
    else:
        rating, explanation = "Critical", "Your finances need immediate attention across multiple areas."

    weakest = min(components, key=components.get)
    reasons = {
        "savings_rate": "your savings rate is low relative to your income",
        "expense_ratio": "your expenses are consuming a large share of your income",
        "budget_adherence": "you are exceeding several of your category budgets",
        "emergency_fund": "your cash reserves would not cover many months of expenses",
        "investment_diversification": "your investments are concentrated in few asset types",
        "goal_progress": "progress toward your savings goals is behind schedule",
    }

    return {
        "score": total,
        "rating": rating,
        "explanation": explanation,
        "components": {k: round(v, 1) for k, v in components.items()},
        "weakest_area": weakest,
        "weakest_area_reason": reasons[weakest],
    }
