"""TODO-093 check: corners screen shows the buttons unfolded and moves the match inputs.

    uv run -q --no-project --with playwright python archives/agents/TODO-093/verify_todo093.py
"""
import json, os, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path("/home/ytani/work/bganalyzer")
URL = os.environ.get("BG_URL", "http://127.0.0.1:8000/")
CHROMIUM = "/usr/bin/chromium"
SHOT = Path(os.path.expanduser("~/tmp/playwright-mcp/todo093-corners.png"))
SAMPLE = "screen1"

INIT = """
window.__spoken = [];
if (window.speechSynthesis) speechSynthesis.speak = (u) => { window.__spoken.push(u.text); };
delete Navigator.prototype.canShare; delete Navigator.prototype.share;
"""

results = {}

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROMIUM)
    page = browser.new_page(viewport={"width": 412, "height": 915})
    page.add_init_script(INIT)
    page.alerts = []
    page.on("dialog", lambda d: (page.alerts.append(d.message), d.dismiss()))
    page.goto(URL)
    page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")

    # 1. version
    results["1_version"] = page.evaluate("fetch('/version').then(r => r.json())")
    results["1_hdr_version"] = page.text_content("#hdr-version")

    # photo -> corners screen
    truth = json.loads((ROOT / f"samples/{SAMPLE}.truth.json").read_text())
    page.set_input_files("#file", str(ROOT / "samples" / truth["image"]))
    page.wait_for_function("BgApp.state.cornerGuess !== 'finding'", timeout=60000)
    page.wait_for_timeout(500)

    # 2. corners screen layout
    results["2_corners_visible"] = page.evaluate("!document.querySelector('#corners').hidden")
    results["2_edit_start_visible"] = page.is_visible("#edit-start")
    results["2_find_again_visible"] = page.is_visible("#find-again")
    results["2_details_in_corners"] = page.evaluate("document.querySelectorAll('#corners details').length")
    results["2_match_parent"] = page.evaluate("document.querySelector('#match').parentElement.id")
    results["2_match_visible"] = page.is_visible("#match")
    results["2_match_length_value"] = page.evaluate("document.querySelector('#match-length').value")

    # 3. set 7-point match, white 3 on corners screen
    page.select_option("#match-length", "7")
    page.wait_for_timeout(300)
    page.select_option("#score-white", "3")
    page.wait_for_timeout(300)
    results["3_before_read_match_parent"] = page.evaluate("document.querySelector('#match').parentElement.id")
    results["3_before_read_length"] = page.evaluate("document.querySelector('#match-length').value")
    results["3_before_read_white"] = page.evaluate("document.querySelector('#score-white').value")

    page.click(f'.seg[data-name="homePick"] [data-value="{truth["home"]}"]')
    page.click(f'.seg[data-name="bottomColour"] [data-value="{truth["bottom_colour"]}"]')
    page.evaluate("c => BgApp.update({ corners: c, cornersMoved: true })", truth["corners_TL_TR_BR_BL"])
    page.click("#recognize")
    page.wait_for_function("!document.querySelector('#board').hidden && document.querySelector('#busy').hidden",
                           timeout=120000)
    page.wait_for_timeout(500)
    results["3_board_match_parent"] = page.evaluate("document.querySelector('#match').parentElement.id")
    results["3_board_match_visible"] = page.is_visible("#match")
    results["3_board_length"] = page.evaluate("document.querySelector('#match-length').value")
    results["3_board_length_text"] = page.evaluate("document.querySelector('#match-length').selectedOptions[0].textContent")
    results["3_board_white"] = page.evaluate("document.querySelector('#score-white').value")
    results["3_alerts"] = page.alerts

    # 4. screenshot of corners screen: go back to corners via the step tabs
    page.evaluate("BgApp.update({ step: 'corners' })")
    page.wait_for_timeout(500)
    results["4_corners_visible"] = page.evaluate("!document.querySelector('#corners').hidden")
    results["4_match_parent_on_corners"] = page.evaluate("document.querySelector('#match').parentElement.id")
    SHOT.parent.mkdir(parents=True, exist_ok=True)
    page.locator("#corners").screenshot(path=str(SHOT))
    results["4_shot"] = str(SHOT)

    # 5. back to money game
    page.select_option("#match-length", "0")
    page.wait_for_timeout(300)
    results["5_length_after_reset"] = page.evaluate("document.querySelector('#match-length').value")

    browser.close()

for k, v in results.items():
    print(f"{k}: {json.dumps(v, ensure_ascii=False)}")
