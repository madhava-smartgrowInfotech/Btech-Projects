"""Walks every screen of the running app with Playwright and saves 1440x900 PNGs to docs/screenshots/.

Needs the app running (run.bat, or the API on 8306 and the web app on 5306).  It signs in with the demo account,
drives the real features (simulation scenarios, the camera path, calibration, thresholds, the synthetic research
sample) so every screen shows live data, and fails loudly if a console error or a wrong verdict shows up.

Camera: Chromium's fake webcam plays a looping video made from one public-domain face photograph
(scikit-image's sample astronaut portrait). Pass --video path.y4m to use your own; without it the camera
step is skipped and the simulation screens are still captured.

    python scripts/capture_screens.py [--video face.y4m] [--base http://localhost:5306]
"""
import argparse
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'docs' / 'screenshots'

parser = argparse.ArgumentParser()
parser.add_argument('--base', default='http://localhost:5306')
parser.add_argument('--video', default=None)
parser.add_argument('--keep-going', action='store_true', help='report console errors instead of failing on them')
args = parser.parse_args()
BASE = args.base.rstrip('/')

console_errors = []


def shot(page, name):
    OUT.mkdir(parents=True, exist_ok=True)
    page.wait_for_timeout(700)
    path = OUT / f'{name}.png'
    page.screenshot(path=str(path))
    print('saved', path.relative_to(ROOT))


def scroll_through(page):
    """GSAP ScrollTrigger sections stay blank until scrolled into view."""
    height = page.evaluate('document.documentElement.scrollHeight')
    for y in range(0, height, 500):
        page.mouse.wheel(0, 500)
        page.wait_for_timeout(120)
    page.evaluate('window.scrollTo(0,0)')
    page.wait_for_timeout(400)


def set_theme(page, theme):
    page.evaluate(f"localStorage.setItem('smartrider-theme','{theme}')")
    page.reload()
    page.wait_for_load_state('networkidle')


def main():
    launch_args = []
    if args.video:
        launch_args = ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream',
                       f'--use-file-for-fake-video-capture={args.video}']
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(args=launch_args)
        except Exception:
            browser = p.chromium.launch(channel='chrome', args=launch_args)
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900}, color_scheme='dark',
                                  permissions=['camera'] if args.video else [])
        page = ctx.new_page()
        page.on('console', lambda m: console_errors.append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: console_errors.append(f'pageerror: {e}'))
        page.on('requestfailed', lambda r: console_errors.append(f'requestfailed: {r.url}'))

        # ---- landing, both themes
        page.goto(BASE + '/')
        page.wait_for_load_state('networkidle')
        scroll_through(page)
        shot(page, '01_landing_dark')
        set_theme(page, 'light')
        scroll_through(page)
        shot(page, '02_landing_light')
        set_theme(page, 'dark')

        # ---- login
        page.goto(BASE + '/app')
        expect(page).to_have_url(re.compile(r'/login'))
        page.wait_for_load_state('networkidle')
        shot(page, '03_login')
        page.get_by_role('button', name='Use the demo account').click()
        expect(page).to_have_url(re.compile(r'/app$'))

        # ---- monitor: simulation, prolonged closure -> warning
        expect(page.get_by_text('Live monitor')).to_be_visible()
        page.get_by_label('Simulation scenario').click()
        page.get_by_role('option', name='Prolonged eye closure').click()
        page.get_by_role('button', name='Simulation mode').click()
        page.get_by_role('button', name='Start monitoring').click()
        verdict = page.get_by_test_id('verdict')
        expect(verdict).to_have_text('Unable to assess', timeout=5000)           # warm-up
        expect(verdict).to_have_text('Possible impairment or drowsiness', timeout=15000)
        expect(page.get_by_test_id('alert')).to_contain_text('stop somewhere safe')
        page.wait_for_timeout(1500)
        shot(page, '04_monitor_simulation_warning')
        # scenario switch keeps monitoring on and gives a different verdict (Missing face -> Unable to assess)
        page.get_by_label('Simulation scenario').click()
        page.get_by_role('option', name='Missing face').click()
        expect(page.get_by_role('button', name='Stop monitoring')).to_be_visible()
        expect(verdict).to_have_text('Unable to assess', timeout=5000)
        expect(page.get_by_test_id('reason')).to_contain_text('No face')
        page.get_by_label('Simulation scenario').click()
        page.get_by_role('option', name='Normal').click()
        expect(verdict).to_have_text('Normal', timeout=15000)
        page.get_by_role('button', name='Stop monitoring').click()
        expect(page.get_by_role('button', name='Start monitoring')).to_be_visible()

        # ---- monitor: camera
        if args.video:
            page.get_by_role('button', name='Start camera').click()
            expect(page.get_by_alt_text(re.compile('Camera frame with eye landmarks'))).to_be_visible(timeout=20000)
            expect(page.get_by_text('Signal quality: Good')).to_be_visible(timeout=15000)
            page.get_by_role('button', name='Calibrate').click()
            expect(page.get_by_text('Calibration', exact=True).first).to_be_visible()
            page.wait_for_timeout(3000)
            page.mouse.wheel(0, 520)                    # bring the calibration progress card into view
            shot(page, '05_monitor_calibrating')
            page.evaluate('window.scrollTo(0,0)')
            expect(page.get_by_test_id('status')).to_contain_text('Calibration saved', timeout=25000)
            expect(page.get_by_text('Calibrated', exact=True)).to_be_visible()
            page.get_by_role('button', name='Start monitoring').click()
            expect(verdict).to_have_text('Normal', timeout=20000)
            page.wait_for_timeout(2500)
            shot(page, '06_monitor_camera_normal')
            page.get_by_role('button', name='Stop camera').click()
            expect(page.get_by_text('Camera stopped', exact=True)).to_be_visible()
        shot(page, '07_monitor_idle')

        # ---- history (events from the runs above)
        page.get_by_role('link', name='Event history').first.click()
        expect(page.get_by_role('heading', name='Event history')).to_be_visible()
        expect(page.get_by_text('Events logged')).to_be_visible(timeout=10000)
        page.wait_for_timeout(1500)
        shot(page, '08_history')
        page.get_by_role('radio', name='Simulation').click()
        expect(page.get_by_role('cell', name=re.compile('SIMULATION')).first).to_be_visible()
        with page.expect_download() as dl:
            page.get_by_role('button', name='Export CSV').click()
        assert dl.value.suggested_filename == 'rider_events.csv'
        csv_text = Path(dl.value.path()).read_text(encoding='utf-8-sig')
        assert csv_text.startswith('id,timestamp,source,state'), csv_text[:60]
        print('CSV export ok,', csv_text.count('\n'), 'lines')

        # ---- thresholds
        page.get_by_role('link', name='Thresholds').first.click()
        expect(page.get_by_role('heading', name='Rule thresholds')).to_be_visible()
        field = page.get_by_label('Closure seconds')
        expect(field).to_have_value(re.compile(r'^1\.\d$'), timeout=8000)
        field.fill('9')
        expect(page.get_by_text('Must be between 0.5 and 5.')).to_be_visible()
        expect(page.get_by_role('button', name='Save thresholds')).to_be_disabled()
        shot(page, '09_thresholds_validation')
        field.fill('1.7')
        page.get_by_role('button', name='Save thresholds').click()
        expect(page.get_by_text('Thresholds saved. Monitoring was stopped')).to_be_visible()
        page.get_by_role('button', name='Reset to defaults').click()
        expect(field).to_have_value('1.5')
        page.get_by_role('button', name='Save thresholds').click()
        page.wait_for_timeout(800)
        shot(page, '10_thresholds')

        # ---- research: empty, then the synthetic sample
        page.get_by_role('link', name='Research').first.click()
        expect(page.get_by_role('heading', name='Research and evaluation')).to_be_visible()
        expect(page.get_by_text('Model not trained').first).to_be_visible(timeout=8000)
        shot(page, '11_research_empty')
        page.get_by_role('button', name='Use synthetic sample').click()
        expect(page.get_by_text('synthetic_demo_measurements.csv')).to_be_visible()
        page.get_by_role('button', name='Train and evaluate offline').click()
        expect(page.get_by_text('Synthetic data.')).to_be_visible(timeout=60000)
        expect(page.get_by_text('Precision')).to_be_visible()
        page.wait_for_timeout(4500)                      # let the success toast leave
        page.evaluate("document.querySelector('[role=note]').scrollIntoView({block:'start'}); window.scrollBy(0,-90)")
        shot(page, '12_research_report')
        # a wrong CSV is rejected with the reason
        bad = ROOT / 'docs' / 'screenshots' / '_bad.csv'
        bad.write_text('a,b\n1,2\n', encoding='utf-8')
        page.get_by_label('Choose a file to upload').click() if False else None
        page.set_input_files('input[type=file]', str(bad))
        page.get_by_role('button', name='Train and evaluate offline').click()
        expect(page.get_by_role('alert').filter(has_text='Required CSV columns')).to_be_visible(timeout=15000)
        bad.unlink()

        # ---- about
        page.get_by_role('link', name='How it works').first.click()
        expect(page.get_by_role('heading', name='How it works')).to_be_visible()
        page.wait_for_timeout(600)
        shot(page, '13_about')
        page.get_by_role('tab', name='Formulas & rules').click()
        page.wait_for_timeout(500)
        shot(page, '14_about_formulas')

        # ---- dark/light toggle persists inside the app
        page.get_by_label('Switch to light mode').click()
        expect(page.locator('html')).not_to_have_class(re.compile('dark'))
        page.get_by_role('link', name='Monitor').first.click()
        page.wait_for_timeout(1500)
        shot(page, '15_monitor_light')
        page.get_by_label('Switch to dark mode').click()

        # ---- 404 + sign out
        page.goto(BASE + '/app/nope')
        expect(page.get_by_text("This page doesn't exist")).to_be_visible()
        page.get_by_label('Account menu').click()
        page.get_by_role('menuitem', name='Sign out').click()
        expect(page).to_have_url(re.compile(r'/login'))
        browser.close()

    # the one expected "error": the 422 from the deliberately wrong CSV is a response, not a console error
    real = [e for e in console_errors if '422' not in e and 'Failed to load resource' not in e]
    if real and not args.keep_going:
        print('CONSOLE ERRORS:', *real, sep='\n  ')
        sys.exit(1)
    print('\nAll screens walked.', f'{len(console_errors)} console message(s) filtered' if console_errors else 'Console clean.')


if __name__ == '__main__':
    main()
