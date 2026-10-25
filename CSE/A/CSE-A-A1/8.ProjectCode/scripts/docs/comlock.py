"""Cross-process lock for Word / PowerPoint COM automation (several agents share this PC).

    from .comlock import ComLock
    with ComLock():
        ...  # any win32com Word/PowerPoint work
"""
import os
import tempfile
import time

LOCK = os.path.join(tempfile.gettempdir(), "scps_office_com.lock")


class ComLock:
    def __init__(self, timeout=900):
        self.timeout = timeout
        self.fd = None

    def __enter__(self):
        t0 = time.time()
        while True:
            try:
                self.fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.write(self.fd, str(os.getpid()).encode())
                return self
            except FileExistsError:
                try:  # stale lock (older than 20 min)
                    if time.time() - os.path.getmtime(LOCK) > 1200:
                        os.remove(LOCK)
                        continue
                except OSError:
                    pass
                if time.time() - t0 > self.timeout:
                    raise TimeoutError("could not get the Office COM lock")
                time.sleep(3)

    def __exit__(self, *a):
        try:
            os.close(self.fd)
            os.remove(LOCK)
        except OSError:
            pass
