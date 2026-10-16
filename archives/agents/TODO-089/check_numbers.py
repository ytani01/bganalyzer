"""TODO-089 の確認: 盤の番号（text.num）と長押しのパレットの見出し、black の番で解析した結果の番号。

実行: uv run -q --no-project --with playwright python archives/agents/TODO-089/check_numbers.py
URL は BG_URL（既定 http://localhost:8011/）。コードは変えない。
"""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path("/home/ytani/work/bganalyzer")
URL = os.environ.get("BG_URL", "http://localhost:8011/")
CHROMIUM = os.environ.get("BG_CHROMIUM", "/usr/bin/chromium")
SAMPLE = "screen1"   # dice 4-2 (see tools/pi_ui_check.py)

NUM_JS = "sel => [...document.querySelectorAll(sel)].map(t => ({x: +t.getAttribute('x'), y: +t.getAttribute('y'), t: t.textContent}))"


def clockwise(nums):
    """Top row left to right, then the bottom row right to left (from the top-left, clockwise)."""
    top = sorted([n for n in nums if n["y"] < 200], key=lambda n: n["x"])
    bot = sorted([n for n in nums if n["y"] >= 200], key=lambda n: -n["x"])
    return top + bot


def main():
    truth = json.loads((ROOT / f"samples/{SAMPLE}.truth.json").read_text())
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROMIUM if Path(CHROMIUM).exists() else None)
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.alerts = []
        page.on("dialog", lambda d: (page.alerts.append(d.message), d.dismiss()))
        page.goto(URL)
        page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
        page.set_input_files("#file", str(ROOT / "samples" / truth["image"]))
        page.wait_for_function("BgApp.state.cornerGuess !== 'finding'", timeout=60000)
        page.click(f'.seg[data-name="homePick"] [data-value="{truth["home"]}"]')
        page.click(f'.seg[data-name="bottomColour"] [data-value="{truth["bottom_colour"]}"]')
        page.evaluate("c => BgApp.update({ corners: c, cornersMoved: true })", truth["corners_TL_TR_BR_BL"])
        page.click("#recognize")
        page.wait_for_function("!document.querySelector('#board').hidden && document.querySelector('#busy').hidden",
                               timeout=120000)

        # 1. numbers on the board, for each side on roll
        ordered = {}
        for side in ["white", "black"]:
            page.click(f'.seg[data-name="onRoll"] [data-value="{side}"]')
            ordered[side] = clockwise(page.evaluate(NUM_JS, "#board-svg text.num"))
            print(f"[{side}] onRoll={page.evaluate('BgApp.state.onRoll')} "
                  f"nums={[n['t'] for n in ordered[side]]} count={len(ordered[side])}")
        w = [int(n["t"]) for n in ordered["white"]]
        b = [int(n["t"]) for n in ordered["black"]]
        sums = [a + c for a, c in zip(w, b)]
        print(f"sums(white+black at same position)={sums} all25={all(s == 25 for s in sums) and len(w) == 24}")

        # 2. long press (right click) on the top-left point -> palette title
        rects = page.evaluate("() => [...document.querySelectorAll('#board-svg rect.hit')]"
                              ".map((r, idx) => ({idx, cx: +r.getAttribute('x') + +r.getAttribute('width') / 2, "
                              "y: +r.getAttribute('y')}))")
        for side in ["white", "black"]:
            page.click(f'.seg[data-name="onRoll"] [data-value="{side}"]')
            first = clockwise(page.evaluate(NUM_JS, "#board-svg text.num"))[0]
            cands = [r for r in rects if abs(r["cx"] - first["x"]) < 0.01 and r["y"] < 200]
            page.locator("#board-svg rect.hit").nth(cands[0]["idx"]).click(button="right")
            title = page.text_content("#palette-title")
            print(f"[palette {side}] title={title!r} expected_num={first['t']!r} "
                  f"match={title == 'ポイント ' + first['t']}")
            page.evaluate("() => { document.body.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true})); }")
            page.wait_for_timeout(300)

        # 3. analyze with black on roll
        page.click(f'.seg[data-name="onRoll"] [data-value="black"]')
        dice = page.evaluate("BgApp.rolled()")
        print(f"[analyze] dice={dice}")
        page.click("#analyze")
        page.wait_for_function("!document.querySelector('#outcome').hidden", timeout=120000)
        best = page.evaluate("() => { const li = document.querySelector('#result ol.moves li'); "
                             "return li ? li.childNodes[0].textContent : null; }")
        rnums = clockwise(page.evaluate(NUM_JS, "#result-svg text.num"))
        print(f"[result] best_line={best!r}")
        print(f"[result] result-svg nums={[n['t'] for n in rnums]}")
        print(f"[result] board black nums={b}")
        print(f"[result] same as board black numbers={[int(n['t']) for n in rnums] == b}")
        from_tok = best.split(" ")[0].split("/")[0] if best else None
        print(f"[result] first from-point token={from_tok!r}")
        if from_tok and from_tok.isdigit():
            n = int(from_tok)
            i = 24 - n   # index of the point with black's number n
            pos = w.index(25 - n)   # the same position on the board, by white's number
            state_points = page.evaluate("BgApp.state.board.points")
            print(f"[result] points[{i}]={state_points[i]} (negative = black) "
                  f"black_at_from={state_points[i] < 0} result-svg num at that position={rnums[pos]['t']!r} "
                  f"expected={str(n)!r}")
        else:
            print("[result] no numeric from-point (bar or none); not checked")
        print(f"alerts={page.alerts}")
        browser.close()


if __name__ == "__main__":
    main()
