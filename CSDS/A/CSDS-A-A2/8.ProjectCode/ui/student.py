"""Student check-in wizard for a session link (?session=TOKEN)."""
from __future__ import annotations

import streamlit as st

import config
from core import face_match, geofence, liveness, services, timeutil
from ui import common

STEPS = ["Sign in", "Eligibility", "Location", "Live challenge", "Face match", "Done"]
MAX_LIVENESS_RETRIES = 3


def _progress(current: int) -> None:
    cols = st.columns(len(STEPS))
    for i, (c, name) in enumerate(zip(cols, STEPS)):
        icon = "✅" if i < current else ("🔵" if i == current else "⚪")
        c.markdown(f"<div style='text-align:center;font-size:0.8rem'>{icon}<br>{name}</div>", unsafe_allow_html=True)
    st.progress(current / (len(STEPS) - 1))


def _state(session_id: int) -> dict:
    ck = st.session_state.get("checkin")
    if not ck or ck.get("session_id") != session_id:
        ck = {"session_id": session_id, "step": 1, "challenge": liveness.random_challenge(),
              "liveness_tries": 0}
        st.session_state["checkin"] = ck
    return ck


def render(token: str | None) -> None:
    if not token:
        st.subheader("Student check-in")
        st.info("Open the **session link** shared by your faculty, or paste it below.")
        raw = st.text_input("Session link or token")
        if raw:
            tok = raw.strip().split("session=")[-1].split("&")[0]
            st.query_params["session"] = tok
            st.rerun()
        return

    session = services.get_session_by_token(token)
    if session is None:
        st.error("Invalid session link.")
        return

    status = session.status()
    st.markdown(
        f"### {session.course_code} · {session.course_name}  \n"
        f"{common.status_badge(status)} &nbsp;·&nbsp; {session.section} &nbsp;·&nbsp; "
        f"{timeutil.fmt(session.starts_at)} → {timeutil.fmt(session.ends_at)} &nbsp;·&nbsp; "
        f"faculty: {session.faculty.full_name}"
    )
    if status != "live":
        st.warning({"upcoming": "This session has not started yet.",
                    "expired": "This session has expired.",
                    "closed": "This session has been closed by the faculty."}[status])

    claims = common.current_claims()
    if claims is None:
        _progress(0)
        t1, t2 = st.tabs(["Sign in", "New student? Register"])
        with t1:
            common.login_form("student", "student")
        with t2:
            common.register_form("student", "student")
        return
    if claims.role != "student":
        st.error("Faculty accounts cannot mark attendance. Sign out and use a student account.")
        if st.button("Sign out"):
            common.logout()
            st.rerun()
        return

    with st.sidebar:
        st.markdown(f"**🎓 {claims.full_name}**  \n{claims.roll_number}")
        st.caption(f"Device: `{common.device_hash()[:10]}…`")
        if st.button("Sign out", use_container_width=True):
            common.logout()
            st.rerun()

    user = services.get_user(claims.user_id)
    ck = _state(session.id)
    _progress(ck["step"])
    dev = common.device_hash()

    # ---- Step 1: eligibility ------------------------------------------------ #
    if ck["step"] == 1:
        elig = services.check_eligibility(session, user, dev, common.device_label())
        services.log_attempt(session.id, user.roll_number, "eligibility", elig.ok, elig.reason, dev)
        if not elig.ok:
            st.error(f"🚫 {elig.reason}")
            return
        st.success("✅ Session is live, your roll number is allowed and this device is registered to you.")
        ck["step"] = 2
        st.rerun()

    # ---- Step 2: location ----------------------------------------------------- #
    if ck["step"] == 2:
        st.markdown("#### Step 2 · Verify you are in the classroom")
        loc = common.location_picker("checkin", session.latitude, session.longitude)
        if loc and st.button("Verify my location", type="primary"):
            geo = geofence.check_geofence(loc["lat"], loc["lon"], session.latitude, session.longitude,
                                          session.radius_m, loc.get("accuracy"))
            services.log_attempt(session.id, user.roll_number, "location", geo.inside, geo.reason, dev)
            if geo.inside:
                ck.update(step=3, loc=loc, distance=geo.distance_m)
                st.rerun()
            else:
                st.error(f"🚫 {geo.reason}")
        return

    # ---- Step 3: liveness challenge ------------------------------------------- #
    if ck["step"] == 3:
        st.markdown("#### Step 3 · Live facial challenge")
        text, emoji = liveness.describe(ck["challenge"])
        st.info(f"Photo 1: **look straight** at the camera, mouth closed.  \n"
                f"Photo 2: {emoji} **{text}** — then take the photo while holding the pose.")
        c1, c2 = st.columns(2)
        with c1:
            neutral = st.camera_input("Photo 1 — neutral", key=f"neutral_{ck['liveness_tries']}")
            if neutral is not None:
                m = liveness.analyze(common.camera_to_bgr(neutral))
                if err := liveness.check_neutral(m):
                    st.warning(err)
                else:
                    st.success("Good neutral frame.")
        with c2:
            chal = st.camera_input(f"Photo 2 — {text}", key=f"chal_{ck['liveness_tries']}")

        if neutral is not None and chal is not None and st.button("Verify challenge", type="primary"):
            n_img, c_img = common.camera_to_bgr(neutral), common.camera_to_bgr(chal)
            res = liveness.verify_challenge(ck["challenge"], liveness.analyze(n_img), liveness.analyze(c_img))
            services.log_attempt(session.id, user.roll_number, "liveness", res.passed,
                                 f"{ck['challenge']}: {res.reason}", dev)
            if res.passed:
                ck.update(step=4, neutral_bytes=neutral.getvalue(), challenge_bytes=chal.getvalue(),
                          liveness_score=res.score, liveness_reason=res.reason)
                st.rerun()
            ck["liveness_tries"] += 1
            st.error(f"🚫 Challenge failed — {res.reason}")
            if ck["liveness_tries"] >= MAX_LIVENESS_RETRIES:
                st.error("Too many failed attempts. Reload the link to start over, or contact faculty.")
                ck["step"] = 99
            else:
                ck["challenge"] = liveness.random_challenge()  # new random challenge each retry
                st.warning(f"New challenge issued ({MAX_LIVENESS_RETRIES - ck['liveness_tries']} tries left). "
                           "Take both photos again.")
                st.rerun()
        return

    # ---- Step 4: face identity + duplicate check ------------------------------ #
    if ck["step"] == 4:
        st.markdown("#### Step 4 · Face verification")
        with st.spinner("Comparing your face with the enrolled reference and this session's records…"):
            try:
                n_img = liveness.decode_image(ck["neutral_bytes"])
                c_img = liveness.decode_image(ck["challenge_bytes"])
                emb_n, emb_c = face_match.embed(n_img), face_match.embed(c_img)
            except (face_match.FaceError, ValueError) as exc:
                services.log_attempt(session.id, user.roll_number, "face", False, str(exc), dev)
                st.error(f"🚫 {exc}")
                if st.button("Retake photos"):
                    ck["step"] = 3
                    st.rerun()
                return
            enrolled = face_match.from_bytes(user.face_embedding) if user.face_embedding else None
            match = face_match.verify_faces(emb_n, enrolled, services.session_embeddings(session.id, user.id), emb_c)
        services.log_attempt(session.id, user.roll_number, "face", match.passed, match.reason, dev)
        if not match.passed:
            st.error(f"🚫 {match.reason}")
            return
        # Re-check eligibility right before writing (session may have expired meanwhile).
        elig = services.check_eligibility(session, user, dev)
        if not elig.ok:
            st.error(f"🚫 {elig.reason}")
            return
        rec = services.record_attendance(
            session, user, lat=ck["loc"]["lat"], lon=ck["loc"]["lon"], accuracy=ck["loc"].get("accuracy"),
            distance=ck["distance"], device_hash=dev, challenge=ck["challenge"],
            liveness_score=ck["liveness_score"], identity_sim=match.identity_similarity,
            dup_sim=match.max_duplicate_similarity, embedding=emb_n,
        )
        ck.update(step=5, record_id=rec.id, match=match)
        st.rerun()

    # ---- Step 5: done ---------------------------------------------------------- #
    if ck["step"] == 5:
        st.balloons()
        st.success(f"🎉 Attendance marked for **{user.roll_number} – {user.full_name}**")
        m = ck["match"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Distance", f"{ck['distance']:.0f} m")
        c2.metric("Liveness", f"{ck['liveness_score']:.2f}", liveness.describe(ck["challenge"])[1])
        c3.metric("Identity match", f"{m.identity_similarity:.2f}" if m.identity_similarity is not None else "n/a")
        c4.metric("Max duplicate sim.", f"{m.max_duplicate_similarity:.2f}" if m.max_duplicate_similarity is not None else "—")
        st.caption(f"Recorded at {timeutil.fmt(timeutil.utcnow(), True)} · device {dev[:10]}… · "
                   f"thresholds: identity ≥ {config.IDENTITY_THRESHOLD}, duplicate < {config.DUPLICATE_THRESHOLD}")
        return

    if ck["step"] == 99:
        st.error("Check-in locked after repeated failed liveness challenges.")
        if st.button("Start over"):
            st.session_state.pop("checkin", None)
            st.rerun()
