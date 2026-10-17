"""Keep the app open in a phone-sized Chromium window, and reload it whenever the server runs another
commit (after a merge restarts the service). Close the window to stop (TODO-108).
Downloads (「ファイルに書き出す」) are saved to ~/Downloads, not to Playwright's folder that goes with the window (TODO-127).

usage: uv run -q --no-project --with playwright python tools/live_view.py [URL]   (default: the local service)

With it open, tools/pi_ui_check.py and tools/ui_snapshot.py run with BG_CDP=http://127.0.0.1:9222 drive this
browser (in a window of their own) instead of a hidden one, so what they do can be watched.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import Error, sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("BG_URL", "http://127.0.0.1:8000/")
CHROMIUM = os.environ.get("BG_CHROMIUM", "/usr/bin/chromium")
# a Pixel 9a (1080 x 2424 at 2.625: 412 x 923 CSS px) less Chrome's bars, in the proportion of Playwright's
# Pixel 8a (412 x 839 of 914). 412 x 915 with the window's frame did not fit a 1080-high screen (TODO-110)
PHONE = {"width": 412, "height": 848}
DENSITY = 2.625
CDP_PORT = 9222   # other tools drive this browser with BG_CDP=http://127.0.0.1:9222, to be watched here
EVERY_MS = 2000
DOWNLOADS = Path.home() / "Downloads"


def commit():
    """The commit the server runs, or None while it is restarting."""
    try:
        with urllib.request.urlopen(URL.rstrip("/") + "/version", timeout=3) as r:
            return json.load(r).get("commit")
    except (OSError, ValueError):
        return None


def save(download):
    """Save a download to ~/Downloads, as name (1).ext and so on when the name is taken."""
    DOWNLOADS.mkdir(exist_ok=True)
    name = Path(download.suggested_filename)
    path, n = DOWNLOADS / name, 0
    while path.exists():
        n += 1
        path = DOWNLOADS / f"{name.stem} ({n}){name.suffix}"
    try:
        download.save_as(path)
    except Error as e:   # raised again in the main loop, it would read as the window closed
        print(f"not saved: {path}: {e}", flush=True)
        return
    print(f"saved: {path}", flush=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROMIUM, headless=False, args=[f"--remote-debugging-port={CDP_PORT}"])
        # no service worker: it would keep serving the old app.js after an update
        context = browser.new_context(viewport=PHONE, is_mobile=True, has_touch=True, device_scale_factor=DENSITY,
                                      service_workers="block")
        context.on("page", lambda pg: pg.on("download", save))
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
