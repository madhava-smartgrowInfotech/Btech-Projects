"""
Attendance Magic — Streamlit entry point.

    streamlit run app.py

Routes:
  /                  landing page (faculty portal / student portal tabs)
  /?session=TOKEN    student check-in for a specific session
"""
from __future__ import annotations

import streamlit as st

import config
from core.db import init_db
from ui import faculty, student

st.set_page_config(page_title=config.APP_NAME, page_icon="🪄", layout="wide")


@st.cache_resource(show_spinner=False)
def _bootstrap() -> bool:
    init_db()
    return True


@st.cache_resource(show_spinner="Loading face models (first run only)…")
def _warm_models() -> dict:
    """Load MediaPipe + InsightFace once per server process."""
    from core import face_match, liveness

    det = liveness.get_detector()
    face_match.get_embedder()
    return {"landmarks": det.backend, "recognition": f"insightface/{config.INSIGHTFACE_MODEL}"}


_bootstrap()

st.markdown(f"## 🪄 {config.APP_NAME}")
st.caption(config.APP_TAGLINE)

token = st.query_params.get("session")

if token:
    _warm_models()
    student.render(token)
else:
    tab_f, tab_s, tab_about = st.tabs(["👩‍🏫 Faculty portal", "🎓 Student portal", "ℹ️ How it works"])
    with tab_f:
        faculty.render()
    with tab_s:
        _warm_models()
        student.render(None)
    with tab_about:
        st.markdown(
            """
            **Attendance Magic** blocks proxy attendance by verifying *location, liveness and identity*
            together inside a time-bound session:

            1. **Session** — faculty create a time window with a GPS geo-fence and a unique link.
            2. **JWT authentication** — students sign in; the token is bound to their device fingerprint.
            3. **Roll-number & device restrictions** — only allowed roll numbers, one device per student,
               one roll number per device per session.
            4. **GPS verification** — the browser's location is checked against the geo-fence (haversine).
            5. **Live challenge** — a *random* action (turn head, open mouth, …) is verified with
               MediaPipe Face Mesh landmarks, so photos and videos can't pass.
            6. **Face matching** — InsightFace (ArcFace) embeddings confirm identity against the enrolled
               face and reject any face already recorded in the session under another roll number.
            7. **Records & export** — faculty see live records, a verification log, and export to Excel.
            """
        )
        models = _warm_models()
        st.caption(f"Landmarks: `{models['landmarks']}` · Recognition: `{models['recognition']}` · "
                   f"DB: `{config.DATABASE_URL.split('://')[0]}`")
