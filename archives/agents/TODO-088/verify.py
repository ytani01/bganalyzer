"""TODO-088 verifier, 390x844 touch. uv run -q --no-project --with playwright python archives/agents/TODO-088/verify.py"""
import json, os, struct, sys, zlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import pi_ui_check as pc
from playwright.sync_api import sync_playwright

OUT = Path("/home/ytani/tmp/playwright-mcp/todo088-verify"); OUT.mkdir(parents=True, exist_ok=True)
def say(*a): print(*a, flush=True)
def ev(page, js, arg=None): return page.evaluate(js, arg) if arg is not None else page.evaluate(js)

def black_png(path, w=800, h=600):
    raw = b"".join(b"\x00" + b"\x00\x00\x00" * w for _ in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))

def new_page(b):
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    page = ctx.new_page(); page.add_init_script(pc.INIT); page.on("dialog", lambda d: d.dismiss())
    page.goto(pc.URL); page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
    return page

def wait_corners(page):
    page.wait_for_function("!document.querySelector('#corners').hidden && document.querySelector('#busy').hidden && BgApp.state.cornerGuess !== 'finding'", timeout=60000)

HELP = """() => { const h = document.getElementById('corner-help'); const cs = getComputedStyle(h);
  const lh = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.2; const r = h.getBoundingClientRect();
  const row = document.getElementById('keep-corners').closest('.row');
  return {text: h.textContent, h: Math.round(r.height), lh: Math.round(lh), lines: Math.round(r.height / lh),
    keepRowText: row.textContent.trim(), nextSibText: row.nextElementSibling ? row.nextElementSibling.textContent.trim().slice(0, 40) : null,
    keepNoteNodes: [...row.parentElement.querySelectorAll('.note, small')].filter(e => e.getBoundingClientRect().height && e.closest('#corner-tools') && !e.closest('.opt')).map(e => e.textContent.trim())} }"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=pc.CHROMIUM) if os.path.exists(pc.CHROMIUM) else p.chromium.launch()
    say("version:", pc.URL, json.dumps(ev(new_page(b), "fetch('/version').then(r=>r.json())")))
    # 1
    page = new_page(b)
    r = ev(page, "(() => { const t = document.querySelector('.tips').getBoundingClientRect().top; return {tips: Math.round(t), buttons: [...document.querySelectorAll('.pick > *')].map(e => Math.round(e.getBoundingClientRect().bottom)), tipsText: document.querySelector('.tips summary').textContent}; })()")
    say("[1]", r, "OK" if all(r["tips"] >= x for x in r["buttons"]) and len(r["buttons"]) == 3 else "NG")
    page.screenshot(path=OUT / "1-photo.png")
    # 2: corners, real photo
    truth = json.loads((pc.ROOT / f"samples/{pc.SAMPLE}.truth.json").read_text())
    page.set_input_files("#file", str(pc.ROOT / "samples" / truth["image"])); wait_corners(page)
    page.evaluate("scrollTo(0,0)")
    r = ev(page, HELP); say("[2a] corners (screen1):", r); page.screenshot(path=OUT / "2-corners.png")
    # 2: black image
    pb = new_page(b); bp = Path("/tmp/claude-649/-home-ytani-work-bganalyzer/0e20e271-f3ba-444f-afce-bc6fde18bf68/scratchpad/black.png"); black_png(bp)
    pb.set_input_files("#file", str(bp)); wait_corners(pb)
    r = ev(pb, HELP); say("[2b] black image guess:", ev(pb, "BgApp.state.cornerGuess"), r, "| has 画像を編集:", "画像を編集" in r["text"])
    pb.screenshot(path=OUT / "2-corners-black.png"); pb.context.close()
    # board screen
    pc.read_photo(page)
    page.evaluate("scrollTo(0,0)"); page.screenshot(path=OUT / "3-board.png")
    B = "JSON.stringify(BgApp.state.board)"
    say("[3] loupe elements:", ev(page, "document.querySelectorAll('[class*=loupe], [id*=loupe]').length"))
    b0 = ev(page, B)
    box = page.locator("#photo-svg").bounding_box()
    page.touchscreen.tap(box["x"] + box["width"] * .5, box["y"] + box["height"] * .5)
    page.wait_for_timeout(300)
    say("[3] photo mid tap: board changed:", ev(page, B) != b0, "| palette shown:", ev(page, "!document.getElementById('palette').hidden"), "| photo hit rects:", ev(page, "document.querySelectorAll('#photo-svg .hit').length"))
    # board tap, a point with checkers
    page.locator("#board-svg .hit").nth(0).tap()
    b1 = ev(page, B); say("[3] board tap changed:", b1 != b0)
    page.evaluate("scrollTo(0,0)")
    hb = page.locator("#board-svg .hit").nth(5).bounding_box()
    x, y = hb["x"] + hb["width"] / 2, hb["y"] + 8
    page.mouse.move(x, y); page.mouse.down(); page.wait_for_timeout(800)
    say("[3] hold: palette shown:", ev(page, "!document.getElementById('palette').hidden"), "| title:", ev(page, "document.getElementById('palette-title').textContent"),
        "| side buttons:", ev(page, "[...document.getElementById('palette-side').children].map(e=>e.textContent.trim())"),
        "| loupe now:", ev(page, "document.querySelectorAll('[class*=loupe]').length"))
    page.screenshot(path=OUT / "3-hold.png")
    page.mouse.up(); page.click("#editor-title"); page.wait_for_timeout(200)
    # 6 (before touching cube/dice): marks after a fresh read
    page.evaluate("BgApp.update({board: " + b0 + "})")
    m = ev(page, """() => { const g = (id) => { const e = document.getElementById(id); return {hidden: e.hidden, text: e.textContent.trim(), rowSame: e.closest('.opt') ? e.closest('.opt').querySelector('.seg, .dice') !== null : null,
      prevText: e.previousElementSibling ? e.previousElementSibling.className : null}; }; return {dice: g('dice-note'), cube: g('cube-note'), diceFromPhoto: BgApp.state.diceFromPhoto, cubeFromPhoto: BgApp.state.cubeFromPhoto, cube: BgApp.state.cube, dice: BgApp.state.dice}; }""")
    say("[6] state:", m)
    say("[6] notes visible:", ev(page, "['dice-note','cube-note'].map(i => { const e = document.getElementById(i); return [i, !e.hidden, e.textContent.trim(), e.previousElementSibling.className || e.previousElementSibling.tagName]; })"))
    # 5: counts
    mk = "[document.getElementById('count-mark').hidden, document.getElementById('count-mark').textContent]"
    say("[5] matching:", ev(page, mk), "| errors text:", repr(ev(page, "document.getElementById('errors').textContent")), "| 白: text anywhere:", ev(page, "/盤上とバー|上がり \\d/.test(document.getElementById('board').innerText)"))
    st = ev(page, "BgApp.state.board")
    idx = next(i for i, n in enumerate(st["points"]) if n > 0)
    cut = dict(st, points=[n - 1 if i == idx else n for i, n in enumerate(st["points"])])
    page.evaluate("b => BgApp.update({board: b})", cut); page.wait_for_timeout(200)
    page.evaluate("scrollTo(0,0)")
    say("[5] one removed:", ev(page, mk), "| geometry:", ev(page, "(() => { const r = id => document.getElementById(id).getBoundingClientRect(); return {boardBottom: Math.round(r('board-svg').bottom), markTop: Math.round(r('count-mark').top), markBottom: Math.round(r('count-mark').bottom), editorTop: Math.round(r('editor').top), mark_in_pin: !!document.getElementById('count-mark').closest('#board-pin')}; })()"),
        "| errors:", repr(ev(page, "document.getElementById('errors').textContent")), "errors hidden:", ev(page, "document.getElementById('errors').hidden"))
    page.screenshot(path=OUT / "5-mark.png")
    page.evaluate("b => BgApp.update({board: b})", st); page.wait_for_timeout(200)
    say("[5] restored:", ev(page, mk))
    # 6: dice change removes dice mark
    page.select_option("#die1", "1" if ev(page, "document.getElementById('die1').value") != "1" else "2")
    say("[6] after dice edit: dice-note hidden:", ev(page, "document.getElementById('dice-note').hidden"), "| cube-note hidden:", ev(page, "document.getElementById('cube-note').hidden"))
    # 4: settings
    page.evaluate("scrollTo(0,0)")
    order = ev(page, """() => { const t = id => Math.round(document.getElementById(id).getBoundingClientRect().top);
      const seg = document.querySelector('.seg[data-name=cubeAt]').getBoundingClientRect().top;
      return {title: [...document.querySelectorAll('.panel-title')].map(e => e.textContent), cube: Math.round(seg), cubeSide: t('cube-side'), onroll: t('onroll-label'), dice: t('dice-row'),
        swapBtn: [...document.querySelectorAll('button')].filter(e => e.textContent.includes('入れ替える') && !e.closest('details')).map(e => e.textContent), flip: !!document.getElementById('flip-turn')}; }""")
    say("[4] order:", order, "cube<side<onroll<dice:", order["cube"] < order["cubeSide"] < order["onroll"] < order["dice"])
    say("[4] cube-side contents:", ev(page, "document.getElementById('cube-side').innerText"))
    page.locator('.seg[data-name="cubeAt"] [data-value="white"]').tap(); page.wait_for_timeout(200)
    sv = lambda: ev(page, "[document.getElementById('cube-side').hidden, document.getElementById('cube-offered').checked, document.getElementById('dice-row').hidden, getComputedStyle(document.getElementById('dice-row')).display]")
    say("[4] cube on white [side hidden, offered, dice hidden, display]:", sv())
    page.screenshot(path=OUT / "4-cube.png", full_page=True)
    page.locator("#cube-offered").evaluate("e => e.click()"); page.wait_for_timeout(200)
    say("[4] offered unchecked:", sv())
    b.close()
