"""TODO-144 control: the same page and swipe, with only the sheet's touch-action set inline to auto.

Port 8000 serves this checkout's static files (already 0.79.1 on disk), so it is no longer the
unmodified main. Setting touch-action: auto on #sheet-roll inline stands in for the old CSS.
    uv run -q --no-project --with playwright python archives/agents/TODO-144/control_touch_action.py
"""
import json, sys, time
sys.path.insert(0, "/home/ytani/work/bganalyzer/tools")
import pi_ui_check as P
from playwright.sync_api import sync_playwright

Y = -300

def swipe(session, x, y, steps=10):
    session.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
    for i in range(1, steps + 1):
        session.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y + Y * i / steps}]})
        time.sleep(0.02)
    session.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})

out = {}
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.new_context(viewport={"width": 412, "height": 848}, has_touch=True, is_mobile=True)
    for port in ("8001", "8000"):
        page = ctx.new_page()
        page.add_init_script(P.INIT)
        page.alerts = []
        page.on("dialog", lambda d: (page.alerts.append(d.message), d.dismiss()))
        page.goto(f"http://127.0.0.1:{port}/")
        page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
        P.read_photo(page)
        page.evaluate("window.scrollTo(0, 400)"); page.wait_for_timeout(300)
        page.locator("#board-svg g.die").first.click()
        page.wait_for_function("BgApp.state.sheet === 'roll'", timeout=10000)
        page.wait_for_timeout(300)
        r = page.evaluate("(() => { const s = document.querySelector('#sheet-roll').getBoundingClientRect(); return [s.left + s.width/2, s.top + s.height/2]; })()")
        s = ctx.new_cdp_session(page)
        res = {"computed_touch_action": page.evaluate("getComputedStyle(document.querySelector('#sheet-roll')).touchAction")}
        for label, style in (("as_served", None), ("inline_auto", "auto")):
            if style:
                page.evaluate("v => document.querySelector('#sheet-roll').style.touchAction = v", style)
            page.evaluate("window.scrollTo(0, 400)"); page.wait_for_timeout(200)
            before = page.evaluate("Math.round(scrollY)")
            swipe(s, r[0], r[1])
            page.wait_for_timeout(700)
            res[label] = {"before": before, "after": page.evaluate("Math.round(scrollY)")}
        out[port] = res
        page.close()
    b.close()
print(json.dumps(out, ensure_ascii=False, indent=2))
