"""TODO-070: 「画像を編集」 on the corners screen at 390x844.

1. samples/collected-sj1vrx.jpg (the board is small): cut round the board -> 確定 -> the corners found
   in the cut image, their largest distance from the truth (px of the cut image).
2. samples/photo2.jpg turned 90° to the left (as if taken sideways): 右に 90° -> 確定 -> the same.
Also prints what was kept (history entry size, trimmed). Screenshots go to OUT.

    BG_URL=http://127.0.0.1:8765/ OUT=<dir> uv run -q --no-project --with playwright --with opencv-python-headless python archives/agents/TODO-070/check_pwa.py
"""
import json, math, os
from pathlib import Path
import cv2
import numpy as np
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
URL = os.environ.get("BG_URL", "http://127.0.0.1:8765/")
OUT = Path(os.environ.get("OUT", "."))


def truth(name):
    return json.loads((ROOT / f"samples/{name}.truth.json").read_text())["corners_TL_TR_BR_BL"]


def err(cs, t):
    return None if not cs else round(max(math.dist(a, b) for a, b in zip(cs, t)), 1)


with sync_playwright() as p:
    exe = "/usr/bin/chromium" if Path("/usr/bin/chromium").exists() else None
    b = p.chromium.launch(executable_path=exe)
    page = b.new_page(viewport={"width": 390, "height": 844})
    page.on("pageerror", lambda e: print("PAGE ERROR:", e))
    page.goto(URL)
    wait = lambda: page.wait_for_function("() => state.photo && !state.busy && !['finding', 'again'].includes(state.cornerGuess) && !overlay", timeout=120000)
    st = lambda: page.evaluate("() => ({corners: state.corners, guess: state.cornerGuess, trimmed: state.photo.trimmed, size: [state.photo.bitmap.width, state.photo.bitmap.height], edit: state.edit, historyScale: state.historyScale})")
    at = lambda x, y: page.evaluate(f"() => {{ const r = $('photo-canvas').getBoundingClientRect(); const [x, y] = cornersView.toCanvas([{x}, {y}]); return [r.left + x, r.top + y]; }}")

    # 1. cut round the board
    t = truth("collected-sj1vrx")
    page.set_input_files("#file", str(ROOT / "samples/collected-sj1vrx.jpg"))
    wait()
    s = st(); W, H = s["size"]; print("1 first:", s["guess"], "size", s["size"])
    page.click("#edit-start")
    print("  edit tools shown:", page.is_visible("#edit-tools"), "| corner tools hidden:", not page.is_visible("#corner-tools"),
          "| recognize disabled:", page.is_disabled("#recognize"), "| help:", page.inner_text("#corner-help")[:30])
    pw, ph = page.evaluate("() => [editPreview().width, editPreview().height]")
    k = pw / W
    xs, ys = [q[0] for q in t], [q[1] for q in t]
    mx, my = 0.15 * (max(xs) - min(xs)), 0.15 * (max(ys) - min(ys))
    a, z = at((min(xs) - mx) * k, (min(ys) - my) * k), at((max(xs) + mx) * k, (max(ys) + my) * k)
    page.mouse.move(*a); page.mouse.down(); page.mouse.move(*z, steps=5); page.mouse.up()
    rect = st()["edit"]["rect"]; print("  rect:", [round(v, 3) for v in rect])
    page.screenshot(path=str(OUT / "1-cut.png"))
    page.click("#edit-done")
    wait()
    s = st()
    ox, oy = round(rect[0] * W), round(rect[1] * H)
    print("  after 確定:", s["guess"], "size", s["size"], "trimmed", s["trimmed"], "err px:", err(s["corners"], [[x - ox, y - oy] for x, y in t]),
          "| edit tools hidden:", not page.is_visible("#edit-tools"))
    page.screenshot(path=str(OUT / "2-cut-found.png"))
    e = page.evaluate("async () => { const e = await PhotoHistory.get(state.historyId); const b = await createImageBitmap(e.image); return [b.width, b.height, e.trimmed]; }")
    print("  history entry image:", e)

    # 2. a photo taken sideways
    t = truth("photo2")
    img = cv2.imread(str(ROOT / "samples/photo2.jpg"))
    side = OUT / "photo2-left.jpg"
    cv2.imwrite(str(side), cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE))
    page.set_input_files("#file", str(side))
    wait()
    print("2 first:", st()["guess"])
    page.click("#edit-start")
    page.click("#edit-right")
    page.screenshot(path=str(OUT / "3-turned.png"))
    page.click("#edit-done")
    wait()
    s = st()
    f = s["size"][0] / img.shape[1]
    print("  after 確定:", s["guess"], "size", s["size"], "trimmed", s["trimmed"], "err px (of the photo's size):",
          err([[x / f, y / f] for x, y in s["corners"]], t) if s["corners"] else None)
    page.screenshot(path=str(OUT / "4-turned-found.png"))
    b.close()
