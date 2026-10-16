"""TODO-070 verifier: 3a-3e at 390x844. BG_URL, OUT as check_pwa.py."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
URL = os.environ.get("BG_URL", "http://127.0.0.1:8765/")
OUT = Path(os.environ.get("OUT", "."))
SJ = str(ROOT / "samples/collected-sj1vrx.jpg")

with sync_playwright() as p:
    exe = "/usr/bin/chromium" if Path("/usr/bin/chromium").exists() else None
    b = p.chromium.launch(executable_path=exe)
    page = b.new_page(viewport={"width": 390, "height": 844})
    page.on("pageerror", lambda e: print("PAGE ERROR:", e))
    posts = []
    page.on("request", lambda r: posts.append((r.url, (r.post_data_buffer or b"").decode("latin-1"))) if r.method == "POST" else None)
    page.add_init_script("window.__crop = []; const a = FormData.prototype.append; FormData.prototype.append = function (k, v, ...r) { if (k === 'crop') window.__crop.push(String(v)); return a.call(this, k, v, ...r); };")
    page.goto(URL)
    wait = lambda: page.wait_for_function("() => state.photo && !state.busy && !['finding', 'again'].includes(state.cornerGuess) && !overlay", timeout=120000)
    st = lambda: page.evaluate("() => ({corners: state.corners, guess: state.cornerGuess, trimmed: state.photo.trimmed, size: [state.photo.bitmap.width, state.photo.bitmap.height], edit: state.edit, step: state.step})")
    at = lambda x, y: page.evaluate(f"() => {{ const r = $('photo-canvas').getBoundingClientRect(); const [x, y] = cornersView.toCanvas([{x}, {y}]); return [r.left + x, r.top + y]; }}")
    def drag(fx0, fy0, fx1, fy1):
        pw, ph = page.evaluate("() => [editPreview().width, editPreview().height]")
        a, z = at(fx0 * pw, fy0 * ph), at(fx1 * pw, fy1 * ph)
        page.mouse.move(*a); page.mouse.down(); page.mouse.move(*z, steps=5); page.mouse.up()
    def load(path):
        page.set_input_files("#file", path); wait()

    # 3a rectangle then right 90
    load(SJ); W, H = st()["size"]; print("photo", W, H)
    page.click("#edit-start"); drag(0.2, 0.3, 0.6, 0.7)
    r0 = st()["edit"]["rect"]; print("3a rect drawn:", [round(v, 3) for v in r0], "px in photo:", round((r0[2]-r0[0])*W), "x", round((r0[3]-r0[1])*H))
    page.click("#edit-right"); e1 = st()["edit"]; print("  after 右90 state.edit:", {k: (round(v,3) if isinstance(v,float) else v) for k, v in e1.items() if k != "rect"}, "rect:", e1["rect"] and [round(v, 3) for v in e1["rect"]])
    page.screenshot(path=str(OUT / "5-editing-rect-turned.png"))
    page.click("#edit-done"); wait(); s = st()
    print("  after 確定 size:", s["size"], "trimmed", s["trimmed"])
    print("  expect if rect turns with image: ", round((r0[3]-r0[1])*H), "x", round((r0[2]-r0[0])*W),
          "| if rect kept as drawn on turned view: ", round((e1["rect"][2]-e1["rect"][0])*H), "x", round((e1["rect"][3]-e1["rect"][1])*W) if e1["rect"] else None)

    # 3b angle 10
    load(SJ); W, H = st()["size"]
    page.click("#edit-start")
    page.evaluate("() => { const i = $('edit-angle'); i.value = '10'; i.dispatchEvent(new Event('input', {bubbles: true})); }")
    print("3b #edit-angle-text:", repr(page.inner_text("#edit-angle-text")), "state angle", st()["edit"]["angle"])
    page.screenshot(path=str(OUT / "6-editing-angle10.png"))
    page.click("#edit-done"); wait(); s = st()
    print("  before", [W, H], "after 確定 size:", s["size"], "max side <= 2048:", max(s["size"]) <= 2048, "trimmed", s["trimmed"])
    page.screenshot(path=str(OUT / "7-angle10-found.png"))
    corner = page.evaluate("""() => { const b = state.photo.bitmap, c = document.createElement('canvas'); c.width = b.width; c.height = b.height;
        const x = c.getContext('2d'); x.drawImage(b, 0, 0); return [...x.getImageData(0,0,1,1).data, ...x.getImageData(b.width-1,b.height-1,1,1).data]; }""")
    print("  pixels TL, BR corner RGBA:", corner)

    # 3c cancel
    load(SJ); s0 = st(); c0 = s0["corners"]
    page.click("#edit-start"); drag(0.2, 0.3, 0.6, 0.7); page.click("#edit-right")
    page.click("#edit-cancel"); s1 = st()
    print("3c cancel: size same", s0["size"] == s1["size"], "corners same", c0 == s1["corners"], "edit", s1["edit"], "trimmed", s1["trimmed"])

    # 3d back while editing, then reopen from history
    page.click("#edit-start"); page.click("#edit-right")
    print("3d editing:", st()["edit"] is not None)
    page.click("#back"); print("  after 戻る step:", st()["step"], "edit:", st()["edit"])
    page.click("#history-list li .open"); wait(); s = st()
    print("  reopened: edit", s["edit"], "| edit tools visible:", page.is_visible("#edit-tools"), "| corner tools visible:", page.is_visible("#corner-tools"), "| corners", len(s["corners"] or []))

    # 3e crop field
    def find_again_post():
        page.evaluate("() => { window.__crop = []; }"); n = len(posts); page.click("#find-again"); wait()
        return {"find-corners POSTs": len([1 for u, d in posts[n:] if "find-corners" in u]), "crop values": page.evaluate("() => window.__crop")}
    has_crop = lambda x: x
    load(SJ); page.click("#back"); page.click("#history-list li .open"); wait()
    print("3e uncropped: trimmed", st()["trimmed"], "crop fields:", has_crop(find_again_post()))
    load(SJ); page.click("#edit-start"); drag(0.2, 0.3, 0.6, 0.7); page.click("#edit-done"); wait()
    sz = st()["size"]
    page.click("#back"); page.click("#history-list li .open"); wait(); s = st()
    print("  cropped: size", sz, "reopened size", s["size"], "trimmed", s["trimmed"], "crop fields:", has_crop(find_again_post()))
    b.close()
