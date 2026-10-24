"""Layout / console / accessibility sweep: every route at 360, 768 and 1440 px, in light and dark mode.

Needs the app running. Fails on horizontal overflow, console errors or failed requests, and reports any form
control without an accessible name. Screenshots of the phone layout go to docs/screenshots/mobile_*.png.

    python scripts/check_layout.py [--base http://localhost:5306]
"""
import argparse
import sys
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'docs' / 'screenshots'
parser = argparse.ArgumentParser()
parser.add_argument('--base', default='http://localhost:5306')
args = parser.parse_args()
BASE = args.base.rstrip('/')

ROUTES = ['/', '/login', '/app', '/app/history', '/app/thresholds', '/app/research', '/app/about', '/app/missing']
SIZES = [(360, 740), (768, 1024), (1440, 900)]
problems = []


def main():
    demo = requests.get(BASE + '/api/auth/demo', timeout=10).json()
    token = requests.post(BASE + '/api/auth/login', json=demo, timeout=10).json()['token']
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception:
            browser = p.chromium.launch(channel='chrome')
        for theme in ('dark', 'light'):
            for w, h in SIZES:
                ctx = browser.new_context(viewport={'width': w, 'height': h}, color_scheme=theme)
                ctx.add_init_script(f"localStorage.setItem('smartrider-token','{token}');localStorage.setItem('smartrider-theme','{theme}')")
                page = ctx.new_page()
                errors = []
                page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
                page.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
                page.on('requestfailed', lambda r: errors.append(f'requestfailed: {r.url}'))
                for route in ROUTES:
                    page.goto(BASE + route)
                    page.wait_for_load_state('networkidle')
                    page.wait_for_timeout(900)
                    height = page.evaluate('document.documentElement.scrollHeight')
                    for y in range(0, height, 600):          # trigger scroll reveals
                        page.mouse.wheel(0, 600)
                        page.wait_for_timeout(60)
                    page.evaluate('window.scrollTo(0,0)')
                    page.wait_for_timeout(300)
                    over = page.evaluate('document.documentElement.scrollWidth - window.innerWidth')
                    dark = page.evaluate("document.documentElement.classList.contains('dark')")
                    unnamed = page.evaluate("""() => [...document.querySelectorAll('input,select,textarea,button')]
                        .filter(e => e.type !== 'hidden' && !e.closest('[aria-hidden=true]'))
                        .filter(e => !(e.getAttribute('aria-label') || e.getAttribute('aria-labelledby') || e.textContent.trim()
                                       || (e.labels && e.labels.length) || e.title || e.getAttribute('role') === 'combobox' && e.textContent.trim()))
                        .map(e => e.outerHTML.slice(0, 90))""")
                    tag = f'{theme} {w}px {route}'
                    if over > 0:
                        problems.append(f'OVERFLOW {over}px  {tag}')
                    if (theme == 'dark') != dark:
                        problems.append(f'THEME not applied  {tag}')
                    for u in unnamed:
                        problems.append(f'UNNAMED control {u}  {tag}')
                    if route == '/app' and w == 360 and theme == 'dark':
                        OUT.mkdir(parents=True, exist_ok=True)
                    if w == 360 and theme == 'dark' and route in ('/', '/app', '/app/history', '/app/research'):
                        name = {'/': 'landing', '/app': 'monitor', '/app/history': 'history', '/app/research': 'research'}[route]
                        page.screenshot(path=str(OUT / f'mobile_{name}.png'))
                    print('ok  ' if over <= 0 else 'BAD ', tag)
                bad = [e for e in errors if 'the server responded with a status of 404' not in e]
                for e in bad:
                    problems.append(f'CONSOLE {theme} {w}px: {e}')
                ctx.close()
        browser.close()
    print()
    if problems:
        print(f'{len(problems)} problem(s):')
        for line in dict.fromkeys(problems):
            print(' -', line)
        sys.exit(1)
    print('Layout sweep clean: no overflow, theme applied everywhere, no unnamed controls, console clean.')


if __name__ == '__main__':
    main()
