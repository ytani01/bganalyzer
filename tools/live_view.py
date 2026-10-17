"""Keep the app open in a phone-sized Chromium window, and reload it whenever the server runs another
commit (after a merge restarts the service). Close the window to stop (TODO-108).

usage: uv run -q --no-project --with playwright python tools/live_view.py [URL]   (default: the local service)
"""
import json
import os
import sys
import urllib.request

from playwright.sync_api import Error, sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("BG_URL", "http://127.0.0.1:8000/")
CHROMIUM = os.environ.get("BG_CHROMIUM", "/usr/bin/chromium")
PHONE = {"width": 412, "height": 915}   # as tools/pi_ui_check.py
EVERY_MS = 2000


def commit():
    """The commit the server runs, or None while it is restarting."""
    try:
        with urllib.request.urlopen(URL.rstrip("/") + "/version", timeout=3) as r:
            return json.load(r).get("commit")
    except (OSError, ValueError):
        return None


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROMIUM, headless=False)
        # no service worker: it would keep serving the old app.js after an update
        context = browser.new_context(viewport=PHONE, is_mobile=True, has_touch=True, device_scale_factor=2,
                                      service_workers="block")
        page = context.new_page()
        seen = commit()
        page.goto(URL)
        print(f"{URL} at {seen}", flush=True)
        try:
            while not page.is_closed():
                page.wait_for_timeout(EVERY_MS)
                now = commit()
                if now and now != seen:
                    seen = now
                    page.reload()
                    print(f"reloaded: {now}", flush=True)
        except Error:   # the window was closed
            pass


if __name__ == "__main__":
    main()
