"""Generate the ClauseGuard design diagrams (PNG, 150 dpi) into docs/diagrams/.

    python scripts/make_diagrams.py

Every diagram is drawn from the real design: the SQLAlchemy models in backend/app/db.py, the services in backend/app/services
and the routers in backend/app/routes.  Uses matplotlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diag_flow import dfd1, dfd2, flowchart  # noqa: E402
from diag_overview import architecture, dfd0, workflow  # noqa: E402
from diag_struct import er, sequence, uml, usecase  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "docs" / "diagrams"

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1:]
    jobs = [("01_system_architecture.png", architecture), ("02_high_level_workflow.png", workflow), ("03_dfd_level0.png", dfd0),
            ("04_dfd_level1.png", dfd1), ("05_dfd_level2.png", dfd2), ("06_er_diagram.png", er), ("07_uml_class_diagram.png", uml),
            ("08_use_case_diagram.png", usecase), ("09_sequence_diagram.png", sequence), ("10_algorithm_flowchart.png", flowchart)]
    for name, fn in jobs:
        if not only or name[:2] in only:
            fn(OUT / name)
    print("done")
