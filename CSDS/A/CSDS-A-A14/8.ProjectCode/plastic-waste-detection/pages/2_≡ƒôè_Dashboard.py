"""
pages/2_📊_Dashboard.py
------------------------
Aggregate statistics dashboard + Detection History, built from
the SQLite detection_history table (real logged runs only —
no fabricated numbers).
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from src.database import clear_history, get_history

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.title("📊 Dashboard")

history = get_history()

if not history:
    st.info(
        "No detection history yet. Run a detection on the Detection page — "
        "every analysed image is automatically logged here."
    )
    st.stop()

df = pd.DataFrame(history)
df["avg_confidence_pct"] = (df["avg_confidence"] * 100).round(1)

# ---- Summary cards ----
total_images = len(df)
total_objects = int(df["object_count"].sum())
avg_conf = df["avg_confidence_pct"].mean()
max_conf = df["avg_confidence_pct"].max()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Images Analysed", total_images)
c2.metric("Total Plastic Objects Detected", total_objects)
c3.metric("Average Confidence", f"{avg_conf:.1f}%")
c4.metric("Highest Confidence", f"{max_conf:.1f}%")

st.divider()

# ---- Charts ----
col1, col2 = st.columns(2)

with col1:
    st.subheader("Objects Detected per Image")
    fig1 = px.bar(df.iloc[::-1], x="filename", y="object_count",
                   labels={"filename": "Image", "object_count": "Objects Detected"})
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Confidence Distribution")
    fig2 = px.histogram(df, x="avg_confidence_pct", nbins=10,
                         labels={"avg_confidence_pct": "Average Confidence (%)"})
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Detection History Over Time")
fig3 = px.line(df.iloc[::-1], x="timestamp", y="object_count", markers=True,
                labels={"timestamp": "Time", "object_count": "Objects Detected"})
st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ---- History table ----
st.subheader("Detection History")
display_df = df.rename(columns={
    "filename": "Filename",
    "object_count": "Objects",
    "avg_confidence_pct": "Avg Confidence (%)",
    "timestamp": "Date",
})[["Filename", "Objects", "Avg Confidence (%)", "Date"]]
st.dataframe(display_df, use_container_width=True)

if st.button("🗑️ Clear History", type="secondary"):
    clear_history()
    st.success("History cleared.")
    st.rerun()
