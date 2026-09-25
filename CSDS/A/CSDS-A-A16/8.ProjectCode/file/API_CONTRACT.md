# Mosaic — API Contract (v1)

Source of truth for both backend and frontend. Do not diverge from this without updating this file.

Product name: **Mosaic**. Tagline: "See every emotion, not just one." No academic/college/project wording anywhere in the product UI, copy, or API responses (backend code comments/README are fine to be technical).

Base URL (dev): `http://localhost:8000/api`
Frontend dev: `http://localhost:3000`, reads backend URL from `NEXT_PUBLIC_API_URL` env var (default `http://localhost:8000/api`).

## Auth

All authenticated requests send `Authorization: Bearer <token>`.

### POST /api/auth/register
Body: `{ "name": string, "email": string, "password": string }`
201 → `{ "token": string, "user": { "id": string, "name": string, "email": string, "created_at": string } }`
409 if email already registered → `{ "detail": "Email already registered" }`

### POST /api/auth/login
Body: `{ "email": string, "password": string }`
200 → same shape as register response.
401 on bad credentials.

### GET /api/auth/me
Header auth required. 200 → `{ "id", "name", "email", "created_at" }`

## Emotion taxonomy (fixed — do not change label strings, frontend keys off them)

Basic (7): `angry, disgust, fear, happy, sad, surprise, neutral`

Compound (11) — Du, Tao & Martinez compound-expression taxonomy:
`happily_surprised, happily_disgusted, sadly_fearful, sadly_angry, sadly_surprised, sadly_disgusted, fearfully_angry, fearfully_surprised, angrily_surprised, angrily_disgusted, disgustedly_surprised`

Each has a human display label the backend also returns (e.g. `happily_surprised` → `"Happily Surprised"`) so the frontend never has to reformat snake_case itself.

## POST /api/analyze

Multipart form, field `image` (jpeg/png). Auth optional — if a valid Bearer token is present, the result is saved to that user's history; if not, it's analyzed but not persisted.

200 →
```json
{
  "id": "uuid-or-null-if-not-persisted",
  "created_at": "2026-09-23T12:00:00Z",
  "face_detected": true,
  "basic_emotions": [
    { "key": "happy", "label": "Happy", "confidence": 0.82 },
    { "key": "surprise", "label": "Surprise", "confidence": 0.41 }
    // all 7, sorted desc by confidence
  ],
  "compound_emotions": [
    { "key": "happily_surprised", "label": "Happily Surprised", "confidence": 0.63 }
    // all 11, sorted desc by confidence
  ],
  "dominant": { "key": "happily_surprised", "label": "Happily Surprised", "confidence": 0.63, "kind": "compound" },
  "thumbnail_url": "/api/media/thumbs/<id>.jpg or null"
}
```
422 if no face detected in the image → `face_detected: false`, emotion arrays empty, `dominant: null`.

## GET /api/history
Auth required. Query: `?limit=20&offset=0`
200 → `{ "items": [ { ...same shape as analyze response, minus nothing... }, ], "total": number }`

## GET /api/history/{id}
Auth required, must own the record. 200 → single analysis object. 404 if not found/not owned.

## DELETE /api/history/{id}
Auth required, must own the record. 204 on success.

## GET /api/health
No auth. 200 → `{ "status": "ok", "model_loaded": true }`

## Errors
Standard shape: `{ "detail": string }` with appropriate 4xx/5xx status.
