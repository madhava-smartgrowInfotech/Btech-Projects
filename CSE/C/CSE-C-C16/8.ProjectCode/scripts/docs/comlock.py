"""Cross-process lock so that parallel agents do not drive Word / PowerPoint COM at the same time.

    from scripts.docs.comlock import com_lock
    with com_lock():
        ... Word or PowerPoint COM session ...
"""
import contextlib
import os
import time

LOCK = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".com.lock")


@contextlib.contextmanager
def com_lock(timeout=900, poll=2.0):
    start = time.time()
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            # stale lock (older than 20 minutes) is removed
            try:
                if time.time() - os.path.getmtime(LOCK) > 1200:
                    os.remove(LOCK)
            except OSError:
                pass
            if time.time() - start > timeout:
                raise TimeoutError("COM lock busy")
            time.sleep(poll)
    try:
        yield
    finally:
        try:
            os.remove(LOCK)
        except OSError:
            pass
