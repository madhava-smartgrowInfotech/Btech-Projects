"""
eda.py
-------
Exploratory Data Analysis helpers: KPI computation and Plotly figure
builders used by the Exploratory Analysis and Dashboard pages. Kept
free of Streamlit calls so it can be unit tested independently.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils import make_tenure_group, safe_divide


def compute_kpis(df: pd.DataFrame, target_col: str, churn_positive_series: pd.Series) -> dict:
    total = len(df)
    churned = int(churn_positive_series.sum())
    retained = total - churned
    kpis = {
        "total_customers": total,
        "churned_customers": churned,
        "retained_customers": retained,
        "churn_rate_pct": round(100 * safe_divide(churned, total), 2),
    }
    if "tenure" in df.columns:
        kpis["avg_tenure"] = round(df["tenure"].mean(), 1)
    if "MonthlyCharges" in df.columns:
        kpis["avg_monthly_charges"] = round(df["MonthlyCharges"].mean(), 2)
    if "TotalCharges" in df.columns:
        kpis["avg_total_charges"] = round(pd.to_numeric(df["TotalCharges"], errors="coerce").mean(), 2)
    return kpis


def churn_distribution_fig(churn_series: pd.Series):
    counts = churn_series.value_counts().rename({0: "Retained", 1: "Churned"})
    fig = px.pie(values=counts.values, names=counts.index, title="Churn Distribution",
                 color=counts.index, color_discrete_map={"Retained": "#2ecc71", "Churned": "#e74c3c"}, hole=0.45)
    return fig


def churn_by_category_fig(df: pd.DataFrame, category_col: str, churn_series: pd.Series, title: str = None):
    tmp = df.copy()
    tmp["_churn"] = churn_series.values
    grouped = tmp.groupby(category_col)["_churn"].agg(["mean", "count"]).reset_index()
    grouped["churn_rate_pct"] = (grouped["mean"] * 100).round(1)
    fig = px.bar(
        grouped.sort_values("churn_rate_pct", ascending=False), x=category_col, y="churn_rate_pct",
        title=title or f"Churn Rate by {category_col}", text="churn_rate_pct",
        color="churn_rate_pct", color_continuous_scale="Reds",
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(yaxis_title="Churn Rate (%)", coloraxis_showscale=False)
    return fig


def churn_by_numeric_fig(df: pd.DataFrame, numeric_col: str, churn_series: pd.Series, title: str = None, nbins: int = 30):
    tmp = df.copy()
    tmp["_churn_label"] = np.where(churn_series.values == 1, "Churned", "Retained")
    fig = px.histogram(
        tmp, x=numeric_col, color="_churn_label", barmode="overlay", nbins=nbins,
        title=title or f"Distribution of {numeric_col} by Churn",
        color_discrete_map={"Retained": "#2ecc71", "Churned": "#e74c3c"}, opacity=0.65,
    )
    fig.update_layout(legend_title_text="")
    return fig


def churn_by_tenure_group_fig(df: pd.DataFrame, churn_series: pd.Series):
    tmp = df.copy()
    tmp["_tenure_group"] = make_tenure_group(tmp["tenure"])
    tmp["_churn"] = churn_series.values
    grouped = tmp.groupby("_tenure_group", observed=True)["_churn"].mean().reset_index()
    grouped["churn_rate_pct"] = (grouped["_churn"] * 100).round(1)
    fig = px.bar(grouped, x="_tenure_group", y="churn_rate_pct", title="Churn Rate by Tenure Group",
                 text="churn_rate_pct", color="churn_rate_pct", color_continuous_scale="Reds")
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(xaxis_title="Tenure Group", yaxis_title="Churn Rate (%)", coloraxis_showscale=False)
    return fig


def correlation_heatmap_fig(df: pd.DataFrame, numeric_cols: list):
    corr = df[numeric_cols].corr()
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                     title="Correlation Between Numerical Features")
    return fig


def top_churn_drivers_bar(importance_df: pd.DataFrame, label_fn=None, top_n: int = 10, title: str = "Top Churn Drivers"):
    top = importance_df.head(top_n).copy()
    if label_fn:
        top["feature"] = top["feature"].apply(label_fn)
    fig = px.bar(top.sort_values("importance"), x="importance", y="feature", orientation="h", title=title,
                 color="importance", color_continuous_scale="Blues")
    fig.update_layout(coloraxis_showscale=False, yaxis_title="", xaxis_title="Importance")
    return fig
