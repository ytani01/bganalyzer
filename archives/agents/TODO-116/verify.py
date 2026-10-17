"""TODO-116 確認: 「解析する」のグレーアウトと理由を、PWA の盤面の画面で操作して読む。読むだけ（コードは変えない）。"""
import json, sys, time, urllib.request, os
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8017/"

def wait_server():
    for _ in range(120):
        try:
            urllib.request.urlopen(URL + "version", timeout=2).read()
            return
        except Exception:
            time.sleep(0.5)
    raise SystemExit("server did not start")

SNAP_JS = """() => {
  const a = document.getElementById('analyze'), w = document.getElementById('analyze-why');
  const s = BgApp.state, b = s.board;
  return { step: s.step, disabled: a.disabled, analyzeHidden: a.hidden, whyHidden: w.hidden, why: w.textContent,
           points: b ? b.points : null, bar: b ? [b.bar_white, b.bar_black] : null,
           match: s.match, cubeAt: s.cube.at, bottomColour: s.bottomColour };
}"""

def snap(page, label):
    r = page.evaluate(SNAP_JS)
    print(label, json.dumps(r, ensure_ascii=False), flush=True)
    return r

def click_point_at(page, selector_fn):
    """Click the hit rect chosen by selector_fn (JS returning the element); click at its centre."""
    coords = page.evaluate("""(fn) => {
      const el = eval(fn)(); if (!el) return null;
      el.scrollIntoView({block: 'center'});
      const svg = document.getElementById('board-svg');
      const bb = el.getBoundingClientRect();
      return {x: bb.x + bb.width / 2, y: bb.y + bb.height / 2, hit: document.elementFromPoint(bb.x + bb.width / 2, bb.y + bb.height / 2) === el};
    }""", selector_fn)
    return coords

ADD_PT_FN = """() => () => {
  const svg = document.getElementById('board-svg');
  const rs = [...svg.querySelectorAll('rect.hit')].filter(r => +r.getAttribute('y') === 24 && +r.getAttribute('width') === 48);
  rs.sort((a, b) => +a.getAttribute('x') - +b.getAttribute('x'));
  return rs[0];
}"""

def add_checker(page):
    # 2 checkers on the first top point; tapping the third level puts one more of the same colour on it
    r = page.evaluate("""() => {
      const svg = document.getElementById('board-svg');
      const rs = [...svg.querySelectorAll('rect.hit')].filter(r => +r.getAttribute('y') === 24 && +r.getAttribute('width') === 48);
      rs.sort((a, b) => +b.getAttribute('x') - +a.getAttribute('x'));   // rightmost top point: the 24-point with home left (2 checkers)
      const x = +rs[0].getAttribute('x') + 24, y = 119;   // SVG coords: level 3 (24 + 2.5 * 38)
      const pt = new DOMPoint(x, y).matrixTransform(svg.getScreenCTM());
      return {x: pt.x, y: pt.y};
    }""")
    page.mouse.click(r["x"], r["y"])
    page.wait_for_timeout(300)

def clear_board(page):
    n = page.evaluate("() => document.querySelectorAll('#board-svg rect.hit-num').length")
    for i in range(n):
        p = page.evaluate("""(i) => {
          const svg = document.getElementById('board-svg');
          const r = svg.querySelectorAll('rect.hit-num')[i];
          r.scrollIntoView({block: 'center'});
          const bb = r.getBoundingClientRect();
          return {x: bb.x + bb.width / 2, y: bb.y + bb.height / 2};
        }""", i)
        page.mouse.click(p["x"], p["y"])
        page.wait_for_timeout(120)
    return n

def main():
    wait_server()
    out = {}
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.on("dialog", lambda d: (print("dialog:", d.message, flush=True), d.accept()))
        page.goto(URL)
        page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
        print("version:", page.inner_text("#hdr-version"), flush=True)

        # 6a: the photo screen (no board yet)
        out["6a photo"] = snap(page, "6a photo screen")

        # 1: by hand -> initial 15/15 board
        page.click("#manual")
        page.wait_for_function("!document.querySelector('#board').hidden")
        page.select_option("#match-length", "0")   # 前の実行で残った設定（クロフォード）を外す
        page.wait_for_timeout(200)
        out["1 initial"] = snap(page, "1 initial")

        # 2: add a checker -> 16, then undo
        add_checker(page)
        out["2 added"] = snap(page, "2 added 16")
        page.click("#undo")
        page.wait_for_timeout(200)
        out["2 undone"] = snap(page, "2 undone")

        # 3: clear all points (tap each point's number)
        n = clear_board(page)
        print("cleared with taps:", n, flush=True)
        out["3 cleared"] = snap(page, "3 cleared")
        page.click("#reset-start")   # 初期配置へ戻す（confirm は accept）
        page.wait_for_timeout(300)
        out["3 restored"] = snap(page, "3 restored start")

        # 4: match, crawford on, cube off centre
        opts = page.evaluate("() => [...document.getElementById('match-length').options].map(o => o.value)")
        print("match-length options:", opts, flush=True)
        page.select_option("#match-length", "5")
        page.wait_for_timeout(200)
        page.select_option("#score-white", "4")
        page.wait_for_timeout(200)
        page.check("#crawford")
        page.wait_for_timeout(200)
        page.click('.seg[data-name="cubeAt"] [data-value="white"]')
        page.wait_for_timeout(200)
        out["4 crawford cube white"] = snap(page, "4 crawford cube white")
        page.click('.seg[data-name="cubeAt"] [data-value="centre"]')
        page.wait_for_timeout(200)
        out["4 crawford cube centre"] = snap(page, "4 crawford cube centre")

        # 5: 16 checkers, then switch the near side colour
        add_checker(page)
        out["5 16 before switch"] = snap(page, "5 16 before switch")
        # 手前の駒の色の .seg は写真の画面にしか無い。盤面の画面では「色を入れ替え」が bottomColour を反転させる
        page.click("#swap-colours")
        page.wait_for_timeout(200)
        out["5 swap 1"] = snap(page, "5 after swap (bottomColour flipped)")
        page.click("#swap-colours")
        page.wait_for_timeout(200)
        out["5 swap 2"] = snap(page, "5 after second swap (back)")
        page.click("#reset-start")   # 15/15 に戻す（swap で undo は空になるため）
        page.wait_for_timeout(300)
        out["5 reset"] = snap(page, "5 reset to start")

        # 6b: the result screen (only when reachable): money game, cube centre, valid board
        page.select_option("#match-length", "0")
        page.wait_for_timeout(200)
        out["6b before analyze"] = snap(page, "6b before analyze")
        page.click("#analyze")
        try:
            page.wait_for_function("!document.querySelector('#outcome').hidden", timeout=120000)
            out["6b outcome"] = snap(page, "6b outcome screen")
        except Exception as e:
            print("6b did not reach outcome:", type(e).__name__, str(e)[:200], flush=True)
            out["6b outcome"] = "not reached"
        page.close()
    print("RESULT " + json.dumps(out, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()
