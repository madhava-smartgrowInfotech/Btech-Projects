"""Walk every SignSpeak screen in a real browser and save 1440x900 screenshots to docs/screenshots/.

Needs the app running (run.bat, or the API on :8316 and `npm run dev` on :5316) and `data/` filled
(see scripts/prepare_data.py). If no model is trained yet it trains one through the UI first.

A webcam is not available in a headless browser, so Chromium's fake camera is fed a short video built
from real ASL alphabet photos (held-out ones from archive/ when present; for each letter the first of 12 that the
trained model reads correctly at >= 80% confidence) placed inside the ROI box, spelling H E L L O. The model is
only ~80% accurate on arbitrary photos, so this keeps the screenshot readable. Everything the screens show comes from the live API.

    pip install playwright && playwright install chromium
    python scripts/capture_screens.py [--epochs 12] [--base http://127.0.0.1:5316]
"""

from __future__ import annotations

import argparse
import random
import sys
import tempfile
from pathlib import Path

import cv2
import httpx
import numpy as np
from playwright.sync_api import Page, expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
DATA = ROOT / "data"
ARCHIVE = ROOT / "archive" / "asl_alphabet_train" / "asl_alphabet_train"
SPELL = ["H", "E", "L", "nothing", "L", "O", "nothing"]
W, H, FPS, SEG_FRAMES = 480, 270, 10, 40        # 4 s per letter, so the ~1 s hold rule commits each one


def candidates(cls: str, n: int = 12) -> list[np.ndarray]:
    """Real photos of `cls`, preferring ones that were not copied into data/ (held out from training)."""
    rng = random.Random(7)
    src = ARCHIVE / cls
    files: list[Path] = []
    if src.is_dir():
        used = {p.name for p in (DATA / cls).glob("*.jpg")}
        files = [p for p in sorted(src.glob("*.jpg")) if p.name not in used]
    if not files:
        files = sorted((DATA / cls).glob("*.*"))
    return [cv2.imread(str(p)) for p in rng.sample(files, min(n, len(files)))]


def sample_image(cls: str, api: str) -> np.ndarray:
    """The first candidate photo the live model reads correctly with confidence >= 0.8 (keeps the demo legible);
    falls back to the first candidate. The model's overall accuracy is on the Model screen."""
    photos = candidates(cls)
    try:
        client = httpx.Client(base_url=api + "/api", timeout=30)
        for photo in photos:
            frame = np.full((540, 960, 3), (46, 38, 34), np.uint8)
            frame[90:390, 620:920] = cv2.resize(photo, (300, 300))
            sid = client.post("/recognize/session").json()["session_id"]
            r = client.post("/recognize/frame", files={"frame": ("f.jpg", cv2.imencode(".jpg", frame)[1].tobytes(), "image/jpeg")},
                            data={"session_id": sid})
            if r.status_code == 200 and r.json()["label"] == cls and r.json()["confidence"] >= 0.8:
                return photo
    except httpx.HTTPError:
        pass
    return photos[0]


def build_fake_camera(path: Path, api: str) -> None:
    """y4m video: each letter's photo sits where the (mirrored) ROI box lands after the page mirrors the frame."""
    with open(path, "wb") as f:
        f.write(f"YUV4MPEG2 W{W} H{H} F{FPS}:1 Ip A1:1 C420jpeg\n".encode())
        for letter in SPELL:
            photo = cv2.flip(cv2.resize(sample_image(letter, api), (150, 150)), 1)   # grab() mirrors it back
            frame = np.full((H, W, 3), (46, 38, 34), np.uint8)
            frame[45:195, 20:170] = photo        # ROI x 620..920 / y 90..390 of 960x540, mirrored, halved
            yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV_I420)
            for _ in range(SEG_FRAMES):
                f.write(b"FRAME\n")
                f.write(yuv.tobytes())


def shot(page: Page, name: str, **kw) -> None:
    page.wait_for_timeout(700)
    page.screenshot(path=str(OUT / f"{name}.png"), **kw)
    print("saved", name)


def scroll_through(page: Page) -> None:
    height = page.evaluate("document.documentElement.scrollHeight")
    y = 0
    while y < height:
        y += 500
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(120)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:5316")
    ap.add_argument("--api", default="http://127.0.0.1:8316")
    ap.add_argument("--epochs", default="12")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    # ---- train through the UI when no model exists (the camera clip below needs the trained model) ----
    with sync_playwright() as p0:
        b0 = p0.chromium.launch()
        pg0 = b0.new_page(viewport={"width": 1440, "height": 900})
        pg0.goto(args.base + "/app/model", wait_until="networkidle")
        if pg0.get_by_text("No trained model yet").count():
            pg0.goto(args.base + "/app/train", wait_until="networkidle")
            pg0.get_by_label("Epochs").fill(args.epochs)
            pg0.get_by_role("button", name="Start training").click()
            print("training started...")
            expect(pg0.get_by_text("Finished", exact=True)).to_be_visible(timeout=40 * 60 * 1000)
        b0.close()

    tmp = Path(tempfile.mkdtemp(prefix="signspeak_cam_"))
    video = tmp / "spell.y4m"
    build_fake_camera(video, args.api)
    chrome_args = [
        "--use-fake-ui-for-media-stream",
        "--use-fake-device-for-media-stream",
        f"--use-file-for-fake-video-capture={video}",
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(args=chrome_args)

        def new_page(scheme: str):
            ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme=scheme, permissions=["camera"])
            pg = ctx.new_page()
            problems: list[str] = []
            pg.on("console", lambda m: problems.append(f"console {m.type}: {m.text}") if m.type == "error" else None)
            pg.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
            pg.on("response", lambda r: problems.append(f"HTTP {r.status} {r.url}") if r.status >= 400 else None)
            return ctx, pg, problems

        # ---- landing page, light and dark ----
        for scheme, n in (("dark", "01"), ("light", "02")):
            ctx, pg, problems = new_page(scheme)
            pg.goto(args.base + "/", wait_until="networkidle")
            scroll_through(pg)
            shot(pg, f"{n}_landing_{scheme}")
            if scheme == "dark":
                pg.locator("#features").scroll_into_view_if_needed()
                pg.evaluate("document.getElementById('features').scrollIntoView()")
                shot(pg, "01b_landing_features_dark")
            ctx.close()
            if problems:
                print("PROBLEMS", scheme, problems)

        ctx, pg, problems = new_page("dark")

        pg.goto(args.base + "/app", wait_until="networkidle")
        shot(pg, "03_dashboard")

        # ---- recognize: spell H E L L O with the fake camera ----
        pg.goto(args.base + "/app/recognize", wait_until="networkidle")
        pg.get_by_role("button", name="Start camera").first.click()
        sentence = pg.get_by_label("Sentence", exact=True)
        expect(sentence).not_to_have_value("", timeout=60_000)
        pg.wait_for_function("document.querySelector('textarea').value.length >= 3", timeout=120_000)
        pg.wait_for_timeout(20_000)                  # let a few more letters of the looping H E L L O clip land
        shot(pg, "04_recognize")
        print("sentence:", sentence.input_value())
        pg.get_by_role("button", name="Stop camera").click()

        # ---- collect: capture + burst on class L, then remove those files again ----
        before = {p.name for p in (DATA / "L").glob("*")}
        pg.goto(args.base + "/app/collect", wait_until="networkidle")
        pg.get_by_role("button", name="Start camera").first.click()
        expect(pg.get_by_alt_text("Segmentation preview of the hand")).to_be_visible(timeout=30_000)
        pg.get_by_role("button", name="L: ", exact=False).first.click()      # pick class L in the coverage grid
        pg.get_by_label("Burst size").fill("5")
        pg.get_by_role("button", name="Capture 1 image").click()
        expect(pg.get_by_text("Saved 1 image for L")).to_be_visible(timeout=15_000)
        pg.get_by_role("button", name="Burst capture").click()
        expect(pg.get_by_text("Done!")).to_be_visible(timeout=30_000)
        pg.wait_for_timeout(1000)
        shot(pg, "05_collect")                      # camera still running: live view + mask preview
        pg.get_by_role("button", name="Stop camera").click()
        for f in (DATA / "L").glob("*"):
            if f.name not in before:
                f.unlink()

        # ---- train screen (shows the last run's charts only after a run in this server session) ----
        pg.goto(args.base + "/app/train", wait_until="networkidle")
        shot(pg, "06_train")
        pg.evaluate("document.querySelector('main').scrollIntoView(); window.scrollTo(0, document.body.scrollHeight)")
        shot(pg, "06b_train_charts")

        # ---- model performance ----
        pg.goto(args.base + "/app/model", wait_until="networkidle")
        shot(pg, "07_model_per_class")
        pg.get_by_role("tab", name="Confusion matrix").click()
        shot(pg, "07b_model_confusion")
        pg.get_by_role("tab", name="Training curves").click()
        shot(pg, "07c_model_curves")

        # ---- about ----
        pg.goto(args.base + "/app/about", wait_until="networkidle")
        shot(pg, "08_about")

        print("\n".join(problems) if problems else "console clean on every app screen")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
