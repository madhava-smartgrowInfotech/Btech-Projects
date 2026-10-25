"""Update fields in the seven built documents with Word, report page counts and export PDFs.

    python -m scripts.docs.finalize_all [--pdfdir <dir>] [--only 17 9 ...]
"""

import argparse
import os
import time

from . import facts as F
from .build_docs import NAMES
from .word_finalize import finalize


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdfdir")
    ap.add_argument("--only", type=int, nargs="*")
    a = ap.parse_args()
    for k, name in NAMES.items():
        if a.only and k not in a.only:
            continue
        path = os.path.join(F.BATCH, name)
        pdf = os.path.join(a.pdfdir, os.path.splitext(name)[0] + ".pdf") if a.pdfdir else None
        for attempt in range(3):
            try:
                pages, words = finalize(path, pdf)
                print(f"{name}: {pages} pages, {words} words")
                break
            except Exception as e:  # Word COM is flaky right after another run
                print("retry", name, type(e).__name__, str(e)[:100])
                time.sleep(8)
        time.sleep(2)


if __name__ == "__main__":
    main()
