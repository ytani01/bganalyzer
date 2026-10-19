"""Check the PWA the way a phone would, in a headless browser (docs/raspi.md).

    uv run -q --no-project --with playwright python tools/pi_ui_check.py          # all checks
    uv run -q --no-project --with playwright python tools/pi_ui_check.py collect  # some of them

Run it on the local host, next to the running app (bganalyzer.service). The browser is the host's own
/usr/bin/chromium, so Playwright downloads nothing. It sends only samples/ photos (public in this
repository). The "collect" check saves one pair in collected/ and removes it again.
What it cannot see stays for the phone: the voice itself, iPhone's share sheet, attaching files.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = os.environ.get(
    "BG_URL", "http://127.0.0.1:8000/"
)  # elsewhere: the app under test
CHROMIUM = os.environ.get(
    "BG_CHROMIUM", "/usr/bin/chromium"
)  # elsewhere: a Chromium there
COLLECTED = ROOT / "collected"
SAMPLE = "screen-app-grey-shot"  # an app screenshot with dice (4-2): read the same every time

# before the app's scripts: record what would be spoken, and no share sheet (a PC: download instead)
INIT = """
window.__spoken = [];
// saving on the server is the app's default (TODO-112): off here, or every run would leave a pair in collected/
try { if (!localStorage.getItem("collect")) localStorage.setItem("collect", "off"); } catch (_) { /* no storage */ }
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
# a share sheet that refuses the files, as Chrome on Android does for a .json
SHARE_DENIED = """
navigator.canShare = () => true;
navigator.share = () => Promise.reject(new DOMException("Permission denied", "NotAllowedError"));
"""


def open_app(browser, *scripts):
    page = browser.new_page(
        viewport={"width": 412, "height": 915}, accept_downloads=True
    )
    for script in (INIT, *scripts):
        page.add_init_script(script)
    page.alerts = []
    page.on("dialog", lambda d: (page.alerts.append(d.message), d.dismiss()))
    page.goto(URL)
    page.wait_for_function(
        "document.querySelector('#hdr-version').textContent.trim() !== ''"
    )
    return page


def read_photo(page, cube=None):
    """Load the sample, put its corners where the truth has them, and read it."""
    truth = json.loads((ROOT / f"samples/{SAMPLE}.truth.json").read_text())
    page.set_input_files("#file", str(ROOT / "samples" / truth["image"]))
    page.wait_for_function(
        "BgApp.state.photo && BgApp.state.cornerGuess !== 'finding'", timeout=60000
    )  # the photo in, then its corners
    # nothing picks these on the screen (TODO-113): read as the truth has them
    page.evaluate(
        "t => BgApp.update({ homePick: t.home, bottomColour: t.bottom_colour })", truth
    )
    page.evaluate(
        "c => BgApp.update({ corners: c, cornersMoved: true })",
        truth["corners_TL_TR_BR_BL"],
    )
    if (
        cube
    ):  # a cube set by hand before reading, as when reading again after setting it
        page.evaluate("c => BgApp.update({ cube: c })", cube)
    page.click("#recognize")
    page.wait_for_function(
        "!document.querySelector('#board').hidden && document.querySelector('#busy').hidden",
        timeout=120000,
    )
    return truth


def show_outcome(page):
    page.click("#analyze")
    page.wait_for_function("!document.querySelector('#outcome').hidden", timeout=120000)


def check_double(browser):
    """PI-017: a double set by hand, then a photo with dice: the best move, not 422."""
    page = open_app(browser)
    read_photo(page, {"at": "white", "value": 2, "offered": True})
    dice = page.evaluate("BgApp.rolled()")
    best = page.evaluate(
        "(r => r && r.moves && r.moves[0] && r.moves[0].move)(BgApp.state.result)"
    )
    help_ = page.text_content("#cube-help")
    ok = (
        not page.alerts and dice and best and help_ == ""
    )  # with dice, no cube help (TODO-086)
    return ok, f"dice={dice} best={best!r} cube-help={help_!r} alerts={page.alerts}"


def check_speech(browser):
    """PI-013: what the 読み上げ button reads is a short summary, without percentages or pip counts."""
    page = open_app(browser)
    read_photo(page)
    show_outcome(page)
    page.click("#speak")
    # every sentence asked for: the button turns back when the last one has ended
    page.wait_for_function(
        "document.querySelector('#speak').getAttribute('aria-pressed') === 'false'"
    )
    spoken = page.evaluate("window.__spoken")
    text = "".join(spoken)  # one sentence per /speech request (TODO-111)
    ok = (
        len(spoken) >= 1
        and "最善手" in text
        and not re.search(r"[%％]|勝率|\d+\s*ピップ|\d+\.\d", text)
    )
    return ok, f"spoken={spoken!r} alerts={page.alerts}"


def check_export(browser, *scripts):
    """PI-014: 「ファイルに書き出す」 gives the photo and a truth.json that matches the screen."""
    page = open_app(browser, *scripts)
    truth = read_photo(page)
    files, downloads = {}, []
    page.on("download", lambda d: downloads.append(d))
    page.click("#export-sample")
    for _ in range(100):  # both come at once
        if len(downloads) >= 2:
            break
        page.wait_for_timeout(100)
    with tempfile.TemporaryDirectory() as tmp:
        for dl in downloads:
            files[dl.suggested_filename] = Path(tmp, dl.suggested_filename)
            dl.save_as(files[dl.suggested_filename])
        names = sorted(files)
        t = next(
            (
                json.loads(p.read_text())
                for n, p in files.items()
                if n.endswith(".truth.json")
            ),
            {},
        )
        image = files.get(t.get("image"))
        board = page.evaluate("BgApp.state.board.points")
        ok = (
            len(files) == 2
            and image
            and image.stat().st_size > 0
            and t["points"] == board
            and t["dice"] == page.evaluate("BgApp.rolled()")
            and t["home"] == truth["home"]
        )
    return (
        ok,
        f"files={names} points_match={t.get('points') == board} dice={t.get('dice')} alerts={page.alerts}",
    )


def collected():
    return set(p.name for p in COLLECTED.iterdir()) if COLLECTED.is_dir() else set()


def evaluate(path):
    return subprocess.run(
        [str(ROOT / ".venv/bin/python"), "recognizer/evaluate.py", str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )


def check_collect(browser):
    """PI-015: with 「サーバーに保存する」 on, analysing keeps one pair in collected/ (off: nothing)."""
    out = []
    for mode in ("off", "on"):
        before = collected()
        page = open_app(browser)
        read_photo(page)
        seg = f'.seg[data-name="collect"] [data-value="{mode}"]'  # in 「読み取りの改善」: shown only when the server keeps samples
        page.click(seg)
        show_outcome(page)
        page.wait_for_timeout(2000)  # sendSample does not hold up the result
        new = sorted(collected() - before)
        out.append((mode, new, page.alerts))
    (_, off_new, _), (_, on_new, alerts) = out
    ok = (
        not off_new
        and len(on_new) == 2
        and any(n.endswith(".truth.json") for n in on_new)
        and not alerts
    )
    measured = ""
    if ok:
        t = next(n for n in on_new if n.endswith(".truth.json"))
        r = evaluate(COLLECTED / t)
        measured = (r.stdout or r.stderr).strip().splitlines()[-1:]
        ok = r.returncode == 0
    if on_new:  # this pair is a test, not a photo to learn from
        for n in on_new:
            (COLLECTED / n).unlink(missing_ok=True)
    return (
        ok,
        f"off={off_new} on={on_new} evaluate={measured} left={sorted(collected() & set(on_new))}",
    )


CHECKS = {
    "double": check_double,
    "speech": check_speech,
    "export": check_export,
    "export-denied": lambda browser: check_export(browser, SHARE_DENIED),
    "collect": check_collect,
}


def main(names):
    failed = 0
    with sync_playwright() as p:
        browser = (
            p.chromium.connect_over_cdp(os.environ["BG_CDP"])
            if os.environ.get("BG_CDP")  # tools/live_view.py's, to watch
            else p.chromium.launch(executable_path=CHROMIUM)
        )
        print("version:", json.loads(browser.new_page().goto(URL + "version").text()))
        for name in names or CHECKS:
            try:
                ok, detail = CHECKS[name](browser)
            except Exception as e:  # one check failing should not hide the others
                ok, detail = False, f"{type(e).__name__}: {e}".splitlines()[0]
            failed += not ok
            print(f"{'OK  ' if ok else 'FAIL'} {name}: {detail}")
        browser.close()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
