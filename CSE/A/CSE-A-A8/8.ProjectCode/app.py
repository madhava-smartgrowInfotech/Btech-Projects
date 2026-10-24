"""
app.py
------
AI-Powered Medical Lab Report Analysis & Health Insights Platform
Main Streamlit entry point: sidebar navigation + page routing.

Run with:
    streamlit run app.py
"""

import os
import time
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

import database as db
from report_processor import process_uploaded_report
from ai_insights import MEDICAL_DISCLAIMER
from ocr_processor import SUPPORTED_EXTENSIONS

load_dotenv()  # loads ANTHROPIC_API_KEY etc. from a local .env file, if present

# ---------------------------------------------------------------------------
# Page config + one-time DB init
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Medical Lab AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()

STATUS_COLORS = {"NORMAL": "#2E7D32", "LOW": "#F9A825", "HIGH": "#C62828", "UNKNOWN": "#616161"}
STATUS_ICONS = {"NORMAL": "🟢", "LOW": "🟡", "HIGH": "🔴", "UNKNOWN": "⚪"}


def status_badge(status: str) -> str:
    icon = STATUS_ICONS.get(status, "⚪")
    return f"{icon} {status}"


def show_disclaimer():
    st.info(f"⚕️ **Medical Disclaimer:** {MEDICAL_DISCLAIMER}")


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

PAGES = [
    "Home",
    "Dashboard",
    "Upload Report",
    "Report Analysis",
    "My Reports",
    "Health Trends",
    "Compare Reports",
    "Health Insights",
    "About",
]

with st.sidebar:
    st.markdown("## 🩺 Medical Lab AI")
    page = st.radio("Navigate", PAGES, label_visibility="collapsed")
    st.markdown("---")
    use_llm = st.toggle(
        "Use LLM for richer explanations",
        value=bool(os.environ.get("ANTHROPIC_API_KEY")),
        help="Requires ANTHROPIC_API_KEY to be set in your .env file. "
             "Falls back to built-in explanations if unavailable.",
    )
    st.session_state["use_llm_insights"] = use_llm
    st.markdown("---")
    st.caption("Educational tool only — not a medical device.")


# ---------------------------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------------------------

def page_home():
    st.title("AI-Powered Medical Lab Report Analysis")
    st.subheader(
        "Upload your laboratory report and convert complex medical information "
        "into simple, structured health insights."
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🚀 Get Started", type="primary", use_container_width=True):
            st.session_state["_nav_redirect"] = "Upload Report"
            st.rerun()

    st.markdown("---")

    st.header("✨ Features")
    f1, f2, f3, f4 = st.columns(4)
    f1.markdown("**📄 Multi-format Upload**\n\nPDF, JPG, JPEG, PNG lab reports.")
    f2.markdown("**🔍 OCR + AI Extraction**\n\nAutomatic test name, value & range extraction.")
    f3.markdown("**📊 Trends & Comparison**\n\nTrack results across multiple reports over time.")
    f4.markdown("**💡 Plain-language Insights**\n\nEducational explanations for abnormal results.")

    st.header("⚙️ How It Works")
    steps = [
        "Upload a lab report (PDF or image).",
        "The system extracts text using OCR / PDF parsing.",
        "Test names, values, units & reference ranges are identified.",
        "Each result is classified as Low, Normal, or High.",
        "You get a structured table plus plain-language explanations.",
    ]
    for i, s in enumerate(steps, 1):
        st.markdown(f"**{i}.** {s}")

    st.header("🌟 Benefits")
    b1, b2, b3 = st.columns(3)
    b1.markdown("- Understand your labs without medical jargon")
    b2.markdown("- Track health trends over time")
    b3.markdown("- Organize your lab history in one place")

    st.markdown("---")
    show_disclaimer()


# ---------------------------------------------------------------------------
# DASHBOARD PAGE
# ---------------------------------------------------------------------------

def page_dashboard():
    st.title("📊 Dashboard")

    stats = db.get_dashboard_stats()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Reports", stats["total_reports"])
    c2.metric("Total Tests", stats["total_tests"])
    c3.metric("Normal Results", stats["normal"])
    c4.metric("Abnormal Results", stats["abnormal"])
    c5.metric("Critical Alerts", stats["critical"], delta_color="inverse")

    st.markdown("---")
    st.subheader("Recent Reports")
    reports = db.get_all_reports()[:10]
    if not reports:
        st.info("No reports uploaded yet. Go to **Upload Report** to get started.")
        return

    rows = [{
        "ID": r.id,
        "File Name": r.file_name,
        "Type": (r.file_type or "").upper(),
        "Uploaded": r.upload_date.strftime("%Y-%m-%d %H:%M") if r.upload_date else "",
        "Status": r.processing_status,
    } for r in reports]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if stats["critical"] > 0:
        st.error(f"⚠️ {stats['critical']} result(s) are far outside the reference range. "
                 "Please review them in **Report Analysis** and consider consulting a doctor.")


# ---------------------------------------------------------------------------
# UPLOAD REPORT PAGE
# ---------------------------------------------------------------------------

def page_upload():
    st.title("📤 Upload Report")
    st.write("Supported formats: PDF, JPG, JPEG, PNG")

    uploaded_file = st.file_uploader(
        "Choose a lab report file",
        type=["pdf", "jpg", "jpeg", "png"],
    )

    if uploaded_file is None:
        return

    file_bytes = uploaded_file.getvalue()
    st.write(f"**File:** {uploaded_file.name}  ·  **Size:** {len(file_bytes) / 1024:.1f} KB")

    if st.button("Process Report", type="primary"):
        progress = st.progress(0, text="Uploading...")
        status_area = st.empty()

        stages = [
            (10, "Uploading..."),
            (30, "Processing..."),
            (55, "Extracting text..."),
            (80, "Analyzing results..."),
        ]
        for pct, label in stages:
            progress.progress(pct, text=label)
            time.sleep(0.15)  # brief pause so the status is visible to the user

        with st.spinner("Running OCR, extraction, and classification..."):
            result = process_uploaded_report(
                filename=uploaded_file.name,
                file_bytes=file_bytes,
                use_llm_insights=st.session_state.get("use_llm_insights", False),
            )

        if result.status == "Completed":
            progress.progress(100, text="Completed")
            status_area.success(
                f"✅ Report processed successfully. Stages completed: "
                f"{', '.join(result.stages_completed)}"
            )
            st.session_state["last_report_id"] = result.report_id

            st.subheader("Extracted Text (preview)")
            with st.expander("Show raw extracted text"):
                st.text(result.raw_text[:5000])

            st.subheader("Extracted & Classified Results")
            df = pd.DataFrame([c.as_dict() for c in result.classified_results])
            display_df = df[["test_name", "result_value", "unit", "reference_range", "status"]].rename(
                columns={
                    "test_name": "Test Name", "result_value": "Result", "unit": "Unit",
                    "reference_range": "Reference Range", "status": "Status",
                }
            )
            display_df["Status"] = display_df["Status"].apply(status_badge)
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            st.info("Go to **Report Analysis** or **My Reports** to view full details and insights.")
        else:
            progress.progress(100, text="Failed")
            status_area.error(f"❌ Processing failed: {result.error}")


# ---------------------------------------------------------------------------
# REPORT ANALYSIS PAGE
# ---------------------------------------------------------------------------

def page_report_analysis():
    st.title("🔬 Report Analysis")

    reports = db.get_all_reports()
    if not reports:
        st.info("No reports available. Upload one first.")
        return

    options = {f"#{r.id} — {r.file_name} ({r.upload_date.strftime('%Y-%m-%d')})": r.id for r in reports}
    default_id = st.session_state.get("last_report_id")
    default_label = next((k for k, v in options.items() if v == default_id), list(options.keys())[0])
    selected_label = st.selectbox("Select a report", list(options.keys()), index=list(options.keys()).index(default_label))
    report_id = options[selected_label]

    report = db.get_report_by_id(report_id)
    results = db.get_results_for_report(report_id)

    if report.processing_status != "Completed":
        st.warning(f"Report status: {report.processing_status}. {report.error_message or ''}")
        return

    if not results:
        st.info("No test results were extracted for this report.")
        return

    rows = []
    for r in results:
        low = r.reference_low
        high = r.reference_high
        if low is not None and high is not None:
            ref = f"{low} - {high}"
        elif high is not None:
            ref = f"< {high}"
        elif low is not None:
            ref = f"> {low}"
        else:
            ref = "N/A"
        rows.append({
            "Test Name": r.test_name, "Result": r.result_value, "Unit": r.unit,
            "Reference Range": ref, "Status": status_badge(r.status),
            "_status_raw": r.status, "_id": r.id,
        })
    df = pd.DataFrame(rows)

    st.subheader("All Results")
    st.dataframe(df.drop(columns=["_status_raw", "_id"]), use_container_width=True, hide_index=True)

    abnormal = df[df["_status_raw"].isin(["LOW", "HIGH"])]
    st.subheader(f"⚠️ Abnormal Results ({len(abnormal)})")
    if abnormal.empty:
        st.success("All results are within the normal reference range.")
    else:
        st.dataframe(abnormal.drop(columns=["_status_raw", "_id"]), use_container_width=True, hide_index=True)

        st.subheader("💡 AI Health Insights for Abnormal Results")
        for _, row in abnormal.iterrows():
            insight = db.get_insight_for_test_result(row["_id"])
            with st.expander(f"{status_badge(row['_status_raw'])} — {row['Test Name']}"):
                if insight:
                    st.write(f"**What this measures / means:** {insight.explanation}")
                    st.write(f"**Possible general causes:** {insight.possible_causes}")
                    st.write(f"**Suggestion:** {insight.recommendations}")
                else:
                    st.write("No insight available for this result.")

    show_disclaimer()


# ---------------------------------------------------------------------------
# MY REPORTS PAGE
# ---------------------------------------------------------------------------

def page_my_reports():
    st.title("🗂️ My Reports")

    reports = db.get_all_reports()
    if not reports:
        st.info("No reports uploaded yet.")
        return

    for r in reports:
        with st.expander(f"#{r.id} · {r.file_name} · {r.upload_date.strftime('%Y-%m-%d %H:%M')} · {r.processing_status}"):
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"**Type:** {(r.file_type or '').upper()}")
            c2.write(f"**Status:** {r.processing_status}")
            if r.error_message:
                st.error(r.error_message)
            results = db.get_results_for_report(r.id)
            if results:
                rows = [{"Test": t.test_name, "Result": t.result_value, "Unit": t.unit,
                         "Status": status_badge(t.status)} for t in results]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            if c3.button("🗑️ Delete", key=f"del_{r.id}"):
                db.delete_report(r.id)
                st.rerun()


# ---------------------------------------------------------------------------
# HEALTH TRENDS PAGE
# ---------------------------------------------------------------------------

def page_health_trends():
    st.title("📈 Health Trends")

    test_names = db.get_distinct_test_names()
    if not test_names:
        st.info("No test history yet. Upload at least one report first.")
        return

    selected_test = st.selectbox("Select a test to view its trend", test_names)
    rows = db.get_results_by_test_name(selected_test)

    if len(rows) < 1:
        st.info("No data available for this test.")
        return

    data = [{
        "Date": report.upload_date,
        "Result": tr.result_value,
        "Reference Low": tr.reference_low,
        "Reference High": tr.reference_high,
        "Status": tr.status,
    } for tr, report in rows]
    df = pd.DataFrame(data).sort_values("Date")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Result"], mode="lines+markers",
                              name=selected_test, line=dict(color="#1565C0", width=3)))
    if df["Reference Low"].notna().any():
        fig.add_trace(go.Scatter(x=df["Date"], y=df["Reference Low"], mode="lines",
                                  name="Reference Low", line=dict(dash="dot", color="#9E9E9E")))
    if df["Reference High"].notna().any():
        fig.add_trace(go.Scatter(x=df["Date"], y=df["Reference High"], mode="lines",
                                  name="Reference High", line=dict(dash="dot", color="#9E9E9E")))
    fig.update_layout(title=f"{selected_test} Over Time", xaxis_title="Date", yaxis_title="Result")
    st.plotly_chart(fig, use_container_width=True)

    if len(df) >= 2:
        first, last = df["Result"].iloc[0], df["Result"].iloc[-1]
        if last > first:
            direction = "increasing 📈"
        elif last < first:
            direction = "decreasing 📉"
        else:
            direction = "stable ➡️"
        st.write(f"**Overall pattern across your uploaded reports:** {direction}")
        st.caption(
            "This reflects the trend across the reports you've uploaded only, and is not a "
            "medical conclusion. Please discuss any trend with a healthcare professional."
        )

    st.dataframe(df, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# COMPARE REPORTS PAGE
# ---------------------------------------------------------------------------

def page_compare_reports():
    st.title("⚖️ Compare Reports")

    reports = db.get_all_reports()
    completed = [r for r in reports if r.processing_status == "Completed"]
    if len(completed) < 2:
        st.info("You need at least two completed reports to compare.")
        return

    options = {f"#{r.id} — {r.file_name} ({r.upload_date.strftime('%Y-%m-%d')})": r.id for r in completed}
    labels = list(options.keys())
    col1, col2 = st.columns(2)
    label1 = col1.selectbox("Report 1", labels, index=min(1, len(labels) - 1))
    label2 = col2.selectbox("Report 2", labels, index=0)

    id1, id2 = options[label1], options[label2]
    if id1 == id2:
        st.warning("Please select two different reports.")
        return

    results1 = {t.test_name: t for t in db.get_results_for_report(id1)}
    results2 = {t.test_name: t for t in db.get_results_for_report(id2)}
    common_tests = sorted(set(results1.keys()) & set(results2.keys()))

    if not common_tests:
        st.info("These two reports have no lab tests in common.")
        return

    rows = []
    for name in common_tests:
        rows.append({
            "Test": name,
            "Report 1": results1[name].result_value,
            "Report 2": results2[name].result_value,
            "Unit": results1[name].unit,
            "Change": round(results2[name].result_value - results1[name].result_value, 2)
            if results1[name].result_value is not None and results2[name].result_value is not None else None,
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    fig = px.bar(df, x="Test", y=["Report 1", "Report 2"], barmode="group",
                 title="Report 1 vs Report 2")
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# HEALTH INSIGHTS PAGE (all abnormal results across all reports)
# ---------------------------------------------------------------------------

def page_health_insights():
    st.title("💡 Health Insights")
    st.write("A consolidated view of AI-generated explanations for every abnormal result on file.")

    all_results = db.get_all_test_results()
    abnormal = [r for r in all_results if r.status in ("LOW", "HIGH")]

    if not abnormal:
        st.success("No abnormal results on file. 🎉")
        show_disclaimer()
        return

    for r in abnormal:
        insight = db.get_insight_for_test_result(r.id)
        with st.expander(f"{status_badge(r.status)} — {r.test_name} ({r.result_value} {r.unit or ''})"):
            if insight:
                st.write(f"**Explanation:** {insight.explanation}")
                st.write(f"**Possible general causes:** {insight.possible_causes}")
                st.write(f"**Suggestion:** {insight.recommendations}")
            else:
                st.write("No insight generated for this result yet.")

    show_disclaimer()


# ---------------------------------------------------------------------------
# ABOUT PAGE
# ---------------------------------------------------------------------------

def page_about():
    st.title("ℹ️ About")
    st.write(
        "**AI-Powered Medical Lab Report Analysis & Health Insights Platform** is an "
        "educational tool that extracts, organizes, and explains laboratory test results "
        "from uploaded PDF or image reports."
    )
    st.subheader("Technology Stack")
    st.markdown(
        "- **Streamlit** — web application UI\n"
        "- **SQLite + SQLAlchemy** — data storage\n"
        "- **PyMuPDF** — PDF text extraction\n"
        "- **OpenCV + Tesseract OCR** — scanned document/image OCR\n"
        "- **scikit-learn** — fuzzy test-name normalization\n"
        "- **spaCy** — optional metadata NER\n"
        "- **Plotly** — trend and comparison charts\n"
    )
    st.subheader("Limitations")
    st.markdown(
        "- OCR accuracy depends on scan/photo quality.\n"
        "- Only lab report layouts with recognizable name/value/range rows are supported.\n"
        "- This is **not** a diagnostic tool and does not replace professional medical advice."
    )
    show_disclaimer()


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

if "_nav_redirect" in st.session_state:
    page = st.session_state.pop("_nav_redirect")

ROUTES = {
    "Home": page_home,
    "Dashboard": page_dashboard,
    "Upload Report": page_upload,
    "Report Analysis": page_report_analysis,
    "My Reports": page_my_reports,
    "Health Trends": page_health_trends,
    "Compare Reports": page_compare_reports,
    "Health Insights": page_health_insights,
    "About": page_about,
}

ROUTES.get(page, page_home)()
