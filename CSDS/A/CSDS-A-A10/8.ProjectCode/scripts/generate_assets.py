from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Ellipse


ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS = ROOT / "docs" / "diagrams"
CHARTS = ROOT / "docs" / "charts"
DIAGRAMS.mkdir(parents=True, exist_ok=True)
CHARTS.mkdir(parents=True, exist_ok=True)

NAVY = "#0B1220"
PANEL = "#111C31"
BLUE = "#3B82F6"
CYAN = "#22D3EE"
TEAL = "#10B981"
AMBER = "#F59E0B"
RED = "#EF4444"
INK = "#E5EEF9"
MUTED = "#9FB0C7"
LINE = "#52677F"


def canvas(title: str, size=(12, 7)):
    fig, ax = plt.subplots(figsize=size, dpi=150)
    fig.patch.set_facecolor(NAVY)
    ax.set_facecolor(NAVY)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    ax.text(4, 96, title, color=INK, fontsize=18, weight="bold", va="top")
    return fig, ax


def box(ax, x, y, w, h, title, body="", color=BLUE, fs=10, radius=2):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.45,rounding_size={radius}",
        facecolor=PANEL, edgecolor=color, linewidth=1.8,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h - 2.6, title, ha="center", va="top", color=INK, fontsize=fs + 1, weight="bold")
    if body:
        ax.text(x + w / 2, y + h / 2 - 1.2, body, ha="center", va="center", color=MUTED, fontsize=fs, linespacing=1.35)
    return patch


def arrow(ax, x1, y1, x2, y2, label="", color=LINE, rad=0.0, style="-|>"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=13,
                        linewidth=1.5, color=color, connectionstyle=f"arc3,rad={rad}")
    ax.add_patch(a)
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 2.0, label, color=MUTED, fontsize=8, ha="center",
                bbox=dict(facecolor=NAVY, edgecolor="none", pad=1.2))


def save(fig, path: Path):
    fig.savefig(path, dpi=150, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)


def architecture():
    fig, ax = canvas("CareFlow System Architecture")
    box(ax, 4, 62, 18, 23, "Users", "Reception\nDoctor\nNurse\nLab technician\nAdministrator", CYAN)
    box(ax, 29, 62, 22, 23, "React Frontend", "Role dashboards\nAxios API client\nZustand session\nWaiting-room board", BLUE)
    box(ax, 59, 62, 22, 23, "FastAPI Application", "REST routers\nJWT + role checks\nPydantic validation\nWebSocket manager", TEAL)
    box(ax, 29, 20, 22, 22, "ML Prediction Layer", "Gradient Boosting triage\nRandom Forest wait-time\nJoblib artefacts", AMBER)
    box(ax, 59, 20, 22, 22, "SQLAlchemy + SQLite", "Users, departments, patients\nvisits, beds, lab tests\nmovement logs", CYAN)
    box(ax, 85, 62, 12, 23, "Live Clients", "WebSocket\n/ws/live", RED, fs=9)
    arrow(ax, 22, 73, 29, 73, "HTTPS / UI")
    arrow(ax, 51, 73, 59, 73, "JSON REST")
    arrow(ax, 70, 62, 70, 42, "ORM")
    arrow(ax, 59, 68, 51, 36, "predict")
    arrow(ax, 81, 75, 85, 75, "events")
    arrow(ax, 85, 58, 51, 58, "", rad=-0.12)
    ax.text(68, 51, "WebSocket live refresh", color=MUTED, fontsize=8, ha="center")
    ax.text(4, 8, "Implemented ports: frontend 5173; backend 8010. Public endpoints: health, department list, queue board.", color=MUTED, fontsize=9)
    save(fig, DIAGRAMS / "01_system_architecture.png")


def workflow():
    fig, ax = canvas("High-Level Patient Flow Workflow")
    xs = [3, 19, 35, 51, 67, 83]
    items = [
        ("1. Register", "Patient details,\ncomplaint, vitals", BLUE),
        ("2. Predict", "Triage priority +\nexpected wait", AMBER),
        ("3. Queue", "Priority then\ntoken order", CYAN),
        ("4. Consult", "Doctor assigns\nand evaluates", TEAL),
        ("5. Route", "Lab / ward / ICU /\npharmacy", BLUE),
        ("6. Close", "Discharge and\nrelease bed", TEAL),
    ]
    for x, (t, b, c) in zip(xs, items):
        box(ax, x, 52, 13, 24, t, b, c, fs=9)
    for i in range(5): arrow(ax, xs[i] + 13, 64, xs[i + 1], 64)
    box(ax, 20, 18, 24, 16, "Live Operational State", "Visit status + department + bed + lab test", CYAN, fs=9)
    box(ax, 57, 18, 24, 16, "Role Dashboards", "KPIs, queue board, department load, capacity", BLUE, fs=9)
    arrow(ax, 73, 52, 70, 34, "persist + broadcast")
    arrow(ax, 44, 26, 57, 26, "WebSocket / REST")
    save(fig, DIAGRAMS / "02_high_level_workflow.png")


def dfd0():
    fig, ax = canvas("Data Flow Diagram - Level 0 (Context)")
    box(ax, 38, 36, 25, 32, "CareFlow System", "Queue, triage, visits, labs, beds, analytics", TEAL, fs=11)
    box(ax, 4, 68, 21, 18, "Reception", "Patient registration\nand token request", BLUE)
    box(ax, 4, 16, 21, 18, "Clinical Staff", "Consultation, lab and\nbed state updates", CYAN)
    box(ax, 75, 68, 21, 18, "Administrator", "KPI and load requests", AMBER)
    box(ax, 75, 16, 21, 18, "Waiting Board", "Public live queue view", RED)
    arrow(ax, 25, 75, 38, 59, "registration")
    arrow(ax, 38, 52, 25, 27, "assigned work / state", rad=-0.05)
    arrow(ax, 63, 59, 75, 75, "KPIs")
    arrow(ax, 63, 45, 75, 27, "tokens + waits")
    arrow(ax, 38, 62, 25, 80, "token + prediction", rad=0.08)
    arrow(ax, 25, 22, 38, 43, "status updates", rad=0.08)
    save(fig, DIAGRAMS / "03_dfd_level_0.png")


def dfd1():
    fig, ax = canvas("Data Flow Diagram - Level 1")
    processes = [
        (5, 66, "1.0 Authenticate", "JWT login and roles", BLUE),
        (29, 66, "2.0 Manage Visits", "register, assign, status", TEAL),
        (53, 66, "3.0 Predict", "triage and wait", AMBER),
        (77, 66, "4.0 Manage Resources", "labs and beds", CYAN),
        (29, 25, "5.0 Track Movement", "department transitions", BLUE),
        (60, 25, "6.0 Report Live State", "KPIs, loads, queue board", RED),
    ]
    for x, y, t, b, c in processes: box(ax, x, y, 18, 17, t, b, c, fs=8)
    box(ax, 5, 25, 15, 17, "D1 Users", "credentials, role", LINE, fs=8)
    box(ax, 5, 5, 27, 12, "D2 Clinical Records", "patients, visits, movements, lab tests", LINE, fs=8)
    box(ax, 37, 5, 21, 12, "D3 Resources", "departments and beds", LINE, fs=8)
    box(ax, 65, 5, 29, 12, "D4 Model Artefacts", "encoders + trained estimators", LINE, fs=8)
    arrow(ax, 14, 66, 14, 42, "user lookup")
    arrow(ax, 47, 66, 47, 17, "visit data")
    arrow(ax, 53, 74, 47, 74, "features")
    arrow(ax, 68, 66, 82, 17, "", rad=-0.18)
    ax.text(84, 52, "load model", color=MUTED, fontsize=8, ha="center")
    arrow(ax, 86, 66, 70, 17, "", rad=0.04)
    ax.text(78, 49, "resource state", color=MUTED, fontsize=8, ha="center")
    arrow(ax, 38, 66, 38, 42, "movement")
    arrow(ax, 47, 33, 60, 33, "operational state")
    save(fig, DIAGRAMS / "04_dfd_level_1.png")


def dfd2():
    fig, ax = canvas("Data Flow Diagram - Level 2: Register and Prioritise a Visit")
    steps = [
        (3, 58, "2.1 Validate", "patient, department, vitals", BLUE),
        (22, 58, "2.2 Resolve Patient", "match phone or create MRN", CYAN),
        (41, 58, "2.3 Classify Triage", "vitals -> priority + confidence", AMBER),
        (60, 58, "2.4 Calculate Queue", "count patients ranked ahead", TEAL),
        (79, 58, "2.5 Predict Wait", "queue + service + hour", AMBER),
    ]
    for x, y, t, b, c in steps: box(ax, x, y, 16, 20, t, b, c, fs=8)
    for i in range(4): arrow(ax, steps[i][0] + 16, 68, steps[i + 1][0], 68)
    box(ax, 22, 20, 23, 17, "2.6 Persist Visit", "token, status, priority, wait, movement", TEAL, fs=8)
    box(ax, 58, 20, 23, 17, "2.7 Publish Event", "visit_created via WebSocket", RED, fs=8)
    arrow(ax, 87, 58, 42, 37, "prediction", rad=0.08)
    arrow(ax, 45, 28, 58, 28, "committed visit")
    ax.text(4, 9, "Fallback behaviour: missing individual vitals are replaced with DEFAULT_VITALS before classification.", color=MUTED, fontsize=9)
    save(fig, DIAGRAMS / "05_dfd_level_2.png")


def uml_class():
    fig, ax = canvas("UML Class Diagram - Persistent Domain Model", size=(14, 9))
    classes = [
        (3, 64, 22, 25, "User", "id: str\nemail: str\nrole: RoleEnum\ndepartment_id: FK\nis_active: bool", BLUE),
        (28, 64, 22, 25, "Department", "id: str\ncode: str\ntype: DepartmentType\navg_service_minutes: float", CYAN),
        (53, 64, 22, 25, "Patient", "id: str\nmrn: str\nname, age, gender\nphone, blood_group", TEAL),
        (78, 64, 19, 25, "Visit", "id: str\npatient_id: FK\nstatus, priority\ncurrent_department_id: FK\nbed_id: FK", AMBER),
        (7, 21, 22, 25, "Bed", "id: str\ndepartment_id: FK\nbed_number, type\nstatus\ncurrent_visit_id: FK", RED),
        (39, 21, 22, 25, "LabTest", "id: str\nvisit_id: FK\ntest_name\nstatus\nordered/scheduled/completed", CYAN),
        (71, 21, 24, 25, "MovementLog", "id: str\nvisit_id: FK\nfrom_department_id: FK\nto_department_id: FK\ntimestamp", BLUE),
    ]
    for x, y, w, h, t, b, c in classes: box(ax, x, y, w, h, t, b, c, fs=8)
    arrow(ax, 25, 76, 28, 76, "0..* staff")
    arrow(ax, 75, 76, 78, 76, "1..* visits")
    arrow(ax, 88, 64, 50, 46, "0..* lab tests", rad=-0.08)
    arrow(ax, 88, 64, 83, 46, "0..* movements")
    arrow(ax, 39, 70, 18, 46, "0..* beds", rad=0.08)
    arrow(ax, 78, 68, 29, 34, "0..1 assigned bed", rad=0.12)
    ax.text(3, 8, "Enumerations: Role, DepartmentType, VisitStatus, Priority, BedStatus, LabTestStatus.", color=MUTED, fontsize=9)
    save(fig, DIAGRAMS / "06_uml_class_diagram.png")


def sequence():
    fig, ax = canvas("Sequence Diagram - Register, Predict and Broadcast", size=(14, 8))
    parts = [(8, "Reception"), (27, "React UI"), (47, "FastAPI"), (67, "ML Layer"), (87, "SQLite / WS")]
    for x, name in parts:
        box(ax, x - 7, 80, 14, 10, name, "", BLUE if x < 50 else TEAL, fs=8)
        ax.plot([x, x], [15, 80], color=LINE, lw=1, ls="--")
    msgs = [
        (8, 27, 72, "enter patient + vitals"),
        (27, 47, 64, "POST /api/visits"),
        (47, 87, 56, "find/create patient; count queue"),
        (47, 67, 48, "predict_triage + predict_wait"),
        (67, 47, 40, "priority, confidence, minutes"),
        (47, 87, 32, "insert visit + movement; commit"),
        (47, 87, 24, "broadcast visit_created"),
        (47, 27, 18, "201 VisitOut"),
    ]
    for a, b, y, label in msgs:
        arrow(ax, a, y, b, y, label, color=CYAN if a < b else AMBER)
    save(fig, DIAGRAMS / "07_sequence_diagram.png")


def use_case():
    fig, ax = canvas("Use-Case Diagram")
    box(ax, 30, 12, 46, 76, "CareFlow Boundary", "", LINE, fs=10)
    actors = [(7, 76, "Reception"), (7, 53, "Doctor"), (7, 30, "Nurse"), (89, 76, "Lab staff"), (89, 53, "Administrator"), (89, 30, "Public board")]
    for x, y, name in actors:
        ax.add_patch(Ellipse((x, y + 4), 5, 6, edgecolor=CYAN, facecolor=PANEL, lw=1.5))
        ax.plot([x, x], [y + 1, y - 7], color=CYAN, lw=1.5)
        ax.plot([x - 4, x + 4], [y - 2, y - 2], color=CYAN, lw=1.5)
        ax.plot([x, x - 4], [y - 7, y - 12], color=CYAN, lw=1.5)
        ax.plot([x, x + 4], [y - 7, y - 12], color=CYAN, lw=1.5)
        ax.text(x, y - 16, name, color=INK, fontsize=8, ha="center")
    cases = [
        (42, 75, "Register visit"), (64, 75, "Issue token + predict"),
        (42, 58, "Manage consultation"), (64, 58, "Order / progress lab"),
        (42, 41, "Admit / release bed"), (64, 41, "Update visit location"),
        (42, 24, "View KPIs and load"), (64, 24, "View public queue"),
    ]
    for x, y, text in cases:
        e=Ellipse((x,y),18,9,facecolor=PANEL,edgecolor=TEAL,lw=1.5); ax.add_patch(e)
        ax.text(x,y,text,color=INK,fontsize=8,ha="center",va="center")
    links=[(11,76,33,75),(11,53,33,58),(11,30,33,41),(85,76,73,58),(85,53,73,24),(85,30,73,24)]
    for x1,y1,x2,y2 in links: ax.plot([x1,x2],[y1,y2],color=LINE,lw=1.2)
    save(fig, DIAGRAMS / "08_use_case_diagram.png")


def er_diagram():
    fig, ax = canvas("Entity-Relationship Diagram", size=(14, 9))
    entities = [
        (4, 65, 20, 23, "DEPARTMENT", "PK id\ncode UNIQUE\ntype\navg_service_minutes", CYAN),
        (29, 65, 19, 23, "USER", "PK id\nFK department_id\nemail UNIQUE\nrole", BLUE),
        (53, 65, 19, 23, "PATIENT", "PK id\nmrn UNIQUE\nname\nage, gender", TEAL),
        (77, 58, 20, 30, "VISIT", "PK id\nFK patient_id\nFK current_department_id\nFK assigned_doctor_id\nFK bed_id\nstatus, priority", AMBER),
        (5, 20, 20, 23, "BED", "PK id\nFK department_id\nFK current_visit_id\nbed_number\nstatus", RED),
        (37, 20, 20, 23, "LAB_TEST", "PK id\nFK visit_id\ntest_name\nstatus\ntimestamps", CYAN),
        (69, 20, 25, 23, "MOVEMENT_LOG", "PK id\nFK visit_id\nFK from_department_id\nFK to_department_id\ntimestamp", BLUE),
    ]
    for x,y,w,h,t,b,c in entities: box(ax,x,y,w,h,t,b,c,fs=8)
    arrow(ax,24,76,29,76,"1 : many staff")
    arrow(ax,72,76,77,76,"1 : many visits")
    arrow(ax,77,65,48,42,"1 : many tests",rad=-0.12)
    arrow(ax,87,58,81,43,"1 : many movements")
    arrow(ax,15,65,15,43,"1 : many beds")
    arrow(ax,24,69,77,69,"1 : many current visits",rad=0.08)
    save(fig, DIAGRAMS / "09_er_diagram.png")


def algorithm_flow():
    fig, ax = canvas("Core Algorithm Flowchart - Triage and Wait Prediction")
    box(ax, 37, 82, 26, 10, "Visit request received", "", BLUE)
    box(ax, 35, 65, 30, 11, "Validate department and patient fields", "", CYAN)
    box(ax, 35, 48, 30, 11, "Complete missing vitals with defaults", "", AMBER)
    box(ax, 6, 28, 28, 13, "Triage classifier", "vitals -> normal / urgent / critical\n+ confidence", RED, fs=8)
    box(ax, 66, 28, 28, 13, "Queue and wait regressor", "priority rank -> people ahead\n+ department, hour, service, servers", TEAL, fs=8)
    box(ax, 35, 8, 30, 12, "Persist token, predictions and movement; broadcast", "", BLUE, fs=8)
    arrow(ax,50,82,50,76)
    arrow(ax,50,65,50,59)
    arrow(ax,43,48,25,41,"six vital features")
    arrow(ax,57,48,80,41,"queue context")
    arrow(ax,20,28,42,20,"priority + confidence")
    arrow(ax,80,28,58,20,"wait minutes")
    save(fig, DIAGRAMS / "10_core_algorithm_flowchart.png")


def chart_style(ax, title):
    ax.set_facecolor(NAVY)
    ax.set_title(title, color=INK, fontsize=15, weight="bold", pad=14)
    ax.tick_params(colors=MUTED)
    for s in ax.spines.values(): s.set_color(LINE)
    ax.grid(axis="y", color="#26364B", alpha=.7)


def charts():
    # Confusion matrix
    cm=np.array([[63,0,37],[0,1525,2],[2,31,590]])
    fig,ax=plt.subplots(figsize=(7,5),dpi=150); fig.patch.set_facecolor(NAVY); ax.set_facecolor(NAVY)
    im=ax.imshow(cm,cmap="Blues")
    ax.set_xticks(range(3),["Critical","Normal","Urgent"],color=MUTED); ax.set_yticks(range(3),["Critical","Normal","Urgent"],color=MUTED)
    ax.set_xlabel("Predicted",color=INK); ax.set_ylabel("Actual",color=INK); ax.set_title("Triage Test Confusion Matrix (n=2,250)",color=INK,weight="bold")
    for i in range(3):
        for j in range(3): ax.text(j,i,str(cm[i,j]),ha="center",va="center",color="white" if cm[i,j]>.45*cm.max() else NAVY,weight="bold")
    save(fig,CHARTS/"01_triage_confusion_matrix.png")

    fig,ax=plt.subplots(figsize=(8,5),dpi=150); fig.patch.set_facecolor(NAVY); chart_style(ax,"Measured Model Metrics")
    labs=["Wait R-squared","Triage accuracy","Triage macro F1"]; vals=[.951041,.968,.898475]
    bars=ax.bar(labs,vals,color=[BLUE,TEAL,CYAN],width=.6); ax.set_ylim(0,1.05); ax.set_ylabel("Score",color=INK)
    for b,v in zip(bars,vals): ax.text(b.get_x()+b.get_width()/2,v+.018,f"{v:.3f}",ha="center",color=INK,weight="bold")
    save(fig,CHARTS/"02_model_metrics.png")

    fig,ax=plt.subplots(figsize=(7,5),dpi=150); fig.patch.set_facecolor(NAVY); chart_style(ax,"Wait-Time Regression Error")
    labs=["MAE","RMSE"]; vals=[5.982,8.580]; bars=ax.bar(labs,vals,color=[CYAN,AMBER],width=.5); ax.set_ylabel("Minutes",color=INK); ax.set_ylim(0,10)
    for b,v in zip(bars,vals): ax.text(b.get_x()+b.get_width()/2,v+.25,f"{v:.3f}",ha="center",color=INK,weight="bold")
    save(fig,CHARTS/"03_wait_error.png")

    eps=["health","queue board","auth/me","departments","doctors","visits","beds","labs","KPIs","dept load"]
    means=[4.496,10.056,3.985,9.124,7.101,10.629,10.862,8.528,12.321,14.231]
    fig,ax=plt.subplots(figsize=(10,6),dpi=150); fig.patch.set_facecolor(NAVY); chart_style(ax,"Mean Local API Latency (15 Sequential Requests Each)")
    bars=ax.barh(eps[::-1],means[::-1],color=BLUE); ax.set_xlabel("Milliseconds",color=INK)
    for b,v in zip(bars,means[::-1]): ax.text(v+.2,b.get_y()+b.get_height()/2,f"{v:.1f}",va="center",color=INK,fontsize=8)
    save(fig,CHARTS/"04_api_latency.png")

    fig,ax=plt.subplots(figsize=(8,5),dpi=150); fig.patch.set_facecolor(NAVY); chart_style(ax,"Demonstration Bed Capacity")
    labels=["General Ward","ICU"]; occupied=[7,4]; available=[5,2]; x=np.arange(2)
    ax.bar(x,occupied,label="Occupied",color=RED); ax.bar(x,available,bottom=occupied,label="Available",color=TEAL)
    ax.set_xticks(x,labels,color=MUTED); ax.set_ylabel("Beds",color=INK); ax.legend(facecolor=PANEL,labelcolor=INK)
    for i,(o,a) in enumerate(zip(occupied,available)): ax.text(i,o+a+.25,f"{o+a} total",ha="center",color=INK)
    save(fig,CHARTS/"05_bed_capacity.png")

    fig,ax=plt.subplots(figsize=(8,5),dpi=150); fig.patch.set_facecolor(NAVY); chart_style(ax,"Synthetic Dataset Partitions")
    labs=["Wait-time","Triage"]; train=[10200,12750]; test=[1800,2250]; x=np.arange(2)
    ax.bar(x,train,label="Train (85%)",color=BLUE); ax.bar(x,test,bottom=train,label="Test (15%)",color=CYAN)
    ax.set_xticks(x,labs,color=MUTED); ax.set_ylabel("Rows",color=INK); ax.legend(facecolor=PANEL,labelcolor=INK)
    for i,total in enumerate([12000,15000]): ax.text(i,total+350,f"{total:,}",ha="center",color=INK,weight="bold")
    save(fig,CHARTS/"06_dataset_split.png")


def main():
    architecture(); workflow(); dfd0(); dfd1(); dfd2(); uml_class(); sequence(); use_case(); er_diagram(); algorithm_flow(); charts()
    print(f"Generated {len(list(DIAGRAMS.glob('*.png')))} diagrams and {len(list(CHARTS.glob('*.png')))} charts.")


if __name__ == "__main__":
    main()
