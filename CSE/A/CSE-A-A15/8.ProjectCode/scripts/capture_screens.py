"""Capture every CipherVeil screen at 1440x900 with real data, driving the UI like a user.

Needs the app running (run.bat: backend 8315, frontend 5315) and a fresh database, then:
    pip install playwright   (Chrome is used through channel="chrome")
    python scripts/capture_screens.py
Writes docs/screenshots/<nn>_<screen>.png. Everything on screen is produced by the real backend:
keys are generated, files are encrypted into covers, received, attacked and logged.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://localhost:5315"
ARGS = ["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--disable-gpu-sandbox"]
notes = []


def shot(page, name, wait=0.8, full=False):
    page.wait_for_timeout(int(wait * 1000))
    p = OUT / f"{name}.png"
    page.screenshot(path=str(p), full_page=full)
    notes.append(name)
    print("saved", p.name)


def pick(page, label, startswith):
    """Choose the option whose text starts with `startswith` in the select labelled `label`."""
    sel = page.get_by_label(label, exact=True)
    value = sel.evaluate("(el, s) => [...el.options].find(o => o.text.startsWith(s))?.value", startswith)
    assert value is not None, f"{label}: no option starting {startswith!r}"
    sel.select_option(value)


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True, args=ARGS)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        page = ctx.new_page()
        page.set_default_timeout(60000)

        page.goto(BASE + "/")
        page.wait_for_timeout(7000)               # count-up counters and backdrop settle
        shot(page, "01_landing", wait=0.5)
        page.mouse.wheel(0, 900)
        shot(page, "02_landing_features", wait=2.5)

        page.goto(BASE + "/login")
        shot(page, "03_login", wait=1.5)
        page.get_by_role("button", name="Sign in", exact=True).last.click()
        page.wait_for_url("**/keys")

        # ---- keys
        page.get_by_label("Name").first.fill("Receiver key")
        page.get_by_label("Key size").select_option("3072")
        page.get_by_role("button", name="Generate", exact=True).click()
        page.get_by_text("Receiver key", exact=True).first.wait_for()
        page.wait_for_timeout(1500)
        page.get_by_label("Name").first.fill("Spare key")
        page.get_by_label("Key size").select_option("3072")
        page.get_by_role("button", name="Generate", exact=True).click()
        page.get_by_text("Spare key", exact=True).first.wait_for()
        page.wait_for_timeout(1500)
        # a partner's public key arrives as a PEM; make one with the same library the backend uses
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        partner = rsa.generate_private_key(public_exponent=65537, key_size=2048).public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
        page.get_by_label("Name").nth(1).fill("Partner office (public only)")
        page.get_by_label("PEM").fill(partner)
        page.get_by_role("button", name="Import", exact=True).click()
        page.get_by_text("Partner office (public only)").first.wait_for()
        page.get_by_label("Name").first.fill("My receiving key")
        page.wait_for_timeout(6500)               # let the toast go away
        shot(page, "04_keys", wait=0.5)

        token = page.evaluate("localStorage.getItem('cv_token')")

        # ---- send: first message (PDF memo into the astronaut photo)
        page.goto(BASE + "/send")
        page.get_by_label("Receiver's key").wait_for()
        pick(page, "Receiver's key", "Receiver key")
        pick(page, "File to protect", "confidential_memo.pdf")
        pick(page, "Cover image", "astronaut_512x512.png")
        shot(page, "05_send_form", wait=1.0)
        page.get_by_role("button", name="Encrypt and hide").click()
        page.get_by_text("SHA-256 of the file you sent").wait_for()
        page.wait_for_timeout(2500)
        shot(page, "06_send_result", wait=1.0)
        ops = page.evaluate("""async (t) => (await fetch('/api/log?op=send', {headers: {Authorization: 'Bearer ' + t}})).json()""", token)
        first_op = ops[0]["id"]

        # ---- send: blocked by the capacity check (too small a cover)
        pick(page, "File to protect", "confidential_memo.pdf")
        pick(page, "Cover image", "coffee_small_200x200.png")
        page.wait_for_timeout(600)
        page.get_by_role("button", name="Encrypt and hide").click()
        page.wait_for_timeout(2500)
        shot(page, "07_send_capacity_blocked", wait=0.6)

        # ---- more messages so the log, benchmark and analysis have variety
        for payload, cover in (("accounts.csv", "coffee_600x400.png"), ("settings.json", "generated_landscape_1280x720.png"),
                               ("meeting_notes.txt", "rocket_640x427.png")):
            pick(page, "File to protect", payload)
            pick(page, "Cover image", cover)
            page.get_by_role("button", name="Encrypt and hide").click()
            page.wait_for_timeout(2500)
        ops = page.evaluate("""async (t) => (await fetch('/api/log?op=send', {headers: {Authorization: 'Bearer ' + t}})).json()""", token)
        last_op = ops[0]["id"]

        # ---- analysis of the first message
        page.goto(f"{BASE}/analysis?op={first_op}")
        page.get_by_text("Imperceptibility").first.wait_for()
        page.wait_for_timeout(3500)
        shot(page, "08_analysis", wait=1.0)
        page.get_by_text("Histograms", exact=True).first.scroll_into_view_if_needed()
        page.mouse.wheel(0, 250)
        page.wait_for_timeout(3500)
        shot(page, "09_analysis_histograms", wait=1.0)
        page.get_by_text("Bit planes", exact=True).first.scroll_into_view_if_needed()
        page.mouse.wheel(0, 520)
        page.wait_for_timeout(3500)
        shot(page, "10_analysis_bitplanes", wait=1.0)

        # ---- receive: success
        page.goto(f"{BASE}/receive?op={first_op}")
        page.get_by_label("Your private key").wait_for()
        pick(page, "Your private key", "Receiver key")
        page.wait_for_timeout(500)
        page.get_by_role("button", name="Extract and decrypt").click()
        page.get_by_text("SHA-256 of the restored file").wait_for()
        page.wait_for_timeout(2500)
        shot(page, "11_receive_result", wait=1.0)

        # ---- receive: wrong key (the spare keypair was not the receiver)
        page.goto(f"{BASE}/receive?op={first_op}")
        page.get_by_label("Your private key").wait_for()
        pick(page, "Your private key", "Spare key")
        page.wait_for_timeout(500)
        page.get_by_role("button", name="Extract and decrypt").click()
        page.wait_for_timeout(3000)
        shot(page, "12_receive_wrong_key", wait=0.6)

        # ---- robustness
        page.goto(f"{BASE}/robustness?op={first_op}")
        page.get_by_role("button", name="Run robustness tests").wait_for()
        page.get_by_role("button", name="Run robustness tests").click()
        page.get_by_text("payload survives").first.wait_for()
        page.wait_for_timeout(3000)
        shot(page, "13_robustness_results", wait=1.0)
        page.mouse.wheel(0, 650)
        shot(page, "14_robustness_detail", wait=2.5)
        page.get_by_text("Capacity per cover").first.scroll_into_view_if_needed()
        page.wait_for_timeout(2500)
        shot(page, "15_capacity_table", wait=1.0)
        page.get_by_role("button", name="Run benchmark").click()
        page.get_by_text("does not fit").first.wait_for(timeout=180000)
        page.wait_for_timeout(2000)
        page.get_by_text("Speed and quality benchmark").first.scroll_into_view_if_needed()
        page.mouse.wheel(0, 380)
        page.wait_for_timeout(2500)
        shot(page, "16_benchmark", wait=1.0)

        # ---- log
        page.goto(BASE + "/log")
        page.get_by_text("Operations", exact=True).first.wait_for()
        page.wait_for_timeout(3000)
        shot(page, "17_log", wait=1.0)
        page.locator("button", has_text=f"#{last_op}").first.click()
        page.wait_for_timeout(1500)
        page.mouse.wheel(0, 800)
        shot(page, "18_log_detail", wait=1.0)

        browser.close()
    (OUT / "_inventory.json").write_text(json.dumps({"screens": notes, "first_op": first_op, "last_op": last_op}, indent=1))
    print("done", len(notes))


if __name__ == "__main__":
    sys.exit(main())
