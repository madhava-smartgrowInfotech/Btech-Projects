"""
Cross-process lock for Office COM automation (Word / PowerPoint), so parallel build jobs never drive Office at the same time.

    from .comlock import ComLock
    with ComLock():
        ...  # win32com work
"""

import os
import time

LOCK = os.path.join(os.environ.get("TEMP", "."), "lablens_office.lock")


class ComLock:
    def __init__(self, timeout=1800):
        self.timeout = timeout
        self.fd = None

    def __enter__(self):
        end = time.time() + self.timeout
        while True:
            try:
                self.fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                return self
            except FileExistsError:
                try:  # a stale lock older than 20 minutes is ignored
                    if time.time() - os.path.getmtime(LOCK) > 1200:
                        os.remove(LOCK)
                        continue
                except OSError:
                    pass
                if time.time() > end:
                    raise TimeoutError("Office lock busy")
                time.sleep(2)

    def __exit__(self, *a):
        try:
            os.close(self.fd)
            os.remove(LOCK)
        except OSError:
            pass
