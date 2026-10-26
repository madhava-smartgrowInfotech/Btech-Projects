"""
visualization.py
-------------------
All Plotly chart-building functions live here, kept separate from the
Streamlit page code so charts are reusable and easy to test/tweak.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_daily_trend(daily_demand: pd.DataFrame) -> go.Figure:
    """Total demand across ALL products, per day."""
    trend = daily_demand.groupby("t_dat")["demand"].sum().reset_index()
    fig = px.line(trend, x="t_dat", y="demand", title="Daily Total Demand Trend")
    fig.update_layout(xaxis_title="Date", yaxis_title="Units Sold")
    return fig


def plot_monthly_demand(daily_demand: pd.DataFrame) -> go.Figure:
    df = daily_demand.copy()
    df["month"] = df["t_dat"].dt.to_period("M").astype(str)
    monthly = df.groupby("month")["demand"].sum().reset_index()
    fig = px.bar(monthly, x="month", y="demand", title="Monthly Total Demand")
    fig.update_layout(xaxis_title="Month", yaxis_title="Units Sold")
    return fig


def plot_weekly_demand(daily_demand: pd.DataFrame) -> go.Figure:
    df = daily_demand.copy()
    df["week"] = df["t_dat"].dt.to_period("W").astype(str)
    weekly = df.groupby("week")["demand"].sum().reset_index()
    fig = px.line(weekly, x="week", y="demand", title="Weekly Total Demand")
    fig.update_layout(xaxis_title="Week", yaxis_title="Units Sold")
    return fig


def plot_top_products(daily_demand: pd.DataFrame, top_n: int = 10) -> go.Figure:
    top = daily_demand.groupby("article_id")["demand"].sum().sort_values(ascending=False).head(top_n)
    fig = px.bar(
        x=top.values, y=top.index.astype(str), orientation="h", title=f"Top {top_n} Products by Total Demand"
    )
    fig.update_layout(xaxis_title="Total Units Sold", yaxis_title="Article ID")
    fig.update_yaxes(autorange="reversed")
    return fig


def plot_categorical_demand(daily_demand: pd.DataFrame, category_col: str, top_n: int = 15) -> go.Figure:
    """Generic bar chart of demand summed by any categorical column (department, colour, etc.)."""
    if category_col not in daily_demand.columns:
        return go.Figure()
    grouped = (
        daily_demand.groupby(category_col)["demand"].sum().sort_values(ascending=False).head(top_n)
    )
    fig = px.bar(x=grouped.index.astype(str), y=grouped.values, title=f"Demand by {category_col}")
    fig.update_layout(xaxis_title=category_col, yaxis_title="Total Units Sold")
    return fig


def plot_price_distribution(daily_demand: pd.DataFrame) -> go.Figure:
    fig = px.histogram(daily_demand, x="price", nbins=50, title="Price Distribution")
    fig.update_layout(xaxis_title="Price", yaxis_title="Count")
    return fig


def plot_feature_importance(importance_pairs: list[tuple[str, float]]) -> go.Figure:
    features = [p[0] for p in importance_pairs][::-1]
    values = [p[1] for p in importance_pairs][::-1]
    fig = px.bar(x=values, y=features, orientation="h", title="Feature Importance (XGBoost)")
    fig.update_layout(xaxis_title="Importance", yaxis_title="Feature")
    return fig


def plot_model_comparison(comparison_df: pd.DataFrame, metric: str = "RMSE") -> go.Figure:
    fig = px.bar(comparison_df, x="Model", y=metric, title=f"Model Comparison — {metric}")
    return fig


def plot_domain_shift_histogram(source_series, target_series, feature_name: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=source_series, name="Source", opacity=0.6))
    fig.add_trace(go.Histogram(x=target_series, name="Target", opacity=0.6))
    fig.update_layout(
        barmode="overlay", title=f"Distribution Comparison: {feature_name}", xaxis_title=feature_name
    )
    return fig


def plot_domain_shift_boxplot(source_series, target_series, feature_name: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Box(y=source_series, name="Source"))
    fig.add_trace(go.Box(y=target_series, name="Target"))
    fig.update_layout(title=f"Box Plot Comparison: {feature_name}", yaxis_title=feature_name)
    return fig


def plot_forecast(history_df: pd.DataFrame, forecast_df: pd.DataFrame) -> go.Figure:
    """
    WHAT: Line chart showing recent historical demand followed by the
          predicted future demand, visually joined at the transition point.
    """
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=history_df["t_dat"], y=history_df["demand"], mode="lines", name="Historical Demand")
    )
    fig.add_trace(
        go.Scatter(
            x=forecast_df["t_dat"],
            y=forecast_df["predicted_demand"],
            mode="lines+markers",
            name="Forecasted Demand",
            line=dict(dash="dash"),
        )
    )
    fig.update_layout(title="Demand Forecast", xaxis_title="Date", yaxis_title="Demand")
    return fig
