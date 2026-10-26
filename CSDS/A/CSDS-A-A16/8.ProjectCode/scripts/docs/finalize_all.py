"""Updates fields / page numbers of the chapter documents and the report in Word and prints page counts.
Never kills WINWORD (other sessions use it): serialised through comlock, retried with a fresh DispatchEx instance.

    python -m scripts.docs.finalize_all [out_pdf_dir] [--only 17 14 ...]
"""

import os
import sys
import time

from . import facts as F
from .build_docs import NAMES
from .comlock import com_lock
from .word_finalize import finalize


def main():
    args = [a for a in sys.argv[1:]]
    only = None
    if "--only" in args:
        i = args.index("--only")
        only = [int(x) for x in args[i + 1:]]
        args = args[:i]
    out = args[0] if args else None
    if out:
        os.makedirs(out, exist_ok=True)
    for k, name in NAMES.items():
        if only and k not in only:
            continue
        path = os.path.join(F.BATCH, name)
        for attempt in range(4):
            try:
                with com_lock():
                    pdf = os.path.join(out, f"{k}.pdf") if out else None
                    pages, words = finalize(path, pdf)
                print(f"{name}: {pages} pages, {words} words", flush=True)
                break
            except Exception as e:  # noqa: BLE001
                print("retry", name, str(e)[:100], flush=True)
                time.sleep(10)
        else:
            print("FAILED", name)


if __name__ == "__main__":
    main()
