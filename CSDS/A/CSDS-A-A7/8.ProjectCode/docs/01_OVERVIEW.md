# SHEGUARD - Overview

SHEGUARD is a women's safety companion: it recommends safer travel routes, lets a user
trigger emergency help hands-free, keeps trusted guardians informed with a live location
link, and preserves time-stamped, hashed evidence from the emergency.

## Who it's for
- Women travelling alone or at night, choosing a route or needing to raise an alert fast.
- Guardians (family, friends) who receive an alert and watch a live tracking page - no
  account or app install required on their side.

## Feature list (see docs/02_HOW_IT_WORKS.md for how each works)
| Feature | What it does |
|---|---|
| Safe Route | OSRM route alternatives scored by area risk + time of day; safest one is recommended |
| Area risk model | K-Means clustering of district-level crime data into low/medium/high risk tiers |
| Emergency triggers | SafePhrase voice trigger (Web Speech API) and a one-tap SOS button |
| Live location session | Position streams to guardians over a WebSocket while the session is active |
| Free alerts | Telegram message + email to every guardian with the live tracking link |
| Evidence capture | Photo or audio clip, saved with time, location and a SHA-256 hash |
| AI safety assistant | Gemini answers safety questions and suggests next steps |
| Roles & access | Every query is scoped to the logged-in user; guardians only ever see a per-session share link |
| Installable PWA | Add-to-home-screen, full-screen app on a phone |

## Architecture at a glance
```
React + Vite (5107)  <-- proxy /api, /ws -->  FastAPI + SQLite (8107)
        |                                              |
   Web Speech API                          OSRM, Nominatim, Gemini,
   Leaflet map                             Telegram Bot API, Gmail SMTP
```

See `docs/PLAN.md` for the original architecture plan and `docs/02_HOW_IT_WORKS.md` for
implementation detail, data provenance and evaluation numbers.
