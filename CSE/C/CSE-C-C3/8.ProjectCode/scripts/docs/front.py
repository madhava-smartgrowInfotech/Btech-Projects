"""Front matter of the full report: cover, certificate, declaration, acknowledgement, abstract, abbreviations."""

import os

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from . import facts as F
from .kit import add_runs

BANNER = os.path.join(F.DOCS, "figures", "college_banner.png")


def _banner():
    """The institution's letterhead image, taken from the final-review template (written once to docs/figures)."""
    if os.path.exists(BANNER):
        return BANNER
    try:
        from pptx import Presentation

        os.makedirs(os.path.dirname(BANNER), exist_ok=True)
        prs = Presentation(r"D:\abstracts\Templates\Final_PPT.pptx")
        for sh in prs.slides[0].shapes:
            if sh.shape_type == 13:
                with open(BANNER, "wb") as f:
                    f.write(sh.image.blob)
                return BANNER
    except Exception:
        pass
    return None


def _banner_par(d, width=5.9):
    b = _banner()
    if b:
        par = d.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.line_spacing = 1.0
        par.add_run().add_picture(b, width=Inches(width))


def cover(d):
    _banner_par(d)
    d.spacer(2)
    d.p(F.FULL_TITLE.upper(), align="center", size=17, bold=True, space_after=6)
    d.p(f"{F.PRODUCT}: {F.SUBTITLE}", align="center", size=12, italic=True, space_after=8)
    d.p("A project report submitted in partial fulfilment of the requirements for the award of the degree of", align="center", size=12, space_after=6)
    d.p("BACHELOR OF TECHNOLOGY", align="center", size=15, bold=True, space_after=2)
    d.p("in", align="center", size=12, space_after=2)
    d.p("COMPUTER SCIENCE AND ENGINEERING", align="center", size=15, bold=True, space_after=6)
    d.p("Submitted by", align="center", size=12, bold=True, space_after=4)
    rows = [[n.upper(), r] for n, r in F.STUDENTS]
    t = d.doc.add_table(rows=len(rows), cols=2)
    t.alignment = 1
    for i, (n, r) in enumerate(rows):
        for j, v in enumerate((n, r)):
            c = t.rows[i].cells[j]
            c.text = ""
            par = c.paragraphs[0]
            par.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
            par.paragraph_format.line_spacing = 1.15
            par.paragraph_format.space_after = Pt(2)
            add_runs(par, v, 12, True)
            c.width = Inches(3.2 if j == 0 else 1.6)
    d.p(f"Batch {F.BATCH_NO} ({F.SECTION})", align="center", size=12, space_after=6)
    d.p("Under the esteemed guidance of", align="center", size=12, space_after=2)
    d.p(F.GUIDE.upper(), align="center", size=13, bold=True, space_after=0)
    d.p(F.GUIDE_DESIGNATION, align="center", size=12, space_after=8)
    d.p("DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING", align="center", size=13, bold=True, space_after=2)
    d.p(F.COLLEGE.upper(), align="center", size=12, bold=True, space_after=2)
    d.p(F.ADDRESS, align="center", size=11, space_after=2)
    d.p(f"Academic year {F.YEAR}", align="center", size=12, space_after=0)


def certificate(d):
    d.h1("CERTIFICATE", page_break=False)
    _banner_par(d, 5.2)
    d.p(f"This is to certify that the project report entitled **\"{F.FULL_TITLE}\"** is a bonafide record of the work carried out by "
        + ", ".join(f"**{n.upper()}** ({r})" for n, r in F.STUDENTS)
        + f", in partial fulfilment of the requirements for the award of the degree of Bachelor of Technology in Computer Science and Engineering, "
          f"during the academic year {F.YEAR}, under my supervision.")
    d.spacer(30)
    t = d.doc.add_table(rows=3, cols=3)
    cells = [("Project Guide", F.GUIDE, F.GUIDE_DESIGNATION), ("Head of the Department", F.HOD, F.DEPT), ("Principal", F.PRINCIPAL, F.COLLEGE_SHORT)]
    for j, (a, b, c) in enumerate(cells):
        for i, v in enumerate((a, b, c)):
            cell = t.rows[i].cells[j]
            cell.text = ""
            par = cell.paragraphs[0]
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            par.paragraph_format.line_spacing = 1.15
            add_runs(par, v, 11, i == 0)
    d.spacer(30)
    d.p("External Examiner: [NAME AND SIGNATURE]", align="left")
    d.p(f"Place: {F.PLACE}", align="left", space_after=0)
    d.p(f"Date: {F.DATE}", align="left")


def declaration(d):
    d.h1("DECLARATION")
    d.p(f"We hereby declare that the project report entitled **\"{F.FULL_TITLE}\"**, submitted to the {F.DEPT}, {F.COLLEGE_SHORT}, in partial fulfilment of the "
        f"requirements for the award of the degree of Bachelor of Technology in Computer Science and Engineering, is a record of original work carried out by us under the "
        f"guidance of {F.GUIDE}, {F.GUIDE_DESIGNATION}. The results embodied in this report have not been submitted to any other university or institution for the award of any degree or diploma.")
    d.spacer(24)
    for n, r in F.STUDENTS:
        d.p(f"{n.upper()}   {r}", align="right", space_after=2)
    d.spacer(18)
    d.p(f"Place: {F.PLACE}", align="left", space_after=0)
    d.p(f"Date: {F.DATE}", align="left")


def acknowledgement(d):
    d.h1("ACKNOWLEDGEMENT")
    d.p(f"We express our sincere gratitude to our project guide, {F.GUIDE}, {F.GUIDE_DESIGNATION}, for valuable guidance, encouragement and constructive suggestions "
        "throughout this project.")
    d.p(f"We thank {F.HOD}, Head of the {F.DEPT}, for providing the facilities and support needed to complete this work, and {F.PRINCIPAL}, Principal, {F.COLLEGE_SHORT}, "
        "for the encouragement given to us.")
    d.p("We thank the project coordinators and all faculty and staff members of the department for their help, and our families and friends for their constant support.")
    d.p("We also acknowledge the authors of the two papers on which this project rests: M. Jemmali, L. K. B. Melhim, A. Ammar, T. R. Gadekallu and W. Boulila, whose work on smart parking allocation is the registered base paper, "
        "and G. Cabri, M. Montangero, F. Muzzini and R. Wang, whose reservation buffer and reward system are implemented in the engine. "
        "We are grateful to the maintainers of the open-source software used here: FastAPI, SQLAlchemy, SQLite, APScheduler, React, Vite, Recharts, pytest, matplotlib and Playwright.")
    d.spacer(14)
    for n, r in F.STUDENTS:
        d.p(n.upper(), align="right", space_after=2)


def abstract(d):
    t = F.SEED["insights_60d"]["totals"]
    d.p("Drivers in dense urban areas lose time and add congestion searching for a free bay, and operators who run parking from manual registers and cash have no view of demand. "
        f"This project builds {F.PRODUCT}, a web-based Online Vehicle Parking Reservation System in which drivers register, search live availability for a time window, reserve a bay in advance, pay online, "
        "and check in and out, while administrators manage locations, users, bookings and payments. A Smart Availability Engine admits a request only if overlapping bookings plus a hold-back buffer stay below "
        "capacity, moves a driver who finds the lot full to the one nearest alternate by haversine distance (or credits the fee if none exists), and keeps a Trust Score from 0 to 5 that changes the fee and can suspend booking. "
        "The buffer and reputation ideas follow Cabri et al.; the registered base paper is the work of Jemmali et al. on passenger-aware allocation. "
        "The system has 22 REST routes, five database tables and a React console.")
    d.p(f"We measured it with its own tools. All {F.PYTEST_PASSED} automated tests pass, and a simulator of the base paper's 80-bay scenario agrees with the engine on {F.PAR['total_cases']:,} decisions. "
        f"Search takes {F.lat('GET /api/search'):.1f} ms and a reservation {F.lat('POST /api/reservations'):.1f} ms on average. In the simulator the buffer rule shipped in the code, which grows on on-time checkouts, "
        "refuses far more reservations than the base paper's rule, so the paper's claim for the dynamic buffer is not reproduced for it. "
        f"The probes also found an over-booking race (1 of 10 trials), an unauthenticated payment-confirmation route, and no vehicle profile or receipt. The data are the product's synthetic seed history, and no study with real drivers was done.")
    d.p("**Keywords:** online vehicle parking, parking reservation system, web application, slot booking, vehicle parking management, online payment, user authentication, admin dashboard, database management, smart parking.")


ABBR = [
    ("API", "Application Programming Interface"), ("ASAP", "Agent-assisted Smart Auction-based Parking"), ("CORS", "Cross-Origin Resource Sharing"),
    ("CRUD", "Create, Read, Update, Delete"), ("DFD", "Data Flow Diagram"), ("ER", "Entity-Relationship"),
    ("FR", "Functional Requirement"), ("GVb", "Grouping variant b of the base paper"), ("HTTP", "Hypertext Transfer Protocol"), ("IoT", "Internet of Things"),
    ("ITS", "Intelligent Transportation Systems"), ("JSON", "JavaScript Object Notation"), ("JWT", "JSON Web Token"), ("MR", "Baseline algorithm of the base paper"),
    ("NFR", "Non-Functional Requirement"), ("OJCS", "IEEE Open Journal of the Computer Society"), ("ORM", "Object-Relational Mapping"), ("QR", "Quick Response (code)"),
    ("REST", "Representational State Transfer"), ("SQL", "Structured Query Language"), ("SUMO", "Simulation of Urban Mobility"), ("UI", "User Interface"),
    ("UML", "Unified Modeling Language"), ("USD", "United States dollar"), ("UTC", "Coordinated Universal Time"), 
]


def abbreviations(d):
    """Two abbreviation/expansion pairs per row so the list takes half the space."""
    half = (len(ABBR) + 1) // 2
    rows = [list(ABBR[i]) + (list(ABBR[i + half]) if i + half < len(ABBR) else ["", ""]) for i in range(half)]
    d.table("Abbreviations used in this report", ["Abbreviation", "Expansion", "Abbreviation", "Expansion"], rows, widths=[0.95, 2.25, 0.95, 2.25], size=10)
