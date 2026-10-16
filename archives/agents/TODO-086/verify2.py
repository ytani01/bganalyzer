"""TODO-086 re-check of 3 points. uv run -q --no-project --with playwright python archives/agents/TODO-086/verify2.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.argv = [sys.argv[0]]
import json, os
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import pi_ui_check as pc
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=pc.CHROMIUM) if os.path.exists(pc.CHROMIUM) else p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    page = ctx.new_page(); page.add_init_script(pc.INIT); page.goto(pc.URL)
    page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
    print("tips summary h:", page.evaluate("document.querySelector('.tips > summary').getBoundingClientRect().height"))
    truth = json.loads((pc.ROOT / "samples/screen1.truth.json").read_text())
    page.set_input_files("#file", str(pc.ROOT / "samples" / truth["image"]))
    page.wait_for_function("!document.querySelector('#corners').hidden && document.querySelector('#busy').hidden && BgApp.state.cornerGuess !== 'finding'", timeout=60000)
    print("keep-corners label h:", page.evaluate("(() => { const l = document.getElementById('keep-corners').closest('label'); const r = l.getBoundingClientRect(); return [l.tagName, Math.round(r.width), r.height]; })()"))
    page.click('.seg[data-name="homePick"] [data-value="left"]'); page.click('.seg[data-name="bottomColour"] [data-value="1"]')
    page.evaluate("c => BgApp.update({ corners: c, cornersMoved: true })", truth["corners_TL_TR_BR_BL"])
    page.click("#recognize")
    page.wait_for_function("!document.querySelector('#board').hidden && document.querySelector('#busy').hidden", timeout=120000)
    print("editor-title:", repr(page.evaluate("document.getElementById('editor-title').textContent")))
    b.close()
