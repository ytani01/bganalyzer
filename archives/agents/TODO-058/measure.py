"""TODO-058 / PI-041: measure the PWA header on the Pi (title, version, steps list).

    uv run -q --no-project --with playwright python archives/agents/TODO-058/measure.py [widths...]

Default widths: 390 1000 (the first check, screenshots todo058-*). The steps check (commit 43e4958)
uses 600 1000 and 390; give the widths and it writes todo058-steps-* screenshots instead.
Reuses tools/pi_ui_check.py (INIT script, URL, SAMPLE, truth file). Prints one JSON line per screen.
Screenshots of the header go to ~/tmp/playwright-mcp/.
"""
import json, sys
from pathlib import Path

sys.path.insert(0, "/home/ytani/work/bganalyzer/tools")
import pi_ui_check as P
from playwright.sync_api import sync_playwright

OUT = Path.home() / "tmp" / "playwright-mcp"
OUT.mkdir(parents=True, exist_ok=True)
TRUTH = json.loads((P.ROOT / f"samples/{P.SAMPLE}.truth.json").read_text())
STEPS = "steps" in sys.argv[1:] or True  # always measure the step list
WIDTHS = [int(a) for a in sys.argv[1:] if a.isdigit()] or [390, 1000]
PREFIX = next((f"todo058-{w}" for w in ("steps", "icon", "merge") if w in sys.argv[1:]), "todo058")

MEASURE_JS = """() => {
  const r = (el) => { const b = el.getBoundingClientRect(); return {top: +b.top.toFixed(1), bottom: +b.bottom.toFixed(1), left: +b.left.toFixed(1), right: +b.right.toFixed(1)}; };
  const t = document.querySelector('#title'), name = document.querySelector('.app-name'),
        ver = document.querySelector('#hdr-version'), bar = document.querySelector('header .bar');
  const shown = [...document.querySelectorAll('header button')].filter(b => b.getClientRects().length > 0);
  const btns = shown.map(b => ({id: b.id || b.textContent.trim().slice(0, 12), ...r(b), beyondRight: b.getBoundingClientRect().right > innerWidth + 0.5}));
  const act = document.querySelector('header .actions');
  const nav = document.querySelector('#steps'), spans = [...nav.querySelectorAll('span')];
  const sr = spans.map(s => s.getBoundingClientRect());
  const ic = document.querySelector('.app-icon'), nm = document.querySelector('.app-name'), nmCs = getComputedStyle(nm);
  const ib = ic.getBoundingClientRect(), nb = nm.getBoundingClientRect(), vb = ver.getBoundingClientRect();
  const icon = {complete: ic.complete, naturalWidth: ic.naturalWidth, w: +ib.width.toFixed(1), h: +ib.height.toFixed(1),
    left: +ib.left.toFixed(1), leftOfName: ib.right <= nb.left + 0.5, centreDiff: +((ib.top + ib.bottom) / 2 - (nb.top + nb.bottom) / 2).toFixed(1),
    nameFontSize: nmCs.fontSize, nameFontWeight: nmCs.fontWeight, nameVsVerCentreDiff: +((nb.top + nb.bottom) / 2 - (vb.top + vb.bottom) / 2).toFixed(1),
    verScrollW: ver.scrollWidth, verClientW: ver.clientWidth, verText: ver.textContent,
    sameLine: Math.abs(ib.top - nb.top) < 3 && Math.abs(nb.top - vb.top) < 3};
  const steps = {
    navDisplay: getComputedStyle(nav).display, navVisible: nav.getClientRects().length > 0,
    texts: spans.map(s => s.textContent),
    on: spans.filter(s => s.classList.contains('on')).map(s => s.textContent),
    tops: sr.map(b => +b.top.toFixed(1)), topSpread: +(Math.max(...sr.map(b => b.top)) - Math.min(...sr.map(b => b.top))).toFixed(1),
    maxRight: +Math.max(...sr.map(b => b.right)).toFixed(1),
    beyondRight: Math.max(...sr.map(b => b.right)) > innerWidth + 0.5,
  };
  return {
    step: BgApp.state.step,
    title: t.textContent, titleScrollW: t.scrollWidth, titleClientW: t.clientWidth,
    titleRect: r(t), actionsRect: act ? r(act) : null,
    appName: r(name), verTop: r(ver).top, verText: ver.textContent, verClass: ver.className,
    sameLine: Math.abs(name.getBoundingClientRect().top - ver.getBoundingClientRect().top) < 2,
    verAboveBar: ver.getBoundingClientRect().bottom <= bar.getBoundingClientRect().top + 0.5,
    docScrollW: document.documentElement.scrollWidth, innerW: innerWidth,
    hdrButtons: btns,
    headerRightOverflow: btns.some(b => b.beyondRight),
    steps, icon,
  };
}"""


def measure(page, width, screen):
    m = page.evaluate(MEASURE_JS)
    if "r0." not in m["verText"]:
        page.wait_for_timeout(2000)
        m["verTextAfter2s"] = page.evaluate("document.querySelector('#hdr-version').textContent")
    m["width"], m["screen"] = width, screen
    if True:
        page.locator("header").screenshot(path=str(OUT / f"{PREFIX}-{width}-{screen}.png"))
    print(json.dumps(m, ensure_ascii=False), flush=True)


def run(browser, width, full):
    page = browser.new_page(viewport={"width": width, "height": 844})
    page.add_init_script(P.INIT)
    page.on("dialog", lambda d: d.dismiss())
    page.goto(P.URL)
    page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
    measure(page, width, "photo")
    if full:
        page.set_input_files("#file", str(P.ROOT / "samples" / TRUTH["image"]))
        page.wait_for_function("BgApp.state.step === 'corners'", timeout=60000)
        page.wait_for_function("BgApp.state.cornerGuess !== 'finding'", timeout=60000)
        measure(page, width, "corners")
        page.click(f'.seg[data-name="homePick"] [data-value="{TRUTH["home"]}"]')
        page.click(f'.seg[data-name="bottomColour"] [data-value="{TRUTH["bottom_colour"]}"]')
        page.evaluate("c => BgApp.update({ corners: c, cornersMoved: true })", TRUTH["corners_TL_TR_BR_BL"])
        page.click("#recognize")
        page.wait_for_function("!document.querySelector('#board').hidden && document.querySelector('#busy').hidden",
                               timeout=120000)
        measure(page, width, "board")
        page.click("#analyze")
        page.wait_for_function("!document.querySelector('#outcome').hidden", timeout=120000)
        measure(page, width, "outcome")
    page.close()


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=P.CHROMIUM, args=["--no-sandbox"])
    for w in WIDTHS:
        run(browser, w, PREFIX != "todo058-steps" or w != 390)
    browser.close()
