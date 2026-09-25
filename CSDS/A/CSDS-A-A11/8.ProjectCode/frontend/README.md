# Nuvara — Storefront & Intelligence Console

The Nuvara web client: a dark-mode-first commerce storefront and **Nuvara Intelligence**, the
internal ops console for the recommendation layer behind it.

Built with React 18 + TypeScript + Vite, Tailwind CSS, GSAP (ScrollTrigger), Lenis, Framer Motion,
Three.js, TanStack Query, Zustand, React Router and Recharts. UI primitives are hand-built on Radix
UI with `class-variance-authority` + `tailwind-merge`.

---

## Quick start

```bash
cd frontend
npm install
cp .env.example .env        # optional — defaults already point at localhost:8000
npm run dev                 # http://localhost:5173
```

The client talks to the FastAPI service on `http://localhost:8000`. **It does not require the
service to be running to start**: every surface degrades to a skeleton, an empty state or a
retryable error panel, the WebSocket reconnects with exponential backoff, and traffic telemetry
falls back to REST polling.

### Scripts

| Command             | What it does                                            |
| ------------------- | ------------------------------------------------------- |
| `npm run dev`       | Vite dev server on port 5173 with HMR                   |
| `npm run build`     | Type-checks (`tsc --noEmit`) then builds to `dist/`      |
| `npm run preview`   | Serves the production build locally                     |
| `npm run typecheck` | Type-check only                                         |

---

## Environment variables

Read at build/dev time by Vite. Both have working defaults, so a `.env` file is optional.

| Variable             | Default                        | Purpose                                 |
| -------------------- | ------------------------------ | --------------------------------------- |
| `VITE_API_BASE_URL`  | `http://localhost:8000/api`    | REST base URL for every API call        |
| `VITE_WS_URL`        | `ws://localhost:8000/ws/traffic` | Live traffic telemetry socket         |

See `.env.example`.

---

## Routes

| Route              | Surface                                                                      |
| ------------------ | ---------------------------------------------------------------------------- |
| `/`                | Hero (Three.js particle field), category rail, **Recommended for you** rail, trending rail, social proof |
| `/shop`            | Product grid — search, category filter, sort, pagination, skeletons           |
| `/shop/:category`  | Same grid scoped to a category                                                |
| `/product/:slug`   | Gallery, price, add-to-bag, reviews, rating widget, similar-items rail with **Why this?** explainability drawer |
| `/cart`            | Persisted client-side bag, order summary, complementary-items rail            |
| `/intelligence`    | Ops console — `?tab=twin` \| `?tab=learning` \| `?tab=traffic`                |

---

## Nuvara Intelligence

**Digital Twin Lab** (`?tab=twin`) — weight sliders for the four agents (auto-normalised to sum to
1.00), population/rounds controls, strategy presets, `POST /api/simulate`, animated baseline-vs-candidate
metric cards, lift figures, a round-by-round timeline chart, a segment breakdown chart, a verdict
badge with the narrative, `POST /api/simulate/{run_id}/deploy`, and the run history from
`GET /api/simulate/history`.

**Learning Loop** (`?tab=learning`) — the live orchestrator weights as a donut with per-agent drift,
the full online-update trace from `GET /api/feedback/weights-history`, and a feed of the
reinforcement signals this browser has emitted.

**Traffic Control** (`?tab=traffic`) — live rps / p50 / p99 / queue depth / cache hit rate / workers
with spring-animated transitions, rps area chart and p50-vs-p99 latency chart over a rolling window,
and `steady` / `flash_sale` / `spike` load profiles via `POST /api/traffic/load-test`. The socket
reconnects with exponential backoff and falls back to polling `GET /api/traffic/live`; the connection
mode is always shown in the status bar.

---

## Behavioural telemetry

Every meaningful interaction is routed through `src/hooks/useTracking.ts`:

- `POST /api/events` for `view`, `click`, `search`, `add_to_cart`, `purchase` and `rating`.
- `POST /api/feedback` with the item's `rec_id` whenever a **recommended** item is clicked, added to
  the bag or purchased — this is what closes the self-learning loop.

A `session_id` (uuid) is generated on first load and persisted in `localStorage`; the selected demo
persona is persisted alongside it and sent as `user_id`. Recommendation queries are keyed on the
persona, so switching profiles in the header immediately refetches and re-ranks every rail on screen.
Telemetry calls are fire-and-forget and never surface an error into the UI.

---

## Source layout

```
src/
  components/
    bits/           AnimatedNumber, GradientText, MagneticButton, Marquee,
                    ProductArt, Reveal, SpotlightCard, TextReveal
    common/         ErrorBoundary, Rail, SectionHeading, Skeletons, States
    intelligence/   ChartFrame (+ shared chart theme), DigitalTwinLab,
                    FeedbackPanel, TrafficCenter
    layout/         Header, Footer, Logo, PersonaSwitcher, RootLayout
    product/        ProductCard, RecommendationRail, ExplainDrawer, ReviewList
    three/          HeroScene
    ui/             badge, button, card, dialog (+ sheet), input/select,
                    skeleton, slider, tabs, toast, tooltip
  hooks/            useQueries, useReveal, useSmoothScroll, useTracking, useTrafficStream
  lib/              api (typed client + error shape), types, utils
  pages/            Home, Shop, ProductDetail, Cart, Intelligence, NotFound
  store/            session (session_id + persona), cart, activity
```

## Design notes

Near-black graphite base (`ink-950`) with a single warm amber accent, Inter Tight for UI and
Instrument Serif for editorial accents. Motion is restrained and shares one easing curve
(`cubic-bezier(0.16, 1, 0.3, 1)`) across GSAP and Framer Motion. Lenis drives smooth scrolling
site-wide via the GSAP ticker so ScrollTrigger stays in sync. All motion respects
`prefers-reduced-motion`, and the Three.js scene parks itself when off-screen or backgrounded.
