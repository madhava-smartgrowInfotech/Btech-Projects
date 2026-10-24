"""Pure feature calculations, conservative quality gating, calibration and rules."""
from dataclasses import dataclass, asdict
from collections import deque
import math
import numpy as np

NORMAL = 'Normal'
WARNING = 'Possible impairment or drowsiness'
UNKNOWN = 'Unable to assess'

@dataclass
class Settings:
    ear_threshold: float = 0.21
    closure_seconds: float = 1.5
    persistence_seconds: float = 1.0
    closed_fraction: float = 0.55
    tilt_degrees: float = 25.0
    cooldown_seconds: float = 15.0
    calibrated: bool = False

    def validate(self):
        limits = {'ear_threshold': (.08, .4), 'closure_seconds': (.5, 5),
                  'persistence_seconds': (.5, 5), 'closed_fraction': (.3, .9),
                  'tilt_degrees': (10, 45), 'cooldown_seconds': (5, 120)}
        for key, (low, high) in limits.items():
            value = getattr(self, key)
            if not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f'{key} must be between {low} and {high}')
        if type(self.calibrated) is not bool:
            raise ValueError('calibrated must be boolean')
        return self

@dataclass
class Observation:
    t: float
    ear: float = 0.0
    roll: float = 0.0
    quality: str = 'No face'
    brightness: float = 0.0
    sharpness: float = 0.0

@dataclass
class Decision:
    state: str
    reason: str
    quality: str
    ear: float = 0.0
    closure: float = 0.0
    blink_rate: float = 0.0
    closed_fraction: float = 0.0
    roll: float = 0.0
    alert: bool = False


def eye_aspect_ratio(points):
    """Six perimeter points: (|p2-p6|+|p3-p5|)/(2|p1-p4|)."""
    p = np.asarray(points, dtype=float)
    if p.shape != (6, 2) or not np.isfinite(p).all():
        raise ValueError('EAR needs six finite 2D points')
    width = np.linalg.norm(p[0] - p[3])
    if width < 1e-6:
        raise ValueError('Degenerate eye width')
    return float((np.linalg.norm(p[1]-p[5])+np.linalg.norm(p[2]-p[4]))/(2*width))


def head_roll(left, right):
    delta = np.asarray(right, float) - np.asarray(left, float)
    if not np.isfinite(delta).all() or np.linalg.norm(delta) < 1e-6:
        raise ValueError('Invalid eye centers')
    return math.degrees(math.atan2(delta[1], abs(delta[0])))


class RiskEngine:
    def __init__(self, settings=None):
        self.settings = (settings or Settings()).validate()
        self.reset()

    def reset(self):
        self.samples = deque()
        self.ears = deque(maxlen=3)
        self.blinks = deque()
        self.closed_since = None
        self.risk_since = None
        self.last_t = None
        self.good_since = None
        self.last_alert = getattr(self, "last_alert", -math.inf)

    def update(self, o):
        gap = self.last_t is not None and not 0 < o.t-self.last_t <= .5
        if o.quality != 'Good' or gap or not all(math.isfinite(x) for x in (o.t, o.ear, o.roll)) or not 0 <= o.ear <= .65:
            self.reset()
            reason = o.quality if o.quality != 'Good' else 'Unstable timing or invalid measurement'
            return Decision(UNKNOWN, reason, reason)
        self.last_t = o.t
        if self.good_since is None:
            self.good_since = o.t
        self.ears.append(o.ear)
        ear = float(np.median(self.ears))
        closed = ear < self.settings.ear_threshold
        if closed and self.closed_since is None:
            self.closed_since = o.t
        if not closed and self.closed_since is not None:
            duration = o.t - self.closed_since
            if .08 <= duration <= .8:
                self.blinks.append(o.t)
            self.closed_since = None
        closure = 0 if self.closed_since is None else o.t-self.closed_since
        self.samples.append((o.t, closed))
        while self.samples and self.samples[0][0] < o.t-10:
            self.samples.popleft()
        while self.blinks and self.blinks[0] < o.t-60:
            self.blinks.popleft()
        span = o.t-self.samples[0][0]
        # Time-weighted closure fraction; do not overweight high-frame-rate periods.
        duration_closed = sum((b[0]-a[0])*a[1] for a,b in zip(self.samples, list(self.samples)[1:]))
        fraction = duration_closed/span if span else 0
        blink_rate = len(self.blinks)*60/min(60, max(o.t-self.good_since, .1))
        reasons = []
        if closure >= self.settings.closure_seconds:
            reasons.append(f'Continuous eye closure {closure:.1f} s')
        if span >= 8 and fraction >= self.settings.closed_fraction:
            reasons.append(f'Closed-eye fraction {fraction:.0%} over {span:.1f} s')
        if abs(o.roll) >= self.settings.tilt_degrees and closed:
            reasons.append(f'Head tilt {o.roll:.0f} degrees with low EAR')
        if reasons:
            if self.risk_since is None:
                self.risk_since = o.t
        else:
            self.risk_since = None
        state = UNKNOWN if span < 2 else NORMAL
        reason = 'Gathering 2 seconds of reliable observations' if span < 2 else 'No sustained warning observations'
        if reasons:
            reason = '; '.join(reasons) + ' (persistence pending)'
            if span >= 2 and o.t-self.risk_since >= self.settings.persistence_seconds:
                state, reason = WARNING, '; '.join(reasons)
        alert = state == WARNING and o.t-self.last_alert >= self.settings.cooldown_seconds
        if alert:
            self.last_alert = o.t
        return Decision(state, reason, 'Good', ear, closure, blink_rate, fraction, o.roll, alert)


class Calibration:
    def __init__(self, now):
        self.start = now
        self.values = []
        self.attempts = 0

    def add(self, o):
        self.attempts += 1
        if o.quality == 'Good' and .15 <= o.ear <= .5 and abs(o.roll) < 15:
            self.values.append(o.ear)
        elapsed = o.t-self.start
        if elapsed < 8:
            return None
        if len(self.values) >= 40 and len(self.values)/self.attempts >= .7:
            a = np.asarray(self.values)
            median = float(np.median(a))
            if float(np.std(a))/median <= .15:
                return float(np.clip(median*.72, .12, .32))
        if elapsed >= 15:
            raise ValueError('Calibration failed: keep eyes open, face forward and improve lighting. Existing threshold retained.')
        return None


def simulate(scenario, elapsed, now):
    quality = {'Missing face': 'No face', 'Poor lighting': 'Poor lighting'}.get(scenario, 'Good')
    ear = .30
    if scenario == 'Prolonged eye closure' and elapsed > 3:
        ear = .10
    elif scenario == 'Normal' and 2.0 < elapsed % 4 < 2.2:
        ear = .12
    return Observation(now, ear, 2*math.sin(elapsed), quality, 115 if quality != 'Poor lighting' else 15, 180)
