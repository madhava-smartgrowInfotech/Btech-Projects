"""Bounded webcam diagnostic; never writes frames or images."""
import queue
import time
import cv2
import numpy as np
from vision import Vision, CameraWorker

def main():
    v=Vision()
    try:
        observation=v.process(np.zeros((480,640,3),dtype=np.uint8),0)
        assert observation.quality=='Poor lighting'
        rng=np.random.default_rng(3)
        frame=rng.integers(50,200,(480,640,3),dtype=np.uint8)
        observation=v.process(frame,.1)
        assert observation.quality!='Good'
        print('PASS: MediaPipe model initialization, dark-frame quality gate and no-face inference')
    finally: v.close()
    worker=CameraWorker(); worker.start(); start=time.monotonic(); frames=0; qualities=set(); error=None
    try:
        while time.monotonic()-start<10:
            try: o,frame,error=worker.results.get(timeout=.5)
            except queue.Empty:
                if not worker.is_alive(): break
                continue
            if error: break
            frames+=1; qualities.add(o.quality)
    finally:
        worker.stop(); worker.join(timeout=10)
    if worker.is_alive(): raise RuntimeError('Camera did not stop within 10 seconds')
    print(f'Camera result: frames={frames}, qualities={sorted(qualities)}, error={error}')
    print('PASS: camera worker terminated and cleanup completed')

if __name__=='__main__': main()
