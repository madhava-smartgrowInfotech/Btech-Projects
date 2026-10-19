import time
from collections import defaultdict, deque

# simple in-memory rate limiter
_requests: dict[str, deque] = defaultdict(deque)

def is_rate_limited(key: str, max_req: int = 20, window_sec: int = 60) -> bool:
    now = time.time()
    dq = _requests[key]
    # remove old
    while dq and dq[0] < now - window_sec:
        dq.popleft()
    if len(dq) >= max_req:
        return True
    dq.append(now)
    return False
