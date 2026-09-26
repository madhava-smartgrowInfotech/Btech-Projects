"""Faculty portal: create geo-fenced sessions, monitor attendance, export Excel."""
from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

import config
from core import export, liveness, services, timeutil
from ui import common


def render() -> None:
    claims = common.current_claims()
    if claims is None:
        st.subheader("Faculty portal")
        t1, t2 = st.tabs(["Sign in", "Register"])
        with t1:
            common.login_form("faculty", "faculty")
        with t2:
            common.register_form("faculty", "faculty")
        return
    if claims.role != "faculty":
        st.error("You are signed in as a student. Sign out to use the faculty portal.")
        if st.button("Sign out"):
            common.logout()
            st.rerun()
        return

    with st.sidebar:
        st.markdown(f"**👩‍🏫 {claims.full_name}**  \nFaculty · token expires {claims.expires_at.astimezone(timeutil.LOCAL_TZ):%H:%M}")
        if st.button("Sign out", use_container_width=True):
            common.logout()
            st.rerun()

    tab_new, tab_sessions, tab_students = st.tabs(["➕ Create session", "📋 Sessions & records", "🎓 Students"])
    with tab_new:
        _create_session(claims)
    with tab_sessions:
        _sessions(claims)
    with tab_students:
        _students()


# --------------------------------------------------------------------------- #
def _create_session(claims) -> None:
    st.markdown("Create a **time-bound, geo-fenced** attendance session and share the unique link.")
    c1, c2, c3 = st.columns([1, 2, 1])
    course_code = c1.text_input("Course code", placeholder="CS601")
    course_name = c2.text_input("Course name", placeholder="Machine Learning")
    section = c3.text_input("Section", placeholder="CSDS-A")

    now_local = timeutil.now_local()
    c4, c5, c6 = st.columns(3)
    date = c4.date_input("Date", value=now_local.date())
    start_time = c5.time_input("Start time", value=now_local.time().replace(second=0, microsecond=0))
    duration = c6.number_input("Duration (minutes)", min_value=1, max_value=600, value=15)

    loc = common.location_picker("create")
    radius = st.slider("Geo-fence radius (metres)", 10, 500, int(config.DEFAULT_GEOFENCE_RADIUS_M), 5)
    allowed = st.text_input(
        "Allowed roll numbers (comma-separated, wildcards ok)", value="*",
        help="Examples: `23K91A67*` (all with that prefix) or `23K91A6706,23K91A6740` (explicit list). `*` = anyone.",
    )
    if loc:
        st.map(pd.DataFrame({"lat": [loc["lat"]], "lon": [loc["lon"]]}), zoom=16, size=radius)

    if st.button("Create session", type="primary", disabled=loc is None):
        try:
            starts_local = datetime.combine(date, start_time)
            starts_utc = timeutil.to_utc(starts_local)
            s = services.create_session(
                claims.user_id, course_code, course_name, section, starts_utc,
                starts_utc + timedelta(minutes=int(duration)), loc["lat"], loc["lon"], float(radius), allowed,
            )
        except services.ServiceError as exc:
            st.error(str(exc))
            return
        st.session_state["last_session_id"] = s.id
        st.success("Session created!")
    if loc is None:
        st.caption("Set the classroom location first to enable session creation.")

    if sid := st.session_state.get("last_session_id"):
        s = services.get_session_by_id(sid)
        if s:
            link = services.session_link(s)
            st.markdown("#### Share this link with students")
            st.code(link, language=None)
            if png := common.qr_png(link):
                st.image(png, width=220, caption="Scan to open the session")
            st.caption(f"Window: {timeutil.fmt(s.starts_at)} → {timeutil.fmt(s.ends_at)} · "
                       f"radius {s.radius_m:.0f} m · allowed: `{s.allowed_rolls}`")


# --------------------------------------------------------------------------- #
def _sessions(claims) -> None:
    sessions = services.list_sessions(claims.user_id)
    if not sessions:
        st.info("No sessions yet. Create one in the first tab.")
        return
    labels = {f"{common.status_badge(s.status())}  {s.course_code} · {s.section} · {timeutil.fmt(s.starts_at)}": s
              for s in sessions}
    choice = st.selectbox("Session", list(labels))
    s = labels[choice]
    records = services.records_for(s.id)
    attempts = services.attempts_for(s.id)
    expected = services.expected_rolls(s.allowed_rolls)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Status", s.status().upper())
    m2.metric("Present", len(records))
    m3.metric("Expected", len(expected) if expected else "—")
    m4.metric("Blocked attempts", sum(1 for a in attempts if not a.passed))

    st.code(services.session_link(s), language=None)
    st.caption(f"{s.course_name} · {timeutil.fmt(s.starts_at)} → {timeutil.fmt(s.ends_at)} · "
               f"centre {s.latitude:.5f}, {s.longitude:.5f} · radius {s.radius_m:.0f} m · allowed `{s.allowed_rolls}`")

    b1, b2, b3 = st.columns(3)
    with b1:
        st.download_button(
            "⬇️ Export to Excel", data=export.to_excel_bytes(s, records, attempts, expected),
            file_name=f"attendance_{s.course_code}_{timeutil.to_local(s.starts_at):%Y%m%d_%H%M}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with b2:
        if s.status() in ("live", "upcoming") and st.button("⛔ Close session now", use_container_width=True):
            services.close_session(s.id)
            st.rerun()
    with b3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    df = export.records_dataframe(s, records, expected)
    st.markdown("#### Attendance records")
    if df.empty:
        st.info("No attendance marked yet.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        if records:
            pts = pd.DataFrame({"lat": [r.latitude for r in records], "lon": [r.longitude for r in records]})
            centre = pd.DataFrame({"lat": [s.latitude], "lon": [s.longitude]})
            st.map(pd.concat([centre.assign(color="#ff0000", size=s.radius_m),
                              pts.assign(color="#0066ff", size=3)]), zoom=16, color="color", size="size")

    with st.expander(f"Verification log ({len(attempts)} attempts)"):
        if attempts:
            st.dataframe(pd.DataFrame([{
                "Time": timeutil.fmt(a.created_at, True), "Roll": a.roll_number, "Stage": a.stage,
                "Result": "✅ PASS" if a.passed else "🚫 BLOCKED", "Reason": a.reason, "Device": a.device_hash[:10],
            } for a in reversed(attempts)]), use_container_width=True, hide_index=True)
        else:
            st.caption("No attempts yet.")


# --------------------------------------------------------------------------- #
def _students() -> None:
    students = services.list_students()
    if not students:
        st.info("No students registered yet.")
        return
    st.dataframe(pd.DataFrame([{
        "Roll": u.roll_number, "Name": u.full_name, "Username": u.username,
        "Face enrolled": "✅" if u.face_embedding else "❌", "Registered": timeutil.fmt(u.created_at),
    } for u in students]), use_container_width=True, hide_index=True)

    st.markdown("#### Manage a student")
    pick = st.selectbox("Student", [f"{u.roll_number} – {u.full_name}" for u in students])
    user = students[[f"{u.roll_number} – {u.full_name}" for u in students].index(pick)]
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Reset device bindings", help="Allow the student to check in from a new phone."):
            n = services.reset_devices(user.id)
            st.success(f"Removed {n} device binding(s) for {user.roll_number}.")
    with c2:
        st.caption("Re-enrol reference face (student must be present):")
        shot = st.camera_input("Reference face", key=f"reenrol_{user.id}")
        if shot is not None and st.button("Save reference face"):
            try:
                img = common.camera_to_bgr(shot)
                if err := liveness.check_neutral(liveness.analyze(img)):
                    st.error(err)
                else:
                    services.enroll_face(user.id, img)
                    st.success("Reference face updated.")
            except Exception as exc:
                st.error(f"Enrolment failed: {exc}")
