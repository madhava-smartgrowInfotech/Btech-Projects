"""DFD level 1 and 2 and the core-algorithm flowchart for CropSight."""
from __future__ import annotations

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor


def store(c, x, y, w, h, label, fc="#fff8e8", fs=6.2):
    """Open-ended rectangle: a data store (id | name)."""
    c.rect(x, y, w, h, fc=fc, ec="#44506b", lw=1.1)
    c.line((x + 5, y), (x + 5, y + h))
    parts = label.split(" ", 1)
    c.text(x + 2.5, y + h / 2, parts[0], fs=7, bold=True)
    c.text(x + 5 + (w - 5) / 2, y + h / 2, parts[1], fs=fs)


def dfd1(out):
    c = Canvas(10.4, 7.8)
    c.box(5, 68, 94, 6.5, "Farmer  -  Buyer  -  Distributor  -  Admin     (browser: credentials, photos, orders, status changes, monitor and KPI requests)",
          fc=BLUE_L, fs=7.2, bold=True)
    xa = [14, 36, 58, 80]
    pa = ["1.0\nAuthenticate\nand authorise", "2.0\nGrade crop\n(photo)", "3.0\nForecast\nprice", "4.0\nPlan\ndelivery"]
    for x, t in zip(xa, pa):
        c.ellipse(x, 58, 19.5, 11.5, t, fc=INDIGO_L, ec=INDIGO, fs=7.0)
        c.arrow((x, 68), (x, 63.8), both=True)
    c.ellipse(14, 26.5, 19.5, 11.5, "5.0\nMarketplace\nand orders", fc=INDIGO_L, ec=INDIGO, fs=7.0)
    c.ellipse(36, 26.5, 19.5, 11.5, "6.0\nMonitor\nshipments", fc=INDIGO_L, ec=INDIGO, fs=7.0)
    c.ellipse(82, 26.5, 19.5, 11.5, "7.0\nAdmin\nanalytics", fc=INDIGO_L, ec=INDIGO, fs=7.0)
    # request bus for row B (left edge) and admin (right edge)
    c.line((5, 71), (2.5, 71)); c.line((2.5, 71), (2.5, 37.2)); c.line((2.5, 37.2), (36, 37.2))
    c.arrow((14, 37.2), (14, 32.3), both=True)
    c.arrow((36, 37.2), (36, 32.3), both=True)
    c.text(24, 39.2, "requests and responses", fs=6.4, italic=True)
    c.line((99, 71), (101.5, 71)); c.line((101.5, 71), (101.5, 26.5)); c.arrow((101.5, 26.5), (91.8, 26.5), both=True)
    # sensor stream
    c.box(50, 20.5, 18, 11, "Simulated sensor\nstream\n(ShipmentSensorState)", fc=ROSE_L, ec="#c98a8a", fs=6.6, bold=True)
    c.arrow((50, 26.5), (45.8, 26.5), ls="--", label="readings", loff=(0, 2.2), fs=6.2)
    # stores under row A
    sa = [("D1 users", 14), ("D2 listings, grades", 36), ("D6 models, uploads", 58), ("D5 recommendations", 80)]
    for t, x in sa:
        store(c, x - 10.5, 41, 21, 5.6, t, fs=6.0)
        c.arrow((x, 52.2), (x, 46.6), both=True, ls=":")
    sb = [("D3 orders", 14), ("D4 shipments, readings", 36), ("D1-D3 (read only)", 82)]
    for t, x in sb:
        store(c, x - 10.5, 8, 21, 5.6, t, fs=6.0)
        c.arrow((x, 20.7), (x, 13.6), both=True, ls=":")
    c.text(52, 4.6, "1.0 issues the JWT and checks role + ownership for every call of 2.0-7.0.  2.0 also reads D6 (quality model); 3.0 reads D6 (price model);", fs=6.3, italic=True)
    c.text(52, 1.8, "4.0 reads D2, D1, D6 and writes D5.  5.0 reads D2.  DFD level 1: 7 processes, 6 data stores.  Solid: external flows.  Dotted: store access.  Dashed: simulated source.", fs=6.3, italic=True)
    c.save(out)


def dfd2(out):
    c = Canvas(10.4, 6.8)
    c.box(0.5, 40, 8.5, 12, "Farmer", fc=BLUE_L, fs=7.4, bold=True)
    xs = [21, 39, 57, 75, 93]
    r1, r2 = 46, 23
    row1 = ["2.1\nValidate type\n(JPEG, PNG,\nWEBP), <= 8 MB", "2.2\nSave photo,\ncreate draft\nlisting", "2.3\nDecode, centre\non 256 x 256\nwhite canvas",
            "2.4\nForeground mask\n(Otsu, morphology)", "2.5\nColour features\n(HSV: hue, sat,\nvalue, uniformity)"]
    row2 = ["2.6\nGLCM texture (3)\n+ edge density", "2.7\nBlemish ratio\n+ size score", "2.8\nRandom Forest\npredict_proba\n-> A/B/C/Reject", "2.9\nSHAP top 6;\nstore\nQualityGrade"]
    for x, t in zip(xs, row1):
        c.ellipse(x, r1, 15.8, 13, t, fc=INDIGO_L, ec=INDIGO, fs=6.3)
    for x, t in zip(xs[::-1][:4], row2):
        c.ellipse(x, r2, 15.8, 13, t, fc=INDIGO_L, ec=INDIGO, fs=6.3)
    c.arrow((9, 46), (13.1, 46))
    c.text(5.5, 55.2, "photo, crop,\nquantity", fs=6.2)
    for a, b in zip(xs[:-1], xs[1:]):
        c.arrow((a + 7.9, r1), (b - 7.9, r1))
    c.arrow((93, 39.5), (93, 29.5))
    c.text(97.5, 34.5, "HSV +\nmask", fs=6, ha="center")
    r2x = xs[::-1][:4]
    for a, b in zip(r2x[:-1], r2x[1:]):
        c.arrow((a - 7.9, r2), (b + 7.9, r2))
    c.path([(30.25, r2), (4.5, r2), (4.5, 39.8)], ls="--")
    c.text(17, r2 - 2.8, "grade, confidence, class\nprobabilities, features, SHAP", fs=6.0)
    c.box(10, 58, 31, 7.5, "Rejected: HTTP 400 when the type is not\nJPEG / PNG / WEBP or the file is over 8 MB", fc=AMBER_L, ec="#c9a45a", fs=6.2)
    c.arrow((21, 52.5), (21, 58), ls=":")
    c.box(66, 58, 36, 7.5, "If the mask covers < 3 % or > 98 % of the image,\nthe whole image is used as the mask (2.4)", fc=AMBER_L, ec="#c9a45a", fs=6.2)
    c.arrow((75, 52.5), (80, 58), ls=":")
    store(c, 43, 58, 21, 5.6, "D6 uploads/", fs=6.2)
    c.arrow((39, 52.5), (48, 58), ls=":")
    store(c, 27, 3, 24, 5.6, "D2 listings, grades", fs=6.0)
    c.arrow((39, 8.6), (39, 16.5), both=True, ls=":")
    store(c, 55, 3, 30, 5.6, "D6 quality_model.joblib", fs=6.0)
    c.arrow((62, 8.6), (57, 16.5), ls=":")
    c.text(52, 1.0, "Data passed on: bytes -> image -> RGB 256 px -> mask -> 5 colour features -> +4 (texture, edges) -> +2 (blemish, size) = 11 features -> probabilities.", fs=6.1, italic=True)
    c.save(out)


def flowchart(out):
    c = Canvas(10.4, 8.8)
    cx, rx = 24, 80
    c.text(2, 87, "Algorithm 1: grade_image()  (POST /api/crops/upload)", fs=8, bold=True, ha="left")
    c.text(63, 87, "Algorithm 2: recommend()  (GET /api/delivery/{id}/...)", fs=8, bold=True, ha="left")
    c.terminal(cx, 82, 32, 4.4, "Start: farmer uploads photo + crop + quantity", fs=6.8)
    c.diamond(cx, 74.5, 32, 7.5, "type JPEG / PNG /\nWEBP ?", fs=6.6)
    c.diamond(cx, 65, 32, 7.5, "size <= 8 MB ?", fs=6.6)
    c.box(cx - 17, 53.2, 34, 5.6, "Decode, centre on 256 x 256 white canvas;\nHSV foreground mask (Otsu + morphology)", fc=BLUE_L, fs=6.5)
    c.diamond(cx, 44.5, 32, 8, "mask coverage\n< 3 % or > 98 % ?", fs=6.6)
    c.box(cx - 17, 32.5, 34, 6, "11 features: colour (5), GLCM texture (3),\nedge density, blemish ratio, size score", fc=BLUE_L, fs=6.5)
    c.box(cx - 17, 24, 34, 5.6, "Random Forest (250 trees) predict_proba\ngrade = argmax, confidence = max", fc=INDIGO_L, fs=6.5)
    c.box(cx - 17, 16, 34, 5, "SHAP TreeExplainer: top-6 contributions", fc=INDIGO_L, fs=6.5)
    c.box(cx - 17, 8.2, 34, 5, "Insert QualityGrade; return listing", fc=GREEN_L, fs=6.5)
    c.terminal(cx, 3, 24, 4.2, "End: grade A / B / C / Reject", fc=GREEN_L, fs=6.8)
    c.arrow((cx, 79.8), (cx, 78.25))
    c.arrow((cx, 70.75), (cx, 68.75), label="yes", loff=(2.5, 0), fs=6.2)
    c.arrow((cx, 61.25), (cx, 58.8), label="yes", loff=(2.5, 0), fs=6.2)
    c.arrow((cx, 53.2), (cx, 48.5))
    c.arrow((cx, 40.5), (cx, 38.5), label="no", loff=(2.5, 0), fs=6.2)
    c.arrow((cx, 32.5), (cx, 29.6))
    c.arrow((cx, 24), (cx, 21))
    c.arrow((cx, 16), (cx, 13.2))
    c.arrow((cx, 8.2), (cx, 5.1))
    c.box(45, 71.5, 16, 6, "HTTP 400\nunsupported type", fc=ROSE_L, ec="#c98a8a", fs=6.3)
    c.arrow((cx + 16, 74.5), (45, 74.5), label="no", loff=(0, 1.6), fs=6.2)
    c.box(45, 62, 16, 6, "HTTP 400\nimage too large", fc=ROSE_L, ec="#c98a8a", fs=6.3)
    c.arrow((cx + 16, 65), (45, 65), label="no", loff=(0, 1.6), fs=6.2)
    c.box(45, 41.5, 16, 6, "use the whole\nimage as mask", fc=AMBER_L, ec="#c9a45a", fs=6.3)
    c.arrow((cx + 16, 44.5), (45, 44.5), label="yes", loff=(0, 1.6), fs=6.2)
    c.path([(53, 41.5), (53, 35.5), (cx + 17, 35.5)])
    # algorithm 2
    c.terminal(rx, 82, 34, 4.4, "Start: farmer's listing (crop, region, grade)", fs=6.8)
    c.box(rx - 17, 70.8, 34, 6.4, "predict_price(): point model on 31 daily contexts;\nbest_sell_day = argmax of forecast, days 0-14", fc=INDIGO_L, fs=6.3)
    c.box(rx - 17, 61.5, 34, 6, "for each buyer: haversine distance between\ntowns (else 50 + hash x 400 km)", fc=BLUE_L, fs=6.4)
    c.box(rx - 17, 52.5, 34, 6, "offered = base x (0.90 + 0.28 x hash);\ntransit = km / 380 + 0.5 d; spoilage span 5 or 21 d", fc=BLUE_L, fs=6.2)
    c.box(rx - 17, 43.5, 34, 6, "five terms in [0, 1]: price, distance, quality\nfit, reliability, 1 - spoilage risk", fc=BLUE_L, fs=6.4)
    c.box(rx - 17, 34.5, 34, 6, "score = 100 x (0.38 p + 0.22 d + 0.18 q\n+ 0.14 r + 0.08 s)", fc=INDIGO_L, fs=6.5)
    c.diamond(rx, 26.5, 28, 7.5, "more buyers ?", fs=6.6)
    c.box(rx - 17, 14.2, 34, 6, "sort by score; keep top 5; best route =\ntop buyer's town (km, days)", fc=GREEN_L, fs=6.5)
    c.terminal(rx, 6, 34, 4.4, "Store DeliveryRecommendation; return", fc=GREEN_L, fs=6.6)
    c.arrow((rx, 79.8), (rx, 77.2))
    c.arrow((rx, 70.8), (rx, 67.5))
    c.arrow((rx, 61.5), (rx, 58.5))
    c.arrow((rx, 52.5), (rx, 49.5))
    c.arrow((rx, 43.5), (rx, 40.5))
    c.arrow((rx, 34.5), (rx, 30.25))
    c.arrow((rx, 22.75), (rx, 20.2), label="no", loff=(2.5, 0), fs=6.2)
    c.arrow((rx, 14.2), (rx, 8.2))
    c.path([(rx + 14, 26.5), (99.5, 26.5), (99.5, 64.5), (rx + 17, 64.5)], label="yes: next buyer", seg=0, loff=(0, 2.0), fs=6.2)
    c.save(out)
