"""API smoke test: walks the main flow end to end against temporary storage (your data/ is untouched).

Run from the project root:  .venv\\Scripts\\python.exe scripts\\smoke_test.py
The camera path is driven with a blank frame (expects the quality gate to answer "Poor lighting"), because no
person is available in a script; real face handling is covered by tests/test_system.py and camera_check.py.
"""
import io
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = tempfile.mkdtemp(prefix='rider_smoke_')
os.environ['RIDER_DATA_DIR'] = os.path.join(TMP, 'data')
os.environ['RIDER_RESEARCH_DIR'] = os.path.join(TMP, 'research')

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend import synthetic  # noqa: E402
from backend.main import app  # noqa: E402

failures = []


def check(name, condition, detail=''):
    print(('PASS' if condition else 'FAIL'), name, detail if not condition else '')
    if not condition:
        failures.append(name)


def run():
    c = TestClient(app)
    check('health is public', c.get('/api/health').json()['status'] == 'ok')
    check('config lists 4 scenarios', len(c.get('/api/config').json()['scenarios']) == 4)
    check('about has pipeline', len(c.get('/api/about').json()['pipeline']) >= 5)
    check('protected route needs login', c.get('/api/history').status_code == 401)
    check('wrong password rejected', c.post('/api/auth/login', json={'email': 'x@y.z', 'password': 'no'}).status_code == 401)
    demo = c.get('/api/auth/demo').json()
    token = c.post('/api/auth/login', json=demo).json()['token']
    c.headers['Authorization'] = f'Bearer {token}'
    check('me works with token', c.get('/api/auth/me').json()['email'] == demo['email'])

    s = c.get('/api/settings').json()
    check('default threshold 0.21', s['settings']['ear_threshold'] == 0.21 and not s['calibrated'])

    sid = c.post('/api/session').json()['session_id']
    r = c.post(f'/api/session/{sid}/monitoring', json={'active': True})
    check('monitoring needs a source (409)', r.status_code == 409, r.text)
    r = c.post(f'/api/session/{sid}/calibration', json={'active': True})
    check('calibration refused without camera (409)', r.status_code == 409, r.text)

    st = c.post(f'/api/session/{sid}/source', json={'source': 'simulation', 'scenario': 'Prolonged eye closure'}).json()
    check('simulation source set', st['source'] == 'simulation' and 'SIMULATION' in st['source_label'])
    r = c.post(f'/api/session/{sid}/calibration', json={'active': True})
    check('calibration refused in simulation (409)', r.status_code == 409)
    st = c.post(f'/api/session/{sid}/monitoring', json={'active': True}).json()
    check('monitoring on', st['monitoring'])
    states = []
    for _ in range(30):
        states.append(c.post(f'/api/session/{sid}/tick').json())
        time.sleep(0.25)
    check('simulation produced a metrics block', states[-1]['metrics'] is not None)
    check('state is one of the three outputs', states[-1]['state'] in states[-1]['verdicts'].values())
    st = c.post(f'/api/session/{sid}/source', json={'source': 'simulation', 'scenario': 'Missing face'}).json()
    check('scenario switch keeps session', st['scenario'] == 'Missing face' and not st['monitoring'])
    c.post(f'/api/session/{sid}/monitoring', json={'active': True})
    st = c.post(f'/api/session/{sid}/tick').json()
    check('missing face -> Unable to assess', st['state'] == 'Unable to assess', st['state'])

    # camera path with a blank frame
    st = c.post(f'/api/session/{sid}/source', json={'source': 'camera'})
    check('camera source starts (landmark model loads)', st.status_code == 200, st.text)
    ok, jpg = cv2.imencode('.jpg', np.zeros((480, 640, 3), np.uint8))
    r = c.post(f'/api/session/{sid}/frame', files={'frame': ('f.jpg', jpg.tobytes(), 'image/jpeg')})
    check('blank frame -> Poor lighting + preview', r.status_code == 200 and r.json()['quality'] == 'Poor lighting'
          and r.json()['preview'].startswith('data:image/jpeg'), r.text[:200])
    r = c.post(f'/api/session/{sid}/frame', files={'frame': ('f.jpg', b'not an image', 'image/jpeg')})
    check('garbage frame -> 422', r.status_code == 422)
    r = c.post(f'/api/session/{sid}/calibration', json={'active': True})
    check('calibration can start with camera', r.status_code == 200 and r.json()['calibrating'])
    r = c.post(f'/api/session/{sid}/monitoring', json={'active': True})
    check('monitoring blocked while calibrating', r.status_code == 409)
    c.post(f'/api/session/{sid}/calibration', json={'active': False})
    c.post(f'/api/session/{sid}/source', json={'source': 'none'})

    h = c.get('/api/history').json()
    check('history has events and summary', h['total'] > 0 and h['events'] and 'summary' in h)
    check('simulation events are labelled', any(e['simulation'] for e in h['events']))
    csv_resp = c.get('/api/history/export')
    check('CSV export', csv_resp.status_code == 200 and csv_resp.text.startswith('﻿id,timestamp') or csv_resp.text.startswith('id,timestamp'))

    bad = dict(s['settings'], ear_threshold=0.9)
    check('invalid threshold -> 422', c.put('/api/settings', json=bad).status_code == 422)
    good = dict(s['settings'], ear_threshold=0.22, closure_seconds=1.6)
    r = c.put('/api/settings', json=good)
    check('valid thresholds saved', r.status_code == 200 and r.json()['settings']['ear_threshold'] == 0.22)
    check('thresholds persisted', c.get('/api/settings').json()['settings']['closure_seconds'] == 1.6)

    check('research starts "Model not trained"', c.get('/api/research').json()['trained'] is False)
    check('evaluate without subjects -> 422', c.post('/api/research/evaluate', files={'file': ('a.csv', b'x', 'text/csv')}).status_code == 422)
    r = c.post('/api/research/evaluate', files={'file': ('a.csv', b'a,b\n1,2\n', 'text/csv')}, data={'test_subjects': 'S1'})
    check('bad CSV -> 422 with reason', r.status_code == 422 and 'Required CSV columns' in r.text, r.text)
    sample = c.get('/api/research/sample-csv').text
    r = c.post('/api/research/evaluate', files={'file': ('s.csv', io.BytesIO(sample.encode()), 'text/csv')},
               data={'test_subjects': ','.join(synthetic.HELD_OUT)})
    check('synthetic evaluation trains', r.status_code == 200 and r.json()['trained'], r.text[:300])
    check('report is flagged synthetic', r.json().get('synthetic') is True)
    check('confusion matrix PNG', c.get('/api/research/confusion-matrix').headers['content-type'] == 'image/png')

    r = c.delete(f'/api/session/{sid}')
    check('session closed', r.json()['closed'])


if __name__ == '__main__':
    run()
    print('\nALL PASSED' if not failures else f'\n{len(failures)} FAILED: {failures}')
    sys.exit(1 if failures else 0)
