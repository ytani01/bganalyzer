"""TODO-084 verifier: 「四隅を固定する」(#keep-corners) on the PWA at 127.0.0.1:8765 (a test server, not the 8000 service).

    uv run -q --no-project --with playwright python archives/agents/TODO-084/check_ui.py
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path("/home/ytani/work/bganalyzer")
URL = "http://127.0.0.1:8765/"
CHROMIUM = "/usr/bin/chromium"
TRUTH = json.loads((ROOT / "samples/screen2.truth.json").read_text())
PHOTO = str(ROOT / "samples" / TRUTH["image"])
CORNERS = TRUTH["corners_TL_TR_BR_BL"]

# as tools/pi_ui_check.py: no speech, no share sheet
INIT = """
window.__spoken = [];
if (window.speechSynthesis) speechSynthesis.speak = (u) => { window.__spoken.push(u.text); };
delete Navigator.prototype.canShare; delete Navigator.prototype.share;
"""


def open_app(browser):
    page = browser.new_page(viewport={"width": 412, "height": 915}, accept_downloads=True)
    page.add_init_script(INIT)
    page.alerts = []
    page.on("dialog", lambda d: (page.alerts.append(d.message), d.dismiss()))
    page.goto(URL)
    page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
    return page


def pick(page):
    page.set_input_files("#file", PHOTO)
    page.wait_for_function("BgApp.state.cornerGuess !== 'finding'", timeout=60000)
    page.click(f'.seg[data-name="homePick"] [data-value="{TRUTH["home"]}"]')
    page.click(f'.seg[data-name="bottomColour"] [data-value="{TRUTH["bottom_colour"]}"]')


def state_of(page):
    return page.evaluate("({keep: BgApp.state.keepCorners, guess: BgApp.state.cornerGuess, step: BgApp.state.step,"
                         " n: BgApp.state.corners.length, moved: BgApp.state.cornersMoved})")


def read(page):
    """Press 盤面を読み取る and wait for a new geometry (not the old one from before)."""
    page.evaluate("window.__g0 = BgApp.state.geometry")
    sent = page.evaluate("BgApp.state.corners")
    page.click("#recognize")
    page.wait_for_function("BgApp.state.geometry !== window.__g0 && !BgApp.state.busy", timeout=120000)
    geo = page.evaluate("BgApp.state.geometry.corners")
    after = page.evaluate("BgApp.state.corners")
    return sent, geo, after


def maxdiff(a, b):
    return max(abs(x - u) for p, q in zip(a, b) for x, u in zip(p, q))


def fmt(pts):
    return [[round(x, 1), round(y, 1)] for x, y in pts]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROMIUM)
        page = open_app(browser)

        # a. a new photo: the box is off
        pick(page)
        print("a", state_of(page), "checkbox=", page.is_checked("#keep-corners"), "alerts=", page.alerts)

        # b. reset, then 4 real taps on the canvas: the box turns on
        page.click("#corner-reset")
        box = page.locator("#photo-canvas").bounding_box()
        print("b canvas box", box)
        for fx, fy in [(0.3, 0.3), (0.7, 0.3), (0.7, 0.7), (0.3, 0.7)]:
            page.mouse.click(box["x"] + box["width"] * fx, box["y"] + box["height"] * fy)
            page.wait_for_timeout(300)
        print("b", state_of(page), "checkbox=", page.is_checked("#keep-corners"), "alerts=", page.alerts)

        # c. the true corners set by update, read with the box on
        page.evaluate("c => BgApp.update({ corners: c })", CORNERS)
        sent, geo, after = read(page)
        print("c sent=", fmt(sent))
        print("c geometry=", fmt(geo))
        print("c maxdiff(geometry, sent)=", round(maxdiff(geo, sent), 3),
              " maxdiff(geometry, state.corners after)=", round(maxdiff(geo, after), 3),
              " state=", state_of(page), "alerts=", page.alerts)

        # d. back to the corners screen, box off, read again
        page.click("#back")
        page.wait_for_function("BgApp.state.step === 'corners'", timeout=30000)
        print("d before uncheck", state_of(page), "checkbox=", page.is_checked("#keep-corners"))
        page.locator("label:has(#keep-corners)").click()
        print("d after uncheck", state_of(page), "checkbox=", page.is_checked("#keep-corners"))
        sent2, geo2, after2 = read(page)
        print("d sent=", fmt(sent2))
        print("d geometry=", fmt(geo2))
        print("d maxdiff(geometry, sent)=", round(maxdiff(geo2, sent2), 3),
              " state=", state_of(page), "alerts=", page.alerts)

        # e. box on again (an extra step: e is only meaningful from the on state), then pick the same photo
        page.click("#back")
        page.wait_for_function("BgApp.state.step === 'corners'", timeout=30000)
        page.locator("label:has(#keep-corners)").click()
        print("e before re-pick", state_of(page), "checkbox=", page.is_checked("#keep-corners"))
        pick(page)
        print("e after re-pick", state_of(page), "checkbox=", page.is_checked("#keep-corners"),
              "alerts=", page.alerts)

        browser.close()


if __name__ == "__main__":
    main()
