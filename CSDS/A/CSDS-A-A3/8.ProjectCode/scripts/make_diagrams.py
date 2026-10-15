"""Generate the PhishGuard design diagrams (PNG, 150 dpi) into docs/diagrams/.

    python scripts/make_diagrams.py

Each diagram is drawn from the real design: phishguard/ (features, detector, threat_intel, train, retrain, webapp),
backend/server.py and the SQLite schema in threat_intel.py. Uses matplotlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagrams_a import architecture, dfd0, dfd1, dfd2, workflow  # noqa: E402
from diagrams_b import er, flowchart, sequence, uml, usecase  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "docs" / "diagrams"

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for fn, name in [(architecture, "01_system_architecture"), (workflow, "02_high_level_workflow"), (dfd0, "03_dfd_level0"),
                     (dfd1, "04_dfd_level1"), (dfd2, "05_dfd_level2"), (er, "06_er_diagram"), (uml, "07_uml_class_diagram"),
                     (usecase, "08_use_case_diagram"), (sequence, "09_sequence_diagram"), (flowchart, "10_algorithm_flowchart")]:
        fn(OUT / f"{name}.png")
        print("saved", name)
