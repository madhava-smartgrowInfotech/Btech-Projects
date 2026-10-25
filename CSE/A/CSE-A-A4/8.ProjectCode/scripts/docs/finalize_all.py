"""Updates fields / page numbers of the chapter documents and the report in Word and prints page counts.

    python -m scripts.docs.finalize_all [out_pdf_dir]
"""

import os
import subprocess
import sys
import time

from . import facts as F
from .build_docs import NAMES
from .comlock import com_lock
from .word_finalize import finalize


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else None
    for k, name in NAMES.items():
        path = os.path.join(F.BATCH, name)
        for attempt in range(3):
            time.sleep(3)
            try:
                pdf = os.path.join(out, f"{k}.pdf") if out else None
                with com_lock():
                    pages, words = finalize(path, pdf)
                print(f"{name}: {pages} pages, {words} words", flush=True)
                break
            except Exception as e:  # noqa: BLE001
                print("retry", name, str(e)[:80], flush=True)
        else:
            print("FAILED", name)


if __name__ == "__main__":
    main()
