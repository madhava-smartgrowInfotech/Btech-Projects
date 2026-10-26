"""Updates fields / page numbers of the chapter documents and the report in Word and prints page counts.
Each document runs in its own process with a timeout (a hung Word instance is killed and the document retried).

    python -m scripts.docs.finalize_all [out_pdf_dir] [--only 12 17]
"""

import os
import subprocess
import sys
import time

from . import facts as F
from .build_docs import NAMES


def main():
    args = [a for a in sys.argv[1:]]
    only = None
    if "--only" in args:
        i = args.index("--only")
        only = {int(x) for x in args[i + 1:]}
        args = args[:i]
    out = args[0] if args else None
    for k, name in NAMES.items():
        if only and k not in only:
            continue
        path = os.path.join(F.BATCH, name)
        for attempt in range(3):
            time.sleep(3)
            cmd = [sys.executable, "-m", "scripts.docs.word_finalize", path]
            if out:
                cmd += ["--pdf", os.path.join(out, f"{k}.pdf")]
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=900, cwd=F.CODE)
                if r.returncode == 0:
                    print(r.stdout.strip(), flush=True)
                    break
                print("retry", name, (r.stderr or "")[-120:].strip(), flush=True)
            except subprocess.TimeoutExpired:
                print("timeout, retry", name, flush=True)
        else:
            print("FAILED", name, flush=True)


if __name__ == "__main__":
    main()
