"""Explicit one-time download from Google's official MediaPipe model storage."""
from pathlib import Path
import hashlib
import urllib.request
URL = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'

def main():
    target = Path(__file__).parent/'models'/'face_landmarker.task'
    target.parent.mkdir(exist_ok=True)
    if not target.exists():
        temp = target.with_suffix('.download')
        try:
            with urllib.request.urlopen(URL, timeout=60) as response, temp.open('wb') as f:
                while block := response.read(1024*1024):
                    f.write(block)
            if temp.stat().st_size < 1000000:
                raise RuntimeError('Incomplete model download')
            temp.replace(target)
        finally:
            temp.unlink(missing_ok=True)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    print(f'Model ready: {target}\nSHA256: {digest}')

if __name__ == '__main__':
    main()
