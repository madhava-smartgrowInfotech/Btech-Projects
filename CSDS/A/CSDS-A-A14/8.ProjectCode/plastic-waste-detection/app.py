"""
app.py
------
Streamlit Home page. This is the entry point:
    streamlit run app.py

Streamlit auto-discovers the pages/ folder and adds each file
there as a sidebar navigation item, so this file only needs to
render the Home/landing content.
"""

import streamlit as st

st.set_page_config(
    page_title="Plastic Waste Detection",
    page_icon="🌊",
    layout="wide",
)

st.title("Automated Plastic Waste Detection in Oceans Using Artificial Intelligence")
st.caption("AI-powered detection and localisation of plastic waste in ocean images")

st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Project Overview")
    st.write(
        "Plastic pollution in oceans is a growing environmental crisis that "
        "harms marine ecosystems and is difficult to monitor manually. This "
        "project builds a computer-vision system that automatically detects "
        "and localises plastic waste in ocean/water images using a YOLO "
        "object-detection model, then presents the results through this "
        "interactive Streamlit interface — a working prototype suitable for "
        "future extension to video, drone and robotic-collection systems."
    )

    st.subheader("Problem Statement")
    st.write(
        "Plastic waste in oceans harms marine ecosystems. Manual monitoring "
        "is slow, costly and limited in coverage. Classification-only "
        "approaches identify that plastic is present but do not localise "
        "individual objects. This project addresses that gap by detecting "
        "and drawing bounding boxes around each plastic item in an image, "
        "along with a confidence score for every detection."
    )

    st.subheader("Project Objectives")
    st.markdown(
        """
1. Collect and annotate a dataset of ocean images containing plastic waste.
2. Preprocess images to handle lighting, reflections and turbidity.
3. Train a deep-learning object detector for plastic waste.
4. Localise each plastic item with bounding boxes and confidence scores.
5. Provide a prototype interface to upload images and view detections.
6. Evaluate detection accuracy using precision, recall and mAP.
        """
    )

with col2:
    st.subheader("Technology Stack")
    st.markdown(
        """
**Backend:** Python, OpenCV, NumPy, Pandas, PyTorch
**Model:** Ultralytics YOLO (YOLOv8) — see *About* page for the
YOLOv7 base-paper comparison
**Frontend:** Streamlit
**Visualization:** Matplotlib, Plotly
**Storage:** Local filesystem + SQLite (detection history)
        """
    )

    st.subheader("How the System Works")
    st.markdown(
        """
1. Upload an ocean/water image
2. Image is preprocessed (denoise, contrast, colour correction)
3. YOLO model runs object detection
4. Bounding boxes + confidence scores are drawn
5. Results, statistics and a downloadable report are generated
        """
    )

st.divider()
st.info(
    "Use the sidebar to navigate: **Detection** (upload & run detection), "
    "**Dashboard** (aggregate stats), **Evaluation** (model metrics), "
    "**About** (architecture & base-paper comparison)."
)
