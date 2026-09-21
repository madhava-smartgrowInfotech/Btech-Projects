"""Generates monthly financial reports as PDF (ReportLab), Excel (OpenPyXL via
pandas), and CSV. All data pulled fresh, scoped to the requesting user only."""
from __future__ import annotations

import os
from datetime import date
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from services.analytics_service import summary_metrics, spending_by_category
from services.budget_service import get_budget_status
from services.investment_service import portfolio_summary
from services.transaction_service import get_transactions
from ml.financial_health import calculate_financial_health
from services.ai_service import generate_insights
from utils.helpers import format_currency, month_name

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def _build_report_data(user_id: int, month: int, year: int, monthly_income: float) -> dict:
    metrics = summary_metrics(user_id, month, year, monthly_income)
    budget_status = get_budget_status(user_id, month, year)
    by_cat = spending_by_category(user_id)
    port = portfolio_summary(user_id)
    health = calculate_financial_health(
        monthly_income=metrics["monthly_income"], monthly_expenses=metrics["monthly_expenses"],
        savings_rate=metrics["savings_rate"], total_balance=metrics["total_balance"],
        budget_status=budget_status, holdings=port["holdings"], goals=[],
    )
    insights = generate_insights(user_id, monthly_income)
    return {
        "metrics": metrics, "budget_status": budget_status, "by_category": by_cat,
        "portfolio": port, "health": health, "insights": insights,
        "month": month, "year": year,
    }


def generate_pdf_report(user_id: int, month: int, year: int, monthly_income: float, user_name: str) -> str:
    data = _build_report_data(user_id, month, year, monthly_income)
    filepath = os.path.join(REPORTS_DIR, f"finjarvis_report_{user_id}_{year}_{month:02d}.pdf")

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("FINJARVIS Monthly Financial Report", styles["Title"]),
        Paragraph(f"{user_name} — {month_name(month)} {year}", styles["Normal"]),
        Spacer(1, 16),
        Paragraph("Summary", styles["Heading2"]),
    ]

    m = data["metrics"]
    summary_rows = [
        ["Metric", "Value"],
        ["Monthly Income", format_currency(m["monthly_income"])],
        ["Monthly Expenses", format_currency(m["monthly_expenses"])],
        ["Monthly Savings", format_currency(m["monthly_savings"])],
        ["Savings Rate", f"{m['savings_rate']:.1f}%"],
        ["Net Worth", format_currency(m["net_worth"])],
        ["Financial Health Score", f"{data['health']['score']}/100 ({data['health']['rating']})"],
    ]
    story.append(_styled_table(summary_rows))
    story.append(Spacer(1, 16))

    if not data["by_category"].empty:
        story.append(Paragraph("Category-wise Expenses", styles["Heading2"]))
        cat_rows = [["Category", "Amount"]] + [
            [r["category"], format_currency(r["amount"])] for _, r in data["by_category"].iterrows()
        ]
        story.append(_styled_table(cat_rows))
        story.append(Spacer(1, 16))

    if data["budget_status"]:
        story.append(Paragraph("Budget Performance", styles["Heading2"]))
        b_rows = [["Category", "Budget", "Spent", "% Used"]] + [
            [b["category"], format_currency(b["budget_amount"]), format_currency(b["actual_spent"]),
             f"{b['percent_used']:.0f}%"] for b in data["budget_status"]
        ]
        story.append(_styled_table(b_rows))
        story.append(Spacer(1, 16))

    port = data["portfolio"]
    story.append(Paragraph("Investment Summary", styles["Heading2"]))
    story.append(_styled_table([
        ["Total Invested", format_currency(port["total_invested"])],
        ["Current Value", format_currency(port["total_current_value"])],
        ["Profit/Loss", format_currency(port["total_profit_loss"])],
        ["Return %", f"{port['total_return_percent']:.2f}%"],
    ]))
    story.append(Spacer(1, 16))

    story.append(Paragraph("AI-Generated Observations", styles["Heading2"]))
    for insight in data["insights"]:
        story.append(Paragraph(f"• {insight}", styles["Normal"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Disclaimer: These observations are generated from your own recorded data and are "
        "informational only, not professional financial advice.", styles["Italic"]
    ))

    doc.build(story)
    return filepath


def _styled_table(rows: list[list[str]]) -> Table:
    table = Table(rows, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
    ]))
    return table


def generate_excel_report(user_id: int, month: int, year: int, monthly_income: float) -> str:
    data = _build_report_data(user_id, month, year, monthly_income)
    filepath = os.path.join(REPORTS_DIR, f"finjarvis_report_{user_id}_{year}_{month:02d}.xlsx")

    m = data["metrics"]
    summary_df = pd.DataFrame([
        {"Metric": "Monthly Income", "Value": m["monthly_income"]},
        {"Metric": "Monthly Expenses", "Value": m["monthly_expenses"]},
        {"Metric": "Monthly Savings", "Value": m["monthly_savings"]},
        {"Metric": "Savings Rate (%)", "Value": m["savings_rate"]},
        {"Metric": "Net Worth", "Value": m["net_worth"]},
        {"Metric": "Financial Health Score", "Value": data["health"]["score"]},
    ])
    txns_df = pd.DataFrame(get_transactions(user_id))
    budget_df = pd.DataFrame(data["budget_status"])
    holdings_df = pd.DataFrame(data["portfolio"]["holdings"])

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        if not data["by_category"].empty:
            data["by_category"].to_excel(writer, sheet_name="Category Spending", index=False)
        if not txns_df.empty:
            txns_df.to_excel(writer, sheet_name="Transactions", index=False)
        if not budget_df.empty:
            budget_df.to_excel(writer, sheet_name="Budgets", index=False)
        if not holdings_df.empty:
            holdings_df.to_excel(writer, sheet_name="Investments", index=False)

    return filepath


def generate_csv_report(user_id: int) -> str:
    filepath = os.path.join(REPORTS_DIR, f"finjarvis_transactions_{user_id}.csv")
    df = pd.DataFrame(get_transactions(user_id))
    df.to_csv(filepath, index=False)
    return filepath
