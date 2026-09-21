"""FINJARVIS AI Assistant chat page."""
from __future__ import annotations

import os
import streamlit as st

from services.ai_service import answer_question, generate_insights, DISCLAIMER


def render(user):
    st.title("🤖 FINJARVIS AI Assistant")
    st.caption(DISCLAIMER)

    if not os.getenv("AI_API_KEY", "").strip():
        st.info("Free-form AI chat is currently running on built-in analytics only. "
                 "Set AI_API_KEY in your .env file to enable richer natural-language answers.")

    st.subheader("💡 Insights")
    for insight in generate_insights(user.id, user.monthly_income):
        st.write(f"- {insight}")

    st.divider()
    st.subheader("Ask FINJARVIS")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for role, message in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(message)

    examples = [
        "How much did I spend on Food this month?",
        "Where am I spending the most money?",
        "Can I save ₹10000 this month?",
        "How can I reduce my expenses?",
        "What is my financial health?",
    ]
    st.caption("Try: " + " · ".join(examples))

    question = st.chat_input("Ask about your spending, budgets, savings, or financial health...")
    if question:
        st.session_state.chat_history.append(("user", question))
        with st.chat_message("user"):
            st.write(question)

        result = answer_question(question, user.id, user.monthly_income)
        with st.chat_message("assistant"):
            st.write(result["answer"])
        st.session_state.chat_history.append(("assistant", result["answer"]))
