"""TODO-115 / TODO-109 / TODO-117 の PWA 確認（実測・読み取りのみ）。

http://127.0.0.1:8011/ を、開いている live_view のブラウザ（CDP）の新しいページで開く。
出力は 1 行 1 項目の JSON に近い行。
"""
import json
import time

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8011/"
CDP = "http://127.0.0.1:9222"
TIMEOUT = 120_000

console_errors = []


def out(key, value):
    print(f"[{key}] {json.dumps(value, ensure_ascii=False)}", flush=True)


def visible(page, sel):
    return page.locator(sel).first.is_visible()


def aria(page, sel):
    return page.get_attribute(sel, "aria-pressed")


def wait_visible(page, sel, timeout=TIMEOUT):
    page.locator(sel).first.wait_for(state="visible", timeout=timeout)


with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP)
    ctx = browser.contexts[0]
    page = ctx.new_page()
    page.set_default_timeout(TIMEOUT)
    page.on("console", lambda m: console_errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: console_errors.append(f"pageerror: {e}"))

    page.goto(URL, wait_until="load")
    page.wait_for_function("document.getElementById('hdr-version') && document.getElementById('hdr-version').textContent.trim().length > 0")

    # --- TODO-115 a
    ver = page.inner_text("#hdr-version").strip()
    out("115a hdr-version", ver)
    out("115a startswith a0.65.0", ver.startswith("a0.65.0"))

    # --- TODO-117 1
    note = page.evaluate("document.querySelector('#history .note') && document.querySelector('#history .note').textContent")
    out("117.1 history note", note)
    out("117.1 history note matches", note == "最近の 100 枚を、この端末の中だけに残します。")
    out("117.1 history hidden", page.evaluate("document.getElementById('history').hidden"))

    # --- TODO-109 2
    tips = page.evaluate("Array.from(document.querySelectorAll('details.tips li')).map(li => li.textContent)")
    out("109.2 tips count", len(tips))
    for t in tips:
        out("109.2 tip", t)
    expected = [
        "手前の人が写真の下になる向きで撮る（バーが縦になるように）。向きが違うときは、四隅の画面で 90° 回せる",
        "ダイスは、見やすい位置に置く",
        "カップなど、不要なものはボードの外に置く",
    ]
    for e in expected:
        out("109.2 has", {"text": e[:20], "found": e in tips})
    out("109.2 dice-outside absent", not any("ダイスやカップは盤の外に置く" in t for t in tips))

    # --- TODO-115 b (photo screen part)
    out("115b photo: auto-speak-opt visible", visible(page, "#auto-speak-opt"))
    out("115b photo: auto-speak-opt hidden attr", page.evaluate("document.getElementById('auto-speak-opt').hidden"))

    # 手で入力へ
    page.click("#manual")
    wait_visible(page, "#analyze")
    out("115b board: auto-speak-opt visible", visible(page, "#auto-speak-opt"))
    out("115b board: auto-speak checked (default)", page.is_checked("#auto-speak"))
    out("115b localStorage autoSpeak at start", page.evaluate("localStorage.getItem('autoSpeak')"))

    # --- TODO-115 c: オフのまま解析
    if page.is_checked("#auto-speak"):
        out("115c WARNING", "auto-speak was already on at start; not default-off")
    page.click("#analyze")
    wait_visible(page, "#speak")
    time.sleep(2)
    out("115c result: speak aria-pressed (after 2s, off)", aria(page, "#speak"))
    out("115c result: speak visible", visible(page, "#speak"))

    # --- TODO-115 d: 戻ってオンにして解析
    page.click("#back")
    wait_visible(page, "#analyze")
    page.locator("#auto-speak").check()
    out("115d board: auto-speak checked after on", page.is_checked("#auto-speak"))
    out("115d localStorage autoSpeak after on", page.evaluate("localStorage.getItem('autoSpeak')"))
    page.click("#analyze")
    wait_visible(page, "#speak")
    t0 = time.time()
    try:
        page.wait_for_function("document.getElementById('speak').getAttribute('aria-pressed') === 'true'", timeout=20_000)
        out("115d result: speak aria-pressed becomes true", {"seen": True, "after_s": round(time.time() - t0, 2)})
    except Exception as ex:  # noqa: BLE001
        out("115d result: speak aria-pressed becomes true", {"seen": False, "value": aria(page, "#speak"), "err": str(ex).splitlines()[0]})
    out("115d result: speak aria-pressed now", aria(page, "#speak"))

    # --- TODO-115 e: 戻る で盤面へ、aria-pressed が false に戻る
    page.click("#back")
    wait_visible(page, "#analyze")
    time.sleep(1)
    out("115e board after back: speak aria-pressed", aria(page, "#speak"))

    # --- TODO-115 f: 再読み込みで autoSpeak が残る
    page.reload(wait_until="load")
    page.wait_for_function("document.getElementById('hdr-version') && document.getElementById('hdr-version').textContent.trim().length > 0")
    page.click("#manual")
    wait_visible(page, "#analyze")
    out("115f after reload: localStorage autoSpeak", page.evaluate("localStorage.getItem('autoSpeak')"))
    out("115f after reload: auto-speak checked", page.is_checked("#auto-speak"))

    # 最後にオフへ戻す
    page.locator("#auto-speak").uncheck()
    out("115f restore: localStorage autoSpeak", page.evaluate("localStorage.getItem('autoSpeak')"))
    out("115f restore: auto-speak checked", page.is_checked("#auto-speak"))

    out("console errors", console_errors)
    page.close()
    # browser は閉じない（利用者の live_view の窓）
    browser.close  # no-op reference; connect_over_cdp の close はブラウザを閉じないよう呼ばない
