"""TODO-126 check: drive the PWA at BG_URL via the CDP browser. Run: uv run -q --no-project --with playwright python archives/agents/TODO-126/verify.py"""
import json, os, re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
URL = os.environ.get("BG_URL", "http://127.0.0.1:8126/")
CDP = os.environ.get("BG_CDP", "http://127.0.0.1:9222")
truth = json.loads((ROOT / "samples/screen1.truth.json").read_text())
res = []
def rec(name, ok, detail): res.append(ok); print(("OK   " if ok else "FAIL ") + name + ": " + str(detail))
S = "(k => BgApp.state[k])"

def arrow(page, sel):
    """U path end point (x,y) from d, tip polygon first point, and number of circles/faint ones."""
    return page.evaluate("""sel => { const s = document.querySelector(sel);
      const paths = [...s.querySelectorAll('path')].map(p => p.getAttribute('d'));
      const poly = s.querySelector('polygon');
      const circ = [...s.querySelectorAll('circle')].map(c => [c.getAttribute('cx'), c.getAttribute('cy'), c.getAttribute('fill-opacity'), c.getAttribute('r')]);
      return {paths, tip: poly && poly.getAttribute('points'), circ}; }""", sel)

def end_corner(a):
    """which corner the arrow head is at, from path d's last point"""
    if not a["paths"]: return None
    m = re.search(r"H(-?[\d.]+)$", a["paths"][0]); x = float(m.group(1))
    y = float(re.search(r"A\S+ \S+ \S+ \S+ [\d.]+,([\d.]+)", a["paths"][0]).group(1))
    return ("near" if y > 40 else "far") + "-" + ("left" if x < 60 else "right")

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP)
    page = browser.new_page(viewport={"width": 412, "height": 915})
    errs = []; page.on("pageerror", lambda e: errs.append(str(e))); page.on("dialog", lambda d: (errs.append("dialog:" + d.message), d.dismiss()))
    page.add_init_script("try{localStorage.setItem('collect','off')}catch(_){}")
    page.goto(URL); page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
    page.set_input_files("#file", str(ROOT / "samples" / truth["image"]))
    page.wait_for_function("BgApp.state.cornerGuess !== 'finding'", timeout=60000)
    st = lambda: page.evaluate("({h: BgApp.state.homePick, b: BgApp.state.bottomColour})")
    # 1
    page.click('#home-pick [data-corner="near-right"]'); s = st()
    rec("1a near-right", s == {"h": "right", "b": 1}, s)
    a = arrow(page, "#home-pick"); rec("1a arrow end", end_corner(a) == "near-right", (end_corner(a), a["paths"][0]))
    page.click('#home-pick [data-corner="far-left"]'); s = st()
    rec("1b far-left", s == {"h": "left", "b": 0}, s)
    a = arrow(page, "#home-pick"); rec("1b arrow end", end_corner(a) == "far-left", (end_corner(a), a["paths"][0]))
    page.locator("#home-pick").screenshot(path=str(ROOT / "archives/agents/TODO-126/shot-corners-far-left.png"))
    page.click('#home-pick + .seg [data-value="auto"], [data-name="homePick"] [data-value="auto"]'); s = st()
    a = arrow(page, "#home-pick")
    rec("1c auto", s == {"h": "auto", "b": 0} and not a["paths"] and a["tip"] is None, (s, a["paths"]))
    rec("1c dots", True, a["circ"])
    page.locator("#home-pick").screenshot(path=str(ROOT / "archives/agents/TODO-126/shot-corners-auto.png"))
    # 2
    near = "near" if truth["bottom_colour"] else "far"
    page.click(f'#home-pick [data-corner="{near}-{truth["home"]}"]')
    page.evaluate("c => BgApp.update({ corners: c, cornersMoved: true })", truth["corners_TL_TR_BR_BL"])
    page.click("#recognize")
    page.wait_for_function("!document.querySelector('#board').hidden && document.querySelector('#busy').hidden", timeout=120000)
    bs = lambda: page.evaluate("({h: BgApp.state.home, b: BgApp.state.bottomColour, pts: BgApp.state.board.points, bw: BgApp.state.board.bar_white, bb: BgApp.state.board.bar_black})")
    s0 = bs(); a = arrow(page, "#home-svg")
    rec("2 board corner", end_corner(a) == f"{near}-{truth['home']}" and s0["h"] == truth["home"] and s0["b"] == truth["bottom_colour"], (end_corner(a), s0["h"], s0["b"]))
    print("   points read:", s0["pts"], "bar", s0["bw"], s0["bb"], "truth match:", s0["pts"] == truth["points"])
    page.locator("#home-svg").screenshot(path=str(ROOT / "archives/agents/TODO-126/shot-board-0.png"))
    # 4
    rec("4 no #swap-colours", page.evaluate("document.querySelector('#swap-colours') === null") or not page.is_visible("#swap-colours"),
        page.evaluate("document.querySelector('#swap-colours') === null ? 'absent' : 'hidden'"))
    # 3
    other = "far" if near == "near" else "near"
    page.click(f'#home-svg [data-corner="{other}-{s0["h"]}"]'); s1 = bs(); a = arrow(page, "#home-svg")
    rec("3a far same col", s1["b"] == 1 - s0["b"] and s1["pts"] == [-x for x in s0["pts"]] and s1["h"] == s0["h"]
        and (s1["bw"], s1["bb"]) == (s0["bb"], s0["bw"]), (s1["b"], s1["h"], s1["pts"], s1["bw"], s1["bb"]))
    rec("3a arrow", end_corner(a) == f"{other}-{s0['h']}", end_corner(a))
    page.locator("#home-svg").screenshot(path=str(ROOT / "archives/agents/TODO-126/shot-board-1.png"))
    oc = "right" if s0["h"] == "left" else "left"
    page.click(f'#home-svg [data-corner="{other}-{oc}"]'); s2 = bs(); a = arrow(page, "#home-svg")
    rec("3b other col", s2["h"] == oc and s2["b"] == s1["b"], (s2["h"], s2["b"]))
    print("   after home flip points:", s2["pts"], "bar", s2["bw"], s2["bb"], "| reversed(s1)==s2:", s2["pts"] == s1["pts"][::-1], "| bars same:", (s2["bw"], s2["bb"]) == (s1["bw"], s1["bb"]))
    rec("3b arrow", end_corner(a) == f"{other}-{oc}", end_corner(a))
    page.locator("#home-svg").screenshot(path=str(ROOT / "archives/agents/TODO-126/shot-board-2.png"))
    # 6
    page.click("#analyze"); page.wait_for_function("!document.querySelector('#outcome').hidden", timeout=120000)
    rec("6 analyze", not errs and page.evaluate("!!BgApp.state.result"), errs)
    browser_errs = errs
    page.close()
import sys; sys.exit(0 if all(res) else 1)
