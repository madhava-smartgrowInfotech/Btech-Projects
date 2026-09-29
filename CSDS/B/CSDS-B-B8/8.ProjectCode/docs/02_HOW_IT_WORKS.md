# CareWatch - How it works

## Architecture
```
 camera (webcam index / phone IP-Webcam URL / video file)
   |  OpenCV grabber thread - keeps only the newest frame (no lag build-up); frames stay in memory
   v
 low-light check (mean grey < 80) -> gamma 0.5 + CLAHE on L channel            [F4]
   v
 YOLO11n-pose (pretrained, CPU, 480 px) -> 17 COCO keypoints of the main person [F1]
   |--> ActivityRecognizer: 20-frame window -> 123 features -> RandomForest -> smoothed label [F2]
   |--> FallDetector: drop > 0.35 body-height within 2 s + lying posture -> 3 s confirmation   [F3]
   |--> inactivity tracker (no keypoint movement > threshold)                   [F7]
   v
 SQLite: activity_segments, alerts, warnings, contacts, settings, users
   v
 Alert watchdog: 'I'm OK' countdown expires -> Telegram sendPhoto + Gmail SMTP  [F5]
   v
 FastAPI (:8208)  <-- React + Tailwind (:5208) polls the skeleton state          [F6: skeleton only]
```

The monitor runs in a backend thread, so monitoring continues with the browser closed. The `monitor_running`
setting resumes it after a restart.

## Pose and features (`backend/app/services/features.py`)
- **Per frame (57 values):** keypoints centred on the torso and scaled by body size (34), keypoint visibility
  (17), torso angle from vertical, body box aspect, wrist-to-head distance (drinking), knee angle (sitting),
  hip-to-knee height and wrist height (picking up).
- **Per window (20 frames, about 2 s):** mean and standard deviation of the 57 frame values, plus motion:
  body-centre speed (mean/max, horizontal/vertical), vertical displacement, wrist and leg speed relative to
  the body, torso-angle range, and the fraction of frames with a person. That's 123 features in total.
- **Classifier:** scikit-learn RandomForest (300 trees, balanced class weights). The live output is
  exponentially smoothed. A new timeline segment starts only once a label has held for 1 s.

## Fall detection (`backend/app/services/fall.py`)
1. **Impact.** The body centre drops more than 0.35 x the person's upright body height within 2 s, and the
   posture is now "down" (torso > 50 deg from vertical, a wide body box, or the classifier says lying).
2. **Confirmation window (default 3 s).** The person stays down at least 60% of the time and is still (centre
   speed < 0.35 body-heights/s). Someone struggling on the floor is still confirmed after 9 s. If the person
   stands back up for 1 s, the fall is cancelled.
3. **Countdown (default 20 s).** A full-screen 'I'm OK' dialog appears on every screen. If nobody presses it,
   the watchdog sends a Telegram photo and an email to every active contact, and records per-contact results
   and timings.

If the person disappears after the impact (for example, behind a sofa), their last posture is kept, so an
occluded fall is still confirmed.

## Low light (F4)
- **At runtime:** if the frame's mean brightness is below 80, the frame gets a gamma lift and CLAHE before pose
  estimation. The live view shows the "Low-light enhancement on" badge.
- **In training:** every image is processed three ways: normal, *dark* (exposure x0.18-0.35, gamma 1.5-2.2,
  sensor noise) and *dark + enhanced*. Poses from all three train the classifier.
- **Occlusion:** training windows randomly hide the legs or one arm, and drop up to 12% of keypoints.

## Privacy (F6)
- Privacy mode is on by default, so the browser receives only 17 keypoints and draws a skeleton.
- Frames are never written to disk. When privacy mode is off, the video view is served from memory only.
- The only image ever saved is the snapshot attached to a fall alert (`data/snapshots/`, git-ignored).
- Training clips recorded in the app store keypoints only.

## Data
| Source | Licence | Used for | Committed |
|---|---|---|---|
| [CCTV Incident Dataset - Fall & Lying Down](https://www.kaggle.com/datasets/simuletic/cctv-incident-dataset-fall-and-lying-down-detection) (Simuletic) | CC BY-NC-SA 4.0 | 111 CCTV-style images with boxes and 17 keypoints - lying / standing | Yes, full set in `data/cctv_lying/` (165 MB) |
| [Fall Detection Dataset](https://www.kaggle.com/datasets/uttejkumarkandagatla/fall-detection-dataset) | As listed on Kaggle | 485 labelled images - fallen / walking / sitting (train + val) | Yes, full set in `data/fall_detection/` (52 MB) |
| [Human Action Recognition (HAR)](https://www.kaggle.com/datasets/meetnagadia/human-action-recognition-har-dataset) | As listed on Kaggle | drinking, sitting and sleeping (lying) classes - 2,520 images | Sample of 900 images in `data/sample/har/`. The full classes are fetched by `scripts/download_data.py` into `data/raw/` (git-ignored) |
| Own clips (in-app recorder) | Recorded with consent | Real keypoint sequences per activity | `data/own_clips/<label>/*.json` (keypoints only) |
| Extracted keypoints | derived | Everything above, run through YOLO11n-pose | `data/keypoints/poses.npz` |
| Sample video | derived, **sample data** | 5 s standing + 15 s fallen, from Fall Detection validation stills | `data/sample/demo_fall.mp4` (`scripts/make_demo_video.py`) |

**Label mapping.** CCTV: laying -> lying, standing -> standing. Fall Detection: fall -> lying, walking ->
standing (upright), sitting -> sitting. HAR: drinking -> drinking, sitting -> sitting, sleeping -> lying.

**Walking and picking up.** The public datasets are still images with no walking or picking-up video. The
seeded sequence builder (`ml/sequences.py`) starts from real extracted poses and adds motion:
- sway for still postures
- gait oscillation plus translation for walking (across the view or towards the camera)
- a forward bend with a hand to the floor for picking up (side and frontal views)
- gravity-eased standing-to-floor transitions for fall evaluation

This generated data is deterministic and comes only from committed scripts. Clips recorded in the app are
real sequences, and training uses them automatically.

**Splits.** Fall Detection uses its own train/val split. CCTV and HAR are split 75/25 per image with seed 42.
Every test window is built only from held-out images.

## Evaluation (F8)
`ml/eval.py` writes `experiments/eval/metrics.json`. The Model performance screen shows the results.
- **Activity:** accuracy (per-class recall) and F1 under four conditions: normal light, dim without
  enhancement, dim with CareWatch enhancement, and legs occluded. It also reports the person detection rate
  per lighting condition.
- **Falls:** 640 simulated sequences built from held-out real poses, run through the real `FallDetector` with
  the classifier's smoothed lying probability. There are 3 fall types (fast, slow collapse, legs occluded)
  and 5 non-fall types (sit down, lie down slowly, pick up, walk, stand), 80 of each. It reports sensitivity,
  specificity, and impact-to-confirmation latency.
- **Latency:** pose-model time per frame on CPU, classifier time, pipeline fps, and alert delivery time
  (measured on real deliveries once Telegram and Gmail are configured). End-to-end latency is confirmation +
  countdown + delivery.

## API
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/register`, `/api/auth/login` | Account and JWT |
| GET | `/api/auth/me` | Current user |
| POST | `/api/monitor/start` `{source}` / `/api/monitor/stop` | Start or stop continuous monitoring |
| GET | `/api/monitor/state` | Keypoints, activity, probabilities, fall state, fps, low-light, pending alert |
| GET | `/api/monitor/frame.jpg` | Live frame, only when privacy mode is off |
| POST | `/api/monitor/record` `{label, seconds}` | Record a keypoint-only training clip |
| GET | `/api/alerts` | Alert history |
| POST | `/api/alerts/{id}/ok` | 'I'm OK' - cancel a pending alert |
| POST | `/api/alerts/test` | Send a test alert to all contacts |
| GET | `/api/alerts/{id}/snapshot` | Alert snapshot |
| GET/POST/PUT/DELETE | `/api/contacts[/{id}]` | Emergency contacts |
| GET | `/api/telegram/chats` | Chats that messaged the bot (to find chat IDs) |
| GET/PUT | `/api/settings` | Room, camera, privacy, low light, thresholds, channel status |
| GET | `/api/reports/daily?day=YYYY-MM-DD`, `/api/reports/days` | Daily report |
| GET | `/api/metrics` | Training, evaluation and live alert metrics |
