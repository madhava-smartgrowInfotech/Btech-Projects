"""Cross-process lock so parallel builders never drive Word / PowerPoint COM at the same time."""
import contextlib
import os
import tempfile
import time

LOCK = os.path.join(tempfile.gettempdir(), "a5_office_com.lock")


@contextlib.contextmanager
def com_lock(timeout=900):
    t0 = time.time()
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            if time.time() - t0 > timeout:
                try:
                    os.remove(LOCK)  # stale lock from a crashed process
                except OSError:
                    pass
            time.sleep(2)
    try:
        yield
    finally:
        try:
            os.remove(LOCK)
        except OSError:
            pass
