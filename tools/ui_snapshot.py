"""Record what the PWA shows while it is used, to compare two versions of the app (e.g. before and after
changing app.js). Only what is visible counts: a screen hidden behind another is not recorded.

The app is used with clicks only, as a person would (nothing inside app.js is read or called), through
three flows: "manual" (a board set up by hand: editing, dice, cube, turn, analysis, reading aloud),
"photo" (samples/screen1.png: corners, reading, the photo beside the board, tapping and dragging
corners) and "history" (reopening and deleting a photo kept on the phone). After each step it keeps
the visible screen: which parts show, their text, the board pictures (SVG), the photo canvas (a hash
of its pixels), the result, what was read aloud and the alerts.

    uv run -q --no-project --with playwright python tools/ui_snapshot.py record before.json
    uv run -q --no-project --with playwright python tools/ui_snapshot.py record after.json manual photo
    uv run -q --no-project --with playwright python tools/ui_snapshot.py compare before.json after.json

record needs the app running with gnubg (BG_URL, default http://127.0.0.1:8000/) and a Chromium
(BG_CHROMIUM, default the Pi's /usr/bin/chromium; Playwright's own when that is missing).
compare prints each difference and exits 1 if there is any. Two versions side by side, for example:

    git worktree add ../base main
    (cd ../base && uv run uvicorn app:app --app-dir analyzer --port 8001) &
    uv run uvicorn app:app --app-dir analyzer --port 8000 &
    BG_URL=http://127.0.0.1:8001/ ... record before.json;  BG_URL=http://127.0.0.1:8000/ ... record after.json

The recording is the same from run to run (checked by recording twice), so any difference is the app's.
"""
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = os.environ.get("BG_URL", "http://127.0.0.1:8000/")
CHROMIUM = os.environ.get("BG_CHROMIUM", "/usr/bin/chromium")
SAMPLE = "screen1"   # an app screenshot with dice (4-2): read the same every time
WAIT = 180000        # ms: a reading or an analysis on the Pi

# before the app's scripts: record what would be spoken, and no share sheet
INIT = """
window.__spoken = [];
// saving on the server is the app's default (TODO-112): off here, or every run would leave a pair in collected/
try { if (!localStorage.getItem("collect")) localStorage.setItem("collect", "off"); } catch (_) { /* no storage */ }
// 手前's colour is kept on the phone (TODO-113): each flow starts from the lighter checkers, whatever ran before it
try { localStorage.removeItem("bottomColour"); } catch (_) { /* no storage */ }
if (window.speechSynthesis) speechSynthesis.speak = (u) => { window.__spoken.push(u.text); };
// Google's voice through /speech (TODO-111): note the sentence asked for, and play nothing
HTMLMediaElement.prototype.play = function () {
  const text = new URL(this.src, location.href).searchParams.get("text");
  if (text) window.__spoken.push(text);
  setTimeout(() => this.dispatchEvent(new Event("ended")));
  return Promise.resolve();
};
delete Navigator.prototype.canShare; delete Navigator.prototype.share;
"""

# What is on screen. A part that is hidden (or inside something hidden) is recorded as null.
SNAP = """() => {
  const el = (id) => document.getElementById(id);
  const vis = (id) => { const e = el(id); return !!e && !e.hidden && !e.closest('[hidden]'); };
  const txt = (id) => (vis(id) ? el(id).textContent.trim() : null);
  const html = (id) => (vis(id) ? el(id).innerHTML : null);
  const hash = (s) => { let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return [s.length, h]; };
  const segs = {};
  for (const s of document.querySelectorAll('.seg')) {
    if (!s.offsetParent) continue;
    const on = s.querySelector('.on'); segs[s.dataset.name] = on ? on.dataset.value : null;
  }
  const shown = {};
  for (const id of ['back', 'recognize', 'hdr-reuse', 'analyze', 'speak', 'busy', 'errors', 'count-mark', 'home-note',
                    'palette', 'dice-note', 'cube-note', 'cube-side', 'photo-tools', 'photo-wrap', 'result',
                    'export-sample', 'history']) shown[id] = vis(id);
  return {
    step: [...document.querySelectorAll('section.step')].filter((s) => !s.hidden).map((s) => s.id),
    shown, segs, title: txt('title'), sheet: [...document.querySelectorAll('.sheet')].filter((e) => !e.hidden).map((e) => e.id)[0] || null,
    cornerHelp: html('corner-help'), recognizeDisabled: vis('recognize') ? el('recognize').disabled : null,
    canvas: vis('photo-canvas') ? hash(el('photo-canvas').toDataURL()) : null,
    countMark: txt('count-mark'), errors: txt('errors'), homeNote: txt('home-note'), editor: txt('editor-title'),
    palette: vis('palette') ? [txt('palette-title'), ...['#palette-side .on', '#palette-counts .on'].map((q) => {
      const e = document.querySelector(q); return e && (e.dataset.value || e.dataset.n); })] : null,
    undo: vis('undo') ? !el('undo').disabled : null,
    cubeHelp: txt('cube-help'), rollLabel: txt('onroll-label'),
    dice: vis('die1') ? [el('die1').dataset.value, el('die2').dataset.value] : null,
    cube: vis('cube-side') ? [el('cube-value').value, el('cube-offered').checked] : null,
    boardSvg: html('board-svg'),
    photoSvg: vis('photo-svg') ? hash(el('photo-svg').innerHTML) : null,
    twoBoards: vis('boards') ? el('boards').classList.contains('two') : null,
    result: html('result'), stale: vis('result') ? el('result').classList.contains('stale') : null,
    spoken: window.__spoken.slice(), speakLabel: txt('speak'),
    history: vis('history') ? [...document.querySelectorAll('#history-list .sub')].map((e) => e.textContent) : null,
    colours: ['--white-chk', '--black-chk'].map((v) => document.documentElement.style.getPropertyValue(v)),
  };
}"""


class Run:
    """One recording: the page in use and the snapshots taken so far."""

    def __init__(self, ctx):
        self.ctx, self.snaps, self.page = ctx, [], None

    def open(self):
        page = self.ctx.new_page()
        page.alerts = []
        page.on("dialog", lambda d: (page.alerts.append(d.message), d.accept() if d.type == "confirm" else d.dismiss()))
        page.goto(URL)
        page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
        self.page = page

    def snap(self, name):
        self.page.wait_for_function("document.getElementById('busy').hidden", timeout=WAIT)
        s = self.page.evaluate(SNAP)
        s["alerts"] = list(self.page.alerts)
        self.page.alerts.clear()
        self.snaps.append([name, s])

    def sheet_for(self, selector=None):     # open the sheet the selector is in (TODO-113), or close the one open, by taps
        want, shown = self.page.evaluate("""(q) => {
          const sh = q && document.querySelector(q)?.closest('.sheet');
          return [sh ? sh.id : null, [...document.querySelectorAll('.sheet')].find((e) => !e.hidden)?.id || null];
        }""", selector)
        if shown and shown != want:
            self.page.click(f"#{shown} .sheet-close")
        if want and shown != want:
            self.page.locator(f'#board-svg [data-part="{want[len("sheet-"):]}"]').first.click()

    def click(self, selector):
        self.sheet_for(selector)
        self.page.click(selector)

    def part(self, kind):                   # a tap on a part around the board picture: home, colour, match, cube, roll
        self.sheet_for()
        self.page.locator(f'#board-svg [data-part="{kind}"]').first.click()

    def seg(self, name, value):
        self.click(f'.seg[data-name="{name}"] [data-value="{value}"]')

    def point(self, k, svg="#board-svg"):   # the middle of the k-th tap area of a board picture (24, 25: the bar)
        self.sheet_for()
        self.page.locator(f"{svg} .hit").nth(k).click()

    def tap(self, k, level, svg="#board-svg"):   # level 1..5 from the board's edge (the bar's middle) of the k-th tap area
        self.sheet_for()
        hit = self.page.locator(f"{svg} .hit").nth(k)
        top = k < 12 or k == 24                  # 0..11 the upper row, 12..23 the lower, 24/25 the bar's halves
        f = (level - 0.5) * 38 / 196             # the level's middle, as a fraction of the half
        if k >= 24:                              # the bar's stacks start by its middle (board-view.js BAR_GAP, BAR_STEP)
            f, top = (9 + (level - 0.5) * 36) / 196, not top
        box = hit.bounding_box()
        hit.click(position={"x": box["width"] / 2, "y": box["height"] * (f if top else 1 - f)})

    def number(self, k):                    # the number of the k-th point: empties it
        self.sheet_for()
        self.page.locator("#board-svg .hit-num").nth(k).click()

    def hold(self, k):                      # the palette of the k-th tap area (a right click, as a long press)
        self.sheet_for()
        self.page.locator("#board-svg .hit").nth(k).click(button="right")

    def pick(self, n, side=None):           # in the palette: the colour, then the count
        if side:
            self.page.click(f'#palette-side [data-value="{side}"]')
        self.page.click(f'#palette-counts [data-n="{n}"]')

    def choose(self, selector, value):
        self.sheet_for(selector)
        if self.page.evaluate("(q) => document.querySelector(q).classList.contains('die-pick')", selector):
            # the dice are buttons (TODO-141): press the value, or the pressed one again to clear it
            now = self.page.evaluate("(q) => document.querySelector(q).dataset.value", selector)
            if value or now:
                self.page.click(f'{selector} button[data-n="{value or now}"]')
            return
        self.page.select_option(selector, value)

    def wait_step(self, step):
        self.page.wait_for_function(f"!document.getElementById('{step}').hidden && document.getElementById('busy').hidden",
                                    timeout=WAIT)

    def go(self, selector, step):           # a button that leads to another screen
        self.click(selector)
        self.wait_step(step)

    def wait_corners(self):                 # the corners screen, once the search for the corners is over
        self.wait_step("corners")
        self.page.wait_for_function("!/探しています/.test(document.getElementById('corner-help').textContent)", timeout=WAIT)


def flow_manual(r):
    r.open()
    r.snap("start")
    r.click("#manual"); r.snap("manual")
    r.tap(0, 2); r.snap("tap level 2 of 13")
    r.tap(0, 2); r.snap("tap the top checker")
    r.tap(1, 3); r.snap("tap an empty point")
    r.hold(2); r.pick(0, "black"); r.tap(2, 2); r.snap("奥's colour on an empty point")   # the colour last put (TODO-145)
    r.tap(18, 5); r.tap(18, 5); r.snap("5th level of 5: two more")
    r.number(5); r.snap("number: emptied")
    r.hold(17); r.snap("palette")
    r.pick(4, "white"); r.snap("palette: 手前 4")
    r.hold(17); r.click("#palette-close"); r.snap("palette closed")
    r.hold(17); r.click("#editor-title"); r.snap("palette closed by a tap outside")
    r.tap(25, 1); r.tap(24, 2); r.snap("bar")
    r.hold(24); r.pick(0); r.snap("bar: 奥 0 from the palette")
    r.click("#undo"); r.click("#undo"); r.snap("undo twice")
    r.part("colour"); r.snap("swap colours")   # 手前 dark (TODO-113)
    r.part("home"); r.snap("home left")        # mirrored
    r.part("roll"); r.snap("dice sheet")
    r.part("cube"); r.snap("cube sheet")
    r.part("match"); r.snap("match sheet")
    r.click("#sheet-match .sheet-close"); r.snap("sheet closed")
    r.choose("#die1", "3"); r.snap("one die")
    r.choose("#die2", "1"); r.snap("dice 3-1")
    r.seg("onRoll", "black"); r.snap("on roll 奥")
    r.seg("cubeAt", "white"); r.snap("cube 手前 offered: the dice are hidden")   # TODO-086
    r.click("#cube-offered"); r.snap("cube 手前 owned, with dice")
    r.choose("#die1", ""); r.click("#cube-offered"); r.snap("no dice: the cube is offered")
    r.choose("#cube-value", "8"); r.snap("cube 8")
    r.click("#cube-offered"); r.snap("cube owned")
    r.click("#cube-offered"); r.seg("onRoll", "white"); r.snap("offered, 手前 on roll: the cube moves")
    r.seg("cubeAt", "centre"); r.snap("cube centre")
    r.click("#reset-start"); r.snap("reset to the start")
    r.go("#analyze", "outcome"); r.snap("analysed: cube decision")
    r.click("#speak"); r.snap("read aloud")
    r.go("#back", "board")
    r.tap(0, 1); r.snap("one of 手前's checkers borne off: 手前 leads the race")
    r.choose("#die1", "6"); r.choose("#die2", "5"); r.snap("dice 6-5: result stale")
    r.go("#analyze", "outcome"); r.snap("analysed: best moves")
    if r.page.locator("#result .moves li").count() > 1:
        r.page.locator("#result .moves li").nth(1).click(); r.snap("second move")
    r.go("#back", "board")
    r.go("#analyze", "outcome"); r.snap("same board: result shown again")
    r.go("#back", "board")
    r.seg("plies", "3"); r.snap("3-ply: result stale")
    r.seg("plies", "2")
    r.seg("onRoll", "black"); r.go("#analyze", "outcome"); r.snap("turn flipped: analysed again")
    r.go("#back", "board"); r.go("#back", "photo"); r.snap("back to the start")


def flow_photo(r):
    r.open()
    truth = json.loads((ROOT / f"samples/{SAMPLE}.truth.json").read_text())
    r.page.set_input_files("#file", str(ROOT / "samples" / truth["image"]))
    r.wait_corners(); r.snap("corners found")
    r.go("#recognize", "board"); r.snap("photo read")
    r.click("#photo-side"); r.snap("photo hidden")
    r.click("#photo-side"); r.snap("photo beside")
    r.page.locator("#photo-svg").click(); r.snap("tap on the photo: the board stays")   # for looking only (TODO-088)
    r.go("#analyze", "outcome"); r.snap("analysed")
    r.go("#back", "board"); r.go("#back", "corners"); r.snap("back to the corners")
    r.go("#hdr-reuse", "board"); r.snap("board again (header)")
    r.go("#back", "corners")
    r.go("#to-board", "board"); r.snap("board again (button)")
    r.go("#back", "corners")
    r.click("#corner-reset"); r.snap("corners cleared")
    box = r.page.locator("#photo-canvas").bounding_box()
    at = lambda fx, fy: (box["x"] + fx * box["width"], box["y"] + fy * box["height"])   # noqa: E731
    for k, (fx, fy) in enumerate([(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8)]):
        r.page.mouse.click(*at(fx, fy)); r.snap(f"corner {k + 1} tapped")
    x, y = at(0.8, 0.8)
    r.page.mouse.move(x, y); r.page.mouse.down(); r.page.mouse.move(x + 15, y + 10, steps=3)
    r.snap("dragging corner 3 (loupe)")
    r.page.mouse.up(); r.snap("corner 3 dropped")
    r.go("#back", "photo"); r.snap("recent photos")


def flow_history(r):
    """Needs a photo kept by flow_photo in the same browser."""
    r.open()   # a new page: as after closing the app
    r.page.wait_for_function("document.querySelectorAll('#history-list li').length > 0")
    r.snap("reopened app")
    r.page.locator("#history-list .open").first.click(); r.wait_corners(); r.snap("photo reopened")
    r.go("#to-board", "board"); r.snap("its board")
    r.go("#back", "corners")
    r.click("#corner-reset"); r.go("#to-board", "board"); r.snap("its board without corners")
    r.go("#back", "corners"); r.go("#back", "photo")
    r.page.locator("#history-list .del").first.click(); r.snap("photo deleted")


FLOWS = {"manual": flow_manual, "photo": flow_photo, "history": flow_history}


def record(out, names):
    from playwright.sync_api import sync_playwright
    names = names or list(FLOWS)
    if "history" in names and "photo" not in names:
        names = [n for n in FLOWS if n in names or n == "photo"]
    with sync_playwright() as p:
        browser = (p.chromium.connect_over_cdp(os.environ["BG_CDP"]) if os.environ.get("BG_CDP")   # tools/live_view.py's, to watch
                   else p.chromium.launch(executable_path=CHROMIUM if Path(CHROMIUM).exists() else None))
        ctx = browser.new_context(viewport={"width": 412, "height": 915}, reduced_motion="reduce",
                                  service_workers="block", accept_downloads=True)
        ctx.add_init_script(INIT)
        r = Run(ctx)
        for name in names:
            n = len(r.snaps)
            FLOWS[name](r)
            for snap in r.snaps[n:]:
                snap[0] = f"{name}: {snap[0]}"
        browser.close()
    Path(out).write_text(json.dumps(r.snaps, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(r.snaps)} snapshots -> {out}")


def differences(a, b):
    """[(step, what, a's value, b's value), ...] between two recordings."""
    out = []
    for (na, sa), (nb, sb) in zip(a, b):
        if na != nb:
            out.append((na, "step", na, nb))
            continue
        for k in sorted(set(sa) | set(sb)):
            if sa.get(k) != sb.get(k):
                out.append((na, k, sa.get(k), sb.get(k)))
    if len(a) != len(b):
        out.append(("(end)", "snapshots", len(a), len(b)))
    return out


def excerpt(va, vb, width=100):
    """Where two values first differ, with a little around it."""
    sa, sb = str(va), str(vb)
    i = next((i for i, (x, y) in enumerate(zip(sa, sb)) if x != y), min(len(sa), len(sb)))
    lo = max(0, i - width // 2)
    return sa[lo:lo + width], sb[lo:lo + width]


def compare(path_a, path_b):
    diffs = differences(json.loads(Path(path_a).read_text()), json.loads(Path(path_b).read_text()))
    for step, what, va, vb in diffs:
        xa, xb = excerpt(va, vb)
        print(f"[{step}] {what}\n  A: {xa!r}\n  B: {xb!r}")
    print(f"{len(diffs)} differences")
    return 1 if diffs else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == "record":
        sys.exit(record(args[1], args[2:]))
    if len(args) == 3 and args[0] == "compare":
        sys.exit(compare(args[1], args[2]))
    print(__doc__)
    sys.exit(2)
