"""Draws the ParkSure design diagrams (matplotlib, 150 dpi) into docs/diagrams/.

    python -m scripts.docs.make_diagrams            # from 8.ProjectCode; all twelve
    python -m scripts.docs.make_diagrams arch dfd1  # selected keys

01-05 are in diagrams_a.py, 06-09 in diagrams_b.py, 10-12 in diagrams_c.py. Every box mirrors a real module, route, table or
function of the product (app/main.py, app/engine.py, app/models.py, app/auth.py, app/stripe_pay.py, frontend/src/pages).
"""

import sys

from . import diagrams_a, diagrams_b, diagrams_c


def drawers():
    d = {}
    for m in (diagrams_a, diagrams_b, diagrams_c):
        d.update(m.DRAWERS)
    return d


def main():
    all_ = drawers()
    keys = sys.argv[1:] or list(all_)
    for k in keys:
        all_[k]()


if __name__ == "__main__":
    main()
