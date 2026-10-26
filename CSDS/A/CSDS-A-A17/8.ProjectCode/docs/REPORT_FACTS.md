# REPORT FACTS - CropSight (CSDS-A-A17)

Single source of truth for every number in the submission documents. Each figure comes from an `experiments/*/metrics.json` file,
a pytest run, a measured API call, or the code itself. **Nothing here is a literature figure.** Where something was not measured it says so.

Project: *CropSight: Smart Crop Delivery with AI-Based Price and Quality Intelligence* - Department of CSE (Data Science), Batch A17, Section A.
Team: G.PRANAVI (23K91A6765), G.SIRI CHANDANA (23K91A6763), A.NIKHIL (23K91A6715), G.VISHNU VARDHAN (23K91A6754). Guide: K. Mounika.
Base paper (from `3.BASE PAPER.docx`): *AI-Driven Smart Agriculture: An Integrated Approach for Soil Analysis, Irrigation, and Crop-Fertilizer
Recommendations*, IEEE Access, 2025, doi 10.1109/access.2025.3594162 (PDF in `Documentary/`). The base paper is pre-harvest (soil, irrigation, crop-fertiliser);
CropSight applies the same IoT + deep learning + XAI idea post-harvest.

---

## 0. The headline, stated plainly

1. **Both ML models are trained on synthetic data** (the product says so itself in the admin "Model insights" screen). No real crop-image set and no real market-price series were in the project.
   The high scores (quality accuracy 92.3 %, price R2 0.992) measure how well a model recovers the *generator it was trained on*, not performance on farms or markets.
2. **Real-photo check (3,200 real fruit photographs): the shipped quality model does not transfer.** It predicts grade B for 99.8 % of fresh and 99.1 % of rotten fruit;
   mapped to fresh/rotten it is at chance (50.4 %, AUC 0.571). The same 11 computer-vision features, when trained on *real* labels, reach 90.6 % (5-fold CV), so the extractor is sound and the trained classifier is the weak part.
3. The price "forecast" is a model evaluated on a *hash-generated* daily market context, not a time-series forecast; the weather features carry ~0 importance.
4. The IoT stream is a simulator whose alarm, once on, usually stays on (97.3 % of flagged steps are persistent drift, not events).
5. The delivery engine is a transparent weighted score (not trained); its buyer "offers" are hash-derived simulated numbers.
6. What *is* solid: the end-to-end marketplace (roles, order state machine, JWT auth, grading + SHAP + forecast + planner + WebSocket stream), 36 passing tests, measured latencies, and real-time computer-vision feature extraction.

---

## 1. System summary

| Item | Value |
|---|---|
| Backend | Python 3.11.9, FastAPI 0.115.6, SQLAlchemy 2.0.36 (SQLite), Pydantic 2.10.3, JWT (python-jose, HS256), bcrypt (passlib), uvicorn 0.32.1 |
| ML | scikit-learn 1.5.2 (RandomForestClassifier, GradientBoostingRegressor incl. quantile), SHAP 0.46.0 (TreeExplainer), OpenCV 4.10 (headless), scikit-image 0.24 (GLCM), NumPy 1.26.4, pandas 2.2.3 |
| Frontend | React 19.3 + TypeScript, Vite 8.3, Tailwind CSS 4, Framer Motion, GSAP, Lenis, Three.js (React Three Fiber), Recharts, Zustand, React Router |
| Size | backend Python 1,980 lines (app + seed); frontend TS/TSX 3,302 lines; 17 page components, 23 other components |
| Ports as shipped | API 8000, web 5190 (README / `vite.config.ts`, proxy `/api`, `/uploads`, `/ws`); the prompt's 8117/5117 were not used because the product code is unchanged |
| Database | SQLite, 9 tables: `users`, `crop_listings`, `quality_grades`, `towns`, `price_predictions` (model exists, **never written to** by any route), `shipments`, `sensor_readings`, `orders`, `delivery_recommendations` |
| Roles | farmer, buyer, distributor, admin (admin cannot self-register) |
| Endpoints | 21: 20 REST + 1 WebSocket |

**Endpoints**

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | /api/health | any | liveness |
| POST | /api/auth/signup | public | create farmer/buyer/distributor; returns JWT |
| POST | /api/auth/login | public | returns JWT + user |
| GET | /api/auth/me | any | current user |
| POST | /api/crops/upload | farmer | multipart photo (JPEG/PNG/WEBP, max 8 MB) + crop, region, qty -> creates draft listing, extracts CV features, grades, SHAP |
| GET | /api/crops/mine | farmer | own listings |
| GET | /api/crops/{id} | any signed-in | one listing |
| POST | /api/crops/{id}/list?asking_price= | farmer (owner) | publish (status draft -> listed) |
| GET | /api/prices/options | public | crops, regions, grades |
| POST | /api/prices/predict | any signed-in | current price, 15-85 % band, 31-day forecast, best sell day, SHAP |
| GET | /api/delivery/{listing_id}/recommend | farmer (owner) | ranked buyers (top 5), best route, best sell day; stores a row |
| GET | /api/marketplace/listings | any signed-in | listed crops, filter crop/region/grade |
| GET | /api/marketplace/listings/{id} | any signed-in | listing detail |
| POST | /api/marketplace/orders | buyer | place order (listing -> sold) |
| GET | /api/marketplace/orders/mine | any signed-in | role-scoped orders |
| PATCH | /api/marketplace/orders/{id}/status | farmer / distributor / admin | placed -> confirmed -> in_transit -> delivered (or cancelled) |
| GET | /api/iot/shipments | any signed-in | shipments in transit (distributor sees own) |
| GET | /api/iot/shipments/{id}/history | any signed-in | latest 60 sensor rows |
| WS | /api/iot/ws/iot/{id} | none (unauthenticated) | sensor reading every 1.4 s, stored in `sensor_readings` |
| GET | /api/admin/overview | admin | KPIs |
| GET | /api/admin/model-insights | admin | algorithm, accuracy / MAE / R2, importances, training-data disclosure |

**Order state machine:** placed -> {confirmed, cancelled}; confirmed -> {in_transit, cancelled}; in_transit -> {delivered}. confirmed/cancelled: owning farmer or admin; in_transit: any distributor (becomes the order's distributor, creates a `shipments` row with `seed = order_id*97+13`); delivered: assigned distributor or admin.

**Pipelines**

- *Quality:* image -> centre on 256x256 white canvas -> HSV foreground mask (Otsu on saturation, bright-background removal, morphology; falls back to whole image if mask <3 % or >98 %) -> 11 features: mean_hue (circular mean), mean_saturation, mean_value, saturation_std, color_uniformity (=1-2.2*saturation_std), texture_contrast / homogeneity / energy (GLCM, 16 levels, distance 2, 4 angles), edge_density (Canny 60/150), blemish_ratio (pixels darker than mean-1.15 SD), size_score (mask area/0.55) -> Random Forest (250 trees, depth 9, min leaf 4) -> grade A/B/C/Reject + probabilities + top-6 SHAP.
- *Price:* 19 features (month sin/cos, rainfall, temperature, demand index, supply index, fuel index, days to harvest, year trend, grade premium, region factor, 8 crop one-hots) -> GBR point model (300 trees, depth 4, lr 0.06) + two quantile GBRs (alpha 0.15 / 0.85; 250 trees, depth 3). Forecast = point model on a context walked forward 30 days (EWMA 0.8/0.2 of a per-day hash-seeded context). Best sell day = argmax over days 0-14 (spoilage window 14 days). Band = [min(low,current), max(high,current)].
- *Delivery:* score = 0.38 price + 0.22 distance + 0.18 quality fit + 0.14 reliability + 0.08 (1 - spoilage risk), x100; weights sum to 1.00. Offered price = base x (0.90 + 0.28*hash). Distance = haversine between town coordinates; transit days = km/380 + 0.5; spoilage span 5 days for Tomato/Mango/Onion/Potato else 21. Top 5 buyers returned.
- *IoT:* per-shipment seeded random walk (temp +-0.35/step, humidity +-1.2/step, shock |N(0.3,0.25)|) with an injected event every 18-55 steps (temp +4-8 C, humidity +12-20 %, or shock +2.2-4 g); `is_anomaly` if injected, temp outside [0.5, 9.5] C, humidity outside [47, 83] %, or shock >= 2.4 g.

---

## 2. Datasets (all disclosed)

| Dataset | Used for | Source | Licence | Size / split |
|---|---|---|---|---|
| Synthetic quality features | training + evaluating the shipped quality model | generated by `backend/app/ml/quality/generate_dataset.py` (seed 42) | project code | 6,000 rows (1,500 per grade A/B/C/Reject), 11 features; 360 labels (6 %) moved to a neighbouring grade; 80/20 stratified split (4,800 / 1,200) |
| Synthetic market series | training + evaluating the shipped price model | `backend/app/ml/price/generate_dataset.py` (seed 7) | project code | 23,360 rows = 8 crops x 8 regions x every 3rd day, 2022-01-01 to 2024-12-28; price 402-19,176 INR/quintal (mean 3,796); 85/15 random split (19,856 / 3,504) |
| **Fresh and Rotten Fruits** (real photos) | real-photo check of the grading pipeline | Sultana, Jahan, Uddin (2022), *Data in Brief* 44:108552, Mendeley Data doi 10.17632/bdd69gyhv8.1; copy: Hugging Face `Project-AgML/fresh_rotten_fruit_classification` (raw) | CC BY 4.0 | 3,200 images: 8 fruits (apple, banana, grape, guava, jujube, orange, pomegranate, strawberry) x 200 fresh + 200 rotten |
| **Vegetable Classification (Bangladesh)** (real photos) | tomato / onion / potato photos for the demo screens and sample inputs | Hugging Face `Project-AgML/vegetable_classification_bangladesh` | CC BY 4.0 | first 40 tomato, 40 onion, 40 potato images were scanned; 4 were used (`docs/sample_inputs/`) |

The demo database holds 4 buyers, 1 farmer, 1 distributor, 1 admin, 8 towns (`scripts/seed_db.py`) and one **seeded** tomato listing (480 kg, 1,950 INR, grade A, confidence 0.91, empty features) that was *not* graded by the model.
Sample photos were scanned and chosen so the screens show more than one grade; the scan itself is in `docs/sample_inputs/_chosen.json`: all 40 onions -> B, all 40 tomatoes -> B, potatoes 39 B + 1 A.

---

## 3. Measured results

### 3.1 Quality grading - shipped Random Forest on its synthetic test set (`experiments/quality/metrics.json`)

| Metric | Value |
|---|---|
| Test accuracy (1,200 rows, seed 42; identical to `train_model.py` output and the admin screen: 92.3 %) | **0.9233** |
| Macro F1 / weighted F1 | 0.9244 / 0.9227 |
| Train accuracy | 0.9394 |
| Precision / recall / F1 / support, A | 0.928 / 0.964 / 0.946 / 280 |
| B | 0.924 / 0.862 / 0.892 / 325 |
| C | 0.909 / 0.894 / 0.901 / 312 |
| Reject | 0.933 / 0.986 / 0.959 / 283 |
| Errors | 92 of 1,200; **100 % are between neighbouring grades** (never A<->C, A<->Reject, B<->Reject) |
| Confidence (mean max-probability) correct / wrong | 0.869 / 0.788 |
| Accuracy against the clean (pre-noise) labels of the same test rows | 0.9808 (the model recovers the generator; 6 % label noise caps accuracy on noisy labels at 0.9408 if noise is unlearnable) |
| Trained and tested on clean labels | 0.980 |
| Five split/forest seeds | accuracy 0.9286 +- 0.0034 (min 0.925, max 0.932); macro F1 0.9297 +- 0.0034 |

**Confusion matrix** (rows = true, columns = predicted; order A, B, C, Reject):

|  | A | B | C | Reject |
|---|---|---|---|---|
| A | 270 | 10 | 0 | 0 |
| B | 21 | 280 | 24 | 0 |
| C | 0 | 13 | 279 | 20 |
| Reject | 0 | 0 | 4 | 279 |

**Baselines on the same split:** majority class 0.271; logistic regression 0.931; k-NN (k=15) 0.930; decision tree (depth 9) 0.885; histogram gradient boosting 0.922; Random Forest (shipped) 0.923. A linear model matches the forest - the synthetic classes are close to linearly separable.

**Feature importance** (impurity, shown in the admin screen): blemish_ratio 0.241, color_uniformity 0.239, texture_homogeneity 0.156, texture_contrast 0.109, edge_density 0.107, texture_energy 0.040, saturation_std 0.037, mean_saturation 0.027, size_score 0.025, mean_value 0.015, mean_hue 0.004.
Permutation importance (accuracy drop): color_uniformity 0.209, blemish_ratio 0.202, texture_homogeneity 0.081, texture_contrast 0.039, edge_density 0.032.

**Ablation (drop one group):** colour 0.912, texture 0.917, edge density 0.918, blemish 0.923, size 0.923 (full 0.923). **Only one group:** colour 0.850, texture 0.831, blemish 0.750, edge density 0.672, size 0.563.

### 3.2 Quality grading - real photographs (`experiments/real_images/metrics.json`, 3,200 images)

| Check | Result |
|---|---|
| Shipped model, share predicted B: fresh / rotten | 99.81 % / 99.13 % (A 0.13 % / 0.06 %, C 0.06 % / 0.81 %, Reject 0 % / 0 %) |
| Fresh -> {A,B}, rotten -> {C,Reject} accuracy | **0.5038** (chance = 0.5) |
| AUC fresh vs rotten using P(A)+P(B) | **0.571** (per fruit: apple 0.79, banana 0.76, grape 0.51, guava 0.35, jujube 0.19, orange 0.45, pomegranate 0.64, strawberry 0.81 - below 0.5 means inverted) |
| Mean top-class probability | 0.663 |
| Real images outside the 3-SD envelope of every synthetic grade profile | 99.8 % |
| Same 11 features, RF retrained on real fresh/rotten labels, 5-fold CV | accuracy **0.906 +- 0.007**, AUC 0.970 (majority baseline 0.50) |
| Same, leave-fruits-out (4 folds, unseen fruit types) | accuracy 0.669, AUC 0.748 |
| Real-label importance | mean_hue 0.291, mean_saturation 0.122, texture_energy 0.096, mean_value 0.088 ... blemish_ratio 0.033 (the opposite order to the synthetic model) |

Mean feature values: real fresh / real rotten / synthetic A / B / C / Reject - e.g. mean_hue 0.141 / 0.141 / 0.28 / 0.27 / 0.26 / 0.24; texture_contrast 0.023 / 0.018 / 0.18 / 0.30 / 0.46 / 0.64; blemish_ratio 0.145 / 0.140 / 0.02 / 0.07 / 0.15 / 0.30; color_uniformity 0.72 / 0.70 / 0.90 / 0.74 / 0.55 / 0.35 (full table in the JSON).
Caveat: fresh/rotten is a binary freshness label, not an A/B/C/Reject grade; the mapping is this project's assumption, and the fruits are not the app's crop list.

### 3.3 Price model - shipped Gradient Boosting (`experiments/price/metrics.json`)

| Metric | Value |
|---|---|
| Test MAE / RMSE (3,504 rows, INR per quintal) | **164.61 / 252.24** |
| R2 | **0.9916** |
| MAPE | **5.08 %** |
| Noise floor (noise-free formula vs observed price) | MAE 105.5, MAPE 2.80 %, R2 0.9966 - the best any model can do on this data |
| Model vs the noise-free formula | MAE 120.5, MAPE 3.99 %, R2 0.9951 |
| 15-85 % band empirical coverage | **0.693** (nominal 0.70); mean width 1,088 INR (23.1 % of price); 119 test rows where the low model exceeded the high model |
| Five seeds | MAE 162.8 +- 5.5; R2 0.9919 +- 0.0006; MAPE 4.94 % |
| Time hold-out (train 2022-23, test 2024, 7,744 rows) | MAE 191.8, RMSE 309.2, R2 0.988, MAPE 5.12 % |

Baselines (same split) MAE / R2 / MAPE: crop mean 990.0 / 0.719 / 32.8 %; crop x grade mean 714.3 / 0.858 / 20.2 %; linear regression 527.7 / 0.908 / 20.6 %; random forest (200) 245.3 / 0.983 / 7.2 %; GBR (shipped) 164.6 / 0.992 / 5.1 %.
Per crop MAE: Tomato 97, Onion 112, Potato 99, Wheat 118, Rice 158, Mango 250, Cotton 383, Maize 104. Per grade MAPE: A 4.2 %, B 4.2 %, C 5.0 %, Reject 11.4 %.
Grouped importance (admin screen): Crop type 0.715, Quality grade 0.142, Market supply 0.073, Market demand 0.044, Seasonal timing 0.020, Regional factor 0.004, days to harvest 0.001, trend 0.001, fuel 0.0003, **rainfall 0.00009, temperature 0.00005**.
**Served forecast over all 256 crop x region x grade combinations** (`predict_price`): best sell day is day 0 in 24.2 % of cases, mean 6.2 days; waiting to the best day gains a mean 14.6 % (median 8.4 %, max 135.7 %) - an artefact of the hash-generated daily context; mean 30-day range 33.5 % of mean price; A > B > C > Reject price order holds in 64/64 crop-region pairs; mean price A 4,629, B 4,019, C 3,287, Reject 1,763; model latency median 13.1 ms, p95 29.9 ms.
Note: the model is not a time-series forecaster; "forecast" = the point model evaluated on 31 successive hash-generated contexts.

### 3.4 Delivery recommendation (`experiments/delivery/metrics.json`)

256 crop x region x grade combinations, 4 buyers, 8 towns. Weights 0.38 / 0.22 / 0.18 / 0.14 / 0.08 (sum 1.00). Replica of the score matches the served top buyer in 256/256 cases.
Weight perturbation (each weight x U(0.5,1.5), renormalised, 100 trials per case): top-1 buyer unchanged 97.7 % on average (worst case 74 %), mean rank correlation 0.948.
Top buyer share: Harvest & Co. 32.8 %, Coastal Fresh 28.1 %, GreenMart 21.9 %, Riverstone 17.2 %. Mean top score 76.0 (0-100), mean top-to-bottom spread 18.1. Across buyers, distance varies most (SD of weighted term 0.052), then price 0.021; quality fit does not vary across buyers (0) - it is a property of the listing.
Latency (in process) median 64.7 ms, p95 107.1 ms. Offers are simulated (hash factor 0.90-1.18), so "price" differences between buyers are not market information.

### 3.5 IoT simulator (`experiments/iot/metrics.json`; 50 seeds x 1,200 steps)

First flagged step: median 26 (0.61 min at 1.4 s/step), mean 27.1. Share of seeds flagged at step 25 / 50 / 100 / 200 / 400: 18 % / 28 % / 58 % / 86 % / **100 %**; share of all steps flagged 91.6 %.
1,499 injected events (25.0 per 1,000 steps); only 1,499 of 54,985 flagged steps are the injection step itself - **97.3 % of flags are persistent drift** (median longest uninterrupted alarm 1,101 of 1,200 steps; mean final temperature 33.4 C and humidity 94.4 %, clamped at 35 C / 98 %).
Conclusion: once the random walk leaves the band the alarm usually stays on (an in-band spike raises a one-step alert only, as in the live run below); each WebSocket connection also restarts the simulator from its seed, so reopening a shipment replays the same trajectory and writes duplicate history rows.
Live check on shipment #1 (order #3, so seed 3*97+13 = 304, `scripts/capture_alert.py`): the first alert (an injected humidity spike to 77.6 %, flagged because the event step is always flagged; first flag at step 31 = 43.4 s) appeared 44.2 s after opening the page; the in-page red banner was on at 215 s (temperature 9.5 C, humidity 93.7 %), matching the simulator trajectory (sustained alarm from step 133, about 186 s).

### 3.6 Tests (`backend/tests/`, pytest 9.1.1, 30 s)

**36 passed, 3 expected failures (xfail), 0 failed.** Groups: health and auth (8), role guards (1), listings, grading and CV features (12), price (5), delivery (3), marketplace and order lifecycle (5), IoT and simulator (4), admin (1).
The 3 xfail tests document real gaps in the shipped code (they assert the hardened behaviour and fail today):
1. a corrupt file sent with an image content type raises inside `grade_image()` -> HTTP 500, and a **draft listing row with no grade is left behind** (observed: a later test found a gradeless listing);
2. `crop_type` / `region` are not validated: an unknown crop is priced from an all-zero crop one-hot;
3. order quantity and price are not validated (zero, negative, or more than the listing quantity are accepted).
Run: `cd backend && python -m pytest tests -q` (tests use a throw-away SQLite file via `DATABASE_URL`). Test e-mails use `@cropsight.dev` because the e-mail validator rejects `.test`/`.local` domains.

### 3.7 API latency (`experiments/api_latency/metrics.json`; live uvicorn on 127.0.0.1, same machine, other jobs running)

| Endpoint | n | median ms | p95 ms |
|---|---|---|---|
| health | 30 | 1.6 | 4.7 |
| login (bcrypt) | 30 | 325.3 | 349.0 |
| upload + grade (CV + RF + SHAP + DB write; 900x675 JPEG) | 20 | 173.9 | 207.3 |
| price predict (31 days + 2 bands + SHAP) | 30 | 54.9 | 119.4 |
| delivery recommend | 30 | 99.8 | 147.9 |
| marketplace listings | 30 | 17.7 | 36.5 |
| admin overview | 30 | 22.8 | 46.0 |
| admin model insights | 30 | 112.9 | 149.5 |

Hardware: Intel Core i5-12500 (6 cores / 12 threads), 15.7 GB RAM, Windows 11 Pro, no discrete GPU (Intel UHD 770); Python 3.11.9, Node 24.19.0. Training of both models: about 20 s on this machine (quality experiment script 53 s including all baselines).

---

## 4. Defects and limitations found (state them; do not hide them)

1. **Synthetic training data** for both models; the quality model fails on real photos (section 3.2).
2. **Admin "gross transaction volume" unit error:** it sums `agreed_price x quantity_kg`, but prices are INR per **quintal** (100 kg). Demo: 3 orders (900 kg @ 1,640; 1,200 kg @ 1,090; 620 kg @ 2,250) show INR 41,79,000; per-quintal arithmetic gives INR 41,790. The screen overstates by 100x.
3. **Price band clamp:** `confidence_low/high` are clamped to include the point estimate, so the displayed "range" can end exactly at the current price (screen 08: INR 2,068 - 2,272 with price 2,272).
4. **IoT alarm drifts into permanent alarm** (section 3.5); WebSocket endpoint is unauthenticated; any signed-in user can read any shipment's history.
5. **Authorisation gaps:** `GET /api/crops/{id}` and marketplace detail return any listing to any signed-in user; any distributor can start transit on any confirmed order; `POST /orders` does not check quantity or price (xfail test 3).
6. **Secrets:** a default `secret_key` ships in `config.py`; `.env` (Gemini key, unused by the app code) is not read by the product.
7. **Unvalidated catalogue values** (xfail test 2); `PricePrediction` table and `CropListingCreate` schema unused; `on_event("startup")` is deprecated in FastAPI.
8. **Delivery offers are simulated**; reliability scores are seeded constants; transit time uses a fixed 380 km/day.
9. No Gemini / LLM and no Docker; no real sensor hardware; no payment; single-process SQLite.
10. The landing page shows fixed marketing counters (e.g. '38,400+ crops graded', '+17 % uplift', '92 % accuracy', '2,400+ farmers') that are static text, not measured values. The price generator ignores temperature entirely (`true_price` has no temperature term) and uses rainfall only above 150 mm.
10b. `CORS` allows only port 5173 while the UI is served on 5190 (works because the browser talks to the Vite proxy on the same origin).
11. The batch's abstract mentions "deep learning grades crop quality from images"; the shipped grader is **classical machine learning on hand-crafted features** (Random Forest), not a deep network. Documents must say so.

---

## 5. How the numbers were produced

- Drive D: of the build machine was full when the run started (0 bytes free); after approved clean-up of old scratch folders the work was done on a **copy of the unmodified product code on drive C:** (`C:\cs17\app`, own venv and `node_modules`); only scripts, metrics, screenshots, diagrams and documents were written to the batch folder. Product source under `backend/app` and `frontend/src` is unchanged; `backend/tests/` is new.
- `scripts/exp_quality.py`, `exp_price.py`, `exp_delivery_iot.py` (delivery + IoT), `exp_real_images.py`, `measure_api.py`, `pick_sample_photos.py`, `capture_screenshots.py`, `capture_alert.py`; shared setup in `exp_common.py` (env `CS_BACKEND`, `CS_DATA`). Each experiment writes `experiments/<name>/metrics.json`.
- Large real-image shards (about 5.5 GB of parquet) live outside the repository (`C:\cs17\data`) and are re-downloadable from the Hugging Face repos named above.

---

## 6. Screenshot inventory (`docs/screenshots/`, 1440x900, real app, real photos)

The farmer flow of screens 05-18 was driven through the browser UI (Playwright, Chrome); extra listings (onion, two potato lots) and orders that fill the lists were created through the same API the UI uses.
Photo of the featured tomato: `docs/sample_inputs/tomato_1.jpg` (grade B, confidence 70.1 %; forecast 2,272 INR/quintal, best day 9 Nov, #1 buyer Harvest & Co. 67.7 % match).

| File | Shows |
|---|---|
| 01_landing, 01b_landing_full | landing page (counters settled), full length |
| 02_login | log-in with demo-account shortcuts |
| 03_login_error | failure case: wrong password rejected |
| 04_signup | sign-up with role choice |
| 05_farmer_dashboard | farmer dashboard before upload |
| 06_upload_preview | real tomato photo selected, preview |
| 07_grading_result, 07b_grading_full | grade B, 70.1 %, radar + SHAP; full workspace |
| 08_price_forecast, 08b_price_forecast_scrolled | forecast chart, band, best day, SHAP drivers |
| 09_delivery_planner | four ranked buyers, suggested route |
| 10_publish_listing, 11_listing_published | asking price and publishing |
| 12_farmer_listings, 12b_farmer_listings_scrolled | farmer's graded listings |
| 13_marketplace | buyer marketplace (3 listed) |
| 14_listing_detail | quality breakdown and price trend for the buyer |
| 15_place_order_dialog, 16_buyer_orders | place order, order list |
| 17_farmer_orders_placed, 18_farmer_orders_confirmed | farmer confirms |
| 19_distributor_deliveries, 20_distributor_in_transit | distributor start transit |
| 21_live_monitoring_start, 22_live_monitoring | live sensor traces (WebSocket) |
| 22b_live_alert, 22c_live_alert_later | first cold-chain alert toast (44 s); red in-page banner after 215 s with temperature and humidity out of band |
| 23_admin_overview | KPIs (shows the 100x volume overstatement) |
| 24_model_insights, 24b_model_insights_scrolled | model transparency, disclosure of synthetic training data |

`docs/screenshots/_run.json` lists each file with a one-line description.

---

## 7. Git

Batch folder `CSDS/A/CSDS-A-A17`; commits are made with explicit pathspecs (docs, experiments, scripts, tests, screenshots, diagrams, the eleven documents). `.env`, `MASTER_PROMPT*.md`, `2.ABSTRACT.docx` (under `8.ProjectCode`) and `DOCS_PROMPT.md` are not committed.
