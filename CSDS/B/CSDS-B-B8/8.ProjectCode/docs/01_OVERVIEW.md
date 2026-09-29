# CareWatch - Overview

## The problem
- Activity-recognition systems trained on small, controlled datasets fail in real homes.
- Accuracy drops in low light and when furniture hides part of the body.
- Falls go unnoticed when elderly people live alone.
- Most home cameras don't send an emergency alert on their own.

## What CareWatch does
CareWatch turns a webcam, or an Android phone running the free IP Webcam app, into a privacy-first monitor.
It watches the room continuously, recognises daily activities, detects falls in real time and alerts family
within seconds.

| # | Feature | What you see |
|---|---|---|
| F1 | Live monitoring | Webcam or phone camera. A pretrained YOLO11n-pose model finds 17 body keypoints in every frame. |
| F2 | Activity recognition | Walking, standing, sitting, lying, drinking water and picking up objects, with confidence bars and a live 30-minute timeline. |
| F3 | Fall detection | A rapid drop to the floor, then stillness inside a 3 s confirmation window. Getting back up cancels it. |
| F4 | Low-light robustness | Automatic gamma + CLAHE enhancement when the room is dim. The model was also trained on darkened images. |
| F5 | Emergency alerts | A full-screen 'I'm OK' countdown, then a Telegram message with a snapshot and an email to every contact. |
| F6 | Privacy mode | The live view is a skeleton only. Video is never stored, and a snapshot is saved only when an alert is raised. |
| F7 | Daily report | Time per activity, a 24-hour timeline, long-inactivity warnings and falls. |
| F8 | Evaluation | Per-activity accuracy and F1 (normal, dim, occluded), fall sensitivity and specificity, and alert latency. |

## Who uses it
- **Elderly people living alone.** There's nothing to wear or remember. A tap on 'I'm OK' cancels a false alarm.
- **Family and caregivers.** They get a Telegram message with a photo, plus an email.
- **Care homes.** Daily reports and inactivity warnings for each monitored room.

## Screens
1. Landing
2. Sign in / create account
3. Live monitor: skeleton, activity, fall status, timeline, and recording of training clips
4. Alerts: snapshots, delivery results, latency, 'I'm OK', and a test alert
5. Contacts & settings: contacts, Telegram chat-ID lookup, camera, privacy, low light, and thresholds
6. Daily report
7. Model performance

## Design choices
- **Pose-based, not pixel-based.** Keypoints hold up better when lighting changes. They're also private, and a
  small CPU model can classify them.
- **A pretrained pose model and a small classifier.** No GPU is needed. The activity model trains in about a
  minute on a laptop CPU.
- **A confirmation window plus a countdown.** These cut false alarms before anyone is disturbed.
