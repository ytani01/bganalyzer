"""TODO-087 の確認: 読み取りを待つ間の絵（三角形・バー）の時間を、写真 1 枚で撮って確かめる。

    uv run -q --no-project --with playwright python archives/agents/TODO-087/verify.py

BG_URL（既定 http://127.0.0.1:8001/。変更を入れた worktree のアプリ）に対して、
押してから 300・550・800・1300ms の 4 枚を #photo-canvas から撮る。
読み取りの応答（/analyze-photo）は止めておき、最後に離して盤面の画面に移るかを見る。
時間は page.clock で進める。
"""
import base64, json, os
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = os.environ.get("BG_URL", "http://127.0.0.1:8001/")
ROOT = Path("/home/ytani/work/bganalyzer")
OUT = Path("/home/ytani/tmp/playwright-mcp/todo087")
CHROMIUM = os.environ.get("BG_CHROMIUM", "/usr/bin/chromium")
PHOTO = ROOT / "samples" / "screen1.png"
SHOTS = [(300, 300), (550, 250), (800, 250), (1300, 500)]   # (ms from the press, step ms to run)


def canvas_png(page, name):
    data = page.evaluate("() => document.getElementById('photo-canvas').toDataURL('image/png')")
    (OUT / name).write_bytes(base64.b64decode(data.split(",", 1)[1]))


def visible_steps(page):
    return page.evaluate("() => [...document.querySelectorAll('section.step')].filter((s) => !s.hidden).map((s) => s.id)")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    held, errors, log = [], [], {}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROMIUM if Path(CHROMIUM).exists() else None)
        ctx = browser.new_context(viewport={"width": 390, "height": 844})
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.clock.install()
        page.route("**/analyze-photo", lambda route: held.append(route))   # hold the reading
        page.goto(URL)
        page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
        page.set_input_files("#file", str(PHOTO))
        page.wait_for_function("BgApp.state.cornerGuess !== 'finding'", timeout=60000)
        page.wait_for_function("!document.getElementById('recognize').disabled", timeout=60000)
        log["version"] = page.evaluate("document.querySelector('#hdr-version').textContent.trim()")

        # from here the clock only moves when run_for is called
        page.clock.pause_at(page.evaluate("Date.now()") + 2000)
        page.evaluate("() => document.getElementById('recognize').click()")   # the press: t = 0
        elapsed = 0
        for (at, step) in SHOTS:
            page.clock.run_for(step)
            elapsed += step
            name = f"t{at}.png"
            canvas_png(page, name)
            log[f"shot_{at}"] = {"file": str(OUT / name), "elapsed_ms": elapsed,
                                 "steps": visible_steps(page), "held_reads": len(held)}

        # release the reading: the real server answers, the board screen should come
        page.clock.resume()
        for route in held:
            route.continue_()
        page.wait_for_function("!document.querySelector('#board').hidden && document.querySelector('#busy').hidden",
                               timeout=180000)
        log["after_release"] = {"steps": visible_steps(page), "busy_hidden": True}
        browser.close()
    log["page_errors"] = errors
    print(json.dumps(log, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
