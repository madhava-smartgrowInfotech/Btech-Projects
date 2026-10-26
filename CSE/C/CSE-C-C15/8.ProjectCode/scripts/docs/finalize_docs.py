"""Update fields and page numbers of the chapter documents and the report in Word (one at a time, under the COM lock)."""
import os
import sys
import time

from . import facts as F
from .build_docs import NAMES
from .comlock import com_lock
from .word_finalize import finalize


def main():
    only = [int(x) for x in sys.argv[1:]]
    out = os.path.join(F.DOCS, "pdf")
    os.makedirs(out, exist_ok=True)
    for k, name in NAMES.items():
        if only and k not in only:
            continue
        path = os.path.join(F.BATCH, name)
        for attempt in range(4):
            try:
                with com_lock():
                    pages, words = finalize(path, os.path.join(out, f"{k}.pdf"))
                print(f"{name}: {pages} pages, {words} words", flush=True)
                break
            except Exception as e:  # noqa: BLE001
                print("retry", name, str(e)[:100], flush=True)
                time.sleep(10)
        else:
            print("FAILED", name)


if __name__ == "__main__":
    main()
