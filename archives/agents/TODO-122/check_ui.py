"""TODO-122 check. BG_CDP=http://127.0.0.1:9222 uv run -q --no-project --with playwright python this.py"""
import os, json
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8001/"
ROOT = Path("/home/ytani/work/bganalyzer")
IMG = ROOT / "samples/collected-2aunci.jpg"
OUT = Path(__file__).parent

def info(page):
    return page.evaluate("""() => { const s = BgApp.state; const b = s.photo.bitmap;
      return {w: b.width, h: b.height, corners: s.corners.map(c => c.map(Math.round)), guess: s.cornerGuess,
              edit: s.edit, ver: document.querySelector('#hdr-version').textContent.trim()} }""")

def box(page, sel):
    return page.evaluate("s => { const r = document.querySelector(s).getBoundingClientRect(); return {x:r.x,y:r.y,w:r.width,h:r.height,b:r.bottom, hidden: document.querySelector(s).hidden, disp: getComputedStyle(document.querySelector(s)).display} }", sel)

def rect(page):
    return page.evaluate("() => BgApp.state.edit && BgApp.state.edit.rect && BgApp.state.edit.rect.map(v => +v.toFixed(4))")

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(os.environ["BG_CDP"])
    ctx = browser.contexts[0]
    page = ctx.new_page()
    page.goto(URL)
    page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
    page.set_input_files("#file", str(IMG))
    page.wait_for_function("BgApp.state.cornerGuess !== 'finding' && BgApp.state.cornerGuess !== ''", timeout=60000)
    page.wait_for_timeout(500)
    print("4. version:", info(page)["ver"])
    # 1
    c, t = box(page, "#photo-canvas"), box(page, "#turn-tools")
    print("1. canvas", c, "turn-tools", t, "gap", t["y"] - (c["y"] + c["h"]))
    before = info(page); print("2. before", before)
    page.click("#edit-right")
    page.wait_for_function("BgApp.state.cornerGuess !== 'finding' && BgApp.state.photo.bitmap.width !== %d" % before["w"], timeout=60000)
    page.wait_for_timeout(500)
    print("2. after", info(page))
    page.click("#edit-start"); page.wait_for_timeout(300)
    print("1b. edit mode turn-tools:", box(page, "#turn-tools"))
    c = box(page, "#photo-canvas"); print("canvas", c)
    def drag(a, b, steps=8):
        page.mouse.move(*a); page.mouse.down(); page.mouse.move(*b, steps=steps); page.mouse.up(); page.wait_for_timeout(200)
    A = (c["x"] + c["w"] * .25, c["y"] + c["h"] * .25); B = (c["x"] + c["w"] * .75, c["y"] + c["h"] * .75)
    drag(A, B); r0 = rect(page); print("3. drawn rect", r0)
    # mapping client = o + frac*size
    fx = lambda f: A[0] + (f - r0[0]) / (r0[2] - r0[0]) * (B[0] - A[0])
    fy = lambda f: A[1] + (f - r0[1]) / (r0[3] - r0[1]) * (B[1] - A[1])
    X0, Y0, X1, Y1 = A[0], A[1], B[0], B[1]
    drag((X0 + 2, Y0 + 2), (X0 - 40, Y0 - 30)); r1 = rect(page); print("3a. corner TL drag (-40,-30):", r0, "->", r1)
    drag((X1 - 2, (Y0 + Y1) / 2), (X1 + 20, (Y0 + Y1) / 2 + 40)); r2 = rect(page)
    print("3b. right edge drag (+20,+40):", r1, "->", r2)
    cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2
    drag((cx, cy), (cx + 100, cy + 80)); r3 = rect(page)
    print("3c. center (far from edges) drag (+100,+80):", r2, "->", r3)
    c = box(page, "#photo-canvas")
    drag((c["x"] + 200, c["y"] + c["h"] - 20), (c["x"] + 100, c["y"] + c["h"] - 120)); r4 = rect(page)
    print("3c'. outside (below rect) drag:", r3, "->", r4)
    page.screenshot(path=str(OUT / "edit.png"))
    page.close()
