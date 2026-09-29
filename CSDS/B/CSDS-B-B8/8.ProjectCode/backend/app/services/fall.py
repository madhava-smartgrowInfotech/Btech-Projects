"""Fall detection: rapid drop to the floor, then inactivity inside a confirmation window.

States: normal -> possible_fall -> confirmed. Getting back up during the window cancels it.
"""
from collections import deque

import numpy as np

from .features import body_geometry


class FallDetector:
    def __init__(self, confirm_seconds=3.0, drop_ratio=0.35, drop_window=2.0, still_speed=0.35):
        self.confirm_seconds = confirm_seconds
        self.drop_ratio = drop_ratio
        self.drop_window = drop_window
        self.still_speed = still_speed
        self.reset()

    def reset(self):
        self.state = "normal"
        self.hist = deque()          # (t, centre_y, down, up) for frames with a person
        self.heights = deque()       # (t, upright body height px)
        self.impact_t = None
        self.after = []              # frames since impact: (t, centre_xy or None, down, up)
        self.up_since = None
        self.last_down = False

    def body_height(self, fallback):
        if self.heights:
            return float(np.median([h for _, h in self.heights]))
        return fallback

    def update(self, t, k, p_lying=0.0):
        """Feed one frame (k = keypoints [17,3] or None). Returns an event dict or None."""
        g = body_geometry(k) if k is not None else None
        centre = down = up = None
        if g is not None:
            centre, scale, angle, aspect, _, h = g
            down = angle > 50 or aspect < 0.45 or p_lying > 0.6
            up = angle < 30 and aspect > 0.6 and p_lying < 0.5
            if up:
                self.heights.append((t, h))
            while self.heights and t - self.heights[0][0] > 15:
                self.heights.popleft()
            self.hist.append((t, float(centre[1]), down, up, scale))
            self.last_down = down
        while self.hist and t - self.hist[0][0] > self.drop_window:
            self.hist.popleft()

        if self.state == "normal":
            if g is None or not down or len(self.hist) < 2:
                return None
            H = self.body_height(g[1])
            drop = centre[1] - min(y for _, y, *_ in self.hist)
            if drop / H > self.drop_ratio:
                self.state = "possible_fall"
                self.impact_t = t
                self.after = []
                self.up_since = None
                return {"type": "possible_fall", "t": t, "drop": round(drop / H, 2)}
            return None

        if self.state == "possible_fall":
            if g is None:  # person hidden (often behind furniture on the floor): keep last posture
                self.after.append((t, None, self.last_down, False))
            else:
                self.after.append((t, centre, down, up))
            if up:
                self.up_since = self.up_since or t
                if t - self.up_since >= 1.0:
                    self.state = "normal"
                    return {"type": "recovered", "t": t}
            else:
                self.up_since = None
            elapsed = t - self.impact_t
            if elapsed < self.confirm_seconds:
                return None
            recent = [a for a in self.after if t - a[0] <= self.confirm_seconds]
            down_frac = np.mean([a[2] for a in recent]) if recent else 0
            H = self.body_height(g[1] if g else 100.0)
            pts = [(a[0], a[1]) for a in recent if a[1] is not None]
            speed = 0.0
            if len(pts) >= 2:
                d = [np.linalg.norm(pts[i][1] - pts[i - 1][1]) for i in range(1, len(pts))]
                speed = sum(d) / H / max(pts[-1][0] - pts[0][0], 1e-3)
            if down_frac >= 0.6 and (speed < self.still_speed or elapsed >= 3 * self.confirm_seconds):
                self.state = "confirmed"
                return {"type": "fall", "t": t, "impact_t": self.impact_t,
                        "latency": elapsed, "speed": round(speed, 3)}
            if down_frac < 0.3:
                self.state = "normal"
                return {"type": "recovered", "t": t}
            return None

        # confirmed: wait until the person is clearly upright again before re-arming
        if up:
            self.up_since = self.up_since or t
            if t - self.up_since >= 5.0:
                self.state = "normal"
                self.up_since = None
        else:
            self.up_since = None
        return None
