"""Continuous monitoring: camera -> enhancement -> pose -> activity + fall -> timeline, warnings, alerts.

Privacy: frames live only in memory. Nothing is written to disk except a snapshot when a fall alert is raised
and keypoint-only clips the user explicitly records.
"""
import json
import threading
import time
from collections import deque
from datetime import datetime, timedelta

import cv2
import numpy as np

from ..config import CLIPS_DIR, CLIP_LABELS, SNAPSHOT_DIR
from ..db import ActivitySegment, Alert, InactivityWarning, SessionLocal
from .activity import ActivityRecognizer
from .fall import FallDetector
from .features import SKELETON, VIS, body_geometry
from .pose import get_estimator, maybe_enhance
from .settings import get_settings, update_settings


class Grabber:
    """Keeps only the newest frame so slow inference never builds up lag. Video files play in real time."""

    def __init__(self, source):
        self.source = source
        is_index = str(source).strip().isdigit()
        if is_index:
            self.cap = cv2.VideoCapture(int(source), cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(int(source))
        else:
            self.cap = cv2.VideoCapture(str(source))
        self.is_file = not is_index and not str(source).lower().startswith(("http", "rtsp"))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25
        self.frame = None
        self.seq = 0
        self.ended = False
        self.stop_flag = False
        self.lock = threading.Lock()
        if self.cap.isOpened():
            threading.Thread(target=self.loop, daemon=True).start()

    def opened(self):
        return self.cap.isOpened()

    def loop(self):
        fails = 0
        t_next = time.time()
        while not self.stop_flag:
            ok, frame = self.cap.read()
            if not ok:
                fails += 1
                if self.is_file or fails > 50:
                    self.ended = True
                    break
                time.sleep(0.05)
                continue
            fails = 0
            with self.lock:
                self.frame = frame
                self.seq += 1
            if self.is_file:
                t_next += 1.0 / self.fps
                time.sleep(max(0.0, t_next - time.time()))
        self.cap.release()

    def latest(self):
        with self.lock:
            return self.seq, self.frame


class Monitor:
    def __init__(self):
        self.lock = threading.Lock()
        self.thread = None
        self.grabber = None
        self.running = False
        self.error = ""
        self.state = self.idle_state()
        self.jpeg = None
        self.recording = None
        self.last_clip = ""

    def idle_state(self):
        return {"running": False, "activity": "stopped", "confidence": 0, "probs": {}, "keypoints": [],
                "fall_state": "normal", "fps": 0, "enhanced": False, "brightness": 0, "person": False,
                "inactive_seconds": 0, "source": "", "frame_w": 640, "frame_h": 480}

    # --- control -------------------------------------------------------------------------------------
    def start(self, source=None):
        self.stop(persist=False)
        s = get_settings()
        source = str(source if source not in (None, "") else s["camera_source"])
        get_estimator()
        self.recog = ActivityRecognizer()
        g = Grabber(source)
        if not g.opened():
            self.error = f"Could not open camera source '{source}'"
            raise RuntimeError(self.error)
        self.grabber = g
        self.error = ""
        self.running = True
        self.source = source
        update_settings({"monitor_running": True})
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def stop(self, persist=True):
        self.running = False
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(timeout=5)
        if self.grabber:
            self.grabber.stop_flag = True
            self.grabber = None
        self.thread = None
        self.jpeg = None
        if persist:
            update_settings({"monitor_running": False})
        with self.lock:
            self.state = {**self.state, "running": False, "activity": "stopped", "keypoints": [], "person": False}

    def record(self, label, seconds):
        if label not in CLIP_LABELS:
            raise ValueError(f"label must be one of {CLIP_LABELS}")
        if not self.running:
            raise RuntimeError("Start monitoring first")
        self.recording = {"label": label, "until": time.time() + seconds, "frames": [], "seconds": seconds}

    # --- main loop -----------------------------------------------------------------------------------
    def loop(self):
        try:
            self._loop()
        except Exception as e:  # surface the problem on the Live monitor instead of dying silently
            self.error = f"Monitoring stopped: {e}"
            print(self.error)
            self.running = False
            with self.lock:
                self.state = {**self.state, "running": False, "activity": "stopped", "keypoints": []}

    def _loop(self):
        est = get_estimator()
        s = get_settings()
        fall = FallDetector(confirm_seconds=s["confirm_seconds"])
        seg = None                 # [activity, start_dt, db_id]
        pending = (None, 0.0)      # label waiting to become stable
        last_flush = time.time()
        last_settings = time.time()
        last_seq = -1
        fps_hist = deque(maxlen=20)
        prev_k, last_motion, warning_id = None, time.time(), None
        H_hist = deque(maxlen=50)

        while self.running:
            seq, frame = self.grabber.latest() if self.grabber else (-1, None)
            if frame is None or seq == last_seq:
                if self.grabber and self.grabber.ended:
                    break
                time.sleep(0.01)
                continue
            last_seq = seq
            t = time.time()
            if t - last_settings > 2:
                s = get_settings()
                fall.confirm_seconds = s["confirm_seconds"]
                last_settings = t

            img, enhanced, bright = maybe_enhance(frame, s["low_light"])
            person = est.main_person(est.detect(img))
            k = person["kpts"] if person is not None and (person["kpts"][:, 2] > VIS).sum() >= 5 else None
            label, conf, probs = self.recog.update(t, k)
            ev = fall.update(t, k, probs.get("lying", 0.0))
            if ev and ev["type"] == "fall":
                try:
                    self.raise_fall_alert(img, ev, s)
                except Exception as e:  # never let one bad write stop monitoring
                    self.error = f"Could not save fall alert: {e}"
                    print(self.error)

            # activity timeline (a label must hold for 1 s before the segment changes)
            if label != "detecting":
                lab = "away" if label == "no_person" else label
                if seg is None or lab == seg[0]:
                    pending = (None, 0.0)
                elif pending[0] != lab:
                    pending = (lab, t)
                if seg is None or (pending[0] == lab and t - pending[1] >= 1.0):
                    seg = self.switch_segment(seg, lab)
                    pending = (None, 0.0)
            if seg and t - last_flush > 5:
                self.flush_segment(seg)
                last_flush = t

            # long inactivity
            g = body_geometry(k) if k is not None else None
            if g is not None:
                H_hist.append(g[1])
                if prev_k is not None:
                    both = (k[:, 2] > VIS) & (prev_k[:, 2] > VIS)
                    if both.sum() >= 4:
                        move = np.linalg.norm(k[both, :2] - prev_k[both, :2], axis=1).mean() / np.median(H_hist)
                        if move > 0.02:
                            last_motion = t
                prev_k = k
            else:
                prev_k = None
                if label == "no_person":
                    last_motion = t
            inactive = t - last_motion
            if inactive >= s["inactivity_minutes"] * 60 and warning_id is None:
                warning_id = self.open_warning(seg[0] if seg else "", last_motion)
            elif inactive < 1 and warning_id is not None:
                self.close_warning(warning_id)
                warning_id = None
            elif warning_id is not None and t - last_flush < 0.2:
                self.close_warning(warning_id, final=False)

            # clip recording (keypoints only)
            rec = self.recording
            if rec:
                rec["frames"].append({"t": round(t, 3), "kpts": k.round(2).tolist() if k is not None else None})
                if t >= rec["until"]:
                    self.save_clip(rec)

            fps_hist.append(t)
            fps = (len(fps_hist) - 1) / (fps_hist[-1] - fps_hist[0]) if len(fps_hist) > 1 else 0
            h, w = frame.shape[:2]
            kp = [[float(x / w), float(y / h), float(c)] for x, y, c in k] if k is not None else []
            with self.lock:
                self.state = {
                    "running": True, "source": self.source, "activity": label, "confidence": round(conf, 3),
                    "probs": probs, "keypoints": kp, "person": k is not None, "fall_state": fall.state,
                    "fps": round(fps, 1), "enhanced": enhanced, "brightness": round(bright, 1),
                    "inactive_seconds": round(inactive, 1), "frame_w": w, "frame_h": h,
                    "segment": {"activity": seg[0], "start": seg[1].isoformat()} if seg else None,
                    "recording": ({"label": rec["label"], "left": max(0, round(rec["until"] - t, 1))}
                                  if self.recording else None),
                    "last_clip": self.last_clip,
                }
            if not s["privacy_mode"]:
                self.jpeg = self.annotated(img, k)
            else:
                self.jpeg = None

        if seg:
            self.flush_segment(seg)
        if warning_id is not None:
            self.close_warning(warning_id)
        self.running = False
        with self.lock:
            ended = self.grabber.ended if self.grabber else False
            self.state = {**self.state, "running": False, "activity": "stopped", "keypoints": [],
                          "person": False, "ended": ended}

    # --- helpers -------------------------------------------------------------------------------------
    def switch_segment(self, seg, activity):
        now = datetime.now()
        if seg:
            self.flush_segment(seg, end=now)
        with SessionLocal() as db:
            row = ActivitySegment(activity=activity, start=now, end=now, seconds=0)
            db.add(row)
            db.commit()
            return [activity, now, row.id]

    def flush_segment(self, seg, end=None):
        end = end or datetime.now()
        with SessionLocal() as db:
            row = db.get(ActivitySegment, seg[2])
            if row:
                row.end = end
                row.seconds = round((end - row.start).total_seconds(), 1)
                db.commit()

    def open_warning(self, activity, since_ts):
        with SessionLocal() as db:
            start = datetime.now() - timedelta(seconds=time.time() - since_ts)
            w = InactivityWarning(activity=activity, started_at=start,
                                  minutes=round((datetime.now() - start).total_seconds() / 60, 1))
            db.add(w)
            db.commit()
            return w.id

    def close_warning(self, wid, final=True):
        with SessionLocal() as db:
            w = db.get(InactivityWarning, wid)
            if w:
                now = datetime.now()
                w.minutes = round((now - w.started_at).total_seconds() / 60, 1)
                if final:
                    w.ended_at = now
                db.commit()

    def raise_fall_alert(self, img, ev, s):
        now = datetime.now()
        with SessionLocal() as db:
            a = Alert(kind="fall", status="pending", detected_at=now,
                      impact_at=now - timedelta(seconds=ev["latency"]),
                      deadline=now + timedelta(seconds=s["countdown_seconds"]),
                      detection_latency_ms=round(ev["latency"] * 1000, 1),
                      details={"drop_speed": ev.get("speed"), "room": s["room_name"]})
            db.add(a)
            db.commit()
            name = f"alert_{a.id}_{now:%Y%m%d_%H%M%S}.jpg"
            cv2.imwrite(str(SNAPSHOT_DIR / name), img)  # the only image CareWatch ever saves
            a.snapshot = name
            db.commit()

    def save_clip(self, rec):
        self.recording = None
        d = CLIPS_DIR / rec["label"]
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"clip_{datetime.now():%Y%m%d_%H%M%S}.json"
        path.write_text(json.dumps({"label": rec["label"], "recorded": datetime.now().isoformat(),
                                    "format": "COCO-17 keypoints (x, y, conf) in pixels",
                                    "frames": rec["frames"]}))
        self.last_clip = f"{rec['label']}/{path.name} ({len(rec['frames'])} frames)"

    def annotated(self, img, k):
        out = img.copy()
        if k is not None:
            for a, b in SKELETON:
                if k[a, 2] > VIS and k[b, 2] > VIS:
                    cv2.line(out, tuple(map(int, k[a, :2])), tuple(map(int, k[b, :2])), (80, 220, 120), 2)
            for x, y, c in k:
                if c > VIS:
                    cv2.circle(out, (int(x), int(y)), 3, (255, 255, 255), -1)
        ok, buf = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return buf.tobytes() if ok else None

    def get_state(self):
        with self.lock:
            st = dict(self.state)
        st["error"] = self.error
        return st


monitor = Monitor()
