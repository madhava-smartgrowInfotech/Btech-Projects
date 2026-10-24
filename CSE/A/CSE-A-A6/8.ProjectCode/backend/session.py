"""One browser tab = one rider session. Mirrors Application.consume()/tick() from app.py.

The decision logic is NOT reimplemented here: observations come from vision.Vision / core.simulate and are
judged by core.RiskEngine, exactly as in the desktop app. This module only holds the session state that the
Tk widgets used to hold (source, monitoring flag, calibration, status text) and writes events through storage.Store.
"""
from dataclasses import asdict
import math
import threading
import time
import uuid

import cv2
import numpy as np

from core import (Calibration, Decision, NORMAL, Observation, RiskEngine, Settings, UNKNOWN, WARNING, simulate)
from storage import Store

SCENARIOS = ['Normal', 'Prolonged eye closure', 'Missing face', 'Poor lighting']
FRAME_SIZE = (640, 480)


class SessionError(Exception):
    """A user-facing failure; `status` is the HTTP status the API should answer with."""

    def __init__(self, message, status=409):
        super().__init__(message)
        self.status = status


class RiderSession:
    def __init__(self, data_dir):
        self.id = uuid.uuid4().hex[:12]
        self.data_dir = data_dir
        self.lock = threading.RLock()
        self.created = self.touched = time.monotonic()
        self.settings, self.note = self._store_call(lambda s: s.load_settings())
        self.engine = RiskEngine(self.settings)
        self.vision = None
        self.source = 'none'              # none | camera | simulation
        self.scenario = SCENARIOS[0]
        self.monitoring = False
        self.calibration = None
        self.sim_start = 0.0
        self.last_sample = 0.0
        self.last_log = 0.0
        self.last_key = None
        self.alert_seq = 0
        self.progress = 0.0
        self.status = self.note
        self.quality = 'No source'
        self.brightness = 0.0
        self.state = UNKNOWN
        self.reason = 'Start camera or select Simulation Mode.'
        self.alert = 'Monitoring stopped'
        self.metrics = None
        self.frames = 0

    # ---- storage (a fresh sqlite connection per call: connections are thread-bound) ----
    def _store_call(self, fn):
        store = Store(self.data_dir)
        try:
            return fn(store)
        finally:
            store.close()

    def source_name(self):
        return 'SIMULATION: ' + self.scenario if self.source == 'simulation' else 'LIVE CAMERA'

    def reset_engine(self):
        self.engine = RiskEngine(self.settings)
        self.last_key = None

    # ---- source control (Start/Stop Camera, Simulation Mode) ----
    def set_source(self, source, scenario=None):
        with self.lock:
            self.touched = time.monotonic()
            if scenario is not None:
                if scenario not in SCENARIOS:
                    raise SessionError('Unknown scenario.', 422)
            if source == 'camera':
                self._start_camera()
            elif source == 'simulation':
                if scenario is not None:
                    self.scenario = scenario
                self._start_simulation()
            elif source == 'none':
                self._stop_camera()
            else:
                raise SessionError('Unknown source.', 422)
            return self.snapshot()

    def _start_camera(self):
        if self.source == 'camera' and self.vision is not None:
            self.status = 'Camera is already active.'
            return
        self.stop_monitoring()
        self.calibration = None
        self._close_vision()
        try:
            from vision import Vision
            self.vision = Vision()
        except FileNotFoundError as exc:
            raise SessionError(f'{exc}', 503)
        except Exception as exc:  # mediapipe import / model load failure
            raise SessionError(f'Landmark model could not start: {exc}', 503)
        self.source = 'camera'
        self.reset_engine()
        self.last_sample = time.monotonic()
        self.quality = 'Waiting for first frame'
        self.metrics = None
        self.status = 'Opening webcam and landmark model...'

    def _stop_camera(self):
        self.stop_monitoring()
        self.calibration = None
        self._close_vision()
        self.source = 'none'
        self.quality, self.brightness, self.metrics, self.progress = 'No source', 0.0, None, 0.0
        self.status = 'Camera stopped. No video or face images are saved.'

    def _start_simulation(self):
        self.stop_monitoring()
        self.calibration = None
        self._close_vision()
        self.source = 'simulation'
        self.sim_start = time.monotonic()
        self.reset_engine()
        self.quality, self.metrics = 'Simulation', None
        self.status = 'Simulation ready. Select Start Monitoring to record labeled demonstration events.'

    def _close_vision(self):
        if self.vision is not None:
            try:
                self.vision.close()
            finally:
                self.vision = None

    # ---- monitoring / calibration ----
    def set_monitoring(self, active):
        with self.lock:
            self.touched = time.monotonic()
            if active:
                if self.calibration:
                    raise SessionError('Finish calibration before monitoring.')
                if self.source == 'none':
                    raise SessionError('Start a camera or Simulation Mode first.')
                self.monitoring = True
                self.reset_engine()
                self.sim_start = time.monotonic()
                self.alert = 'Monitoring active'
                self.status = 'Monitoring with explainable rules. No trained research model is used.'
            else:
                self.stop_monitoring()
            return self.snapshot()

    def stop_monitoring(self):
        if self.monitoring:
            self._store_call(lambda s: s.add(self.source_name(), Decision(UNKNOWN, 'Monitoring stopped', 'Not assessed')))
        self.monitoring = False
        self.reset_engine()
        self.state = UNKNOWN
        self.reason = 'Monitoring stopped'
        self.alert = 'Monitoring stopped'

    def set_calibration(self, active):
        with self.lock:
            self.touched = time.monotonic()
            if not active:
                self.calibration = None
                self.progress = 0.0
                self.status = 'Calibration cancelled; previous threshold retained.'
                return self.snapshot()
            if self.source == 'simulation':
                raise SessionError('Calibration uses real rider measurements only. Start Camera first.')
            if self.source != 'camera' or self.vision is None:
                raise SessionError('Start Camera before calibration.')
            self.stop_monitoring()
            self.calibration = Calibration(time.monotonic())
            self.progress = 0.0
            self.status = 'Calibration: remain stationary, look forward with eyes naturally open for 8-15 seconds.'
            return self.snapshot()

    def apply_settings(self, settings):
        """Called after Thresholds are saved: stop monitoring, drop calibration, adopt the new values."""
        with self.lock:
            self.stop_monitoring()
            self.calibration = None
            self.settings = settings
            self.reset_engine()
            self.status = 'Thresholds saved. Monitoring stopped; restart to use the new settings.'

    # ---- observations ----
    def frame(self, data):
        """A JPEG from the browser camera -> Vision.process -> consume(). Returns the annotated preview JPEG."""
        with self.lock:
            self.touched = time.monotonic()
            if self.source != 'camera' or self.vision is None:
                raise SessionError('Camera is not started. Press Start camera first.')
            image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            if image is None:
                raise SessionError('The frame could not be decoded as an image.', 422)
            image = cv2.resize(image, FRAME_SIZE)
            now = time.monotonic()
            observation = self.vision.process(image, now)
            self.frames += 1
            self.consume(observation)
            ok, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 72])
            return buffer.tobytes() if ok else b''

    def tick(self):
        with self.lock:
            self.touched = time.monotonic()
            if self.source == 'simulation':
                now = time.monotonic()
                self.consume(simulate(self.scenario, now - self.sim_start, now))
            return self.snapshot()

    def consume(self, o):
        self.last_sample = time.monotonic()
        self.brightness = o.brightness
        self.quality = o.quality
        if self.source == 'camera' and self.status == 'Opening webcam and landmark model...':
            self.status = 'Camera ready. Calibrate while stationary, then Start Monitoring.'
        if self.calibration:
            self.progress = min(100.0, (o.t - self.calibration.start) / 8 * 100)
            try:
                threshold = self.calibration.add(o)
                self.status = (f'Calibration: {len(self.calibration.values)} usable / '
                               f'{self.calibration.attempts} frames. Keep eyes open.')
                if threshold is not None:
                    candidate = Settings(**{**asdict(self.settings), 'ear_threshold': threshold, 'calibrated': True})
                    self._store_call(lambda s: s.save_settings(candidate))
                    self.settings, self.calibration = candidate, None
                    self.reset_engine()
                    self.status = f'Calibration saved: EAR threshold {threshold:.3f}. Start Monitoring when ready.'
            except (ValueError, OSError) as exc:
                self.calibration = None
                self.status = str(exc)
        if self.calibration and o.t - self.calibration.start > 16:
            self.calibration = None
            self.status = 'Calibration timed out; previous threshold retained.'
        if self.monitoring:
            d = self.engine.update(o)
            self._display(d)
            key = (d.state, d.quality)
            if key != self.last_key or o.t - self.last_log >= 5 or d.alert:
                self._store_call(lambda s: s.add(self.source_name(), d))
                self.last_key, self.last_log = key, o.t
        else:
            self.metrics = {'ear': o.ear, 'closure': None, 'blink_rate': None, 'closed_fraction': None, 'roll': o.roll}

    def _display(self, d):
        self.state, self.reason = d.state, d.reason
        self.metrics = {'ear': d.ear, 'closure': d.closure, 'blink_rate': d.blink_rate,
                        'closed_fraction': d.closed_fraction, 'roll': d.roll}
        prefix = 'SIMULATION: ' if self.source == 'simulation' else ''
        if d.state == WARNING:
            self.alert = prefix + 'Warning: stop somewhere safe.\nPossible impairment or drowsiness.'
        elif d.state == UNKNOWN:
            self.alert = 'Assessment unavailable: check signal.'
        else:
            self.alert = 'No sustained warning. This does not certify safety.'
        if d.alert:
            self.alert_seq += 1

    def _watchdog(self):
        """No frame for >1 s while the camera is active -> Unable to assess (as the Tk tick did)."""
        if self.source == 'camera' and self.vision is not None and time.monotonic() - self.last_sample > 1:
            self.consume(Observation(time.monotonic(), quality='Camera stalled or warming up'))
            self.last_sample = time.monotonic() - 0.5

    # ---- view ----
    def snapshot(self):
        with self.lock:
            self._watchdog()
            if self.source == 'simulation':
                source_label = 'SOURCE: SIMULATION | Scripted behavior, not model validation'
            elif self.source == 'camera':
                source_label = 'SOURCE: LIVE CAMERA | Rule-based baseline'
            else:
                source_label = 'SOURCE: NONE | Rule-based baseline'
            calibration = None
            if self.calibration:
                calibration = {'progress': round(self.progress, 1), 'usable': len(self.calibration.values),
                               'attempts': self.calibration.attempts,
                               'elapsed': round(time.monotonic() - self.calibration.start, 1)}
            metrics = None
            if self.metrics:
                metrics = {k: (None if v is None or not math.isfinite(v) else round(float(v), 4))
                           for k, v in self.metrics.items()}
            return {
                'session_id': self.id, 'source': self.source, 'source_label': source_label,
                'scenario': self.scenario, 'monitoring': self.monitoring, 'calibrating': self.calibration is not None,
                'calibration': calibration, 'status': self.status, 'quality': self.quality,
                'brightness': round(self.brightness, 1), 'state': self.state, 'reason': self.reason,
                'alert': self.alert, 'alert_seq': self.alert_seq, 'metrics': metrics,
                'threshold': self.settings.ear_threshold, 'calibrated': self.settings.calibrated,
                'frames': self.frames, 'verdicts': {'normal': NORMAL, 'warning': WARNING, 'unknown': UNKNOWN},
            }

    def close(self):
        with self.lock:
            try:
                if self.monitoring:
                    self.stop_monitoring()
            finally:
                self._close_vision()
