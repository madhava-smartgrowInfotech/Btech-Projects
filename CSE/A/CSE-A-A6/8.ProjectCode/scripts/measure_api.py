"""Measure HTTP latency of the Smart Rider API on this machine (127.0.0.1, temporary storage, own server process).

The camera path is fed one real face still (a CEW open-eye face that passes the quality gates) encoded as a
640x480 JPEG, the same payload a browser camera frame would be. Latency therefore covers: HTTP, JPEG decode,
MediaPipe landmarks, EAR/quality gates, rule engine, SQLite event write and the annotated JPEG reply.

    .venv\\Scripts\\python.exe scripts\\measure_api.py --face C:\\ceww\\d1\\dataset_B_FacialImages\\OpenFace\\<file>.jpg
"""
import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import cv2
import httpx
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'experiments' / 'api_latency'
PORT = 8399


def summary(ms):
    ms = sorted(ms)
    return {'n': len(ms), 'mean_ms': statistics.fmean(ms), 'p50_ms': ms[len(ms) // 2],
            'p95_ms': ms[int(len(ms) * 0.95) - 1], 'max_ms': ms[-1]}


def face_jpeg(path):
    img = cv2.imread(path)
    img = cv2.resize(img, (480, 480), interpolation=cv2.INTER_CUBIC)
    canvas = np.empty((480, 640, 3), np.uint8)
    canvas[:] = img.reshape(-1, 3).mean(axis=0).astype(np.uint8)
    canvas[:, 80:560] = img
    ok, buf = cv2.imencode('.jpg', canvas, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return buf.tobytes()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--face', required=True)
    ap.add_argument('--frames', type=int, default=150)
    args = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix='rider_api_')
    env = {**os.environ, 'RIDER_DATA_DIR': os.path.join(tmp, 'data'), 'RIDER_RESEARCH_DIR': os.path.join(tmp, 'research')}
    server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1',
                               '--port', str(PORT), '--log-level', 'warning'], cwd=ROOT, env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f'http://127.0.0.1:{PORT}'
    try:
        client = httpx.Client(base_url=base, timeout=30)
        for _ in range(60):
            try:
                if client.get('/api/health').status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.5)
        demo = client.get('/api/auth/demo').json()
        t0 = time.perf_counter()
        token = client.post('/api/auth/login', json=demo).json()['token']
        login_ms = (time.perf_counter() - t0) * 1000
        client.headers['Authorization'] = f'Bearer {token}'
        result = {'login_ms': login_ms}

        health = []
        for _ in range(100):
            t0 = time.perf_counter(); client.get('/api/health'); health.append((time.perf_counter() - t0) * 1000)
        result['GET /api/health'] = summary(health)

        sid = client.post('/api/session').json()['session_id']
        client.post(f'/api/session/{sid}/source', json={'source': 'simulation', 'scenario': 'Normal'})
        client.post(f'/api/session/{sid}/monitoring', json={'active': True})
        tick = []
        for _ in range(150):
            t0 = time.perf_counter(); client.post(f'/api/session/{sid}/tick'); tick.append((time.perf_counter() - t0) * 1000)
        result['POST tick (simulation, monitoring on)'] = summary(tick)

        t0 = time.perf_counter()
        r = client.post(f'/api/session/{sid}/source', json={'source': 'camera'})
        result['camera source start_ms (loads MediaPipe model)'] = (time.perf_counter() - t0) * 1000
        client.post(f'/api/session/{sid}/monitoring', json={'active': True})
        jpeg = face_jpeg(args.face)
        frames, states, qualities = [], {}, {}
        for _ in range(args.frames):
            t0 = time.perf_counter()
            r = client.post(f'/api/session/{sid}/frame', files={'frame': ('f.jpg', jpeg, 'image/jpeg')})
            frames.append((time.perf_counter() - t0) * 1000)
            j = r.json()
            states[j['state']] = states.get(j['state'], 0) + 1
            qualities[j['quality']] = qualities.get(j['quality'], 0) + 1
        result['POST frame (real face JPEG 640x480, monitoring on)'] = summary(frames)
        result['frame_states'] = states
        result['frame_qualities'] = qualities
        result['frame_jpeg_bytes'] = len(jpeg)

        hist = []
        for _ in range(50):
            t0 = time.perf_counter(); client.get('/api/history'); hist.append((time.perf_counter() - t0) * 1000)
        result['GET /api/history (limit 500)'] = summary(hist)
        client.delete(f'/api/session/{sid}')
    finally:
        server.terminate()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'metrics.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=1))


if __name__ == '__main__':
    main()
