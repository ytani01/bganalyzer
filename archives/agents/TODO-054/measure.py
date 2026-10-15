"""TODO-054: measure how long each streamed reading stage is shown on the PWA (/analyze-photo).

    uv run -q --no-project --with playwright python archives/agents/TODO-054/measure.py [URL]

Opens the PWA in headless Chromium, loads samples/photo2.jpg, sets the corners from its truth
file (as tools/pi_ui_check.py does), and presses 盤面を読み取る once. The stage clock is read by
a one-line log injected into the served scan.js (route), at the moment each stage is set on screen
(the `cur.t0 = now` line, rAF time = performance.now() clock). The /analyze-photo stream is buffered
so that every stage is queued at once: the hold of each stage is then only STAGE_MS (without this, a
stage waits for the server and the hold is longer). Nothing is tapped to skip a stage.
Prints the table of durations and the STAGE_MS in effect.
"""
import json, sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8011/"
CHROMIUM = "/usr/bin/chromium"
TRUTH = json.loads((ROOT / "samples/photo2.truth.json").read_text())
ANCHOR = "        cur.t0 = now;"
LOG = "        cur.t0 = now; (window.__stg ||= []).push([cur.stage, now]);"
ARRIVE = "queue.push({ stage, data });"
ARRIVE_LOG = "queue.push({ stage, data }); (window.__arr ||= []).push([stage, performance.now()]);"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROMIUM)
        page = browser.new_page(viewport={"width": 412, "height": 915})

        def patch(route):
            resp = route.fetch()
            body = resp.text()
            assert body.count(ANCHOR) == 1, "anchor line not found exactly once"
            assert body.count(ARRIVE) == 1, "arrival line not found exactly once"
            body = body.replace(ANCHOR, LOG).replace(ARRIVE, ARRIVE_LOG)
            route.fulfill(response=resp, body=body)

        def buffer_stream(route):
            # all stages arrive at once (the server's pace would stretch the holds); the stages are still shown in turn
            resp = route.fetch()
            route.fulfill(response=resp, body=resp.body())

        page.route("**/scan.js", patch)
        page.route("**/analyze-photo", buffer_stream)
        page.goto(URL)
        page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
        page.set_input_files("#file", str(ROOT / "samples" / TRUTH["image"]))
        page.wait_for_function("state.cornerGuess !== 'finding'", timeout=60000)
        page.click(f'.seg[data-name="homePick"] [data-value="{TRUTH["home"]}"]')
        page.click(f'.seg[data-name="bottomColour"] [data-value="{TRUTH["bottom_colour"]}"]')
        page.evaluate("c => { state.corners = c; state.cornersMoved = true; }", TRUTH["corners_TL_TR_BR_BL"])
        page.evaluate("window.__stg = []; window.__arr = []")
        page.click("#recognize")
        page.wait_for_function("!document.querySelector('#board').hidden && document.querySelector('#busy').hidden",
                           timeout=120000)
        log = page.evaluate("window.__stg")
        arr = page.evaluate("window.__arr")
        stage_ms = page.evaluate("BgScan.STAGE_MS")
        version = page.text_content("#hdr-version")
        browser.close()

    print("version on screen:", version.strip())
    print("STAGE_MS:", json.dumps(stage_ms, ensure_ascii=False))
    print("arrivals (server -> client, ms from first shown):", [(s, round(t - (log[0][1] if log else 0))) for s, t in arr])
    print("n\tstage\tstart_ms\tshown_ms\tSTAGE_MS\tnext_arrived_before_end")
    t0 = log[0][1] if log else 0
    for i, (stage, t) in enumerate(log):
        shown = (log[i + 1][1] - t) if i + 1 < len(log) else None
        ends = t + stage_ms.get(stage, 1000)
        # the next stage had arrived by the time this one's STAGE_MS was up: the hold is not server-bound
        waiting = [a for a in arr if a[1] <= ends]
        free = "yes" if len(waiting) > i + 1 else "no (waited for server)"
        print(f"{i}\t{stage}\t{t - t0:.0f}\t{'-' if shown is None else f'{shown:.0f}'}\t{stage_ms.get(stage, 'default')}\t{free}")


if __name__ == "__main__":
    main()
