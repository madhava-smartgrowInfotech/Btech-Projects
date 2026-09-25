# Nuvara — API Contract (backend ⇄ frontend)

Backend: FastAPI on `http://localhost:8000`, all routes prefixed `/api` (WebSocket at `/ws/traffic`).
CORS must allow `http://localhost:5173` (Vite dev server) with credentials.
All responses are JSON. Timestamps are ISO-8601 UTC strings.

## Catalog

`GET /api/categories` → `[{id, name, slug, product_count}]`

`GET /api/products?category=&q=&sort=&page=&page_size=` →
`{items: [Product], total, page, page_size}`

`Product` = `{id, slug, name, category, subcategory, price, compare_at_price, currency, description, short_description, image_seed, colorway, rating, review_count, stock, tags: [string], attributes: {key: value}, created_at}`

`GET /api/products/{id}` → `Product` with `related_ids: [id]`

`GET /api/products/{id}/reviews?page=` → `{items: [{id, user_name, rating, title, body, created_at, helpful_count}], total}`

## Session / identity

Frontend generates a `session_id` (uuid, persisted in localStorage) and a lightweight demo `user_id` picker (switch between a few synthetic personas to show personalization differences). Both sent as query params or JSON body fields where relevant.

`GET /api/users/demo-personas` → `[{id, name, segment, avatar_seed, blurb}]`

## Behaviour tracking

`POST /api/events` body `{session_id, user_id?, product_id?, type: "view"|"click"|"search"|"add_to_cart"|"purchase"|"rating"|"review", query?, value?, rec_id?, source_agent?}` → `{ok: true, event_id}`

## Recommendations (multi-agent)

`GET /api/recommendations?user_id=&session_id=&context=home|product|cart|search&product_id=&limit=12` →
```
{
  strategy: {name, weights: {collaborative, content, trending, diversity}},
  items: [{
    product: Product,
    rec_id: string,          // unique id for this recommendation impression, used in feedback + explain
    score: number,
    reason: string,          // short human reason, e.g. "Because you viewed Aria Desk Lamp"
    agents: {collaborative: number, content: number, trending: number, diversity_bonus: number},
    confidence: number
  }]
}
```

`GET /api/recommendations/{rec_id}/explain` →
```
{
  rec_id, product: Product,
  headline: string,
  agent_breakdown: [{agent: "collaborative"|"content"|"trending", weight, raw_score, contribution, narrative}],
  similar_because: [{product: Product, similarity, shared_signal}],
  audience_fit: {segment, percentile}
}
```

## Feedback / self-learning

`POST /api/feedback` body `{session_id, user_id?, rec_id, action: "click"|"add_to_cart"|"purchase"|"dismiss"|"ignore"}` →
`{ok: true, updated_weights: {collaborative, content, trending, diversity}, learning_step}`

`GET /api/feedback/weights-history?limit=50` → `[{step, timestamp, weights, trigger_action}]` (time series for a chart)

## Digital Twin simulation lab

`POST /api/simulate` body `{name, weights: {collaborative, content, trending, diversity}, population_size?, rounds?}` →
```
{
  run_id, name, weights,
  baseline: {ctr, conversion_rate, avg_order_value, catalog_coverage, diversity_index},
  candidate: {ctr, conversion_rate, avg_order_value, catalog_coverage, diversity_index},
  lift: {ctr_pct, conversion_pct, revenue_pct},
  timeline: [{round, baseline_ctr, candidate_ctr}],
  segment_breakdown: [{segment, baseline_ctr, candidate_ctr}],
  verdict: "deploy"|"hold"|"reject",
  narrative: string
}
```

`GET /api/simulate/history?limit=20` → `[{run_id, name, weights, verdict, lift, created_at}]`

`POST /api/simulate/{run_id}/deploy` → `{ok, live_weights}` (sets this run's weights as the live orchestrator strategy)

## Traffic / load control center

`GET /api/traffic/live` → `{rps, p50_latency_ms, p99_latency_ms, queue_length, cache_hit_rate, active_workers, autoscale_target, status: "nominal"|"elevated"|"critical", updated_at}`

`POST /api/traffic/load-test` body `{profile: "steady"|"flash_sale"|"spike", duration_s}` → `{ok, test_id}` — kicks off a background simulated traffic profile that drives the numbers `GET /api/traffic/live` and the WebSocket report for `duration_s` seconds.

`WS /ws/traffic` → server pushes a JSON snapshot (same shape as `/api/traffic/live`) roughly once per second. Frontend must reconnect with backoff if the socket drops, and fall back to polling `/api/traffic/live` if WS is unavailable.

## Error shape

All errors: `{detail: string}` with appropriate HTTP status code.

## Notes for both sides

- No authentication system needed — this is a demo storefront with switchable synthetic personas, not real accounts.
- All "AI" is genuine, runnable Python logic (real cosine similarity / TF-IDF / weighted scoring / online weight updates) — not hardcoded fake numbers. Numbers must visibly change when weights or feedback change.
- The product must never expose academic/coursework language anywhere in the UI or copy (no "project", "batch", "submitted by", "B.Tech", "abstract", etc.). It reads as a real consumer product called **Nuvara**, with an internal-looking ops console called **Nuvara Intelligence**.
