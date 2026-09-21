"""Notifications page."""
from __future__ import annotations

import streamlit as st

from database.database import get_session
from database.models import Notification


def render(user):
    st.title("🔔 Notifications")

    with get_session() as session:
        notes = session.query(Notification).filter(
            Notification.user_id == user.id
        ).order_by(Notification.created_at.desc()).all()
        notes_data = [
            {"id": n.id, "message": n.message, "type": n.notification_type,
             "created_at": n.created_at, "is_read": n.is_read}
            for n in notes
        ]

    if not notes_data:
        st.info("No notifications yet. They'll appear here as your budgets, goals, and spending change.")
        return

    if st.button("Mark all as read"):
        with get_session() as session:
            session.query(Notification).filter(Notification.user_id == user.id).update({"is_read": True})
        st.rerun()

    for n in notes_data:
        icon = {"danger": "🔴", "warning": "🟠", "success": "🟢", "info": "🔵"}.get(n["type"], "🔵")
        prefix = "" if n["is_read"] else "**[NEW]** "
        st.write(f"{icon} {prefix}{n['message']}")
        st.caption(str(n["created_at"]))
        st.divider()
