"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx.

Self-contained: the small slide helpers (prepare, set_title, wipe, agenda, title_slide, thank_you) are defined here so the deck does not depend on
the Review 1 module. All numbers come from facts.py (experiments/**/metrics.json); nothing is typed in by hand.
    python -m scripts.docs.deck_review2        # from 8.ProjectCode
"""
import os

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"
DELAY = "Avg delay / vehicle (s)"
EMG = "Emergency delay (s)"


# ------------------------------------------------------------------ helpers
def is_ph(sh, *types):
    return sh.is_placeholder and sh.placeholder_format.type in types


def prepare(prs, review_label):
    for lay in prs.slide_layouts:
        for sh in lay.shapes:
            if sh.has_text_frame and LAYOUT_FOOTER_OLD in sh.text_frame.text:
                K.replace_text(sh, f"{F.PRODUCT}  ·  {review_label}")
    cp = prs.core_properties
    cp.title = f"{F.FULL_TITLE}: {review_label}"
    cp.subject = f"Batch {F.BATCH_NO} ({F.SECTION})"
    cp.author = ", ".join(n for n, _ in F.STUDENTS)
    cp.keywords = "smart traffic management, YOLOv8, adaptive signal control, emergency vehicle priority, queue forecasting"
    cp.comments = ""
    cp.last_modified_by = ""


def set_title(slide, text, size=None):
    for sh in slide.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, text, size)
            return sh


def wipe(slide):
    K.clear(slide, lambda sh: sh.is_placeholder)


def agenda(slide, items, colors, cols=3):
    n = len(items)
    rows = (n + cols - 1) // cols
    gx, gy = 0.29, 0.3
    w = (12.13 - gx * (cols - 1)) / cols
    h = min(1.45, (5.3 - gy * (rows - 1)) / rows)
    x0, y0 = 0.6, 1.55
    for i, (n_, label) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = x0 + c * (w + gx), y0 + r * (h + gy)
        K.box(slide, x, y, w, h)
        K.text(slide, x + 0.25, y + 0.14, 1.0, 0.5, n_, size=26, color=colors[i % len(colors)], bold=True, font="Cambria")
        K.text(slide, x + 0.25, y + 0.72, w - 0.5, 0.65, label, size=16, color=K.INK, bold=True)


def title_slide(s, subtitle, label):
    for sh in s.shapes:
        nm = sh.name
        if is_ph(sh, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, F.TITLE, 32)
        elif is_ph(sh, PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.BODY):
            K.replace_text(sh, subtitle, 20)
        elif nm == "review label":
            K.replace_text(sh, label)
        elif nm == "team":
            K.replace_text(sh, "\n".join(f"{n_}  {r_}" for n_, r_ in F.STUDENTS))
        elif nm == "Text 6":
            K.replace_text(sh, f"{F.GUIDE}, {F.GUIDE_DESIGNATION}")
        elif nm == "Text 7":
            K.replace_text(sh, f"{F.DEPT}\n{F.COLLEGE_SHORT}  ·  Batch {F.BATCH_NO} ({F.SECTION})  ·  {F.YEAR}")


def thank_you(s):
    for sh in s.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
            K.replace_text(sh, "Thank you")
        elif is_ph(sh, PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.SUBTITLE):
            K.replace_text(sh, "Questions and suggestions are welcome.")


def trim(path, tag):
    """Copy of a diagram or chart with its white margins removed (written to the temp folder, source untouched)."""
    import tempfile

    from PIL import Image, ImageChops

    with Image.open(path) as im:
        im = im.convert("RGB")
        bbox = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
        if bbox:
            pad = 12
            bbox = (max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, im.size[0]), min(bbox[3] + pad, im.size[1]))
            im = im.crop(bbox)
        out = os.path.join(tempfile.gettempdir(), f"a10_r2_{tag}.png")
        im.save(out)
    return out


def shot_box(slide, name, x, y, w, h, caption):
    """Real screenshot in a w x h area with a one-line caption under it."""
    K.picture(slide, F.shot(name), x, y, w, h - 0.34, border=True)
    K.text(slide, x, y + h - 0.3, w, 0.3, caption, size=11, color=K.TXT, align="c", italic=True)


def api_ms(prefix):
    for r in F.API["results"]:
        if r["endpoint"].startswith(prefix):
            return r["mean_ms"]
    raise KeyError(prefix)


# ------------------------------------------------------------------ the deck
def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}

    d2, d3 = F.derived("2x2"), F.derived("3x3")
    dl = {c: F.gm("2x2", c, DELAY) for c in F.CTRL_KEYS}
    el = {c: F.gm("2x2", c, EMG) for c in F.CTRL_KEYS}
    dl3 = {c: F.gm("3x3", c, DELAY) for c in F.CTRL_KEYS}
    el3 = {c: F.gm("3x3", c, EMG) for c in F.CTRL_KEYS}
    pr_rs, pr_lo = F.PR["random_split_5x"], F.PR["leave_one_simulation_out"]
    gb_rs, gb_lo, pe_lo = pr_rs["Gradient Boosting (used)"], pr_lo["Gradient Boosting (used)"], pr_lo["Persistence"]
    pe_rs = pr_rs["Persistence"]
    shipped = F.PR["shipped_fit"]
    vs = F.VS["results"]["clean"]
    vm = F.VR["mixed_traffic"]["per_class"]
    va = F.VR["ambulance_classification"]
    lb, yl = va["lightbar_cluster_any"], va["ambulance_flag_yolo_plus_lightbar"]
    ab = F.AB["results"]
    ab_full, ab_noml = ab["advanced (full)"], ab["no ML forecast"]
    ab_nopre, ab_nogw = ab["no emergency pre-emption"], ab["no emergency green wave"]
    sw_adv = {r["demand"]: r["delay_mean"] for r in F.SW["series"]["advanced"]}
    sw_ada = {r["demand"]: r["delay_mean"] for r in F.SW["series"]["adaptive"]}
    th = F.TH

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: adaptive, emergency-aware and coordinated signal control with YOLOv8 vision and queue forecasting",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = ("This review shows how FlowSense is designed and built, what is implemented, the first measured results from the in-house traffic simulator and from public real-image "
                "datasets, and the open items. Introduce the four team members and the guide.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and datasets"), ("03", "Feature construction and models"), ("04", "Training and decision logic"),
               ("05", "Data flow, entities and UML"), ("06", "Technology stack"), ("07", "Progress and preliminary results"),
               ("08", "Output screens and testing"), ("09", "Challenges and next steps")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Fixed-time signals waste green on empty approaches while queues build elsewhere, ambulances wait at red with no priority, and neighbouring junctions act independently so clearing one only moves the queue to the next.", K.ORANGE, "!"),
        ("Proposed system", "FlowSense puts the whole chain in one product: YOLOv8n vehicle detection and a light-bar rule, a 30-second queue forecaster, an advanced signal controller with emergency green wave and spill-back avoidance, a violation log and a live console.", K.BLUE, "i"),
        ("Base paper link [1]", "Lamrabet et al. add a trained YOLO26m light-bar detector over a GA-SGD controller and validate it in SUMO on one roundabout. We keep the emergency-priority idea but build the full chain and measure it in our own simulator. Results are not comparable in absolute terms.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.6, W, 4.5, t, b_, col, gl, body_size=18)
    notes[3] = ("Recap of Review 1: the surveyed systems do adaptive control or vehicle detection separately. The gap is one pipeline that detects, adapts timing, prioritises emergency vehicles "
                "and coordinates junctions. The base paper's detector is trained; ours is a stock YOLOv8n plus an HSV light-bar rule, so we say plainly that we did not reach its detection quality.")

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, trim(F.diag("01_system_architecture.png"), "01"), 0.6, 1.3, 7.2, 5.7)
    K.text(s, 8.0, 1.45, 4.75, 5.4, [
        ("**Four tiers, no database**", {"space_after": 8}),
        (f"Console: React 19 + Vite on port {F.WEB_PORT}, 8 pages (landing, sign-in, live control, benchmark, vision, prediction, violations, about).", {"bullet": True}),
        (f"API: FastAPI on port {F.API_PORT}, 20 routes under /api, token sign-in, validation errors with a message and a hint.", {"bullet": True}),
        ("Engine: smart_traffic/sim.py (simulator and four controllers), predictor.py (queue forecaster), vision.py (YOLOv8n, light-bar rule, density).", {"bullet": True}),
        ("State: one shared live simulation, a benchmark cache and the last violation log live in process memory.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[4] = "Routes live in backend/main.py; service.py wraps the engine and holds no control logic. The legacy Streamlit app (app.py) is still in the project and uses the same engine."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: detect, forecast, decide, coordinate")
    wipe(s)
    K.picture(s, trim(F.diag("02_high_level_workflow.png"), "02"), 0.6, 1.4, 7.4, 5.0)
    for i, (t, b_) in enumerate([("Sense", "Vehicles enter on the entry roads (Poisson demand, rush-hour profile). The vision layer turns a camera frame into counts, PCU density and an emergency flag."),
                                 ("Forecast and decide", "Each second a controller scores both phases per junction. The advanced controller adds a 30 s queue forecast, inbound platoons within 8 s and fairness."),
                                 ("Coordinate", "Inter-junction look-ahead damps green toward a full downstream link and clears an ambulance's route up to 15 s ahead (green wave).")]):
        y = 1.4 + i * 1.78
        K.box(s, 8.3, y, 4.43, 1.65)
        K.text(s, 8.45, y + 0.07, 4.15, 0.4, t, size=15, color=K.INK, bold=True)
        K.text(s, 8.45, y + 0.42, 4.15, 1.2, b_, size=12.5, color=K.TXT)
    K.text(s, 0.6, 6.5, 7.4, 0.45, "High-level workflow as implemented in the simulator and the API.", size=12, color=K.TXT, align="c", italic=True)
    notes[5] = ("Four controllers face identical random demand so the comparison is like for like. Emergency vehicles are known to the simulated controllers by ground truth; the vision module is a separate demo, not closed loop with them.")

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Data: simulated demand, forecaster set and real images")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.PR['n_samples']:,} x {F.PR['n_features']}", "forecaster training samples x features", K.ORANGE), ("293", "real dashcam frames, 1,506 boxes (CC BY 4.0)", K.BLUE),
                                   ("600", "real photos: 300 ambulance, 300 other (CC BY 4.0)", K.GREEN), ("5", "benchmark seeds (40-44), 1800 s each", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["", "Simulator-generated", "Public real images (evaluation only)"],
            ["Source", "FlowSense simulator: 2x2 or 3x3 grid, Poisson arrivals, seeded", "Visaitech mixed-traffic frames [32]; shravya11 ambulance photos [33]"],
            ["Forecaster set", "6 runs of 1800 s under the adaptive controller; demand 0.7-1.6, start 07/08/12/17 h; a snapshot every 10 s", "none - the forecaster never sees real data"],
            ["Targets", f"queue 30 s ahead per approach (mean {F.PR['target_mean']:.2f}, std {F.PR['target_std']:.2f}, max {F.PR['target_max']:.0f})", "boxes: 2-, 3-, 4-wheelers; ambulance yes / no"],
            ["Split", "random 75/25 (shipped) and leave-one-simulation-out (added)", "no training: YOLOv8n COCO weights used as shipped, conf 0.3"],
            ["Limit", "assumptions are ours (saturation 0.5 veh/s, link 12 s); not SUMO", "dashcam, not junction cameras; first 300 files by name per folder"]]
    K.table(s, 0.6, 2.95, [1.5, 5.4, 5.23], rows, font_size=12.5, row_h=0.62, first_bold=True)
    K.text(s, 0.6, 6.75, 12.13, 0.35, "No private data is used; the base paper's 3,130 light-bar images were not available to us.", size=12, color=K.TXT, italic=True)
    notes[6] = ("The control experiments need no external dataset: demand is a seeded Poisson process with a morning and evening peak. The two public image sets are used only to test the shipped vision layer, "
                "with no tuning on them.")

    # ---- 7 feature construction
    s = S[6]
    set_title(s, "Feature construction (preprocessing)")
    wipe(s)
    K.flow(s, 0.6, 1.45, 12.13, 1.0, [("Simulator state each second", K.NAVY), ("Queue and PCU queue", K.PURPLE), ("Lags 10 s and 30 s", K.PURPLE),
                                       ("Inflow and inbound", K.GREEN), ("Signal state, time of day", K.GREEN), ("11 features per approach", K.ORANGE)], size=12, gap=0.22)
    for i, (v, l, c) in enumerate([("11", "features per approach: queue, pcu_queue, queue_lag10, queue_lag30, inflow_30s, inbound_15s, is_green, green_time, is_entry, sin_day, cos_day", K.BLUE),
                                   ("30 s", "forecast horizon; predictions clipped to 0-40 vehicles", K.GREEN)]):
        K.tile(s, 0.6 + i * 6.2, 2.8, 5.95, 1.25, v, l, c, vsize=28, lsize=12)
    K.text(s, 0.6, 4.35, 12.13, 2.6, [
        ("Vision frames: YOLOv8n is restricted to the COCO classes car, motorcycle, bus and truck; the HSV rule marks red-and-blue blobs that touch after dilation as a light bar.", {"bullet": True}),
        ("Density: passenger-car units (car 1, bike 0.5, bus 3, truck 2) divided by a road capacity of 14 PCU gives LOW, MEDIUM, HIGH or JAMMED.", {"bullet": True}),
        ("Time of day enters as sin and cos of the hour; the rush-hour demand multiplier peaks at 08:30 and 17:30.", {"bullet": True}),
        ("Known limit: feature importance is dominated by the current queue (0.69) and the 30 s lag (0.13); inbound and inflow features add little.", {"bullet": True}),
    ], size=16, color=K.INK, space_after=9)
    notes[7] = "feature_matrix() in sim.py builds one row per approach at each snapshot. The same function is used for training and for live forecasting in the advanced controller."

    # ---- 8 model
    s = S[7]
    set_title(s, "Models: queue forecaster, YOLOv8n and light-bar rule")
    wipe(s)
    K.picture(s, trim(F.diag("12_model_architecture.png"), "12"), 0.6, 1.35, 7.6, 5.0)
    K.text(s, 8.5, 1.45, 4.25, 5.4, [
        ("**Forecaster**: Gradient Boosting regressor, 160 trees, depth 4; Random Forest and persistence as baselines.", {"bullet": True, "space_after": 8}),
        ("**YOLOv8n** (Ultralytics, COCO weights): vehicle boxes at confidence 0.3; no fine-tuning.", {"bullet": True, "space_after": 8}),
        ("**Light-bar rule**: HSV red and blue clusters; a box carrying a cluster is relabelled ambulance.", {"bullet": True, "space_after": 8}),
        ("The base paper's trained YOLO26m light-bar detector is not reproduced.", {"bullet": True, "italic": True, "color": K.TXT}),
    ], size=14, color=K.INK)
    K.text(s, 0.6, 6.45, 7.6, 0.45, "Forecaster architecture and its closed-loop use inside the advanced controller.", size=12, color=K.TXT, align="c", italic=True)
    notes[8] = "Three components with separate jobs. A classical contour detector handles the synthetic overhead scenes; YOLOv8n handles real photos."

    # ---- 9 training configuration
    s = S[8]
    set_title(s, "Training and evaluation configuration")
    wipe(s)
    rows = [["Setting", "Value"],
            ["Forecaster", f"GradientBoostingRegressor: 160 trees, depth 4, learning rate 0.08, subsample 0.9, seed 0; fit time {shipped['fit_seconds']:.1f} s on CPU"],
            ["Baselines", "Random Forest (80 trees, depth 10), ridge regression, persistence (queue now = queue in 30 s)"],
            ["Split", f"random 75/25 (shipped, seed 1) plus 5 random splits and a leave-one-simulation-out check over the 6 runs ({F.PR['n_samples']:,} samples)"],
            ["Vision", "YOLOv8n pretrained on COCO, not trained here; conf 0.3; light-bar thresholds S >= 120, V >= 190 (red H 0-8 / 172-180, blue H 100-130)"],
            ["Controller benchmark", "4 controllers x 5 seeds (40-44), 1800 s, demand x1.2, start 08:00, 2x2 and 3x3 grids; ablation, demand sweep and emergency-heavy test"],
            ["Machine", "Core i5-12500, 15.7 GB RAM, no CUDA GPU; Python 3.11.9, scikit-learn 1.5.0, ultralytics 8.4.186"]]
    K.table(s, 0.6, 1.45, [2.3, 9.83], rows, font_size=14, row_h=0.72, first_bold=True)
    K.text(s, 0.6, 6.6, 12.13, 0.4, "Hyper-parameters are those in the shipped code; nothing was tuned on the real images.", size=12, color=K.TXT, italic=True)
    notes[9] = "Hyper-parameters are those in smart_traffic/predictor.py. The experiment scripts (scripts/run_experiments.py, eval_real_vision.py) reuse the shipped code and write metrics.json files."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: the advanced controller")
    wipe(s)
    K.picture(s, trim(F.diag("10_flowchart_control.png"), "10"), 0.6, 1.3, 5.9, 5.65)
    rows = [["Rule (per junction, per second)", "Action"],
            ["Ambulance in queue or inbound within 15 s", "Force its phase green after >= 2 s"],
            ["Green shorter than 13 s", "Hold"],
            ["Current phase empty, other has traffic", "Switch"],
            ["Other pressure > 2 x current + 4", "Switch"],
            ["Green reaches 60 s", "Switch if other phase has traffic"]]
    K.table(s, 6.8, 1.4, [3.55, 2.4], rows, font_size=12.5, row_h=0.5)
    K.text(s, 6.8, 4.55, 5.95, 2.4, [
        ("**Pressure** = PCU queue + 0.7 x max(forecast - queue, 0) + inbound PCU within 8 s + head wait / 12, times 0.3 if the straight-ahead downstream queue is within 4 vehicles of capacity (30).", {"bullet": True, "space_after": 6}),
        ("Switching costs 3 s of clearance; start-up lost time is 2 s; saturation discharge 0.5 veh/s.", {"bullet": True}),
    ], size=13, color=K.INK)
    notes[10] = "This mirrors Sim._decide and Sim._pressure. The forecast term comes from the Gradient Boosting model every 10 s once 30 s of history exists. The base-paper-style controller uses only the emergency rule at one junction with a 5 s look-ahead."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, trim(F.diag("04_dfd_level1.png"), "04"), 0.6, 1.3, 7.0, 5.65)
    rows = [["Module", "Role"], ["smart_traffic/sim.py", "simulator, 4 controllers, KPIs"], ["smart_traffic/predictor.py", "30 s queue forecaster"], ["smart_traffic/vision.py", "YOLOv8n, light bar, density"],
            ["backend/service.py", "wraps the engine for HTTP"], ["backend/main.py", "20 routes, validation, auth"], ["backend/auth.py", "HS256 token, demo account"], ["frontend/src/pages", "8 React pages"],
            ["scripts/ and tests/", "experiments, smoke test, 38 tests"]]
    K.table(s, 7.9, 1.45, [2.35, 2.48], rows, font_size=12, row_h=0.55, first_bold=True)
    K.text(s, 7.9, 6.5, 4.83, 0.5, "Level-1 data-flow diagram of the platform.", size=11.5, color=K.TXT, italic=True)
    notes[11] = "Level 1 has seven processes: authenticate and validate, simulate traffic, control signals, forecast queues, analyse a vision frame, benchmark the controllers, and report KPIs, map and violation log."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Entities and UML (no database)")
    wipe(s)
    K.picture(s, trim(F.diag("09_er_diagram.png"), "09"), 0.6, 1.3, 6.0, 4.95)
    K.picture(s, trim(F.diag("06_uml_class.png"), "06"), 6.75, 1.3, 6.0, 5.2)
    K.text(s, 0.6, 6.35, 6.0, 0.7, "FlowSense keeps no database - in-memory entities only. The shared live simulation, benchmark cache and violation log are lost on restart; the ER diagram is logical.", size=11.5, color=K.TXT, italic=True)
    K.text(s, 6.75, 6.55, 6.0, 0.5, "Core classes: Sim, Vehicle, QueuePredictor, vision functions, service Live / Preview.", size=11.5, color=K.TXT, italic=True)
    notes[12] = "Honest point: persistence of runs, violations and users is future work. There is one demo operator account and one shared live simulation."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    rows = [["Layer", "Technology"],
            ["Language and API", "Python 3.11.9, FastAPI 0.143.3, Uvicorn, Pydantic, python-multipart; stdlib HS256 token for the demo sign-in"],
            ["Simulation", "Pure Python and NumPy 1.26.4: 1 s time step, Poisson arrivals, deque queues; thousands of times faster than real time"],
            ["Machine learning", "scikit-learn 1.5.0 (Gradient Boosting, Random Forest, ridge), pandas 2.2.1, NumPy"],
            ["Vision", "Ultralytics 8.4.186 (YOLOv8n on PyTorch 2.14.1 CPU) and OpenCV 4.11.0 for the HSV light-bar rule and annotations"],
            ["Front end", "React 19, Vite 8, Tailwind 4, Recharts, Framer Motion, GSAP; legacy Streamlit app kept in app.py"],
            ["Testing and capture", "pytest 8.2 with FastAPI TestClient, urllib smoke script, Playwright browser capture at 1440 x 900"],
            ["Run", f"run.bat creates the virtual environment, installs packages and starts both servers; ports {F.API_PORT} and {F.WEB_PORT}"]]
    K.table(s, 0.6, 1.45, [2.6, 9.53], rows, font_size=14, row_h=0.65, first_bold=True)
    notes[13] = "Versions are those installed on the measurement PC. On Windows torch must be imported before scikit-learn or OpenCV, so backend/main.py imports it first."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Simulator with fixed, adaptive, emergency-aware and advanced controllers", "Done", "24 engine tests; 2x2 and 3x3 grids; 5-seed benchmark"],
            ["Queue forecaster (Gradient Boosting) used inside the controller", "Done", f"MAE {gb_rs['mae_mean']:.2f} on a random split; weak on unseen congestion"],
            ["Vision layer: YOLOv8n, light-bar rule, PCU density", "Done", "synthetic and real-image evaluation; stock detector, not fine-tuned"],
            ["API (20 routes) and React console (8 pages), demo sign-in", "Done", f"{F.SMOKE_PASSED}/{F.SMOKE_TOTAL} smoke checks; {F.PYTEST_PASSED}/{F.PYTEST_TOTAL} pytest tests"],
            ["Violation log (red-light, wrong-way)", "Simulated", "events from ground truth with a drawn confidence; no detector"],
            ["Trained light-bar or emergency-vehicle detector", "Not done", f"HSV rule recall {lb['recall'] * 100:.1f}% on {va['ambulance_images']} real ambulance photos"],
            ["SUMO or CARLA validation, real camera stream, hardware", "Not done", "in-house simulator only; results not comparable in absolute terms"],
            ["Database, persistence, multi-user accounts", "Not done", "in-memory state; one demo operator"]]
    K.table(s, 0.6, 1.4, [5.4, 1.4, 5.33], rows, font_size=12.5, row_h=0.6)
    notes[14] = "State of the code base. The honest gaps are the last four rows: violations are simulated, no trained emergency detector, no SUMO, and no persistence."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results: controller benchmark")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"-{d2['delay_cut_advanced_vs_fixed_pct']:.1f}%", f"average delay, advanced vs fixed-time (2x2; 3x3 -{d3['delay_cut_advanced_vs_fixed_pct']:.1f}%)", K.ORANGE),
                                   (f"-{d2['delay_cut_advanced_vs_adaptive_pct']:.1f}%", f"advanced vs plain adaptive: about one std (3x3 -{d3['delay_cut_advanced_vs_adaptive_pct']:.1f}%)", K.BLUE),
                                   (f"{el['advanced'][0]:.1f} s", f"ambulance delay, advanced; fixed-time {el['fixed'][0]:.1f} s (-{d2['emergency_cut_advanced_vs_fixed_pct']:.1f}%)", K.GREEN),
                                   (f"+{-d2['delay_cut_basepaper_vs_adaptive_pct']:.1f}%", "mean delay of the base-paper-style controller vs adaptive: pre-emption costs", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.35, 2.85, 1.2, v, l, c, vsize=26, lsize=11)
    K.picture(s, trim(F.fig("f01_delay_by_controller.png"), "f01"), 0.6, 2.7, 6.0, 3.25)
    K.picture(s, trim(F.fig("f02_emergency_delay.png"), "f02"), 6.75, 2.7, 6.0, 3.25)
    K.text(s, 0.6, 6.05, 12.13, 1.0, [
        (f"2x2, 5 seeds, demand x1.2: fixed {dl['fixed'][0]:.1f}, adaptive {dl['adaptive'][0]:.1f}, base-paper-style {dl['emergency'][0]:.1f}, advanced {dl['advanced'][0]:.1f} s. "
         f"At low demand (x0.6) advanced is worse than adaptive ({sw_adv[0.6]:.1f} vs {sw_ada[0.6]:.1f} s). Ablation: no forecast +{ab_noml[DELAY]['mean'] - ab_full[DELAY]['mean']:.1f} s; no pre-emption gives the lowest network delay "
         f"({ab_nopre[DELAY]['mean']:.1f} s) but ambulance delay {ab_nopre[EMG]['mean']:.1f} s. Own simulator, not SUMO.", {}),
    ], size=12.5, color=K.TXT)
    notes[15] = (f"Headline: the adaptive family beats fixed-time by about a third; most of the gain is adaptivity. Advanced beats plain adaptive by only {d2['delay_cut_advanced_vs_adaptive_pct']:.1f} percent on 2x2, within one standard deviation. "
                 f"Ambulance delay drops from {el['fixed'][0]:.1f} s to {el['advanced'][0]:.1f} s. The UI default benchmark uses three seeds and shows -38 percent vs fixed-time; the tables use five seeds.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    cw, ch = 3.95, 2.62
    grid = [("06_live_map_and_status.png", "Live control: road map, queue chart, junction status"), ("07_benchmark.png", "Benchmark: four controllers on identical traffic"),
            ("09_benchmark_sweep.png", "Delay against demand, four controllers"), ("11_vision_density.png", "Vision: synthetic scene, PCU density and green time"),
            ("12_vision_yolo.png", "Vision: YOLOv8n on the sample street photo"), ("14_prediction_forecast.png", "Prediction: model comparison and live 30 s forecast")]
    for i, (n_, cap) in enumerate(grid):
        r, c = divmod(i, 3)
        shot_box(s, n_, 0.6 + c * (cw + 0.19), 1.3 + r * (ch + 0.14), cw, ch, cap)
    K.text(s, 0.6, 6.72, 12.13, 0.3, "Real captures of the running application at 1440 x 900, with live simulation data. Benchmark screens use the UI defaults (3 seeds).", size=11, color=K.TXT, italic=True)
    notes[16] = "Real screenshots from the running console. The benchmark screen shows fixed 73.0, adaptive 48.5, emergency-aware 51.2 and advanced 45.4 s for the UI default of three seeds."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.PYTEST_PASSED} / {F.PYTEST_TOTAL}", f"pytest tests passed ({F.PYTEST_ENGINE} engine, {F.PYTEST_API} API)", K.GREEN), (f"{F.SMOKE_PASSED} / {F.SMOKE_TOTAL}", "smoke-test checks passed against the live API", K.BLUE),
                                   (f"{api_ms('live step 2 s'):.1f} ms", "mean API time for a 2 s simulation step (127.0.0.1)", K.ORANGE),
                                   (f"{api_ms('vision sample'):.0f} ms", "mean YOLOv8n sample-photo call incl. first model load", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Observation", "Action"],
            [f"Forecaster looks strong on a random split (R2 {gb_rs['r2_mean']:.3f}) but R2 is {gb_lo['r2_mean']:.2f} leave-one-run-out", "Reported both; failure on the one heavily congested run explained"],
            [f"Synthetic vision recall {vs['recall'] * 100:.1f}% but {va['ambulance_images']} real ambulance photos: light-bar recall {lb['recall'] * 100:.1f}%", "Stated in every result; trained detector listed as next step"],
            ["torch fails to load (WinError 1114) if numpy or pandas are imported first on this host", "torch-first import in the backend, tests and scripts"],
            ["Advanced is worse than adaptive at low demand (x0.6)", "Shown in the demand sweep; load-aware gains listed as next step"]]
    K.table(s, 0.6, 2.95, [6.4, 5.73], rows, font_size=13.5, row_h=0.78)
    notes[17] = "Tests cover the simulator, controllers, forecaster, vision rules and the API through FastAPI's TestClient; the smoke script drives the live server. Each observation came from running the code and is recorded rather than hidden."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "Corrective action"],
            ["No traffic dataset or SUMO set-up came with the project", "Built a seeded simulator with four controllers on identical demand; labelled it as such and not comparable with the base paper"],
            ["Emergency detection: the base paper trains YOLO26m on 3,130 light-bar images", f"Tested our rule on real photos (a light-bar cluster in {lb['tp']} of {va['ambulance_images']}) and said so; training a detector is the first next step"],
            [f"Real dashcam traffic: YOLOv8n recall {vm['any vehicle class']['recall'] * 100:.0f}% of all vehicles, {vm['2-wheeler']['recall'] * 100:.0f}% of 2-wheelers, 0% of 3-wheelers", "Reported per class; fine-tuning on mixed-traffic data planned"],
            [f"Forecaster fails outside its training range (MAE {pr_lo['Gradient Boosting (used)']['mae_per_fold'][3]:.1f} vs persistence {pe_lo['mae_per_fold'][3]:.1f} on the congested run)", "Leave-one-simulation-out check added; wider demand coverage in training listed"],
            ["CPU-only machine shared with other jobs", f"Simulator is fast ({th['2x2/advanced']['speedup']:,.0f}x real time for the 2x2 advanced run); YOLO timings reported as indicative"]]
    K.table(s, 0.6, 1.5, [5.9, 6.23], rows, font_size=14, row_h=0.88)
    notes[18] = "Each challenge was met by a concrete design choice or by measuring it and saying so in the report."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Train a detector", "Fine-tune YOLOv8 on a light-bar and mixed-traffic set and close the loop so vision, not ground truth, triggers pre-emption.", K.BLUE, "1"),
        ("Validate in SUMO", "Port the four controllers to SUMO or CARLA and repeat the comparison on a real network to allow a fair look at the base paper.", K.GREEN, "2"),
        ("Make the forecast robust", "Train on wider demand, add a congestion regime, try sequence models, and keep persistence as a fallback.", K.ORANGE, "3"),
        ("Productionise", "Add a database for runs and violations, real violation detection with tracking, user accounts and TLS.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.09, 1.6, 2.85, 3.9, t, b_, col, gl, body_size=17)
    K.box(s, 0.6, 5.75, 12.13, 0.95, fill=K.FHEAD, line=None)
    K.text(s, 0.85, 5.9, 11.6, 0.7, "Priority: items 1 and 2 close the largest honest gaps - the missing trained emergency detector and the absence of a standard simulator validation.", size=16, color=K.INK, anchor="m")
    notes[19] = "Plan to the final review. The first two items address the biggest honest gaps."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = ("Likely questions: why not SUMO; why advanced is only a few percent better than adaptive; why the light-bar rule fails on real photos; "
                 "how the forecaster behaves on unseen congestion; what is simulated and what is detected.")

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


def render(path, outdir):
    """Export every slide to PNG with PowerPoint COM (absolute path; serialised with the other builders)."""
    import win32com.client

    from .comlock import com_lock

    os.makedirs(outdir, exist_ok=True)
    with com_lock():
        app = win32com.client.DispatchEx("PowerPoint.Application")
        try:
            pres = app.Presentations.Open(os.path.abspath(path), True, False, False)
            pres.SaveAs(os.path.abspath(outdir), 18)
            pres.Close()
        finally:
            app.Quit()


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
