"""TODO-145 の実測（検証の担当が書いた）。BG_URL のサーバーに、live_view の Chromium から新しいページでつなぐ。

uv run -q --no-project --with playwright python archives/agents/TODO-145/verify_145.py
"""
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = os.environ.get("BG_URL", "http://127.0.0.1:8002/")
HERE = Path(__file__).resolve().parent


def log(name, ok, detail):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}", flush=True)


def points(page):
    return page.evaluate("() => BgApp.state.board.points.slice()")


with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = browser.new_context(viewport={"width": 412, "height": 848}, reduced_motion="reduce",
                              service_workers="block")
    page = ctx.new_page()
    page.goto(URL)
    page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
    print("version text:", page.text_content("#hdr-version").strip(), flush=True)
    page.click("#manual")
    page.wait_for_function("document.getElementById('busy').hidden")
    page.wait_for_selector("#board-svg .hit")

    # 1. #paint-side が DOM に無い
    n = page.locator("#paint-side").count()
    log("1 #paint-side count", n == 0, f"count={n}")

    # 2. 位置・折り返し
    geo = page.evaluate("""() => {
      const box = (id) => document.getElementById(id).getBoundingClientRect();
      const t = box('editor-title'), u = box('undo'), e = box('editor');
      const cs = getComputedStyle(document.getElementById('undo'));
      const ecs = getComputedStyle(document.getElementById('editor'));
      const r = document.createRange();
      r.selectNodeContents(document.getElementById('undo'));
      const tops = new Set([...r.getClientRects()].map((x) => Math.round(x.top)));
      const rowCs = getComputedStyle(document.querySelector('#editor .editor-row'));
      return {
        titleTop: t.top, titleBottom: t.bottom, undoTop: u.top, undoBottom: u.bottom,
        undoLeft: u.left, undoRight: u.right, undoH: u.height, editorRight: e.right, editorLeft: e.left,
        padR: ecs.paddingRight, borderR: ecs.borderRightWidth,
        whiteSpace: cs.whiteSpace, lineHeight: cs.lineHeight, fontSize: cs.fontSize, lineCount: tops.size,
        rowFlexWrap: rowCs.flexWrap, titleDisplay: getComputedStyle(document.getElementById('editor-title')).display,
        titleText: document.getElementById('editor-title').textContent.trim(),
        undoText: document.getElementById('undo').textContent.trim(),
        undoDisabled: document.getElementById('undo').disabled,
      };
    }""")
    overlap = min(geo["titleBottom"], geo["undoBottom"]) - max(geo["titleTop"], geo["undoTop"])
    log("2a same row (vertical overlap px)", overlap > 0, f"overlap={overlap:.1f} titleTop={geo['titleTop']:.1f} titleBottom={geo['titleBottom']:.1f} undoTop={geo['undoTop']:.1f} undoBottom={geo['undoBottom']:.1f}")
    gap = geo["editorRight"] - geo["undoRight"]
    log("2b undo at right end (editor.right - undo.right px)", 0 < gap <= 14,
        f"gap={gap:.2f} padR={geo['padR']} borderR={geo['borderR']} undoRight={geo['undoRight']:.2f} editorRight={geo['editorRight']:.2f}")
    log("2c undo single line", geo["lineCount"] == 1 and geo["whiteSpace"] == "nowrap",
        f"lines={geo['lineCount']} white-space={geo['whiteSpace']} height={geo['undoH']:.2f} line-height={geo['lineHeight']} font-size={geo['fontSize']}")
    print("2 detail:", {k: geo[k] for k in ("rowFlexWrap", "titleDisplay", "titleText", "undoText", "undoDisabled")}, flush=True)

    ed = page.locator("#editor")
    ed.scroll_into_view_if_needed()
    shot = HERE / "editor-412x848.png"
    ed.screenshot(path=str(shot))
    print("screenshot:", shot, flush=True)

    # 3. 右クリックでパレット → 黒・数 0 → 別の空のポイントをタップ
    info = page.evaluate("""() => {
      const home = BgApp.state.home;
      const pts = BgApp.state.board.points;
      const hits = [...document.querySelectorAll('#board-svg .hit')];
      const idx = hits.map((_, k) => (k < 12 ? BgBoard.pointAt(home, true, k) : BgBoard.pointAt(home, false, k - 12)));
      return { home, n: hits.length, idx, empties: idx.filter((i) => i >= 0 && pts[i] === 0), points: pts };
    }""")
    print("home:", info["home"], "hits:", info["n"], "empty points (index):", info["empties"], flush=True)
    empties = info["empties"]
    if len(empties) < 2:
        log("3 precondition", False, f"need 2 empty points, got {empties}")
    else:
        a, b_ = empties[0], empties[1]
        ka = info["idx"].index(a)
        kb = info["idx"].index(b_)
        page.locator("#board-svg .hit").nth(ka).click(button="right")
        page.wait_for_function("!document.getElementById('palette').hidden", timeout=5000)
        page.click('#palette-side [data-value="black"]')
        page.click('#palette-counts [data-n="0"]')
        pts_before_tap = points(page)
        page.locator("#board-svg .hit").nth(kb).click()
        page.wait_for_timeout(300)
        pts_after = points(page)
        changed = [i for i in range(24) if pts_before_tap[i] != pts_after[i]]
        ok3 = pts_after[b_] < 0 and changed == [b_]
        palette_hidden = page.evaluate("() => document.getElementById('palette').hidden")
        log("3 black placed on empty point", ok3,
            f"pointIndex={b_} before={pts_before_tap[b_]} after={pts_after[b_]} changedIndices={changed} palette_hidden_after={palette_hidden}")

        # 4. #undo で直前の盤面に戻る
        page.click("#undo")
        page.wait_for_timeout(300)
        pts_undo = points(page)
        log("4 undo restores points", pts_undo == pts_before_tap,
            f"equal={pts_undo == pts_before_tap} diffIndices={[i for i in range(24) if pts_undo[i] != pts_before_tap[i]]}")
    browser.close()
