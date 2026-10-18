"""TODO-144 check: a swipe on the dice sheet must not scroll the page below; a swipe outside it must.

    uv run -q --no-project --with playwright python archives/agents/TODO-144/verify_todo144.py
Needs the branch server on 8001 and the main server on 8000 (both 127.0.0.1), and tools/live_view.py's
Chromium on 127.0.0.1:9222. Opens its own context and pages; leaves the live_view tabs alone.
"""
import json, sys, time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path("/home/ytani/work/bganalyzer")
sys.path.insert(0, str(ROOT / "tools"))
import pi_ui_check as P   # INIT, read_photo (the same helpers the other checks use)

CDP = "http://127.0.0.1:9222"
SERVERS = {"8001": "http://127.0.0.1:8001/", "8000": "http://127.0.0.1:8000/"}
Y_DISTANCE = -300   # finger moves up 300 px: the page would scroll down


def scroll_y(page):
    return page.evaluate("Math.round(window.scrollY)")


def swipe(session, x, y, steps=10):
    # Input.synthesizeScrollGesture (touch) did not scroll even the 8000 control, so the finger is
    # sent as raw touch events (Input.dispatchTouchEvent): touch-action applies to them as to a real finger.
    session.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
    for i in range(1, steps + 1):
        session.send("Input.dispatchTouchEvent", {"type": "touchMove",
                     "touchPoints": [{"x": x, "y": y + Y_DISTANCE * i / steps}]})
        time.sleep(0.02)
    session.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})


def rect(page, sel):
    return page.evaluate("""s => { const e = document.querySelector(s); if (!e) return null;
        const r = e.getBoundingClientRect(); return {x: r.left, y: r.top, w: r.width, h: r.height, b: r.bottom}; }""", sel)


results = {}
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP)
    ctx = browser.new_context(viewport={"width": 412, "height": 848}, has_touch=True, is_mobile=True)
    for port, url in SERVERS.items():
        page = ctx.new_page()
        for script in (P.INIT,):
            page.add_init_script(script)
        page.alerts = []
        page.on("dialog", lambda d: (page.alerts.append(d.message), d.dismiss()))
        page.goto(url)
        page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
        version = page.evaluate("document.querySelector('#hdr-version').textContent.trim()")
        P.read_photo(page)
        page.evaluate("window.scrollTo(0, 400)")   # below the board, so a free band lies between it and the sheet
        page.wait_for_timeout(300)
        page.locator("#board-svg g.die").first.click()
        page.wait_for_function("BgApp.state.sheet === 'roll'", timeout=10000)
        page.wait_for_timeout(300)
        sheet = rect(page, "#sheet-roll")
        svg = rect(page, "#board-svg")
        info = {"version_header": version, "sheet_rect": sheet, "svg_rect": svg,
                "scrollHeight": page.evaluate("document.documentElement.scrollHeight"),
                "innerHeight": page.evaluate("innerHeight")}
        session = ctx.new_cdp_session(page)

        # 1: inside the sheet (centre of its rectangle, away from the buttons' edges)
        ix, iy = sheet["x"] + sheet["w"] / 2, sheet["y"] + sheet["h"] / 2
        info["inside_point_hit"] = page.evaluate(
            "([x,y]) => { const e = document.elementFromPoint(x,y); return e && e.closest('#sheet-roll') ? 'sheet-roll' : (e && e.tagName) }", [ix, iy])
        page.evaluate("window.scrollTo(0, 400)"); page.wait_for_timeout(200)
        before = scroll_y(page)
        swipe(session, ix, iy)
        page.wait_for_timeout(700)
        after = scroll_y(page)
        info["inside"] = {"point": [round(ix), round(iy)], "before": before, "after": after}

        # 2: outside the sheet: above the sheet top, in the page content (not the sheet)
        ox = 206
        oy = 440   # between the board's bottom (about 398 at scrollY 400) and the sheet's top (480)
        info["outside_point_hit"] = page.evaluate(
            "([x,y]) => { const e = document.elementFromPoint(x,y); return e ? (e.closest('#sheet-roll') ? 'sheet-roll' : e.tagName + (e.id ? '#' + e.id : '')) : null }", [ox, oy])
        page.evaluate("window.scrollTo(0, 400)"); page.wait_for_timeout(200)
        before = scroll_y(page)
        swipe(session, ox, oy)
        page.wait_for_timeout(700)
        after = scroll_y(page)
        info["outside"] = {"point": [ox, round(oy)], "before": before, "after": after}

        # 4: a tap on a die button sets dice[0] (only on the branch server, as asked)
        if port == "8001":
            btns = page.evaluate("[...document.querySelectorAll('#die1 button')].map(b => Number(b.dataset.n))")
            current = page.evaluate("BgApp.state.dice[0]")
            target = next(n for n in btns if n != current)
            page.locator(f"#die1 button[data-n='{target}']").tap()
            page.wait_for_timeout(300)
            info["tap"] = {"buttons": btns, "before": current, "tapped": target,
                           "after": page.evaluate("BgApp.state.dice[0]")}
        results[port] = info
        page.close()
    browser.close()

print(json.dumps(results, ensure_ascii=False, indent=2))
