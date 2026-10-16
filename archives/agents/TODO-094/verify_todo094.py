"""TODO-094 check: board screen's photo toggle is a single checkbox #photo-side.

    uv run -q --no-project --with playwright python archives/agents/TODO-094/verify_todo094.py
"""
import json, os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path("/home/ytani/work/bganalyzer-094")
URL = "http://127.0.0.1:8094/"
CHROMIUM = "/usr/bin/chromium"
SHOT = Path(os.path.expanduser("~/tmp/playwright-mcp/todo094-photo-tools.png"))
SAMPLE = "screen1"

INIT = """
window.__spoken = [];
if (window.speechSynthesis) speechSynthesis.speak = (u) => { window.__spoken.push(u.text); };
delete Navigator.prototype.canShare; delete Navigator.prototype.share;
"""

R = {}
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROMIUM)
    page = browser.new_page(viewport={"width": 412, "height": 915})
    page.add_init_script(INIT)
    page.alerts = []
    page.on("dialog", lambda d: (page.alerts.append(d.message), d.dismiss()))
    page.goto(URL)
    page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
    R["hdr_version"] = page.text_content("#hdr-version")

    truth = json.loads((ROOT / f"samples/{SAMPLE}.truth.json").read_text())
    page.set_input_files("#file", str(ROOT / "samples" / truth["image"]))
    page.wait_for_function("BgApp.state.cornerGuess !== 'finding'", timeout=60000)
    page.wait_for_timeout(500)
    page.click(f'.seg[data-name="homePick"] [data-value="{truth["home"]}"]')
    page.click(f'.seg[data-name="bottomColour"] [data-value="{truth["bottom_colour"]}"]')
    page.evaluate("c => BgApp.update({ corners: c, cornersMoved: true })", truth["corners_TL_TR_BR_BL"])
    page.click("#recognize")
    page.wait_for_function("!document.querySelector('#board').hidden && document.querySelector('#busy').hidden",
                           timeout=120000)
    page.wait_for_timeout(800)

    def state():
        return page.evaluate("""() => ({
            tools_hidden: document.querySelector('#photo-tools').hidden,
            tools_visible: (() => { const e = document.querySelector('#photo-tools'); return !!(e.offsetWidth || e.offsetHeight); })(),
            side_exists: !!document.querySelector('#photo-side'),
            side_type: document.querySelector('#photo-side').type,
            side_checked: document.querySelector('#photo-side').checked,
            side_visible: (() => { const e = document.querySelector('#photo-side'); return !!(e.offsetWidth || e.offsetHeight); })(),
            label_text: document.querySelector('#photo-tools').textContent.trim(),
            wrap_hidden: document.querySelector('#photo-wrap').hidden,
            wrap_visible: (() => { const e = document.querySelector('#photo-wrap'); return !!(e.offsetWidth || e.offsetHeight); })(),
            wrap_box: (() => { const r = document.querySelector('#photo-wrap').getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })(),
            state_photoView: BgApp.state.photoView,
            seg_photoView_count: document.querySelectorAll('.seg[data-name="photoView"]').length,
            photo_buttons_text: [...document.querySelectorAll('#photo-tools button')].map(b => b.textContent),
        })""")

    # 1
    R["1_initial"] = state()
    # 2
    page.click("#photo-side")
    page.wait_for_timeout(400)
    R["2_after_click1"] = state()
    page.click("#photo-side")
    page.wait_for_timeout(400)
    R["2_after_click2"] = state()
    # 3
    SHOT.parent.mkdir(parents=True, exist_ok=True)
    page.locator("#photo-tools").screenshot(path=str(SHOT))
    R["3_shot"] = str(SHOT)
    R["alerts"] = page.alerts
    browser.close()

print(json.dumps(R, ensure_ascii=False, indent=1))
