"""
KnowledgeX AI - AI Abstraction Layer
========================================
Central switchboard between LOCAL MODE (default, fully offline: rule-based
reasoning, graph algorithms, scikit-learn similarity matching -- everything
this project ships with) and an optional EXTERNAL LLM API MODE that a
developer can enable later by setting AI_MODE=api and LLM_API_KEY in .env.

No component of the application is hard-dependent on a paid API. This file
is the single integration point to swap in a real LLM later.
"""
import os
from dotenv import load_dotenv

load_dotenv()

AI_MODE = os.getenv("AI_MODE", "local").lower()


def is_api_mode() -> bool:
    return AI_MODE == "api" and bool(os.getenv("LLM_API_KEY"))


def generate_text_response(prompt: str, context: str = "") -> str:
    """
    Generic entry point for any free-text AI generation used across the app.
    LOCAL MODE: returns a clearly-labelled deterministic local response.
    API MODE: placeholder integration point -- wire up your preferred LLM
    SDK here using the LLM_API_KEY from the environment.
    """
    if is_api_mode():
        # --- Integration point for an external LLM API ---
        # Example (pseudo-code):
        # import anthropic
        # client = anthropic.Anthropic(api_key=os.getenv("LLM_API_KEY"))
        # response = client.messages.create(...)
        # return response.content[0].text
        return "[API mode is enabled but no integration is wired up yet. Falling back to local logic.]"

    return f"[Local AI Mode] Based on available data: {context or prompt}"


def explain_recommendation(reason: str) -> str:
    """Wraps an explanation string so recommendations are always transparent
    to the student, per the 'explainable AI' requirement of the system."""
    return reason
