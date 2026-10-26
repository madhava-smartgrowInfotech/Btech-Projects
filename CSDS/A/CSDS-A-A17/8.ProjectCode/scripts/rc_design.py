"""Chapter 5 content: architecture, workflow, DFDs, UML, database, modules, user interface; plus the diagram registry (CropSight).

Diagrams are drawn by scripts/make_diagrams.py from the real routers, models and ml modules; each paragraph below was checked against
the picture and against backend/app.
"""
from __future__ import annotations

from doc_common import DIAG, SHOTS

ORDER = ["architecture", "workflow", "dfd0", "dfd1", "dfd2", "usecase", "sequence", "er", "uml", "flowchart"]

DIAGRAMS = {
    "architecture": ("01_system_architecture.png", "System architecture of CropSight",
                     ["The diagram shows five layers. At the top are the four kinds of user, each working in a browser: the farmer uploads a photo, forecasts the "
                      "price, plans delivery and publishes; the buyer browses the marketplace and places orders; the distributor starts transit and watches the "
                      "live sensor stream; the admin sees platform figures and model insights. Below them is the React 19 web application served by Vite on port "
                      "5190, which proxies `/api`, `/uploads` and `/ws` to the backend. It has role-based pages, Recharts charts (quality radar, SHAP bars, price "
                      "forecast with its band, live sensor traces), a data layer (Axios with the bearer token, a Zustand authentication store and the WebSocket "
                      "client) and the user-interface kit.",
                      "The backend is a FastAPI application on port 8000. Its REST routers (`auth`, `crops`, `prices`, `delivery`, `marketplace`, `iot`, `admin` and "
                      "`health`) and one WebSocket route call seven building blocks: security (JWT and bcrypt, `require_roles`), the image feature extractor, the "
                      "quality grader (Random Forest with SHAP), the price model (gradient boosting with two quantile models, a 31-day forecast and SHAP), the "
                      "delivery scorer, the sensor simulator and the order state machine. SQLAlchemy maps nine models to SQLite; the joblib model files are loaded "
                      "once and cached. Storage is local: the `cropsight.db` file, the two model artefacts with their synthetic CSV datasets, and the uploaded photos. "
                      "The shaded box marks the sensor source as simulated: no hardware is connected."]),
    "workflow": ("02_high_level_workflow.png", "High-level workflow",
                 ["The ten steps follow one crop from the field to delivery. Steps 1 to 5 belong to the farmer: upload the photo with crop type and quantity, grade "
                  "it (11 features, Random Forest, SHAP), forecast the price, plan delivery and publish the listing. Step 6 is the buyer's order, which marks the "
                  "listing sold. Step 7 is the owning farmer's confirmation. Steps 8 to 10 belong to the distributor: start transit, which creates a shipment; watch "
                  "the live sensor stream; and mark the order delivered. Every step is a role-checked API call and the order moves only along placed, confirmed, "
                  "in transit and delivered. The note at the bottom states that the models were trained on synthetic data and the sensor stream is simulated."]),
    "dfd0": ("03_dfd_level0.png", "Data-flow diagram, level 0 (context)",
             ["At the highest level CropSight is one process with five external entities. The farmer sends sign-up or login details, the crop photo, crop type, "
              "quantity, asking price and order confirmations, and receives the grade with its SHAP explanation, the price forecast, the ranked buyers and the "
              "orders. The buyer sends filters and orders and receives listings with grade, price trend and order status. The distributor sends login, start-transit "
              "and delivered actions and receives orders to ship and the live readings and alerts. The admin sends login and KPI or model-insight requests and "
              "receives user, listing and order totals, gross volume, and each model's accuracy or R2 and feature importances. The simulated sensor stream "
              "(`ShipmentSensorState`) supplies a temperature, humidity and shock reading every 1.4 seconds."]),
    "dfd1": ("04_dfd_level1.png", "Data-flow diagram, level 1",
             ["Level 1 splits CropSight into seven processes: authenticate and authorise (1.0), grade crop from a photo (2.0), forecast price (3.0), plan delivery "
              "(4.0), marketplace and orders (5.0), monitor shipments (6.0) and admin analytics (7.0). Six data stores hold the users (D1), the listings and grades "
              "(D2), the orders (D3), the shipments and sensor readings (D4), the stored delivery recommendations (D5) and the model files with the uploaded photos "
              "(D6). Process 1.0 issues the token and checks role and ownership for every call to processes 2.0 to 7.0. Process 2.0 reads the quality model "
              "from D6 and writes D2; 3.0 reads the price model from D6; 4.0 reads D2, the buyers in D1 and the towns, and writes D5; 5.0 reads D2 and writes D3 and "
              "the listing status; 6.0 receives readings from the simulated source and writes D4; 7.0 reads D1 to D3 and the two model files. Admin analytics is "
              "read-only."]),
    "dfd2": ("05_dfd_level2.png", "Data-flow diagram, level 2: Grade crop (process 2.0)",
             ["Process 2.0 is expanded into nine steps that follow the code of `upload_crop()` and `grade_image()`. The type (JPEG, PNG or WEBP) and the size (8 MB at "
              "most) are validated first (2.1); a failure returns HTTP 400. The photo is saved under a random file name and a draft listing is created (2.2). The "
              "image is decoded and centred on a 256 x 256 white canvas (2.3). A foreground mask is made by Otsu thresholding on saturation, removal of bright "
              "low-saturation background and morphological opening and closing; if the mask covers less than 3 % or more than 98 % of the image, the whole image is "
              "used instead (2.4). Colour features are computed in HSV space: circular mean hue, mean saturation, mean value, saturation spread and colour "
              "uniformity (2.5). Three GLCM texture statistics and the edge density follow (2.6), then the blemish ratio and the size score (2.7). The 11 features "
              "go to the Random Forest, which returns class probabilities; the grade is the most probable class (2.8). SHAP gives the six strongest contributions "
              "and the result is stored as a `QualityGrade` row and returned (2.9)."]),
    "usecase": ("08_use_case_diagram.png", "Use-case diagram",
                ["Every actor first signs up or logs in. The farmer can upload and grade a crop photo, view the SHAP explanation of the grade, forecast the price and "
                 "best day to sell, plan delivery, publish a listing with an asking price, and confirm or cancel an order. The buyer can browse and filter the "
                 "marketplace, place an order and view their orders. The distributor can start transit, monitor the live sensor stream and mark an order "
                 "delivered. The admin can view platform KPIs and the model insights. In the code the admin may also confirm, cancel or deliver any order; the "
                 "diagram shows the use cases each role performs in normal operation. Admin accounts are seeded, not self-registered."]),
    "sequence": ("09_sequence_diagram.png", "Sequence diagram: from photo upload to delivery",
                 ["The sequence shows the main flow in 24 steps across seven participants. The farmer chooses a photo and presses Grade; the web app posts the multipart "
                  "request with the bearer token to `/api/crops/upload`. The API decodes the token, applies `require_roles(\"farmer\")` and checks type and size (3), saves "
                  "the file and inserts a draft `CropListing` (4), calls `grade_image()` on the machine-learning services (5), inserts the `QualityGrade` (6) and returns "
                  "the listing (7). The web app then calls `/api/prices/predict` (8 to 10) and `/api/delivery/{id}/recommend` (11 to 13), after which the farmer publishes "
                  "the listing (14). The buyer posts an order, which inserts an `Order` in the placed state and marks the listing sold (15, 16). The farmer confirms "
                  "(17); the distributor starts transit, which inserts a `Shipment` whose seed is 97 times the order id plus 13 (18, 19) and opens the WebSocket (20); "
                  "every 1.4 seconds the simulator produces a reading that is stored and pushed to the browser (21 to 23). Finally the distributor marks the order delivered "
                  "and the shipment stage becomes delivered (24)."]),
    "er": ("06_er_diagram.png", "Entity-relationship diagram (9 tables)",
           ["Nine tables are created by SQLAlchemy in SQLite. A user (farmer) owns many crop listings; each listing has at most one quality grade, many delivery "
            "recommendations and, once sold, orders. An order refers to a listing and to a buyer, and optionally to the distributor who took it; a shipment refers "
            "to an order and a distributor, and a shipment has many sensor readings. The `towns` table holds the eight market towns with coordinates and is joined "
            "to users and listings by region name only, not by a foreign key. The `price_predictions` table is drawn dashed: the model and table exist, but no "
            "route writes to it. No foreign key has an `ON DELETE` rule."]),
    "uml": ("07_uml_class_diagram.png", "UML class diagram",
            ["The upper part shows the domain model, the nine SQLAlchemy entities with their main attributes and associations (a user has many listings; a listing "
             "has one quality grade, many orders and many recommendations; an order has one shipment; a shipment has many sensor readings; `Order` points to users twice, as "
             "buyer and as distributor). `PricePrediction` is marked as never written and `Town` is matched to users by region name only. The lower part shows the boundary "
             "classes, the seven FastAPI routers with their routes, and the engine classes behind them: `FeatureExtractor` with the 11 feature names and the 256-pixel "
             "target size; `QualityInference` with the Random Forest (250 trees, depth 9) and the SHAP explainer; `PriceInference` with the point and two quantile "
             "models, the 30-day horizon and the 14-day spoilage window; `DeliveryRecommender` with the five weights and the perishable-crop set; "
             "`ShipmentSensorState`; and `Security`. Arrows show which router uses which engine."]),
    "flowchart": ("10_algorithm_flowchart.png", "Flowcharts of the two core algorithms: grade_image() and recommend()",
                  ["The left flowchart is the grading algorithm. Two decisions guard the input: an unsupported type or a file over 8 MB is rejected with HTTP 400. The "
                   "image is decoded, centred and masked; the third decision handles a failed mask by using the whole image. Eleven features are computed, the Random "
                   "Forest returns probabilities, the grade is the most probable class, SHAP gives the top six contributions, and the `QualityGrade` row is stored.",
                   "The right flowchart is the delivery recommender. It first calls `predict_price()` to obtain the reference price and the best sell day (argmax of the "
                   "forecast over days 0 to 14). For every buyer it computes the haversine distance between the two towns (or 50 plus a hash times 400 km when a town is "
                   "missing), a simulated offered price of the base price times 0.90 to 1.18, the transit time as distance over 380 km per day plus half a day, and the "
                   "spoilage risk against a 5-day span for perishable crops (21 days otherwise). The five terms, each in [0, 1], are combined as 100 x (0.38 price + 0.22 "
                   "distance + 0.18 quality fit + 0.14 reliability + 0.08 (1 - spoilage risk)). The loop repeats while buyers remain; the list is sorted, the top five are "
                   "kept, the best route is the top buyer's town, and the recommendation is stored."]),
}


def diagram(d, key, width=None):
    fname, caption, paras = DIAGRAMS[key]
    d.figure(DIAG / fname, caption, width=width, max_h=3.9 if getattr(d, 'report', False) else 4.5)
    for p in paras:
        d.p(p)


def sec_arch(d):
    d.h2("System Architecture")
    d.p("CropSight is a single-machine web application: a React front end, a FastAPI back end, a SQLite database, two trained scikit-learn "
        "models and a sensor simulator. No external service is called. The figure below shows the layers.")
    diagram(d, "architecture")
    d.p("The design follows five principles. **Explain every prediction**: the grade and the forecast each return the SHAP contributions that "
        "produced them, so the farmer sees the drivers and not only the result. **Keep scoring transparent**: the buyer ranking is a stated weighted "
        "sum, not a second black-box model. **Enforce roles on the server**: the web app hides screens a role should not see, but the "
        "decision is made by `require_roles` in the API and by the order state machine. **Keep the heavy work local**: image analysis, the models "
        "and the SHAP explanations run on the CPU in the same process. **Isolate what is simulated**: the market context for the price forecast "
        "(`market_context()`) and the sensor stream (`ShipmentSensorState`) are the only two places where data is generated instead of read, so "
        "a real weather and price feed or real sensors could replace them without changing the routes.")


def sec_workflow(d):
    d.h2("High-Level Workflow")
    diagram(d, "workflow")


def sec_dfd(d):
    d.h2("Data-Flow Diagrams")
    d.p("The data-flow diagrams show how data moves through CropSight at three levels of detail: the context (level 0), the seven main processes "
        "with their data stores (level 1) and the expansion of the grading process (level 2).")
    diagram(d, "dfd0")
    diagram(d, "dfd1")
    diagram(d, "dfd2")


def sec_uml(d):
    d.h2("UML Diagrams")
    d.p("Three UML views describe the design: the use-case diagram (who does what), the class diagram (what the code contains) and the sequence "
        "diagram (how the main flow runs). The two core algorithms are shown as flowcharts in Chapter 6.")
    diagram(d, "usecase")
    diagram(d, "uml")
    diagram(d, "sequence")


def sec_database(d):
    d.h2("Database Design")
    d.p("The database is SQLite, created by SQLAlchemy 2 at start-up with `create_all`; there are no migrations. Results that are read and written "
        "whole (class probabilities, features, SHAP explanations, forecasts, ranked buyers) are stored as JSON columns. Uploaded photographs "
        "are stored as files under `app/data/uploads` with random names, and the table keeps only the path.")
    diagram(d, "er")
    d.table([["Table", "Purpose", "Key columns"],
             ["users", "Accounts of all four roles", "id, name, email (unique, indexed), hashed_password (bcrypt), role (farmer, buyer, distributor, admin), region, phone, reliability_score (default 4.5), created_at"],
             ["crop_listings", "A graded crop lot", "id, farmer_id (FK users), crop_type, region, quantity_kg, image_path, status (draft, listed, sold), asking_price, created_at"],
             ["quality_grades", "Grade of a listing", "id, listing_id (FK), grade (A, B, C, Reject), confidence, probabilities (JSON), features (JSON, 11 values), shap_explanation (JSON), created_at"],
             ["towns", "Eight market towns", "id, name, region, lat, lon, is_market"],
             ["price_predictions", "Defined for stored forecasts; never written by any route", "id, listing_id (FK, nullable), crop_type, region, grade, current_price, confidence_low/high, forecast (JSON), shap_explanation (JSON), best_sell_day, created_at"],
             ["delivery_recommendations", "Stored delivery plan", "id, listing_id (FK), ranked_buyers (JSON), best_route (JSON), best_sell_day, created_at"],
             ["orders", "A buyer's order", "id, listing_id (FK), buyer_id (FK users), distributor_id (FK users, nullable), quantity_kg, agreed_price, status (placed, confirmed, in_transit, delivered, cancelled), created_at, updated_at"],
             ["shipments", "A transit of one order", "id, order_id (FK, nullable), distributor_id (FK, nullable), origin, destination, stage (storage, in_transit, delivered), seed, created_at"],
             ["sensor_readings", "One simulated reading", "id, shipment_id (FK), temperature_c, humidity_pct, shock_g, is_anomaly, recorded_at"]],
            "Database tables", widths=[0.17, 0.25, 0.58], font=9)
    d.p("Two design points should be noted. First, the schema keeps the quality grade in its own table with a one-to-one relationship to the listing, "
        "so a listing can exist as a draft before it is graded; if grading fails after the draft is saved, the draft remains without a grade, which is one of the "
        "known gaps. Second, no foreign key declares an `ON DELETE` rule and passwords are never stored in clear text: `hashed_password` holds a bcrypt hash.")


def sec_modules(d):
    d.h2("Module Design")
    d.table([["Module", "Code", "Responsibility"],
             ["Application", "backend/app/main.py", "Creates the FastAPI app, CORS, the `/uploads` static mount, the start-up table creation and the `/api/health` route; includes the seven routers"],
             ["Configuration and database", "app/core/config.py, database.py", "Settings (secret, algorithm, token lifetime, database URL), engine, session dependency"],
             ["Security", "app/core/security.py", "bcrypt hashing, HS256 JWT creation and decoding, `get_current_user`, `require_roles`"],
             ["Auth API", "app/api/auth.py", "Sign-up for farmer, buyer or distributor, login, current user"],
             ["Crops API", "app/api/crops.py", "Upload with validation, grading, own listings, listing detail, publish"],
             ["Prices API", "app/api/prices.py", "Catalogue options and price prediction (uses the listing's grade when a listing is given)"],
             ["Delivery API", "app/api/delivery.py", "Owner-only recommendation, stored as a row"],
             ["Marketplace API", "app/api/marketplace.py", "Listings with filters, orders, role-scoped order list, status transitions that create shipments"],
             ["IoT API", "app/api/iot.py", "Shipments in transit, last 60 readings, WebSocket stream that stores each reading"],
             ["Admin API", "app/api/admin.py", "Platform counts and gross volume; model cards with importances and training-data disclosure"],
             ["Quality pipeline", "app/ml/quality/", "`feature_extraction.py` (11 features), `generate_dataset.py` (synthetic profiles), `train_model.py` (Random Forest), `infer.py` (grade, probabilities, SHAP)"],
             ["Price pipeline", "app/ml/price/", "`features.py` (catalogue, 19 features, market context, price formula), `generate_dataset.py`, `train_model.py` (point and two quantile models), `infer.py` (forecast, best day, SHAP)"],
             ["Delivery engine", "app/ml/delivery/recommend.py", "Weighted score, haversine distance, transit time, spoilage risk, top five buyers and best route"],
             ["Sensor simulator", "app/ml/iot/simulate.py", "Seeded random walk with injected anomalies and the alert rule"],
             ["Models and schemas", "app/models/, app/schemas/", "Nine SQLAlchemy models and the Pydantic request and response types"],
             ["Seed script and tests", "scripts/seed_db.py, tests/", "Demo accounts, towns and one sample listing; 39 pytest tests"],
             ["Web application", "frontend/src/", "17 page and layout components in six groups (marketing, auth, farmer, buyer, distributor, admin), 23 shared components, the API client, the authentication store and the types"]],
            "Modules of CropSight", widths=[0.19, 0.27, 0.54], font=9)
    d.p("The package `app/ml/explain/` exists but is empty: SHAP is called directly inside the two inference modules.")


def sec_ui(d):
    d.h2("User Interface Design")
    d.paras(
        "The web application has one landing page, a log-in page and a sign-up page, and a sidebar layout for each role. The farmer has a dashboard "
        "(upload form and own listings), a listing workspace (grade, price forecast, delivery planner, publication) and an orders page. The buyer has "
        "the marketplace, a listing detail page with an order dialog, and an orders page. The distributor has an active-deliveries page and a live "
        "monitoring page. The admin has an overview and a model-insights page. A route guard sends a user who opens another role's address back to "
        "their own home page.",
        "Design decisions follow from the users. Every grade is shown with a badge, the confidence and a six-axis quality radar next to the SHAP bars that "
        "explain it. The forecast chart shows the confidence band and marks the best day to sell. The live monitoring page draws three sensor traces, shows "
        "a banner while the latest reading is out of range, and raises a toast when an alert begins. The admin model-insights page prints the algorithm, the "
        "measured accuracy, the feature importances and a sentence stating that the training data were synthetic. Colour is paired with text labels "
        "and the layout adapts to narrow screens.",
        "One limitation of the interface should be stated: the statistics on the landing page (crops graded, price uplift, grading accuracy, farmers onboarded) "
        "and its price ticker are fixed marketing text in the page source, not measurements, and the figures in this report are the measured ones. "
        "The sign-in page also offers one-click demo accounts for the four roles. The screens below were captured from the running application with real crop "
        "photographs; the complete set is in Chapter 8 and Appendix C.")
    d.figure_pair([(SHOTS / "02_login.png", "Log-in page with demo-account shortcuts"),
                   (SHOTS / "05_farmer_dashboard.png", "Farmer dashboard: upload form and own listings")])
    d.figure_pair([(SHOTS / "07_grading_result.png", "Listing workspace: grade, confidence, quality radar and SHAP bars"),
                   (SHOTS / "13_marketplace.png", "Buyer marketplace with grade badges and asking prices")])
    d.figure_pair([(SHOTS / "19_distributor_deliveries.png", "Distributor: confirmed orders ready to ship"),
                   (SHOTS / "22c_live_alert_later.png", "Live monitoring with the out-of-range banner")])
    d.figure_pair([(SHOTS / "23_admin_overview.png", "Admin overview: counts and gross volume"),
                   (SHOTS / "24_model_insights.png", "Admin model insights with training-data disclosure")])
