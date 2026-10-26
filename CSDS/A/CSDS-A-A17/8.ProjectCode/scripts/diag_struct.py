"""ER, UML class, use-case and sequence diagrams for CropSight (drawn from backend/app/models, ml and api)."""
from __future__ import annotations

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor


# --------------------------------------------------------------------------- ER
def _table(c, x, top, w, name, cols, fc=BLUE_L, fs=6.0):
    h = 4.2 + 2.55 * len(cols)
    y = top - h
    c.box(x, y, w, h, "", fc="white", r=1.2)
    c.box(x, y + h - 4.2, w, 4.2, name, fc=fc, bold=True, fs=7.6, r=1.2)
    for i, col in enumerate(cols):
        c.text(x + 1.2, y + h - 6.0 - 2.55 * i, col, fs=fs, ha="left")
    return {"x": x, "y": y, "w": w, "h": h}


def er(out):
    c = Canvas(10.4, 11.2)
    W = 22
    X = [1.5, 27.5, 53.5, 79.5]
    R1, R2, R3 = 109, 70, 35
    _table(c, X[1], R1, W, "delivery_recommendations", ["PK id", "FK listing_id -> crop_listings", "ranked_buyers (JSON)", "best_route (JSON)", "best_sell_day", "created_at"], GREEN_L)
    _table(c, X[2], R1, W, "price_predictions", ["PK id", "FK listing_id (nullable)", "crop_type, region, grade", "current_price", "confidence_low", "confidence_high", "forecast (JSON)", "shap_explanation (JSON)", "best_sell_day", "created_at"], GREY_L)
    _table(c, X[0], R2, W, "users", ["PK id", "name", "email (unique, index)", "hashed_password", "role", "region", "phone", "reliability_score", "created_at"], BLUE_L)
    _table(c, X[1], R2, W, "crop_listings", ["PK id", "FK farmer_id -> users", "crop_type", "region", "quantity_kg", "image_path", "status (draft|listed|sold)", "asking_price", "created_at"], AMBER_L)
    _table(c, X[2], R2, W, "quality_grades", ["PK id", "FK listing_id -> crop_listings", "grade (A|B|C|Reject)", "confidence", "probabilities (JSON)", "features (JSON)", "shap_explanation (JSON)", "created_at"], AMBER_L)
    _table(c, X[3], R2, W, "towns", ["PK id", "name", "region", "lat, lon", "is_market"], GREY_L)
    _table(c, X[1], R3, W, "orders", ["PK id", "FK listing_id -> crop_listings", "FK buyer_id -> users", "FK distributor_id -> users", "quantity_kg", "agreed_price", "status", "created_at", "updated_at"], ROSE_L)
    _table(c, X[2], R3, W, "shipments", ["PK id", "FK order_id -> orders", "FK distributor_id -> users", "origin, destination", "stage (storage|in_transit|delivered)", "seed", "created_at"], ROSE_L)
    _table(c, X[3], R3, W, "sensor_readings", ["PK id", "FK shipment_id -> shipments", "temperature_c", "humidity_pct", "shock_g", "is_anomaly", "recorded_at"], ROSE_L)

    def card(a, b, la="1", lb="N", fs=7):
        c.text(a[0], a[1], la, fs=fs, bold=True, color=INDIGO)
        c.text(b[0], b[1], lb, fs=fs, bold=True, color=INDIGO)

    y = 61
    c.line((X[0] + W, y), (X[1], y)); card((X[0] + W + 1.0, y + 1.6), (X[1] - 1.0, y + 1.6))          # users 1 - N listings
    c.line((X[1] + W, y), (X[2], y)); card((X[1] + W + 1.0, y + 1.6), (X[2] - 1.0, y + 1.6), "1", "1")  # listing 1 - 1 grade
    c.line((X[1] + 11, R2), (X[1] + 11, 109 - 4.2 - 2.55 * 6)); card((X[1] + 12.4, R2 + 1.8), (X[1] + 12.4, 109 - 4.2 - 2.55 * 6 - 1.6))  # listing 1 - N delivery_recs
    c.path([(X[1] + 19, R2), (X[1] + 19, R2 + 2.1), (X[2] + 8, R2 + 2.1), (X[2] + 8, R1 - 4.2 - 2.55 * 10)], head=False, ls="--")           # listing - price_predictions
    card((X[1] + 20.3, R2 + 3.7), (X[2] + 9.4, R1 - 4.2 - 2.55 * 10 - 1.6))
    c.line((X[1] + 11, R2 - (4.2 + 2.55 * 9)), (X[1] + 11, R3)); card((X[1] + 12.4, R2 - (4.2 + 2.55 * 9) - 1.8), (X[1] + 12.4, R3 + 1.6))  # listing 1 - N orders
    c.path([(X[0] + 8, R2 - (4.2 + 2.55 * 9)), (X[0] + 8, 20), (X[1], 20)], head=False); card((X[0] + 9.4, R2 - (4.2 + 2.55 * 9) - 1.8), (X[1] - 1.4, 21.5))   # users - orders (buyer, distributor)
    c.line((X[1] + W, 21), (X[2], 21)); card((X[1] + W + 1.0, 22.6), (X[2] - 1.0, 22.6), "1", "N")      # orders 1 - N shipments
    c.line((X[2] + W, 21), (X[3], 21)); card((X[2] + W + 1.0, 22.6), (X[3] - 1.0, 22.6))                # shipments 1 - N readings
    c.path([(X[0] + 3, R2 - (4.2 + 2.55 * 9)), (X[0] + 3, 5.5), (X[2] + 17, 5.5), (X[2] + 17, R3 - (4.2 + 2.55 * 7))], head=False)           # users - shipments
    card((X[0] + 4.4, R2 - (4.2 + 2.55 * 9) - 1.8), (X[2] + 18.4, R3 - (4.2 + 2.55 * 7) - 1.6))
    c.box(1.5, 79, 22, 29, "", fc="#f7f8fb", ec="#9aa5ba", lw=0.9, ls="--")
    for i, t in enumerate(["How to read", "PK primary key, FK foreign key", "1 / N  cardinality at each end", "solid line: enforced FK", "dashed line: table exists but no", "route ever writes to it",
                           "users.role: farmer, buyer,", "distributor, admin", "towns.region is matched to", "users.region by name (no FK)"]):
        c.text(2.7, 105.2 - i * 2.55, t, fs=6.0 if i else 6.6, ha="left", bold=(i == 0))
    c.text(52, 1.6, "9 tables, SQLite via SQLAlchemy 2.  Every foreign key points at users, crop_listings, orders or shipments; no ON DELETE rules are defined.", fs=6.4, italic=True)
    c.save(out)


# --------------------------------------------------------------------------- UML
def _cls(c, x, top, w, name, attrs, methods, head=BLUE_L, fs=5.8):
    n = max(len(attrs), 1) + max(len(methods), 1)
    h = 4.2 + 2.5 * n + 1.6
    y = top - h
    c.box(x, y, w, h, "", fc="white", r=0.8, lw=1.1)
    c.box(x, y + h - 4.2, w, 4.2, name, fc=head, bold=True, fs=6.8, r=0.8)
    ya = y + h - 6.0
    for a in attrs:
        c.text(x + 1.0, ya, a, fs=fs, ha="left")
        ya -= 2.5
    if not attrs:
        ya -= 2.5
    c.line((x, ya + 1.2), (x + w, ya + 1.2), lw=0.8)
    ya -= 0.2
    for m in methods:
        c.text(x + 1.0, ya, m, fs=fs, ha="left", italic=True)
        ya -= 2.5
    return {"x": x, "y": y, "w": w, "h": h, "top": top}


def uml(out):
    c = Canvas(10.4, 12.2)
    c.zone(1, 62, 102, 59, "Domain model (SQLAlchemy entities)", fc="#f4f5fb")
    W = 17.8
    xs = [1.5 + i * 20.8 for i in range(5)]
    T1, T2 = 113, 88
    U = _cls(c, xs[0], T1, W, "User", ["id, name, email", "hashed_password", "role, region, phone", "reliability_score", "created_at"], [])
    L = _cls(c, xs[1], T1, W, "CropListing", ["id, farmer_id", "crop_type, region", "quantity_kg, image_path", "status, asking_price", "created_at"], [])
    Q = _cls(c, xs[2], T1, W, "QualityGrade", ["id, listing_id", "grade, confidence", "probabilities (JSON)", "features (JSON)", "shap_explanation"], [])
    D = _cls(c, xs[3], T1, W, "DeliveryRecommendation", ["id, listing_id", "ranked_buyers (JSON)", "best_route (JSON)", "best_sell_day"], [])
    P = _cls(c, xs[4], T1, W, "PricePrediction", ["(never written)", "id, listing_id", "crop_type, region, grade", "current_price", "confidence_low/high", "forecast, best_sell_day"], [], head=GREY_L)
    O = _cls(c, xs[1], T2, W, "Order", ["id, listing_id", "buyer_id, distributor_id", "quantity_kg, agreed_price", "status, created_at", "updated_at"], [], head=ROSE_L)
    S = _cls(c, xs[2], T2, W, "Shipment", ["id, order_id", "distributor_id", "origin, destination", "stage, seed"], [], head=ROSE_L)
    R = _cls(c, xs[3], T2, W, "SensorReading", ["id, shipment_id", "temperature_c", "humidity_pct, shock_g", "is_anomaly, recorded_at"], [], head=ROSE_L)
    Tn = _cls(c, xs[4], T2, W, "Town", ["id, name, region", "lat, lon", "is_market"], [], head=GREY_L)
    mid = lambda b: b["y"] + b["h"] / 2
    ly = T1 - 12
    c.arrow((xs[0] + W, ly), (xs[1], ly), head=False)
    c.text(xs[0] + W + 0.8, ly + 1.6, "1", fs=6.2, bold=True); c.text(xs[1] - 0.8, ly + 1.6, "*", fs=6.2, bold=True)
    c.arrow((xs[1] + W, ly), (xs[2], ly), head=False)
    c.text(xs[1] + W + 0.8, ly + 1.6, "1", fs=6.2, bold=True); c.text(xs[2] - 0.8, ly + 1.6, "0..1", fs=6.0, bold=True)
    c.path([(xs[1] + 9, T1), (xs[1] + 9, T1 + 2.4), (xs[3] + 9, T1 + 2.4), (xs[3] + 9, T1)], head=False)
    c.text(xs[1] + 11, T1 + 4.0, "1", fs=6.2, bold=True); c.text(xs[3] + 11, T1 + 4.0, "*", fs=6.2, bold=True)
    c.path([(xs[1] + 14, T1), (xs[1] + 14, T1 + 5.0), (xs[4] + 9, T1 + 5.0), (xs[4] + 9, T1)], head=False, ls="--")
    c.text(xs[1] + 15.8, T1 + 6.6, "1", fs=6.2, bold=True); c.text(xs[4] + 11, T1 + 6.6, "*", fs=6.2, bold=True)
    c.arrow((xs[1] + 9, L["y"]), (xs[1] + 9, T2), head=False)
    c.text(xs[1] + 10.6, L["y"] - 1.6, "1", fs=6.2, bold=True); c.text(xs[1] + 10.6, T2 + 1.6, "*", fs=6.2, bold=True)
    c.path([(xs[0] + 6, U["y"]), (xs[0] + 6, mid(O)), (xs[1], mid(O))], head=False)
    c.text(xs[0] + 7.6, U["y"] - 1.6, "1", fs=6.2, bold=True); c.text(xs[1] - 1.0, mid(O) + 1.6, "*", fs=6.2, bold=True)
    c.text(xs[0] + 8.5, mid(O) - 2.0, "buyer, distributor", fs=5.8, ha="left", italic=True)
    c.arrow((xs[1] + W, mid(O)), (xs[2], mid(O)), head=False)
    c.text(xs[1] + W + 0.8, mid(O) + 1.6, "1", fs=6.2, bold=True); c.text(xs[2] - 0.8, mid(O) + 1.6, "*", fs=6.2, bold=True)
    c.arrow((xs[2] + W, mid(O)), (xs[3], mid(O)), head=False)
    c.text(xs[2] + W + 0.8, mid(O) + 1.6, "1", fs=6.2, bold=True); c.text(xs[3] - 0.8, mid(O) + 1.6, "*", fs=6.2, bold=True)
    c.text(52, 64.0, "Shipment.distributor_id also points at User.  Town.region is matched to User.region by name only.  PricePrediction is defined but no route writes to it.", fs=6.0, italic=True)

    c.zone(1, 1, 102, 58, "Boundary classes (FastAPI routers) and engine classes (backend/app/ml, core)", fc="#f1f9f5")
    RT = [("AuthRouter\n/api/auth", ["POST /signup", "POST /login", "GET /me"]),
          ("CropsRouter\n/api/crops", ["POST /upload", "GET /mine, /{id}", "POST /{id}/list"]),
          ("PricesRouter\n/api/prices", ["GET /options", "POST /predict"]),
          ("DeliveryRouter\n/api/delivery", ["GET /{id}/recommend"]),
          ("MarketplaceRouter\n/api/marketplace", ["GET /listings", "POST /orders", "GET /orders/mine", "PATCH /orders/{id}/status"]),
          ("IotRouter\n/api/iot", ["GET /shipments", "GET /shipments/{id}/history", "WS /ws/iot/{id}"]),
          ("AdminRouter\n/api/admin", ["GET /overview", "GET /model-insights"])]
    rx = [1.5 + i * 14.6 for i in range(7)]
    rb = []
    for (name, ms), x in zip(RT, rx):
        n = len(ms)
        h = 4.2 + 3.0 + 2.5 * n + 1.0
        top = 55
        c.box(x, top - h, 13.2, h, "", fc="white", r=0.8, lw=1.1)
        c.box(x, top - 7.2, 13.2, 7.2, name, fc=INDIGO_L, bold=True, fs=6.2, r=0.8, ec=INDIGO)
        for i, m in enumerate(ms):
            c.text(x + 0.8, top - 9.2 - 2.5 * i, m, fs=5.5, ha="left", italic=True)
        rb.append({"x": x, "y": top - h, "w": 13.2, "h": h})
    EN = [("FeatureExtractor", ["FEATURE_NAMES (11)", "TARGET_SIZE = 256"], ["extract_features(bytes)", "features_to_vector()"], BLUE_L),
          ("QualityInference", ["RandomForest 250/9/4", "SHAP TreeExplainer"], ["grade_image(bytes)", "load_artifact()"], INDIGO_L),
          ("PriceInference", ["GBR point + low + high", "FORECAST_DAYS = 30", "SPOILAGE_WINDOW = 14"], ["predict_price(c, r, g)", "market_context()"], INDIGO_L),
          ("DeliveryRecommender", ["WEIGHTS (sum 1.0)", "PERISHABLE_CROPS"], ["recommend(db, ...)", "_haversine_km()"], GREEN_L),
          ("ShipmentSensorState", ["temperature_c, humidity_pct", "shock_g, countdown"], ["step() -> reading"], AMBER_L),
          ("Security", ["HS256 JWT, bcrypt"], ["hash_password()", "create_access_token()", "require_roles(*roles)"], GREY_L)]
    ex = [1.5 + i * 16.9 for i in range(6)]
    eb = []
    for (name, at, me, col), x in zip(EN, ex):
        b = _cls(c, x, 27, 15.2, name, at, me, head=col, fs=5.5)
        eb.append(b)
    ctop = lambda b: (b["x"] + b["w"] / 2, b["y"] + b["h"])
    # routers -> engines
    c.arrow((rx[1] + 8, rb[1]["y"]), (eb[1]["x"] + 8, 27), label="uses", fs=5.8, loff=(3, 0))
    c.arrow((rx[2] + 6, rb[2]["y"]), (eb[2]["x"] + 6, 27), label="uses", fs=5.8, loff=(3, 0))
    c.arrow((rx[3] + 6, rb[3]["y"]), (eb[3]["x"] + 6, 27), label="uses", fs=5.8, loff=(3, 0))
    c.arrow((rx[5] + 6, rb[5]["y"]), (eb[4]["x"] + 8, 27), label="uses", fs=5.8, loff=(4, 0))
    # engine -> engine
    mid = lambda b: b["y"] + b["h"] / 2
    c.arrow((eb[1]["x"], 21), (eb[0]["x"] + 15.2, 21), label="calls", fs=5.8, loff=(0, 1.6))
    c.arrow((eb[3]["x"], 18), (eb[2]["x"] + 15.2, 18), label="calls", fs=5.8, loff=(0, 1.6))
    c.text(52, 5.0, "Every router also depends on Security (get_current_user, require_roles) and on the SQLAlchemy session (get_db); MarketplaceRouter and AdminRouter use the ORM only.", fs=6.0, italic=True)
    c.text(52, 2.2, "CropsRouter -> QualityInference -> FeatureExtractor;  DeliveryRouter -> DeliveryRecommender -> PriceInference;  IotRouter -> ShipmentSensorState.", fs=6.0, italic=True)
    c.save(out)


# --------------------------------------------------------------------------- use case
def usecase(out):
    c = Canvas(10.4, 8.8)
    c.zone(22, 1.5, 59, 84, "CropSight", fc="#fbfbff")

    def actor(x, y, label):
        c.ax.plot([x], [y + 6.2], "o", ms=7, mfc="white", mec="#1b2238")
        c.line((x, y + 5.4), (x, y + 2.4)); c.line((x - 2.6, y + 4.2), (x + 2.6, y + 4.2))
        c.line((x, y + 2.4), (x - 2.2, y)); c.line((x, y + 2.4), (x + 2.2, y))
        c.text(x, y - 2.4, label, fs=7.8, bold=True)

    actor(9, 49, "Farmer")
    actor(9, 17, "Buyer")
    actor(95, 62, "Distributor")
    actor(95, 21, "Admin")
    left = ["Upload and grade a crop photo", "View SHAP explanation of the grade", "Forecast price and best day to sell", "Plan delivery (ranked buyers, route)",
            "Publish listing with asking price", "Confirm or cancel an order"]
    left_b = ["Browse and filter marketplace", "Place an order", "View my orders"]
    right = ["Start transit", "Monitor live sensor stream", "Mark delivered"]
    right_a = ["View platform KPIs", "View model insights"]
    ys_l = [72 - i * 7.6 for i in range(6)]
    ys_b = [26 - i * 7.6 for i in range(3)]
    ys_r = [72 - i * 7.6 for i in range(3)]
    ys_a = [32 - i * 7.6 for i in range(2)]
    for t, y in zip(left, ys_l):
        c.ellipse(38, y, 27, 5.8, t, fs=6.6)
        c.line((13.5, 54), (24.5, y))
    for t, y in zip(left_b, ys_b):
        c.ellipse(38, y, 27, 5.8, t, fs=6.6)
        c.line((13.5, 22), (24.5, y))
    for t, y in zip(right, ys_r):
        c.ellipse(66, y, 25, 5.8, t, fs=6.6)
        c.line((90.5, 67), (78.5, y))
    for t, y in zip(right_a, ys_a):
        c.ellipse(66, y, 25, 5.8, t, fs=6.6)
        c.line((90.5, 26), (78.5, y))
    # login: shared by every actor
    c.ellipse(52, 81.0, 30, 4.6, "Sign up / log in  (JWT)  - all roles", fs=6.6, fc=GREEN_L, ec="#3a8a5f")
    c.line((37, 81.0), (2, 81.0), color="#3a8a5f", ls="--"); c.line((2, 81.0), (2, 23.2), color="#3a8a5f", ls="--")
    c.line((2, 55.2), (7.6, 55.2), color="#3a8a5f", ls="--"); c.line((2, 23.2), (7.6, 23.2), color="#3a8a5f", ls="--")
    c.line((67, 81.0), (102, 81.0), color="#3a8a5f", ls="--"); c.line((102, 81.0), (102, 27.2), color="#3a8a5f", ls="--")
    c.line((102, 68.2), (95.9, 68.2), color="#3a8a5f", ls="--"); c.line((102, 27.2), (95.9, 27.2), color="#3a8a5f", ls="--")
    c.text(52, 0.4, "Solid: actor uses the use case.  Dashed green: every actor signs in first (admin accounts are seeded, not self-registered).", fs=6.2, italic=True)
    c.save(out)


# --------------------------------------------------------------------------- sequence
def sequence(out):
    c = Canvas(10.4, 9.2)
    names = [("Farmer", 7), ("Web app\n(React)", 21), ("API\n(FastAPI)", 37), ("ML services\nCV, RF, GBR", 53), ("SQLite +\nuploads/", 69), ("Buyer", 84), ("Distributor", 97)]
    top, bot = 86, 1.5
    for n, x in names:
        c.box(x - 6.2, top, 12.4, 5.2, n, fc=INDIGO_L, ec=INDIGO, fs=6.8, bold=True)
        c.line((x, top), (x, bot), color="#9aa5ba", ls="--", lw=0.9)
    X = dict((n.split("\n")[0], x) for n, x in names)
    X["SQLite"] = X["SQLite +"]
    y = 82.2

    def msg(a, b, text, dy=3.3, dashed=False, self_=False):
        nonlocal y
        xa, xb = X[a], X[b]
        if self_:
            c.path([(xa, y), (xa + 5, y), (xa + 5, y - 2.0), (xa, y - 2.0)], label=None)
            c.text(xa + 6.2, y - 1.0, text, fs=6.3, ha="left")
            y -= dy + 2.2
            return
        c.arrow((xa, y), (xb, y), ls="--" if dashed else "-", label=text, fs=6.2, loff=(0, 1.5))
        y -= dy

    msg("Farmer", "Web app", "1  choose photo, crop, quantity; press Grade")
    msg("Web app", "API", "2  POST /api/crops/upload  (multipart, Bearer JWT)")
    msg("API", "API", "3  decode JWT, require_roles(farmer), check type and size", self_=True)
    msg("API", "SQLite", "4  save file to uploads/; INSERT CropListing (draft)")
    msg("API", "ML services", "5  grade_image(): 11 features, RF predict_proba, SHAP")
    msg("ML services", "API", "grade, probabilities, features, top-6 SHAP", dashed=True)
    msg("API", "SQLite", "6  INSERT QualityGrade")
    msg("API", "Web app", "7  200 listing with grade", dashed=True)
    msg("Web app", "API", "8  POST /api/prices/predict")
    msg("API", "ML services", "9  predict_price(): 31-day forecast, two bands, SHAP")
    msg("API", "Web app", "10  current price, band, forecast, best sell day", dashed=True)
    msg("Web app", "API", "11  GET /api/delivery/{id}/recommend")
    msg("API", "ML services", "12  recommend(): score every buyer, keep top 5")
    msg("API", "SQLite", "13  INSERT DeliveryRecommendation")
    msg("Web app", "API", "14  POST /api/crops/{id}/list?asking_price=  (listed)")
    msg("Buyer", "API", "15  POST /api/marketplace/orders  (listing -> sold)")
    msg("API", "SQLite", "16  INSERT Order (placed)")
    msg("Farmer", "API", "17  PATCH .../orders/{id}/status = confirmed")
    msg("Distributor", "API", "18  PATCH .../orders/{id}/status = in_transit")
    msg("API", "SQLite", "19  INSERT Shipment (seed = 97 x order id + 13)")
    msg("Distributor", "API", "20  WebSocket /api/iot/ws/iot/{shipment id}")
    msg("API", "ML services", "21  every 1.4 s: ShipmentSensorState.step()")
    msg("API", "SQLite", "22  INSERT SensorReading")
    msg("API", "Distributor", "23  send_json(temperature, humidity, shock, is_anomaly)", dashed=True)
    msg("Distributor", "API", "24  PATCH status = delivered  (shipment stage = delivered)")
    c.save(out)
