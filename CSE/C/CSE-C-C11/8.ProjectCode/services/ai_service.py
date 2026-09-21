"""
FINJARVIS AI Assistant.

Two layers, both scoped strictly to the currently logged-in user's data:

1. Deterministic analytics layer (always available, works fully offline):
   answers common questions ("how much did I spend on X", "where am I
   overspending", etc.) by querying this user's own transactions/budgets/
   goals — never another user's data, never fabricated numbers.

2. Optional LLM layer: if AI_API_KEY is set in the environment, free-form
   questions that the deterministic layer can't match are forwarded to the
   LLM along with a compact, factual summary of this user's own financial
   data (never raw access to the whole database, never other users' data).
   If no key is set, or the request fails, the assistant gracefully falls
   back to the deterministic layer / a clear "AI features unavailable" note
   rather than crashing or inventing numbers.

DISCLAIMER (always surfaced in the UI): the assistant is not a certified
financial advisor and its suggestions are informational only.
"""
from __future__ import annotations

import os
from datetime import date

from services.analytics_service import summary_metrics, spending_by_category, analytics_overview
from services.budget_service import get_budget_status
from services.transaction_service import get_transactions
from ml.financial_health import calculate_financial_health
from services.investment_service import portfolio_summary
from services.goal_service import get_goals
from utils.helpers import format_currency, current_month_year

DISCLAIMER = (
    "This is informational analysis based on your own recorded data, not professional "
    "financial advice. Consider consulting a certified financial advisor for major decisions."
)


def _financial_context(user_id: int, monthly_income: float) -> dict:
    month, year = current_month_year()
    metrics = summary_metrics(user_id, month, year, monthly_income)
    budget_status = get_budget_status(user_id, month, year)
    holdings = portfolio_summary(user_id)["holdings"]
    goals = get_goals(user_id)
    health = calculate_financial_health(
        monthly_income=metrics["monthly_income"], monthly_expenses=metrics["monthly_expenses"],
        savings_rate=metrics["savings_rate"], total_balance=metrics["total_balance"],
        budget_status=budget_status, holdings=holdings, goals=goals,
    )
    return {"metrics": metrics, "budget_status": budget_status, "holdings": holdings,
            "goals": goals, "health": health, "month": month, "year": year}


def _answer_food_or_category_spend(question: str, user_id: int) -> str | None:
    q = question.lower()
    month, year = current_month_year()
    by_cat = spending_by_category(user_id)
    if by_cat.empty:
        for kw in ("food", "spend on", "spent on"):
            if kw in q:
                return "I don't see any transactions recorded yet, so I can't calculate that. Add some transactions first."
        return None
    for _, row in by_cat.iterrows():
        if row["category"].lower() in q:
            return (f"You've spent {format_currency(row['amount'])} on {row['category']} "
                    f"across your recorded transactions.")
    return None


def _answer_where_overspending(question: str, user_id: int) -> str | None:
    q = question.lower()
    if "where" in q and ("spend" in q or "spending" in q):
        by_cat = spending_by_category(user_id)
        if by_cat.empty:
            return "I don't have enough transaction history yet to identify your top spending category."
        top = by_cat.iloc[0]
        others = ", ".join(f"{r['category']} ({format_currency(r['amount'])})" for _, r in by_cat.iloc[1:4].iterrows())
        msg = f"Your biggest spending category is {top['category']} at {format_currency(top['amount'])}."
        if others:
            msg += f" Next highest: {others}."
        return msg
    return None


def _answer_can_i_save(question: str, user_id: int, monthly_income: float) -> str | None:
    q = question.lower()
    if "can i save" in q or ("save" in q and any(c.isdigit() for c in q)):
        ctx = _financial_context(user_id, monthly_income)
        m = ctx["metrics"]
        # Try to extract a target amount from the question
        digits = "".join(c for c in q if c.isdigit())
        target = float(digits) if digits else None
        projected_savings = m["monthly_income"] - m["monthly_expenses"]
        if target:
            if projected_savings >= target:
                return (f"Based on this month so far, your income minus expenses leaves you "
                        f"{format_currency(projected_savings)}, which comfortably covers a "
                        f"{format_currency(target)} savings goal.")
            gap = target - projected_savings
            return (f"At your current pace, you're on track to have about {format_currency(projected_savings)} "
                    f"left over this month — {format_currency(gap)} short of {format_currency(target)}. "
                    f"Reducing spending in your top category could help close that gap.")
        return (f"So far this month your income is {format_currency(m['monthly_income'])} against "
                f"{format_currency(m['monthly_expenses'])} in expenses, leaving roughly "
                f"{format_currency(projected_savings)} available to save.")
    return None


def _answer_reduce_expenses(question: str, user_id: int, monthly_income: float) -> str | None:
    q = question.lower()
    if "reduce" in q and "expense" in q:
        by_cat = spending_by_category(user_id)
        if by_cat.empty:
            return "I need some transaction history first before I can suggest where to cut back."
        top_3 = by_cat.head(3)
        lines = [f"- {r['category']}: {format_currency(r['amount'])}" for _, r in top_3.iterrows()]
        return ("Your highest spending categories are:\n" + "\n".join(lines) +
                "\n\nA common approach is trimming your top 1-2 categories by 10-15% and redirecting "
                "that toward savings or a goal — that alone can meaningfully improve your savings rate.")
    return None


def _answer_financial_health(question: str, user_id: int, monthly_income: float) -> str | None:
    q = question.lower()
    if "health" in q or "score" in q:
        ctx = _financial_context(user_id, monthly_income)
        h = ctx["health"]
        return (f"Your financial health score is {h['score']}/100 ({h['rating']}). {h['explanation']} "
                f"The area most holding you back right now is {h['weakest_area'].replace('_', ' ')}, "
                f"because {h['weakest_area_reason']}.")
    return None


def answer_question(question: str, user_id: int, monthly_income: float) -> dict:
    """Route a question through the deterministic analytics layer first;
    fall back to the LLM layer (if configured) for anything unmatched."""
    question = (question or "").strip()
    if not question:
        return {"answer": "Ask me something about your spending, budgets, savings, or financial health.",
                "disclaimer": DISCLAIMER}

    for handler in (
        lambda: _answer_can_i_save(question, user_id, monthly_income),
        lambda: _answer_reduce_expenses(question, user_id, monthly_income),
        lambda: _answer_financial_health(question, user_id, monthly_income),
        lambda: _answer_where_overspending(question, user_id),
        lambda: _answer_food_or_category_spend(question, user_id),
    ):
        result = handler()
        if result:
            return {"answer": result, "disclaimer": DISCLAIMER, "source": "analytics"}

    llm_answer = _try_llm(question, user_id, monthly_income)
    if llm_answer:
        return {"answer": llm_answer, "disclaimer": DISCLAIMER, "source": "llm"}

    return {
        "answer": ("I can answer questions like \"How much did I spend on Food?\", \"Where am I "
                   "spending the most?\", \"Can I save ₹5000 this month?\", \"How can I reduce my "
                   "expenses?\", or \"What is my financial health?\" — try rephrasing your question, "
                   "or set an AI_API_KEY in .env to enable free-form answers."),
        "disclaimer": DISCLAIMER, "source": "fallback",
    }


def _try_llm(question: str, user_id: int, monthly_income: float) -> str | None:
    api_key = os.getenv("AI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        import anthropic
        ctx = _financial_context(user_id, monthly_income)
        m = ctx["metrics"]
        by_cat = spending_by_category(user_id)
        cat_summary = ", ".join(f"{r['category']}: {r['amount']:.2f}" for _, r in by_cat.head(6).iterrows())

        system_prompt = (
            "You are FINJARVIS, a personal finance assistant. You are given ONLY this one user's "
            "own summarized financial data below — never assume or reference any other user's data. "
            "Answer concisely and practically. You are not a certified financial advisor; do not "
            "claim to be one, and keep suggestions informational rather than prescriptive.\n\n"
            f"Monthly income: {m['monthly_income']:.2f}\n"
            f"Monthly expenses: {m['monthly_expenses']:.2f}\n"
            f"Savings rate: {m['savings_rate']:.1f}%\n"
            f"Net worth: {m['net_worth']:.2f}\n"
            f"Financial health score: {ctx['health']['score']}/100 ({ctx['health']['rating']})\n"
            f"Top spending categories: {cat_summary or 'none recorded'}\n"
        )

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            system=system_prompt,
            messages=[{"role": "user", "content": question}],
        )
        text_parts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
        return "\n".join(text_parts).strip() or None
    except Exception:
        # Network/API failure -> degrade gracefully, caller falls back to the generic message
        return None


def generate_insights(user_id: int, monthly_income: float) -> list[str]:
    """Rule-based insights generated only from this user's real data."""
    insights = []
    trend_df = spending_by_category(user_id)
    if not trend_df.empty:
        top = trend_df.iloc[0]
        insights.append(f"{top['category']} is currently your largest expense category at "
                         f"{format_currency(top['amount'])}.")

    ctx = _financial_context(user_id, monthly_income)
    for b in ctx["budget_status"]:
        if b["percent_used"] >= 90:
            insights.append(f"You may exceed your {b['category']} budget this month "
                             f"({b['percent_used']:.0f}% used).")
    for g in ctx["goals"]:
        if g["status"] == "active" and g["percent_complete"] >= 70:
            insights.append(f"You are on track — your \"{g['goal_name']}\" goal is "
                             f"{g['percent_complete']:.0f}% complete.")

    if not insights:
        insights.append("Add a few transactions and budgets to start seeing personalized insights.")
    return insights
