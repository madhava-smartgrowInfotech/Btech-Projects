"""Render the blocks of one content function into a stand-alone .docx so an author can check their module without building the report.

    python -m scripts.docs.try_blocks ch6 methodology_blocks "<out.docx>" [--pages]

--pages also opens the file in Word (COM, under ComLock) and prints the page and word counts.
"""
import importlib
import sys

from .blocks import render
from .kit import Doc


def main():
    mod, func, out = sys.argv[1], sys.argv[2], sys.argv[3]
    fn = getattr(importlib.import_module("scripts.docs." + mod), func)
    d = Doc("Try " + mod, header_text="try")
    d.footer_numbers()
    render(d, fn(), h1_page_break=True)
    d.save(out)
    print("wrote", out)
    if "--pages" in sys.argv:
        from .comlock import ComLock
        from .word_finalize import finalize
        with ComLock():
            print("pages, words:", finalize(out, None))


if __name__ == "__main__":
    main()
