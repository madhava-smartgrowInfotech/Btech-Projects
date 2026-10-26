"""Generate the SHEGUARD design diagrams (PNG, 150 dpi) into docs/diagrams/.

    python scripts/make_diagrams.py

Every diagram is drawn from the real design: the SQLAlchemy models in backend/app/models.py, the routers in backend/app/routes,
the services in backend/app/services and the React app in frontend/src.  Uses matplotlib only.
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
    architecture(OUT / "01_system_architecture.png")
    workflow(OUT / "02_high_level_workflow.png")
    dfd0(OUT / "03_dfd_level0.png")
    dfd1(OUT / "04_dfd_level1.png")
    dfd2(OUT / "05_dfd_level2.png")
    er(OUT / "06_er_diagram.png")
    uml(OUT / "07_uml_class_diagram.png")
    usecase(OUT / "08_use_case_diagram.png")
    sequence(OUT / "09_sequence_diagram.png")
    flowchart(OUT / "10_algorithm_flowchart.png")
    print("done")
