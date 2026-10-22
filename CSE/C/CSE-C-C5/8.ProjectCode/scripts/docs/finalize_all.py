"""Updates fields / page numbers of the chapter documents and the report in Word and prints page counts (no process kills; ComLock + retries).

    python -m scripts.docs.finalize_all [--only 17 ...]
"""
import argparse
import os
import time

from . import facts as F
from .build_docs import NAMES
from .comlock import ComLock
from .word_finalize import finalize


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=int, nargs="*")
    a = ap.parse_args()
    for k, name in NAMES.items():
        if a.only and k not in a.only:
            continue
        path = os.path.join(F.BATCH, name)
        for attempt in range(4):
            try:
                with ComLock():
                    pages, words = finalize(path, None)
                print(f"{name}: {pages} pages, {words} words", flush=True)
                break
            except Exception as e:  # noqa: BLE001
                print("retry", name, str(e)[:90], flush=True)
                time.sleep(10)
        else:
            print("FAILED", name)


if __name__ == "__main__":
    main()
