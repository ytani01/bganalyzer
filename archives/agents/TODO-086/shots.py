"""TODO-086: take the four PWA screens at a phone size (full page and the first screenful), and measure
how far down the main buttons are and how small the tap targets are.

    uv run -q --no-project --with playwright python archives/agents/TODO-086/shots.py OUTDIR
"""
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import pi_ui_check as pc
from playwright.sync_api import sync_playwright

W, H = 390, 844
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)

# visible buttons/inputs: size and position (y below the first screenful = needs scrolling)
MEASURE = """() => [...document.querySelectorAll('button, input, select, label.button, a')].filter(e => {
  const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && !e.closest('[hidden]');
}).map(e => { const r = e.getBoundingClientRect();
  return {id: e.id || e.dataset.value || '', text: e.textContent.trim().slice(0, 16),
          w: Math.round(r.width), h: Math.round(r.height), y: Math.round(r.top + scrollY)}; })"""

def shot(page, name):
    page.evaluate("scrollTo(0, 0)")
    page.screenshot(path=OUT / f"{name}-top.png")
    page.screenshot(path=OUT / f"{name}-full.png", full_page=True)
    data = {"page_h": page.evaluate("document.documentElement.scrollHeight"), "controls": page.evaluate(MEASURE)}
    (OUT / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    small = [c for c in data["controls"] if min(c["w"], c["h"]) < 44]
    below = [c for c in data["controls"] if c["y"] > H]
    print(f"{name}: page {data['page_h']}px, {len(data['controls'])} controls, "
          f"{len(small)} under 44px, {len(below)} below the first screen")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=pc.CHROMIUM) if os.path.exists(pc.CHROMIUM) else p.chromium.launch()
    page = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=2, is_mobile=True, has_touch=True)
    page.add_init_script(pc.INIT)
    page.on("dialog", lambda d: d.dismiss())
    page.goto(pc.URL)
    page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
    shot(page, "1-photo")
    truth = json.loads((pc.ROOT / f"samples/{pc.SAMPLE}.truth.json").read_text())
    page.set_input_files("#file", str(pc.ROOT / "samples" / truth["image"]))
    # the corners screen, once the photo is loaded and the corners are found (not under the busy overlay)
    page.wait_for_function("!document.querySelector('#corners').hidden && document.querySelector('#busy').hidden"
                           " && BgApp.state.cornerGuess !== 'finding'", timeout=60000)
    shot(page, "2-corners")
    pc.read_photo(page)   # the truth's corners, so that the board can be analysed
    shot(page, "3-board")
    pc.show_outcome(page)
    shot(page, "4-outcome")
    b.close()
