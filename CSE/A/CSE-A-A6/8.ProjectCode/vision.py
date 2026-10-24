"""MediaPipe Tasks landmarks, pixel quality heuristics and camera worker."""
from pathlib import Path
import queue
import threading
import time
import cv2
import numpy as np
from core import Observation, eye_aspect_ratio, head_roll

MODEL_PATH = Path(__file__).parent/'models'/'face_landmarker.task'
LEFT = [33,160,158,133,153,144]
RIGHT = [362,385,387,263,373,380]

class Vision:
    def __init__(self):
        import mediapipe as mp
        self.mp = mp
        if not MODEL_PATH.exists():
            raise FileNotFoundError('Landmark model missing. Run: python setup_model.py')
        options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO, num_faces=2,
            min_face_detection_confidence=.7, min_face_presence_confidence=.7,
            min_tracking_confidence=.7)
        self.detector = mp.tasks.vision.FaceLandmarker.create_from_options(options)
        self.previous = None
        self.last_ms = -1

    def process(self, frame, now):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))
        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        small = cv2.resize(gray, (96,72)).astype(np.float32)
        motion = 0 if self.previous is None else float(np.mean(np.abs(small-self.previous)))
        self.previous = small
        quality = 'Good'
        if brightness < 40 or brightness > 225:
            quality = 'Poor lighting'
        elif sharpness < 25:
            quality = 'Blurred or hidden eyes'
        elif motion > 35:
            quality = 'Unstable video'
        o = Observation(now, quality=quality, brightness=brightness, sharpness=sharpness)
        if quality != 'Good':
            return o
        ms = max(self.last_ms+1, int(now*1000))
        self.last_ms = ms
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.detector.detect_for_video(self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb), ms)
        if len(result.face_landmarks) != 1:
            o.quality = 'No face' if not result.face_landmarks else 'Multiple faces'
            return o
        h,w = gray.shape
        points = np.array([(v.x*w, v.y*h) for v in result.face_landmarks[0]])
        eyes = [points[LEFT], points[RIGHT]]
        for eye in eyes:
            x0,y0 = np.floor(eye.min(axis=0)-6).astype(int)
            x1,y1 = np.ceil(eye.max(axis=0)+6).astype(int)
            if x0 < 0 or y0 < 0 or x1 >= w or y1 >= h or np.linalg.norm(eye[0]-eye[3]) < 14:
                o.quality = 'Eyes out of view or too small'
                return o
            patch = gray[y0:y1+1,x0:x1+1]
            if patch.mean() < 35 or patch.mean() > 230 or patch.std() < 8:
                o.quality = 'Hidden eyes or poor eye lighting'
                return o
        ears = [eye_aspect_ratio(eye) for eye in eyes]
        if abs(ears[0]-ears[1]) > .12 or max(ears) > .65:
            o.quality = 'Unreliable eye geometry'
            return o
        o.ear = float(np.mean(ears))
        o.roll = head_roll(points[33], points[263])
        for eye in eyes:
            for x,y in eye.astype(int):
                cv2.circle(frame, (int(x),int(y)), 2, (70,220,90), -1)
        return o

    def close(self):
        self.detector.close()

class CameraWorker(threading.Thread):
    def __init__(self, index=0):
        super().__init__(daemon=True)
        self.index = index
        self.stop_event = threading.Event()
        self.results = queue.Queue(maxsize=2)

    def publish(self, item):
        try:
            self.results.put_nowait(item)
        except queue.Full:
            try:
                self.results.get_nowait()
            except queue.Empty:
                pass
            self.results.put_nowait(item)

    def run(self):
        cap, vision = None, None
        try:
            vision = Vision()
            cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                raise RuntimeError('Cannot open webcam. Check Windows camera permissions and close other camera apps.')
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            while not self.stop_event.is_set():
                ok, frame = cap.read()
                now = time.monotonic()
                if not ok:
                    raise RuntimeError('Webcam frame unavailable')
                frame = cv2.resize(frame, (640,480))
                observation = vision.process(frame, now)
                self.publish((observation, frame, None))
                self.stop_event.wait(.035)
        except Exception as exc:
            self.publish((None,None,str(exc)))
        finally:
            if cap is not None:
                cap.release()
            if vision is not None:
                vision.close()

    def stop(self):
        self.stop_event.set()
