"""Reports page: generate and download PDF/Excel/CSV reports."""
from __future__ import annotations

import streamlit as st

from services.report_service import generate_pdf_report, generate_excel_report, generate_csv_report
from utils.helpers import current_month_year, month_name


def render(user):
    st.title("📄 Financial Reports")

    month, year = current_month_year()
    col1, col2 = st.columns(2)
    with col1:
        month = st.selectbox("Month", list(range(1, 13)), index=month - 1, format_func=month_name)
    with col2:
        year = st.number_input("Year", min_value=2020, max_value=2100, value=year, step=1)

    st.write("Generate a monthly report including income, expenses, savings, category breakdown, "
             "budget performance, financial health score, investment summary, and AI observations.")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Generate PDF Report", use_container_width=True):
            try:
                path = generate_pdf_report(user.id, month, year, user.monthly_income, user.name)
                with open(path, "rb") as f:
                    st.download_button("Download PDF", f, file_name=f"finjarvis_report_{year}_{month:02d}.pdf",
                                        mime="application/pdf", use_container_width=True)
            except Exception as e:
                st.error(f"Could not generate PDF report: {e}")

    with col2:
        if st.button("Generate Excel Report", use_container_width=True):
            try:
                path = generate_excel_report(user.id, month, year, user.monthly_income)
                with open(path, "rb") as f:
                    st.download_button("Download Excel", f, file_name=f"finjarvis_report_{year}_{month:02d}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        use_container_width=True)
            except Exception as e:
                st.error(f"Could not generate Excel report: {e}")

    with col3:
        if st.button("Export Transactions CSV", use_container_width=True):
            try:
                path = generate_csv_report(user.id)
                with open(path, "rb") as f:
                    st.download_button("Download CSV", f, file_name="finjarvis_transactions.csv",
                                        mime="text/csv", use_container_width=True)
            except Exception as e:
                st.error(f"Could not generate CSV export: {e}")
