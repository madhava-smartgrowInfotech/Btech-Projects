"""Updates fields/page numbers of the chapter documents and the report in Word, one document at a time under ComLock.

    python -m scripts.docs.finalize_locked <out_pdf_dir> [doc numbers ...]
"""
import os
import sys
import time

from . import facts as F
from .build_docs import NAMES
from .comlock import ComLock
from .word_finalize import finalize


def main():
    out = sys.argv[1]
    only = {int(x) for x in sys.argv[2:]}
    os.makedirs(out, exist_ok=True)
    for k, name in NAMES.items():
        if only and k not in only:
            continue
        path = os.path.join(F.BATCH, name)
        for attempt in range(4):
            try:
                with ComLock():
                    pages, words = finalize(path, os.path.join(out, f"{k}.pdf"))
                print(f"{k}: {name}: {pages} pages, {words} words", flush=True)
                break
            except Exception as e:  # noqa: BLE001
                print("retry", k, str(e)[:90], flush=True)
                time.sleep(8)
        else:
            print("FAILED", name, flush=True)


if __name__ == "__main__":
    main()
