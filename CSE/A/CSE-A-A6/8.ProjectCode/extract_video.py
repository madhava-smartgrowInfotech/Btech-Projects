"""Extract consented labeled video frames to numeric CSV for offline research."""
import argparse
import csv
from pathlib import Path
import cv2
import numpy as np
from vision import Vision
from research import FIELDS

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video'); parser.add_argument('output')
    parser.add_argument('--subject',required=True); parser.add_argument('--session',required=True)
    parser.add_argument('--label',choices=['normal','possible_impairment'],required=True)
    parser.add_argument('--consent',action='store_true',required=True,help='Affirm documented permission for research processing')
    args=parser.parse_args()
    if not args.subject.strip() or not args.session.strip(): parser.error('Nonempty subject and session required')
    if Path(args.video).resolve()==Path(args.output).resolve(): parser.error('Output cannot overwrite the video')
    capture=cv2.VideoCapture(args.video); vision=None
    try:
        fps=capture.get(cv2.CAP_PROP_FPS)
        if not capture.isOpened() or not np.isfinite(fps) or fps<2:
            raise ValueError('Cannot read video or reliable FPS metadata')
        vision=Vision(); count=0
        # Exclusive creation prevents accidental overwrite of an existing dataset.
        with open(args.output,'x',newline='',encoding='utf-8') as f:
            writer=csv.writer(f); writer.writerow(FIELDS)
            while True:
                ok,frame=capture.read()
                if not ok: break
                t=count/fps
                o=vision.process(cv2.resize(frame,(640,480)),t)
                writer.writerow([args.subject,args.session,t,o.ear,o.roll,o.quality,args.label,'yes'])
                count+=1
        if not count: raise ValueError('Video contained no decodable frames')
        print(f'Extracted {count} frame measurements. Review quality and labels before evaluation.')
    finally:
        capture.release()
        if vision: vision.close()

if __name__=='__main__': main()
