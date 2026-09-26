"""
pages/4_ℹ️_About.py
---------------------
Architecture explanation, base-paper comparison, and future
scope — useful reference material for the project report/viva.
"""

import streamlit as st

st.set_page_config(page_title="About", page_icon="ℹ️", layout="wide")

st.title("ℹ️ About This Project")

st.subheader("System Architecture")
st.code(
    """
User
  ↓
Streamlit Interface
  ↓
Image Upload
  ↓
Image Preprocessing (denoise, contrast, colour correction)
  ↓
YOLO Object Detection Model
  ↓
Bounding Box + Confidence Scores
  ↓
Post Processing (sorting, table, stats)
  ↓
Results Dashboard
  ↓
Database (SQLite history) / Downloadable Report
    """,
    language="text",
)

st.divider()

st.subheader("Base Paper Connection")
st.write(
    "The base paper uses YOLOv7 for floating-water-garbage detection, combined "
    "with an improved A* algorithm for robotic collection path planning. "
    "This project adopts the YOLO-based detection concept from the base paper "
    "but focuses specifically on the detection/localisation stage:"
)
st.markdown(
    """
- Plastic waste detection
- Image-based detection
- Object localisation with bounding boxes
- Confidence scores per detection
- A user-friendly prototype interface (this Streamlit app)
    """
)
st.warning(
    "This project does **not** implement the robotic path-planning / "
    "collection component from the base paper — that is listed under "
    "Future Scope, not claimed as implemented."
)

st.subheader("Why YOLOv8 (Ultralytics) instead of YOLOv7?")
st.write(
    "Both are members of the YOLO family of single-stage object detectors "
    "trained the same way conceptually: transfer learning from a "
    "COCO-pretrained backbone onto a custom dataset, then evaluated with "
    "Precision/Recall/mAP. This project uses the Ultralytics implementation "
    "(YOLOv8) because it provides a stable, actively maintained Python API "
    "for training, validation and inference — making it far easier for a "
    "B.Tech project to install, train and demonstrate reliably, while "
    "keeping the detection methodology and evaluation approach consistent "
    "with the base paper."
)

st.divider()

st.subheader("Future Scope")
st.markdown(
    """
- Real-time video detection
- Drone-based monitoring
- Underwater camera integration
- Robotic waste collection (the path-planning component from the base paper)
- Mobile application
- Cloud deployment
- Edge AI (on-device inference)
- GPS-based pollution mapping
- Plastic-type classification (bottle, bag, net, etc.)
- Real-time ocean monitoring networks
    """
)

st.divider()

st.subheader("Quick Reference for Viva")
with st.expander("Why is preprocessing done before detection?"):
    st.write(
        "Ocean images often have colour cast (water absorbs red light), "
        "low contrast/haze, and sensor noise. The preprocessing pipeline "
        "(colour correction, denoising, CLAHE contrast enhancement) reduces "
        "these issues so plastic objects are easier to distinguish from the "
        "water/background — without over-processing, which could remove "
        "the texture information the model needs."
    )
with st.expander("How is the model evaluated?"):
    st.write(
        "Using standard object-detection metrics computed by the Ultralytics "
        "validation routine: Precision, Recall, mAP@0.5, and mAP@0.5:0.95, "
        "plus a confusion matrix and PR curve. These are only shown after "
        "running evaluate.py on a real trained model — nothing is fabricated."
    )
with st.expander("What happens if no trained model is available?"):
    st.write(
        "The app falls back to a general COCO-pretrained model purely so the "
        "interface remains demoable end-to-end, and clearly labels this as a "
        "placeholder in the sidebar. Real plastic detection requires running "
        "train.py on an annotated dataset to produce models/best.pt."
    )
