"""Shared facts for the submission documents. Every figure here comes from docs/REPORT_FACTS.md."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT.parent
DIAG = ROOT / "docs" / "diagrams"
SHOTS = ROOT / "docs" / "screenshots"
EXP = ROOT / "experiments" / "engine-benchmark-20260921"
CHARTS = ROOT / "docs" / "charts"

PRODUCT = "SeatWise"
TITLE = "AI-Enabled Digital Examination Seating Management System"
DEPT = "Department of Computer Science and Engineering (Data Science)"
BATCH_NAME = "Batch A13 (CSE - Data Science, Section A)"
COLLEGE = "[COLLEGE NAME]"
YEAR = "[ACADEMIC YEAR]"
GUIDE = "[GUIDE NAME]"
GUIDE_DESIG = "[DESIGNATION]"

STUDENTS = [
    ("A.SANJAY", "23K91A6702"),
    ("CH.NAVEEN", "23K91A6743"),
    ("D.KOTESH", "24K95A6705"),
    ("A.AKSHITH", "[Roll number to be confirmed]"),
]

BASE_PAPER = ('P. Yukth, I. S. Mahmood, K. H. Shashank, S. G. Thejus and M. S. Darshini, "Exam Seating Arrangement System," '
              'International Journal of Research Publication and Reviews (IJRPR), vol. 6, no. 12, pp. 2093-2105, Dec. 2025.')

REFERENCES = [
    BASE_PAPER,
    '"Automated examination seating arrangement and hall allocation system," International Journal of AI, Electrical, Civil and Mechanical Engineering, 2026.',
    '"An intelligent machine learning-based system for automated examination hall seating arrangement in universities," in Proc. 2026 Int. Conf. AI-Driven Solutions for Sustainable Smart Cities: Challenges and Opportunities (ADSSSC), 2026.',
    'S. O. Adetona and F. A. Akintoye, "Design and implementation of an examination seating arrangement application to curb examination malpractice," ABUAD Journal of Engineering Research and Development (AJERD), vol. 6, no. 2, pp. 143-156, Dec. 2023.',
    '"Automated seating arrangement for conducting examination," in Proc. 2025 Int. Conf. Multi-Agent Systems for Collaborative Intelligence (ICMSCI), 2025.',
    'Kashyap et al., "Exam seating allocation to prevent malpractice using genetic multi-optimization algorithm," Springer, 2021, doi: 10.1007/978-981-16-0419-5_11.',
    'K. Jitha and A. Fathima, "Web application based exam hall seating management system," in Proc. IEEE Int. Conf. Applied Artificial Intelligence and Computing (ICAAIC), 2022 (as described in [1]).',
    'M. Patel, "Smart seating system for universities," in Proc. IEEE Int. Conf. Computing, Communication and Automation, 2021 (as described in [1]).',
    '"Automated students examination seat allocation using linear congruential generator," International Journal of Computer Trends and Technology (IJCTT), 2021 (as described in [1]).',
    '"AI powered automated exam hall allocation and management system," International Journal of Science and Research (IJSART), 2025 (as described in [1]).',
    'D. J. A. Welsh and M. B. Powell, "An upper bound for the chromatic number of a graph and its application to timetabling problems," The Computer Journal, vol. 10, no. 1, pp. 85-86, 1967.',
    'R. Qu, E. K. Burke, B. McCollum, L. T. G. Merlot and S. Y. Lee, "A survey of search methodologies and automated system development for examination timetabling," Journal of Scheduling, vol. 12, no. 1, pp. 55-89, 2009.',
    'F. Rossi, P. van Beek and T. Walsh, Eds., Handbook of Constraint Programming. Amsterdam, The Netherlands: Elsevier, 2006.',
    'L. Perron and V. Furnon, "OR-Tools," Google. [Online]. Available: https://developers.google.com/optimization',
    'M. Jones, J. Bradley and N. Sakimura, "JSON Web Token (JWT)," RFC 7519, Internet Engineering Task Force, May 2015.',
    'N. Provos and D. Mazieres, "A future-adaptable password scheme," in Proc. USENIX Annual Technical Conference, 1999.',
    'S. Ramirez, "FastAPI documentation." [Online]. Available: https://fastapi.tiangolo.com',
    'M. Bayer, "SQLAlchemy," in The Architecture of Open Source Applications, vol. 2, A. Brown and G. Wilson, Eds., 2012.',
    'Meta Platforms, "React documentation." [Online]. Available: https://react.dev',
]

# ---------------------------------------------------------------- measured facts (docs/REPORT_FACTS.md)
BENCH_RUN = "engine-benchmark-20260921"
HEAD = dict(plans_ok="24 of 24", same_paper=0, seq_600=1253, solve_600=2.36, solve_2000=4.77, max_solve=6.14,
            corr=0.065, overlap="1.0%", tests=58)
SCEN = [  # name, candidates, papers, depts, halls, seats, adj, gap
    ("xs-150", 150, 4, 3, 3, 212, 8, 5), ("s-300", 300, 6, 4, 6, 398, 8, 5), ("m-600", 600, 8, 6, 12, 752, 8, 5),
    ("l-1000", 1000, 10, 7, 19, 1359, 8, 5), ("xl-2000", 2000, 14, 8, 39, 2522, 8, 5),
    ("m-600-adj4", 600, 8, 6, 12, 752, 4, 5), ("m-600-gap0", 600, 8, 6, 12, 752, 8, 0), ("m-600-gap10", 600, 8, 6, 12, 752, 8, 10)]
# scenario -> method -> (solve_s, same_paper, roll_gap, accessible_missed, same_dept, halls, filled%)
BENCH = {
    "xs-150": {"SeatWise": (1.25, 0, 0, 0, 23, 3, 71), "Sequential": (0.00, 307, 122, 3, 405, 3, 71), "Round-robin": (0.00, 41, 44, 3, 93, 3, 71), "Random shuffle": (0.00, 116, 21, 3, 164, 3, 71)},
    "s-300": {"SeatWise": (2.03, 0, 0, 0, 7, 5, 82), "Sequential": (0.00, 648, 231, 3, 803, 5, 100), "Round-robin": (0.00, 63, 56, 3, 111, 5, 100), "Random shuffle": (0.00, 171, 21, 3, 221, 5, 100)},
    "m-600": {"SeatWise": (2.36, 0, 0, 0, 109, 9, 96), "Sequential": (0.00, 1253, 453, 6, 1648, 10, 97), "Round-robin": (0.00, 281, 198, 7, 324, 10, 97), "Random shuffle": (0.00, 265, 23, 7, 366, 10, 97)},
    "l-1000": {"SeatWise": (2.55, 0, 0, 0, 190, 12, 96), "Sequential": (0.00, 1954, 755, 11, 2801, 14, 97), "Round-robin": (0.00, 607, 408, 12, 687, 14, 97), "Random shuffle": (0.00, 376, 21, 12, 617, 14, 97)},
    "xl-2000": {"SeatWise": (4.77, 0, 0, 0, 597, 28, 97), "Sequential": (0.00, 3299, 1528, 16, 5768, 29, 99), "Round-robin": (0.00, 511, 351, 16, 932, 29, 99), "Random shuffle": (0.00, 490, 18, 16, 1008, 29, 99)},
    "m-600-adj4": {"SeatWise": (6.02, 0, 0, 0, 12, 9, 96), "Sequential": (0.00, 704, 453, 6, 924, 10, 97), "Round-robin": (0.00, 216, 166, 7, 233, 10, 97), "Random shuffle": (0.00, 145, 12, 7, 205, 10, 97)},
    "m-600-gap0": {"SeatWise": (2.31, 0, 0, 0, 108, 9, 96), "Sequential": (0.00, 1253, 0, 6, 1648, 10, 97), "Round-robin": (0.00, 281, 0, 7, 324, 10, 97), "Random shuffle": (0.00, 265, 0, 7, 366, 10, 97)},
    "m-600-gap10": {"SeatWise": (2.42, 0, 0, 0, 104, 9, 96), "Sequential": (0.00, 1253, 921, 6, 1648, 10, 97), "Round-robin": (0.00, 281, 252, 7, 324, 10, 97), "Random shuffle": (0.00, 265, 48, 7, 366, 10, 97)},
}
METHODS = ["SeatWise", "Sequential", "Round-robin", "Random shuffle"]
UNPRED = [("SeatWise", 0.065, "1.0%", 4.7), ("Sequential", 1.000, "100%", 12.4), ("Round-robin", 0.213, "100%", 3.4), ("Random shuffle", 0.034, "1.0%", 1.6)]
TUNING = [(0.10, 127.25, 3.72), (0.15, 123.25, 2.63), (0.25, 119.25, 3.56), (0.40, 116.0, 5.01), (0.60, 114.0, 6.58)]
DEMO = [("Mon 12 Oct 2026 Morning", 451, 6, 1099, 2.1), ("Mon 12 Oct 2026 Afternoon", 457, 7, 1175, 1.8), ("Tue 13 Oct 2026 Morning", 451, 7, 1105, 2.2)]
LATENCY = [("GET /health", 1.9, 2.6), ("GET /data/summary", 4.0, 4.6), ("GET /plans/1", 4.1, 4.7), ("GET seat map (hall)", 7.2, 10.8),
           ("GET swap-check (one seat)", 8.0, 11.4), ("GET /candidates?q=ACF", 9.3, 12.9), ("GET /sessions", 10.7, 12.1),
           ("GET public lookup", 2.8, 3.2), ("GET seating-charts.pdf", 96.0, 96.0), ("GET hall-lists.xlsx", 314.0, 354.0),
           ("GET qr-slips.pdf", 3208.0, 3236.0), ("POST verify plan", 2178.0, 2191.0)]
TESTS = [("test_auth.py", 8), ("test_engine.py", 14), ("test_imports.py", 9), ("test_plans.py", 6), ("test_exports.py", 7),
         ("test_attendance.py", 5), ("test_public.py", 5), ("test_analytics.py", 4)]
