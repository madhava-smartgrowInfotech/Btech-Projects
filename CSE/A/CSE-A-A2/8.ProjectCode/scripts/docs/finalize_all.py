"""Updates fields / page numbers of the chapter documents and the report in Word and prints page counts.

    python -m scripts.docs.finalize_all [out_pdf_dir] [--only 17 9 ...]

Uses a fresh Word instance per document (DispatchEx) under the cross-process COM lock; never kills other Word processes.
"""

import argparse
import os
import time

from . import facts as F
from .build_docs import NAMES
from .comlock import com_lock
from .word_finalize import finalize


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?")
    ap.add_argument("--only", type=int, nargs="*")
    a = ap.parse_args()
    for k, name in NAMES.items():
        if a.only and k not in a.only:
            continue
        path = os.path.join(F.BATCH, name)
        for attempt in range(4):
            try:
                with com_lock():
                    pdf = os.path.join(a.out, f"{k}.pdf") if a.out else None
                    pages, words = finalize(path, pdf)
                print(f"{name}: {pages} pages, {words} words", flush=True)
                break
            except Exception as e:  # noqa: BLE001
                print("retry", name, str(e)[:80], flush=True)
                time.sleep(10)
        else:
            print("FAILED", name)


if __name__ == "__main__":
    main()
