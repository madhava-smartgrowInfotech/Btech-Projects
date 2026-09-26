"""Shared Streamlit helpers (auth state, device fingerprint, camera/GPS widgets)."""
from __future__ import annotations

import io
from typing import Any

import numpy as np
import streamlit as st

import config
from core import auth, device, liveness, services


# --------------------------------------------------------------------------- #
# Device fingerprint
# --------------------------------------------------------------------------- #
def request_headers() -> dict:
    try:
        return dict(st.context.headers)
    except Exception:  # bare mode / old streamlit
        return {}


def device_hash() -> str:
    if "device_hash" not in st.session_state:
        st.session_state["device_hash"] = device.fingerprint(request_headers())
    return st.session_state["device_hash"]


def device_label() -> str:
    return device.label(request_headers())


# --------------------------------------------------------------------------- #
# Auth state (JWT kept in session_state, verified on every rerun)
# --------------------------------------------------------------------------- #
def current_claims() -> auth.TokenClaims | None:
    token = st.session_state.get("token")
    if not token:
        return None
    try:
        return auth.verify_token(token, device_hash())
    except auth.TokenError as exc:
        st.session_state.pop("token", None)
        st.warning(str(exc))
        return None


def logout() -> None:
    for k in ("token", "checkin"):
        st.session_state.pop(k, None)


def login_form(role_hint: str, key: str) -> bool:
    """Render a login form. Returns True when a login just happened."""
    with st.form(key=f"login_{key}"):
        label = "Roll number or username" if role_hint == "student" else "Username / email"
        username = st.text_input(label)
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
    if submitted:
        try:
            user, token = services.authenticate(username, password, device_hash())
        except services.ServiceError as exc:
            st.error(str(exc))
            return False
        if role_hint and user.role != role_hint:
            st.error(f"This account is a {user.role} account. Please use the {user.role} portal.")
            return False
        st.session_state["token"] = token
        st.success(f"Welcome, {user.full_name}! (JWT issued, valid {config.JWT_EXPIRY_MINUTES} min)")
        st.rerun()
    return False


def register_form(role: str, key: str) -> None:
    with st.form(key=f"register_{key}"):
        full_name = st.text_input("Full name")
        if role == "student":
            roll = st.text_input("Roll number (hall-ticket no.)", placeholder="23K91A6706")
            username = st.text_input("Username (optional, defaults to roll number)")
        else:
            roll = None
            username = st.text_input("Username / email")
        password = st.text_input("Password (min 6 chars)", type="password")
        face_file = None
        if role == "student":
            st.caption("Enrol your reference face now. Look straight at the camera, good light, no mask/cap.")
            face_file = st.camera_input("Reference face photo", key=f"enrol_cam_{key}")
        submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
    if not submitted:
        return
    try:
        face_img = None
        if role == "student":
            if config.REQUIRE_ENROLLMENT and face_file is None:
                st.error("A reference face photo is required for student registration.")
                return
            if face_file is not None:
                face_img = liveness.decode_image(face_file.getvalue())
                m = liveness.analyze(face_img)
                if err := liveness.check_neutral(m):
                    st.error(err)
                    return
            username = (username or roll or "").strip()
        user = services.register_user(role, username, full_name, password, roll, face_img)
    except (services.ServiceError, ValueError) as exc:
        st.error(str(exc))
        return
    except Exception as exc:  # face errors
        st.error(f"Face enrolment failed: {exc}")
        return
    st.success(f"Account created for {user.full_name}. You can sign in now.")


# --------------------------------------------------------------------------- #
# Camera / GPS widgets
# --------------------------------------------------------------------------- #
def camera_to_bgr(uploaded) -> np.ndarray:
    return liveness.decode_image(uploaded.getvalue())


def browser_geolocation(key: str) -> dict[str, Any] | None:
    """
    Ask the browser for GPS via streamlit-js-eval. Returns
    {"lat", "lon", "accuracy"} or None while the browser is still responding.
    """
    try:
        from streamlit_js_eval import get_geolocation
    except ImportError:
        st.warning("streamlit-js-eval not installed; browser GPS unavailable.")
        return None
    loc = get_geolocation(component_key=key)
    if not loc or "coords" not in loc:
        return None
    c = loc["coords"]
    return {"lat": float(c["latitude"]), "lon": float(c["longitude"]),
            "accuracy": float(c.get("accuracy") or 0.0)}


def location_picker(key: str, default_lat: float = 17.385, default_lon: float = 78.4867) -> dict | None:
    """Combined GPS + manual location input. Returns dict or None if nothing chosen yet."""
    st.markdown("**Location**")
    tabs = ["📡 Browser GPS"] + (["✍️ Manual (testing)"] if config.ALLOW_MANUAL_LOCATION else [])
    tab_objs = st.tabs(tabs)
    result = None
    with tab_objs[0]:
        st.caption("Allow the location permission when your browser asks.")
        if st.button("Get my location", key=f"gps_btn_{key}"):
            st.session_state[f"gps_req_{key}"] = True
        if st.session_state.get(f"gps_req_{key}"):
            loc = browser_geolocation(f"gps_{key}")
            if loc is None:
                st.info("Waiting for the browser to return a GPS fix…")
            else:
                st.session_state[f"gps_val_{key}"] = loc
        loc = st.session_state.get(f"gps_val_{key}")
        if loc:
            acc = f" (±{loc['accuracy']:.0f} m)" if loc.get("accuracy") is not None else " (manual)"
            st.success(f"Location: {loc['lat']:.6f}, {loc['lon']:.6f}{acc}")
            result = loc
    if config.ALLOW_MANUAL_LOCATION:
        with tab_objs[1]:
            c1, c2 = st.columns(2)
            lat = c1.number_input("Latitude", value=default_lat, format="%.6f", key=f"mlat_{key}")
            lon = c2.number_input("Longitude", value=default_lon, format="%.6f", key=f"mlon_{key}")
            if st.button("Use these coordinates", key=f"manual_btn_{key}"):
                st.session_state[f"gps_val_{key}"] = {"lat": lat, "lon": lon, "accuracy": None}
                result = st.session_state[f"gps_val_{key}"]
                st.rerun()
    return result or st.session_state.get(f"gps_val_{key}")


def qr_png(text: str) -> bytes | None:
    try:
        import qrcode
    except ImportError:
        return None
    img = qrcode.make(text)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def status_badge(status: str) -> str:
    return {"live": "🟢 LIVE", "upcoming": "🟡 Upcoming", "expired": "⚪ Expired", "closed": "🔴 Closed"}[status]
