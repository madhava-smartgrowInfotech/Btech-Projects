"""
gemini_helper.py
-------------------
Optional AI-Insights feature. Uses Google's Gemini API purely to EXPLAIN
results in plain language -- it never makes forecasts itself, and we
never send raw transaction data to it. We only send small, aggregated
summaries (metrics, feature importance, domain-shift stats).

The app must work perfectly fine with this feature disabled (no API key
configured), which is why every function here fails gracefully.
"""

from __future__ import annotations

import json
import streamlit as st


def is_gemini_available() -> bool:
    """Checks whether a Gemini API key has been configured via st.secrets."""
    try:
        return bool(st.secrets.get("GEMINI_API_KEY"))
    except Exception:
        return False


def _get_model():
    """Lazily imports and configures the Gemini client, only when needed."""
    import google.generativeai as genai

    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")


def build_context_summary(
    metrics: dict | None = None,
    feature_importance: list[tuple[str, float]] | None = None,
    domain_shift: dict | None = None,
    forecast_summary: dict | None = None,
) -> str:
    """
    WHAT: Builds a small JSON blob of AGGREGATED information to send to
          Gemini -- never the raw dataset.
    """
    context = {}
    if metrics:
        context["model_metrics"] = metrics
    if feature_importance:
        context["top_features"] = [{"feature": f, "importance": round(float(i), 4)} for f, i in feature_importance[:10]]
    if domain_shift:
        context["domain_shift"] = domain_shift
    if forecast_summary:
        context["forecast_summary"] = forecast_summary

    return json.dumps(context, indent=2, default=str)


def get_ai_explanation(question: str, context_summary: str) -> str:
    """
    WHAT: Sends the user's question + the aggregated context summary to
          Gemini and returns its plain-language explanation.
    WHY:  Helps a non-technical examiner/guide understand WHY the model
          behaved the way it did, grounded in the actual numbers computed
          by the app (not fabricated).
    """
    if not is_gemini_available():
        return (
            "AI Insights is not configured. Add a GEMINI_API_KEY to "
            ".streamlit/secrets.toml to enable this optional feature. "
            "The rest of the app works fully without it."
        )

    prompt = f"""You are helping explain a fashion demand forecasting ML project
to a student and their project examiner. Base your explanation ONLY on
the data below -- do not invent numbers or facts not present here.

DATA SUMMARY:
{context_summary}

QUESTION:
{question}

Answer in clear, simple, plain language suitable for a project demo."""

    try:
        model = _get_model()
        response = model.generate_content(prompt)
        return response.text
    except Exception as exc:
        return f"AI Insights is temporarily unavailable ({exc}). You can still use every other part of the app."


def get_forecast_summary(forecast_df, feature_importance: list[tuple[str, float]] | None = None) -> str:
    """
    WHAT: Generates a short natural-language summary of a forecast run,
          e.g. "Demand is expected to increase over the next 7 days...".
    WHY:  Required by the project spec as an optional post-forecast
          explanation. Grounded strictly in the forecast numbers.
    """
    if forecast_df is None or forecast_df.empty:
        return "No forecast data available to summarize."

    start_val = forecast_df["predicted_demand"].iloc[0]
    end_val = forecast_df["predicted_demand"].iloc[-1]
    trend = "increase" if end_val > start_val else ("decrease" if end_val < start_val else "stay stable")

    context = build_context_summary(
        forecast_summary={
            "horizon_days": len(forecast_df),
            "start_predicted_demand": round(float(start_val), 2),
            "end_predicted_demand": round(float(end_val), 2),
            "trend": trend,
        },
        feature_importance=feature_importance,
    )

    question = "Summarize this demand forecast in 2-3 short sentences for a project demo."
    return get_ai_explanation(question, context)
