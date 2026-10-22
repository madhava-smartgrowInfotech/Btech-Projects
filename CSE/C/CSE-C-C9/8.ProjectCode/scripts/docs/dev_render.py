"""
Developer helper: render one content function to a temporary .docx and report its size.

    python -m scripts.docs.dev_render ch5 blocks            # run from 8.ProjectCode, system python
    python -m scripts.docs.dev_render ch9_10 novelty_blocks

Writes to the session scratchpad (never to the batch root). Raises on missing figures or screenshots,
prints the word count and the number of figures and tables, and lists any forbidden template words.
"""
import importlib
import os
import re
import sys
import tempfile

from .blocks import plain_text, render
from .kit import Doc

FORBIDDEN = ["pneumonia", "x-ray", "radiograph", "grad-cam", "kermany", "fakeddit", "pheme", "snopes", "mcnn", "social media manipulation", "bank transaction", "skincare"]


def main():
    mod, fn = sys.argv[1], sys.argv[2]
    m = importlib.import_module(f"scripts.docs.{mod}")
    blocks = getattr(m, fn)()
    text = plain_text(blocks)
    words = len(re.findall(r"\w+", text))
    figs = sum(1 for b in blocks if b[0] == "fig")
    tabs = sum(1 for b in blocks if b[0] == "tab")
    d = Doc("dev render")
    render(d, blocks)
    out = os.path.join(tempfile.gettempdir(), f"dev_{mod}_{fn}.docx")
    d.save(out)
    bad = sorted({w for w in FORBIDDEN if w in text.lower()})
    print(f"{mod}.{fn}: {words} words, {figs} figures, {tabs} tables -> {out}")
    if bad:
        print("FORBIDDEN WORDS PRESENT:", bad)


if __name__ == "__main__":
    main()
