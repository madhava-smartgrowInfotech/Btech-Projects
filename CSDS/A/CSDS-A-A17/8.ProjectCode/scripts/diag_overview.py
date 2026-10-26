"""System architecture, high-level workflow and DFD level 0 for CropSight (drawn from the real modules and routes)."""
from __future__ import annotations

import math

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor


def architecture(out):
    c = Canvas(10.4, 8.0)
    c.zone(2, 66.5, 100, 12.2, "Users  (browser: Chrome / Edge, desktop or phone)", fc="#f4f5fb")
    users = [("Farmer\nupload photo, forecast,\nplan delivery, publish", 5), ("Buyer\nbrowse marketplace,\nplace orders", 31),
             ("Distributor\nstart transit, watch\nlive sensor stream", 57), ("Admin\nplatform KPIs,\nmodel insights", 83)]
    for t, x in users:
        c.box(x, 67.6, 19, 6.2, t, fc="white", fs=6.8)
    c.zone(2, 52, 100, 12.5, "Web app - React 19 + TypeScript + Vite   (port 5190;  proxy: /api, /uploads, /ws -> port 8000)", fc="#eef4fe")
    fe = [("Pages by role\nLanding, Login, Sign-up,\nFarmer, Buyer, Distributor,\nAdmin (RequireRole guard)", 5, 28),
          ("Charts (Recharts)\nQuality radar, SHAP bars,\nprice forecast + band,\nlive sensor traces", 35, 28),
          ("Data layer\nAxios /api + JWT bearer,\nZustand auth store,\nWebSocket client", 65, 18),
          ("UI kit\nTailwind 4, Framer Motion,\nGSAP, Three.js hero", 85, 15.5)]
    for t, x, w in fe:
        c.box(x, 53.2, w, 7.8, t, fc="white", fs=6.6)
    c.arrow((52, 66.5), (52, 64.5), both=True)
    c.zone(2, 20, 100, 28.5, "Backend - FastAPI 0.115 + Python 3.11   (port 8000)", fc="#eef8f2")
    c.box(5, 39.8, 94, 4.4, "REST routers  /api:  auth - crops - prices - delivery - marketplace - iot - admin - health        WebSocket  /api/iot/ws/iot/{id}",
          fc=INDIGO_L, ec=INDIGO, fs=6.8, bold=True)
    c.arrow((52, 52), (52, 48.5), both=True)
    c.text(70, 50.2, "HTTP / JSON  and  WebSocket", fs=6.8, italic=True)
    svc = [("Security\nJWT HS256, bcrypt,\nrequire_roles()", 5), ("CV feature\nextractor\nOpenCV + skimage\n11 features", 18.5),
           ("Quality grader\nRandom Forest\n250 trees, depth 9\n+ SHAP top 6", 32), ("Price model\nGBR point + 2 quantile\n19 features, 31-day\nforecast + SHAP", 45.5),
           ("Delivery scorer\n5 weighted terms\n0.38/.22/.18/.14/.08\nhaversine route", 59), ("Sensor simulator\nShipmentSensorState\nreading / 1.4 s\n(simulated)", 72.5),
           ("Order state\nmachine\nplaced > confirmed >\nin_transit > delivered", 86)]
    for t, x in svc:
        w = 13.0
        c.box(x, 25.6, w, 12.2, t, fc="white", fs=6.3)
        c.arrow((x + w / 2, 39.8), (x + w / 2, 37.8))
    c.box(5, 21.4, 94, 3.2, "SQLAlchemy 2 ORM (9 models) - Pydantic 2 schemas - joblib model loading (lru_cache) - CORS - StaticFiles /uploads",
          fc=AMBER_L, ec="#c9a45a", fs=6.6)
    c.zone(2, 1, 100, 16.5, "Storage  (backend/ and backend/app/data/)", fc="#fff8e8")
    c.box(5, 2.2, 28, 10, "SQLite  cropsight.db\nusers, crop_listings, quality_grades,\ntowns, price_predictions, shipments,\nsensor_readings, orders,\ndelivery_recommendations", fc="white", fs=6.4)
    c.box(36, 2.2, 22, 10, "Model artefacts (.joblib)\nquality_model.joblib\nprice_model.joblib\n(+ synthetic CSV datasets)", fc="white", fs=6.4)
    c.box(61, 2.2, 18, 10, "Uploaded crop photos\napp/data/uploads/\n(JPEG, PNG, WEBP)", fc="white", fs=6.4)
    c.box(82, 2.2, 18, 10, "Simulated sensor\nstream: no hardware,\nseeded random walk", fc=ROSE_L, ec="#c98a8a", fs=6.4)
    c.arrow((19, 20), (19, 17.5), both=True)
    c.arrow((47, 20), (47, 17.5), both=True)
    c.arrow((70, 20), (70, 17.5), both=True)
    c.arrow((91, 12.2), (91, 20), ls="--")
    c.save(out)


def workflow(out):
    c = Canvas(10.4, 5.8)
    steps = [("1  Upload", "photo + crop type +\nquantity (JPEG, PNG,\nWEBP, max 8 MB)", BLUE_L),
             ("2  Grade", "11 CV features ->\nRandom Forest -> A / B /\nC / Reject + SHAP", BLUE_L),
             ("3  Forecast", "current price, 15-85%\nband, 31-day curve,\nbest day to sell", INDIGO_L),
             ("4  Plan", "rank 4 buyers: price,\ndistance, quality fit,\nreliability, spoilage", INDIGO_L),
             ("5  Publish", "asking price set,\nlisting status:\ndraft -> listed", INDIGO_L)]
    steps2 = [("6  Order", "buyer orders; listing\nbecomes sold;\norder = placed", GREEN_L),
              ("7  Confirm", "owning farmer confirms\n(or cancels) the order", GREEN_L),
              ("8  Transit", "distributor starts\ntransit; shipment\nrow is created", AMBER_L),
              ("9  Monitor", "WebSocket stream:\ntemperature, humidity,\nshock, alerts", AMBER_L),
              ("10  Deliver", "distributor marks\ndelivered; shipment\nstage = delivered", ROSE_L)]
    bw, bh, gap = 16.6, 14, 3.9
    xs = [3 + i * (bw + gap) for i in range(5)]
    row1 = [c.box(x, 33, bw, bh, "", fc=f) for x, (_, _, f) in zip(xs, steps)]
    row2 = [c.box(x, 10, bw, bh, "", fc=f) for x, (_, _, f) in zip(xs, steps2)]
    for b, (h, t, _) in zip(row1 + row2, steps + steps2):
        c.text(b["x"] + bw / 2, b["y"] + bh - 3.0, h, fs=8.2, bold=True)
        c.text(b["x"] + bw / 2, b["y"] + 5.4, t, fs=6.6)
    for r in (row1, row2):
        for a, b in zip(r[:-1], r[1:]):
            c.arrow(anchor(a, "r"), anchor(b, "l"))
    last, first = anchor(row1[-1], "b"), anchor(row2[0], "t")
    c.path([last, (last[0], 28.5), (first[0], 28.5), first])
    c.box(3, 51, 97.6, 4.6, "Steps 1-5 are done by the farmer, 6 by the buyer, 7 by the farmer again, 8-10 by the distributor. Every step is a role-checked API call; order moves only along placed > confirmed > in_transit > delivered.",
          fc=AMBER_L, ec="#c9a45a", fs=6.7, r=1.5)
    c.box(3, 2.2, 97.6, 4.6, "Models were trained on synthetic data and the sensor stream is simulated; both are disclosed in the Admin 'Model insights' screen.",
          fc=GREY_L, ec="#9aa5ba", fs=6.8, r=1.5)
    c.save(out)


CX, CY, A, B = 52, 34, 15, 19


def edge_pt(px, py):
    """Point on the central ellipse in the direction of (px, py)."""
    dx, dy = px - CX, py - CY
    t = 1.0 / math.sqrt((dx / A) ** 2 + (dy / B) ** 2)
    return (CX + dx * t, CY + dy * t)


def dfd0(out):
    c = Canvas(10.4, 6.6)
    c.ellipse(CX, CY, 2 * A, 2 * B, "0\nCropSight\ngrading, price,\ndelivery and\nmarketplace", fc=INDIGO_L, ec=INDIGO, fs=8.6)
    c.box(1, 46, 17, 11, "Farmer", fc=BLUE_L, fs=8.5, bold=True)
    c.box(1, 11, 17, 11, "Buyer", fc=BLUE_L, fs=8.5, bold=True)
    c.box(86, 46, 17, 11, "Distributor", fc=BLUE_L, fs=8.5, bold=True)
    c.box(86, 11, 17, 11, "Admin", fc=BLUE_L, fs=8.5, bold=True)
    c.box(36, 1.2, 32, 6.4, "Simulated sensor stream\n(ShipmentSensorState, no hardware)", fc=ROSE_L, ec="#c98a8a", fs=7.0, bold=True)

    def pair(dy, y_in, y_out, side, t_in, t_out):
        xe = 18 if side == "l" else 86
        px = 36 if side == "l" else 68
        c.arrow((xe, y_in) if side == "l" else (xe, y_in), edge_pt(px, y_in), label=t_in, fs=6.4, loff=(0, 2.6))
        c.arrow(edge_pt(px, y_out), (xe, y_out), ls="--", label=t_out, fs=6.4, loff=(0, -dy))

    pair(2.8, 53, 48, "l", "sign-up / login, crop photo,\ncrop, quantity, asking price,\nconfirm order", "grade + SHAP, price forecast,\nranked buyers, orders")
    pair(4.6, 18, 13, "l", "login, listing filters,\norder (quantity, price)", "listings with grade, price\ntrend, order status")
    pair(2.8, 53, 48, "r", "login, start transit,\nmark delivered, open monitor", "orders to ship,\nlive readings and alerts")
    pair(4.6, 18, 13, "r", "login, KPI and\nmodel-insight requests", "users, listings, orders, volume;\naccuracy, MAE / R2, importances")
    c.arrow((52, 7.6), (52, CY - B + 0.2))
    c.text(53.5, 11.0, "temperature, humidity,\nshock every 1.4 s", fs=6.4, ha="left")
    c.text(52, 63.3, "Context diagram (level 0).  Solid arrows: data in.  Dashed arrows: data out.", fs=7.2, italic=True)
    c.save(out)
