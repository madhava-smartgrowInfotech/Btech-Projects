from __future__ import annotations

from pathlib import Path
import zipfile
import re
from xml.etree import ElementTree as ET

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls, qn
from pptx.util import Inches, Pt


BATCH = Path(__file__).resolve().parents[2]
CODE = BATCH / "8.ProjectCode"
TEMPLATES = Path(r"D:\abstracts\Templates")
DIAG = CODE / "docs" / "diagrams"
CHART = CODE / "docs" / "charts"
SHOT = CODE / "docs" / "screenshots"

NAVY = "08111F"; PANEL = "111C31"; PANEL2 = "17243B"; WHITE = "F2F7FD"; MUTED = "9FB0C7"
BLUE = "3B82F6"; CYAN = "22D3EE"; TEAL = "10B981"; AMBER = "F59E0B"; RED = "EF4444"
STUDENTS = "A. RAMU · 23K91A6715     B. RUSHI · 23K91A6720\nB. RAJ KUMAR · 23K91A6725     A. PRABHAS · 23K91A6703"
TITLE = "AI Powered Intelligent Hospital Patient Flow Management System"

LEGACY_TERMS = [
    "[STUDENT NAME", "[ROLL NO", "Fakeddit", "PHEME", "Snopes", "MCNN",
    "bank transaction", "social media manipulation", "skincare", "Dayananda",
    "Sindhu", "recommender system",
]


def ensure_jpg_content_type(path: Path):
    """Make the inherited package standards-compliant and scrub hidden legacy subject text."""
    temp = path.with_suffix(".repacked.pptx")
    with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as target:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename == "[Content_Types].xml":
                root = ET.fromstring(data)
                namespace = root.tag.split("}")[0].strip("{")
                default_tag = f"{{{namespace}}}Default"
                if not any(node.get("Extension", "").lower() == "jpg" for node in root.findall(default_tag)):
                    ET.SubElement(root, default_tag, {"Extension": "jpg", "ContentType": "image/jpeg"})
                data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            elif item.filename.lower().endswith((".xml", ".rels")):
                text = data.decode("utf-8", errors="ignore")
                for term in LEGACY_TERMS:
                    text = re.sub(re.escape(term), "CareFlow project", text, flags=re.IGNORECASE)
                data = text.encode("utf-8")
            target.writestr(item, data)
    temp.replace(path)


def clear_slide(slide):
    for shape in list(slide.shapes):
        slide.shapes._spTree.remove(shape._element)


def bg(slide, number, section):
    fill=slide.background.fill; fill.solid(); fill.fore_color.rgb=RGBColor.from_string(NAVY)
    # Subtle visual motif: paired rounded nodes, not an accent stripe.
    for x,y,w,h,c,t in [(12.1,.45,.45,.45,BLUE,55),(12.55,.32,.22,.22,CYAN,30)]:
        sh=slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.OVAL,Inches(x),Inches(y),Inches(w),Inches(h)); sh.fill.solid(); sh.fill.fore_color.rgb=RGBColor.from_string(c); sh.fill.transparency=t; sh.line.fill.background()
    add_text(slide,section,.55,7.05,4.6,.22,9,MUTED)
    add_text(slide,str(number),12.15,7.02,.55,.25,9,MUTED,align=PP_ALIGN.RIGHT)


def add_text(slide,text,x,y,w,h,size=16,color=WHITE,bold=False,align=PP_ALIGN.LEFT,font="Calibri",margin=.04,vertical=MSO_ANCHOR.TOP):
    box=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h))
    tf=box.text_frame; tf.clear(); tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=Inches(margin); tf.vertical_anchor=vertical
    p=tf.paragraphs[0]; p.alignment=align
    r=p.add_run(); r.text=text; r.font.name=font; r.font.size=Pt(size); r.font.bold=bold; r.font.color.rgb=RGBColor.from_string(color)
    return box


def bullet_char(p):
    pPr=p._p.get_or_add_pPr()
    for child in list(pPr):
        if child.tag in (qn('a:buNone'),qn('a:buChar'),qn('a:buAutoNum')): pPr.remove(child)
    bu=parse_xml(f'<a:buChar {nsdecls("a")} char="&#x2022;"/>'); pPr.append(bu)


def add_bullets(slide,items,x,y,w,h,size=16,color=WHITE):
    box=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)); tf=box.text_frame; tf.clear(); tf.word_wrap=True
    tf.margin_left=tf.margin_right=Inches(.08); tf.margin_top=tf.margin_bottom=Inches(.05)
    for i,item in enumerate(items):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.text=item; p.level=0; p.space_after=Pt(10); p.line_spacing=1.08; bullet_char(p)
        for r in p.runs: r.font.name="Calibri"; r.font.size=Pt(size); r.font.color.rgb=RGBColor.from_string(color)
    return box


def rect(slide,x,y,w,h,fill=PANEL,line="26364B",radius=True):
    typ=MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if radius else MSO_AUTO_SHAPE_TYPE.RECTANGLE
    sh=slide.shapes.add_shape(typ,Inches(x),Inches(y),Inches(w),Inches(h)); sh.fill.solid(); sh.fill.fore_color.rgb=RGBColor.from_string(fill); sh.line.color.rgb=RGBColor.from_string(line); sh.line.width=Pt(1)
    return sh


def title(slide,text,kicker=""):
    if kicker: add_text(slide,kicker.upper(),.6,.42,6,.25,10,CYAN,bold=True)
    add_text(slide,text,.6,.78,11.8,.55,30,WHITE,bold=True,font="Cambria")


def cover(slide,review_label):
    fill=slide.background.fill; fill.solid(); fill.fore_color.rgb=RGBColor.from_string(NAVY)
    # interconnected care nodes
    coords=[(8.9,1.0,1.0,BLUE),(10.7,2.0,.72,CYAN),(8.2,3.1,.65,TEAL),(11.1,4.2,.9,AMBER),(9.2,5.25,.62,RED)]
    for x,y,s,c in coords:
        sh=slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.OVAL,Inches(x),Inches(y),Inches(s),Inches(s)); sh.fill.solid(); sh.fill.fore_color.rgb=RGBColor.from_string(c); sh.fill.transparency=10; sh.line.fill.background()
    add_text(slide,"CAREFLOW",.72,.55,3,.32,12,CYAN,bold=True)
    cover_title=add_text(slide,TITLE,.72,1.18,7.65,1.65,28,WHITE,bold=True,font="Cambria")
    cover_title.text_frame.word_wrap=True
    add_text(slide,review_label,.75,3.04,6.8,.4,15,AMBER,bold=True)
    add_text(slide,STUDENTS,.75,4.05,7.2,.95,14,WHITE)
    add_text(slide,"Guide: [GUIDE NAME]  ·  CSE (Data Science)  ·  Batch A10",.75,5.38,7.6,.35,12,MUTED)
    add_text(slide,"Evidence-based documentation · Synthetic model data · Real running-system captures",.75,6.4,10,.28,11,MUTED)


def contents(slide,number,labels,section):
    bg(slide,number,section); title(slide,"Contents","Navigation")
    cols=2; rows=(len(labels)+1)//2
    for i,label in enumerate(labels):
        col=i//rows; row=i%rows; x=.75+col*6.15; y=1.65+row*.78
        rect(slide,x,y,5.7,.58,PANEL2)
        add_text(slide,f"{i+1:02d}",x+.18,y+.14,.5,.22,11,CYAN,bold=True)
        add_text(slide,label,x+.82,y+.12,4.6,.3,15,WHITE,bold=True)


def text_slide(slide,number,section,heading,items,side_title=None,side_stats=None):
    bg(slide,number,section); title(slide,heading,section)
    if side_stats:
        add_bullets(slide,items,.7,1.62,7.3,4.9,16)
        x=8.4
        for i,(big,label,color) in enumerate(side_stats):
            y=1.65+i*1.45; rect(slide,x,y,4.15,1.12,PANEL2,line=color)
            add_text(slide,big,x+.25,y+.17,1.55,.45,25,color,bold=True)
            add_text(slide,label,x+1.7,y+.26,2.15,.35,13,WHITE,bold=True)
    else:
        rect(slide,.65,1.55,12.0,5.05,PANEL)
        add_bullets(slide,items,.95,1.88,11.35,4.4,17)


def image_slide(slide,number,section,heading,image,caption,items=None,split=False):
    bg(slide,number,section); title(slide,heading,section)
    if split:
        rect(slide,.65,1.55,7.65,5.1,PANEL); slide.shapes.add_picture(str(image),Inches(.85),Inches(1.75),width=Inches(7.25),height=Inches(4.3))
        add_text(slide,caption,.9,6.15,7.1,.25,10,MUTED,align=PP_ALIGN.CENTER)
        rect(slide,8.55,1.55,4.1,5.1,PANEL2)
        add_bullets(slide,items or [],8.82,1.9,3.55,4.2,14)
    else:
        rect(slide,.65,1.5,12,5.22,PANEL); slide.shapes.add_picture(str(image),Inches(.9),Inches(1.72),width=Inches(11.5),height=Inches(4.55))
        add_text(slide,caption,1,6.28,11.25,.24,10,MUTED,align=PP_ALIGN.CENTER)


def two_images(slide,number,section,heading,img1,cap1,img2,cap2):
    bg(slide,number,section); title(slide,heading,section)
    for x,img,cap in [(.65,img1,cap1),(6.78,img2,cap2)]:
        rect(slide,x,1.55,5.9,5.08,PANEL)
        slide.shapes.add_picture(str(img),Inches(x+.2),Inches(1.8),width=Inches(5.5),height=Inches(3.45))
        add_text(slide,cap,x+.3,5.55,5.3,.55,12,WHITE,bold=True,align=PP_ALIGN.CENTER)


def references_slide(slide,number,section):
    bg(slide,number,section); title(slide,"References",section)
    refs=[
        "[1] Saritha et al., Alleviate, IEEE Access, 2025, doi: 10.1109/ACCESS.2025.3647089.",
        "[2] Tan et al., Personalized healthcare, JIWE, 2024.",
        "[3] Abinaya and Ganesan, Nearest healthcare facilities, GCCT, 2015.",
        "[4] Umbare et al., Smart healthcare using AI/ML, ICIPCN, 2024.",
        "[5] Mogaveera et al., E-health monitoring and planning, ICICT, 2021.",
        "[6] Surve et al., Healthcare chatbot using ML/NLP, ICAST, 2023.",
        "[7] Waiting Time Prediction in Queue Management, ICRPSET, 2024.",
        "[8] Outpatient waiting-time prediction, Translational Pediatrics, 2023.",
    ]
    rect(slide,.65,1.5,12,5.3,PANEL); add_bullets(slide,refs,.9,1.78,11.45,4.7,13)


def thank_you(slide,number,label):
    fill=slide.background.fill; fill.solid(); fill.fore_color.rgb=RGBColor.from_string(NAVY)
    add_text(slide,"THANK YOU",1.2,2.0,10.9,.8,42,WHITE,bold=True,font="Cambria",align=PP_ALIGN.CENTER)
    add_text(slide,"Questions and suggestions are welcome",1.2,3.15,10.9,.42,18,CYAN,align=PP_ALIGN.CENTER)
    add_text(slide,"CareFlow · Batch CSDS-A-A10 · "+label,1.2,5.85,10.9,.3,12,MUTED,align=PP_ALIGN.CENTER)
    add_text(slide,str(number),12.15,7.02,.55,.25,9,MUTED,align=PP_ALIGN.RIGHT)


def prep(template_name):
    prs=Presentation(TEMPLATES/template_name)
    for s in prs.slides: clear_slide(s)
    prs.core_properties.title=TITLE; prs.core_properties.subject="CareFlow academic project documentation"; prs.core_properties.author="A. RAMU; B. RUSHI; B. RAJ KUMAR; A. PRABHAS"
    return prs


def review1():
    prs=prep("Review_1_PPT.pptx"); S=prs.slides
    cover(S[0],"REVIEW 1 · PROBLEM IDENTIFICATION AND RESEARCH")
    contents(S[1],2,["Abstract","Base paper","Literature survey","Existing system","Research gap","Objectives","Proposed approach","Expected outcomes"],"Review 1")
    text_slide(S[2],3,"Abstract","Abstract",["Hospitals coordinate registration, queues, consultation, laboratory work and beds through changing shared state.","CareFlow creates digital tokens, tracks visits, exposes laboratory and capacity state, and publishes live role views.","Two models assist triage priority and wait estimation; both are evaluated only on synthetic data.","The project demonstrates software integration—not clinical validity or measured wait reduction."],side_stats=[("7","Departments",CYAN),("5+1","Staff roles + public",TEAL),("2","Saved ML models",AMBER)])
    text_slide(S[3],4,"Research","Base Paper: Alleviate",["IEEE Access, 2025; DOI 10.1109/ACCESS.2025.3647089.","Flutter/Dart + Flask + Firebase integrated appointments, prescriptions, maps, clinic dashboards and personalised guidance.","Reported 97.24% precision belongs to specialist recommendation—not hospital triage.","CareFlow adopts the integrated dashboard idea but focuses on internal patient flow and resource state."],side_stats=[("97.24%","Paper’s recommendation precision",BLUE),("Different","Task and dataset",RED)])
    text_slide(S[4],5,"Research","Literature Survey",["Access and location: hospital discovery, routing and appointment support.","Prediction: disease/specialist recommendation from symptoms.","Personalisation: diet, exercise and chronic-care guidance.","Conversational support: NLP/chatbots for health queries.","Waiting-time research motivates prediction, but institutions and outcome definitions differ."],side_stats=[("19","References retained",CYAN),("4","Research themes",TEAL)])
    image_slide(S[5],6,"Evidence","Supporting Evidence",CHART/"06_dataset_split.png","Figure: project dataset partitions",["12,000 wait rows","15,000 triage rows","85/15 splits","NumPy seed 42","No real patient records"],split=True)
    text_slide(S[6],7,"Problem","Existing System",["Registration and billing may be digital while internal coordination remains fragmented.","Name calling and simple tokens do not preserve priority or department movement.","Laboratory work and bed availability may rely on calls or registers.","Patients and staff lack one consistent current-state view."],side_stats=[("Manual","Queue coordination",RED),("Fragmented","Department state",AMBER)])
    text_slide(S[7],8,"Problem","Limitations of Existing Approaches",["Appointment apps stop before the in-hospital journey.","Prediction-only studies do not provide operational actions or resource state.","Stale bed data delays admission decisions.","Unexplained scores can hide class-specific safety failures.","Disconnected systems create duplicate entry and weak traceability."],side_stats=[("No","Unified visit state",RED),("No","Live capacity view",RED)])
    text_slide(S[8],9,"Problem","Research Gap",["Integrate token, priority, visit status, movement, laboratory work and bed state.","Give each authorised role a focused action surface over the same data.","Publish public queue progress without exposing patient identity.","Separate synthetic-model evidence from clinical or operational impact claims."],side_stats=[("One","Operational source of truth",TEAL),("Explicit","Evidence boundary",CYAN)])
    text_slide(S[9],10,"Problem","Problem Statement",["Design and implement a role-based system that coordinates patients across OPD, emergency, laboratory, pharmacy, ward and ICU.","Preserve priority and current state, expose resource availability, and provide reproducible prediction assistance.","Report limitations honestly where real data, validation or deployment evidence is absent."],side_stats=[("Input","Patient + vitals + department",BLUE),("Output","Token + state + wait",TEAL)])
    text_slide(S[10],11,"Objectives","Project Objectives",["Generate department tokens and priority-aware queues.","Track visit state and explicit department movement.","Coordinate laboratory orders and progress.","Expose ward and ICU capacity in real time.","Predict triage class and expected wait from documented features.","Provide role dashboards plus a public waiting board."],side_stats=[("6","Objectives",CYAN),("0","Clinical claims",AMBER)])
    image_slide(S[11],12,"Approach","Proposed Approach",DIAG/"02_high_level_workflow.png","Figure: end-to-end workflow",["Register","Predict","Queue","Consult","Route","Close"],split=True)
    image_slide(S[12],13,"Design","System Architecture",DIAG/"01_system_architecture.png","Figure: implemented application architecture")
    text_slide(S[13],14,"Outcomes","Expected Outcomes and Contributions",["A working multi-role prototype with populated operational screens.","Reproducible synthetic model evaluation with class-specific reporting.","Auditable queue ordering and movement evidence.","Measured local API availability and latency.","A clear list of unmeasured outcomes and production gaps."],side_stats=[("150/150","Read smoke requests",TEAL),("13","Real screenshots",CYAN)])
    references_slide(S[14],15,"Research")
    thank_you(S[15],16,"Review 1")
    out=BATCH/"7.Review_1_PPT.pptx"; prs.save(out); ensure_jpg_content_type(out); print("Wrote",out.name,out.stat().st_size)


def review2():
    prs=prep("Review_2_PPT.pptx"); S=prs.slides
    cover(S[0],"REVIEW 2 · DESIGN, METHODOLOGY AND PROGRESS")
    contents(S[1],2,["Recap","Architecture","Methodology","Data and models","Decision logic","Database and UML","Implementation","Results","Outputs","Testing","Next steps"],"Review 2")
    text_slide(S[2],3,"Recap","Problem and Proposed System",["Problem: fragmented internal queues, laboratory work and bed checks.","System: one persisted Visit state with role-based actions.","Assistance: triage classification and expected-wait regression.","Boundary: academic local prototype using synthetic data."],side_stats=[("23","Demo visits",BLUE),("18","Beds",TEAL)])
    image_slide(S[3],4,"Design","System Architecture",DIAG/"01_system_architecture.png","Implemented layers and live channel")
    image_slide(S[4],5,"Method","End-to-End Methodology",DIAG/"02_high_level_workflow.png","Registration through discharge",["Validate input","Predict once","Persist state","Broadcast changes"],split=True)
    image_slide(S[5],6,"Data","Dataset",CHART/"06_dataset_split.png","Synthetic generator sizes and split",["Wait: 12,000","Triage: 15,000","85/15 train/test","Seed 42","No clinical records"],split=True)
    text_slide(S[6],7,"Data","Preprocessing",["Label-encode department type and priority for wait regression.","Keep numerical features on operational scales for tree ensembles.","Store encoders and triage feature order with Joblib artefacts.","Complete missing individual vitals with documented defaults.","Preserve named pandas columns at inference."],side_stats=[("6","Wait features",CYAN),("6","Triage features",TEAL)])
    text_slide(S[7],8,"Models","Model Architecture",["Wait: RandomForestRegressor; 200 trees; max depth 10.","Triage: GradientBoostingClassifier; 150 estimators; max depth 3.","Triage labels come from a simplified early-warning scoring rule.","Runtime returns wait minutes, priority label and confidence."],side_stats=[("RF","Wait model",BLUE),("GB","Triage model",AMBER)])
    text_slide(S[8],9,"Training","Training Configuration",["NumPy random seed 42; scikit-learn random state 42.","Both splits: 85% train / 15% test.","Triage split is stratified.","Models saved under backend/app/ml/artifacts.","Existing artefacts evaluated without retraining during documentation."],side_stats=[("10,200","Wait train",BLUE),("12,750","Triage train",TEAL)])
    image_slide(S[9],10,"Logic","Decision Logic",DIAG/"10_core_algorithm_flowchart.png","Prediction, persistence and broadcast")
    image_slide(S[10],11,"Flow","Data Flow",DIAG/"04_dfd_level_1.png","DFD Level 1")
    two_images(S[11],12,"Design","Database and UML",DIAG/"09_er_diagram.png","Entity relationships",DIAG/"06_uml_class_diagram.png","Persistent domain classes")
    text_slide(S[12],13,"Build","Technology Stack",["Frontend: React 19, TypeScript, Vite, Tailwind, Axios, Zustand, Recharts.","Backend: FastAPI, Pydantic, SQLAlchemy, SQLite, JWT, WebSockets.","ML: scikit-learn, pandas, NumPy, Joblib.","Verified runtime: Windows 11, Python 3.11.9, Chrome."],side_stats=[("5173","Frontend port",CYAN),("8010","Backend port",TEAL)])
    text_slide(S[13],14,"Progress","Implementation Progress",["Authentication and five staff roles implemented.","Visit, queue and movement routes implemented.","Laboratory and bed workflows implemented.","Admin KPIs and public waiting board implemented.","Two model artefacts present and measured.","Thirteen populated screens captured."],side_stats=[("7","Entities",BLUE),("22","Application routes",TEAL)])
    image_slide(S[14],15,"Results","Preliminary Results",CHART/"02_model_metrics.png","Measured synthetic-test scores",["Wait R² 0.951041","MAE 5.982 min","RMSE 8.580 min","Triage accuracy 0.9680","Macro F1 0.898475","Critical recall 0.63"],split=True)
    two_images(S[15],16,"Outputs","Output Screens",SHOT/"04_admin_dashboard.png","Administrator command centre",SHOT/"07_doctor_dashboard.png","Doctor queue")
    text_slide(S[16],17,"Testing","Initial Testing and Observations",["150/150 sequential read requests returned HTTP 200.","Mean endpoint latency: 3.985–14.231 ms on local loopback.","WebSocket connection: 46.657 ms.","Frontend lint and production build exited zero.","Observed nurse initial-tab defect and large JavaScript chunks.","No automated repository test suite exists."],side_stats=[("150","Successful reads",TEAL),("14","Lint warnings",AMBER)])
    text_slide(S[17],18,"Risks","Challenges and Corrective Actions",["Synthetic data → seek governed real data and external validation.","63% critical recall → cost-sensitive learning and calibration.","State coupling gaps → explicit transition service and tests.","Public WebSocket → authenticated channels and audit.","SQLite/single process → PostgreSQL, broker and resilient deployment."],side_stats=[("63%","Critical recall",RED),("0","Clinical studies",AMBER)])
    text_slide(S[18],19,"Plan","Next Steps",["Automate unit, integration and end-to-end state tests.","Validate on de-identified temporal patient-flow data.","Conduct clinician-led usability and safety assessment.","Integrate hospital systems through HL7 FHIR.","Add production security, monitoring, backups and load testing."],side_stats=[("First","Safety validation",RED),("Then","Production scaling",TEAL)])
    thank_you(S[19],20,"Review 2")
    out=BATCH/"13.Review_2_PPT.pptx"; prs.save(out); ensure_jpg_content_type(out); print("Wrote",out.name,out.stat().st_size)


def final_deck():
    prs=prep("Final_PPT.pptx"); S=prs.slides
    cover(S[0],"FINAL REVIEW · COMPLETE PROJECT")
    contents(S[1],2,["Problem and research","Objectives and approach","Architecture and methodology","Implementation","Measured results","Output screens","Conclusion and future work"],"Final Review")
    text_slide(S[2],3,"Overview","Abstract",["CareFlow coordinates patient visits across queues, consultation, laboratory and bed state.","One persisted Visit record drives role dashboards and a public board.","Random Forest estimates wait; Gradient Boosting estimates triage priority.","Evidence is synthetic-model evaluation plus local software verification."],side_stats=[("7","Departments",CYAN),("13","Captured screens",TEAL)])
    text_slide(S[3],4,"Research","Base Paper",["Alleviate, IEEE Access, 2025.","Integrated mobile healthcare access, recommendation, prescriptions, maps and planning.","Its 97.24% precision concerns specialist recommendation.","CareFlow changes the problem to internal operational flow; metrics are not comparable."],side_stats=[("97.24%","Different task",BLUE),("2025","IEEE Access",CYAN)])
    text_slide(S[4],5,"Research","Literature Survey",["Access and facility-location systems.","Disease and specialist recommendation.","Personalised diet/exercise and monitoring.","Healthcare chatbots and NLP.","Waiting-time prediction and interpretability."],side_stats=[("19","References",CYAN),("4","Survey themes",TEAL)])
    text_slide(S[5],6,"Research","Research Gap",["No single shared state across tokens, movement, tests and beds.","Prediction studies often stop at a score, without operational action.","Patient-facing apps do not coordinate the internal hospital journey.","Evidence boundaries between synthetic metrics and real impact are often unclear."],side_stats=[("Gap","Operational integration",RED),("Need","Auditable state",AMBER)])
    text_slide(S[6],7,"Problem","Problem Statement",["Coordinate patients through OPD, emergency, laboratory, pharmacy, ward and ICU while preserving priority and current state.","Give each role the actions and visibility needed for its part of the journey.","Use AI assistance without overstating clinical validity or operational impact."],side_stats=[("One","Visit state",TEAL),("Many","Role views",BLUE)])
    text_slide(S[7],8,"Objectives","Objectives",["Digital tokens and priority queues.","Visit state and movement tracking.","Laboratory workflow.","Live ward and ICU capacity.","Triage and wait prediction.","Role dashboards and public board."],side_stats=[("6","Project objectives",CYAN),("5+1","Views",TEAL)])
    image_slide(S[8],9,"Approach","Proposed System",DIAG/"02_high_level_workflow.png","End-to-end operational flow")
    image_slide(S[9],10,"Design","System Architecture",DIAG/"01_system_architecture.png","React, FastAPI, ML, SQLite and WebSocket")
    image_slide(S[10],11,"Method","Methodology",DIAG/"10_core_algorithm_flowchart.png","Triage and wait inference integrated with persistence")
    image_slide(S[11],12,"Data","Dataset and Models",CHART/"06_dataset_split.png","Synthetic datasets and 85/15 splits",["RF: 200 trees","GB: 150 estimators","Seed 42","No real patient data"],split=True)
    text_slide(S[12],13,"Logic","Decision Logic",["Missing vital components are completed with documented defaults.","Classifier returns normal, urgent or critical plus confidence.","Queue-ahead count respects priority rank.","Regressor returns non-negative wait minutes.","Visit and movement are committed before broadcast."],side_stats=[("3","Priority classes",CYAN),("2","Default servers",AMBER)])
    image_slide(S[13],14,"Flow","Data Flow",DIAG/"05_dfd_level_2.png","Level 2: register and prioritise")
    two_images(S[14],15,"Design","Database and Classes",DIAG/"09_er_diagram.png","Seven persistent entities",DIAG/"06_uml_class_diagram.png","Domain model")
    text_slide(S[15],16,"Build","Implementation Highlights",["JWT login and role dependencies.","Priority-first queue service and movement logs.","Bed admission/release and laboratory-state routes.","Public queue board and administrator KPIs.","Axios token injection and WebSocket refresh.","Joblib artefacts with stored encoders and feature order."],side_stats=[("22","Application routes",BLUE),("7","Persistent entities",TEAL)])
    image_slide(S[16],17,"Results","Model Performance",CHART/"02_model_metrics.png","Generator-matched test scores",["Wait R² 0.951041","Triage accuracy 0.9680","Macro F1 0.898475","Not clinical validation"],split=True)
    two_images(S[17],18,"Results","Confusion and Error",CHART/"01_triage_confusion_matrix.png","Critical recall = 63%",CHART/"03_wait_error.png","MAE 5.982 · RMSE 8.580 min")
    text_slide(S[18],19,"Analysis","Parameter and Limitation Analysis",["Fixed Random Forest: 200 trees, max depth 10.","Fixed Gradient Boosting: 150 estimators, max depth 3.","No threshold sweep or calibration artefact exists—none is invented.","Overall accuracy hides 37 critical-to-urgent errors.","Real-data temporal and subgroup analysis remains future work."],side_stats=[("63%","Critical recall",RED),("None","Threshold sweep",AMBER)])
    image_slide(S[19],20,"Testing","Performance and Testing",CHART/"04_api_latency.png","Sequential local mean latency",["150/150 HTTP 200","3.985–14.231 ms means","46.657 ms WebSocket","Build passed","14 lint warnings","No load test"],split=True)
    text_slide(S[20],21,"Comparison","Comparison with Base Paper",["Alleviate: patient access, specialist recommendation, prescriptions, maps and personalised plans.","CareFlow: internal queue, visit, laboratory and capacity coordination.","Different tasks, datasets, splits and conditions make numeric comparison invalid.","The valid comparison is functional coverage and research gap."],side_stats=[("Base","Patient-facing",BLUE),("Ours","Operations-facing",TEAL)])
    two_images(S[21],22,"Outputs","Output 1 · Public and Reception",SHOT/"03_waiting_board.png","Public token board",SHOT/"05_reception_dashboard.png","Registration list")
    two_images(S[22],23,"Outputs","Output 2 · Clinical Workflow",SHOT/"07_doctor_dashboard.png","Doctor queue",SHOT/"10_admit_patient.png","Available-bed selection")
    two_images(S[23],24,"Outputs","Output 3 · Operations",SHOT/"04_admin_dashboard.png","Administrator overview",SHOT/"13_laboratory_dashboard.png","Laboratory work queue")
    text_slide(S[24],25,"Close","Conclusion",["Implemented one coherent multi-role patient-flow prototype.","All 150 measured read requests returned HTTP 200.","Models produced reproducible synthetic-test results.","Critical recall and missing clinical validation define the safety boundary.","No real wait-reduction or deployment claim is made."],side_stats=[("Achieved","Functional integration",TEAL),("Limited","Clinical evidence",RED)])
    text_slide(S[25],26,"Next","Future Scope",["Governed real-data collection and temporal validation.","Cost-sensitive triage, calibration and uncertainty display.","Automated state-transition and end-to-end tests.","HL7 FHIR integration with EHR, lab and admission systems.","PostgreSQL, message broker, authenticated live channels and observability.","Clinician-led usability, safety and prospective impact study."],side_stats=[("1","Validate safety",RED),("2","Scale securely",TEAL)])
    references_slide(S[26],27,"Final Review")
    thank_you(S[27],28,"Final Review")
    out=BATCH/"16.Final_PPT.pptx"; prs.save(out); ensure_jpg_content_type(out); print("Wrote",out.name,out.stat().st_size)


def main(): review1(); review2(); final_deck()


if __name__ == "__main__": main()
