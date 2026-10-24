# AI-Based Smart Traffic Management (pure Python)
Base paper: *Emergency-Aware Adaptive Traffic Signal Control Using YOLO-Based Light-Bar Detection and SUMO
System-Level Validation* (IEEE Access 2026, doi:10.1109/access.2026.3710015).

    pip install -r requirements.txt
    streamlit run app.py

Pages: Live Control Center · Controller Benchmark · Vision (YOLOv8) · Traffic Prediction · Violation Detection · About.
Code: `smart_traffic/sim.py` (simulator + 4 controllers), `predictor.py` (ML forecast), `vision.py` (YOLOv8 + light-bar).

## New web app (React + FastAPI)

    run.bat            # API on :8310, web UI on :5310 (demo login is shown on the sign-in page)

The Streamlit app above is unchanged. The web app wraps the same `smart_traffic` engine: `backend/` (FastAPI),
`frontend/` (React, Kinetic Mono design). See `docs/03_HOW_TO_RUN.md` and `docs/FRONTEND_PLAN.md`.
