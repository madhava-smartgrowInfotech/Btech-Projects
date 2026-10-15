"""Generate the SeatWise design diagrams (PNG, 150 dpi) into docs/diagrams/.

    venv\\Scripts\\python scripts\\make_diagrams.py

Every diagram is drawn from the real design: the SQLAlchemy models in backend/app/models, the engine in
backend/app/services/engine and the routers in backend/app/api. Uses matplotlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagrams_overview import architecture as _arch, workflow as _wf  # noqa: E402
from diagrams_dfd0 import dfd0 as _dfd0  # noqa: E402
from diagrams_struct import er as _er, uml as _uml  # noqa: E402
from diagrams_behaviour import usecase as _uc, sequence as _seq  # noqa: E402
from diagrams_flowchart import flowchart as _fc  # noqa: E402
from diagrams_flow import dfd1 as _dfd1, dfd2 as _dfd2  # noqa: E402
from diagram_kit import (AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, INK, ROSE_L, Canvas, anchor)  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "docs" / "diagrams"






if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    _dfd1(OUT / "04_dfd_level1.png")
    _dfd2(OUT / "05_dfd_level2.png")
    _arch(OUT / "01_system_architecture.png")
    _wf(OUT / "02_high_level_workflow.png")
    _dfd0(OUT / "03_dfd_level0.png")
    _er(OUT / "06_er_diagram.png")
    _uml(OUT / "07_uml_class_diagram.png")
    _uc(OUT / "08_use_case_diagram.png")
    _seq(OUT / "09_sequence_diagram.png")
    _fc(OUT / "10_algorithm_flowchart.png")
    print("done")
