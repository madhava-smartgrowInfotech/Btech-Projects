# Nuvara — Backend

Storefront and intelligence services for Nuvara. FastAPI, SQLite, numpy and
scikit-learn. Serves the catalogue, the multi-agent recommender, the
explainability layer, the self-learning feedback loop, the digital twin
simulation lab and the live traffic control centre.

## Setup

From the `backend` directory.

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

The API is then on `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs` and the traffic socket at
`ws://localhost:8000/ws/traffic`. CORS is open to `http://localhost:5173`
with credentials, which is where the storefront runs in development.

The first boot creates `nuvara.db` and seeds it: 148 products across 8
categories, ~1,400 written reviews, a 50-shopper population and their
behaviour stream. Seeding is deterministic from a fixed seed, so every
environment gets the same catalogue and the same intelligence numbers.
Delete `nuvara.db` to reseed from scratch.

## Architecture

Nuvara ranks with four independent signals and a live weight vector that the
product itself learns. The **collaborative agent** builds a shopper × product
interaction matrix weighted by event strength (view 1, click 2, add-to-cart 3,
rating = stars, purchase 5) and derives item-item cosine similarity, scoring a
shopper by multiplying their own interaction row through it. The **content
agent** runs TF-IDF over every listing's name, descriptions, tags, category and
attributes, and compares each product against the interaction-weighted centroid
of what the shopper has touched — or against the current product on a detail
page, or a raw query string on search. The **trending agent** is
recency-weighted demand on a 12-day half-life, held globally and per category.
The **orchestrator** max-normalises all three inside a candidate pool, blends
them by the live weights, and finishes with MMR re-ranking whose trade-off
strength is the `diversity` weight, so a list cannot collapse into eight
variations of one product. Every returned item carries a `rec_id`, its
per-agent breakdown, a written reason and a confidence derived from how much
history backs the shopper, how far the item sits above the rest of the pool,
and how strongly the agents agree.

Those `rec_id`s are what make the rest of the system honest. The
**explainability layer** replays the exact scoring record captured when the
list was built — weights, raw scores, contributions — alongside the specific
past products that drove the score, the TF-IDF terms they share, and which
shopper segment over-indexes on the pick. The **feedback loop** attributes an
incoming click, add-to-cart, purchase or dismiss back to the agents that
actually produced that recommendation and nudges the live blend with an
exponential-weights (Hedge) update, clamped above a floor and renormalised, with
every step appended to a persisted weight history. Before any blend goes live,
the **digital twin** replays the whole synthetic population against both the
current weights and a proposed candidate under common random numbers, deciding
simulated clicks and purchases from the same hidden latent taste vectors that
generated each shopper's real history — so a better-targeted blend genuinely
earns its lift — and returns CTR, conversion, order value, catalogue coverage
and diversity for both arms with a deploy / hold / reject verdict. Separately,
the **traffic control centre** advances a small queueing model once a second:
demand builds a queue against finite worker throughput, the queue drives
latency, autoscaling adds workers with a deliberate lag, and sustained load
warms the cache which shortens service time. Load-test profiles reshape the
incoming demand curve and every downstream number follows from the model rather
than from a script.

## Routes

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Service and engine status |
| GET | `/api/categories` | Categories with product counts |
| GET | `/api/products` | Paged catalogue with `category`, `q`, `sort` |
| GET | `/api/products/{id}` | Product detail with `related_ids` |
| GET | `/api/products/{id}/reviews` | Paged reviews |
| GET | `/api/users/demo-personas` | The eight switchable personas |
| POST | `/api/events` | Behaviour ingestion, folded straight into the agents |
| GET | `/api/recommendations` | Ranked list for `home`/`product`/`cart`/`search` |
| GET | `/api/recommendations/{rec_id}/explain` | Full scoring breakdown |
| POST | `/api/feedback` | Applies the Hedge weight update |
| GET | `/api/feedback/weights-history` | Weight time series |
| POST | `/api/simulate` | Run a candidate blend against the live one |
| GET | `/api/simulate/history` | Past runs |
| GET | `/api/simulate/{run_id}` | Full stored run |
| POST | `/api/simulate/{run_id}/deploy` | Promote that run's weights to live |
| GET | `/api/traffic/live` | Current traffic snapshot |
| GET | `/api/traffic/history` | Recent snapshots for chart backfill |
| POST | `/api/traffic/load-test` | `steady`, `flash_sale` or `spike` |
| WS | `/ws/traffic` | Snapshot pushed roughly once a second |

Errors are always `{"detail": "..."}` with an appropriate status code.

## Layout

```
backend/
  app/
    main.py              FastAPI app, CORS, startup seeding, traffic socket
    config.py            Seed, weight floors, learning rate, traffic constants
    db.py  models.py     SQLAlchemy engine and tables
    schemas.py           Request and response contracts
    catalog_data.py      Merchandising vocabulary the generator composes from
    seed.py              Deterministic catalogue, population and behaviour stream
    recommender/
      collaborative.py   Interaction matrix and item-item cosine similarity
      content.py         TF-IDF listing similarity
      trending.py        Recency-weighted demand
      diversity.py       MMR re-ranking
      orchestrator.py    Blending, candidate pools, reasons, impression store
      explain.py         Per-recommendation scoring breakdown
      feedback_engine.py Hedge weight updates from live feedback
      digital_twin.py    Population simulation and verdicts
      traffic_manager.py Queueing model and load-test profiles
    routers/             HTTP surface, all mounted under /api
```
