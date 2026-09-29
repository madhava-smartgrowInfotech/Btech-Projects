# CareWatch - Build Plan

**Architecture:** OpenCV reads the camera (webcam index or phone IP-Webcam URL, or a video file) in a backend
thread -> low-light enhancement (CLAHE + gamma when the frame is dark) -> YOLO11n-pose (pretrained, COCO-17
keypoints, CPU) -> sliding window of keypoints -> scikit-learn activity classifier + rule-based fall state
machine -> events/alerts -> Telegram (photo) + Gmail SMTP. Frontend polls the skeleton/state; raw video is never
stored or streamed in privacy mode. React (Vite, JS, Tailwind) on :5208, FastAPI on :8208, SQLite.

**Endpoints (`/api`)**: `auth/register`, `auth/login`, `auth/me` | `monitor/start`, `monitor/stop`,
`monitor/state` (keypoints, activity, probabilities, fall status, countdown), `monitor/frame.jpg` (only when
privacy mode is off), `monitor/record` (save a labelled keypoint clip) | `alerts`, `alerts/{id}/ok`
("I'm OK"), `alerts/test` | `contacts` CRUD, `contacts/telegram-chats` (find chat IDs), `settings` GET/PUT |
`reports/daily?date=` | `metrics` (training + evaluation results) | `health`.

**Tables:** users, contacts (name, email, telegram_chat_id), settings (key/value), activity_segments
(activity, start, end, seconds), alerts (kind, status pending/cancelled/sent, detected_at, sent_at,
latency_ms, snapshot, channel results), warnings (long inactivity).

**Model:** window of 24 frames -> features (normalised pose mean/std, joint speeds, torso angle, body aspect,
wrist-to-mouth distance, hip drop) -> RandomForest over 6 classes: walking, standing, sitting, lying,
drinking, picking_up. Training sequences are built by a seeded script from real keypoints extracted from the
datasets (with darkening + occlusion augmentation), plus any own clips recorded in the app. Fall = fast hip
drop + horizontal torso, then inactivity, then a confirmation window, then an 'I'm OK' countdown, then alert.

**Screens:** Landing, Login/Register, Live monitor, Alerts, Contacts & settings, Daily report, Model performance.

**Data:** CCTV Incident Fall & Lying (127 MB, committed), Fall Detection Dataset (50 MB, committed), Human
Action Recognition (313 MB -> sample in `data/sample/` + `scripts/download_data.py`).
