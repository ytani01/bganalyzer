"""TODO-090 check: PIP plates on both boards, result-screen order, cube-decision order, screenshot.

    uv run -q --no-project --with playwright python archives/agents/TODO-090/verify_todo090.py
"""
import json
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8090/"
CHROMIUM = "/usr/bin/chromium"
SHOT = "/home/ytani/tmp/playwright-mcp/todo090-result.png"

PIP_TEXTS = "[...document.querySelectorAll('#board-svg text.pip-n')].map(e => e.textContent)"
RESULT_PIP_TEXTS = "[...document.querySelectorAll('#result-svg text.pip-n')].map(e => e.textContent)"
BAR_TEXTS = "[...document.querySelectorAll('#board-svg text')].map(e => e.textContent).filter(t => t.includes('バー'))"
RESULT_TOP = """[...document.querySelectorAll('#result > *')].map(e => ({
    tag: e.tagName, cls: e.className, text: e.textContent.slice(0, 24),
    top: Math.round(e.getBoundingClientRect().top)}))"""

out = {}
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROMIUM)
    page = browser.new_page(viewport={"width": 412, "height": 915})
    page.on("dialog", lambda d: (out.setdefault("dialogs", []).append(d.message), d.accept()))
    page.goto(URL)
    page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
    out["header_version"] = page.evaluate("document.querySelector('#hdr-version').textContent.trim()")

    page.wait_for_selector("#manual", state="visible", timeout=30000)
    # ---- 1. initial placement, PIP plates, tap changes them
    page.click("#manual")
    page.wait_for_function("!document.querySelector('#board').hidden")
    out["s1_start_points"] = page.evaluate("BgApp.state.board.points")
    out["s1_pip_before"] = page.evaluate(PIP_TEXTS)
    out["s1_bar_texts"] = page.evaluate(BAR_TEXTS)
    out["s1_pips_js_before"] = page.evaluate("BgBoard.pips(BgApp.state.board)")
    page.locator("#board-svg rect.hit").first.click()
    page.wait_for_timeout(400)
    out["s1_points_after_tap"] = page.evaluate("BgApp.state.board.points")
    out["s1_pip_after"] = page.evaluate(PIP_TEXTS)
    out["s1_pips_js_after"] = page.evaluate("BgBoard.pips(BgApp.state.board)")

    # ---- 2. a fresh page (the manual button is hidden once the board shows), start position, white, dice 3-1
    page.close()
    page = browser.new_page(viewport={"width": 412, "height": 915})
    page.on("dialog", lambda d: (out.setdefault("dialogs", []).append(d.message), d.accept()))
    page.goto(URL)
    page.wait_for_selector("#manual", state="visible", timeout=30000)
    page.click("#manual")
    page.wait_for_function("!document.querySelector('#board').hidden")
    page.wait_for_timeout(400)
    out["s2_start_points_restored"] = page.evaluate("BgApp.state.board.points")
    # the seg buttons and dice selects are not visible to Playwright here, so they are set by a DOM click/change
    page.evaluate("""document.querySelector('.seg[data-name="onRoll"] [data-value="white"]').click()""")
    page.evaluate("""(() => { for (const [id, v] of [["die1", "3"], ["die2", "1"]]) { const s = document.getElementById(id); s.value = v; s.dispatchEvent(new Event("change", {bubbles: true})); } })()""")
    page.wait_for_timeout(300)
    with page.expect_response(lambda r: r.url.endswith("/analyze"), timeout=180000) as info:
        page.click("#analyze")
    resp = info.value
    body = resp.json()
    out["s2_analyze_status"] = resp.status
    out["s2_server_pips"] = body.get("pips")
    page.wait_for_function("!document.querySelector('#outcome').hidden", timeout=120000)
    page.wait_for_timeout(500)
    out["s2_result_top"] = page.evaluate(RESULT_TOP)
    out["s2_result_pip_texts"] = page.evaluate(RESULT_PIP_TEXTS)
    out["s2_board_pip_texts"] = page.evaluate(PIP_TEXTS)
    out["s2_result_arrows"] = page.evaluate("document.querySelectorAll('#result-svg g.arrows').length")
    out["s2_result_way"] = page.evaluate("document.querySelectorAll('#result-svg g.way').length")
    out["s2_board_bar_texts"] = page.evaluate(BAR_TEXTS)
    page.locator("#result-svg").screenshot(path=SHOT)
    out["screenshot"] = SHOT

    # ---- 3. back to the board step (the analyze button is hidden on the result step), dice empty
    def run_analyze(tag):
        res = {}
        page.evaluate("document.getElementById('to-board').click()")
        page.wait_for_selector("#analyze", state="visible", timeout=30000)
        res[tag + "_cube_at"] = page.evaluate("BgApp.state.cube")
        res[tag + "_onRoll"] = page.evaluate("BgApp.state.onRoll")
        res[tag + "_rolled"] = page.evaluate("BgApp.rolled()")
        with page.expect_response(lambda r: r.url.endswith("/analyze"), timeout=180000) as inf:
            page.click("#analyze", timeout=10000)
        b = inf.value.json()
        res[tag + "_status"] = inf.value.status
        res[tag + "_has_cube"] = b.get("cube") is not None
        res[tag + "_has_moves"] = bool(b.get("moves"))
        res[tag + "_server_pips"] = b.get("pips")
        page.wait_for_function("!document.querySelector('#outcome').hidden", timeout=120000)
        page.wait_for_timeout(800)
        res[tag + "_result_top"] = page.evaluate(RESULT_TOP)
        res[tag + "_result_pip_texts"] = page.evaluate(RESULT_PIP_TEXTS)
        return res

    # 3a. the literal instruction: cube centred, white on roll, no dice
    page.evaluate("document.querySelector('.seg[data-name=\"onRoll\"] [data-value=\"white\"]').click()")
    page.evaluate("(() => { for (const id of ['die1', 'die2']) { const s = document.getElementById(id); s.value = ''; s.dispatchEvent(new Event('change', {bubbles: true})); } })()")
    out.update(run_analyze("s3a"))

    # 3b. a cube really offered (cube lies on white, black on roll, dice empty), to see the cube decision
    page.evaluate("document.querySelector('.seg[data-name=\"cubeAt\"] [data-value=\"white\"]').click()")
    page.evaluate("(() => { const c = document.getElementById('cube-offered'); c.checked = true; c.dispatchEvent(new Event('change', {bubbles: true})); })()")
    page.wait_for_timeout(300)
    out.update(run_analyze("s3b"))
    browser.close()

print(json.dumps(out, ensure_ascii=False, indent=2))
