"""TODO-164: キューブの色と、ダブル申し出中の矢印・サイコロを、動かした画面で読み出す。
    BG_URL=http://127.0.0.1:8011/ uv run -q --no-project --with playwright python archives/agents/TODO-164/verify.py
"""
import json, os, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
os.environ.setdefault("BG_URL", "http://127.0.0.1:8011/")
import pi_ui_check as P

OUT = Path.home() / "tmp/playwright-mcp"
OUT.mkdir(parents=True, exist_ok=True)

READ = """() => {
  const svg = document.querySelector('#board-svg');
  const cubes = [...svg.querySelectorAll('g.die')].filter(g => g.querySelector('.cube-num, .cube-crawford'));
  const dice = [...svg.querySelectorAll('g.die')].filter(g => !g.querySelector('.cube-num, .cube-crawford'));
  const cs = (e, p) => getComputedStyle(e)[p];
  const g = cubes[0];
  const rect = g && g.querySelector('rect');
  const texts = g ? [...g.querySelectorAll('.cube-num, .cube-crawford')] : [];
  const box = rect && rect.getBoundingClientRect();
  return { cubes: cubes.length, dice: dice.length, ways: svg.querySelectorAll('g.way').length,
    rectFill: rect && cs(rect, 'fill'), rectStroke: rect && cs(rect, 'stroke'),
    texts: texts.map(t => [t.getAttribute('class'), t.textContent, cs(t, 'fill')]),
    box: box && [box.x, box.y, box.width, box.height].map(Math.round),
    cube: JSON.stringify(BgApp.state.cube), onRoll: BgApp.state.onRoll, match: JSON.stringify(BgApp.state.match) };
}"""

with sync_playwright() as pw:
    cdp = os.environ.get("BG_CDP")
    browser = pw.chromium.connect_over_cdp(cdp) if cdp else pw.chromium.launch(executable_path=P.CHROMIUM)
    page = P.open_app(browser)
    P.read_photo(page)
    states = {
        "1-centre": {"cube": {"at": "centre", "value": 1, "offered": False}},
        "2-held":   {"cube": {"at": "black", "value": 4, "offered": False}},
        "3-offered": {"cube": {"at": "white", "value": 2, "offered": True}},
    }
    res = {}
    for name, patch in states.items():
        page.evaluate("p => BgApp.update(p)", patch)
        page.wait_for_timeout(500)
        res[name] = page.evaluate(READ)
        page.locator("#board-svg").screenshot(path=str(OUT / f"verify-164-{name}.png"))
        print(name, json.dumps(res[name], ensure_ascii=False))
    # おまけ: Crawford
    page.evaluate("p => BgApp.update(p)", {"cube": {"at": "centre", "value": 1, "offered": False},
                                          "match": {"length": 5, "white": 4, "black": 2, "crawford": True}})
    page.wait_for_timeout(500)
    res["4-crawford"] = page.evaluate(READ)
    page.locator("#board-svg").screenshot(path=str(OUT / "verify-164-4-crawford.png"))
    print("4-crawford", json.dumps(res["4-crawford"], ensure_ascii=False))
    browser.close()
