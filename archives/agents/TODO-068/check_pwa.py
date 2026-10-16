"""TODO-068: the corners screen at 390x844 with samples/collected-sj1vrx.jpg.

1. the first search (not found), 2. trim round the board -> looked for again, 3. move corner 1 ->
look again: corner 1 stays, the others are placed again. Prints the corners (image px) and their
largest distance from the truth; screenshots go to OUT.

    BG_URL=http://127.0.0.1:8765/ OUT=<dir> uv run -q --no-project --with playwright python archives/agents/TODO-068/check_pwa.py
"""
import json, math, os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
URL = os.environ.get("BG_URL", "http://127.0.0.1:8765/")
OUT = Path(os.environ.get("OUT", "."))
truth = json.loads((ROOT / "samples/collected-sj1vrx.truth.json").read_text())["corners_TL_TR_BR_BL"]


def err(cs):
    return round(max(math.dist(a, b) for a, b in zip(cs, truth)), 1)


with sync_playwright() as p:
    exe = "/usr/bin/chromium" if Path("/usr/bin/chromium").exists() else None
    b = p.chromium.launch(executable_path=exe)
    page = b.new_page(viewport={"width": 390, "height": 844})
    page.goto(URL)
    page.set_input_files("#file", str(ROOT / "samples/collected-sj1vrx.jpg"))
    wait = lambda: page.wait_for_function("() => !['finding', 'again'].includes(state.cornerGuess) && !overlay", timeout=120000)
    st = lambda: page.evaluate("() => ({corners: state.corners, guess: state.cornerGuess, fixed: state.cornersFixed, crop: state.crop})")
    page.wait_for_function("() => state.photo", timeout=60000)
    wait()
    s = st(); print("first:", s["guess"], s["corners"], "help:", page.inner_text("#corner-help")[:40])
    page.screenshot(path=str(OUT / "1-first.png"))

    at = lambda x, y: page.evaluate(f"() => {{ const r = $('photo-canvas').getBoundingClientRect(); const [x, y] = cornersView.toCanvas([{x}, {y}]); return [r.left + x, r.top + y]; }}")
    xs, ys = [q[0] for q in truth], [q[1] for q in truth]
    mx, my = 0.15 * (max(xs) - min(xs)), 0.15 * (max(ys) - min(ys))
    page.click("#crop-start")
    print("trim help:", page.inner_text("#corner-help")[:30], "| button:", page.inner_text("#crop-start"))
    a, z = at(min(xs) - mx, min(ys) - my), at(max(xs) + mx, max(ys) + my)
    page.mouse.move(*a); page.mouse.down(); page.mouse.move(*z, steps=5)
    page.screenshot(path=str(OUT / "2-drawing.png"))
    page.mouse.up()
    wait()
    s = st(); print("after trim:", s["guess"], s["corners"], "crop:", s["crop"], "err px:", err(s["corners"]),
                    "| 範囲を戻す shown:", page.is_visible("#crop-clear"))
    page.screenshot(path=str(OUT / "3-trimmed.png"))

    # corner 1 moved 12 px right and down; corner 3 pushed off so its placing again shows
    c0 = s["corners"][0]
    x, y = at(*c0)
    page.mouse.move(x, y); page.mouse.down(); page.mouse.move(*at(c0[0] + 12, c0[1] + 12), steps=3); page.mouse.up()
    page.evaluate("() => update({corners: state.corners.map((c, k) => k === 2 ? [c[0] - 40, c[1] - 40] : c)})")
    s = st(); moved = s["corners"]; print("moved:", moved, "fixed:", s["fixed"])
    page.click("#find-again")
    wait()
    s = st(); print("again:", s["guess"], s["corners"], "corner 1 kept:", s["corners"][0] == moved[0], "err px:", err(s["corners"]))
    page.screenshot(path=str(OUT / "4-again.png"))

    page.click("#crop-clear")
    s = st(); print("crop cleared:", s["crop"], "| 範囲を戻す shown:", page.is_visible("#crop-clear"))
    page.screenshot(path=str(OUT / "5-whole.png"))
    b.close()
