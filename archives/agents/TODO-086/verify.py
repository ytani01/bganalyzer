"""TODO-086 verifier: 8 checks at 390x844 (touch). uv run -q --no-project --with playwright python archives/agents/TODO-086/verify.py"""
import json, os, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import pi_ui_check as pc
from playwright.sync_api import sync_playwright

W, H = 390, 844
OUT = Path("/home/ytani/tmp/playwright-mcp/todo086-verify"); OUT.mkdir(parents=True, exist_ok=True)
MEASURE = """() => [...document.querySelectorAll('button, input, select, label.button, a, summary')].filter(e => {
  const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && !e.closest('[hidden]');
}).map(e => { const r = e.getBoundingClientRect();
  return {id: e.id || e.dataset.value || '', text: e.textContent.trim().slice(0, 16), w: Math.round(r.width), h: Math.round(r.height)}; })"""
def say(*a): print(*a, flush=True)

def new_page(b, **kw):
    ctx = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=2, is_mobile=True, has_touch=True, **kw)
    page = ctx.new_page(); page.add_init_script(pc.INIT)
    page.on("dialog", lambda d: d.dismiss())
    page.goto(pc.URL)
    page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
    return page

def shot(page, name):
    page.evaluate("scrollTo(0, 0)")
    page.screenshot(path=OUT / f"{name}-top.png"); page.screenshot(path=OUT / f"{name}-full.png", full_page=True)
    ctl = page.evaluate(MEASURE); ph = page.evaluate("document.documentElement.scrollHeight")
    small = [c for c in ctl if min(c["w"], c["h"]) < 44]
    bar = page.evaluate("""() => { const a = document.getElementById('actbar'), r = a.getBoundingClientRect();
      return {display: getComputedStyle(a).display, pos: getComputedStyle(a).position, top: Math.round(r.top), bottom: Math.round(r.bottom),
        btns: [...a.querySelectorAll('button')].filter(b => !b.hidden && b.getBoundingClientRect().height).map(b => [b.id, Math.round(b.getBoundingClientRect().top), Math.round(b.getBoundingClientRect().height)])} }""")
    say(f"[1] {name}: page {ph}px, {len(small)} under 44px {[(c['id'] or c['text'], c['w'], c['h']) for c in small]}, actbar {bar}")

def read_photo(page, colour=None):
    truth = json.loads((pc.ROOT / f"samples/{pc.SAMPLE}.truth.json").read_text())
    if colour is not None: truth["bottom_colour"] = colour
    page.set_input_files("#file", str(pc.ROOT / "samples" / truth["image"]))
    page.wait_for_function("!document.querySelector('#corners').hidden && document.querySelector('#busy').hidden && BgApp.state.cornerGuess !== 'finding'", timeout=60000)
    return truth

def finish_read(page, truth):
    page.click(f'.seg[data-name="homePick"] [data-value="{truth["home"]}"]')
    page.click(f'.seg[data-name="bottomColour"] [data-value="{truth["bottom_colour"]}"]')
    page.evaluate("c => BgApp.update({ corners: c, cornersMoved: true })", truth["corners_TL_TR_BR_BL"])
    page.click("#recognize")
    page.wait_for_function("!document.querySelector('#board').hidden && document.querySelector('#busy').hidden", timeout=120000)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=pc.CHROMIUM) if os.path.exists(pc.CHROMIUM) else p.chromium.launch()
    page = new_page(b)
    shot(page, "1-photo")
    truth = read_photo(page)
    # corners-screen wording (for 6, reference only)
    shot(page, "2-corners")
    finish_read(page, truth)
    shot(page, "3-board")

    # 2: scroll to the bottom of the board screen
    page.evaluate("scrollTo(0, 1e6)"); page.wait_for_timeout(300)
    r = page.evaluate("""() => { const bar = document.getElementById('actbar').getBoundingClientRect();
      const els = [...document.querySelectorAll('#board *')].filter(e => { const r = e.getBoundingClientRect(); return r.width && r.height && !e.closest('[hidden]') && !(e.closest('details:not([open])') && e.tagName !== 'SUMMARY' && !e.closest('summary')); });
      const last = els.reduce((a, e) => e.getBoundingClientRect().bottom > a.getBoundingClientRect().bottom ? e : a);
      return {barTop: Math.round(bar.top), lastBottom: Math.round(last.getBoundingClientRect().bottom), last: last.tagName + '#' + last.id + '.' + last.className,
              main: Math.round(document.querySelector('main').getBoundingClientRect().bottom), scrollY: Math.round(scrollY), maxScroll: document.documentElement.scrollHeight - innerHeight} }""")
    page.screenshot(path=OUT / "3-board-bottom.png")
    say("[2]", r, "OK" if r["lastBottom"] <= r["barTop"] else "HIDDEN")
    page.evaluate("scrollTo(0, 0)")

    # 3: game type
    say("[3] header #match:", page.evaluate("!!document.querySelector('header #match')"),
        "| in board settings:", page.evaluate("!!document.querySelector('#board .panel #match') && !document.querySelector('#match').closest('[hidden]')"),
        "| score visible before:", page.evaluate("!document.getElementById('match-score').hidden"))
    page.locator("#match-length").scroll_into_view_if_needed()
    page.select_option("#match-length", index=2)
    say("    match-length ->", page.evaluate("document.getElementById('match-length').selectedOptions[0].textContent"),
        "| score visible after:", page.evaluate("!document.getElementById('match-score').hidden && getComputedStyle(document.getElementById('match-score')).display"))
    page.screenshot(path=OUT / "3-match.png")
    page.select_option("#match-length", index=0)

    # 4: folded
    say("[4] details.more open:", page.evaluate("[...document.querySelectorAll('details.more')].map(d => [d.querySelector('summary').textContent.trim(), d.open])"))
    say("    more-set before:", repr(page.evaluate("document.getElementById('more-set').textContent")))
    page.locator("#board details.more > summary").click()
    page.click('.seg[data-name="plies"] [data-value="3"]')
    page.locator("#board details.more > summary").click()
    say("    after 3手:", repr(page.evaluate("document.querySelector('#board details.more > summary').textContent.trim()")),
        "| open:", page.evaluate("document.querySelector('#board details.more').open"))
    page.locator("#board details.more").scroll_into_view_if_needed(); page.screenshot(path=OUT / "4-more-closed.png")
    page.click('.seg[data-name="plies"] [data-value="2"]') if False else None
    page.evaluate("BgApp.update && 0")

    # 5: cube
    vis = "(() => { const e = document.getElementById('dice-row'); return !e.hidden && !!e.getBoundingClientRect().height && getComputedStyle(e).display !== 'none'; })()"
    say("[5] dice row visible, cube centre:", page.evaluate(vis), "| cube-offered checked:", page.evaluate("document.getElementById('cube-offered').checked"))
    page.click('.seg[data-name="cubeAt"] [data-value="black"]')
    say("    cube at black: dice-row", page.evaluate(vis), "dice-note hidden:", page.evaluate("document.getElementById('dice-note').hidden || !document.getElementById('dice-note').getBoundingClientRect().height"),
        "offered:", page.evaluate("document.getElementById('cube-offered').checked"))
    page.locator("#cube-side").scroll_into_view_if_needed(); page.screenshot(path=OUT / "5-cube-offered.png")
    page.locator("#cube-offered").evaluate("e => e.closest('label').click()")
    say("    offered off: dice-row", page.evaluate(vis), "offered:", page.evaluate("document.getElementById('cube-offered').checked"))
    page.screenshot(path=OUT / "5-cube-not-offered.png")
    page.click('.seg[data-name="cubeAt"] [data-value="centre"]')

    # 6: wording
    page.locator("#board details.more > summary").click()
    t = page.evaluate("""() => { const f = (id) => document.getElementById(id).innerText; return f('board'); }""")
    say("[6] board 手前/奥 hits (visible innerText, details opened):", re.findall(r".{0,12}[手前奥].{0,12}", t))
    hid = page.evaluate("[...document.querySelectorAll('#board *')].filter(e => e.children.length === 0 && /[手前奥]/.test(e.textContent) && !e.closest('svg')).map(e => [e.tagName + '#' + e.id, e.textContent.trim().slice(0, 40), !!e.closest('[hidden]')])")
    say("    leaf nodes in #board with 手前/奥 (incl. hidden):", hid)
    svgt = page.evaluate("[...document.querySelectorAll('#board svg text')].map(e => e.textContent).filter(s => /[手前奥]/.test(s))")
    say("    svg text with 手前/奥:", svgt)
    page.evaluate("scrollTo(0,0)")
    page.click("#analyze"); page.wait_for_function("!document.querySelector('#outcome').hidden", timeout=120000)
    page.wait_for_function("!document.querySelector('#result').hidden", timeout=120000)
    shot(page, "4-outcome")
    res = page.evaluate("document.getElementById('outcome').innerText")
    say("    outcome 手前/奥 hits:", re.findall(r".{0,12}[手前奥].{0,12}", res))
    say("    outcome text:", repr(res[:500]))
    page.evaluate("scrollTo(0,0)"); page.screenshot(path=OUT / "6-outcome-bright.png")
    head1 = page.evaluate("[...document.querySelectorAll('#result h2, #result th, #result td:first-child')].map(e => e.textContent.trim())")
    spoken_hits = page.evaluate("(window.__spoken||[]).join('|')")
    # swapped colour
    pg2 = new_page(b)
    tr2 = read_photo(pg2, colour=0); finish_read(pg2, tr2)
    pg2.click("#analyze"); pg2.wait_for_function("!document.querySelector('#outcome').hidden && !document.querySelector('#result').hidden", timeout=120000)
    pg2.screenshot(path=OUT / "6-outcome-dark-colour.png")
    head2 = pg2.evaluate("[...document.querySelectorAll('#result h2, #result th, #result td:first-child')].map(e => e.textContent.trim())")
    say("    bright(1) headings:", head1); say("    dark(0) headings:  ", head2)
    say("    outcome text (dark 0):", repr(pg2.evaluate("document.getElementById('outcome').innerText")[:500]))
    pg2.close()
    # corners-screen 手前 (reference)
    pg3 = new_page(b); read_photo(pg3)
    say("    corners-screen hits (ok to keep 手前):", re.findall(r".{0,10}[手前奥].{0,10}", pg3.evaluate("document.getElementById('corners').innerText")))
    pg3.close()

    # 7: loupe, on the board screen of `page`
    page.goto(pc.URL); page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
    pg = new_page(b); t7 = read_photo(pg); finish_read(pg, t7)
    pg.evaluate("scrollTo(0,0)")
    # a point with checkers: point index 5 (5 white checkers), take its lower-half hit rect
    info = pg.evaluate("""() => { const hits = [...document.querySelectorAll('#board-svg .hit')]; 
      const out = hits.map((h, i) => { const r = h.getBoundingClientRect(); return {i, x: r.x + r.width / 2, y: r.y + r.height / 2, w: r.width, h: r.height}; });
      return out; }""")
    # pick the point with highest checker count (point 6 = index 5, white 5), via board state
    st = pg.evaluate("BgApp.state.board.points")
    idx = max(range(24), key=lambda i: abs(st[i]))
    say("[7] board points:", st, "-> using point index", idx, "count", st[idx])
    # find the hit rect at that point: hits are in order for bottom/top; choose by x and half
    cands = [h for h in info if h["w"] > 0]
    say("    hit rects:", len(cands), "sample", cands[0])
    cdp = pg.context.new_cdp_session(pg)
    def touch(kind, x, y):
        cdp.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": [] if kind == "touchEnd" else [{"x": x, "y": y}]})
    loupe = "document.querySelectorAll('.loupe').length"
    def hit_for(idx):
        # find the .hit rect whose centre-x matches the point and whose stack is there: try each hit and check by tapping later
        return None
    # locate the hit via elementFromPoint search: pick hit rects, find the one whose state is point idx using tap effect
    # simpler: compute from the first-level position of the white stack: use the hit rect list sorted; point idx -> pair of rects
    def snap(): return pg.evaluate("BgApp.state.board.points.slice()")
    # choose rect by testing: the lower row for white (points[i] > 0 sits on bottom?) -> try both and take the one that changes idx
    base = snap()
    chosen = None
    for h in cands:
        if not (0 <= h["y"] < H and 0 <= h["x"] < W): continue
        # ensure the rect is the same column as the chosen point: tap and diff
        touch("touchStart", h["x"], h["y"]); touch("touchEnd", h["x"], h["y"]); pg.wait_for_timeout(150)
        now = snap()
        diff = [i for i in range(24) if now[i] != base[i]]
        if diff:
            chosen = (h, diff, base[diff[0]], now[diff[0]]); break
    say("    tap on first rect on screen -> changed:", chosen[1:] if chosen else None)
    h = chosen[0]
    pg.evaluate("(p) => BgApp.update({board: {...BgApp.state.board, points: p}})", base)
    pg.wait_for_timeout(200); assert snap() == base
    # loupe: hold 300ms
    touch("touchStart", h["x"], h["y"]); pg.wait_for_timeout(300)
    n_hold = pg.evaluate(loupe); box = pg.evaluate("(() => { const l = document.querySelector('.loupe'); if (!l) return null; const r = l.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })()")
    pg.screenshot(path=OUT / "7-loupe.png")
    touch("touchEnd", h["x"], h["y"]); pg.wait_for_timeout(150)
    say("    loupe at 300ms:", n_hold, box, "| after release:", pg.evaluate(loupe), "| points changed by that tap:", snap() != base)
    pg.evaluate("(p) => BgApp.update({board: {...BgApp.state.board, points: p}})", base); pg.wait_for_timeout(150)
    # fast big move
    touch("touchStart", h["x"], h["y"]); pg.wait_for_timeout(10); touch("touchMove", h["x"], h["y"] - 60); pg.wait_for_timeout(350)
    n_move = pg.evaluate(loupe); touch("touchEnd", h["x"], h["y"] - 60); pg.wait_for_timeout(100)
    say("    loupe after quick move (350ms later):", n_move, "| points changed:", snap() != base)
    # tap -> count
    pg.evaluate("(p) => BgApp.update({board: {...BgApp.state.board, points: p}})", base); pg.wait_for_timeout(150)
    touch("touchStart", h["x"], h["y"]); pg.wait_for_timeout(60); touch("touchEnd", h["x"], h["y"]); pg.wait_for_timeout(200)
    after = snap(); say("    tap(60ms hold): changed", [(i, base[i], after[i]) for i in range(24) if base[i] != after[i]], "| palette visible:", pg.evaluate("!document.getElementById('palette').hidden"))
    pg.evaluate("(p) => BgApp.update({board: {...BgApp.state.board, points: p}})", base); pg.wait_for_timeout(150)
    touch("touchStart", h["x"], h["y"]); pg.wait_for_timeout(700)
    pal = pg.evaluate("(() => { const e = document.getElementById('palette'); return {hidden: e.hidden, text: e.innerText.slice(0, 80), loupe: document.querySelectorAll('.loupe').length}; })()")
    pg.screenshot(path=OUT / "7-palette.png"); touch("touchEnd", h["x"], h["y"]); pg.wait_for_timeout(150)
    say("    long press:", pal)
    pg.close()

    # 8: dark
    pd = new_page(b, color_scheme="dark"); td = read_photo(pd); finish_read(pd, td)
    pd.evaluate("scrollTo(0,0)"); pd.screenshot(path=OUT / "8-dark-board-top.png"); pd.screenshot(path=OUT / "8-dark-board-full.png", full_page=True)
    say("[8] dark scheme:", pd.evaluate("matchMedia('(prefers-color-scheme: dark)').matches"), "body bg", pd.evaluate("getComputedStyle(document.body).backgroundColor"))
    b.close()
