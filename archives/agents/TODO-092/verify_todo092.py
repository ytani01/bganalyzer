"""TODO-092 check: arrows only on the result board, and the way (U-shape) for the side on roll.

    uv run -q --no-project --with playwright python archives/agents/TODO-092/verify_todo092.py
"""
import json, urllib.request
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8000/"
CHROMIUM = "/usr/bin/chromium"
SHOT = "/home/ytani/tmp/playwright-mcp/todo092-result.png"

out = {}
out["version"] = json.loads(urllib.request.urlopen("http://127.0.0.1:8000/version", timeout=10).read())

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROMIUM)
    page = browser.new_page(viewport={"width": 412, "height": 915})
    page.on("dialog", lambda d: (out.setdefault("dialogs", []).append(d.message), d.accept()))
    page.goto(URL)
    page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")

    # initial placement: 「手で入力」 starts from the start position (as a person would)
    page.click("#manual")
    page.wait_for_function("!document.querySelector('#board').hidden")
    out["start_points_first4"] = page.evaluate("BgApp.state.board.points.slice(0, 4)")

    # step 3 (before analysis): way for white and for black
    page.click('.seg[data-name="onRoll"] [data-value="white"]')
    page.wait_for_timeout(300)
    out["way_count_white"] = page.evaluate("document.querySelectorAll('#board-svg g.way').length")
    out["way_path_d_white"] = page.evaluate("[...document.querySelectorAll('#board-svg g.way path')].map(e => e.getAttribute('d'))")
    page.click('.seg[data-name="onRoll"] [data-value="black"]')
    page.wait_for_timeout(300)
    out["way_path_d_black"] = page.evaluate("[...document.querySelectorAll('#board-svg g.way path')].map(e => e.getAttribute('d'))")
    out["onRoll_after_black"] = page.evaluate("BgApp.state.onRoll")
    out["board_arrows_before_analyze"] = page.evaluate("document.querySelectorAll('#board-svg g.arrows').length")

    # step 2: white on roll, dice 3-1, analyze
    page.click('.seg[data-name="onRoll"] [data-value="white"]')
    page.select_option("#die1", "3")
    page.select_option("#die2", "1")
    page.wait_for_timeout(300)
    out["state_onRoll"] = page.evaluate("BgApp.state.onRoll")
    out["state_rolled"] = page.evaluate("BgApp.rolled()")
    page.click("#analyze")
    page.wait_for_function("!document.querySelector('#outcome').hidden", timeout=120000)
    page.wait_for_timeout(500)
    out["result_arrows"] = page.evaluate("document.querySelectorAll('#result-svg g.arrows').length")
    out["board_arrows"] = page.evaluate("document.querySelectorAll('#board-svg g.arrows').length")
    out["board_way"] = page.evaluate("document.querySelectorAll('#board-svg g.way').length")
    out["result_way"] = page.evaluate("document.querySelectorAll('#result-svg g.way').length")
    out["best_move"] = page.evaluate("(r => r && r.moves && r.moves[0] && r.moves[0].move)(BgApp.state.result)")

    # step 4: screenshot of the result screen
    page.locator("#outcome").screenshot(path=SHOT)
    out["screenshot"] = SHOT
    browser.close()

print(json.dumps(out, ensure_ascii=False, indent=2))
