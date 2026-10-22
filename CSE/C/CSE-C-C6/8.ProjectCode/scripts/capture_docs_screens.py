"""Capture the documentation screenshots (1440x900) of the app running on the model trained on real LIAR2 data.

Start the app first, pointing the backend at a COPY of the LIAR2 model so the Retrain screen cannot overwrite the original:
    set FAKENEWS_MODEL=<copy of models/liar2_msvm_model.pkl>   (then run.bat style: backend 8406, frontend 5406)
    python scripts/capture_docs_screens.py

Inputs : experiments/liar2/test_predictions_seed42.csv (real test statements with true and predicted labels),
         data/liar2/train.csv (a 600-row labelled CSV is cut from it for the Retrain screen).
Outputs: docs/screenshots/10_liar2_*.png ... 22_liar2_*.png and docs/screenshots/captured_statements.json
"""
import json
import os
import tempfile

import numpy as np
import pandas as pd
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "screenshots")
SIZE = {"width": 1440, "height": 900}
LABELS = ["REAL", "PARTIALLY TRUE", "FAKE"]


def read_port():
    port = "5406"
    env = os.path.join(ROOT, ".env")
    if os.path.exists(env):
        for line in open(env, encoding="utf-8"):
            if line.startswith("FRONTEND_PORT="):
                port = line.split("=", 1)[1].strip()
    return port


def launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        return p.chromium.launch(channel="chrome")


def settle(page, ms=1800):
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(ms)


def pick_statements():
    df = pd.read_csv(os.path.join(ROOT, "experiments", "liar2", "test_predictions_seed42.csv"))
    df["words"] = df["statement"].fillna("").str.split().str.len()
    df["ok"] = df["true"] == df["pred"]
    pool = df[(df["words"] >= 14) & (df["words"] <= 45)]

    def best(mask, col):
        sub = pool[mask].sort_values(col, ascending=False)
        return sub.iloc[0]
    real = best((pool["true"] == "REAL") & pool["ok"], "p_real")
    part = best((pool["true"] == "PARTIALLY TRUE") & pool["ok"], "p_partial")
    fake = best((pool["true"] == "FAKE") & pool["ok"], "p_fake")
    miss = best((pool["true"] == "FAKE") & (pool["pred"] == "REAL"), "p_real")
    miss2 = best((pool["true"] == "REAL") & (pool["pred"] == "FAKE"), "p_fake")
    return {"real": real, "partial": part, "fake": fake, "miss_fake_as_real": miss, "miss_real_as_fake": miss2}, df


def main():
    base = f"http://localhost:{read_port()}"
    os.makedirs(OUT, exist_ok=True)
    work = tempfile.mkdtemp(prefix="fn_cap_")
    chosen, df = pick_statements()
    json.dump({k: {"statement": v["statement"], "true": v["true"], "pred": v["pred"], "p_real": float(v["p_real"]), "p_partial": float(v["p_partial"]), "p_fake": float(v["p_fake"])}
               for k, v in chosen.items()}, open(os.path.join(OUT, "captured_statements.json"), "w", encoding="utf-8"), indent=2)

    # batch CSV: 120 real test statements (40 per true class), with the true label kept as a second column
    parts = [df[df["true"] == c].sample(40, random_state=3) for c in LABELS]
    batch = pd.concat(parts).sample(frac=1, random_state=4)
    batch_path = os.path.join(work, "liar2_test_sample.csv")
    pd.DataFrame({"id": range(1, len(batch) + 1), "statement": batch["statement"].values, "true_label": batch["true"].values}).to_csv(batch_path, index=False)

    # retrain CSV: 600 real training statements, 200 per class (the app's own label names)
    tr = pd.read_csv(os.path.join(ROOT, "data", "liar2", "train.csv"))
    tr["lab3"] = np.where(tr["label"].isin([4, 5]), "REAL", np.where(tr["label"] == 3, "PARTIALLY TRUE", "FAKE"))
    sub = pd.concat([tr[tr["lab3"] == c].sample(200, random_state=5) for c in LABELS]).sample(frac=1, random_state=6)
    retrain_path = os.path.join(work, "liar2_train_600.csv")
    pd.DataFrame({"text": sub["statement"].values, "label": sub["lab3"].values}).to_csv(retrain_path, index=False)

    def shot(page, name, top=False):
        if top:
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(500)
        path = os.path.join(OUT, name)
        page.screenshot(path=path)
        print("saved", os.path.relpath(path, ROOT), flush=True)

    def detect(page, text, name):
        page.goto(base + "/app")
        settle(page, 800)
        page.get_by_label("Article text").fill(text)
        page.wait_for_timeout(400)
        shot(page, name.replace(".png", "_input.png"), top=True)
        page.get_by_role("button", name="Detect fake news").click()
        page.get_by_text("Class probabilities").wait_for()
        settle(page, 2200)
        shot(page, name)

    with sync_playwright() as p:
        browser = launch(p)
        ctx = browser.new_context(viewport=SIZE, color_scheme="dark")
        ctx.add_init_script("localStorage.setItem('truthglow-theme','dark')")
        page = ctx.new_page()

        page.goto(base + "/")
        settle(page, 7000)  # the counters on the landing page animate
        shot(page, "10_liar2_landing.png")

        detect(page, chosen["fake"]["statement"], "11_liar2_detect_fake.png")
        detect(page, chosen["real"]["statement"], "12_liar2_detect_real.png")
        detect(page, chosen["partial"]["statement"], "13_liar2_detect_partial.png")
        detect(page, chosen["miss_fake_as_real"]["statement"], "14_liar2_detect_miss.png")

        page.goto(base + "/app/batch")
        settle(page, 1200)
        page.set_input_files("input[type=file]", batch_path)
        page.get_by_role("button", name="Run batch detection").wait_for()
        shot(page, "15_liar2_batch_preview.png", top=True)
        page.get_by_role("button", name="Run batch detection").click()
        page.get_by_text("Batch verdict distribution").wait_for()
        settle(page, 2200)
        shot(page, "16_liar2_batch_results.png")

        page.goto(base + "/app/analytics")
        page.get_by_text("Confusion matrix").first.wait_for()
        settle(page, 2500)
        shot(page, "17_liar2_analytics.png", top=True)
        page.mouse.wheel(0, 650)
        page.wait_for_timeout(1500)
        shot(page, "18_liar2_analytics_charts.png")

        page.goto(base + "/app/about")
        page.get_by_text("The loaded model").wait_for()
        settle(page, 2000)
        shot(page, "19_liar2_about.png")
        page.goto(base + "/app/retrain")
        settle(page, 1200)
        page.set_input_files("input[type=file]", retrain_path)
        page.get_by_label("Fireflies").fill("4")
        page.get_by_label("Generations").fill("3")
        page.wait_for_timeout(600)
        shot(page, "20_liar2_retrain.png", top=True)
        page.get_by_role("button", name="Retrain model").click()
        page.get_by_role("button", name="Retrain and replace").click()
        page.get_by_text("Training PCA + Firefly + MSVM").wait_for()
        shot(page, "21_liar2_retrain_running.png", top=True)
        page.get_by_text("Retrained successfully").wait_for(timeout=600_000)
        settle(page, 1500)
        shot(page, "22_liar2_retrain_done.png", top=True)

        ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
