"""Build 7.Review_1_PPT.pptx from D:\\abstracts\\Templates\\Review_1_PPT.pptx (16 slides)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckkit import (fill, put_picture, replace_chart, set_notes, set_paras, set_table, shape, style_chart, table_size)  # noqa: E402
from doc_common import BASE_PAPER, BATCH, COLLEGE, DEPT, DIAG, GUIDE, GUIDE_DESIG, PRODUCT, REFERENCES, STUDENTS, TITLE, YEAR  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.util import Emu  # noqa: E402

SRC = r"D:\abstracts\Templates\Review_1_PPT.pptx"
OUT = BATCH / "7.Review_1_PPT.pptx"


def scrub_theme(path):
    """The template's theme is named after another project: rename it."""
    import shutil
    import zipfile
    tmp = Path(str(path) + ".tmp")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith("ppt/theme/") and item.filename.endswith(".xml"):
                data = data.decode("utf-8").replace("Hidden Risk", PRODUCT).encode("utf-8")
            zout.writestr(item, data)
    shutil.move(tmp, path)


def build():
    prs = Presentation(SRC)
    S = list(prs.slides)
    cp = prs.core_properties
    cp.title, cp.subject, cp.author, cp.keywords = f"{PRODUCT}: Review 1", TITLE, "Batch A17", "smart agriculture, crop quality grading, price forecasting, IoT, explainable AI"
    cp.category = cp.comments = cp.content_status = ""
    cp.last_modified_by = "Batch A17"
    for lay in prs.slide_layouts:  # footer text lives on the layout
        for sh in lay.shapes:
            if sh.has_text_frame and sh.text_frame.text.startswith("The Hidden Risk"):
                set_paras(sh, f"{PRODUCT}  ·  Review 1  ·  Batch A17")
    for sl in S:  # footer text of the template
        for sh in sl.shapes:
            if sh.has_text_frame and sh.text_frame.text.startswith("The Hidden Risk"):
                set_paras(sh, f"{PRODUCT}  ·  Review 1  ·  Batch A17")

    # 1 title
    s = S[0]
    set_paras(shape(s, 2), PRODUCT)
    set_paras(shape(s, 3), "Smart Crop Delivery with AI-Based Price and Quality Intelligence")
    set_paras(shape(s, 6), [f"{n}  {r}" for n, r in STUDENTS], 15)
    set_paras(shape(s, 8), f"{GUIDE}, {GUIDE_DESIG}")
    set_paras(shape(s, 9), [DEPT, f"{COLLEGE}  \u00b7  Batch A17 (CSE-DS, Section A)  \u00b7  {YEAR}"], 13)
    set_notes(s, "Review 1 covers problem identification and research for CropSight, a platform that grades crop quality from photos, forecasts prices, plans delivery and monitors shipments.")

    # 2 contents
    set_notes(S[1], "Nine parts: the abstract, the base paper and related work, the gap we found, our problem statement and objectives, the approach, expected outcomes and references.")

    # 3 abstract
    s = S[2]
    set_paras(shape(s, 2), "Abstract: from harvest to delivery with AI")
    fill(s, 8, "Farmers face fluctuating prices, inconsistent quality assessment, supply-chain inefficiencies and little real-time decision support. Post-harvest losses occur because storage and transport are not monitored.", 16)
    fill(s, 13, "CropSight integrates AI, ML and IoT. Crop quality is graded from a photo (colour, texture, size, defects), prices are predicted from market, weather and demand data, and sensors monitor storage and transport. XAI explains each decision.", 15)
    fill(s, 18, "A smart delivery module recommends buyers, routes and the best time to sell, and a marketplace connects farmers, distributors and buyers in one web application.", 16)
    set_notes(s, "The abstract in one slide: the problem, the AI + ML + IoT idea, and the marketplace deliverable.")

    # 4 base paper
    s = S[3]
    fill(s, 5, BASE_PAPER, 14)
    set_paras(shape(s, 7), "Method")
    fill(s, 8, "IoT soil and environment sensors feed deep tabular models: a transformer (TTL) for irrigation advice, TabNet for soil analysis and fertiliser choice, and SwiFT for crop recommendation. XAI explains the predictions; a weather API and a chatbot support farmers.", 14)
    set_paras(shape(s, 10), "Data and reported results")
    fill(s, 11, "Soil nutrient profiles, sensor readings, historical weather and crop-yield records. Reported: irrigation accuracy 99.13%; soil TabNet RMSE 1.51 and R2 98.7%; crop SwiFT accuracy 98.75%; fertiliser TabNet accuracy 99.3%.", 14)
    set_paras(shape(s, 13), "Stated future work and our adaptation")
    fill(s, 14, "The authors name real-time adaptive control and wider regional generalisation as future work. The system is pre-harvest. CropSight adopts the IoT + ML + XAI idea after harvest: grading, price, delivery.", 14)
    set_notes(s, "The base paper is a pre-harvest smart-agriculture system. CropSight keeps its IoT, learning and explainability architecture and applies it to post-harvest quality grading, price prediction and delivery.")

    # 5 literature survey
    s = S[4]
    rows = [["Work", "Approach", "Data", "Reported result"],
            ["Khaliq et al., 2025 (base) [1]", "IoT sensors + TTL, TabNet, SwiFT deep tabular models + XAI, weather API, chatbot", "Soil, weather, fertiliser and crop data", "Irrigation 99.13%; crop 98.75%; fertiliser 99.3%; soil R2 98.7%"],
            ["Crop leaf disease diagnosis and severity grading, 2026 [2]", "Multi-task learning (from the title)", "Listed in survey, details not retrieved", "Not retrieved"],
            ["Agricultural product quality inspection and e-commerce grading, 2026 [3]", "Image recognition (from the title)", "Listed in survey, details not retrieved", "Not retrieved"],
            ["Crop and market price prediction, 2023 [4]", "Machine learning (from the title)", "Listed in survey, details not retrieved", "Not retrieved"],
            ["Crop price prediction, 2024 [5]", "Machine learning (from the title)", "Listed in survey, details not retrieved", "Not retrieved"],
            ["Additional reading: Wang and Zhang, 2026 [6]", "17 forecasting methods incl. 5 time-series foundation models", "USDA ERS monthly commodity prices, 1997-2025", "Zero-shot foundation models beat USDA futures-based forecasts on 3 of 4 commodities"],
            ["Additional reading: Feng and Zong, 2026 [7]", "ConvLSTM + LCMST-Net crop image recognition", "Large-scale crop images", "Average classification accuracy 0.982"]]
    sz = table_size(rows, 1164, 520, [0.27, 0.30, 0.20, 0.23], 14, 9)
    set_table(shape(s, 6), rows, sz, header_size=sz)
    set_notes(s, "[1], [6] and [7] were read; [2] to [5] are listed in the batch literature survey but could not be retrieved independently, so only their titles are used and no results are claimed for them.")

    # 6 supporting evidence
    s = S[5]
    set_paras(shape(s, 2), "Supporting evidence: ML and XAI work in farming")
    ch = replace_chart(s, 4, ["Irrigation (TTL)", "Crop (SwiFT)", "Fertiliser (TabNet)", "Soil R2 (TabNet)"], [("Reported (%)", [99.13, 98.75, 99.3, 98.7])], number_format="0.00")
    style_chart(ch, "Results reported by the base paper [1] on its own data (%)", ["2F7D4F"], number_format="0.00", legend=False, label_pt=12, axis_title="accuracy or R2 (%)")
    ch.value_axis.maximum_scale = 100
    set_paras(shape(s, 8), "Takeaway")
    fill(s, 9, "IoT data with learned models and XAI gave high reported scores for farm decisions [1]. For prices, modern foundation models beat USDA futures-based forecasts on three of four commodities [6]. Manual grading and unmonitored storage are the post-harvest gaps.", 14)
    set_paras(shape(s, 13), "Caveat")
    fill(s, 14, "These figures are published results on other tasks and datasets (pre-harvest, USDA prices). They motivate our approach; they are not our results.", 15)
    set_notes(s, "These are published numbers from the base paper and an arXiv study, not ours. They show the approach is viable; CropSight's own measurements come in the later reviews.")

    # 7 existing system
    s = S[6]
    set_paras(shape(s, 2), "Existing system and current approaches")
    steps = ["Harvest the crop", "Trader grades by eye", "Sell via middleman", "Mandi price accepted", "Store and transport", "Losses found late"]
    for sid, t in zip((5, 8, 11, 14, 17, 20), steps):
        fill(s, sid, t, 14)
    set_paras(shape(s, 24), "Manual grading and mandi sales")
    fill(s, 25, "Crop quality is graded manually by traders at markets, and farmers sell through middlemen at mandi prices.", 16)
    set_paras(shape(s, 29), "Portals without forecasts")
    fill(s, 30, "Government portals such as e-NAM publish prices without forecasts, and storage and transport conditions are rarely monitored.", 16)
    set_notes(s, "How a farmer sells a crop today.")

    # 8 limitations
    s = S[7]
    set_paras(shape(s, 2), "Limitations of existing methods")
    for tid, bid, ttl, body in [
        (7, 8, "Subjective grading", "Manual grading is inconsistent from trader to trader."),
        (12, 13, "No price foresight", "Farmers lack forecasts to decide when to sell; middlemen reduce their share."),
        (17, 18, "Unmonitored losses", "Storage and transport conditions cause post-harvest losses."),
        (22, 23, "Opaque decisions", "Grading and pricing decisions are not transparent to the farmer.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 16)
    set_notes(s, "Four limitations: grading is subjective, prices cannot be foreseen, losses go unmonitored and decisions are opaque.")

    # 9 research gap
    s = S[8]
    gaps = [("Stage", "Smart-agriculture systems focus on pre-harvest decisions [1]; post-harvest support is thin."),
            ("Quality", "Image-based quality grading exists, but it is not joined with pricing and delivery."),
            ("Price", "Price prediction studies [4], [5] stop at a forecast; no best-time-to-sell advice."),
            ("Delivery", "Few systems recommend buyers and routes using price, distance and spoilage risk."),
            ("Transparency", "Grading and price decisions are rarely explained to farmers with XAI.")]
    for (lid, tid), (lab, txt) in zip([(5, 6), (8, 9), (11, 12), (14, 15), (17, 18)], gaps):
        set_paras(shape(s, lid), lab)
        fill(s, tid, txt, 16)
    set_notes(s, "Smart-agriculture systems focus on pre-harvest decisions; few support post-harvest quality grading, price forecasting and delivery planning for farmers.")

    # 10 problem statement
    s = S[9]
    fill(s, 5, "Given a photo of a harvested crop and its market context, grade its quality automatically, forecast its price and the best day to sell, recommend buyers and routes, monitor storage and transport conditions, explain each decision, and connect farmers, distributors and buyers through one digital marketplace.", 22)
    set_paras(shape(s, 8), "Crop photo, crop and region, market data")
    set_paras(shape(s, 11), "Grade, price forecast, buyer and route ranking")
    set_paras(shape(s, 14), "Sensor alerts + XAI explanations")
    set_notes(s, "Inputs are the crop photo, its crop type and region, and market data; outputs are a grade, a price forecast, a ranked delivery plan and alerts; the extra property is explainability.")

    # 11 objectives
    s = S[10]
    fill(s, 4, ["Grade crop quality automatically from images.",
                "Forecast crop prices from market, weather and demand data.",
                "Monitor storage and transport conditions using IoT sensors.",
                "Explain grading and pricing decisions with XAI.",
                "Recommend buyers, delivery routes and the best time to sell.",
                "Connect farmers, distributors and buyers through a digital marketplace."], 22, bullet=True)
    set_notes(s, "The six objectives of the project.")

    # 12 proposed approach
    s = S[11]
    for tid, bid, ttl, body in [
        (7, 8, "Quality grading", "Colour, texture, edge, blemish and size features from the photo; classifier gives grade A/B/C/Reject."),
        (12, 13, "Price intelligence", "Gradient-boosted model: current price, confidence band, 30-day forecast, best day to sell."),
        (17, 18, "Explainable AI", "SHAP shows which features drove each grade and each price."),
        (22, 23, "Delivery planner", "Buyers ranked by price, distance, reliability and spoilage risk; best route."),
        (27, 28, "Web application", "React + FastAPI marketplace for farmers, buyers, distributors and admin; live sensor stream (simulated in the prototype).")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 13)
    set_notes(s, "The approach: image features to a grade, a price model with a forecast, explanations with SHAP, a scored delivery plan, and one web application. The prototype's sensors are simulated and its models are trained on synthetic data.")

    # 13 architecture
    s = S[12]
    put_picture(s, DIAG / "01_system_architecture.png", (215, 118, 790, 482), remove_ids=(4,), name="System architecture diagram")
    set_paras(shape(s, 5), "Proposed architecture: React web app, FastAPI backend with grading, price, delivery and sensor services, SQLite and model files")
    set_notes(s, "Browser to React to FastAPI. The grading, price and delivery services run in the backend; sensor readings are streamed to the browser over a WebSocket.")

    # 14 expected outcomes
    s = S[13]
    for tid, bid, ttl, body in [
        (7, 8, "Automatic grading", "A consistent grade with confidence from every photo."),
        (12, 13, "Price foresight", "A price, a confidence band and the best day to sell."),
        (17, 18, "Cold-chain alerts", "Temperature, humidity and shock readings with alerts."),
        (22, 23, "Explained decisions", "SHAP drivers shown with each grade and price."),
        (27, 28, "Smarter delivery", "Ranked buyers and a route for each listing."),
        (32, 33, "Connected marketplace", "Order lifecycle from listing to delivery for four roles.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 16)
    set_notes(s, "Expected outcomes are stated as targets at this stage; they are measured and reported honestly in the later reviews.")

    # 15 references
    s = S[14]
    fill(s, 4, [f"[{i}] {r}" for i, r in enumerate(REFERENCES[:10], 1)], 14, min_pt=8.5, bullet=True, gap_pt=3)
    set_notes(s, "References [1] to [10]; the full list is in the report.")

    set_notes(S[15], "Thank you. Questions are welcome.")
    prs.save(OUT)
    scrub_theme(OUT)
    print("saved", OUT, len(prs.slides._sldIdLst), "slides")


if __name__ == "__main__":
    build()
