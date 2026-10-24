"""Static product text taken from README.md / app.py so the web UI says exactly what the desktop app says."""
from dataclasses import asdict

from core import Settings

TITLE = 'Smart Rider Impairment Warning System for Two-Wheelers'

DISCLAIMERS = [
    'A camera cannot confirm alcohol consumption. This is a possible drowsiness / impairment indicator only.',
    'Normal does not certify fitness to ride.',
    'Mount the camera firmly facing the rider with eyes visible; never obstruct vision or controls.',
    'Windows laptop prototype: demonstrate while stationary. Not road-ready.',
    'The system never controls vehicle power, ignition or brakes.',
]

BOUNDS = {
    'ear_threshold': {'min': 0.08, 'max': 0.4, 'step': 0.005, 'label': 'EAR threshold',
                      'help': 'Smoothed eye-aspect-ratio below this counts as a closed eye. Calibration sets it per rider.'},
    'closure_seconds': {'min': 0.5, 'max': 5, 'step': 0.1, 'label': 'Closure seconds',
                        'help': 'Continuous closed-eye time that starts a warning timer.'},
    'persistence_seconds': {'min': 0.5, 'max': 5, 'step': 0.1, 'label': 'Persistence seconds',
                            'help': 'Evidence must persist this long before the warning is shown.'},
    'closed_fraction': {'min': 0.3, 'max': 0.9, 'step': 0.01, 'label': 'Closed fraction',
                        'help': 'Share of the last 10 s with eyes closed (needs at least 8 s of history).'},
    'tilt_degrees': {'min': 10, 'max': 45, 'step': 1, 'label': 'Tilt degrees',
                     'help': 'Head roll that counts as risk when combined with a low EAR.'},
    'cooldown_seconds': {'min': 5, 'max': 120, 'step': 1, 'label': 'Alert cooldown seconds',
                         'help': 'Minimum gap between two audible alerts.'},
}

QUALITY_GATES = [
    'Frame mean grayscale below 40 or above 225 (poor lighting)',
    'Laplacian variance below 25 (blurred or hidden eyes)',
    'Mean difference of consecutive 96x72 frames above 35 (unstable video)',
    'No face, or more than one face',
    'Eye width below 14 px, or eye patches outside the image',
    'Eye-region mean below 35 / above 230, or standard deviation below 8',
    'Inter-eye EAR difference above 0.12 (unreliable geometry)',
]


def config():
    return {
        'title': TITLE,
        'scenarios': ['Normal', 'Prolonged eye closure', 'Missing face', 'Poor lighting'],
        'bounds': BOUNDS,
        'defaults': {k: v for k, v in asdict(Settings()).items() if k != 'calibrated'},
        'frame': {'width': 640, 'height': 480},
        'quality_gates': QUALITY_GATES,
        'disclaimers': DISCLAIMERS,
        'states': {'normal': 'Normal', 'warning': 'Possible impairment or drowsiness', 'unknown': 'Unable to assess'},
    }


def about():
    return {
        'title': TITLE,
        'summary': ('A stationary demonstration prototype. It estimates possible drowsiness or impairment from visible '
                    'eye and head observations with transparent, explainable rules. It is not an alcohol test, not a '
                    'medical device and not road-ready.'),
        'pipeline': [
            {'name': 'Camera', 'text': 'The browser webcam sends 640x480 frames; they live in RAM only and are never saved.'},
            {'name': 'MediaPipe landmarks', 'text': 'Face Landmarker finds six perimeter points on each eye plus both outer eye corners.'},
            {'name': 'Quality gates', 'text': 'Lighting, blur, motion, face count and eye geometry are checked first; bad frames never produce a verdict.'},
            {'name': 'Observation', 'text': 'EAR (eye aspect ratio) and image-plane head roll are extracted with a 3-sample median.'},
            {'name': 'Rule engine', 'text': 'Closure time, closed-eye fraction over 10 s and tilt-with-low-EAR must persist before a warning.'},
            {'name': 'Output + log', 'text': 'Normal / Possible impairment or drowsiness / Unable to assess, with the reason, logged as numbers to SQLite.'},
        ],
        'formulas': [
            {'name': 'EAR', 'text': '(|p2-p6| + |p3-p5|) / (2 |p1-p4|) over six eye points, averaged over both eyes. Dimensionless.'},
            {'name': 'Closed eye', 'text': 'Smoothed EAR below the threshold (default 0.21, an engineering heuristic, not a clinical cutoff).'},
            {'name': 'Blink', 'text': 'A completed low-EAR interval of 0.08-0.8 s. Blink rate is shown but never warns on its own.'},
            {'name': 'Closed fraction', 'text': 'Time-weighted closed-eye duration over the last 10 s. Not validated clinical PERCLOS.'},
            {'name': 'Head roll', 'text': 'atan2(right_eye_y - left_eye_y, |right_eye_x - left_eye_x|) in degrees, image plane only.'},
            {'name': 'Calibration', 'text': '8-15 s of open eyes; threshold = clip(0.72 x median EAR, 0.12, 0.32); needs 40 usable frames and 70% accepted.'},
        ],
        'rules': [
            'Closure of 1.5 s or longer',
            'Closed fraction of 0.55 or more with at least 8 s of history',
            'Head tilt of 25 degrees or more together with a low EAR',
            'Any one must persist 1 more second, with 2 s of reliable history, before the warning appears',
        ],
        'limitations': [
            'Visible-eye requirement: helmets, visors, glasses, blur, vibration and dark skin tones or lighting can prevent assessment.',
            'Closed eyes and low EAR have many explanations; open eyes do not establish alertness.',
            'Head roll is image-plane tilt, not full head pose. Calibration may be wrong if the rider is already fatigued.',
            'No validated sensitivity, specificity, demographic robustness or safety assurance. False alerts and misses happen.',
            'Simulation scenarios are scripted measurements, not model predictions or research validation.',
            'No consented labelled dataset is bundled, so the research model is "Model not trained" until you supply one.',
        ],
        'reference': {
            'citation': ('Feng and Li (2026), Robust Driver State Assessment on an Embedded Platform Using a Fuzzy Belief '
                         'Rule-Based Fusion of Eye Aspect Ratio and Voice Commands, IEEE Access 14, 36158-36175.'),
            'doi': 'https://doi.org/10.1109/ACCESS.2026.3670924',
            'note': ('This app borrows only the general idea of combining observable signals with personal calibration. '
                     'It does not reproduce their EAR4, voice interface, fuzzy belief engine or measured results.'),
        },
        'cli_tools': [
            {'name': 'extract_video.py', 'text': 'Offline: turn an existing consented, labelled video clip into a frame-measurement CSV.'},
            {'name': 'research.py', 'text': 'Offline: train and evaluate the nearest-centroid classifier with held-out subjects.'},
            {'name': 'setup_model.py', 'text': 'One-time download of Google\'s face_landmarker.task (run.bat does this for you).'},
            {'name': 'camera_check.py', 'text': 'Bounded diagnostic for the desktop webcam worker.'},
        ],
    }
