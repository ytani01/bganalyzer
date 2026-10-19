"""TODO-163 verifier: measure the board view at 3 widths, 2 setups. Run:
  uv run -q --no-project --with playwright python archives/agents/TODO-163/verify_163.py
Server: BG_URL (default http://127.0.0.1:8011/)."""
import json, os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "shots"
URL = os.environ.get("BG_URL", "http://127.0.0.1:8011/")
SAMPLE = "screen-app-grey-shot"
SIZES = [tuple(map(int, x.split("x"))) for x in os.environ.get("BG_SIZES", "390x844,1280x800,800x800").split(",")]   # BG_SIZES=1100x800 for one more
ONLY = os.environ.get("BG_SETUP")
pts = [0] * 24; pts[23] = 9; pts[0] = -7          # white 9 on point 24 (216 pips, 6 off), black 7 on point 1 (168 pips, 8 off)
BOARD = {"points": pts, "bar_white": 0, "bar_black": 0}
SETUPS = {
    "A-cubeblack-m25": {"cube": {"at": "black", "value": 4, "offered": False}, "match": {"length": 25, "white": 24, "black": 10, "crawford": False}},
    "B-crawford": {"cube": {"at": "centre", "value": 64, "offered": False}, "match": {"length": 25, "white": 24, "black": 10, "crawford": True}},
}
INIT = "try{localStorage.setItem('collect','off')}catch(_){};"
MEASURE = """() => {
  return [...document.querySelectorAll('#board .board-wrap svg')].filter(s => s.getBoundingClientRect().width > 0).map(svg => {
  const wrap = svg.closest('.board-wrap');
  const r = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal;
  const out = [];
  for (const e of svg.querySelectorAll('text, circle, path, line, polygon')) {   // outside the viewBox = clipped
    let b; try { b = e.getBBox(); } catch (_) { continue; }
    if (!b.width && !b.height) continue;
    if (b.x < vb.x - 0.01 || b.y < vb.y - 0.01 || b.x + b.width > vb.x + vb.width + 0.01 || b.y + b.height > vb.y + vb.height + 0.01)
      out.push(e.tagName + ' ' + (e.textContent || '').slice(0, 12) + ' ' + [b.x, b.y, b.width, b.height].map(v => +v.toFixed(1)).join(','));
  }
  const texts = [...svg.querySelectorAll('text')].map(t => t.textContent.trim()).filter(Boolean);
  return { svgW: r.width, svgLeft: r.left, svgRight: r.right, innerWidth, hscroll: document.documentElement.scrollWidth > innerWidth,
           scrollW: document.documentElement.scrollWidth, radius: getComputedStyle(wrap).borderRadius, wrapRect: [wrap.getBoundingClientRect().left, wrap.getBoundingClientRect().right],
           viewBox: [vb.x, vb.y, vb.width, vb.height].join(' '), clipped: out, texts, inPin: !!svg.closest('#board-pin'), pipTexts: texts.filter(t => /^\\d{3}$/.test(t)) };
  });
}"""

truth = json.loads((ROOT / f"samples/{SAMPLE}.truth.json").read_text())
res = {}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/chromium", headless=True)
    for sname, setup in SETUPS.items():
        if ONLY and not sname.startswith(ONLY): continue
        for w, h in SIZES:
            page = b.new_page(viewport={"width": w, "height": h})
            errs = []
            page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errs.append("pageerror " + str(e)))
            page.add_init_script(INIT)
            page.goto(URL)
            page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
            page.set_input_files("#file", str(ROOT / "samples" / truth["image"]))
            page.wait_for_function("BgApp.state.photo && BgApp.state.cornerGuess !== 'finding'", timeout=60000)
            page.evaluate("t => BgApp.update({ homePick: t.home, bottomColour: t.bottom_colour })", truth)
            page.evaluate("c => BgApp.update({ corners: c, cornersMoved: true })", truth["corners_TL_TR_BR_BL"])
            page.click("#recognize")
            page.wait_for_function("!document.querySelector('#board').hidden && document.querySelector('#busy').hidden", timeout=120000)
            page.evaluate("s => BgApp.update({ board: s.board, dice: [0, 0], cube: s.cube, cubeFromPhoto: false, match: s.match, result: null })", {**setup, "board": BOARD})
            page.wait_for_timeout(500)
            m = page.evaluate(MEASURE)
            key = f"{sname}@{w}"
            res[key] = {"boards": m, "errors": errs}
            page.screenshot(path=str(OUT / f"{sname}-{w}.png"))
            if w == 390 and sname.startswith("A"):   # stuck at the top after scrolling
                page.evaluate("window.scrollTo(0, 700)"); page.wait_for_timeout(300)
                pin = page.evaluate("""() => { const p = document.querySelector('#board-pin'); const r = p.getBoundingClientRect();
                  const s = [...p.querySelectorAll('svg')][0].getBoundingClientRect();
                  return { pinTop: r.top, pinLeft: r.left, pinRight: r.right, svgLeft: s.left, svgRight: s.right, hscroll: document.documentElement.scrollWidth > innerWidth, scrollY } }""")
                res[key]["pinned"] = pin
                page.screenshot(path=str(OUT / f"{sname}-{w}-pinned.png"))
            page.close()
    b.close()
print(json.dumps(res, ensure_ascii=False, indent=1))
