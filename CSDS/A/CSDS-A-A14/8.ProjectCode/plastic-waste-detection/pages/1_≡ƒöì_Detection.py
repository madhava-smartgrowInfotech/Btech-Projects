"""
pages/1_🔍_Detection.py
------------------------
Image upload + detection page: upload -> preprocess -> detect ->
show boxes/confidence -> download image & report.
"""

import sys
from pathlib import Path

# Allow "from src...." imports when Streamlit runs this file directly
sys.path.append(str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np
import streamlit as st
from PIL import Image

from src.database import add_record
from src.detection import detections_to_rows, run_detection
from src.model import load_model
from src.preprocessing import preprocess_image
from src.utils import REPORTS_DIR, RESULTS_DIR, ensure_dirs, is_valid_image_file, timestamp_now

st.set_page_config(page_title="Detection", page_icon="🔍", layout="wide")
ensure_dirs(RESULTS_DIR, REPORTS_DIR)

st.title("🔍 Image Detection")
st.write("Upload an ocean/water image to detect and localise plastic waste.")

# ---- Sidebar controls ----
st.sidebar.header("Settings")
conf_threshold = st.sidebar.slider(
    "Confidence Threshold", min_value=0.1, max_value=0.9, value=0.5, step=0.05,
    help="Only detections above this confidence score are shown."
)
apply_preprocessing = st.sidebar.checkbox("Apply preprocessing pipeline", value=True)

# ---- Load model (cached) ----
@st.cache_resource(show_spinner="Loading YOLO model...")
def get_cached_model():
    return load_model()

try:
    model, device, used_fallback, model_msg = get_cached_model()
except RuntimeError as e:
    st.error(f"Model failed to load: {e}")
    st.stop()

st.sidebar.markdown(f"**Device Used:** `{device.upper()}`")
if used_fallback:
    st.sidebar.warning(model_msg)
else:
    st.sidebar.success(model_msg)

# ---- Upload ----
uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded_file is None:
    st.info("👆 Upload a JPG, JPEG or PNG image to begin.")
    st.stop()

if not is_valid_image_file(uploaded_file.name):
    st.error("Invalid file format. Please upload a .jpg, .jpeg or .png image.")
    st.stop()

# ---- Read & validate image ----
try:
    pil_image = Image.open(uploaded_file).convert("RGB")
    image_bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
except Exception:
    st.error("Could not read this image — it may be corrupted. Please try another file.")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    st.subheader("Original Image")
    st.image(pil_image, use_container_width=True)

# ---- Preprocess + detect ----
with st.spinner("Running detection..."):
    processed_bgr = preprocess_image(image_bgr) if apply_preprocessing else image_bgr
    annotated_bgr, detections = run_detection(model, processed_bgr, conf_threshold=conf_threshold)
    annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)

with col2:
    st.subheader("Detected Image")
    st.image(annotated_rgb, use_container_width=True)

st.divider()

# ---- Results ----
count = len(detections)
st.metric("Detected Plastic Objects", count)

if count == 0:
    st.warning(
        "No objects detected above the current confidence threshold. "
        "Try lowering the threshold in the sidebar, or note that this may "
        "reflect a model not yet trained on a plastic-waste dataset "
        "(see the sidebar model status above)."
    )
else:
    st.subheader("Confidence Scores")
    for i, d in enumerate(detections, start=1):
        st.write(f"Plastic {i} → {d.confidence * 100:.1f}%")

    st.subheader("Detection Table")
    st.table(detections_to_rows(detections))

    avg_conf = sum(d.confidence for d in detections) / count

    # ---- Save annotated image + report for download ----
    out_name = f"detected_{Path(uploaded_file.name).stem}.jpg"
    out_path = RESULTS_DIR / out_name
    cv2.imwrite(str(out_path), annotated_bgr)

    is_ok, buf = cv2.imencode(".jpg", annotated_bgr)
    dl_col1, dl_col2 = st.columns(2)

    with dl_col1:
        st.download_button(
            "⬇️ Download Detection Image",
            data=buf.tobytes(),
            file_name=out_name,
            mime="image/jpeg",
        )

    import json
    report = {
        "image_name": uploaded_file.name,
        "detection_count": count,
        "average_confidence_percent": round(avg_conf * 100, 2),
        "detections": detections_to_rows(detections),
        "timestamp": timestamp_now(),
    }
    with dl_col2:
        st.download_button(
            "⬇️ Download Detection Report (JSON)",
            data=json.dumps(report, indent=2),
            file_name=f"report_{Path(uploaded_file.name).stem}.json",
            mime="application/json",
        )

    # ---- Log to history ----
    add_record(uploaded_file.name, count, avg_conf, timestamp_now())
    st.caption("This run has been logged to Detection History.")
